"""
USSD Session Handler for EduAGI - Interactive menu-driven learning via USSD

Provides educational content through USSD menus that work on ANY phone, including
basic feature phones without internet connectivity. Critical for rural students.
"""

import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

# Import from main project structure
from ..config import settings
from ..models.database import get_db
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Database models for USSD session management
Base = declarative_base()

class USSDSession(Base):
    """Track USSD sessions (USSD is stateless, so we maintain state server-side)"""
    __tablename__ = 'ussd_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, index=True, nullable=False)
    student_id = Column(String, index=True, nullable=True)
    current_menu = Column(String, nullable=False, default='main')
    menu_history = Column(JSON, nullable=False, default=list)  # Stack for navigation
    current_data = Column(JSON, nullable=False, default=dict)  # Store current lesson/quiz state
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class USSDLog(Base):
    """Log all USSD interactions for analytics"""
    __tablename__ = 'ussd_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    user_input = Column(String, nullable=True)
    menu_displayed = Column(String, nullable=False)
    response_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class MenuType(Enum):
    """USSD menu types"""
    MAIN = "main"
    SUBJECTS = "subjects"
    TOPICS = "topics"
    LESSONS = "lessons"
    LESSON_CONTENT = "lesson_content"
    QUIZ = "quiz"
    QUIZ_QUESTION = "quiz_question"
    PROGRESS = "progress"
    PROFILE = "profile"
    HELP = "help"


@dataclass
class USSDMenuOption:
    """Individual menu option"""
    key: str
    text: str
    action: str
    data: Optional[Dict[str, Any]] = None


@dataclass
class USSDMenu:
    """Complete USSD menu structure"""
    title: str
    options: List[USSDMenuOption]
    footer: Optional[str] = None
    menu_type: MenuType = MenuType.MAIN


@dataclass
class USSDResponse:
    """USSD response to send back to user"""
    text: str
    end_session: bool = False


class USSDSessionHandler:
    """Main USSD session handler with menu navigation and educational content"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.session_timeout = timedelta(minutes=10)  # USSD sessions expire after 10 min
        self.max_text_length = 182  # USSD character limit
        
        # Educational content structure (in production, this would come from curriculum system)
        self.subjects = {
            "1": {"name": "Mathematics", "topics": {
                "1": {"name": "Basic Numbers", "lessons": ["Counting 1-10", "Addition Basics", "Subtraction Basics"]},
                "2": {"name": "Shapes", "lessons": ["Circles & Squares", "Triangles", "Rectangle"]},
                "3": {"name": "Time", "lessons": ["Reading Clock", "Days of Week", "Months"]}
            }},
            "2": {"name": "English", "topics": {
                "1": {"name": "Alphabet", "lessons": ["Letters A-M", "Letters N-Z", "Letter Sounds"]},
                "2": {"name": "Words", "lessons": ["Simple Words", "Action Words", "Animal Names"]},
                "3": {"name": "Sentences", "lessons": ["Making Sentences", "Questions", "Stories"]}
            }},
            "3": {"name": "Science", "topics": {
                "1": {"name": "Animals", "lessons": ["Farm Animals", "Wild Animals", "Animal Homes"]},
                "2": {"name": "Plants", "lessons": ["Parts of Plant", "How Plants Grow", "Trees & Flowers"]},
                "3": {"name": "Weather", "lessons": ["Sun & Rain", "Hot & Cold", "Seasons"]}
            }}
        }
        
        # Sample lesson content (would be loaded from curriculum system)
        self.lesson_content = {
            "Counting 1-10": {
                "content": "Let's learn numbers!\n\n1 - One\n2 - Two\n3 - Three\n4 - Four\n5 - Five\n\nPractice counting objects around you!",
                "quiz": {
                    "question": "What number comes after 3?",
                    "options": ["2", "4", "5", "1"],
                    "correct": 1,  # Index of correct answer (4)
                    "explanation": "4 comes after 3 when counting: 1, 2, 3, 4, 5..."
                }
            }
        }
    
    async def handle_ussd_request(self, session_id: str, phone_number: str, user_input: str = "") -> USSDResponse:
        """Handle incoming USSD request and return appropriate response"""
        try:
            # Get or create session
            session = await self._get_or_create_session(session_id, phone_number)
            
            # Check session timeout
            if not self._is_session_valid(session):
                await self._cleanup_expired_session(session)
                return USSDResponse(
                    text="Session expired. Dial again to start fresh.",
                    end_session=True
                )
            
            # Process user input and generate response
            response = await self._process_user_input(session, user_input)
            
            # Log interaction
            await self._log_ussd_interaction(session, user_input, response.text)
            
            # Update session activity
            session.last_activity = datetime.utcnow()
            self.db.commit()
            
            return response
            
        except Exception as e:
            logger.error(f"USSD handler error: {str(e)}")
            return USSDResponse(
                text="Sorry, something went wrong. Please try again.",
                end_session=True
            )
    
    async def _get_or_create_session(self, session_id: str, phone_number: str) -> USSDSession:
        """Get existing session or create new one"""
        session = self.db.query(USSDSession).filter_by(session_id=session_id).first()
        
        if not session:
            session = USSDSession(
                session_id=session_id,
                phone_number=phone_number,
                current_menu='main',
                menu_history=[],
                current_data={}
            )
            self.db.add(session)
            self.db.commit()
        
        return session
    
    def _is_session_valid(self, session: USSDSession) -> bool:
        """Check if session is still valid (not expired)"""
        return (datetime.utcnow() - session.last_activity) < self.session_timeout
    
    async def _cleanup_expired_session(self, session: USSDSession):
        """Clean up expired session"""
        session.is_active = False
        self.db.commit()
    
    async def _process_user_input(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Process user input based on current menu state"""
        user_input = user_input.strip()
        
        # Handle special navigation commands
        if user_input == "0":
            return await self._handle_back_navigation(session)
        elif user_input == "#":
            return await self._handle_home_navigation(session)
        elif user_input == "*":
            return await self._handle_help_menu(session)
        
        # Route to appropriate handler based on current menu
        menu_handlers = {
            'main': self._handle_main_menu,
            'subjects': self._handle_subjects_menu,
            'topics': self._handle_topics_menu,
            'lessons': self._handle_lessons_menu,
            'lesson_content': self._handle_lesson_content,
            'quiz': self._handle_quiz_menu,
            'quiz_question': self._handle_quiz_question,
            'progress': self._handle_progress_menu,
            'profile': self._handle_profile_menu,
            'help': self._handle_help_menu
        }
        
        handler = menu_handlers.get(session.current_menu, self._handle_main_menu)
        return await handler(session, user_input)
    
    async def _handle_main_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle main menu navigation"""
        if not user_input:  # First time - show welcome menu
            menu_text = self._format_menu(
                title="🎓 EduAGI Learning",
                options=[
                    ("1", "📚 Start Learning"),
                    ("2", "📊 My Progress"),
                    ("3", "👤 My Profile"),
                    ("4", "❓ Help")
                ],
                footer="0=Back  #=Home  *=Help"
            )
            return USSDResponse(text=menu_text)
        
        # Handle menu selection
        if user_input == "1":
            session.current_menu = 'subjects'
            session.menu_history.append('main')
            self.db.commit()
            return await self._handle_subjects_menu(session, "")
        elif user_input == "2":
            session.current_menu = 'progress'
            session.menu_history.append('main')
            self.db.commit()
            return await self._handle_progress_menu(session, "")
        elif user_input == "3":
            session.current_menu = 'profile'
            session.menu_history.append('main')
            self.db.commit()
            return await self._handle_profile_menu(session, "")
        elif user_input == "4":
            return await self._handle_help_menu(session, "")
        else:
            return USSDResponse(text="Invalid option. Please select 1-4.")
    
    async def _handle_subjects_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle subject selection menu"""
        if not user_input:
            options = []
            for key, subject in self.subjects.items():
                options.append((key, subject["name"]))
            
            menu_text = self._format_menu(
                title="📚 Choose Subject",
                options=options,
                footer="0=Back  #=Home"
            )
            return USSDResponse(text=menu_text)
        
        if user_input in self.subjects:
            session.current_data['selected_subject'] = user_input
            session.current_menu = 'topics'
            session.menu_history.append('subjects')
            self.db.commit()
            return await self._handle_topics_menu(session, "")
        else:
            return USSDResponse(text="Invalid subject. Please try again.")
    
    async def _handle_topics_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle topic selection within chosen subject"""
        selected_subject = session.current_data.get('selected_subject')
        if not selected_subject:
            return await self._handle_main_menu(session, "")
        
        subject = self.subjects[selected_subject]
        
        if not user_input:
            options = []
            for key, topic in subject["topics"].items():
                options.append((key, topic["name"]))
            
            menu_text = self._format_menu(
                title=f"📖 {subject['name']} Topics",
                options=options,
                footer="0=Back  #=Home"
            )
            return USSDResponse(text=menu_text)
        
        if user_input in subject["topics"]:
            session.current_data['selected_topic'] = user_input
            session.current_menu = 'lessons'
            session.menu_history.append('topics')
            self.db.commit()
            return await self._handle_lessons_menu(session, "")
        else:
            return USSDResponse(text="Invalid topic. Please try again.")
    
    async def _handle_lessons_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle lesson selection within chosen topic"""
        selected_subject = session.current_data.get('selected_subject')
        selected_topic = session.current_data.get('selected_topic')
        
        if not selected_subject or not selected_topic:
            return await self._handle_main_menu(session, "")
        
        topic = self.subjects[selected_subject]["topics"][selected_topic]
        
        if not user_input:
            options = []
            for i, lesson in enumerate(topic["lessons"], 1):
                options.append((str(i), lesson))
            
            menu_text = self._format_menu(
                title=f"📝 {topic['name']} Lessons",
                options=options,
                footer="0=Back  #=Home"
            )
            return USSDResponse(text=menu_text)
        
        lesson_index = int(user_input) - 1 if user_input.isdigit() else -1
        if 0 <= lesson_index < len(topic["lessons"]):
            session.current_data['selected_lesson'] = topic["lessons"][lesson_index]
            session.current_menu = 'lesson_content'
            session.menu_history.append('lessons')
            self.db.commit()
            return await self._handle_lesson_content(session, "")
        else:
            return USSDResponse(text="Invalid lesson. Please try again.")
    
    async def _handle_lesson_content(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Display lesson content with options to continue"""
        selected_lesson = session.current_data.get('selected_lesson')
        
        if not selected_lesson:
            return await self._handle_main_menu(session, "")
        
        lesson_data = self.lesson_content.get(selected_lesson, {
            "content": "Lesson content not available yet. Coming soon!",
            "quiz": None
        })
        
        if not user_input:
            # Display lesson content
            content = lesson_data["content"]
            
            # Add navigation options
            options = [("1", "📝 Take Quiz")]
            if lesson_data.get("quiz"):
                options.append(("2", "🔄 Re-read Lesson"))
            options.append(("3", "📚 Back to Lessons"))
            
            menu_text = self._format_lesson_display(
                title=f"📖 {selected_lesson}",
                content=content,
                options=options
            )
            return USSDResponse(text=menu_text)
        
        if user_input == "1":
            # Start quiz if available
            if lesson_data.get("quiz"):
                session.current_menu = 'quiz_question'
                session.current_data['quiz_data'] = lesson_data["quiz"]
                session.current_data['quiz_score'] = 0
                session.menu_history.append('lesson_content')
                self.db.commit()
                return await self._handle_quiz_question(session, "")
            else:
                return USSDResponse(text="Quiz not available for this lesson yet.")
        elif user_input == "2":
            return await self._handle_lesson_content(session, "")  # Re-display lesson
        elif user_input == "3":
            session.current_menu = 'lessons'
            return await self._handle_lessons_menu(session, "")
        else:
            return USSDResponse(text="Invalid option. Choose 1-3.")
    
    async def _handle_quiz_question(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle quiz question and answer checking"""
        quiz_data = session.current_data.get('quiz_data')
        
        if not quiz_data:
            return await self._handle_lesson_content(session, "")
        
        if not user_input:
            # Display quiz question
            question = quiz_data["question"]
            options = []
            for i, option in enumerate(quiz_data["options"], 1):
                options.append((str(i), option))
            
            menu_text = self._format_menu(
                title="❓ Quiz Time!",
                question=question,
                options=options,
                footer="Select your answer (1-4)"
            )
            return USSDResponse(text=menu_text)
        
        # Check answer
        if user_input.isdigit():
            answer_index = int(user_input) - 1
            correct_index = quiz_data["correct"]
            
            if answer_index == correct_index:
                # Correct answer
                session.current_data['quiz_score'] += 1
                response_text = f"✅ Correct!\n\n{quiz_data['explanation']}\n\n🏆 Great job! You completed the lesson.\n\n1=Back to Lessons\n2=Main Menu"
            else:
                # Wrong answer
                correct_answer = quiz_data["options"][correct_index]
                response_text = f"❌ Wrong. Correct answer: {correct_answer}\n\n{quiz_data['explanation']}\n\n📚 Keep practicing!\n\n1=Back to Lessons\n2=Main Menu"
            
            # Clean up quiz data
            session.current_menu = 'quiz'
            return USSDResponse(text=response_text)
        else:
            return USSDResponse(text="Please select answer 1-4.")
    
    async def _handle_quiz_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle post-quiz navigation"""
        if user_input == "1":
            session.current_menu = 'lessons'
            return await self._handle_lessons_menu(session, "")
        elif user_input == "2":
            session.current_menu = 'main'
            session.menu_history = []
            session.current_data = {}
            self.db.commit()
            return await self._handle_main_menu(session, "")
        else:
            return USSDResponse(text="Choose 1 for Lessons or 2 for Main Menu.")
    
    async def _handle_progress_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Show student progress and statistics"""
        # In production, this would fetch real progress data
        progress_text = (
            "📊 Your Progress\n\n"
            "✅ Lessons: 12 completed\n"
            "🏆 Quizzes: 8 passed\n"
            "🔥 Streak: 3 days\n"
            "⭐ Level: Beginner\n\n"
            "Keep learning! 🚀\n\n"
            "1=Continue Learning\n"
            "2=Main Menu"
        )
        
        if not user_input:
            return USSDResponse(text=progress_text)
        
        if user_input == "1":
            session.current_menu = 'subjects'
            return await self._handle_subjects_menu(session, "")
        elif user_input == "2":
            session.current_menu = 'main'
            return await self._handle_main_menu(session, "")
        else:
            return USSDResponse(text="Choose 1 or 2.")
    
    async def _handle_profile_menu(self, session: USSDSession, user_input: str) -> USSDResponse:
        """Handle user profile menu"""
        profile_text = (
            "👤 Your Profile\n\n"
            f"📞 Phone: {session.phone_number}\n"
            "📅 Joined: This week\n"
            "🎓 Status: Active learner\n"
            "🌍 Language: English\n\n"
            "1=Change Language\n"
            "2=Learning Stats\n"
            "3=Main Menu"
        )
        
        if not user_input:
            return USSDResponse(text=profile_text)
        
        if user_input == "1":
            return USSDResponse(text="Language options coming soon!\n\n*=Main Menu")
        elif user_input == "2":
            return await self._handle_progress_menu(session, "")
        elif user_input == "3":
            session.current_menu = 'main'
            return await self._handle_main_menu(session, "")
        else:
            return USSDResponse(text="Choose 1, 2, or 3.")
    
    async def _handle_help_menu(self, session: USSDSession, user_input: str = "") -> USSDResponse:
        """Show help and navigation instructions"""
        help_text = (
            "❓ Help & Tips\n\n"
            "Navigation:\n"
            "• Type number to select\n"
            "• 0 = Go back\n"
            "• # = Main menu\n"
            "• * = Show this help\n\n"
            "Free learning for all!\n\n"
            "*=Main Menu"
        )
        
        if user_input == "*":
            session.current_menu = 'main'
            return await self._handle_main_menu(session, "")
        
        return USSDResponse(text=help_text)
    
    async def _handle_back_navigation(self, session: USSDSession) -> USSDResponse:
        """Handle back navigation (0 key)"""
        if session.menu_history:
            previous_menu = session.menu_history.pop()
            session.current_menu = previous_menu
            self.db.commit()
            
            # Route to appropriate handler
            handlers = {
                'main': self._handle_main_menu,
                'subjects': self._handle_subjects_menu,
                'topics': self._handle_topics_menu,
                'lessons': self._handle_lessons_menu,
                'lesson_content': self._handle_lesson_content
            }
            
            handler = handlers.get(previous_menu, self._handle_main_menu)
            return await handler(session, "")
        else:
            # Already at root, go to main menu
            session.current_menu = 'main'
            return await self._handle_main_menu(session, "")
    
    async def _handle_home_navigation(self, session: USSDSession) -> USSDResponse:
        """Handle home navigation (# key)"""
        session.current_menu = 'main'
        session.menu_history = []
        session.current_data = {}
        self.db.commit()
        return await self._handle_main_menu(session, "")
    
    def _format_menu(self, title: str, options: List[Tuple[str, str]], 
                     footer: Optional[str] = None, question: Optional[str] = None) -> str:
        """Format USSD menu display within character limits"""
        lines = [title]
        
        if question:
            lines.append("")
            lines.append(question)
        
        lines.append("")
        
        for key, text in options:
            lines.append(f"{key}. {text}")
        
        if footer:
            lines.append("")
            lines.append(footer)
        
        menu_text = "\n".join(lines)
        
        # Ensure within USSD character limit
        if len(menu_text) > self.max_text_length:
            # Truncate options if needed
            truncated_lines = lines[:2]  # Keep title and first blank line
            
            for key, text in options:
                line = f"{key}. {text}"
                if len("\n".join(truncated_lines + [line] + ["", footer or ""])) <= self.max_text_length:
                    truncated_lines.append(line)
                else:
                    truncated_lines.append(f"{key}. {text[:10]}...")
                    break
            
            if footer:
                truncated_lines.extend(["", footer])
            
            menu_text = "\n".join(truncated_lines)
        
        return menu_text
    
    def _format_lesson_display(self, title: str, content: str, 
                              options: List[Tuple[str, str]]) -> str:
        """Format lesson content display within USSD limits"""
        available_chars = self.max_text_length - len(title) - 20  # Reserve space for options
        
        if len(content) > available_chars:
            content = content[:available_chars-3] + "..."
        
        lines = [title, "", content, ""]
        
        for key, text in options:
            lines.append(f"{key}. {text}")
        
        return "\n".join(lines)
    
    async def _log_ussd_interaction(self, session: USSDSession, user_input: str, response: str):
        """Log USSD interaction for analytics"""
        ussd_log = USSDLog(
            session_id=session.session_id,
            phone_number=session.phone_number,
            user_input=user_input,
            menu_displayed=session.current_menu,
            response_text=response
        )
        
        self.db.add(ussd_log)
        self.db.commit()
    
    async def cleanup_expired_sessions(self):
        """Clean up expired USSD sessions (to be called periodically)"""
        cutoff_time = datetime.utcnow() - self.session_timeout
        
        expired_sessions = self.db.query(USSDSession).filter(
            USSDSession.last_activity < cutoff_time,
            USSDSession.is_active == True
        ).all()
        
        for session in expired_sessions:
            session.is_active = False
        
        self.db.commit()
        
        logger.info(f"Cleaned up {len(expired_sessions)} expired USSD sessions")
        
        return len(expired_sessions)