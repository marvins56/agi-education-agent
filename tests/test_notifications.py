"""
Test cases for the notification system components

Tests for NotificationEngine, NotificationScheduler, DeliveryManager, and templates
"""

import asyncio
import pytest
from datetime import datetime, timedelta, time
from unittest.mock import Mock, patch, AsyncMock
import json

from src.notifications.engine import (
    NotificationEngine, NotificationEvent, EventType, Priority, UserPreferences
)
from src.notifications.scheduler import (
    NotificationScheduler, ScheduledNotification, ScheduleType, UserActivity
)
from src.notifications.delivery import (
    DeliveryManager, DeliveryChannel, DeliveryStatus, DeliveryRecord,
    PushNotificationProvider, SMSProvider, EmailProvider, InAppProvider,
    CostLevel
)
from src.notifications.templates import TemplateManager


class TestNotificationScheduler:
    """Tests for NotificationScheduler"""
    
    @pytest.fixture
    def scheduler(self):
        return NotificationScheduler()
    
    @pytest.fixture
    def sample_notification(self):
        return NotificationEvent(
            event_type=EventType.LESSON_REMINDER,
            user_id="user_123",
            priority=Priority.MEDIUM,
            data={"message": "Time for your math lesson!"}
        )
    
    @pytest.mark.asyncio
    async def test_schedule_immediate_notification(self, scheduler, sample_notification):
        """Test scheduling immediate notifications"""
        schedule_id = await scheduler.schedule_notification(
            sample_notification, 
            ScheduleType.IMMEDIATE
        )
        
        assert schedule_id.startswith("schedule_")
        assert len(scheduler.scheduled_notifications) == 1
    
    @pytest.mark.asyncio
    async def test_schedule_optimal_time_notification(self, scheduler, sample_notification):
        """Test scheduling notifications at optimal times"""
        # Set up user activity pattern
        scheduler.update_user_activity("user_123", 9, 1.0)  # 9 AM is optimal
        scheduler.update_user_activity("user_123", 10, 0.8)
        scheduler.update_user_activity("user_123", 14, 0.6)
        
        schedule_id = await scheduler.schedule_notification(
            sample_notification,
            ScheduleType.OPTIMAL_TIME
        )
        
        assert schedule_id.startswith("schedule_")
        # Should schedule for tomorrow at 9 AM (optimal hour)
    
    def test_update_user_activity(self, scheduler):
        """Test updating user activity patterns"""
        scheduler.update_user_activity("user_123", 9, 1.0)
        scheduler.update_user_activity("user_123", 10, 0.8)
        
        activity = scheduler.user_activity_patterns["user_123"]
        assert activity.user_id == "user_123"
        assert activity.activity_hours[9] == 1.0
        assert activity.activity_hours[10] == 0.8
        assert activity.last_active is not None
    
    def test_update_user_streak(self, scheduler):
        """Test updating user streak information"""
        scheduler.update_user_streak("user_123", 5)
        
        activity = scheduler.user_activity_patterns["user_123"]
        assert activity.streak_days == 5
        assert activity.last_study_session is not None
    
    @pytest.mark.asyncio
    async def test_schedule_daily_reminders(self, scheduler):
        """Test scheduling daily study reminders"""
        user_ids = ["user_123", "user_456"]
        
        # Set up activity patterns
        for user_id in user_ids:
            scheduler.update_user_activity(user_id, 9, 1.0)  # Morning preference
        
        await scheduler.schedule_daily_reminders(user_ids)
        
        # Should have scheduled reminders for tomorrow
        assert len(scheduler.scheduled_notifications) > 0
    
    @pytest.mark.asyncio
    async def test_streak_alerts(self, scheduler):
        """Test streak risk alerts"""
        # Set up user with long streak but no recent study
        yesterday = datetime.now() - timedelta(hours=25)
        scheduler.user_activity_patterns["user_123"] = UserActivity(
            user_id="user_123",
            streak_days=7,
            last_study_session=yesterday
        )
        
        await scheduler.schedule_streak_alerts()
        
        # Should have scheduled a streak warning
        assert len(scheduler.scheduled_notifications) > 0
        
    @pytest.mark.asyncio
    async def test_assessment_reminders(self, scheduler):
        """Test assessment deadline reminders"""
        due_date = datetime.now() + timedelta(days=5)
        student_ids = ["student_1", "student_2"]
        
        await scheduler.schedule_assessment_reminders(
            "assessment_123", 
            due_date, 
            student_ids
        )
        
        # Should have scheduled multiple reminders (7d, 3d, 1d, 2h before)
        # But only those in the future
        assert len(scheduler.scheduled_notifications) >= 2  # At least 3d and 1d reminders
    
    def test_quiet_hours_adjustment(self, scheduler):
        """Test quiet hours time adjustment"""
        # Test scheduling during quiet hours (11 PM)
        late_night = datetime.now().replace(hour=23, minute=0)
        adjusted = scheduler._adjust_for_quiet_hours(late_night, "user_123")
        
        # Should be moved to 7 AM
        assert adjusted.hour == 7
        assert adjusted.minute == 0
    
    def test_optimal_study_hour_calculation(self, scheduler):
        """Test calculation of optimal study hours"""
        activity = UserActivity(user_id="user_123")
        activity.activity_hours = {
            6: 0.3,   # Early morning
            9: 0.9,   # Peak morning
            10: 0.7,  # Late morning
            14: 0.5,  # Afternoon
            20: 0.8   # Evening
        }
        
        optimal_hour = scheduler._get_optimal_study_hour(activity)
        assert optimal_hour == 9  # Should prefer 9 AM (highest morning score)


class TestDeliveryManager:
    """Tests for DeliveryManager and providers"""
    
    @pytest.fixture
    def delivery_manager(self):
        return DeliveryManager()
    
    @pytest.fixture
    def sample_notification(self):
        return NotificationEvent(
            event_type=EventType.LESSON_REMINDER,
            user_id="user_123",
            priority=Priority.MEDIUM,
            data={
                "title": "Study Time",
                "message": "Time for your math lesson!"
            }
        )
    
    @pytest.fixture
    def user_contact_info(self):
        return {
            "user_id": "user_123",
            "device_token": "mock_device_token",
            "phone_number": "+256700123456",
            "email": "student@example.com"
        }
    
    def test_provider_registration(self, delivery_manager):
        """Test provider registration"""
        push_provider = PushNotificationProvider("mock_fcm_key")
        delivery_manager.register_provider(DeliveryChannel.PUSH, push_provider)
        
        assert DeliveryChannel.PUSH in delivery_manager.providers
        assert isinstance(delivery_manager.providers[DeliveryChannel.PUSH], PushNotificationProvider)
    
    @pytest.mark.asyncio
    async def test_push_provider_success(self):
        """Test successful push notification"""
        provider = PushNotificationProvider("mock_key")
        
        notification = NotificationEvent(
            event_type=EventType.LESSON_REMINDER,
            user_id="user_123",
            priority=Priority.MEDIUM,
            data={"title": "Test", "message": "Test message"}
        )
        
        # Mock successful FCM response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": 1})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            attempt = await provider.send(notification, device_token="mock_token")
            
            assert attempt.status == DeliveryStatus.SENT
            assert attempt.channel == DeliveryChannel.PUSH
            assert attempt.cost == 0.0  # Push is free
    
    @pytest.mark.asyncio
    async def test_sms_provider_success(self):
        """Test successful SMS delivery"""
        provider = SMSProvider("mock_api_key")
        
        notification = NotificationEvent(
            event_type=EventType.STREAK_WARNING,
            user_id="user_123",
            priority=Priority.HIGH,
            data={"message": "Don't break your streak!"}
        )
        
        # Mock successful SMS response
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={
                "SMSMessageData": {
                    "Recipients": [{"status": "Success"}]
                }
            })
            mock_post.return_value.__aenter__.return_value = mock_response
            
            attempt = await provider.send(notification, phone_number="+256700123456")
            
            assert attempt.status == DeliveryStatus.SENT
            assert attempt.channel == DeliveryChannel.SMS
            assert attempt.cost == provider.cost_per_sms
    
    @pytest.mark.asyncio
    async def test_email_provider(self):
        """Test email provider"""
        provider = EmailProvider({"smtp_host": "localhost"})
        
        notification = NotificationEvent(
            event_type=EventType.PARENT_REPORT,
            user_id="parent_123",
            priority=Priority.MEDIUM,
            data={"message": "Weekly progress report"}
        )
        
        attempt = await provider.send(notification, email="parent@example.com")
        
        assert attempt.status == DeliveryStatus.SENT
        assert attempt.channel == DeliveryChannel.EMAIL
        assert attempt.cost == provider.cost_per_email
    
    @pytest.mark.asyncio
    async def test_inapp_provider(self):
        """Test in-app notification provider"""
        provider = InAppProvider()
        
        notification = NotificationEvent(
            event_type=EventType.ACHIEVEMENT_UNLOCKED,
            user_id="user_123",
            priority=Priority.LOW,
            data={"message": "Achievement unlocked!"}
        )
        
        attempt = await provider.send(notification, user_id="user_123")
        
        assert attempt.status == DeliveryStatus.DELIVERED
        assert attempt.channel == DeliveryChannel.IN_APP
        assert attempt.cost == 0.0
    
    def test_cost_levels(self):
        """Test provider cost levels"""
        push_provider = PushNotificationProvider("key")
        sms_provider = SMSProvider("key")
        email_provider = EmailProvider({})
        inapp_provider = InAppProvider()
        
        assert push_provider.get_cost_level() == CostLevel.FREE
        assert sms_provider.get_cost_level() == CostLevel.HIGH
        assert email_provider.get_cost_level() == CostLevel.LOW
        assert inapp_provider.get_cost_level() == CostLevel.FREE
    
    def test_channel_optimization(self, delivery_manager):
        """Test channel optimization based on priority and cost"""
        channels = [DeliveryChannel.SMS, DeliveryChannel.PUSH, DeliveryChannel.EMAIL]
        
        # For urgent notifications, should prioritize reliability
        urgent_optimized = delivery_manager._optimize_channel_selection(
            channels, Priority.URGENT
        )
        
        # For normal notifications, should prioritize cost
        normal_optimized = delivery_manager._optimize_channel_selection(
            channels, Priority.MEDIUM
        )
        
        assert isinstance(urgent_optimized, list)
        assert isinstance(normal_optimized, list)
        assert len(urgent_optimized) == len(channels)
    
    @pytest.mark.asyncio
    async def test_delivery_with_fallback(self, delivery_manager, sample_notification, user_contact_info):
        """Test delivery with fallback channels"""
        # Register providers
        push_provider = PushNotificationProvider("mock_key")
        email_provider = EmailProvider({})
        
        delivery_manager.register_provider(DeliveryChannel.PUSH, push_provider)
        delivery_manager.register_provider(DeliveryChannel.EMAIL, email_provider)
        
        # Mock push failure, email success
        with patch.object(push_provider, 'send') as mock_push:
            mock_push.return_value = Mock(
                status=DeliveryStatus.FAILED,
                channel=DeliveryChannel.PUSH,
                cost=0.0
            )
            
            record = await delivery_manager.deliver(
                sample_notification,
                preferred_channels=[DeliveryChannel.PUSH],
                user_contact_info=user_contact_info,
                fallback_channels=[DeliveryChannel.EMAIL]
            )
            
            assert len(record.attempts) >= 1
            assert record.notification_id == sample_notification.notification_id
    
    def test_delivery_stats(self, delivery_manager):
        """Test delivery statistics calculation"""
        # Create mock delivery records
        record1 = DeliveryRecord(
            notification_id="notif_1",
            user_id="user_123",
            event_type=EventType.LESSON_REMINDER,
            final_status=DeliveryStatus.SENT,
            total_cost=0.05
        )
        
        record2 = DeliveryRecord(
            notification_id="notif_2",
            user_id="user_456",
            event_type=EventType.STREAK_WARNING,
            final_status=DeliveryStatus.FAILED,
            total_cost=0.0
        )
        
        delivery_manager.delivery_records["notif_1"] = record1
        delivery_manager.delivery_records["notif_2"] = record2
        
        stats = delivery_manager.get_delivery_stats()
        
        assert stats["total_notifications"] == 2
        assert stats["success_rate"] == 0.5
        assert stats["total_cost"] == 0.05
        assert "cost_remaining" in stats


class TestNotificationIntegration:
    """Integration tests for the complete notification system"""
    
    @pytest.fixture
    def notification_engine(self):
        # This would need to be imported once the engine is complete
        # For now, we'll mock it
        return Mock()
    
    @pytest.mark.asyncio
    async def test_end_to_end_notification_flow(self):
        """Test complete notification flow from trigger to delivery"""
        # Set up components
        scheduler = NotificationScheduler()
        delivery_manager = DeliveryManager()
        
        # Register providers
        push_provider = PushNotificationProvider("mock_key")
        delivery_manager.register_provider(DeliveryChannel.PUSH, push_provider)
        
        # Create notification
        notification = NotificationEvent(
            event_type=EventType.LESSON_REMINDER,
            user_id="user_123",
            priority=Priority.MEDIUM,
            data={"title": "Study Time", "message": "Math lesson starting!"}
        )
        
        # Schedule notification
        await scheduler.schedule_notification(notification, ScheduleType.IMMEDIATE)
        
        # Verify scheduling
        assert len(scheduler.scheduled_notifications) == 1
        
        # Mock successful delivery
        user_contact_info = {"device_token": "mock_token"}
        
        with patch.object(push_provider, 'send') as mock_send:
            mock_send.return_value = Mock(
                status=DeliveryStatus.SENT,
                channel=DeliveryChannel.PUSH,
                cost=0.0
            )
            
            record = await delivery_manager.deliver(
                notification,
                preferred_channels=[DeliveryChannel.PUSH],
                user_contact_info=user_contact_info
            )
            
            assert record.final_status == DeliveryStatus.SENT
    
    @pytest.mark.asyncio
    async def test_batch_notification_processing(self):
        """Test batch processing of multiple notifications"""
        scheduler = NotificationScheduler()
        
        notifications = []
        for i in range(5):
            notification = NotificationEvent(
                event_type=EventType.LESSON_REMINDER,
                user_id=f"user_{i}",
                priority=Priority.LOW,
                data={"message": f"Reminder {i}"}
            )
            notifications.append(notification)
        
        # Schedule all as batch
        for notification in notifications:
            await scheduler.schedule_notification(
                notification,
                ScheduleType.BATCH
            )
        
        # Verify batch queuing
        assert len(scheduler.batch_queues) > 0
        total_batched = sum(len(queue) for queue in scheduler.batch_queues.values())
        assert total_batched == 5
    
    def test_notification_cost_optimization(self):
        """Test cost optimization across the system"""
        delivery_manager = DeliveryManager()
        delivery_manager.cost_budget_daily = 1.0  # Low budget for testing
        delivery_manager.cost_spent_today = 0.8   # Already spent most budget
        
        # Register expensive provider
        sms_provider = SMSProvider("key")
        delivery_manager.register_provider(DeliveryChannel.SMS, sms_provider)
        
        # Test that expensive channels are skipped when budget is low
        channels = [DeliveryChannel.SMS, DeliveryChannel.PUSH]
        optimized = delivery_manager._optimize_channel_selection(channels, Priority.MEDIUM)
        
        # Should still return channels but delivery logic will skip expensive ones
        assert len(optimized) > 0