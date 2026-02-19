"""
Delivery Manager - Multi-channel notification delivery

This module provides multi-channel notification delivery with:
- Push notifications (FCM/APNs)
- SMS delivery with cost optimization
- Email notifications
- In-app messaging
- Delivery tracking and retry logic
- Cost-aware channel selection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import aiohttp
from abc import ABC, abstractmethod

from .engine import NotificationEvent, EventType, Priority, DeliveryChannel

logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """Delivery status tracking"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"
    EXPIRED = "expired"


class CostLevel(Enum):
    """Cost levels for different delivery channels"""
    FREE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class DeliveryAttempt:
    """Individual delivery attempt record"""
    attempt_id: str
    channel: DeliveryChannel
    timestamp: datetime
    status: DeliveryStatus
    error_message: Optional[str] = None
    cost: float = 0.0
    response_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryRecord:
    """Complete delivery record for a notification"""
    notification_id: str
    user_id: str
    event_type: EventType
    attempts: List[DeliveryAttempt] = field(default_factory=list)
    final_status: DeliveryStatus = DeliveryStatus.PENDING
    total_cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class DeliveryProvider(ABC):
    """Abstract base class for delivery providers"""
    
    @abstractmethod
    async def send(self, notification: NotificationEvent, **kwargs) -> DeliveryAttempt:
        """Send notification via this provider"""
        pass
    
    @abstractmethod
    def get_cost_level(self) -> CostLevel:
        """Get cost level for this provider"""
        pass
    
    @abstractmethod
    def supports_channel(self, channel: DeliveryChannel) -> bool:
        """Check if provider supports given channel"""
        pass


class PushNotificationProvider(DeliveryProvider):
    """Firebase Cloud Messaging / Apple Push Notification provider"""
    
    def __init__(self, fcm_key: str, apns_key: Optional[str] = None):
        self.fcm_key = fcm_key
        self.apns_key = apns_key
    
    async def send(self, notification: NotificationEvent, **kwargs) -> DeliveryAttempt:
        """Send push notification"""
        attempt_id = f"push_{datetime.now().timestamp()}"
        
        try:
            # FCM payload
            payload = {
                "to": kwargs.get("device_token"),
                "notification": {
                    "title": notification.data.get("title", "EduAGI"),
                    "body": notification.data.get("message", ""),
                    "icon": "ic_notification"
                },
                "data": {
                    "event_type": notification.event_type.value,
                    "user_id": notification.user_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            headers = {
                "Authorization": f"key={self.fcm_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json=payload,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("success", 0) > 0:
                        return DeliveryAttempt(
                            attempt_id=attempt_id,
                            channel=DeliveryChannel.PUSH,
                            timestamp=datetime.now(),
                            status=DeliveryStatus.SENT,
                            cost=0.0,  # Push notifications are free
                            response_data=result
                        )
                    else:
                        return DeliveryAttempt(
                            attempt_id=attempt_id,
                            channel=DeliveryChannel.PUSH,
                            timestamp=datetime.now(),
                            status=DeliveryStatus.FAILED,
                            error_message=result.get("error", "Unknown error"),
                            response_data=result
                        )
        
        except Exception as e:
            return DeliveryAttempt(
                attempt_id=attempt_id,
                channel=DeliveryChannel.PUSH,
                timestamp=datetime.now(),
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def get_cost_level(self) -> CostLevel:
        return CostLevel.FREE
    
    def supports_channel(self, channel: DeliveryChannel) -> bool:
        return channel == DeliveryChannel.PUSH


class SMSProvider(DeliveryProvider):
    """SMS delivery provider (Twilio/Africa's Talking)"""
    
    def __init__(self, api_key: str, sender_id: str = "EduAGI"):
        self.api_key = api_key
        self.sender_id = sender_id
        self.cost_per_sms = 0.05  # USD per SMS
    
    async def send(self, notification: NotificationEvent, **kwargs) -> DeliveryAttempt:
        """Send SMS notification"""
        attempt_id = f"sms_{datetime.now().timestamp()}"
        
        try:
            phone_number = kwargs.get("phone_number")
            message = notification.data.get("message", "")
            
            # Africa's Talking API format
            payload = {
                "username": "eduagi",
                "to": phone_number,
                "message": f"{message}\n\n- EduAGI",
                "from": self.sender_id
            }
            
            headers = {
                "apiKey": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.africastalking.com/version1/messaging",
                    data=payload,
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    if response.status == 201:
                        recipients = result.get("SMSMessageData", {}).get("Recipients", [])
                        if recipients and recipients[0].get("status") == "Success":
                            return DeliveryAttempt(
                                attempt_id=attempt_id,
                                channel=DeliveryChannel.SMS,
                                timestamp=datetime.now(),
                                status=DeliveryStatus.SENT,
                                cost=self.cost_per_sms,
                                response_data=result
                            )
                    
                    return DeliveryAttempt(
                        attempt_id=attempt_id,
                        channel=DeliveryChannel.SMS,
                        timestamp=datetime.now(),
                        status=DeliveryStatus.FAILED,
                        error_message=result.get("SMSMessageData", {}).get("Message", "SMS failed"),
                        response_data=result
                    )
        
        except Exception as e:
            return DeliveryAttempt(
                attempt_id=attempt_id,
                channel=DeliveryChannel.SMS,
                timestamp=datetime.now(),
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def get_cost_level(self) -> CostLevel:
        return CostLevel.HIGH
    
    def supports_channel(self, channel: DeliveryChannel) -> bool:
        return channel == DeliveryChannel.SMS


class EmailProvider(DeliveryProvider):
    """Email delivery provider"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        self.cost_per_email = 0.001  # Very low cost
    
    async def send(self, notification: NotificationEvent, **kwargs) -> DeliveryAttempt:
        """Send email notification"""
        attempt_id = f"email_{datetime.now().timestamp()}"
        
        try:
            # Simulate email sending (replace with actual SMTP)
            await asyncio.sleep(0.1)  # Simulate network delay
            
            return DeliveryAttempt(
                attempt_id=attempt_id,
                channel=DeliveryChannel.EMAIL,
                timestamp=datetime.now(),
                status=DeliveryStatus.SENT,
                cost=self.cost_per_email,
                response_data={"email_sent": True}
            )
        
        except Exception as e:
            return DeliveryAttempt(
                attempt_id=attempt_id,
                channel=DeliveryChannel.EMAIL,
                timestamp=datetime.now(),
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def get_cost_level(self) -> CostLevel:
        return CostLevel.LOW
    
    def supports_channel(self, channel: DeliveryChannel) -> bool:
        return channel == DeliveryChannel.EMAIL


class InAppProvider(DeliveryProvider):
    """In-app notification provider"""
    
    async def send(self, notification: NotificationEvent, **kwargs) -> DeliveryAttempt:
        """Send in-app notification"""
        attempt_id = f"inapp_{datetime.now().timestamp()}"
        
        try:
            # Store in database for in-app display
            # In real implementation, would save to notifications table
            
            return DeliveryAttempt(
                attempt_id=attempt_id,
                channel=DeliveryChannel.IN_APP,
                timestamp=datetime.now(),
                status=DeliveryStatus.DELIVERED,  # In-app is always "delivered"
                cost=0.0,
                response_data={"stored": True}
            )
        
        except Exception as e:
            return DeliveryAttempt(
                attempt_id=attempt_id,
                channel=DeliveryChannel.IN_APP,
                timestamp=datetime.now(),
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
    
    def get_cost_level(self) -> CostLevel:
        return CostLevel.FREE
    
    def supports_channel(self, channel: DeliveryChannel) -> bool:
        return channel == DeliveryChannel.IN_APP


class DeliveryManager:
    """Multi-channel delivery manager with cost optimization"""
    
    def __init__(self):
        self.providers: Dict[DeliveryChannel, DeliveryProvider] = {}
        self.delivery_records: Dict[str, DeliveryRecord] = {}
        self.cost_budget_daily = 10.0  # $10 daily budget
        self.cost_spent_today = 0.0
        self.retry_delays = [60, 300, 900]  # 1min, 5min, 15min
        self.max_retries = 3
        
    def register_provider(self, channel: DeliveryChannel, provider: DeliveryProvider):
        """Register a delivery provider for a channel"""
        self.providers[channel] = provider
        logger.info(f"Registered {provider.__class__.__name__} for {channel.value}")
    
    async def deliver(
        self, 
        notification: NotificationEvent,
        preferred_channels: List[DeliveryChannel],
        user_contact_info: Dict[str, Any],
        fallback_channels: Optional[List[DeliveryChannel]] = None
    ) -> DeliveryRecord:
        """Deliver notification via optimal channel with fallback"""
        
        record = DeliveryRecord(
            notification_id=notification.notification_id,
            user_id=notification.user_id,
            event_type=notification.event_type
        )
        
        # Optimize channel selection based on cost and availability
        optimal_channels = self._optimize_channel_selection(
            preferred_channels, 
            notification.priority
        )
        
        # Add fallback channels if provided
        if fallback_channels:
            optimal_channels.extend([ch for ch in fallback_channels if ch not in optimal_channels])
        
        # Attempt delivery on each channel until success
        for channel in optimal_channels:
            provider = self.providers.get(channel)
            if not provider:
                continue
            
            # Check budget for paid channels
            if provider.get_cost_level() != CostLevel.FREE:
                if self.cost_spent_today >= self.cost_budget_daily:
                    logger.warning(f"Daily budget exceeded, skipping {channel.value}")
                    continue
            
            # Prepare channel-specific parameters
            channel_params = self._get_channel_params(channel, user_contact_info)
            if not channel_params:
                continue
            
            # Attempt delivery
            attempt = await provider.send(notification, **channel_params)
            record.attempts.append(attempt)
            record.total_cost += attempt.cost
            self.cost_spent_today += attempt.cost
            
            if attempt.status == DeliveryStatus.SENT:
                record.final_status = DeliveryStatus.SENT
                record.completed_at = datetime.now()
                break
            elif attempt.status == DeliveryStatus.DELIVERED:
                record.final_status = DeliveryStatus.DELIVERED
                record.completed_at = datetime.now()
                break
        
        # If all channels failed, schedule retry
        if record.final_status == DeliveryStatus.PENDING:
            record.final_status = DeliveryStatus.FAILED
            await self._schedule_retry(notification, record, user_contact_info)
        
        # Store delivery record
        self.delivery_records[record.notification_id] = record
        
        logger.info(f"Delivery completed: {record.final_status} for {notification.event_type}")
        return record
    
    async def retry_failed_delivery(self, notification_id: str):
        """Retry a failed delivery"""
        record = self.delivery_records.get(notification_id)
        if not record or record.final_status != DeliveryStatus.FAILED:
            return
        
        # Implement exponential backoff retry logic
        retry_count = len([a for a in record.attempts if a.status == DeliveryStatus.FAILED])
        if retry_count >= self.max_retries:
            record.final_status = DeliveryStatus.EXPIRED
            return
        
        # Wait for retry delay
        delay = self.retry_delays[min(retry_count - 1, len(self.retry_delays) - 1)]
        await asyncio.sleep(delay)
        
        # Retry with remaining budget
        logger.info(f"Retrying delivery for notification {notification_id}")
    
    def get_delivery_stats(self, time_period: timedelta = timedelta(days=1)) -> Dict[str, Any]:
        """Get delivery statistics"""
        cutoff = datetime.now() - time_period
        recent_records = [
            r for r in self.delivery_records.values() 
            if r.created_at >= cutoff
        ]
        
        total_notifications = len(recent_records)
        successful_deliveries = len([r for r in recent_records if r.final_status in [DeliveryStatus.SENT, DeliveryStatus.DELIVERED]])
        total_cost = sum(r.total_cost for r in recent_records)
        
        channel_stats = {}
        for channel in DeliveryChannel:
            channel_attempts = []
            for record in recent_records:
                channel_attempts.extend([a for a in record.attempts if a.channel == channel])
            
            if channel_attempts:
                channel_stats[channel.value] = {
                    "attempts": len(channel_attempts),
                    "success_rate": len([a for a in channel_attempts if a.status in [DeliveryStatus.SENT, DeliveryStatus.DELIVERED]]) / len(channel_attempts),
                    "total_cost": sum(a.cost for a in channel_attempts)
                }
        
        return {
            "total_notifications": total_notifications,
            "success_rate": successful_deliveries / total_notifications if total_notifications > 0 else 0,
            "total_cost": total_cost,
            "cost_remaining": self.cost_budget_daily - self.cost_spent_today,
            "channel_performance": channel_stats
        }
    
    def _optimize_channel_selection(
        self, 
        preferred_channels: List[DeliveryChannel],
        priority: Priority
    ) -> List[DeliveryChannel]:
        """Optimize channel selection based on cost and priority"""
        available_channels = [ch for ch in preferred_channels if ch in self.providers]
        
        if priority in [Priority.URGENT, Priority.HIGH]:
            # For urgent notifications, prefer reliable channels regardless of cost
            return sorted(available_channels, key=lambda ch: self.providers[ch].get_cost_level().value)
        else:
            # For normal notifications, prefer low-cost channels
            return sorted(available_channels, key=lambda ch: (
                self.providers[ch].get_cost_level().value,
                -len(available_channels)  # Prefer channels with more options
            ))
    
    def _get_channel_params(
        self, 
        channel: DeliveryChannel, 
        user_contact_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get channel-specific parameters from user contact info"""
        if channel == DeliveryChannel.PUSH:
            device_token = user_contact_info.get("device_token")
            return {"device_token": device_token} if device_token else None
        
        elif channel == DeliveryChannel.SMS:
            phone = user_contact_info.get("phone_number")
            return {"phone_number": phone} if phone else None
        
        elif channel == DeliveryChannel.EMAIL:
            email = user_contact_info.get("email")
            return {"email": email} if email else None
        
        elif channel == DeliveryChannel.IN_APP:
            return {"user_id": user_contact_info.get("user_id")}
        
        return None
    
    async def _schedule_retry(
        self, 
        notification: NotificationEvent,
        record: DeliveryRecord,
        user_contact_info: Dict[str, Any]
    ):
        """Schedule retry for failed delivery"""
        retry_count = len(record.attempts)
        if retry_count >= self.max_retries:
            record.final_status = DeliveryStatus.EXPIRED
            return
        
        # Schedule retry with exponential backoff
        delay = self.retry_delays[min(retry_count, len(self.retry_delays) - 1)]
        
        async def retry_task():
            await asyncio.sleep(delay)
            await self.retry_failed_delivery(record.notification_id)
        
        asyncio.create_task(retry_task())
        record.final_status = DeliveryStatus.RETRY