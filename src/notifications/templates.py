"""
Notification Templates - Multi-language template management

This module provides template management for notifications across different
event types, delivery channels, and languages. Templates support personalization
and maintain appropriate tone for different user types (students, parents, teachers).
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .engine import EventType, DeliveryChannel

logger = logging.getLogger(__name__)


@dataclass
class RenderedTemplate:
    """Rendered template content"""
    title: str
    message: str
    data: Dict[str, Any]


class NotificationTemplate(ABC):
    """Base class for notification templates"""
    
    def __init__(self, event_type: EventType, channel: DeliveryChannel, 
                 language: str = "en"):
        self.event_type = event_type
        self.channel = channel
        self.language = language
    
    @abstractmethod
    async def render(self, user_id: str, **context) -> RenderedTemplate:
        """Render template with given context"""
        pass
    
    def _get_user_name(self, user_id: str) -> str:
        """Get user's display name (mock implementation)"""
        # In production, this would fetch from user database
        return f"Student_{user_id[-4:]}"
    
    def _format_time(self, datetime_str: str, language: str = "en") -> str:
        """Format datetime string for display"""
        # Simplified time formatting
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            if language == "sw":  # Swahili
                return dt.strftime("%H:%M, %d/%m/%Y")
            elif language == "lg":  # Luganda
                return dt.strftime("%H:%M, %d/%m/%Y")
            else:  # English
                return dt.strftime("%I:%M %p, %B %d, %Y")
        except:
            return datetime_str


class LessonReminderTemplate(NotificationTemplate):
    """Templates for lesson reminders"""
    
    async def render(self, user_id: str, **context) -> RenderedTemplate:
        user_name = self._get_user_name(user_id)
        lesson_name = context.get('lesson_name', 'your lesson')
        lesson_time = context.get('lesson_time', '')
        
        templates = {
            "en": {
                DeliveryChannel.PUSH: {
                    "title": f"📚 Time to Learn, {user_name}!",
                    "message": f"Your {lesson_name} session starts in 15 minutes. Ready to grow your knowledge?"
                },
                DeliveryChannel.SMS: {
                    "title": "Study Time!",
                    "message": f"Hi {user_name}! Your {lesson_name} lesson starts soon. Open EduAGI to continue learning!"
                },
                DeliveryChannel.EMAIL: {
                    "title": f"Lesson Reminder: {lesson_name}",
                    "message": f"Dear {user_name},\n\nThis is a friendly reminder that your {lesson_name} lesson is scheduled to start soon.\n\nKeep up the great work!\n\nBest regards,\nEduAGI Team"
                }
            },
            "sw": {  # Swahili
                DeliveryChannel.PUSH: {
                    "title": f"📚 Wakati wa Kujifunza, {user_name}!",
                    "message": f"Kipindi chako cha {lesson_name} kinaanza baada ya dakika 15. Uko tayari kuongeza ujuzi?"
                },
                DeliveryChannel.SMS: {
                    "title": "Wakati wa Masomo!",
                    "message": f"Hujambo {user_name}! Somo lako la {lesson_name} linaanza hivi karibuni. Fungua EduAGI kuendelea kujifunza!"
                },
                DeliveryChannel.EMAIL: {
                    "title": f"Ukumbusho wa Somo: {lesson_name}",
                    "message": f"Mpendwa {user_name},\n\nHuu ni ukumbusho wa kirafiki kuwa somo lako la {lesson_name} limepangwa kuanza hivi karibuni.\n\nEndelea kufanya kazi nzuri!\n\nHeshima zetu,\nTimu ya EduAGI"
                }
            },
            "lg": {  # Luganda
                DeliveryChannel.PUSH: {
                    "title": f"📚 Kiseera ky'Okuyiga, {user_name}!",
                    "message": f"Essomo lyo elya {lesson_name} litandika mu ddakiika 15. Oli mwetegefu okwongera amagezi?"
                },
                DeliveryChannel.SMS: {
                    "title": "Kiseera ky'Essomo!",
                    "message": f"Oli otya {user_name}! Essomo lyo elya {lesson_name} litandika mu kaseera katono. Gula EduAGI okusigala ng'oyiga!"
                },
                DeliveryChannel.EMAIL: {
                    "title": f"Okujjukiza Essomo: {lesson_name}",
                    "message": f"Omwagalwa {user_name},\n\nKino kijjukizo eky'obwenzi nti essomo lyo elya {lesson_name} liteekeddwa okutandika mu kaseera katono.\n\nWeyongere okukola omulimu omulungi!\n\nEkitiibwa,\nEkibinja kya EduAGI"
                }
            }
        }
        
        template = templates.get(self.language, templates["en"]).get(
            self.channel, templates[self.language][DeliveryChannel.PUSH]
        )
        
        return RenderedTemplate(
            title=template["title"],
            message=template["message"],
            data=context
        )


class StreakWarningTemplate(NotificationTemplate):
    """Templates for streak warnings"""
    
    async def render(self, user_id: str, **context) -> RenderedTemplate:
        user_name = self._get_user_name(user_id)
        streak_count = context.get('streak_count', 0)
        days_missed = context.get('days_missed', 1)
        
        templates = {
            "en": {
                DeliveryChannel.PUSH: {
                    "title": f"⚡ Don't Break Your Streak!",
                    "message": f"Hey {user_name}! You've missed {days_missed} day(s). Keep your {streak_count}-day learning streak alive!"
                },
                DeliveryChannel.SMS: {
                    "title": "Streak Alert!",
                    "message": f"Hi {user_name}! Your {streak_count}-day streak is at risk. Jump back in and keep learning!"
                }
            },
            "sw": {
                DeliveryChannel.PUSH: {
                    "title": f"⚡ Usiivunje Mfumo Wako!",
                    "message": f"Hujambo {user_name}! Umekosa siku {days_missed}. Endelea na mfumo wako wa kujifunza wa siku {streak_count}!"
                },
                DeliveryChannel.SMS: {
                    "title": "Tahadhari ya Mfumo!",
                    "message": f"Hujambo {user_name}! Mfumo wako wa siku {streak_count} uko hatarini. Rudi na uendelee kujifunza!"
                }
            },
            "lg": {
                DeliveryChannel.PUSH: {
                    "title": f"⚡ Tosigula Olunyiriri Lwo!",
                    "message": f"Oli otya {user_name}! Obusizzeko ennaku {days_missed}. Sigala n'olunyiriri lwo olw'okuyiga olw'ennaku {streak_count}!"
                },
                DeliveryChannel.SMS: {
                    "title": "Okulabula Olunyiriri!",
                    "message": f"Oli otya {user_name}! Olunyiriri lwo olw'ennaku {streak_count} luli mu katyabaga. Ddayo oyige!"
                }
            }
        }
        
        template = templates.get(self.language, templates["en"]).get(
            self.channel, templates[self.language][DeliveryChannel.PUSH]
        )
        
        return RenderedTemplate(
            title=template["title"],
            message=template["message"],
            data=context
        )


class AchievementTemplate(NotificationTemplate):
    """Templates for achievement notifications"""
    
    async def render(self, user_id: str, **context) -> RenderedTemplate:
        user_name = self._get_user_name(user_id)
        achievement_name = context.get('achievement_name', 'Great Work')
        achievement_description = context.get('achievement_description', '')
        
        templates = {
            "en": {
                DeliveryChannel.PUSH: {
                    "title": f"🎉 Achievement Unlocked!",
                    "message": f"Amazing work, {user_name}! You've earned '{achievement_name}'. Keep up the fantastic progress!"
                },
                DeliveryChannel.SMS: {
                    "title": "🏆 New Achievement!",
                    "message": f"Congratulations {user_name}! You've unlocked '{achievement_name}'. You're doing great!"
                }
            },
            "sw": {
                DeliveryChannel.PUSH: {
                    "title": f"🎉 Umefikia Lengo!",
                    "message": f"Kazi nzuri sana, {user_name}! Umepata '{achievement_name}'. Endelea na maendeleo mazuri!"
                },
                DeliveryChannel.SMS: {
                    "title": "🏆 Lengo Jipya!",
                    "message": f"Pongezi {user_name}! Umefungua '{achievement_name}'. Unafanya vizuri!"
                }
            },
            "lg": {
                DeliveryChannel.PUSH: {
                    "title": f"🎉 Otuuse ku Kigenderwamu!",
                    "message": f"Omulimu omulungi nnyo, {user_name}! Ofunye '{achievement_name}'. Weyongere n'enkulaakulana ennungi!"
                },
                DeliveryChannel.SMS: {
                    "title": "🏆 Ekigenderwamu Ekipya!",
                    "message": f"Okwebaze {user_name}! Ogguddeko '{achievement_name}'. Okola bulungi!"
                }
            }
        }
        
        template = templates.get(self.language, templates["en"]).get(
            self.channel, templates[self.language][DeliveryChannel.PUSH]
        )
        
        return RenderedTemplate(
            title=template["title"],
            message=template["message"],
            data=context
        )


class ParentReportTemplate(NotificationTemplate):
    """Templates for parent reports (professional tone)"""
    
    async def render(self, user_id: str, **context) -> RenderedTemplate:
        student_name = context.get('student_name', 'Your child')
        week_number = context.get('week_number', 1)
        lessons_completed = context.get('lessons_completed', 0)
        total_lessons = context.get('total_lessons', 0)
        
        completion_rate = (lessons_completed / total_lessons * 100) if total_lessons > 0 else 0
        
        templates = {
            "en": {
                DeliveryChannel.EMAIL: {
                    "title": f"Weekly Progress Report - {student_name}",
                    "message": f"Dear Parent,\n\nHere's {student_name}'s learning progress for Week {week_number}:\n\n• Lessons completed: {lessons_completed}/{total_lessons} ({completion_rate:.1f}%)\n• Overall performance: {'Excellent' if completion_rate >= 80 else 'Good' if completion_rate >= 60 else 'Needs improvement'}\n\nThank you for supporting your child's education.\n\nBest regards,\nEduAGI Team"
                },
                DeliveryChannel.SMS: {
                    "title": "Weekly Report",
                    "message": f"{student_name}'s Week {week_number} progress: {lessons_completed}/{total_lessons} lessons completed ({completion_rate:.1f}%). Keep encouraging their learning!"
                }
            },
            "sw": {
                DeliveryChannel.EMAIL: {
                    "title": f"Ripoti ya Kila Wiki - {student_name}",
                    "message": f"Mzazi mpendwa,\n\nHapa kuna maendeleo ya kujifunza ya {student_name} kwa Wiki ya {week_number}:\n\n• Masomo yaliyokamilishwa: {lessons_completed}/{total_lessons} ({completion_rate:.1f}%)\n• Utendaji wa jumla: {'Bora sana' if completion_rate >= 80 else 'Nzuri' if completion_rate >= 60 else 'Inahitaji uboreshwaji'}\n\nAsante kwa kuunga mkono elimu ya mtoto wako.\n\nHeshima zetu,\nTimu ya EduAGI"
                },
                DeliveryChannel.SMS: {
                    "title": "Ripoti ya Wiki",
                    "message": f"Maendeleo ya {student_name} Wiki {week_number}: masomo {lessons_completed}/{total_lessons} yamekamilishwa ({completion_rate:.1f}%). Endelea kumtia moyo!"
                }
            }
        }
        
        template = templates.get(self.language, templates["en"]).get(
            self.channel, templates[self.language][DeliveryChannel.EMAIL]
        )
        
        return RenderedTemplate(
            title=template["title"],
            message=template["message"],
            data=context
        )


class TemplateManager:
    """Manages all notification templates"""
    
    def __init__(self):
        self.template_classes = {
            EventType.LESSON_REMINDER: LessonReminderTemplate,
            EventType.STREAK_WARNING: StreakWarningTemplate,
            EventType.ACHIEVEMENT_UNLOCKED: AchievementTemplate,
            EventType.PARENT_REPORT: ParentReportTemplate,
        }
        logger.info("TemplateManager initialized")
    
    async def get_templates(self, event_type: EventType, language: str = "en",
                          channels: List[DeliveryChannel] = None) -> Dict[DeliveryChannel, NotificationTemplate]:
        """Get templates for specific event type and channels"""
        
        if channels is None:
            channels = [DeliveryChannel.PUSH]
        
        template_class = self.template_classes.get(event_type)
        if not template_class:
            logger.warning(f"No template found for event type: {event_type}")
            return {}
        
        templates = {}
        for channel in channels:
            try:
                template = template_class(event_type, channel, language)
                templates[channel] = template
            except Exception as e:
                logger.error(f"Error creating template for {event_type}-{channel}-{language}: {e}")
        
        return templates
    
    def register_template(self, event_type: EventType, template_class):
        """Register a custom template class for an event type"""
        self.template_classes[event_type] = template_class
        logger.info(f"Registered template for {event_type}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return ["en", "sw", "lg"]
    
    def get_supported_channels(self) -> List[DeliveryChannel]:
        """Get list of supported delivery channels"""
        return list(DeliveryChannel)