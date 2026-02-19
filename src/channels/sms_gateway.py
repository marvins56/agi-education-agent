"""
SMS Gateway for EduAGI - Abstraction layer for sending/receiving SMS messages

Supports Africa's Talking (primary) and Twilio (fallback) for maximum coverage
across East African networks with automatic failover and cost optimization.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Import from main project structure
from ..config import settings
from ..models.database import get_db
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Database models for SMS tracking
Base = declarative_base()

class SMSLog(Base):
    """Track all SMS messages sent/received for cost monitoring and delivery tracking"""
    __tablename__ = 'sms_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    message_type = Column(String, nullable=False)  # lesson, quiz, reminder, response
    content = Column(Text, nullable=False)
    provider = Column(String, nullable=False)  # africastalking, twilio
    direction = Column(String, nullable=False)  # inbound, outbound
    status = Column(String, nullable=False)  # sent, delivered, failed, received
    cost_cents = Column(Integer, default=0)  # Cost in cents (US or local currency)
    parts = Column(Integer, default=1)  # Number of SMS parts for long messages
    provider_message_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    

class SMSRateLimit(Base):
    """Track SMS rate limits per student to manage costs"""
    __tablename__ = 'sms_rate_limits'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    daily_count = Column(Integer, default=0)
    weekly_count = Column(Integer, default=0) 
    monthly_count = Column(Integer, default=0)
    daily_cost_cents = Column(Integer, default=0)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(String, nullable=True)


class MessageStatus(Enum):
    """SMS delivery status enumeration"""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RECEIVED = "received"


@dataclass
class SMSMessage:
    """Structured SMS message data"""
    phone_number: str
    content: str
    message_type: str = "general"
    student_id: Optional[str] = None
    template_vars: Optional[Dict[str, Any]] = None
    priority: int = 1  # 1=high, 2=normal, 3=low
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class SMSResponse:
    """Response from SMS provider"""
    success: bool
    message_id: Optional[str] = None
    cost_cents: Optional[int] = None
    parts: int = 1
    error: Optional[str] = None
    provider: Optional[str] = None


class SMSProvider(ABC):
    """Abstract base class for SMS providers"""
    
    @abstractmethod
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send a single SMS message"""
        pass
    
    @abstractmethod
    async def check_delivery_status(self, message_id: str) -> MessageStatus:
        """Check delivery status of sent message"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name for logging"""
        pass


class AfricasTalkingSMSProvider(SMSProvider):
    """Africa's Talking SMS provider - most popular in East Africa"""
    
    def __init__(self, username: str, api_key: str, shortcode: str, environment: str = "sandbox"):
        self.username = username
        self.api_key = api_key
        self.shortcode = shortcode
        self.environment = environment
        if environment == "sandbox":
            self.base_url = "https://api.sandbox.africastalking.com/version1"
        else:
            self.base_url = "https://api.africastalking.com/version1"
        
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS via Africa's Talking API"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    'apiKey': self.api_key,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                
                data = {
                    'username': self.username,
                    'to': message.phone_number,
                    'message': message.content,
                    'from': self.shortcode
                }
                
                response = await client.post(
                    f"{self.base_url}/messaging",
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    sms_message_data = result['SMSMessageData']
                    
                    if sms_message_data['Recipients']:
                        recipient = sms_message_data['Recipients'][0]
                        return SMSResponse(
                            success=True,
                            message_id=recipient.get('messageId'),
                            cost_cents=int(float(recipient.get('cost', '0').replace('KES ', '')) * 100),
                            parts=recipient.get('messageParts', 1),
                            provider="africastalking"
                        )
                    else:
                        return SMSResponse(
                            success=False,
                            error="No recipients in response",
                            provider="africastalking"
                        )
                else:
                    return SMSResponse(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                        provider="africastalking"
                    )
                    
        except Exception as e:
            logger.error(f"Africa's Talking SMS failed: {str(e)}")
            return SMSResponse(
                success=False,
                error=str(e),
                provider="africastalking"
            )
    
    async def check_delivery_status(self, message_id: str) -> MessageStatus:
        """Check delivery status (Africa's Talking doesn't provide easy status checking)"""
        # In production, you'd implement webhook handling for delivery reports
        return MessageStatus.SENT
        
    def get_provider_name(self) -> str:
        return "africastalking"


class TwilioSMSProvider(SMSProvider):
    """Twilio SMS provider as fallback option"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
        
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS via Twilio API"""
        try:
            import base64
            
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            
            async with httpx.AsyncClient() as client:
                headers = {
                    'Authorization': f'Basic {auth_bytes}',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                data = {
                    'To': message.phone_number,
                    'From': self.from_number,
                    'Body': message.content
                }
                
                response = await client.post(
                    f"{self.base_url}/Messages.json",
                    headers=headers,
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code == 201:
                    result = response.json()
                    return SMSResponse(
                        success=True,
                        message_id=result.get('sid'),
                        cost_cents=int(float(result.get('price', '0')) * -100),  # Twilio prices are negative
                        parts=int(result.get('num_segments', 1)),
                        provider="twilio"
                    )
                else:
                    return SMSResponse(
                        success=False,
                        error=f"HTTP {response.status_code}: {response.text}",
                        provider="twilio"
                    )
                    
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return SMSResponse(
                success=False,
                error=str(e),
                provider="twilio"
            )
    
    async def check_delivery_status(self, message_id: str) -> MessageStatus:
        """Check delivery status via Twilio API"""
        try:
            import base64
            
            auth_string = f"{self.account_sid}:{self.auth_token}"
            auth_bytes = base64.b64encode(auth_string.encode()).decode()
            
            async with httpx.AsyncClient() as client:
                headers = {'Authorization': f'Basic {auth_bytes}'}
                
                response = await client.get(
                    f"{self.base_url}/Messages/{message_id}.json",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', '').lower()
                    
                    status_map = {
                        'queued': MessageStatus.QUEUED,
                        'sending': MessageStatus.SENT,
                        'sent': MessageStatus.SENT,
                        'delivered': MessageStatus.DELIVERED,
                        'failed': MessageStatus.FAILED,
                        'undelivered': MessageStatus.FAILED
                    }
                    
                    return status_map.get(status, MessageStatus.SENT)
                    
        except Exception as e:
            logger.error(f"Twilio status check failed: {str(e)}")
            
        return MessageStatus.SENT
        
    def get_provider_name(self) -> str:
        return "twilio"


class SMSGateway:
    """Main SMS Gateway class with provider failover and rate limiting"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.providers: List[SMSProvider] = []
        self.message_templates: Dict[str, str] = {}
        self.rate_limits = {
            'daily_limit': 10,      # Max SMS per student per day
            'weekly_limit': 50,     # Max SMS per student per week  
            'monthly_limit': 200,   # Max SMS per student per month
            'cost_limit_cents': 1000 # Max cost per student per month (in cents)
        }
        
        # Initialize providers
        self._initialize_providers()
        self._load_message_templates()
        
    def _initialize_providers(self):
        """Initialize SMS providers from configuration"""
        # Africa's Talking as primary
        if getattr(settings, 'AFRICASTALKING_API_KEY', ''):
            africastalking = AfricasTalkingSMSProvider(
                username=settings.AFRICASTALKING_USERNAME,
                api_key=settings.AFRICASTALKING_API_KEY,
                shortcode=getattr(settings, 'AFRICASTALKING_SHORTCODE', ''),
                environment=getattr(settings, 'AFRICASTALKING_ENVIRONMENT', 'sandbox')
            )
            self.providers.append(africastalking)
            
        # Twilio as fallback
        if hasattr(settings, 'TWILIO_ACCOUNT_SID'):
            twilio = TwilioSMSProvider(
                account_sid=settings.TWILIO_ACCOUNT_SID,
                auth_token=settings.TWILIO_AUTH_TOKEN,
                from_number=settings.TWILIO_FROM_NUMBER
            )
            self.providers.append(twilio)
            
        if not self.providers:
            logger.warning("No SMS providers configured!")
            
    def _load_message_templates(self):
        """Load SMS message templates"""
        self.message_templates = {
            'welcome': "Welcome to EduAGI! Reply START to begin learning. Reply HELP for commands. Free lessons via SMS & USSD.",
            'lesson_intro': "📚 LESSON {lesson_num}: {title}\n\n{content}\n\nReply NEXT for more or QUIZ to test knowledge.",
            'quiz_question': "❓ Q{question_num}: {question}\n\nA) {option_a}\nB) {option_b}\nC) {option_c}\nD) {option_d}\n\nReply A,B,C or D",
            'quiz_correct': "✅ Correct! {explanation}\n\nScore: {score}/{total}. Reply NEXT for next question or FINISH to complete.",
            'quiz_incorrect': "❌ Incorrect. Correct answer: {correct_answer}\n\n{explanation}\n\nReply NEXT or REVIEW to study again.",
            'progress_report': "📊 Weekly Progress:\n✅ {lessons_completed} lessons\n🏆 {quizzes_passed} quizzes passed\n📈 {streak} day streak!\n\nKeep learning! 🚀",
            'streak_reminder': "🔥 {streak} day streak! Don't break it. Complete today's lesson: {lesson_title}. Reply LESSON to start.",
            'help': "EduAGI Commands:\nSTART - Begin learning\nLESSON - Get daily lesson\nQUIZ - Take a quiz\nPROGRESS - View stats\nHELP - Show commands\nSTOP - Unsubscribe"
        }
    
    async def send_sms(self, message: SMSMessage) -> SMSResponse:
        """Send SMS with automatic provider failover"""
        # Check rate limits first
        if not await self._check_rate_limit(message.student_id, message.phone_number):
            return SMSResponse(
                success=False,
                error="Rate limit exceeded for student"
            )
        
        # Try each provider until one succeeds
        last_error = None
        for provider in self.providers:
            try:
                response = await provider.send_sms(message)
                
                # Log the attempt
                await self._log_sms_attempt(message, response, provider.get_provider_name())
                
                if response.success:
                    # Update rate limits
                    await self._update_rate_limits(message.student_id, message.phone_number, response.cost_cents or 0)
                    return response
                else:
                    last_error = response.error
                    logger.warning(f"SMS failed via {provider.get_provider_name()}: {response.error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"SMS provider {provider.get_provider_name()} exception: {e}")
                continue
        
        # All providers failed
        return SMSResponse(
            success=False,
            error=f"All providers failed. Last error: {last_error}"
        )
    
    def format_message(self, template_key: str, **kwargs) -> str:
        """Format a message using templates with variable substitution"""
        template = self.message_templates.get(template_key, template_key)
        
        try:
            # Handle character limit (160 chars per SMS part)
            formatted = template.format(**kwargs)
            return self._truncate_for_sms(formatted)
        except KeyError as e:
            logger.error(f"Missing template variable {e} for template {template_key}")
            return template  # Return unformatted template as fallback
    
    def _truncate_for_sms(self, text: str, max_length: int = 160) -> str:
        """Truncate text to fit SMS character limits"""
        if len(text) <= max_length:
            return text
        
        # Try to break at word boundary
        truncated = text[:max_length-3]
        if ' ' in truncated:
            truncated = truncated.rsplit(' ', 1)[0]
        
        return truncated + "..."
    
    def split_long_message(self, text: str, max_length: int = 160) -> List[str]:
        """Split long messages into multiple SMS parts"""
        if len(text) <= max_length:
            return [text]
        
        parts = []
        remaining = text
        part_num = 1
        
        while remaining:
            # Reserve space for part indicator like "(1/3)"
            available_length = max_length - 6
            
            if len(remaining) <= available_length:
                parts.append(f"({part_num}/{len(parts)+1}) {remaining}")
                break
            
            # Find good break point
            chunk = remaining[:available_length]
            if ' ' in chunk:
                split_pos = chunk.rfind(' ')
                chunk = chunk[:split_pos]
            
            parts.append(f"({part_num}/{len(parts)+1}) {chunk}")
            remaining = remaining[len(chunk):].lstrip()
            part_num += 1
        
        # Update part indicators with actual count
        total_parts = len(parts)
        parts = [part.replace(f"/{len(parts)+1})", f"/{total_parts})") for part in parts]
        
        return parts
    
    async def _check_rate_limit(self, student_id: str, phone_number: str) -> bool:
        """Check if student is within SMS rate limits"""
        if not student_id:
            return True  # Skip rate limiting for anonymous messages
        
        rate_limit = self.db.query(SMSRateLimit).filter_by(student_id=student_id).first()
        
        if not rate_limit:
            # Create new rate limit record
            rate_limit = SMSRateLimit(
                student_id=student_id,
                phone_number=phone_number
            )
            self.db.add(rate_limit)
            self.db.commit()
            return True
        
        # Check if limits are exceeded
        now = datetime.utcnow()
        if (now - rate_limit.last_reset_date).days >= 1:
            # Reset daily counters
            rate_limit.daily_count = 0
            rate_limit.daily_cost_cents = 0
            rate_limit.last_reset_date = now
        
        if rate_limit.is_blocked:
            logger.warning(f"Student {student_id} is blocked from SMS: {rate_limit.block_reason}")
            return False
        
        # Check limits
        limits_ok = (
            rate_limit.daily_count < self.rate_limits['daily_limit'] and
            rate_limit.weekly_count < self.rate_limits['weekly_limit'] and
            rate_limit.monthly_count < self.rate_limits['monthly_limit'] and
            rate_limit.daily_cost_cents < self.rate_limits['cost_limit_cents']
        )
        
        return limits_ok
    
    async def _update_rate_limits(self, student_id: str, phone_number: str, cost_cents: int):
        """Update rate limit counters after successful SMS send"""
        if not student_id:
            return
        
        rate_limit = self.db.query(SMSRateLimit).filter_by(student_id=student_id).first()
        if rate_limit:
            rate_limit.daily_count += 1
            rate_limit.weekly_count += 1
            rate_limit.monthly_count += 1
            rate_limit.daily_cost_cents += cost_cents
            self.db.commit()
    
    async def _log_sms_attempt(self, message: SMSMessage, response: SMSResponse, provider: str):
        """Log SMS sending attempt for tracking and analytics"""
        sms_log = SMSLog(
            student_id=message.student_id,
            phone_number=message.phone_number,
            message_type=message.message_type,
            content=message.content,
            provider=provider,
            direction="outbound",
            status="sent" if response.success else "failed",
            cost_cents=response.cost_cents or 0,
            parts=response.parts,
            provider_message_id=response.message_id
        )
        
        self.db.add(sms_log)
        self.db.commit()
    
    async def handle_incoming_sms(self, from_number: str, content: str, provider: str = "unknown") -> Optional[str]:
        """Handle incoming SMS from students and generate appropriate responses"""
        content = content.strip().upper()
        
        # Log incoming SMS
        sms_log = SMSLog(
            student_id=None,  # Will be resolved later
            phone_number=from_number,
            message_type="response",
            content=content,
            provider=provider,
            direction="inbound",
            status="received"
        )
        self.db.add(sms_log)
        self.db.commit()
        
        # Route common commands
        command_handlers = {
            'START': self._handle_start_command,
            'HELP': self._handle_help_command,
            'LESSON': self._handle_lesson_command,
            'QUIZ': self._handle_quiz_command,
            'PROGRESS': self._handle_progress_command,
            'STOP': self._handle_stop_command,
            'NEXT': self._handle_next_command,
            'REVIEW': self._handle_review_command,
            'FINISH': self._handle_finish_command,
        }
        
        # Check for single letter quiz answers
        if content in ['A', 'B', 'C', 'D']:
            return await self._handle_quiz_answer(from_number, content)
        
        # Check for command keywords
        for command, handler in command_handlers.items():
            if content.startswith(command):
                return await handler(from_number, content)
        
        # Default response for unrecognized input
        return self.format_message('help')
    
    async def _handle_start_command(self, phone_number: str, content: str) -> str:
        """Handle START command from new students"""
        return self.format_message('welcome')
    
    async def _handle_help_command(self, phone_number: str, content: str) -> str:
        """Handle HELP command"""
        return self.format_message('help')
    
    async def _handle_lesson_command(self, phone_number: str, content: str) -> str:
        """Handle LESSON request - would integrate with curriculum system"""
        # This would integrate with the main EduAGI curriculum system
        return "📚 Today's Lesson: Introduction to Mathematics\n\nNumbers are symbols we use to count things. 1, 2, 3, 4, 5...\n\nReply QUIZ to test your knowledge!"
    
    async def _handle_quiz_command(self, phone_number: str, content: str) -> str:
        """Handle QUIZ request"""
        return self.format_message('quiz_question',
                                   question_num=1,
                                   question="What comes after the number 5?",
                                   option_a="4",
                                   option_b="6", 
                                   option_c="3",
                                   option_d="7")
    
    async def _handle_progress_command(self, phone_number: str, content: str) -> str:
        """Handle PROGRESS request"""
        # Would integrate with progress tracking system
        return self.format_message('progress_report',
                                   lessons_completed=12,
                                   quizzes_passed=8,
                                   streak=3)
    
    async def _handle_quiz_answer(self, phone_number: str, answer: str) -> str:
        """Handle quiz answer submission"""
        # This would integrate with the quiz system to check answers
        if answer == 'B':  # Correct answer from example above
            return self.format_message('quiz_correct',
                                       explanation="Great! 6 comes after 5 in counting.",
                                       score=1,
                                       total=1)
        else:
            return self.format_message('quiz_incorrect',
                                       correct_answer="B) 6",
                                       explanation="When counting, each number is 1 more than the previous.")
    
    async def _handle_next_command(self, phone_number: str, content: str) -> str:
        """Handle NEXT command for continuing lessons/quizzes"""
        return "Moving to next section... Reply LESSON for today's content or QUIZ to practice!"
    
    async def _handle_review_command(self, phone_number: str, content: str) -> str:
        """Handle REVIEW command to revisit content"""
        return "📖 Review Mode: Let's go over the lesson again.\n\nNumbers: 1, 2, 3, 4, 5, 6...\n\nReply QUIZ when ready to test again!"
    
    async def _handle_finish_command(self, phone_number: str, content: str) -> str:
        """Handle FINISH command to complete current session"""
        return "🎉 Great work today! You've completed the lesson.\n\nReply PROGRESS to see stats or LESSON tomorrow for more learning!"
    
    async def _handle_stop_command(self, phone_number: str, content: str) -> str:
        """Handle STOP/unsubscribe command"""
        # Would integrate with subscription management
        return "You have been unsubscribed from EduAGI SMS lessons. Reply START anytime to resume learning. Thank you!"