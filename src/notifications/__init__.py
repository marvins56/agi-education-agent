"""
EduAGI Notification System

A multi-channel notification system designed to deliver personalized educational
notifications across various platforms including push notifications, SMS, email,
and in-app messaging. The system supports multi-language content delivery,
intelligent scheduling, and cost optimization.

Main Components:
- NotificationEngine: Central orchestrator for all notifications
- NotificationTemplate: Multi-language template management
- NotificationScheduler: Smart scheduling and timing optimization
- DeliveryManager: Multi-channel delivery with retry logic

Supported Event Types:
- lesson_reminder: Daily study reminders
- streak_warning: Alert when learning streak is at risk
- achievement_unlocked: Celebrating student milestones
- assessment_due: Upcoming test/assignment reminders
- parent_report: Weekly progress summaries for parents
- teacher_alert: Important notifications for educators
- system_update: Platform updates and announcements

Supported Languages:
- English (default)
- Swahili (sw)
- Luganda (lg)
"""

from .engine import NotificationEngine, NotificationEvent, Priority
from .templates import NotificationTemplate, TemplateManager
from .scheduler import NotificationScheduler
from .delivery import DeliveryManager, DeliveryChannel, DeliveryStatus

__version__ = "1.0.0"
__author__ = "EduAGI Team"

__all__ = [
    "NotificationEngine",
    "NotificationEvent",
    "Priority",
    "NotificationTemplate", 
    "TemplateManager",
    "NotificationScheduler",
    "DeliveryManager",
    "DeliveryChannel",
    "DeliveryStatus",
]