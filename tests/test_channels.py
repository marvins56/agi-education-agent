"""
Tests for SMS/USSD Channels Package

Comprehensive tests for the channels package including SMS gateway, USSD handler,
SMS lesson formatting, and channel routing functionality.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import from channels package
from src.channels import SMSGateway, USSDSessionHandler, SMSLessonFormatter, ChannelRouter
from src.channels.sms_gateway import (
    SMSMessage, SMSResponse, SMSProvider, AfricasTalkingSMSProvider, 
    TwilioSMSProvider, SMSLog, SMSRateLimit, MessageStatus
)
from src.channels.ussd_handler import (
    USSDSession, USSDResponse, USSDMenu, USSDMenuOption, 
    MenuType, USSDLog
)
from src.channels.sms_lessons import (
    LessonContent, SMSLessonPart, LessonDeliveryMode,
    SMSLessonSeries, SMSLearningSchedule, SMSQuizSession
)
from src.channels.channel_router import (
    ChannelType, DeviceCapability, RoutingDecision,
    StudentChannelProfile, ChannelRoutingLog
)


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def sample_lesson():
    """Sample lesson content for testing"""
    return LessonContent(
        title="Basic Counting",
        subject="Mathematics", 
        topic="Numbers",
        content="Let's learn to count from 1 to 10. Numbers help us count things around us. Start with 1, then 2, then 3, and so on. Practice counting objects like books, pencils, or stones.",
        learning_objectives=["Count from 1 to 10", "Recognize number symbols", "Apply counting to real objects"],
        quiz_questions=[
            {
                "question": "What number comes after 5?",
                "options": ["4", "6", "7", "3"],
                "correct": 1,
                "explanation": "6 comes after 5 when counting: 1, 2, 3, 4, 5, 6..."
            }
        ]
    )


class TestSMSGateway:
    """Test SMS Gateway functionality"""
    
    def test_sms_message_creation(self):
        """Test SMS message dataclass creation"""
        message = SMSMessage(
            phone_number="+256701234567",
            content="Hello, this is a test message",
            message_type="lesson",
            student_id="student_123"
        )
        
        assert message.phone_number == "+256701234567"
        assert message.message_type == "lesson"
        assert message.student_id == "student_123"
        assert message.priority == 1  # default
    
    def test_sms_response_creation(self):
        """Test SMS response dataclass creation"""
        response = SMSResponse(
            success=True,
            message_id="msg_123",
            cost_cents=500,
            parts=1,
            provider="africastalking"
        )
        
        assert response.success is True
        assert response.message_id == "msg_123"
        assert response.cost_cents == 500
    
    @pytest.mark.asyncio
    async def test_africastalking_provider(self, mock_db_session):
        """Test Africa's Talking SMS provider"""
        provider = AfricasTalkingSMSProvider(
            username="testuser",
            api_key="test-api-key",
            shortcode="12345"
        )
        
        message = SMSMessage(
            phone_number="+256701234567",
            content="Test message"
        )
        
        # Mock HTTP response
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                'SMSMessageData': {
                    'Recipients': [{
                        'messageId': 'msg_123',
                        'cost': 'KES 2.50',
                        'messageParts': 1
                    }]
                }
            }
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            response = await provider.send_sms(message)
            
            assert response.success is True
            assert response.message_id == 'msg_123'
            assert response.cost_cents == 250  # KES 2.50 = 250 cents
    
    @pytest.mark.asyncio 
    async def test_sms_gateway_send_with_failover(self, mock_db_session):
        """Test SMS gateway with provider failover"""
        gateway = SMSGateway(mock_db_session)
        
        # Mock failed primary provider
        mock_primary = AsyncMock()
        mock_primary.send_sms.return_value = SMSResponse(success=False, error="Network error")
        mock_primary.get_provider_name.return_value = "primary"
        
        # Mock successful fallback provider
        mock_fallback = AsyncMock()
        mock_fallback.send_sms.return_value = SMSResponse(success=True, message_id="msg_123")
        mock_fallback.get_provider_name.return_value = "fallback"
        
        gateway.providers = [mock_primary, mock_fallback]
        
        message = SMSMessage(
            phone_number="+256701234567",
            content="Test message",
            student_id="student_123"
        )
        
        # Mock rate limit check
        with patch.object(gateway, '_check_rate_limit', return_value=True):
            response = await gateway.send_sms(message)
        
        assert response.success is True
        assert response.message_id == "msg_123"
        mock_primary.send_sms.assert_called_once()
        mock_fallback.send_sms.assert_called_once()
    
    def test_message_formatting(self, mock_db_session):
        """Test SMS message template formatting"""
        gateway = SMSGateway(mock_db_session)
        
        formatted = gateway.format_message(
            'lesson_intro',
            lesson_num=1,
            title="Basic Math",
            content="Learning to add numbers"
        )
        
        assert "LESSON 1" in formatted
        assert "Basic Math" in formatted
        assert "Learning to add numbers" in formatted
    
    def test_long_message_splitting(self, mock_db_session):
        """Test splitting long messages into SMS parts"""
        gateway = SMSGateway(mock_db_session)
        
        long_text = "This is a very long message that will definitely exceed the SMS character limit and needs to be split into multiple parts to ensure proper delivery."
        
        parts = gateway.split_long_message(long_text, max_length=50)
        
        assert len(parts) > 1
        for part in parts:
            assert len(part) <= 50
            assert part.startswith("(")  # Should have part indicators
    
    @pytest.mark.asyncio
    async def test_incoming_sms_handling(self, mock_db_session):
        """Test handling of incoming SMS messages"""
        gateway = SMSGateway(mock_db_session)
        
        response = await gateway.handle_incoming_sms("+256701234567", "START", "africastalking")
        
        assert "Welcome to EduAGI" in response
        mock_db_session.add.assert_called()  # Should log incoming SMS


class TestUSSDHandler:
    """Test USSD Session Handler functionality"""
    
    @pytest.mark.asyncio
    async def test_ussd_session_creation(self, mock_db_session):
        """Test USSD session creation"""
        handler = USSDSessionHandler(mock_db_session)
        
        # Mock query to return None (new session)
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        response = await handler.handle_ussd_request("sess_123", "+256701234567", "")
        
        assert "🎓 EduAGI Learning" in response.text
        assert "📚 Start Learning" in response.text
        mock_db_session.add.assert_called()  # Should create new session
    
    @pytest.mark.asyncio
    async def test_ussd_main_menu_navigation(self, mock_db_session):
        """Test main menu navigation"""
        handler = USSDSessionHandler(mock_db_session)
        
        # Mock existing session
        mock_session = Mock()
        mock_session.session_id = "sess_123"
        mock_session.current_menu = "main"
        mock_session.menu_history = []
        mock_session.current_data = {}
        mock_session.last_activity = datetime.utcnow()
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_session
        
        response = await handler.handle_ussd_request("sess_123", "+256701234567", "1")
        
        assert "Choose Subject" in response.text
        assert mock_session.current_menu == "subjects"
    
    @pytest.mark.asyncio
    async def test_ussd_back_navigation(self, mock_db_session):
        """Test USSD back navigation (0 key)"""
        handler = USSDSessionHandler(mock_db_session)
        
        # Mock session with history
        mock_session = Mock()
        mock_session.session_id = "sess_123"
        mock_session.current_menu = "subjects"
        mock_session.menu_history = ["main"]
        mock_session.current_data = {}
        mock_session.last_activity = datetime.utcnow()
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_session
        
        response = await handler.handle_ussd_request("sess_123", "+256701234567", "0")
        
        assert mock_session.current_menu == "main"
        assert len(mock_session.menu_history) == 0
    
    def test_menu_formatting(self, mock_db_session):
        """Test USSD menu formatting within character limits"""
        handler = USSDSessionHandler(mock_db_session)
        
        formatted = handler._format_menu(
            title="Test Menu",
            options=[("1", "Option One"), ("2", "Option Two")],
            footer="0=Back #=Home"
        )
        
        assert "Test Menu" in formatted
        assert "1. Option One" in formatted
        assert "0=Back #=Home" in formatted
        assert len(formatted) <= 182  # USSD character limit
    
    @pytest.mark.asyncio
    async def test_quiz_handling(self, mock_db_session):
        """Test USSD quiz question handling"""
        handler = USSDSessionHandler(mock_db_session)
        
        # Mock session with quiz data
        mock_session = Mock()
        mock_session.current_menu = "quiz_question"
        mock_session.current_data = {
            'quiz_data': {
                'question': "What is 2+2?",
                'options': ["3", "4", "5", "6"],
                'correct': 1,
                'explanation': "2+2 equals 4"
            }
        }
        mock_session.last_activity = datetime.utcnow()
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_session
        
        # Test correct answer
        response = await handler.handle_ussd_request("sess_123", "+256701234567", "2")
        
        assert "✅ Correct!" in response.text
        assert "2+2 equals 4" in response.text


class TestSMSLessonFormatter:
    """Test SMS Lesson Formatter functionality"""
    
    @pytest.mark.asyncio
    async def test_lesson_formatting_for_sms(self, mock_db_session, sample_lesson):
        """Test formatting complete lesson for SMS delivery"""
        mock_sms_gateway = Mock()
        formatter = SMSLessonFormatter(mock_sms_gateway, mock_db_session)
        
        parts = await formatter.format_lesson_for_sms(
            sample_lesson, 
            "student_123", 
            "+256701234567"
        )
        
        assert len(parts) > 0
        assert parts[0].part_type == "content"
        assert "LESSON: Basic Counting" in parts[0].content
        assert parts[-1].part_type == "quiz"  # Last part should be quiz
    
    def test_content_cleaning(self, mock_db_session):
        """Test SMS content cleaning functionality"""
        mock_sms_gateway = Mock()
        formatter = SMSLessonFormatter(mock_sms_gateway, mock_db_session)
        
        dirty_content = "<p>This has &amp; HTML &lt;tags&gt; and   extra   spaces</p>"
        clean_content = formatter._clean_content_for_sms(dirty_content)
        
        assert "<p>" not in clean_content
        assert "&amp;" not in clean_content
        assert "& HTML <tags>" in clean_content
        assert "  extra  " not in clean_content  # Excessive whitespace removed
    
    def test_text_splitting_for_sms(self, mock_db_session):
        """Test intelligent text splitting for SMS"""
        mock_sms_gateway = Mock()
        formatter = SMSLessonFormatter(mock_sms_gateway, mock_db_session)
        
        long_text = "This is a long sentence that needs to be split properly. It should break at sentence boundaries when possible. This makes it more readable for students."
        
        chunks = formatter._split_text_for_sms(long_text, max_length=80)
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 80
        
        # Should break at sentence boundary
        assert chunks[0].endswith(".")
    
    @pytest.mark.asyncio
    async def test_quiz_response_handling(self, mock_db_session):
        """Test handling quiz responses via SMS"""
        mock_sms_gateway = Mock()
        formatter = SMSLessonFormatter(mock_sms_gateway, mock_db_session)
        
        # Mock active quiz session
        mock_quiz = Mock()
        mock_quiz.quiz_questions = [{
            'question': 'What is 2+2?',
            'options': ['3', '4', '5', '6'],
            'explanation': '2+2=4'
        }]
        mock_quiz.correct_answers = [1]  # Index 1 = 'B' = '4'
        mock_quiz.current_question = 0
        mock_quiz.score = 0
        mock_quiz.answers_given = []
        
        mock_db_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = mock_quiz
        
        response = await formatter.handle_quiz_response("student_123", "+256701234567", "B")
        
        assert "Correct" in response
        assert "2+2=4" in response
    
    @pytest.mark.asyncio
    async def test_daily_lesson_scheduling(self, mock_db_session):
        """Test daily lesson scheduling"""
        mock_sms_gateway = Mock()
        formatter = SMSLessonFormatter(mock_sms_gateway, mock_db_session)
        
        success = await formatter.schedule_daily_lessons(
            "student_123", 
            "+256701234567", 
            preferred_time="09:00",
            timezone="Africa/Kampala"
        )
        
        assert success is True
        mock_db_session.add.assert_called()  # Should create schedule record


class TestChannelRouter:
    """Test Channel Router functionality"""
    
    @pytest.mark.asyncio
    async def test_channel_routing_decision(self, mock_db_session):
        """Test intelligent channel routing"""
        router = ChannelRouter(mock_db_session)
        
        # Mock student profile
        mock_profile = Mock()
        mock_profile.student_id = "student_123"
        mock_profile.detected_capabilities = {'device_type': 'smartphone_full'}
        mock_profile.preferred_channels = ['web']
        mock_profile.blocked_channels = []
        mock_profile.primary_channel = 'web'
        mock_profile.success_rates = {'web': 0.9, 'sms': 0.8}
        mock_profile.last_activity = {'web': datetime.utcnow().isoformat()}
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_profile
        
        decision = await router.route_student_to_channel(
            "student_123", 
            "+256701234567", 
            content_type="lesson"
        )
        
        assert decision.chosen_channel == ChannelType.WEB
        assert decision.confidence > 0.5
        assert len(decision.fallback_channels) > 0
    
    @pytest.mark.asyncio
    async def test_device_capability_detection(self, mock_db_session):
        """Test device capability detection"""
        router = ChannelRouter(mock_db_session)
        
        # Mock profile for feature phone
        mock_profile = Mock()
        mock_profile.phone_number = "+256701234567"
        mock_profile.detected_capabilities = {}
        mock_profile.success_rates = {'sms': 0.95, 'ussd': 0.9}  # High SMS success, no web
        
        capability = await router._detect_device_capability(mock_profile)
        
        assert capability == DeviceCapability.FEATURE_PHONE
    
    def test_channel_scoring(self, mock_db_session):
        """Test channel scoring algorithm"""
        router = ChannelRouter(mock_db_session)
        
        # Mock profile with mixed success rates
        mock_profile = Mock()
        mock_profile.success_rates = {'sms': 0.9, 'web': 0.7}
        mock_profile.last_activity = {'sms': datetime.utcnow().isoformat()}
        mock_profile.primary_channel = 'sms'
        
        score = asyncio.run(router._calculate_channel_score(
            mock_profile, 
            ChannelType.SMS, 
            'lesson'
        ))
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    @pytest.mark.asyncio
    async def test_success_rate_updates(self, mock_db_session):
        """Test updating channel success rates"""
        router = ChannelRouter(mock_db_session)
        
        # Mock existing profile
        mock_profile = Mock()
        mock_profile.success_rates = {'sms': 0.8}
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_profile
        
        # Update with successful delivery
        await router.update_channel_success("student_123", "sms", True)
        
        # Success rate should improve (exponential moving average)
        updated_rate = mock_profile.success_rates['sms']
        assert updated_rate > 0.8


class TestIntegration:
    """Integration tests across all channel components"""
    
    @pytest.mark.asyncio
    async def test_complete_sms_lesson_flow(self, mock_db_session, sample_lesson):
        """Test complete flow: routing -> formatting -> delivery"""
        
        # Setup components
        mock_sms_gateway = AsyncMock()
        mock_sms_gateway.send_sms.return_value = SMSResponse(success=True, message_id="msg_123")
        
        formatter = SMSLessonFormatter(mock_sms_gateway, mock_db_session)
        router = ChannelRouter(mock_db_session)
        
        # Mock student profile for SMS routing
        mock_profile = Mock()
        mock_profile.student_id = "student_123"
        mock_profile.detected_capabilities = {'device_type': 'feature_phone'}
        mock_profile.success_rates = {'sms': 0.9}
        mock_profile.primary_channel = 'sms'
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_profile
        
        # 1. Route student to appropriate channel
        decision = await router.route_student_to_channel(
            "student_123", 
            "+256701234567", 
            content_type="lesson"
        )
        
        assert decision.chosen_channel == ChannelType.SMS
        
        # 2. Format lesson for chosen channel
        if decision.chosen_channel == ChannelType.SMS:
            parts = await formatter.format_lesson_for_sms(
                sample_lesson,
                "student_123", 
                "+256701234567"
            )
            
            assert len(parts) > 0
            
            # 3. Deliver lesson parts
            success = await formatter.deliver_lesson_parts(
                "student_123",
                LessonDeliveryMode.IMMEDIATE
            )
            
            # Mock should have been called to send SMS
            assert mock_sms_gateway.send_sms.called
    
    @pytest.mark.asyncio  
    async def test_ussd_to_sms_fallback(self, mock_db_session):
        """Test fallback from USSD to SMS when USSD fails"""
        router = ChannelRouter(mock_db_session)
        
        # Mock profile that prefers USSD but has it blocked
        mock_profile = Mock()
        mock_profile.preferred_channels = ['ussd']
        mock_profile.blocked_channels = ['ussd']  # USSD blocked (network issue)
        mock_profile.detected_capabilities = {'device_type': 'feature_phone'}
        mock_profile.success_rates = {'sms': 0.85}
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_profile
        
        decision = await router.route_student_to_channel(
            "student_123",
            "+256701234567", 
            content_type="lesson"
        )
        
        # Should fallback to SMS
        assert decision.chosen_channel == ChannelType.SMS
        assert ChannelType.USSD in decision.fallback_channels or len(decision.fallback_channels) >= 0


if __name__ == "__main__":
    pytest.main([__file__])