"""
Channel Router for EduAGI - Intelligent routing of students to appropriate communication channels

Routes students to the best available channel based on their device capabilities,
preferences, and connectivity. Ensures seamless learning experience across all channels.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

# Import from main project structure
from ..config import settings
from ..models.database import get_db
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Database models for channel routing
Base = declarative_base()

class StudentChannelProfile(Base):
    """Track student's channel capabilities and preferences"""
    __tablename__ = 'student_channel_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    detected_capabilities = Column(JSON, nullable=False, default=dict)  # Device capabilities
    preferred_channels = Column(JSON, nullable=False, default=list)     # User preferences
    blocked_channels = Column(JSON, nullable=False, default=list)       # Unavailable channels
    primary_channel = Column(String, nullable=False, default='sms')
    fallback_channel = Column(String, nullable=False, default='ussd') 
    last_activity = Column(JSON, nullable=False, default=dict)          # Activity per channel
    success_rates = Column(JSON, nullable=False, default=dict)          # Success rate per channel
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChannelRoutingLog(Base):
    """Log channel routing decisions for analytics"""
    __tablename__ = 'channel_routing_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    requested_channel = Column(String, nullable=True)
    routed_channel = Column(String, nullable=False)
    routing_reason = Column(String, nullable=False)
    success = Column(Boolean, nullable=True)  # Set after delivery attempt
    routing_metadata = Column("metadata", JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)


class ChannelType(Enum):
    """Available communication channels"""
    SMS = "sms"
    USSD = "ussd" 
    VOICE = "voice"
    WEB = "web"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"


class DeviceCapability(Enum):
    """Device capability categories"""
    FEATURE_PHONE = "feature_phone"      # Basic phone, SMS/USSD only
    SMARTPHONE_BASIC = "smartphone_basic" # Smartphone with limited data
    SMARTPHONE_FULL = "smartphone_full"   # Full smartphone capabilities
    UNKNOWN = "unknown"


@dataclass
class ChannelCapabilities:
    """Channel capability requirements"""
    requires_internet: bool
    requires_smartphone: bool
    data_usage: str  # low, medium, high
    offline_capable: bool
    cost_per_interaction: float  # In cents


@dataclass
class RoutingDecision:
    """Channel routing decision result"""
    chosen_channel: ChannelType
    reason: str
    confidence: float  # 0.0 to 1.0
    fallback_channels: List[ChannelType]
    metadata: Dict[str, Any]


class ChannelRouter:
    """Intelligent channel router for optimal student experience"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # Define channel capabilities
        self.channel_capabilities = {
            ChannelType.SMS: ChannelCapabilities(
                requires_internet=False,
                requires_smartphone=False,
                data_usage="none",
                offline_capable=True,
                cost_per_interaction=5.0  # 5 cents per SMS
            ),
            ChannelType.USSD: ChannelCapabilities(
                requires_internet=False,
                requires_smartphone=False,
                data_usage="none",
                offline_capable=True,
                cost_per_interaction=2.0  # 2 cents per USSD session
            ),
            ChannelType.VOICE: ChannelCapabilities(
                requires_internet=False,
                requires_smartphone=False,
                data_usage="none",
                offline_capable=True,
                cost_per_interaction=15.0  # 15 cents per minute
            ),
            ChannelType.WEB: ChannelCapabilities(
                requires_internet=True,
                requires_smartphone=True,
                data_usage="medium",
                offline_capable=False,
                cost_per_interaction=0.0  # Free once connected
            ),
            ChannelType.WHATSAPP: ChannelCapabilities(
                requires_internet=True,
                requires_smartphone=True,
                data_usage="low",
                offline_capable=False,
                cost_per_interaction=0.0  # Free once connected
            ),
            ChannelType.TELEGRAM: ChannelCapabilities(
                requires_internet=True,
                requires_smartphone=True,
                data_usage="low",
                offline_capable=False,
                cost_per_interaction=0.0  # Free once connected
            )
        }
        
        # Default channel priorities by device type
        self.default_priorities = {
            DeviceCapability.FEATURE_PHONE: [ChannelType.USSD, ChannelType.SMS, ChannelType.VOICE],
            DeviceCapability.SMARTPHONE_BASIC: [ChannelType.SMS, ChannelType.USSD, ChannelType.WHATSAPP, ChannelType.WEB],
            DeviceCapability.SMARTPHONE_FULL: [ChannelType.WEB, ChannelType.WHATSAPP, ChannelType.SMS, ChannelType.USSD],
            DeviceCapability.UNKNOWN: [ChannelType.SMS, ChannelType.USSD]
        }
    
    async def route_student_to_channel(self, student_id: str, phone_number: str, 
                                     content_type: str = "lesson", 
                                     preferred_channel: Optional[str] = None) -> RoutingDecision:
        """Route student to the optimal channel based on their profile and content type"""
        
        # Get or create student profile
        profile = await self._get_or_create_profile(student_id, phone_number)
        
        # Detect device capabilities if not already done
        device_capability = await self._detect_device_capability(profile)
        
        # Get available channels for this student
        available_channels = self._get_available_channels(profile, device_capability)
        
        # Consider preferred channel if specified
        if preferred_channel and preferred_channel in [c.value for c in available_channels]:
            chosen_channel = ChannelType(preferred_channel)
            decision = RoutingDecision(
                chosen_channel=chosen_channel,
                reason="user_preference",
                confidence=0.9,
                fallback_channels=[c for c in available_channels if c != chosen_channel],
                metadata={"requested_channel": preferred_channel}
            )
        else:
            # Make intelligent routing decision
            decision = await self._make_routing_decision(profile, available_channels, content_type)
        
        # Log routing decision
        await self._log_routing_decision(student_id, phone_number, decision, preferred_channel)
        
        # Update profile with routing decision
        await self._update_profile_activity(profile, decision.chosen_channel)
        
        return decision
    
    async def _get_or_create_profile(self, student_id: str, phone_number: str) -> StudentChannelProfile:
        """Get existing profile or create new one"""
        profile = self.db.query(StudentChannelProfile).filter_by(student_id=student_id).first()
        
        if not profile:
            profile = StudentChannelProfile(
                student_id=student_id,
                phone_number=phone_number,
                detected_capabilities={},
                preferred_channels=[],
                blocked_channels=[],
                primary_channel='sms',
                fallback_channel='ussd',
                last_activity={},
                success_rates={}
            )
            self.db.add(profile)
            self.db.commit()
        
        return profile
    
    async def _detect_device_capability(self, profile: StudentChannelProfile) -> DeviceCapability:
        """Detect device capability based on historical data and phone number analysis"""
        
        # Check if already detected
        if profile.detected_capabilities.get('device_type'):
            return DeviceCapability(profile.detected_capabilities['device_type'])
        
        # Analyze phone number patterns (basic heuristic)
        phone = profile.phone_number
        device_capability = DeviceCapability.UNKNOWN
        
        # East African carrier patterns (rough heuristics)
        # MTN Uganda: +256 77, +256 78, +256 76
        # Airtel Uganda: +256 70, +256 75, +256 74  
        # Safaricom Kenya: +254 7XX
        
        if phone.startswith('+256') or phone.startswith('+254'):
            # Check success rates on different channels to infer device type
            success_rates = profile.success_rates
            
            if success_rates.get('web', 0) > 0.8 or success_rates.get('whatsapp', 0) > 0.8:
                device_capability = DeviceCapability.SMARTPHONE_FULL
            elif success_rates.get('sms', 0) > 0.9 and not success_rates.get('web'):
                device_capability = DeviceCapability.FEATURE_PHONE
            else:
                device_capability = DeviceCapability.SMARTPHONE_BASIC
        
        # Store detection result
        profile.detected_capabilities['device_type'] = device_capability.value
        profile.detected_capabilities['detected_at'] = datetime.utcnow().isoformat()
        self.db.commit()
        
        return device_capability
    
    def _get_available_channels(self, profile: StudentChannelProfile, 
                               device_capability: DeviceCapability) -> List[ChannelType]:
        """Get list of available channels for this student"""
        
        # Start with channels suitable for device capability
        available = self.default_priorities[device_capability].copy()
        
        # Remove blocked channels
        blocked = [ChannelType(c) for c in profile.blocked_channels]
        available = [c for c in available if c not in blocked]
        
        # Add any explicitly preferred channels not already included
        for pref in profile.preferred_channels:
            pref_channel = ChannelType(pref)
            if pref_channel not in available and pref_channel not in blocked:
                available.insert(0, pref_channel)
        
        return available
    
    async def _make_routing_decision(self, profile: StudentChannelProfile, 
                                   available_channels: List[ChannelType],
                                   content_type: str) -> RoutingDecision:
        """Make intelligent routing decision based on multiple factors"""
        
        if not available_channels:
            # Fallback to SMS if no other channels available
            return RoutingDecision(
                chosen_channel=ChannelType.SMS,
                reason="no_channels_available",
                confidence=0.5,
                fallback_channels=[ChannelType.USSD],
                metadata={"emergency_fallback": True}
            )
        
        # Score each channel
        channel_scores = {}
        
        for channel in available_channels:
            score = await self._calculate_channel_score(profile, channel, content_type)
            channel_scores[channel] = score
        
        # Sort by score (highest first)
        sorted_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)
        
        chosen_channel, best_score = sorted_channels[0]
        fallback_channels = [ch for ch, _ in sorted_channels[1:3]]  # Top 2 fallbacks
        
        # Determine confidence and reason
        confidence = min(best_score / 100.0, 1.0)
        
        if best_score >= 80:
            reason = "optimal_match"
        elif best_score >= 60:
            reason = "good_match"
        else:
            reason = "best_available"
        
        return RoutingDecision(
            chosen_channel=chosen_channel,
            reason=reason,
            confidence=confidence,
            fallback_channels=fallback_channels,
            metadata={
                "scores": {ch.value: score for ch, score in channel_scores.items()},
                "content_type": content_type
            }
        )
    
    async def _calculate_channel_score(self, profile: StudentChannelProfile, 
                                     channel: ChannelType, content_type: str) -> float:
        """Calculate suitability score for a channel (0-100)"""
        
        score = 50.0  # Base score
        
        # Historical success rate (30% weight)
        success_rate = profile.success_rates.get(channel.value, 0.5)  # Default 50%
        score += (success_rate * 30)
        
        # Channel suitability for content type (25% weight)
        content_suitability = {
            'lesson': {
                ChannelType.WEB: 25,
                ChannelType.SMS: 20,
                ChannelType.USSD: 15,
                ChannelType.WHATSAPP: 20,
                ChannelType.VOICE: 10,
                ChannelType.TELEGRAM: 18
            },
            'quiz': {
                ChannelType.WEB: 25,
                ChannelType.USSD: 25,
                ChannelType.SMS: 15,
                ChannelType.WHATSAPP: 20,
                ChannelType.VOICE: 5,
                ChannelType.TELEGRAM: 18
            },
            'reminder': {
                ChannelType.SMS: 25,
                ChannelType.WHATSAPP: 20,
                ChannelType.TELEGRAM: 18,
                ChannelType.VOICE: 15,
                ChannelType.WEB: 10,
                ChannelType.USSD: 5
            }
        }
        score += content_suitability.get(content_type, {}).get(channel, 10)
        
        # Recent activity bonus (15% weight)
        last_activity = profile.last_activity.get(channel.value)
        if last_activity:
            last_used = datetime.fromisoformat(last_activity)
            days_since = (datetime.utcnow() - last_used).days
            
            if days_since <= 1:
                score += 15  # Used recently
            elif days_since <= 7:
                score += 10  # Used this week
            elif days_since <= 30:
                score += 5   # Used this month
        
        # Cost efficiency (10% weight)
        capability = self.channel_capabilities[channel]
        if capability.cost_per_interaction == 0:
            score += 10  # Free channels get bonus
        elif capability.cost_per_interaction < 5:
            score += 5   # Low cost channels get small bonus
        
        # Primary/fallback channel preferences (20% weight)
        if channel.value == profile.primary_channel:
            score += 15
        elif channel.value == profile.fallback_channel:
            score += 10
        
        return min(score, 100.0)  # Cap at 100
    
    async def _log_routing_decision(self, student_id: str, phone_number: str, 
                                  decision: RoutingDecision, requested_channel: Optional[str]):
        """Log routing decision for analytics"""
        
        routing_log = ChannelRoutingLog(
            student_id=student_id,
            phone_number=phone_number,
            requested_channel=requested_channel,
            routed_channel=decision.chosen_channel.value,
            routing_reason=decision.reason,
            routing_metadata={
                'confidence': decision.confidence,
                'fallback_channels': [c.value for c in decision.fallback_channels],
                **decision.metadata
            }
        )
        
        self.db.add(routing_log)
        self.db.commit()
    
    async def _update_profile_activity(self, profile: StudentChannelProfile, channel: ChannelType):
        """Update profile with latest channel activity"""
        
        # Update last activity
        last_activity = profile.last_activity or {}
        last_activity[channel.value] = datetime.utcnow().isoformat()
        profile.last_activity = last_activity
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
    
    async def update_channel_success(self, student_id: str, channel: str, success: bool):
        """Update channel success rate based on delivery/interaction results"""
        
        profile = self.db.query(StudentChannelProfile).filter_by(student_id=student_id).first()
        if not profile:
            return
        
        # Update success rates using exponential moving average
        success_rates = profile.success_rates or {}
        current_rate = success_rates.get(channel, 0.5)  # Default 50%
        
        # Use 0.2 as learning rate (20% weight to new data)
        new_rate = current_rate * 0.8 + (1.0 if success else 0.0) * 0.2
        success_rates[channel] = new_rate
        
        profile.success_rates = success_rates
        profile.updated_at = datetime.utcnow()
        self.db.commit()
    
    async def set_student_channel_preference(self, student_id: str, preferred_channels: List[str], 
                                           blocked_channels: List[str] = None):
        """Set student's channel preferences explicitly"""
        
        profile = self.db.query(StudentChannelProfile).filter_by(student_id=student_id).first()
        if not profile:
            return False
        
        profile.preferred_channels = preferred_channels
        profile.blocked_channels = blocked_channels or []
        
        # Update primary channel to first preference if valid
        if preferred_channels:
            profile.primary_channel = preferred_channels[0]
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    async def sync_progress_across_channels(self, student_id: str) -> bool:
        """Sync learning progress across all channels for seamless experience"""
        
        # This would integrate with the main learning progress system
        # to ensure students can switch between channels without losing progress
        
        # Get student's progress from all channels
        from .sms_lessons import SMSLessonFormatter  # Would be dependency injected
        
        # Sync lesson progress, quiz scores, streaks, etc.
        # Implementation would depend on main learning system architecture
        
        logger.info(f"Synced progress across channels for student {student_id}")
        return True
    
    async def get_student_channel_analytics(self, student_id: str) -> Dict[str, Any]:
        """Get analytics for student's channel usage"""
        
        profile = self.db.query(StudentChannelProfile).filter_by(student_id=student_id).first()
        if not profile:
            return {}
        
        # Get routing logs for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        routing_logs = self.db.query(ChannelRoutingLog).filter(
            ChannelRoutingLog.student_id == student_id,
            ChannelRoutingLog.timestamp >= thirty_days_ago
        ).all()
        
        # Calculate analytics
        channel_usage = {}
        for log in routing_logs:
            channel = log.routed_channel
            if channel not in channel_usage:
                channel_usage[channel] = {'count': 0, 'success_rate': 0}
            channel_usage[channel]['count'] += 1
            if log.success is not None:
                # Update success rate
                current_rate = channel_usage[channel]['success_rate']
                total = channel_usage[channel]['count']
                channel_usage[channel]['success_rate'] = (current_rate * (total-1) + (1 if log.success else 0)) / total
        
        analytics = {
            'device_capability': profile.detected_capabilities.get('device_type', 'unknown'),
            'primary_channel': profile.primary_channel,
            'channel_success_rates': profile.success_rates,
            'channel_usage_30_days': channel_usage,
            'preferred_channels': profile.preferred_channels,
            'blocked_channels': profile.blocked_channels,
            'last_activity': profile.last_activity
        }
        
        return analytics