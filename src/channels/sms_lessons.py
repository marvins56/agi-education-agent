"""
SMS Lesson Formatter for EduAGI - Convert full lessons to SMS-friendly format

Handles breaking down complete educational content into SMS-sized chunks,
manages delivery scheduling, and provides quiz functionality via SMS.
"""

import asyncio
import json
import re
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

# Import from main project structure
from ..config import settings
from ..models.database import get_db
from ..utils.logging import get_logger
from .sms_gateway import SMSGateway, SMSMessage

logger = get_logger(__name__)

# Database models for SMS lesson tracking
Base = declarative_base()

class SMSLessonSeries(Base):
    """Track multi-part SMS lesson series for students"""
    __tablename__ = 'sms_lesson_series'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    lesson_id = Column(String, nullable=False)
    lesson_title = Column(String, nullable=False)
    total_parts = Column(Integer, nullable=False)
    current_part = Column(Integer, default=1)
    content_parts = Column(JSON, nullable=False)  # List of SMS content parts
    quiz_data = Column(JSON, nullable=True)  # Quiz questions for lesson
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    delivery_schedule = Column(String, default='immediate')  # immediate, daily, weekly


class SMSLearningSchedule(Base):
    """Track SMS learning schedules for students"""
    __tablename__ = 'sms_learning_schedules'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    preferred_time = Column(String, default='09:00')  # HH:MM format
    timezone = Column(String, default='Africa/Kampala')
    frequency = Column(String, default='daily')  # daily, weekly, custom
    weekdays_only = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    last_lesson_sent = Column(DateTime, nullable=True)
    streak_days = Column(Integer, default=0)
    streak_last_updated = Column(DateTime, default=datetime.utcnow)


class SMSQuizSession(Base):
    """Track quiz sessions conducted via SMS"""
    __tablename__ = 'sms_quiz_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    lesson_id = Column(String, nullable=False)
    quiz_questions = Column(JSON, nullable=False)  # List of questions
    current_question = Column(Integer, default=0)
    answers_given = Column(JSON, default=list)  # Student's answers
    correct_answers = Column(JSON, nullable=False)  # Correct answer indices
    score = Column(Integer, default=0)
    total_questions = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


class LessonDeliveryMode(Enum):
    """SMS lesson delivery modes"""
    IMMEDIATE = "immediate"  # Send all parts immediately
    SPACED = "spaced"       # Send parts with delays
    DAILY = "daily"         # One part per day
    SCHEDULED = "scheduled"  # Based on student's schedule


@dataclass
class LessonContent:
    """Complete lesson content structure"""
    title: str
    subject: str
    topic: str
    content: str
    learning_objectives: List[str]
    quiz_questions: List[Dict[str, Any]]
    difficulty_level: str = "beginner"
    estimated_time: int = 15  # minutes


@dataclass
class SMSLessonPart:
    """Individual SMS part of a lesson"""
    part_number: int
    total_parts: int
    content: str
    part_type: str = "content"  # content, quiz, summary
    requires_response: bool = False


class SMSLessonFormatter:
    """Format educational content for SMS delivery with intelligent chunking"""
    
    def __init__(self, sms_gateway: SMSGateway, db_session: Session):
        self.sms = sms_gateway
        self.db = db_session
        self.max_sms_length = 160
        self.max_part_length = 150  # Leave space for part indicator
        
        # SMS formatting templates
        self.templates = {
            'lesson_start': "📚 LESSON: {title}\n\nPart {part}/{total_parts}\n\n{content}",
            'lesson_part': "📚 {title} ({part}/{total_parts})\n\n{content}",
            'lesson_quiz': "❓ QUIZ: {title}\n\nQ{qnum}: {question}\n\nA) {opt_a}\nB) {opt_b}\nC) {opt_c}\nD) {opt_d}\n\nReply A,B,C,D",
            'quiz_result': "✅ {result}! Score: {score}/{total}\n\n{explanation}",
            'lesson_complete': "🎉 Lesson Complete!\n\n'{title}' finished.\nScore: {score}%\n\nReply NEXT for next lesson or REVIEW to study again.",
            'daily_lesson': "📅 Daily Lesson: {title}\n\nPart 1/{total_parts}\n\n{content}\n\nReply CONTINUE for more parts.",
            'streak_reminder': "🔥 {streak} day streak! Don't break it!\n\nToday's lesson: {title}\n\nReply LESSON to start learning.",
            'progress_summary': "📊 Weekly Progress:\n✅ {lessons} lessons\n🏆 {quizzes} quizzes passed\n📈 {streak} day streak\n\nKeep learning! 🚀"
        }
    
    async def format_lesson_for_sms(self, lesson: LessonContent, student_id: str, 
                                  phone_number: str, delivery_mode: LessonDeliveryMode = LessonDeliveryMode.IMMEDIATE) -> List[SMSLessonPart]:
        """Convert full lesson content into SMS-friendly parts"""
        
        # Clean and prepare content
        clean_content = self._clean_content_for_sms(lesson.content)
        
        # Break content into logical sections
        sections = self._break_into_sections(clean_content)
        
        # Create SMS parts
        sms_parts = []
        part_num = 1
        
        for section in sections:
            # Split section into SMS-sized chunks
            chunks = self._split_text_for_sms(section, self.max_part_length)
            
            for chunk in chunks:
                if part_num == 1:
                    # Use special template for first part
                    formatted_content = self.templates['lesson_start'].format(
                        title=lesson.title,
                        part=part_num,
                        total_parts=len(chunks) + len(lesson.quiz_questions),
                        content=chunk
                    )
                else:
                    formatted_content = self.templates['lesson_part'].format(
                        title=lesson.title,
                        part=part_num,
                        total_parts=len(chunks) + len(lesson.quiz_questions),
                        content=chunk
                    )
                
                sms_parts.append(SMSLessonPart(
                    part_number=part_num,
                    total_parts=len(chunks) + len(lesson.quiz_questions),
                    content=formatted_content,
                    part_type="content"
                ))
                part_num += 1
        
        # Add quiz questions as separate parts
        for i, quiz_q in enumerate(lesson.quiz_questions):
            quiz_content = self.templates['lesson_quiz'].format(
                title=lesson.title,
                qnum=i+1,
                question=quiz_q['question'],
                opt_a=quiz_q['options'][0],
                opt_b=quiz_q['options'][1], 
                opt_c=quiz_q['options'][2],
                opt_d=quiz_q['options'][3]
            )
            
            sms_parts.append(SMSLessonPart(
                part_number=part_num,
                total_parts=len(sms_parts) + len(lesson.quiz_questions) - i,
                content=quiz_content,
                part_type="quiz",
                requires_response=True
            ))
            part_num += 1
        
        # Store lesson series in database
        await self._store_lesson_series(student_id, phone_number, lesson, sms_parts, delivery_mode)
        
        return sms_parts
    
    def _clean_content_for_sms(self, content: str) -> str:
        """Clean content for SMS - remove formatting, fix encoding, etc."""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', content)
        
        # Replace common HTML entities
        html_entities = {
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&nbsp;': ' '
        }
        
        for entity, replacement in html_entities.items():
            clean_text = clean_text.replace(entity, replacement)
        
        # Remove excessive whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Replace smart quotes with regular quotes
        clean_text = clean_text.replace('"', '"').replace('"', '"')
        clean_text = clean_text.replace(''', "'").replace(''', "'")
        
        return clean_text
    
    def _break_into_sections(self, content: str) -> List[str]:
        """Break content into logical sections based on paragraphs and topics"""
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        sections = []
        current_section = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed reasonable SMS length, start new section
            if len(current_section + "\n\n" + paragraph) > self.max_part_length * 2:
                if current_section:
                    sections.append(current_section)
                current_section = paragraph
            else:
                if current_section:
                    current_section += "\n\n" + paragraph
                else:
                    current_section = paragraph
        
        if current_section:
            sections.append(current_section)
        
        return sections if sections else [content]
    
    def _split_text_for_sms(self, text: str, max_length: int) -> List[str]:
        """Split text into SMS-sized chunks preserving word boundaries"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        remaining = text
        
        while remaining:
            if len(remaining) <= max_length:
                chunks.append(remaining)
                break
            
            # Find the best break point (prefer sentence end, then word boundary)
            chunk = remaining[:max_length]
            
            # Look for sentence end
            sentence_break = max(
                chunk.rfind('. '),
                chunk.rfind('! '),
                chunk.rfind('? ')
            )
            
            if sentence_break > max_length * 0.6:  # If sentence break is reasonable
                split_pos = sentence_break + 1
            else:
                # Look for word boundary
                word_break = chunk.rfind(' ')
                split_pos = word_break if word_break > max_length * 0.6 else max_length
            
            chunks.append(remaining[:split_pos].strip())
            remaining = remaining[split_pos:].strip()
        
        return chunks
    
    async def _store_lesson_series(self, student_id: str, phone_number: str, 
                                 lesson: LessonContent, sms_parts: List[SMSLessonPart],
                                 delivery_mode: LessonDeliveryMode):
        """Store lesson series in database for tracking"""
        
        # Convert parts to serializable format
        parts_data = [
            {
                'part_number': part.part_number,
                'total_parts': part.total_parts,
                'content': part.content,
                'part_type': part.part_type,
                'requires_response': part.requires_response
            }
            for part in sms_parts
        ]
        
        # Store quiz data separately
        quiz_data = {
            'questions': lesson.quiz_questions,
            'total_questions': len(lesson.quiz_questions)
        }
        
        lesson_series = SMSLessonSeries(
            student_id=student_id,
            phone_number=phone_number,
            lesson_id=f"{lesson.subject}_{lesson.topic}_{lesson.title}",
            lesson_title=lesson.title,
            total_parts=len(sms_parts),
            content_parts=parts_data,
            quiz_data=quiz_data,
            delivery_schedule=delivery_mode.value
        )
        
        self.db.add(lesson_series)
        self.db.commit()
    
    async def deliver_lesson_parts(self, student_id: str, delivery_mode: LessonDeliveryMode = LessonDeliveryMode.IMMEDIATE, 
                                 max_parts: int = None) -> bool:
        """Deliver lesson parts to student based on their progress and delivery mode"""
        
        # Get active lesson series for student
        lesson_series = self.db.query(SMSLessonSeries).filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(SMSLessonSeries.created_at.desc()).first()
        
        if not lesson_series:
            logger.warning(f"No active lesson series found for student {student_id}")
            return False
        
        # Determine how many parts to send
        if delivery_mode == LessonDeliveryMode.IMMEDIATE:
            parts_to_send = max_parts or len(lesson_series.content_parts)
        elif delivery_mode == LessonDeliveryMode.DAILY:
            parts_to_send = 1
        elif delivery_mode == LessonDeliveryMode.SPACED:
            parts_to_send = min(3, max_parts or 3)  # Send in groups of 3
        else:
            parts_to_send = 1
        
        # Send the appropriate parts
        current_part = lesson_series.current_part
        parts_sent = 0
        
        for i in range(current_part - 1, min(current_part - 1 + parts_to_send, len(lesson_series.content_parts))):
            part_data = lesson_series.content_parts[i]
            
            message = SMSMessage(
                phone_number=lesson_series.phone_number,
                content=part_data['content'],
                message_type="lesson",
                student_id=student_id
            )
            
            response = await self.sms.send_sms(message)
            
            if response.success:
                parts_sent += 1
                lesson_series.current_part += 1
                
                # Add delay between parts for spaced delivery
                if delivery_mode == LessonDeliveryMode.SPACED and i < current_part - 1 + parts_to_send - 1:
                    await asyncio.sleep(30)  # 30 second delay between parts
            else:
                logger.error(f"Failed to send lesson part {i+1} to {student_id}: {response.error}")
                break
        
        # Mark as started if not already
        if not lesson_series.started_at:
            lesson_series.started_at = datetime.utcnow()
        
        # Check if lesson is complete
        if lesson_series.current_part > len(lesson_series.content_parts):
            lesson_series.completed_at = datetime.utcnow()
            lesson_series.is_active = False
        
        self.db.commit()
        
        return parts_sent > 0
    
    async def handle_quiz_response(self, student_id: str, phone_number: str, answer: str) -> Optional[str]:
        """Handle student's quiz answer and return feedback"""
        
        # Get active quiz session
        quiz_session = self.db.query(SMSQuizSession).filter_by(
            student_id=student_id,
            is_active=True
        ).order_by(SMSQuizSession.started_at.desc()).first()
        
        if not quiz_session:
            return "No active quiz found. Reply QUIZ to start a new quiz."
        
        # Validate answer format
        answer = answer.upper().strip()
        if answer not in ['A', 'B', 'C', 'D']:
            return "Please answer A, B, C, or D for the quiz question."
        
        # Get current question
        current_q_index = quiz_session.current_question
        if current_q_index >= len(quiz_session.quiz_questions):
            return "Quiz already completed! Reply NEXT for next lesson."
        
        current_question = quiz_session.quiz_questions[current_q_index]
        correct_answer_index = quiz_session.correct_answers[current_q_index]
        answer_index = ord(answer) - ord('A')  # Convert A,B,C,D to 0,1,2,3
        
        # Store answer
        answers_given = quiz_session.answers_given or []
        answers_given.append(answer_index)
        quiz_session.answers_given = answers_given
        
        # Check if correct
        is_correct = answer_index == correct_answer_index
        if is_correct:
            quiz_session.score += 1
        
        # Move to next question
        quiz_session.current_question += 1
        
        # Generate feedback
        result_text = "Correct" if is_correct else "Incorrect"
        explanation = current_question.get('explanation', '')
        
        feedback = self.templates['quiz_result'].format(
            result=result_text,
            score=quiz_session.score,
            total=quiz_session.current_question,
            explanation=explanation
        )
        
        # Check if quiz is complete
        if quiz_session.current_question >= len(quiz_session.quiz_questions):
            quiz_session.completed_at = datetime.utcnow()
            quiz_session.is_active = False
            
            # Add completion message
            completion_text = self.templates['lesson_complete'].format(
                title=quiz_session.lesson_id,
                score=int((quiz_session.score / len(quiz_session.quiz_questions)) * 100)
            )
            
            feedback += f"\n\n{completion_text}"
        else:
            # Send next question
            feedback += "\n\nReply NEXT for next question."
        
        self.db.commit()
        
        return feedback
    
    async def schedule_daily_lessons(self, student_id: str, phone_number: str, 
                                   preferred_time: str = "09:00", timezone: str = "Africa/Kampala"):
        """Set up daily lesson delivery schedule for a student"""
        
        # Check if schedule already exists
        existing_schedule = self.db.query(SMSLearningSchedule).filter_by(student_id=student_id).first()
        
        if existing_schedule:
            # Update existing schedule
            existing_schedule.preferred_time = preferred_time
            existing_schedule.timezone = timezone
            existing_schedule.is_active = True
        else:
            # Create new schedule
            schedule = SMSLearningSchedule(
                student_id=student_id,
                phone_number=phone_number,
                preferred_time=preferred_time,
                timezone=timezone,
                frequency='daily'
            )
            self.db.add(schedule)
        
        self.db.commit()
        
        return True
    
    async def send_daily_lessons(self):
        """Send daily lessons to all scheduled students (to be called by scheduler)"""
        from datetime import datetime, time
        import pytz
        
        current_time = datetime.utcnow()
        lessons_sent = 0
        
        # Get all active schedules
        schedules = self.db.query(SMSLearningSchedule).filter_by(is_active=True).all()
        
        for schedule in schedules:
            try:
                # Convert schedule time to UTC
                local_tz = pytz.timezone(schedule.timezone)
                scheduled_time = datetime.strptime(schedule.preferred_time, "%H:%M").time()
                
                # Create datetime in local timezone
                local_dt = local_tz.localize(
                    datetime.combine(current_time.date(), scheduled_time)
                )
                utc_dt = local_dt.astimezone(pytz.UTC)
                
                # Check if it's time to send (within 30 minutes window)
                time_diff = abs((current_time - utc_dt).total_seconds())
                
                if time_diff <= 1800:  # 30 minutes window
                    # Check if lesson already sent today
                    if (schedule.last_lesson_sent and 
                        schedule.last_lesson_sent.date() == current_time.date()):
                        continue
                    
                    # Skip weekends if weekdays_only is True
                    if schedule.weekdays_only and current_time.weekday() >= 5:
                        continue
                    
                    # Send daily lesson
                    success = await self.deliver_lesson_parts(
                        schedule.student_id,
                        LessonDeliveryMode.DAILY,
                        max_parts=1
                    )
                    
                    if success:
                        schedule.last_lesson_sent = current_time
                        
                        # Update streak
                        await self._update_learning_streak(schedule)
                        
                        lessons_sent += 1
                        logger.info(f"Sent daily lesson to student {schedule.student_id}")
                
            except Exception as e:
                logger.error(f"Error sending daily lesson to {schedule.student_id}: {str(e)}")
                continue
        
        self.db.commit()
        
        return lessons_sent
    
    async def send_streak_reminders(self):
        """Send streak reminder messages to students who haven't learned today"""
        
        current_time = datetime.utcnow()
        reminders_sent = 0
        
        # Get students with active streaks who haven't learned today
        schedules = self.db.query(SMSLearningSchedule).filter(
            SMSLearningSchedule.is_active == True,
            SMSLearningSchedule.streak_days > 0
        ).all()
        
        for schedule in schedules:
            # Check if they've learned today
            if (schedule.last_lesson_sent and 
                schedule.last_lesson_sent.date() == current_time.date()):
                continue  # Already learned today
            
            # Send reminder (only once per day)
            reminder_text = self.templates['streak_reminder'].format(
                streak=schedule.streak_days,
                title="Today's Mathematics Lesson"  # Would be dynamic in production
            )
            
            message = SMSMessage(
                phone_number=schedule.phone_number,
                content=reminder_text,
                message_type="reminder",
                student_id=schedule.student_id
            )
            
            response = await self.sms.send_sms(message)
            
            if response.success:
                reminders_sent += 1
                logger.info(f"Sent streak reminder to student {schedule.student_id}")
        
        return reminders_sent
    
    async def generate_progress_report(self, student_id: str) -> str:
        """Generate weekly progress report for a student"""
        
        # Calculate metrics from past week
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Count completed lessons
        completed_lessons = self.db.query(SMSLessonSeries).filter(
            SMSLessonSeries.student_id == student_id,
            SMSLessonSeries.completed_at >= week_ago
        ).count()
        
        # Count completed quizzes
        completed_quizzes = self.db.query(SMSQuizSession).filter(
            SMSQuizSession.student_id == student_id,
            SMSQuizSession.completed_at >= week_ago,
            SMSQuizSession.score > 0
        ).count()
        
        # Get current streak
        schedule = self.db.query(SMSLearningSchedule).filter_by(student_id=student_id).first()
        streak = schedule.streak_days if schedule else 0
        
        # Format progress report
        return self.templates['progress_summary'].format(
            lessons=completed_lessons,
            quizzes=completed_quizzes,
            streak=streak
        )
    
    async def _update_learning_streak(self, schedule: SMSLearningSchedule):
        """Update student's learning streak based on lesson activity"""
        current_date = datetime.utcnow().date()
        
        if schedule.streak_last_updated.date() == current_date:
            return  # Already updated today
        
        # Check if streak continues (learned yesterday or today)
        yesterday = current_date - timedelta(days=1)
        
        if (schedule.last_lesson_sent and 
            schedule.last_lesson_sent.date() in [current_date, yesterday]):
            # Streak continues
            schedule.streak_days += 1
        else:
            # Streak broken, reset
            schedule.streak_days = 1
        
        schedule.streak_last_updated = datetime.utcnow()
    
    async def get_student_lesson_progress(self, student_id: str) -> Dict[str, Any]:
        """Get detailed lesson progress for a student"""
        
        # Get all lesson series for student
        lesson_series = self.db.query(SMSLessonSeries).filter_by(student_id=student_id).all()
        
        # Get quiz sessions
        quiz_sessions = self.db.query(SMSQuizSession).filter_by(student_id=student_id).all()
        
        # Get learning schedule
        schedule = self.db.query(SMSLearningSchedule).filter_by(student_id=student_id).first()
        
        progress = {
            'total_lessons_started': len(lesson_series),
            'total_lessons_completed': len([ls for ls in lesson_series if ls.completed_at]),
            'total_quizzes_taken': len(quiz_sessions),
            'total_quizzes_passed': len([qs for qs in quiz_sessions if qs.score > qs.total_questions / 2]),
            'current_streak': schedule.streak_days if schedule else 0,
            'lessons_this_week': len([ls for ls in lesson_series if ls.started_at and 
                                    ls.started_at >= datetime.utcnow() - timedelta(days=7)]),
            'average_quiz_score': sum([qs.score / qs.total_questions for qs in quiz_sessions if qs.completed_at]) / max(len([qs for qs in quiz_sessions if qs.completed_at]), 1) * 100
        }
        
        return progress