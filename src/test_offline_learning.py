"""
Tests for offline_learning.py module

Comprehensive tests for offline-first learning system including lesson queuing,
progress sync, bandwidth adaptation, and power outage resilience.
"""

import pytest
import sqlite3
import tempfile
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import threading

from offline_learning import (
    OfflineLearningSystem, OfflineStorage, BandwidthEstimator, 
    ProgressSyncManager, LessonQueue, PowerOutageHandler,
    LessonContent, ProgressEntry, ConnectionStatus, ContentQuality, SyncStatus
)


class TestLessonContent:
    """Test LessonContent class"""
    
    def test_lesson_content_creation(self):
        """Test basic lesson content creation"""
        lesson = LessonContent(
            lesson_id="test_001",
            title="Test Lesson",
            subject="Mathematics",
            grade_level=3,
            text_content="This is a test lesson about fractions.",
            key_concepts=["fractions", "numerator", "denominator"],
            learning_objectives=["Understand fractions", "Identify parts of fractions"]
        )
        
        assert lesson.lesson_id == "test_001"
        assert lesson.title == "Test Lesson"
        assert lesson.subject == "Mathematics"
        assert lesson.grade_level == 3
        assert "fractions" in lesson.text_content
        assert len(lesson.key_concepts) == 3
        assert len(lesson.learning_objectives) == 2
        assert lesson.content_quality == ContentQuality.MEDIUM
    
    def test_lesson_content_compression(self):
        """Test lesson content compression for storage"""
        # Create lesson with large text content
        large_text = "This is a test lesson. " * 100  # Large enough to trigger compression
        lesson = LessonContent(
            lesson_id="test_002",
            title="Large Lesson",
            subject="Science",
            grade_level=5,
            text_content=large_text,
            key_concepts=["test"],
            learning_objectives=["test objective"]
        )
        
        # Compress and decompress
        compressed_data = lesson.compress_for_storage()
        assert 'text_compressed' in compressed_data
        assert compressed_data['text_compressed'] is True
        
        decompressed_lesson = LessonContent.decompress_from_storage(compressed_data)
        assert decompressed_lesson.text_content == large_text
        assert decompressed_lesson.lesson_id == lesson.lesson_id
    
    def test_lesson_content_small_text_no_compression(self):
        """Test that small text content is not compressed"""
        small_text = "Small text"
        lesson = LessonContent(
            lesson_id="test_003",
            title="Small Lesson",
            subject="English",
            grade_level=2,
            text_content=small_text,
            key_concepts=["reading"],
            learning_objectives=["read simple text"]
        )
        
        compressed_data = lesson.compress_for_storage()
        assert compressed_data.get('text_compressed', False) is False
        assert compressed_data['text_content'] == small_text


class TestProgressEntry:
    """Test ProgressEntry class"""
    
    def test_progress_entry_creation(self):
        """Test progress entry creation"""
        entry = ProgressEntry(
            student_id="student_123",
            lesson_id="math_001",
            timestamp=datetime.now(),
            interaction_type="lesson_completed",
            data={"score": 85, "time_spent": 300}
        )
        
        assert entry.student_id == "student_123"
        assert entry.lesson_id == "math_001"
        assert entry.interaction_type == "lesson_completed"
        assert entry.data["score"] == 85
        assert entry.offline_generated is True
        assert entry.sync_status == SyncStatus.PENDING
    
    def test_progress_entry_dict_conversion(self):
        """Test conversion to/from dictionary"""
        original_entry = ProgressEntry(
            student_id="student_456",
            lesson_id="science_002",
            timestamp=datetime.now(),
            interaction_type="quiz_answered",
            data={"correct": True, "answer": "photosynthesis"}
        )
        
        # Convert to dict and back
        entry_dict = original_entry.to_dict()
        restored_entry = ProgressEntry.from_dict(entry_dict)
        
        assert restored_entry.student_id == original_entry.student_id
        assert restored_entry.lesson_id == original_entry.lesson_id
        assert restored_entry.interaction_type == original_entry.interaction_type
        assert restored_entry.data == original_entry.data
        assert isinstance(restored_entry.timestamp, datetime)


class TestBandwidthEstimator:
    """Test BandwidthEstimator class"""
    
    def test_bandwidth_estimator_initialization(self):
        """Test bandwidth estimator initialization"""
        estimator = BandwidthEstimator()
        
        assert estimator.current_status == ConnectionStatus.OFFLINE
        assert len(estimator.bandwidth_history) == 0
        assert estimator.last_test_time is None
    
    @patch('offline_learning.requests.get')
    def test_bandwidth_estimation_fast_connection(self, mock_get):
        """Test bandwidth estimation with fast connection"""
        # Mock fast response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'x' * 2048  # 2KB of data
        mock_get.return_value = mock_response
        
        # Mock time to simulate fast download
        with patch('offline_learning.time.time', side_effect=[0.0, 0.1]):  # 0.1 second download
            estimator = BandwidthEstimator()
            status, bandwidth = estimator.estimate_bandwidth()
            
            assert status == ConnectionStatus.FAST
            assert bandwidth > 1000  # Should be > 1 Mbps (1000 kbps)
            assert len(estimator.bandwidth_history) == 1
    
    @patch('offline_learning.requests.get')
    def test_bandwidth_estimation_slow_connection(self, mock_get):
        """Test bandwidth estimation with slow connection"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'x' * 1024  # 1KB of data
        mock_get.return_value = mock_response
        
        # Mock time to simulate slow download
        with patch('offline_learning.time.time', side_effect=[0.0, 30.0]):  # 30 second download
            estimator = BandwidthEstimator()
            status, bandwidth = estimator.estimate_bandwidth()
            
            assert status == ConnectionStatus.SLOW
            assert bandwidth < 100  # Should be < 100 kbps
    
    @patch('offline_learning.requests.get')
    def test_bandwidth_estimation_connection_error(self, mock_get):
        """Test bandwidth estimation with connection error"""
        mock_get.side_effect = ConnectionError("No internet")
        
        estimator = BandwidthEstimator()
        status, bandwidth = estimator.estimate_bandwidth()
        
        assert status == ConnectionStatus.OFFLINE
        assert bandwidth == 0.0
    
    def test_bandwidth_estimator_should_test(self):
        """Test bandwidth test timing logic"""
        estimator = BandwidthEstimator()
        
        # Should test initially
        assert estimator.should_test_bandwidth() is True
        
        # Set recent test time
        estimator.last_test_time = datetime.now()
        assert estimator.should_test_bandwidth() is False
        
        # Set old test time
        estimator.last_test_time = datetime.now() - timedelta(minutes=10)
        assert estimator.should_test_bandwidth() is True
    
    def test_content_quality_recommendations(self):
        """Test content quality recommendations based on connection"""
        estimator = BandwidthEstimator()
        
        # Test different connection states
        estimator.current_status = ConnectionStatus.OFFLINE
        assert estimator.get_recommended_quality() == ContentQuality.MINIMAL
        
        estimator.current_status = ConnectionStatus.SLOW
        assert estimator.get_recommended_quality() == ContentQuality.LOW
        
        estimator.current_status = ConnectionStatus.MODERATE
        assert estimator.get_recommended_quality() == ContentQuality.MEDIUM
        
        estimator.current_status = ConnectionStatus.FAST
        assert estimator.get_recommended_quality() == ContentQuality.HIGH


class TestOfflineStorage:
    """Test OfflineStorage class"""
    
    def test_storage_initialization(self):
        """Test storage database initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            
            # Check that tables were created
            with sqlite3.connect(temp_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                assert 'lessons' in tables
                assert 'progress_entries' in tables
                assert 'lesson_queue' in tables
                assert 'sync_metadata' in tables
    
    def test_lesson_storage_and_retrieval(self):
        """Test storing and retrieving lessons"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            
            # Create test lesson
            lesson = LessonContent(
                lesson_id="storage_test_001",
                title="Storage Test Lesson",
                subject="Mathematics",
                grade_level=4,
                text_content="Test lesson content for storage.",
                key_concepts=["storage", "testing"],
                learning_objectives=["Test storage functionality"]
            )
            
            # Store lesson
            success = storage.store_lesson(lesson)
            assert success is True
            
            # Retrieve lesson
            retrieved_lesson = storage.get_lesson("storage_test_001")
            assert retrieved_lesson is not None
            assert retrieved_lesson.lesson_id == lesson.lesson_id
            assert retrieved_lesson.title == lesson.title
            assert retrieved_lesson.text_content == lesson.text_content
    
    def test_progress_entry_storage(self):
        """Test storing progress entries"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            
            # Create test progress entry
            progress_entry = ProgressEntry(
                student_id="test_student",
                lesson_id="test_lesson",
                timestamp=datetime.now(),
                interaction_type="test_interaction",
                data={"test": "data"}
            )
            
            # Store progress entry
            success = storage.store_progress(progress_entry)
            assert success is True
            
            # Retrieve pending sync entries
            pending_entries = storage.get_pending_sync_entries()
            assert len(pending_entries) == 1
            assert pending_entries[0].student_id == "test_student"
    
    def test_available_lessons_filtering(self):
        """Test filtering available lessons by grade and subject"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            
            # Store lessons with different grades and subjects
            lessons = [
                LessonContent(
                    lesson_id="math_grade3",
                    title="Math Grade 3",
                    subject="Mathematics",
                    grade_level=3,
                    text_content="Grade 3 math content",
                    key_concepts=["math"],
                    learning_objectives=["learn math"]
                ),
                LessonContent(
                    lesson_id="science_grade4",
                    title="Science Grade 4",
                    subject="Science",
                    grade_level=4,
                    text_content="Grade 4 science content",
                    key_concepts=["science"],
                    learning_objectives=["learn science"]
                ),
                LessonContent(
                    lesson_id="math_grade5",
                    title="Math Grade 5",
                    subject="Mathematics",
                    grade_level=5,
                    text_content="Grade 5 math content",
                    key_concepts=["math"],
                    learning_objectives=["learn advanced math"]
                )
            ]
            
            for lesson in lessons:
                storage.store_lesson(lesson)
            
            # Test filtering by grade
            grade4_lessons = storage.get_available_lessons(student_grade=4)
            grade4_lesson_ids = [lesson['lesson_id'] for lesson in grade4_lessons]
            assert "math_grade3" in grade4_lesson_ids  # Should include grade 3 (lower)
            assert "science_grade4" in grade4_lesson_ids  # Should include grade 4 (same)
            assert "math_grade5" not in grade4_lesson_ids  # Should not include grade 5 (higher)
            
            # Test filtering by subject
            math_lessons = storage.get_available_lessons(subject="Mathematics")
            math_lesson_ids = [lesson['lesson_id'] for lesson in math_lessons]
            assert "math_grade3" in math_lesson_ids
            assert "math_grade5" in math_lesson_ids
            assert "science_grade4" not in math_lesson_ids


class TestProgressSyncManager:
    """Test ProgressSyncManager class"""
    
    def test_sync_manager_initialization(self):
        """Test sync manager initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            sync_manager = ProgressSyncManager(storage)
            
            assert sync_manager.storage == storage
            assert sync_manager.sync_in_progress is False
    
    @patch('offline_learning.requests.post')
    def test_successful_sync(self, mock_post):
        """Test successful progress synchronization"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            sync_manager = ProgressSyncManager(storage)
            
            # Add a progress entry to sync
            progress_entry = ProgressEntry(
                student_id="sync_test_student",
                lesson_id="sync_test_lesson",
                timestamp=datetime.now(),
                interaction_type="test_sync",
                data={"test": "sync_data"}
            )
            storage.store_progress(progress_entry)
            
            # Perform sync
            successful, failed = sync_manager.sync_progress_data()
            
            assert successful == 1
            assert failed == 0
    
    @patch('offline_learning.requests.post')
    def test_failed_sync_with_retry(self, mock_post):
        """Test failed sync with retry mechanism"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            sync_manager = ProgressSyncManager(storage)
            
            # Add a progress entry to sync
            progress_entry = ProgressEntry(
                student_id="sync_fail_student",
                lesson_id="sync_fail_lesson",
                timestamp=datetime.now(),
                interaction_type="test_fail_sync",
                data={"test": "fail_sync_data"}
            )
            storage.store_progress(progress_entry)
            
            # Perform sync (should fail)
            successful, failed = sync_manager.sync_progress_data()
            
            assert successful == 0
            assert failed == 1


class TestLessonQueue:
    """Test LessonQueue class"""
    
    def test_lesson_queue_initialization(self):
        """Test lesson queue initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            bandwidth_estimator = BandwidthEstimator()
            lesson_queue = LessonQueue(storage, bandwidth_estimator)
            
            assert lesson_queue.storage == storage
            assert lesson_queue.bandwidth_estimator == bandwidth_estimator
            assert lesson_queue.download_in_progress is False
    
    def test_queue_lesson(self):
        """Test queuing lessons for download"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            bandwidth_estimator = BandwidthEstimator()
            lesson_queue = LessonQueue(storage, bandwidth_estimator)
            
            # Queue a lesson
            success = lesson_queue.queue_lesson(
                "test_student", "test_lesson_queue", 
                priority=8, requested_quality=ContentQuality.HIGH
            )
            
            assert success is True
            
            # Check that lesson was queued in database
            with sqlite3.connect(temp_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM lesson_queue WHERE lesson_id = ?", ("test_lesson_queue",))
                row = cursor.fetchone()
                assert row is not None
    
    @patch('offline_learning.requests.get')
    def test_lesson_download(self, mock_get):
        """Test downloading lessons from queue"""
        # Mock successful lesson download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "lesson_id": "download_test_lesson",
            "title": "Downloaded Lesson",
            "subject": "Test Subject",
            "grade_level": 3,
            "text_content": "Downloaded lesson content",
            "key_concepts": ["download", "test"],
            "learning_objectives": ["test download functionality"]
        }
        mock_get.return_value = mock_response
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            bandwidth_estimator = BandwidthEstimator()
            lesson_queue = LessonQueue(storage, bandwidth_estimator)
            
            # Queue a lesson
            lesson_queue.queue_lesson("test_student", "download_test_lesson", priority=5)
            
            # Process download queue
            successful, failed = lesson_queue.process_download_queue()
            
            assert successful == 1
            assert failed == 0
            
            # Verify lesson was stored
            downloaded_lesson = storage.get_lesson("download_test_lesson")
            assert downloaded_lesson is not None
            assert downloaded_lesson.title == "Downloaded Lesson"


class TestPowerOutageHandler:
    """Test PowerOutageHandler class"""
    
    def test_power_outage_handler_initialization(self):
        """Test power outage handler initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            handler = PowerOutageHandler(storage, auto_save_interval=1)  # 1 second for testing
            
            assert handler.storage == storage
            assert handler.auto_save_interval == 1
            assert len(handler.pending_progress) == 0
            
            # Cleanup
            handler.shutdown()
    
    def test_interaction_recording_and_auto_save(self):
        """Test recording interactions and auto-save functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            handler = PowerOutageHandler(storage, auto_save_interval=1)
            
            # Record an interaction
            handler.record_interaction(
                "auto_save_student", "auto_save_lesson",
                "test_interaction", {"test": "auto_save_data"}
            )
            
            assert len(handler.pending_progress) == 1
            
            # Wait for auto-save (should trigger after 1 second)
            time.sleep(2)
            
            assert len(handler.pending_progress) == 0  # Should be saved and cleared
            
            # Verify data was saved
            pending_entries = storage.get_pending_sync_entries()
            assert len(pending_entries) >= 1
            
            # Cleanup
            handler.shutdown()
    
    def test_force_save(self):
        """Test force save functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            handler = PowerOutageHandler(storage)
            
            # Record multiple interactions
            for i in range(3):
                handler.record_interaction(
                    f"force_save_student_{i}", "force_save_lesson",
                    "test_interaction", {"test": f"force_save_data_{i}"}
                )
            
            assert len(handler.pending_progress) == 3
            
            # Force save
            handler.force_save()
            
            assert len(handler.pending_progress) == 0
            
            # Verify all data was saved
            pending_entries = storage.get_pending_sync_entries()
            assert len(pending_entries) >= 3
            
            # Cleanup
            handler.shutdown()
    
    def test_force_save_on_many_entries(self):
        """Test automatic force save when many entries are pending"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            storage = OfflineStorage(temp_db.name)
            handler = PowerOutageHandler(storage)
            
            # Record many interactions (should trigger force save at 10)
            for i in range(12):
                handler.record_interaction(
                    "many_entries_student", "many_entries_lesson",
                    "test_interaction", {"test": f"data_{i}"}
                )
                
                # Should force save after 10 entries
                if i >= 9:  # After adding 10 entries (0-9)
                    assert len(handler.pending_progress) <= 2  # Should have been saved
            
            # Cleanup
            handler.shutdown()


class TestOfflineLearningSystem:
    """Test main OfflineLearningSystem integration"""
    
    def test_system_initialization(self):
        """Test offline learning system initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            system = OfflineLearningSystem(db_path=temp_db.name)
            
            assert system.storage is not None
            assert system.bandwidth_estimator is not None
            assert system.sync_manager is not None
            assert system.lesson_queue is not None
            assert system.power_outage_handler is not None
            
            # Cleanup
            system.shutdown()
    
    def test_lesson_retrieval_and_adaptation(self):
        """Test lesson retrieval with quality adaptation"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            system = OfflineLearningSystem(db_path=temp_db.name)
            
            # Store a high-quality lesson
            lesson = LessonContent(
                lesson_id="adaptation_test",
                title="Adaptation Test Lesson",
                subject="Science",
                grade_level=4,
                text_content="Full lesson content with details.",
                key_concepts=["adaptation", "quality"],
                learning_objectives=["test adaptation"],
                audio_content="audio_data",
                images=[{"description": "test image", "data": "image_data"}],
                animations=["animation1", "animation2"],
                exercises=[{"type": "quiz", "question": "Test?"}],
                quiz_questions=[{"question": "What is adaptation?"}],
                content_quality=ContentQuality.HIGH
            )
            
            system.storage.store_lesson(lesson)
            
            # Simulate slow connection
            system.bandwidth_estimator.current_status = ConnectionStatus.SLOW
            
            # Retrieve lesson (should be adapted to lower quality)
            retrieved_lesson = system.get_lesson("adaptation_test")
            
            assert retrieved_lesson is not None
            assert retrieved_lesson.lesson_id == "adaptation_test"
            # Should have been adapted - check that content quality considerations were applied
            assert retrieved_lesson.audio_content is not None  # Should still have audio for SLOW
            
            # Cleanup
            system.shutdown()
    
    def test_learning_interaction_recording(self):
        """Test recording learning interactions"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            system = OfflineLearningSystem(db_path=temp_db.name)
            
            # Record a learning interaction
            system.record_learning_interaction(
                "interaction_test_student", "interaction_test_lesson",
                "lesson_completed", {"score": 90, "time_spent": 600}
            )
            
            # Wait a moment for auto-save
            time.sleep(1)
            
            # Force save to ensure data is persisted
            system.power_outage_handler.force_save()
            
            # Verify interaction was recorded
            pending_entries = system.storage.get_pending_sync_entries()
            assert len(pending_entries) >= 1
            
            interaction_entry = next(
                (entry for entry in pending_entries if entry.student_id == "interaction_test_student"), 
                None
            )
            assert interaction_entry is not None
            assert interaction_entry.interaction_type == "lesson_completed"
            assert interaction_entry.data["score"] == 90
            
            # Cleanup
            system.shutdown()
    
    def test_lesson_queuing(self):
        """Test lesson queuing functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            system = OfflineLearningSystem(db_path=temp_db.name)
            
            # Queue a lesson
            success = system.queue_lesson_for_download("queue_test_student", "queue_test_lesson", priority=7)
            assert success is True
            
            # Verify lesson was queued in database
            with sqlite3.connect(temp_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM lesson_queue WHERE lesson_id = ?", ("queue_test_lesson",))
                row = cursor.fetchone()
                assert row is not None
            
            # Cleanup
            system.shutdown()
    
    def test_system_status_reporting(self):
        """Test system status reporting functionality"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            system = OfflineLearningSystem(db_path=temp_db.name)
            
            # Get connection status
            connection_status, bandwidth = system.get_connection_status()
            assert connection_status in [status for status in ConnectionStatus]
            assert isinstance(bandwidth, (int, float))
            
            # Get sync status
            sync_status = system.get_sync_status()
            assert 'pending_sync_entries' in sync_status
            assert 'sync_in_progress' in sync_status
            assert 'connection_status' in sync_status
            
            # Cleanup
            system.shutdown()
    
    def test_available_lessons_retrieval(self):
        """Test retrieving available lessons"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            system = OfflineLearningSystem(db_path=temp_db.name)
            
            # Store some test lessons
            lessons = [
                LessonContent(
                    lesson_id="available_math",
                    title="Available Math Lesson",
                    subject="Mathematics",
                    grade_level=3,
                    text_content="Math content",
                    key_concepts=["math"],
                    learning_objectives=["learn math"]
                ),
                LessonContent(
                    lesson_id="available_science",
                    title="Available Science Lesson", 
                    subject="Science",
                    grade_level=4,
                    text_content="Science content",
                    key_concepts=["science"],
                    learning_objectives=["learn science"]
                )
            ]
            
            for lesson in lessons:
                system.storage.store_lesson(lesson)
            
            # Get all available lessons
            available_lessons = system.get_available_lessons()
            assert len(available_lessons) == 2
            
            # Get filtered lessons
            math_lessons = system.get_available_lessons(subject="Mathematics")
            assert len(math_lessons) == 1
            assert math_lessons[0]["lesson_id"] == "available_math"
            
            # Cleanup
            system.shutdown()


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])