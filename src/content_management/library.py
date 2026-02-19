"""
Content Library - Central repository for educational content

This module provides the ContentLibrary class that manages all educational content
including lessons, quizzes, flashcards, and other learning materials.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, asdict, field
import hashlib
import logging

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of educational content supported"""
    LESSON = "lesson"
    QUIZ = "quiz" 
    FLASHCARD = "flashcard"
    AUDIO_LESSON = "audio_lesson"
    WORKSHEET = "worksheet"
    VIDEO = "video"


class DifficultyLevel(Enum):
    """Content difficulty levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class ContentMetadata:
    """Metadata for educational content"""
    content_id: str
    title: str
    content_type: ContentType
    subject: str
    grade: Union[int, str]
    topic: str
    difficulty: DifficultyLevel
    language: str = "en"
    duration: Optional[int] = None  # in minutes
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    tags: Set[str] = field(default_factory=set)
    author: Optional[str] = None
    quality_score: float = 0.0
    usage_count: int = 0
    rating: float = 0.0
    rating_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['content_type'] = self.content_type.value
        data['difficulty'] = self.difficulty.value
        data['tags'] = list(self.tags)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentMetadata':
        """Create from dictionary"""
        data = data.copy()
        data['content_type'] = ContentType(data['content_type'])
        data['difficulty'] = DifficultyLevel(data['difficulty'])
        data['tags'] = set(data.get('tags', []))
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


@dataclass
class ContentVersion:
    """Content version information"""
    version: int
    content_hash: str
    created_at: datetime
    changes: str
    author: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat(),
            'changes': self.changes,
            'author': self.author
        }


@dataclass
class ContentItem:
    """Complete content item with metadata and data"""
    metadata: ContentMetadata
    content_data: Dict[str, Any]
    versions: List[ContentVersion] = field(default_factory=list)
    
    def get_content_hash(self) -> str:
        """Generate hash of content data"""
        content_str = json.dumps(self.content_data, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()


class ContentLibrary:
    """Central repository for educational content"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize content library
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.storage_path = storage_path
        self._content: Dict[str, ContentItem] = {}
        self._index_by_subject: Dict[str, Set[str]] = {}
        self._index_by_grade: Dict[Union[int, str], Set[str]] = {}
        self._index_by_topic: Dict[str, Set[str]] = {}
        self._index_by_type: Dict[ContentType, Set[str]] = {}
        self._index_by_tags: Dict[str, Set[str]] = {}
        
        # Load existing content if storage path provided
        if storage_path:
            self._load_from_storage()
    
    def add_content(self, 
                    title: str,
                    content_type: ContentType,
                    subject: str,
                    grade: Union[int, str],
                    topic: str,
                    content_data: Dict[str, Any],
                    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
                    language: str = "en",
                    duration: Optional[int] = None,
                    tags: Optional[Set[str]] = None,
                    author: Optional[str] = None) -> str:
        """
        Add new content to the library
        
        Returns:
            content_id: Unique identifier for the content
        """
        content_id = str(uuid.uuid4())
        
        metadata = ContentMetadata(
            content_id=content_id,
            title=title,
            content_type=content_type,
            subject=subject,
            grade=grade,
            topic=topic,
            difficulty=difficulty,
            language=language,
            duration=duration,
            tags=tags or set(),
            author=author
        )
        
        content_item = ContentItem(
            metadata=metadata,
            content_data=content_data
        )
        
        # Create initial version
        content_hash = content_item.get_content_hash()
        initial_version = ContentVersion(
            version=1,
            content_hash=content_hash,
            created_at=datetime.now(),
            changes="Initial version",
            author=author
        )
        content_item.versions.append(initial_version)
        
        # Store content
        self._content[content_id] = content_item
        
        # Update indices
        self._update_indices(content_id, metadata)
        
        # Save to storage
        self._save_to_storage()
        
        logger.info(f"Added content: {title} ({content_id})")
        return content_id
    
    def update_content(self, 
                      content_id: str, 
                      content_data: Optional[Dict[str, Any]] = None,
                      metadata_updates: Optional[Dict[str, Any]] = None,
                      changes: str = "Content updated",
                      author: Optional[str] = None) -> bool:
        """
        Update existing content
        
        Args:
            content_id: ID of content to update
            content_data: New content data (if updating content)
            metadata_updates: Metadata fields to update
            changes: Description of changes
            author: Author of changes
            
        Returns:
            True if update successful, False if content not found
        """
        if content_id not in self._content:
            logger.warning(f"Content not found: {content_id}")
            return False
        
        content_item = self._content[content_id]
        old_metadata = content_item.metadata
        
        # Update metadata if provided
        if metadata_updates:
            for key, value in metadata_updates.items():
                if hasattr(content_item.metadata, key):
                    setattr(content_item.metadata, key, value)
            content_item.metadata.updated_at = datetime.now()
        
        # Update content data if provided
        if content_data:
            content_item.content_data = content_data
            content_item.metadata.version += 1
            content_item.metadata.updated_at = datetime.now()
            
            # Create new version
            content_hash = content_item.get_content_hash()
            new_version = ContentVersion(
                version=content_item.metadata.version,
                content_hash=content_hash,
                created_at=datetime.now(),
                changes=changes,
                author=author
            )
            content_item.versions.append(new_version)
        
        # Update indices if metadata changed
        if metadata_updates:
            self._remove_from_indices(content_id, old_metadata)
            self._update_indices(content_id, content_item.metadata)
        
        # Save to storage
        self._save_to_storage()
        
        logger.info(f"Updated content: {content_id}")
        return True
    
    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """Get content by ID"""
        return self._content.get(content_id)
    
    def delete_content(self, content_id: str) -> bool:
        """Delete content from library"""
        if content_id not in self._content:
            return False
        
        content_item = self._content[content_id]
        self._remove_from_indices(content_id, content_item.metadata)
        del self._content[content_id]
        
        # Save to storage
        self._save_to_storage()
        
        logger.info(f"Deleted content: {content_id}")
        return True
    
    def search_content(self, 
                      subject: Optional[str] = None,
                      grade: Optional[Union[int, str]] = None,
                      topic: Optional[str] = None,
                      content_type: Optional[ContentType] = None,
                      difficulty: Optional[DifficultyLevel] = None,
                      language: Optional[str] = None,
                      tags: Optional[Set[str]] = None,
                      min_quality_score: Optional[float] = None,
                      limit: Optional[int] = None) -> List[ContentItem]:
        """
        Search content with filters
        
        Returns:
            List of matching content items
        """
        # Start with all content IDs
        result_ids = set(self._content.keys())
        
        # Apply filters
        if subject:
            result_ids &= self._index_by_subject.get(subject, set())
        
        if grade is not None:
            result_ids &= self._index_by_grade.get(grade, set())
        
        if topic:
            result_ids &= self._index_by_topic.get(topic, set())
        
        if content_type:
            result_ids &= self._index_by_type.get(content_type, set())
        
        if tags:
            for tag in tags:
                result_ids &= self._index_by_tags.get(tag, set())
        
        # Filter by additional criteria
        results = []
        for content_id in result_ids:
            content_item = self._content[content_id]
            metadata = content_item.metadata
            
            # Check difficulty
            if difficulty and metadata.difficulty != difficulty:
                continue
            
            # Check language
            if language and metadata.language != language:
                continue
                
            # Check quality score
            if min_quality_score and metadata.quality_score < min_quality_score:
                continue
            
            results.append(content_item)
        
        # Sort by quality score (descending) then by rating
        results.sort(key=lambda x: (x.metadata.quality_score, x.metadata.rating), reverse=True)
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    def get_popular_content(self, limit: int = 10) -> List[ContentItem]:
        """Get most popular content by usage count"""
        all_content = list(self._content.values())
        all_content.sort(key=lambda x: x.metadata.usage_count, reverse=True)
        return all_content[:limit]
    
    def get_top_rated_content(self, limit: int = 10) -> List[ContentItem]:
        """Get top rated content"""
        # Only include content with at least 3 ratings
        rated_content = [c for c in self._content.values() if c.metadata.rating_count >= 3]
        rated_content.sort(key=lambda x: x.metadata.rating, reverse=True)
        return rated_content[:limit]
    
    def add_rating(self, content_id: str, rating: float) -> bool:
        """Add a rating to content (1.0 to 5.0)"""
        if content_id not in self._content or not 1.0 <= rating <= 5.0:
            return False
        
        content_item = self._content[content_id]
        metadata = content_item.metadata
        
        # Update rating using running average
        total_rating = metadata.rating * metadata.rating_count + rating
        metadata.rating_count += 1
        metadata.rating = total_rating / metadata.rating_count
        
        # Save to storage
        self._save_to_storage()
        return True
    
    def increment_usage(self, content_id: str) -> bool:
        """Increment usage count for content"""
        if content_id not in self._content:
            return False
        
        self._content[content_id].metadata.usage_count += 1
        self._save_to_storage()
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get library statistics"""
        total_content = len(self._content)
        type_counts = {}
        subject_counts = {}
        grade_counts = {}
        
        for content_item in self._content.values():
            metadata = content_item.metadata
            
            # Count by type
            type_name = metadata.content_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            # Count by subject
            subject_counts[metadata.subject] = subject_counts.get(metadata.subject, 0) + 1
            
            # Count by grade
            grade_key = str(metadata.grade)
            grade_counts[grade_key] = grade_counts.get(grade_key, 0) + 1
        
        return {
            'total_content': total_content,
            'content_by_type': type_counts,
            'content_by_subject': subject_counts,
            'content_by_grade': grade_counts,
            'total_usage': sum(c.metadata.usage_count for c in self._content.values()),
            'average_rating': sum(c.metadata.rating for c in self._content.values()) / max(total_content, 1)
        }
    
    def _update_indices(self, content_id: str, metadata: ContentMetadata):
        """Update search indices"""
        # Subject index
        if metadata.subject not in self._index_by_subject:
            self._index_by_subject[metadata.subject] = set()
        self._index_by_subject[metadata.subject].add(content_id)
        
        # Grade index
        if metadata.grade not in self._index_by_grade:
            self._index_by_grade[metadata.grade] = set()
        self._index_by_grade[metadata.grade].add(content_id)
        
        # Topic index
        if metadata.topic not in self._index_by_topic:
            self._index_by_topic[metadata.topic] = set()
        self._index_by_topic[metadata.topic].add(content_id)
        
        # Type index
        if metadata.content_type not in self._index_by_type:
            self._index_by_type[metadata.content_type] = set()
        self._index_by_type[metadata.content_type].add(content_id)
        
        # Tags index
        for tag in metadata.tags:
            if tag not in self._index_by_tags:
                self._index_by_tags[tag] = set()
            self._index_by_tags[tag].add(content_id)
    
    def _remove_from_indices(self, content_id: str, metadata: ContentMetadata):
        """Remove from search indices"""
        # Remove from all relevant indices
        for index in [self._index_by_subject.get(metadata.subject, set()),
                     self._index_by_grade.get(metadata.grade, set()),
                     self._index_by_topic.get(metadata.topic, set()),
                     self._index_by_type.get(metadata.content_type, set())]:
            index.discard(content_id)
        
        for tag in metadata.tags:
            if tag in self._index_by_tags:
                self._index_by_tags[tag].discard(content_id)
    
    def _save_to_storage(self):
        """Save library to storage (placeholder for actual implementation)"""
        if self.storage_path:
            logger.debug(f"Saving content library to {self.storage_path}")
            # TODO: Implement actual storage (JSON, database, etc.)
    
    def _load_from_storage(self):
        """Load library from storage (placeholder for actual implementation)"""
        logger.debug(f"Loading content library from {self.storage_path}")
        # TODO: Implement actual loading from storage