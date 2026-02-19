"""
Notification Engine - Central orchestrator for all notifications

This module contains the core NotificationEngine class that manages
event-driven notifications with intelligent scheduling, deduplication,
and user preference handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict
import json
import hashlib

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Supported notification event types"""
    LESSON_REMINDER = "lesson_reminder"
    STREAK_WARNING = "streak_warning"  
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    ASSESSMENT_DUE = "assessment_due"
    PARENT_REPORT = "parent_report"
    TEACHER_ALERT = "teacher_alert"
    SYSTEM_UPDATE = "system_update"


class Priority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class DeliveryChannel(Enum):
    """Available delivery channels"""
    PUSH = "push"
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"


@dataclass
class UserPreferences:
    """User notification preferences"""
    user_id: str
    enabled_events: Set[EventType] = field(default_factory=lambda: set(EventType))
    preferred_channels: Dict[EventType, List[DeliveryChannel]] = field(default_factory=dict)
    quiet_hours_start: time = field(default_factory=lambda: time(21, 0))  # 9 PM
    quiet_hours_end: time = field(default_factory=lambda: time(6, 0))    # 6 AM
    timezone: str = "UTC"
    language: str = "en"
    
    def allows_event(self, event_type: EventType) -> bool:
        """Check if user has enabled this event type"""
        return event_type in self.enabled_events
    
    def get_channels_for_event(self, event_type: EventType) -> List[DeliveryChannel]:
        """Get preferred delivery channels for an event type"""
        return self.preferred_channels.get(event_type, [DeliveryChannel.PUSH])
    
    def is_quiet_time(self, check_time: datetime) -> bool:
        """Check if given time falls within user's quiet hours"""
        current_time = check_time.time()
        
        # Handle cases where quiet hours cross midnight
        if self.quiet_hours_start <= self.quiet_hours_end:
            # Normal range (e.g., 9PM to 6AM next day)
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
        else:
            # Range within same day (e.g., 6AM to 9PM)
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end


@dataclass
class NotificationEvent:
    """Represents a notification event"""
    event_id: str
    event_type: EventType
    priority: Priority
    user_id: str
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    channels: List[DeliveryChannel] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "created_at": self.created_at.isoformat(),
            "channels": [c.value for c in self.channels]
        }


class NotificationEngine:
    """
    Central notification orchestrator that manages event processing,
    deduplication, user preferences, and quiet hours
    """
    
    def __init__(self, 
                 template_manager,
                 scheduler,
                 delivery_manager):
        self.template_manager = template_manager
        self.scheduler = scheduler
        self.delivery_manager = delivery_manager
        
        # User preferences storage (in production, this would be from database)
        self.user_preferences: Dict[str, UserPreferences] = {}
        
        # Deduplication tracking
        self.recent_notifications: Dict[str, Set[str]] = defaultdict(set)
        self.dedup_window = timedelta(hours=1)  # Don't send same notification within 1 hour
        
        # Event queue for processing
        self.event_queue: List[NotificationEvent] = []
        
        logger.info("NotificationEngine initialized")
    
    def set_user_preferences(self, user_id: str, preferences: UserPreferences):
        """Set notification preferences for a user"""
        self.user_preferences[user_id] = preferences
        logger.info(f"Updated preferences for user {user_id}")
    
    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get user preferences, creating defaults if not found"""
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(user_id=user_id)
        return self.user_preferences[user_id]
    
    def _generate_dedup_key(self, event: NotificationEvent) -> str:
        """Generate deduplication key for an event"""
        key_data = f"{event.user_id}:{event.event_type.value}:{event.title}:{event.message}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_duplicate(self, event: NotificationEvent) -> bool:
        """Check if this notification is a duplicate within the dedup window"""
        dedup_key = self._generate_dedup_key(event)
        
        # Clean old entries first
        cutoff_time = datetime.utcnow() - self.dedup_window
        for user_id, keys in list(self.recent_notifications.items()):
            # In a real implementation, we'd store timestamps with keys
            # For simplicity, we're using a basic set here
            pass
        
        if dedup_key in self.recent_notifications[event.user_id]:
            logger.info(f"Duplicate notification blocked for user {event.user_id}: {dedup_key}")
            return True
        
        self.recent_notifications[event.user_id].add(dedup_key)
        return False
    
    def _should_respect_quiet_hours(self, event: NotificationEvent) -> bool:
        """Check if quiet hours should be respected for this event"""
        # Urgent notifications always bypass quiet hours
        if event.priority == Priority.URGENT:
            return False
        
        # System updates bypass quiet hours
        if event.event_type == EventType.SYSTEM_UPDATE:
            return False
            
        return True
    
    async def submit_event(self, event: NotificationEvent) -> bool:
        """
        Submit a notification event for processing
        Returns True if event was accepted, False if rejected
        """
        try:
            logger.info(f"Processing event {event.event_id} for user {event.user_id}")
            
            # Get user preferences
            preferences = self.get_user_preferences(event.user_id)
            
            # Check if user has enabled this event type
            if not preferences.allows_event(event.event_type):
                logger.info(f"Event {event.event_type.value} disabled for user {event.user_id}")
                return False
            
            # Check for duplicates
            if self._is_duplicate(event):
                return False
            
            # Check quiet hours
            current_time = datetime.utcnow()
            if (self._should_respect_quiet_hours(event) and 
                preferences.is_quiet_time(current_time)):
                
                # Schedule for after quiet hours instead of dropping
                next_active_time = self._calculate_next_active_time(preferences, current_time)
                event.scheduled_at = next_active_time
                logger.info(f"Event scheduled for after quiet hours: {next_active_time}")
            
            # Set delivery channels based on user preferences
            if not event.channels:
                event.channels = preferences.get_channels_for_event(event.event_type)
            
            # Add to queue for processing
            self.event_queue.append(event)
            
            # Process immediately or schedule
            if event.scheduled_at is None or event.scheduled_at <= current_time:
                await self._process_event_now(event)
            else:
                await self.scheduler.schedule_notification(event)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            return False
    
    def _calculate_next_active_time(self, preferences: UserPreferences, 
                                   current_time: datetime) -> datetime:
        """Calculate next time outside quiet hours"""
        # Simple implementation - schedule for quiet_hours_end tomorrow
        tomorrow = current_time.replace(hour=preferences.quiet_hours_end.hour,
                                       minute=preferences.quiet_hours_end.minute,
                                       second=0, microsecond=0)
        if tomorrow <= current_time:
            tomorrow += timedelta(days=1)
        return tomorrow
    
    async def _process_event_now(self, event: NotificationEvent):
        """Process event immediately"""
        try:
            # Get user preferences for language and personalization
            preferences = self.get_user_preferences(event.user_id)
            
            # Generate personalized content using templates
            templates = await self.template_manager.get_templates(
                event.event_type, 
                preferences.language,
                event.channels
            )
            
            # Deliver through all requested channels
            for channel in event.channels:
                if channel in templates:
                    template = templates[channel]
                    
                    # Personalize the template
                    personalized_content = await template.render(
                        user_id=event.user_id,
                        **event.data
                    )
                    
                    # Deliver notification
                    await self.delivery_manager.deliver(
                        channel=channel,
                        user_id=event.user_id,
                        title=personalized_content.get('title', event.title),
                        message=personalized_content.get('message', event.message),
                        data={
                            **event.data,
                            'event_id': event.event_id,
                            'event_type': event.event_type.value,
                            'priority': event.priority.value
                        }
                    )
            
            logger.info(f"Successfully processed event {event.event_id}")
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
            # In production, might want to retry or send to dead letter queue
    
    async def create_lesson_reminder(self, user_id: str, lesson_name: str, 
                                   lesson_time: datetime, **kwargs) -> str:
        """Convenience method to create lesson reminder"""
        event_id = f"lesson_reminder_{user_id}_{lesson_time.timestamp()}"
        event = NotificationEvent(
            event_id=event_id,
            event_type=EventType.LESSON_REMINDER,
            priority=Priority.MEDIUM,
            user_id=user_id,
            title=f"Time for {lesson_name}!",
            message=f"Your {lesson_name} lesson is starting soon.",
            data={
                'lesson_name': lesson_name,
                'lesson_time': lesson_time.isoformat(),
                **kwargs
            }
        )
        
        success = await self.submit_event(event)
        return event_id if success else None
    
    async def create_streak_warning(self, user_id: str, streak_count: int, 
                                  days_missed: int = 1, **kwargs) -> str:
        """Convenience method to create streak warning"""
        event_id = f"streak_warning_{user_id}_{datetime.utcnow().timestamp()}"
        event = NotificationEvent(
            event_id=event_id,
            event_type=EventType.STREAK_WARNING,
            priority=Priority.HIGH,
            user_id=user_id,
            title="Don't break your streak!",
            message=f"You've missed {days_missed} day(s). Keep your {streak_count}-day streak alive!",
            data={
                'streak_count': streak_count,
                'days_missed': days_missed,
                **kwargs
            }
        )
        
        success = await self.submit_event(event)
        return event_id if success else None
    
    async def create_achievement_notification(self, user_id: str, achievement_name: str,
                                            achievement_description: str, **kwargs) -> str:
        """Convenience method to create achievement notification"""
        event_id = f"achievement_{user_id}_{datetime.utcnow().timestamp()}"
        event = NotificationEvent(
            event_id=event_id,
            event_type=EventType.ACHIEVEMENT_UNLOCKED,
            priority=Priority.HIGH,
            user_id=user_id,
            title="🎉 Achievement Unlocked!",
            message=f"Congratulations! You've earned: {achievement_name}",
            data={
                'achievement_name': achievement_name,
                'achievement_description': achievement_description,
                **kwargs
            }
        )
        
        success = await self.submit_event(event)
        return event_id if success else None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status for monitoring"""
        return {
            'queued_events': len(self.event_queue),
            'active_users': len(self.user_preferences),
            'recent_notifications_count': sum(len(keys) for keys in self.recent_notifications.values())
        }