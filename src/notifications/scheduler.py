"""
Notification Scheduler - Smart scheduling and timing optimization

This module provides intelligent scheduling for notifications, including:
- Daily study reminders at optimal times based on user patterns
- Streak risk alerts when students are at risk of breaking streaks  
- Weekly parent reports delivered at convenient times
- Assessment deadline reminders with escalating urgency
- Batch notification processing for cost reduction
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque
import heapq

from .engine import NotificationEvent, EventType, Priority, UserPreferences

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of notification schedules"""
    IMMEDIATE = "immediate"
    OPTIMAL_TIME = "optimal_time"  
    BATCH = "batch"
    RECURRING = "recurring"
    DEADLINE_BASED = "deadline_based"


@dataclass
class ScheduledNotification:
    """A notification scheduled for future delivery"""
    notification: NotificationEvent
    scheduled_time: datetime
    schedule_type: ScheduleType
    retry_count: int = 0
    max_retries: int = 3
    batch_id: Optional[str] = None


@dataclass
class UserActivity:
    """Tracks user activity patterns for optimal scheduling"""
    user_id: str
    activity_hours: Dict[int, float] = field(default_factory=dict)  # hour -> activity_score
    timezone: str = "UTC"
    last_active: Optional[datetime] = None
    streak_days: int = 0
    last_study_session: Optional[datetime] = None


class NotificationScheduler:
    """Smart notification scheduler with cost optimization and timing intelligence"""
    
    def __init__(self):
        self.scheduled_notifications: List[Tuple[datetime, ScheduledNotification]] = []
        self.user_activity_patterns: Dict[str, UserActivity] = {}
        self.batch_queues: Dict[str, List[ScheduledNotification]] = defaultdict(list)
        self.running = False
        self.batch_interval = timedelta(minutes=30)  # Batch every 30 minutes
        self.max_daily_notifications = 10
        self.quiet_hours = (22, 7)  # 10 PM to 7 AM
        
    async def start(self):
        """Start the scheduler background task"""
        self.running = True
        logger.info("NotificationScheduler started")
        await asyncio.gather(
            self._schedule_processor(),
            self._batch_processor(),
            self._streak_monitor()
        )
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("NotificationScheduler stopped")
    
    async def schedule_notification(
        self, 
        notification: NotificationEvent,
        schedule_type: ScheduleType = ScheduleType.OPTIMAL_TIME,
        target_time: Optional[datetime] = None
    ) -> str:
        """Schedule a notification for optimal delivery"""
        
        if schedule_type == ScheduleType.IMMEDIATE:
            scheduled_time = datetime.now()
        elif schedule_type == ScheduleType.OPTIMAL_TIME:
            scheduled_time = await self._calculate_optimal_time(notification)
        elif target_time:
            scheduled_time = target_time
        else:
            scheduled_time = datetime.now() + timedelta(minutes=5)
        
        # Apply quiet hours filter
        scheduled_time = self._adjust_for_quiet_hours(scheduled_time, notification.user_id)
        
        scheduled_notif = ScheduledNotification(
            notification=notification,
            scheduled_time=scheduled_time,
            schedule_type=schedule_type
        )
        
        # Add to appropriate queue
        if schedule_type == ScheduleType.BATCH:
            batch_id = self._get_batch_id(notification)
            scheduled_notif.batch_id = batch_id
            self.batch_queues[batch_id].append(scheduled_notif)
        else:
            heapq.heappush(self.scheduled_notifications, (scheduled_time, scheduled_notif))
        
        logger.info(f"Scheduled {notification.event_type} for user {notification.user_id} at {scheduled_time}")
        return f"schedule_{hash(str(scheduled_notif))}"
    
    async def schedule_daily_reminders(self, user_ids: List[str]):
        """Schedule daily study reminders for users"""
        for user_id in user_ids:
            activity = self.user_activity_patterns.get(user_id)
            if not activity:
                continue
                
            # Find optimal study time based on activity patterns
            optimal_hour = self._get_optimal_study_hour(activity)
            
            # Schedule for tomorrow at optimal time
            tomorrow = datetime.now().date() + timedelta(days=1)
            optimal_time = datetime.combine(tomorrow, time(optimal_hour, 0))
            
            reminder = NotificationEvent(
                event_type=EventType.LESSON_REMINDER,
                user_id=user_id,
                priority=Priority.MEDIUM,
                data={
                    "message": "Time for your daily study session! 📚",
                    "optimal_time": True
                }
            )
            
            await self.schedule_notification(
                reminder, 
                ScheduleType.OPTIMAL_TIME,
                optimal_time
            )
    
    async def schedule_streak_alerts(self):
        """Monitor and schedule streak risk alerts"""
        current_time = datetime.now()
        
        for user_id, activity in self.user_activity_patterns.items():
            if not activity.last_study_session:
                continue
                
            hours_since_study = (current_time - activity.last_study_session).total_seconds() / 3600
            
            # Alert if no study for 20+ hours and streak > 3 days
            if hours_since_study >= 20 and activity.streak_days >= 3:
                alert = NotificationEvent(
                    event_type=EventType.STREAK_WARNING,
                    user_id=user_id,
                    priority=Priority.HIGH,
                    data={
                        "streak_days": activity.streak_days,
                        "hours_since_study": int(hours_since_study),
                        "risk_level": "high" if hours_since_study >= 30 else "medium"
                    }
                )
                
                await self.schedule_notification(alert, ScheduleType.IMMEDIATE)
    
    async def schedule_parent_reports(self, parent_user_ids: List[str]):
        """Schedule weekly parent reports"""
        # Schedule for Sunday evenings
        now = datetime.now()
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:  # If today is Sunday
            days_until_sunday = 7
            
        report_time = now.replace(hour=19, minute=0, second=0, microsecond=0)
        report_time += timedelta(days=days_until_sunday)
        
        for parent_id in parent_user_ids:
            report = NotificationEvent(
                event_type=EventType.PARENT_REPORT,
                user_id=parent_id,
                priority=Priority.MEDIUM,
                data={
                    "report_type": "weekly_summary",
                    "week_ending": (now + timedelta(days=days_until_sunday-1)).strftime("%Y-%m-%d")
                }
            )
            
            await self.schedule_notification(
                report,
                ScheduleType.RECURRING,
                report_time
            )
    
    async def schedule_assessment_reminders(
        self, 
        assessment_id: str, 
        due_date: datetime, 
        student_ids: List[str]
    ):
        """Schedule escalating assessment deadline reminders"""
        
        # Schedule reminders: 7 days, 3 days, 1 day, 2 hours before
        reminder_intervals = [
            (timedelta(days=7), Priority.LOW),
            (timedelta(days=3), Priority.MEDIUM), 
            (timedelta(days=1), Priority.HIGH),
            (timedelta(hours=2), Priority.URGENT)
        ]
        
        for student_id in student_ids:
            for interval, priority in reminder_intervals:
                reminder_time = due_date - interval
                
                # Skip if reminder time is in the past
                if reminder_time <= datetime.now():
                    continue
                
                reminder = NotificationEvent(
                    event_type=EventType.ASSESSMENT_DUE,
                    user_id=student_id,
                    priority=priority,
                    data={
                        "assessment_id": assessment_id,
                        "due_date": due_date.isoformat(),
                        "time_remaining": str(interval),
                        "urgency": priority.value
                    }
                )
                
                await self.schedule_notification(
                    reminder,
                    ScheduleType.DEADLINE_BASED,
                    reminder_time
                )
    
    def update_user_activity(
        self, 
        user_id: str, 
        activity_hour: int, 
        activity_score: float = 1.0
    ):
        """Update user activity patterns for optimal scheduling"""
        if user_id not in self.user_activity_patterns:
            self.user_activity_patterns[user_id] = UserActivity(user_id=user_id)
        
        activity = self.user_activity_patterns[user_id]
        activity.last_active = datetime.now()
        
        # Update activity score with exponential moving average
        current_score = activity.activity_hours.get(activity_hour, 0)
        activity.activity_hours[activity_hour] = 0.7 * current_score + 0.3 * activity_score
    
    def update_user_streak(self, user_id: str, streak_days: int):
        """Update user streak information"""
        if user_id not in self.user_activity_patterns:
            self.user_activity_patterns[user_id] = UserActivity(user_id=user_id)
        
        self.user_activity_patterns[user_id].streak_days = streak_days
        self.user_activity_patterns[user_id].last_study_session = datetime.now()
    
    async def _schedule_processor(self):
        """Background task to process scheduled notifications"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Process due notifications
                while (self.scheduled_notifications and 
                       self.scheduled_notifications[0][0] <= current_time):
                    
                    scheduled_time, scheduled_notif = heapq.heappop(self.scheduled_notifications)
                    
                    # Yield notification for delivery
                    logger.info(f"Processing scheduled notification: {scheduled_notif.notification.event_type}")
                    # In real implementation, this would send to delivery manager
                    
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in schedule processor: {e}")
                await asyncio.sleep(60)
    
    async def _batch_processor(self):
        """Background task to process batch notifications"""
        while self.running:
            try:
                # Process each batch queue
                for batch_id, notifications in self.batch_queues.items():
                    if notifications:
                        logger.info(f"Processing batch {batch_id} with {len(notifications)} notifications")
                        
                        # Send batch for delivery
                        # In real implementation, would optimize delivery order
                        notifications.clear()
                
                await asyncio.sleep(self.batch_interval.total_seconds())
                
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(300)
    
    async def _streak_monitor(self):
        """Background task to monitor streaks"""
        while self.running:
            try:
                await self.schedule_streak_alerts()
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in streak monitor: {e}")
                await asyncio.sleep(1800)
    
    async def _calculate_optimal_time(self, notification: NotificationEvent) -> datetime:
        """Calculate optimal delivery time based on user patterns"""
        activity = self.user_activity_patterns.get(notification.user_id)
        if not activity or not activity.activity_hours:
            # Default to 9 AM if no pattern data
            tomorrow = datetime.now().date() + timedelta(days=1)
            return datetime.combine(tomorrow, time(9, 0))
        
        # Find hour with highest activity
        best_hour = max(activity.activity_hours.keys(), 
                       key=lambda h: activity.activity_hours[h])
        
        # Schedule for tomorrow at best hour
        tomorrow = datetime.now().date() + timedelta(days=1)
        return datetime.combine(tomorrow, time(best_hour, 0))
    
    def _adjust_for_quiet_hours(self, scheduled_time: datetime, user_id: str) -> datetime:
        """Adjust scheduled time to avoid quiet hours"""
        hour = scheduled_time.hour
        quiet_start, quiet_end = self.quiet_hours
        
        # If scheduled during quiet hours, move to start of day
        if quiet_start <= hour or hour < quiet_end:
            return scheduled_time.replace(hour=quiet_end, minute=0)
        
        return scheduled_time
    
    def _get_optimal_study_hour(self, activity: UserActivity) -> int:
        """Get optimal study hour based on activity patterns"""
        if not activity.activity_hours:
            return 9  # Default 9 AM
        
        # Prefer morning hours for study reminders
        morning_hours = {h: score for h, score in activity.activity_hours.items() 
                        if 6 <= h <= 12}
        
        if morning_hours:
            return max(morning_hours.keys(), key=lambda h: morning_hours[h])
        
        # Fall back to most active hour
        return max(activity.activity_hours.keys(), 
                  key=lambda h: activity.activity_hours[h])
    
    def _get_batch_id(self, notification: NotificationEvent) -> str:
        """Generate batch ID for grouping similar notifications"""
        # Group by event type and hour
        hour_key = datetime.now().strftime("%Y%m%d%H")
        return f"{notification.event_type.value}_{hour_key}"