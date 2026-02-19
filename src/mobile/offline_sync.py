"""
Offline Synchronization Manager for EduAGI Mobile.

Handles offline data sync, conflict resolution, and priority-based synchronization
for mobile users with intermittent connectivity.
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import sqlite3
from pathlib import Path


class SyncStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncPriority(Enum):
    CRITICAL = 1    # User progress, scores, authentication
    HIGH = 2        # Lesson completions, quiz responses
    MEDIUM = 3      # Study notes, bookmarks
    LOW = 4         # Analytics, optional metadata


@dataclass
class SyncEntity:
    """Represents a data entity that needs synchronization."""
    entity_id: str
    entity_type: str  # progress, lesson, user_data, etc.
    data: Dict[str, Any]
    priority: SyncPriority
    last_modified: datetime
    version: int = 1
    checksum: str = field(default="")
    sync_status: SyncStatus = SyncStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate checksum for conflict detection."""
        data_str = json.dumps(self.data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(f"{data_str}_{self.version}".encode()).hexdigest()


@dataclass
class ConflictResolution:
    """Represents a sync conflict and its resolution."""
    entity_id: str
    local_version: int
    remote_version: int  
    local_checksum: str
    remote_checksum: str
    resolution_strategy: str  # "local_wins", "remote_wins", "merge", "manual"
    resolved_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SyncStats:
    """Statistics for sync operations."""
    entities_synced: int = 0
    conflicts_resolved: int = 0
    bytes_transferred: int = 0
    last_sync: Optional[datetime] = None
    sync_duration: float = 0.0
    errors: List[str] = field(default_factory=list)


class OfflineSyncManager:
    """
    Manages offline synchronization for mobile EduAGI clients.
    
    Features:
    - Conflict resolution with multiple strategies
    - Delta synchronization (only changes)
    - Priority-based sync queues
    - Background sync scheduling
    - Storage quota management
    - Per-entity sync status tracking
    """

    def __init__(self, storage_path: str = "./mobile_sync.db", max_storage_mb: int = 100):
        self.storage_path = Path(storage_path)
        self.max_storage_bytes = max_storage_mb * 1024 * 1024
        self.sync_queue: Dict[SyncPriority, List[SyncEntity]] = {
            priority: [] for priority in SyncPriority
        }
        self.conflict_log: List[ConflictResolution] = []
        self.entity_states: Dict[str, SyncEntity] = {}
        self.sync_stats = SyncStats()
        self.background_sync_enabled = True
        self.sync_interval = 300  # 5 minutes
        self._init_storage()

    def _init_storage(self):
        """Initialize local SQLite storage for offline data."""
        self.storage_path.parent.mkdir(exist_ok=True)
        
        with sqlite3.connect(self.storage_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sync_entities (
                    entity_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    last_modified TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    checksum TEXT NOT NULL,
                    sync_status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0
                );
                
                CREATE TABLE IF NOT EXISTS conflict_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    local_version INTEGER,
                    remote_version INTEGER,
                    resolution_strategy TEXT,
                    timestamp TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_entity_type ON sync_entities(entity_type);
                CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_entities(sync_status);
                CREATE INDEX IF NOT EXISTS idx_priority ON sync_entities(priority);
            """)

    async def add_entity(self, entity: SyncEntity):
        """Add an entity to the sync queue."""
        self.entity_states[entity.entity_id] = entity
        self.sync_queue[entity.priority].append(entity)
        
        # Persist to storage
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO sync_entities 
                (entity_id, entity_type, data, priority, last_modified, version, checksum, sync_status, retry_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity.entity_id, entity.entity_type, json.dumps(entity.data),
                entity.priority.value, entity.last_modified.isoformat(), entity.version,
                entity.checksum, entity.sync_status.value, entity.retry_count
            ))

    async def sync_entity(self, entity: SyncEntity) -> bool:
        """
        Synchronize a single entity with the remote server.
        
        Returns:
            bool: True if sync succeeded, False otherwise
        """
        try:
            entity.sync_status = SyncStatus.IN_PROGRESS
            
            # Simulate API call to get remote version
            remote_data = await self._fetch_remote_entity(entity.entity_id, entity.entity_type)
            
            if remote_data:
                # Check for conflicts
                remote_checksum = self._calculate_entity_checksum(remote_data)
                if remote_checksum != entity.checksum:
                    # Conflict detected
                    return await self._resolve_conflict(entity, remote_data)
            
            # No conflict, proceed with sync
            success = await self._push_to_remote(entity)
            
            if success:
                entity.sync_status = SyncStatus.COMPLETED
                entity.retry_count = 0
                self.sync_stats.entities_synced += 1
            else:
                entity.sync_status = SyncStatus.FAILED
                entity.retry_count += 1
                
            await self._update_entity_storage(entity)
            return success
            
        except Exception as e:
            entity.sync_status = SyncStatus.FAILED
            entity.retry_count += 1
            self.sync_stats.errors.append(str(e))
            await self._update_entity_storage(entity)
            return False

    async def _resolve_conflict(self, local_entity: SyncEntity, remote_data: Dict[str, Any]) -> bool:
        """
        Resolve sync conflicts using last-write-wins with merge capability.
        
        Args:
            local_entity: Local version of the entity
            remote_data: Remote version data
            
        Returns:
            bool: True if conflict resolved and synced
        """
        remote_modified = datetime.fromisoformat(remote_data.get('last_modified', datetime.utcnow().isoformat()))
        
        conflict = ConflictResolution(
            entity_id=local_entity.entity_id,
            local_version=local_entity.version,
            remote_version=remote_data.get('version', 1),
            local_checksum=local_entity.checksum,
            remote_checksum=self._calculate_entity_checksum(remote_data)
        )
        
        # Apply conflict resolution strategy
        if local_entity.entity_type in ['user_progress', 'quiz_score']:
            # Critical data: Use merge strategy
            conflict.resolution_strategy = "merge"
            merged_data = self._merge_entity_data(local_entity.data, remote_data)
            conflict.resolved_data = merged_data
            local_entity.data = merged_data
        elif local_entity.last_modified > remote_modified:
            # Local is newer: local wins
            conflict.resolution_strategy = "local_wins"  
            conflict.resolved_data = local_entity.data
        else:
            # Remote is newer: remote wins
            conflict.resolution_strategy = "remote_wins"
            conflict.resolved_data = remote_data
            local_entity.data = remote_data
            local_entity.version = remote_data.get('version', local_entity.version)
            
        # Update entity
        local_entity.version += 1
        local_entity.checksum = local_entity._calculate_checksum()
        local_entity.sync_status = SyncStatus.CONFLICT
        
        # Log conflict
        self.conflict_log.append(conflict)
        self.sync_stats.conflicts_resolved += 1
        
        # Try to sync resolved version
        return await self._push_to_remote(local_entity)

    def _merge_entity_data(self, local_data: Dict[str, Any], remote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge local and remote data for conflict resolution.
        
        Strategy: Take the maximum values for numeric fields (progress, scores),
        merge arrays, and prefer local for string fields unless empty.
        """
        merged = local_data.copy()
        
        for key, remote_value in remote_data.items():
            if key not in merged:
                merged[key] = remote_value
            elif isinstance(remote_value, (int, float)) and isinstance(merged[key], (int, float)):
                # Take maximum for numeric values (progress, scores)
                merged[key] = max(merged[key], remote_value)
            elif isinstance(remote_value, list) and isinstance(merged[key], list):
                # Merge arrays (unique values)
                merged[key] = list(set(merged[key] + remote_value))
            elif isinstance(remote_value, str) and not merged[key]:
                # Use remote string if local is empty
                merged[key] = remote_value
                
        return merged

    async def sync_by_priority(self, max_entities: int = 50) -> SyncStats:
        """
        Sync entities by priority order.
        
        Args:
            max_entities: Maximum entities to sync in this batch
            
        Returns:
            SyncStats: Statistics for this sync operation
        """
        start_time = time.time()
        synced_count = 0
        
        # Process by priority order
        for priority in [SyncPriority.CRITICAL, SyncPriority.HIGH, SyncPriority.MEDIUM, SyncPriority.LOW]:
            if synced_count >= max_entities:
                break
                
            queue = self.sync_queue[priority]
            entities_to_sync = [e for e in queue if e.sync_status in [SyncStatus.PENDING, SyncStatus.FAILED] 
                              and e.retry_count < e.max_retries]
            
            for entity in entities_to_sync[:max_entities - synced_count]:
                success = await self.sync_entity(entity)
                if success:
                    queue.remove(entity)
                synced_count += 1

        self.sync_stats.sync_duration = time.time() - start_time
        self.sync_stats.last_sync = datetime.utcnow()
        return self.sync_stats

    async def get_delta_changes(self, entity_type: str, since: datetime) -> List[SyncEntity]:
        """
        Get only the entities that changed since the last sync.
        
        Args:
            entity_type: Type of entities to check
            since: Only include changes after this timestamp
            
        Returns:
            List of entities that have changes
        """
        changes = []
        
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("""
                SELECT entity_id, entity_type, data, priority, last_modified, version, checksum, sync_status, retry_count
                FROM sync_entities 
                WHERE entity_type = ? AND last_modified > ?
                ORDER BY priority, last_modified DESC
            """, (entity_type, since.isoformat()))
            
            for row in cursor.fetchall():
                entity = SyncEntity(
                    entity_id=row[0],
                    entity_type=row[1], 
                    data=json.loads(row[2]),
                    priority=SyncPriority(row[3]),
                    last_modified=datetime.fromisoformat(row[4]),
                    version=row[5],
                    checksum=row[6],
                    sync_status=SyncStatus(row[7]),
                    retry_count=row[8]
                )
                changes.append(entity)
                
        return changes

    async def schedule_background_sync(self):
        """Schedule background synchronization."""
        while self.background_sync_enabled:
            try:
                await self.sync_by_priority(max_entities=20)
                await self._cleanup_storage()
            except Exception as e:
                self.sync_stats.errors.append(f"Background sync error: {str(e)}")
                
            await asyncio.sleep(self.sync_interval)

    def get_sync_status_by_type(self, entity_type: str) -> Dict[SyncStatus, int]:
        """Get sync status summary for an entity type."""
        status_counts = {status: 0 for status in SyncStatus}
        
        with sqlite3.connect(self.storage_path) as conn:
            cursor = conn.execute("""
                SELECT sync_status, COUNT(*) 
                FROM sync_entities 
                WHERE entity_type = ? 
                GROUP BY sync_status
            """, (entity_type,))
            
            for status, count in cursor.fetchall():
                status_counts[SyncStatus(status)] = count
                
        return status_counts

    async def _cleanup_storage(self):
        """Clean up storage to stay within quota limits."""
        current_size = self.storage_path.stat().st_size if self.storage_path.exists() else 0
        
        if current_size > self.max_storage_bytes:
            # Delete oldest completed sync entities
            with sqlite3.connect(self.storage_path) as conn:
                conn.execute("""
                    DELETE FROM sync_entities 
                    WHERE sync_status = 'completed' 
                    AND entity_id IN (
                        SELECT entity_id FROM sync_entities 
                        WHERE sync_status = 'completed' 
                        ORDER BY last_modified ASC 
                        LIMIT 1000
                    )
                """)

    def _calculate_entity_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for entity data."""
        data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.md5(data_str.encode()).hexdigest()

    async def _fetch_remote_entity(self, entity_id: str, entity_type: str) -> Optional[Dict[str, Any]]:
        """Simulate fetching entity from remote server."""
        # This would be replaced with actual API call
        await asyncio.sleep(0.1)  # Simulate network delay
        return None  # No remote data found

    async def _push_to_remote(self, entity: SyncEntity) -> bool:
        """Simulate pushing entity to remote server."""
        # This would be replaced with actual API call
        await asyncio.sleep(0.1)  # Simulate network delay
        return True  # Simulate success

    async def _update_entity_storage(self, entity: SyncEntity):
        """Update entity in local storage."""
        with sqlite3.connect(self.storage_path) as conn:
            conn.execute("""
                UPDATE sync_entities 
                SET data = ?, sync_status = ?, retry_count = ?, checksum = ?
                WHERE entity_id = ?
            """, (
                json.dumps(entity.data), entity.sync_status.value, 
                entity.retry_count, entity.checksum, entity.entity_id
            ))

    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage quota and usage information."""
        current_size = self.storage_path.stat().st_size if self.storage_path.exists() else 0
        
        return {
            "current_size_bytes": current_size,
            "max_size_bytes": self.max_storage_bytes,
            "usage_percent": (current_size / self.max_storage_bytes) * 100,
            "entities_count": len(self.entity_states),
            "pending_sync": sum(len(queue) for queue in self.sync_queue.values())
        }