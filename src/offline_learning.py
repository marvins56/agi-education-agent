"""
Offline Learning System - Offline-first architecture for intermittent connectivity

This module provides comprehensive offline learning capabilities including lesson queuing,
progress synchronization, bandwidth-adaptive content delivery, and power outage resilience
designed for East African educational constraints.
"""

import json
import os
import time
import sqlite3
import hashlib
import threading
import requests
import gzip
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Network connection status"""
    OFFLINE = "offline"
    SLOW = "slow"  # < 100 kbps
    MODERATE = "moderate"  # 100 kbps - 1 Mbps
    FAST = "fast"  # > 1 Mbps


class ContentQuality(Enum):
    """Content quality levels for bandwidth adaptation"""
    MINIMAL = "minimal"  # Text only, compressed audio
    LOW = "low"  # Text + compressed images + audio
    MEDIUM = "medium"  # Text + images + audio + basic animations
    HIGH = "high"  # Full multimedia experience


class SyncStatus(Enum):
    """Synchronization status for offline content"""
    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


@dataclass
class LessonContent:
    """Lightweight lesson content structure for offline use"""
    lesson_id: str
    title: str
    subject: str
    grade_level: int
    
    # Core content (always required)
    text_content: str
    key_concepts: List[str]
    learning_objectives: List[str]
    
    # Optional multimedia (bandwidth-dependent)
    audio_content: Optional[str] = None  # Base64 or file path
    images: List[Dict[str, str]] = field(default_factory=list)  # [{"description": "...", "data": "base64..."}]
    animations: List[str] = field(default_factory=list)
    
    # Interactive elements
    exercises: List[Dict[str, Any]] = field(default_factory=list)
    quiz_questions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    estimated_duration_minutes: int = 30
    prerequisites: List[str] = field(default_factory=list)
    difficulty_level: float = 5.0  # 1-10 scale
    content_quality: ContentQuality = ContentQuality.MEDIUM
    compressed_size_kb: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def compress_for_storage(self) -> dict:
        """Compress lesson content for efficient storage"""
        compressed_data = asdict(self)
        
        # Compress text content if large
        if len(self.text_content) > 1000:
            compressed_text = gzip.compress(self.text_content.encode('utf-8'))
            compressed_data['text_content'] = compressed_text.hex()
            compressed_data['text_compressed'] = True
        else:
            compressed_data['text_compressed'] = False
            
        return compressed_data
    
    @classmethod
    def decompress_from_storage(cls, data: dict) -> 'LessonContent':
        """Decompress lesson content from storage"""
        if data.get('text_compressed', False):
            compressed_text = bytes.fromhex(data['text_content'])
            data['text_content'] = gzip.decompress(compressed_text).decode('utf-8')
        
        # Remove compression metadata
        data.pop('text_compressed', None)
        
        # Handle datetime conversion
        if isinstance(data.get('last_updated'), str):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
            
        return cls(**data)


@dataclass
class ProgressEntry:
    """Individual progress entry for a learning interaction"""
    student_id: str
    lesson_id: str
    timestamp: datetime
    interaction_type: str  # "lesson_start", "exercise_completed", "quiz_answered", etc.
    data: Dict[str, Any]  # Flexible data for different interaction types
    offline_generated: bool = True  # Whether this was created offline
    sync_status: SyncStatus = SyncStatus.PENDING
    sync_retry_count: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage/transmission"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProgressEntry':
        """Create from dictionary from storage/transmission"""
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class BandwidthEstimator:
    """Estimates available bandwidth and adapts content quality accordingly"""
    
    def __init__(self, test_url: str = "https://httpbin.org/bytes/1024"):
        self.test_url = test_url
        self.bandwidth_history: List[Tuple[datetime, float]] = []  # (timestamp, kbps)
        self.current_status = ConnectionStatus.OFFLINE
        self.last_test_time: Optional[datetime] = None
        self.test_interval_seconds = 300  # Test every 5 minutes
        
    def estimate_bandwidth(self) -> Tuple[ConnectionStatus, float]:
        """Estimate current bandwidth by downloading test data"""
        try:
            start_time = time.time()
            response = requests.get(self.test_url, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                # Calculate bandwidth in kbps
                data_size_kb = len(response.content) / 1024
                duration_seconds = end_time - start_time
                bandwidth_kbps = (data_size_kb / duration_seconds)
                
                # Record measurement
                self.bandwidth_history.append((datetime.now(), bandwidth_kbps))
                
                # Keep only last 10 measurements
                if len(self.bandwidth_history) > 10:
                    self.bandwidth_history.pop(0)
                
                # Determine connection status
                if bandwidth_kbps < 100:
                    self.current_status = ConnectionStatus.SLOW
                elif bandwidth_kbps < 1000:  # 1 Mbps
                    self.current_status = ConnectionStatus.MODERATE
                else:
                    self.current_status = ConnectionStatus.FAST
                    
                self.last_test_time = datetime.now()
                logger.info(f"Bandwidth estimated at {bandwidth_kbps:.2f} kbps ({self.current_status.value})")
                return self.current_status, bandwidth_kbps
            
        except requests.RequestException as e:
            logger.warning(f"Bandwidth test failed: {e}")
            self.current_status = ConnectionStatus.OFFLINE
            
        return self.current_status, 0.0
    
    def should_test_bandwidth(self) -> bool:
        """Check if it's time to test bandwidth again"""
        if self.last_test_time is None:
            return True
        return (datetime.now() - self.last_test_time).seconds > self.test_interval_seconds
    
    def get_recommended_quality(self) -> ContentQuality:
        """Get recommended content quality based on current bandwidth"""
        if self.current_status == ConnectionStatus.OFFLINE:
            return ContentQuality.MINIMAL
        elif self.current_status == ConnectionStatus.SLOW:
            return ContentQuality.LOW
        elif self.current_status == ConnectionStatus.MODERATE:
            return ContentQuality.MEDIUM
        else:
            return ContentQuality.HIGH
    
    def get_average_bandwidth(self) -> float:
        """Get average bandwidth from recent measurements"""
        if not self.bandwidth_history:
            return 0.0
        return sum(measurement[1] for measurement in self.bandwidth_history) / len(self.bandwidth_history)


class OfflineStorage:
    """SQLite-based storage system for offline learning data"""
    
    def __init__(self, db_path: str = "offline_learning.db"):
        self.db_path = db_path
        self.conn_lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS lessons (
                    lesson_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    grade_level INTEGER NOT NULL,
                    content_data TEXT NOT NULL,
                    content_quality TEXT NOT NULL,
                    download_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS progress_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    interaction_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    offline_generated BOOLEAN DEFAULT TRUE,
                    sync_status TEXT DEFAULT 'pending',
                    sync_retry_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS lesson_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id TEXT NOT NULL,
                    lesson_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    requested_quality TEXT DEFAULT 'medium',
                    download_status TEXT DEFAULT 'queued',
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS sync_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_progress_student ON progress_entries(student_id);
                CREATE INDEX IF NOT EXISTS idx_progress_lesson ON progress_entries(lesson_id);
                CREATE INDEX IF NOT EXISTS idx_progress_sync ON progress_entries(sync_status);
                CREATE INDEX IF NOT EXISTS idx_queue_student ON lesson_queue(student_id);
            """)
    
    def store_lesson(self, lesson: LessonContent) -> bool:
        """Store a lesson in the local database"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    compressed_data = lesson.compress_for_storage()
                    conn.execute("""
                        INSERT OR REPLACE INTO lessons 
                        (lesson_id, title, subject, grade_level, content_data, content_quality, last_accessed, access_count)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 
                               COALESCE((SELECT access_count FROM lessons WHERE lesson_id = ?), 0))
                    """, (
                        lesson.lesson_id, lesson.title, lesson.subject, lesson.grade_level,
                        json.dumps(compressed_data), lesson.content_quality.value, lesson.lesson_id
                    ))
            return True
        except Exception as e:
            logger.error(f"Failed to store lesson {lesson.lesson_id}: {e}")
            return False
    
    def get_lesson(self, lesson_id: str) -> Optional[LessonContent]:
        """Retrieve a lesson from local storage"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT content_data FROM lessons WHERE lesson_id = ?
                    """, (lesson_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        # Update access tracking
                        conn.execute("""
                            UPDATE lessons SET last_accessed = CURRENT_TIMESTAMP, 
                                             access_count = access_count + 1 
                            WHERE lesson_id = ?
                        """, (lesson_id,))
                        
                        # Decompress and return lesson
                        content_data = json.loads(row['content_data'])
                        return LessonContent.decompress_from_storage(content_data)
                        
        except Exception as e:
            logger.error(f"Failed to retrieve lesson {lesson_id}: {e}")
        
        return None
    
    def get_available_lessons(self, student_grade: int = None, subject: str = None) -> List[dict]:
        """Get list of available lessons, optionally filtered"""
        lessons = []
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    query = "SELECT lesson_id, title, subject, grade_level, content_quality FROM lessons"
                    params = []
                    
                    conditions = []
                    if student_grade:
                        conditions.append("grade_level <= ?")
                        params.append(student_grade + 1)  # Allow one grade above
                    if subject:
                        conditions.append("subject = ?")
                        params.append(subject)
                    
                    if conditions:
                        query += " WHERE " + " AND ".join(conditions)
                    
                    query += " ORDER BY last_accessed DESC, access_count DESC"
                    
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    
                    for row in cursor.fetchall():
                        lessons.append(dict(row))
                        
        except Exception as e:
            logger.error(f"Failed to get available lessons: {e}")
        
        return lessons
    
    def store_progress(self, progress_entry: ProgressEntry) -> bool:
        """Store a progress entry"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO progress_entries 
                        (student_id, lesson_id, timestamp, interaction_type, data, 
                         offline_generated, sync_status, sync_retry_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        progress_entry.student_id, progress_entry.lesson_id,
                        progress_entry.timestamp.isoformat(), progress_entry.interaction_type,
                        json.dumps(progress_entry.data), progress_entry.offline_generated,
                        progress_entry.sync_status.value, progress_entry.sync_retry_count
                    ))
            return True
        except Exception as e:
            logger.error(f"Failed to store progress entry: {e}")
            return False
    
    def get_pending_sync_entries(self, limit: int = 50) -> List[ProgressEntry]:
        """Get progress entries that need to be synced"""
        entries = []
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM progress_entries 
                        WHERE sync_status = 'pending' AND sync_retry_count < 5
                        ORDER BY timestamp ASC
                        LIMIT ?
                    """, (limit,))
                    
                    for row in cursor.fetchall():
                        data = dict(row)
                        data['data'] = json.loads(data['data'])
                        entries.append(ProgressEntry.from_dict(data))
                        
        except Exception as e:
            logger.error(f"Failed to get pending sync entries: {e}")
        
        return entries
    
    def update_sync_status(self, entry_id: int, status: SyncStatus, retry_count: int = None):
        """Update sync status of a progress entry"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    if retry_count is not None:
                        conn.execute("""
                            UPDATE progress_entries 
                            SET sync_status = ?, sync_retry_count = ?
                            WHERE id = ?
                        """, (status.value, retry_count, entry_id))
                    else:
                        conn.execute("""
                            UPDATE progress_entries 
                            SET sync_status = ?
                            WHERE id = ?
                        """, (status.value, entry_id))
                        
        except Exception as e:
            logger.error(f"Failed to update sync status: {e}")
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to free storage space"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    # Remove old synced progress entries
                    conn.execute("""
                        DELETE FROM progress_entries 
                        WHERE sync_status = 'synced' AND timestamp < ?
                    """, (cutoff_date.isoformat(),))
                    
                    # Remove lessons not accessed recently and with low access count
                    conn.execute("""
                        DELETE FROM lessons 
                        WHERE last_accessed < ? AND access_count < 3
                    """, (cutoff_date.isoformat(),))
                    
                    logger.info("Cleaned up old offline data")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")


class ProgressSyncManager:
    """Manages synchronization of progress data with remote server"""
    
    def __init__(self, storage: OfflineStorage, 
                 sync_endpoint: str = None,
                 api_key: str = None):
        self.storage = storage
        self.sync_endpoint = sync_endpoint or "https://eduagi.example.com/api/sync"
        self.api_key = api_key
        self.sync_in_progress = False
        self.sync_lock = threading.Lock()
        
    def sync_progress_data(self, max_entries: int = 50) -> Tuple[int, int]:
        """Sync pending progress entries to remote server
        
        Returns:
            Tuple of (successful_syncs, failed_syncs)
        """
        if self.sync_in_progress:
            logger.info("Sync already in progress")
            return 0, 0
        
        with self.sync_lock:
            self.sync_in_progress = True
            
        successful_syncs = 0
        failed_syncs = 0
        
        try:
            pending_entries = self.storage.get_pending_sync_entries(max_entries)
            
            if not pending_entries:
                logger.info("No pending progress entries to sync")
                return 0, 0
                
            logger.info(f"Syncing {len(pending_entries)} progress entries")
            
            # Batch sync entries
            for entry in pending_entries:
                success = self._sync_single_entry(entry)
                if success:
                    successful_syncs += 1
                else:
                    failed_syncs += 1
                    
        except Exception as e:
            logger.error(f"Error during progress sync: {e}")
            failed_syncs += len(pending_entries) if 'pending_entries' in locals() else 0
        finally:
            with self.sync_lock:
                self.sync_in_progress = False
                
        logger.info(f"Sync completed: {successful_syncs} successful, {failed_syncs} failed")
        return successful_syncs, failed_syncs
    
    def _sync_single_entry(self, entry: ProgressEntry) -> bool:
        """Sync a single progress entry"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
                headers['Content-Type'] = 'application/json'
            
            response = requests.post(
                self.sync_endpoint,
                json=entry.to_dict(),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Mark as synced
                self.storage.update_sync_status(entry.id if hasattr(entry, 'id') else -1, SyncStatus.SYNCED)
                return True
            else:
                logger.warning(f"Sync failed for entry {entry.student_id}: {response.status_code}")
                # Increment retry count
                retry_count = entry.sync_retry_count + 1
                if retry_count >= 5:
                    self.storage.update_sync_status(entry.id if hasattr(entry, 'id') else -1, SyncStatus.FAILED, retry_count)
                else:
                    self.storage.update_sync_status(entry.id if hasattr(entry, 'id') else -1, SyncStatus.PENDING, retry_count)
                return False
                
        except requests.RequestException as e:
            logger.error(f"Network error syncing entry: {e}")
            # Increment retry count
            retry_count = entry.sync_retry_count + 1
            if retry_count >= 5:
                self.storage.update_sync_status(entry.id if hasattr(entry, 'id') else -1, SyncStatus.FAILED, retry_count)
            else:
                self.storage.update_sync_status(entry.id if hasattr(entry, 'id') else -1, SyncStatus.PENDING, retry_count)
            return False


class LessonQueue:
    """Manages queuing and downloading of lessons for offline use"""
    
    def __init__(self, storage: OfflineStorage,
                 bandwidth_estimator: BandwidthEstimator,
                 lesson_endpoint: str = None,
                 api_key: str = None):
        self.storage = storage
        self.bandwidth_estimator = bandwidth_estimator
        self.lesson_endpoint = lesson_endpoint or "https://eduagi.example.com/api/lessons"
        self.api_key = api_key
        self.download_in_progress = False
        self.download_lock = threading.Lock()
        
    def queue_lesson(self, student_id: str, lesson_id: str, 
                    priority: int = 5, 
                    requested_quality: ContentQuality = None) -> bool:
        """Add a lesson to the download queue"""
        if requested_quality is None:
            requested_quality = self.bandwidth_estimator.get_recommended_quality()
            
        try:
            with sqlite3.connect(self.storage.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO lesson_queue 
                    (student_id, lesson_id, priority, requested_quality, download_status)
                    VALUES (?, ?, ?, ?, 'queued')
                """, (student_id, lesson_id, priority, requested_quality.value))
            
            logger.info(f"Queued lesson {lesson_id} for student {student_id} at {requested_quality.value} quality")
            return True
        except Exception as e:
            logger.error(f"Failed to queue lesson: {e}")
            return False
    
    def process_download_queue(self, max_downloads: int = 5) -> Tuple[int, int]:
        """Process lesson download queue
        
        Returns:
            Tuple of (successful_downloads, failed_downloads)
        """
        if self.download_in_progress:
            logger.info("Download already in progress")
            return 0, 0
        
        with self.download_lock:
            self.download_in_progress = True
            
        successful_downloads = 0
        failed_downloads = 0
        
        try:
            # Get queued lessons ordered by priority
            queued_lessons = self._get_queued_lessons(max_downloads)
            
            if not queued_lessons:
                return 0, 0
                
            logger.info(f"Processing {len(queued_lessons)} lesson downloads")
            
            for lesson_info in queued_lessons:
                success = self._download_lesson(lesson_info)
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads += 1
                    
        except Exception as e:
            logger.error(f"Error processing download queue: {e}")
        finally:
            with self.download_lock:
                self.download_in_progress = False
                
        return successful_downloads, failed_downloads
    
    def _get_queued_lessons(self, limit: int) -> List[dict]:
        """Get lessons from download queue"""
        lessons = []
        try:
            with sqlite3.connect(self.storage.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM lesson_queue 
                    WHERE download_status = 'queued'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT ?
                """, (limit,))
                
                for row in cursor.fetchall():
                    lessons.append(dict(row))
                    
        except Exception as e:
            logger.error(f"Failed to get queued lessons: {e}")
            
        return lessons
    
    def _download_lesson(self, lesson_info: dict) -> bool:
        """Download a single lesson"""
        lesson_id = lesson_info['lesson_id']
        requested_quality = lesson_info['requested_quality']
        
        try:
            # Update status to downloading
            self._update_download_status(lesson_info['id'], 'downloading')
            
            # Make API request
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
                
            params = {
                'quality': requested_quality,
                'format': 'offline'
            }
            
            response = requests.get(
                f"{self.lesson_endpoint}/{lesson_id}",
                params=params,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                lesson_data = response.json()
                lesson = LessonContent(**lesson_data)
                
                # Store lesson locally
                if self.storage.store_lesson(lesson):
                    self._update_download_status(lesson_info['id'], 'completed')
                    logger.info(f"Successfully downloaded lesson {lesson_id}")
                    return True
                else:
                    self._update_download_status(lesson_info['id'], 'failed', "Storage error")
                    return False
            else:
                error_msg = f"HTTP {response.status_code}"
                self._update_download_status(lesson_info['id'], 'failed', error_msg)
                return False
                
        except requests.RequestException as e:
            error_msg = f"Network error: {e}"
            self._update_download_status(lesson_info['id'], 'failed', error_msg)
            logger.error(f"Failed to download lesson {lesson_id}: {e}")
            return False
    
    def _update_download_status(self, queue_id: int, status: str, error_message: str = None):
        """Update download status in queue"""
        try:
            with sqlite3.connect(self.storage.db_path) as conn:
                if error_message:
                    conn.execute("""
                        UPDATE lesson_queue 
                        SET download_status = ?, error_message = ?
                        WHERE id = ?
                    """, (status, error_message, queue_id))
                else:
                    conn.execute("""
                        UPDATE lesson_queue 
                        SET download_status = ?
                        WHERE id = ?
                    """, (status, queue_id))
                    
        except Exception as e:
            logger.error(f"Failed to update download status: {e}")


class PowerOutageHandler:
    """Handles power outage resilience with auto-save functionality"""
    
    def __init__(self, storage: OfflineStorage, 
                 auto_save_interval: int = 30):
        self.storage = storage
        self.auto_save_interval = auto_save_interval  # seconds
        self.last_save_time = datetime.now()
        self.pending_progress: List[ProgressEntry] = []
        self.save_lock = threading.Lock()
        
        # Start auto-save thread
        self.auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self.running = True
        self.auto_save_thread.start()
    
    def record_interaction(self, student_id: str, lesson_id: str, 
                          interaction_type: str, data: dict):
        """Record a learning interaction (auto-saved periodically)"""
        progress_entry = ProgressEntry(
            student_id=student_id,
            lesson_id=lesson_id,
            timestamp=datetime.now(),
            interaction_type=interaction_type,
            data=data.copy()
        )
        
        with self.save_lock:
            self.pending_progress.append(progress_entry)
            
        # Force save if many pending entries
        if len(self.pending_progress) >= 10:
            self.force_save()
    
    def force_save(self):
        """Force immediate save of all pending progress"""
        with self.save_lock:
            if not self.pending_progress:
                return
                
            saved_count = 0
            for entry in self.pending_progress:
                if self.storage.store_progress(entry):
                    saved_count += 1
            
            logger.info(f"Force saved {saved_count} progress entries")
            self.pending_progress.clear()
            self.last_save_time = datetime.now()
    
    def _auto_save_loop(self):
        """Background auto-save loop"""
        while self.running:
            time.sleep(5)  # Check every 5 seconds
            
            if (datetime.now() - self.last_save_time).seconds >= self.auto_save_interval:
                if self.pending_progress:
                    logger.debug("Auto-saving progress data")
                    self.force_save()
    
    def shutdown(self):
        """Graceful shutdown with final save"""
        self.running = False
        self.force_save()
        if self.auto_save_thread.is_alive():
            self.auto_save_thread.join(timeout=5)
        logger.info("Power outage handler shutdown complete")


class OfflineLearningSystem:
    """Main offline learning system that coordinates all components"""
    
    def __init__(self, 
                 db_path: str = "offline_learning.db",
                 sync_endpoint: str = None,
                 lesson_endpoint: str = None,
                 api_key: str = None):
        
        # Initialize components
        self.storage = OfflineStorage(db_path)
        self.bandwidth_estimator = BandwidthEstimator()
        self.sync_manager = ProgressSyncManager(self.storage, sync_endpoint, api_key)
        self.lesson_queue = LessonQueue(self.storage, self.bandwidth_estimator, lesson_endpoint, api_key)
        self.power_outage_handler = PowerOutageHandler(self.storage)
        
        # Background tasks
        self._start_background_tasks()
        
    def _start_background_tasks(self):
        """Start background maintenance tasks"""
        def background_maintenance():
            while True:
                try:
                    # Test bandwidth periodically
                    if self.bandwidth_estimator.should_test_bandwidth():
                        self.bandwidth_estimator.estimate_bandwidth()
                    
                    # Sync progress when online
                    if self.bandwidth_estimator.current_status != ConnectionStatus.OFFLINE:
                        self.sync_manager.sync_progress_data()
                        
                    # Process lesson downloads
                    if self.bandwidth_estimator.current_status != ConnectionStatus.OFFLINE:
                        self.lesson_queue.process_download_queue()
                    
                    # Cleanup old data weekly
                    self.storage.cleanup_old_data()
                    
                    time.sleep(600)  # Run every 10 minutes
                    
                except Exception as e:
                    logger.error(f"Background maintenance error: {e}")
                    time.sleep(60)  # Wait before retrying
        
        maintenance_thread = threading.Thread(target=background_maintenance, daemon=True)
        maintenance_thread.start()
    
    def get_lesson(self, lesson_id: str, student_grade: int = None) -> Optional[LessonContent]:
        """Get lesson content, adapted for current connection quality"""
        lesson = self.storage.get_lesson(lesson_id)
        
        if lesson:
            # Adapt content quality based on current bandwidth
            recommended_quality = self.bandwidth_estimator.get_recommended_quality()
            if lesson.content_quality.value > recommended_quality.value:
                lesson = self._adapt_lesson_quality(lesson, recommended_quality)
                
        return lesson
    
    def _adapt_lesson_quality(self, lesson: LessonContent, target_quality: ContentQuality) -> LessonContent:
        """Adapt lesson content to target quality level"""
        adapted_lesson = LessonContent(
            lesson_id=lesson.lesson_id,
            title=lesson.title,
            subject=lesson.subject,
            grade_level=lesson.grade_level,
            text_content=lesson.text_content,
            key_concepts=lesson.key_concepts,
            learning_objectives=lesson.learning_objectives,
            estimated_duration_minutes=lesson.estimated_duration_minutes,
            prerequisites=lesson.prerequisites,
            difficulty_level=lesson.difficulty_level,
            content_quality=target_quality,
            last_updated=lesson.last_updated
        )
        
        # Add content based on quality level
        if target_quality in [ContentQuality.LOW, ContentQuality.MEDIUM, ContentQuality.HIGH]:
            adapted_lesson.audio_content = lesson.audio_content
            
        if target_quality in [ContentQuality.MEDIUM, ContentQuality.HIGH]:
            # Reduce image quality/size for medium
            adapted_lesson.images = lesson.images[:3] if target_quality == ContentQuality.MEDIUM else lesson.images
            
        if target_quality == ContentQuality.HIGH:
            adapted_lesson.animations = lesson.animations
            adapted_lesson.exercises = lesson.exercises
            adapted_lesson.quiz_questions = lesson.quiz_questions
        elif target_quality == ContentQuality.MEDIUM:
            adapted_lesson.exercises = lesson.exercises[:5]  # Limit exercises
            adapted_lesson.quiz_questions = lesson.quiz_questions[:3]  # Limit quiz
        else:
            # Minimal/Low: text-based exercises only
            text_exercises = [ex for ex in lesson.exercises if ex.get('type') == 'text'][:3]
            adapted_lesson.exercises = text_exercises
            
        return adapted_lesson
    
    def record_learning_interaction(self, student_id: str, lesson_id: str, 
                                   interaction_type: str, data: dict):
        """Record a learning interaction with power outage protection"""
        self.power_outage_handler.record_interaction(student_id, lesson_id, interaction_type, data)
    
    def queue_lesson_for_download(self, student_id: str, lesson_id: str, 
                                 priority: int = 5) -> bool:
        """Queue a lesson for offline download"""
        return self.lesson_queue.queue_lesson(student_id, lesson_id, priority)
    
    def get_available_lessons(self, student_grade: int = None, subject: str = None) -> List[dict]:
        """Get list of available offline lessons"""
        return self.storage.get_available_lessons(student_grade, subject)
    
    def get_connection_status(self) -> Tuple[ConnectionStatus, float]:
        """Get current connection status and bandwidth"""
        return self.bandwidth_estimator.current_status, self.bandwidth_estimator.get_average_bandwidth()
    
    def get_sync_status(self) -> dict:
        """Get synchronization status"""
        pending_entries = len(self.storage.get_pending_sync_entries())
        
        return {
            'pending_sync_entries': pending_entries,
            'sync_in_progress': self.sync_manager.sync_in_progress,
            'last_sync_attempt': None,  # TODO: Track last sync attempt
            'connection_status': self.bandwidth_estimator.current_status.value
        }
    
    def force_sync(self) -> Tuple[int, int]:
        """Force immediate synchronization"""
        return self.sync_manager.sync_progress_data()
    
    def shutdown(self):
        """Graceful shutdown of the offline learning system"""
        logger.info("Shutting down offline learning system")
        self.power_outage_handler.shutdown()
        
        # Final sync attempt
        if self.bandwidth_estimator.current_status != ConnectionStatus.OFFLINE:
            self.sync_manager.sync_progress_data()
            
        logger.info("Offline learning system shutdown complete")


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize offline learning system
    offline_system = OfflineLearningSystem()
    
    # Example: Create and store a lesson
    sample_lesson = LessonContent(
        lesson_id="math_001",
        title="Introduction to Fractions",
        subject="Mathematics",
        grade_level=3,
        text_content="A fraction represents a part of a whole. When we divide something into equal parts, each part is a fraction...",
        key_concepts=["numerator", "denominator", "equivalent fractions"],
        learning_objectives=["Understand what fractions represent", "Identify numerator and denominator"],
        audio_content="base64_encoded_audio_data_here",
        exercises=[
            {
                "type": "multiple_choice",
                "question": "What is the numerator in 3/4?",
                "options": ["3", "4", "7"],
                "correct_answer": "3"
            }
        ]
    )
    
    # Store lesson
    offline_system.storage.store_lesson(sample_lesson)
    
    # Queue lesson for download
    offline_system.queue_lesson_for_download("student_123", "math_002", priority=8)
    
    # Record learning interaction
    offline_system.record_learning_interaction(
        "student_123", 
        "math_001", 
        "exercise_completed",
        {
            "exercise_id": 1,
            "answer": "3",
            "correct": True,
            "time_spent_seconds": 45
        }
    )
    
    # Check system status
    connection_status, bandwidth = offline_system.get_connection_status()
    sync_status = offline_system.get_sync_status()
    
    print(f"Connection: {connection_status.value}, Bandwidth: {bandwidth:.2f} kbps")
    print(f"Pending sync entries: {sync_status['pending_sync_entries']}")
    
    # Simulate usage for a few seconds
    time.sleep(5)
    
    # Graceful shutdown
    offline_system.shutdown()