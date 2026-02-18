"""
SMS/USSD Learning Channels Package

This package provides communication channels for students who don't have smartphones,
enabling access to EduAGI through basic SMS and USSD technologies commonly available
in rural areas of East Africa.

Channels:
- SMS Gateway: Direct SMS communication for lessons, quizzes, and progress
- USSD Handler: Interactive menu-driven learning sessions  
- SMS Lessons: Formatted lesson delivery via SMS
- Channel Router: Intelligent routing between different communication channels

Designed for maximum accessibility across feature phones and smartphones alike.
"""

from .sms_gateway import SMSGateway
from .ussd_handler import USSDSessionHandler
from .sms_lessons import SMSLessonFormatter
from .channel_router import ChannelRouter

__all__ = [
    'SMSGateway',
    'USSDSessionHandler', 
    'SMSLessonFormatter',
    'ChannelRouter'
]