"""
Student Analytics Module

Provides comprehensive individual student performance metrics and learning insights.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum


class LearningStyle(Enum):
    """Detected learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"
    MIXED = "mixed"


class DifficultyLevel(Enum):
    """Difficulty levels for content"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class StudySession:
    """Represents a single study session"""
    session_id: str
    student_id: str
    subject: str
    topic: str
    start_time: datetime
    duration_minutes: float
    completion_rate: float
    score: Optional[float] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    interaction_type: str = "mixed"  # visual, audio, text, interactive


@dataclass
class TopicMastery:
    """Represents mastery status for a topic"""
    topic: str
    subject: str
    mastery_level: float  # 0.0 to 1.0
    first_attempt_date: datetime
    mastery_achieved_date: Optional[datetime] = None
    attempts_to_mastery: int = 0
    predicted_mastery_date: Optional[datetime] = None


class StudentAnalytics:
    """
    Comprehensive analytics for individual student performance and learning patterns.
    """
    
    def __init__(self, student_id: str):
        self.student_id = student_id
        self.sessions: List[StudySession] = []
        self.masteries: Dict[str, TopicMastery] = {}
        self._cache = {}
    
    def add_session(self, session: StudySession):
        """Add a study session to the analytics"""
        if session.student_id != self.student_id:
            raise ValueError(f"Session student_id {session.student_id} doesn't match analytics student_id {self.student_id}")
        
        self.sessions.append(session)
        self._invalidate_cache()
    
    def add_topic_mastery(self, mastery: TopicMastery):
        """Add topic mastery information"""
        key = f"{mastery.subject}_{mastery.topic}"
        self.masteries[key] = mastery
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        """Clear cached calculations when new data is added"""
        self._cache.clear()
    
    def get_learning_velocity(self, weeks: int = 4) -> Dict[str, float]:
        """
        Calculate learning velocity (topics mastered per week) for each subject.
        
        Args:
            weeks: Number of weeks to analyze
            
        Returns:
            Dict mapping subject to topics mastered per week
        """
        cache_key = f"learning_velocity_{weeks}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        velocity = {}
        
        # Group masteries by subject
        subject_masteries = {}
        for mastery in self.masteries.values():
            if mastery.mastery_achieved_date and mastery.mastery_achieved_date >= cutoff_date:
                if mastery.subject not in subject_masteries:
                    subject_masteries[mastery.subject] = []
                subject_masteries[mastery.subject].append(mastery)
        
        # Calculate velocity for each subject
        for subject, masteries in subject_masteries.items():
            topics_mastered = len(masteries)
            velocity[subject] = topics_mastered / weeks if weeks > 0 else 0
        
        self._cache[cache_key] = velocity
        return velocity
    
    def get_retention_rate(self, days_back: int = 30) -> Dict[str, float]:
        """
        Calculate retention rate (% correct on review questions) per subject.
        
        Args:
            days_back: Number of days to look back for review sessions
            
        Returns:
            Dict mapping subject to retention rate (0.0 to 1.0)
        """
        cache_key = f"retention_rate_{days_back}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        retention = {}
        
        # Group sessions by subject and filter for review sessions
        subject_sessions = {}
        for session in self.sessions:
            if (session.start_time >= cutoff_date and 
                session.score is not None and 
                session.completion_rate > 0.8):  # Consider completed sessions as review
                
                if session.subject not in subject_sessions:
                    subject_sessions[session.subject] = []
                subject_sessions[session.subject].append(session)
        
        # Calculate retention rate for each subject
        for subject, sessions in subject_sessions.items():
            if sessions:
                avg_score = sum(s.score for s in sessions) / len(sessions)
                retention[subject] = avg_score / 100.0 if avg_score <= 100 else avg_score
            else:
                retention[subject] = 0.0
        
        self._cache[cache_key] = retention
        return retention
    
    def get_time_on_task_analysis(self) -> Dict[str, Dict[str, float]]:
        """
        Analyze average time spent per lesson and per subject.
        
        Returns:
            Dict with 'by_subject' and 'by_lesson' time analysis
        """
        if 'time_on_task' in self._cache:
            return self._cache['time_on_task']
        
        subject_times = {}
        lesson_times = {}
        
        # Analyze by subject
        for session in self.sessions:
            if session.subject not in subject_times:
                subject_times[session.subject] = []
            subject_times[session.subject].append(session.duration_minutes)
        
        # Calculate averages by subject
        subject_averages = {}
        for subject, times in subject_times.items():
            subject_averages[subject] = {
                'avg_minutes': np.mean(times),
                'median_minutes': np.median(times),
                'total_sessions': len(times),
                'total_minutes': sum(times)
            }
        
        # Analyze by lesson (topic within subject)
        for session in self.sessions:
            lesson_key = f"{session.subject}_{session.topic}"
            if lesson_key not in lesson_times:
                lesson_times[lesson_key] = []
            lesson_times[lesson_key].append(session.duration_minutes)
        
        # Calculate averages by lesson
        lesson_averages = {}
        for lesson, times in lesson_times.items():
            lesson_averages[lesson] = {
                'avg_minutes': np.mean(times),
                'sessions': len(times)
            }
        
        result = {
            'by_subject': subject_averages,
            'by_lesson': lesson_averages
        }
        
        self._cache['time_on_task'] = result
        return result
    
    def get_difficulty_curve_tracking(self) -> Dict[str, List[Dict]]:
        """
        Track how student handles increasing difficulty levels over time.
        
        Returns:
            Dict mapping subject to difficulty progression data
        """
        if 'difficulty_curve' in self._cache:
            return self._cache['difficulty_curve']
        
        subject_progressions = {}
        
        for session in self.sessions:
            if session.score is not None:
                if session.subject not in subject_progressions:
                    subject_progressions[session.subject] = []
                
                subject_progressions[session.subject].append({
                    'date': session.start_time,
                    'difficulty': session.difficulty_level.value,
                    'score': session.score,
                    'completion_rate': session.completion_rate,
                    'topic': session.topic
                })
        
        # Sort by date for each subject
        for subject in subject_progressions:
            subject_progressions[subject].sort(key=lambda x: x['date'])
        
        self._cache['difficulty_curve'] = subject_progressions
        return subject_progressions
    
    def detect_optimal_study_time(self) -> Dict[str, str]:
        """
        Detect when this student learns best based on session performance by time of day.
        
        Returns:
            Dict with optimal study periods and performance metrics
        """
        if 'optimal_study_time' in self._cache:
            return self._cache['optimal_study_time']
        
        # Group sessions by hour of day
        hourly_performance = {}
        for session in self.sessions:
            if session.score is not None:
                hour = session.start_time.hour
                if hour not in hourly_performance:
                    hourly_performance[hour] = []
                hourly_performance[hour].append({
                    'score': session.score,
                    'completion_rate': session.completion_rate,
                    'duration': session.duration_minutes
                })
        
        # Calculate performance metrics by hour
        hour_stats = {}
        for hour, sessions in hourly_performance.items():
            if len(sessions) >= 3:  # Need minimum sessions for reliability
                avg_score = np.mean([s['score'] for s in sessions])
                avg_completion = np.mean([s['completion_rate'] for s in sessions])
                avg_duration = np.mean([s['duration'] for s in sessions])
                
                # Combined performance metric
                performance_metric = (avg_score/100 * 0.5 + avg_completion * 0.3 + 
                                    (1 - min(avg_duration/120, 1)) * 0.2)  # Prefer shorter, focused sessions
                
                hour_stats[hour] = {
                    'performance_metric': performance_metric,
                    'avg_score': avg_score,
                    'avg_completion': avg_completion,
                    'session_count': len(sessions)
                }
        
        # Find optimal times
        if hour_stats:
            best_hour = max(hour_stats.keys(), key=lambda h: hour_stats[h]['performance_metric'])
            
            # Determine time period
            if 6 <= best_hour <= 11:
                period = "morning"
            elif 12 <= best_hour <= 17:
                period = "afternoon"
            elif 18 <= best_hour <= 21:
                period = "evening"
            else:
                period = "late/early hours"
            
            result = {
                'optimal_period': period,
                'best_hour': best_hour,
                'performance_score': round(hour_stats[best_hour]['performance_metric'], 3),
                'recommendation': f"Student performs best during {period} sessions, particularly around {best_hour}:00"
            }
        else:
            result = {
                'optimal_period': "insufficient_data",
                'recommendation': "Need more session data to determine optimal study times"
            }
        
        self._cache['optimal_study_time'] = result
        return result
    
    def calculate_engagement_score(self) -> Dict[str, float]:
        """
        Calculate engagement score based on frequency, duration, and completion rates.
        
        Returns:
            Overall engagement score and component scores
        """
        if 'engagement_score' in self._cache:
            return self._cache['engagement_score']
        
        if not self.sessions:
            return {'overall': 0.0, 'frequency': 0.0, 'duration': 0.0, 'completion': 0.0}
        
        # Calculate frequency score (sessions per week)
        if len(self.sessions) >= 2:
            date_range = (max(s.start_time for s in self.sessions) - 
                         min(s.start_time for s in self.sessions)).days
            weeks = max(date_range / 7, 1)
            sessions_per_week = len(self.sessions) / weeks
            frequency_score = min(sessions_per_week / 5, 1.0)  # Normalize to 5 sessions/week max
        else:
            frequency_score = 0.1
        
        # Calculate duration score (prefer 20-45 min sessions)
        durations = [s.duration_minutes for s in self.sessions]
        avg_duration = np.mean(durations)
        if 20 <= avg_duration <= 45:
            duration_score = 1.0
        elif avg_duration < 20:
            duration_score = avg_duration / 20
        else:
            duration_score = max(0.5, 1 - (avg_duration - 45) / 60)  # Penalty for too long sessions
        
        # Calculate completion score
        completion_rates = [s.completion_rate for s in self.sessions]
        completion_score = np.mean(completion_rates)
        
        # Overall weighted score
        overall_score = (frequency_score * 0.4 + duration_score * 0.3 + completion_score * 0.3)
        
        result = {
            'overall': round(overall_score, 3),
            'frequency': round(frequency_score, 3),
            'duration': round(duration_score, 3),
            'completion': round(completion_score, 3)
        }
        
        self._cache['engagement_score'] = result
        return result
    
    def predict_mastery_dates(self) -> Dict[str, datetime]:
        """
        Predict when student will master each topic based on current progress.
        
        Returns:
            Dict mapping topic to predicted mastery date
        """
        if 'predicted_mastery' in self._cache:
            return self._cache['predicted_mastery']
        
        predictions = {}
        
        for key, mastery in self.masteries.items():
            if mastery.mastery_achieved_date:
                # Already mastered
                predictions[key] = mastery.mastery_achieved_date
            else:
                # Predict based on progress rate
                current_level = mastery.mastery_level
                if current_level > 0 and mastery.attempts_to_mastery > 0:
                    # Calculate progress rate
                    days_learning = (datetime.now() - mastery.first_attempt_date).days
                    progress_per_day = current_level / max(days_learning, 1)
                    
                    if progress_per_day > 0:
                        days_to_mastery = (1.0 - current_level) / progress_per_day
                        predicted_date = datetime.now() + timedelta(days=days_to_mastery)
                        predictions[key] = predicted_date
        
        self._cache['predicted_mastery'] = predictions
        return predictions
    
    def infer_learning_style(self) -> Dict[str, Union[LearningStyle, float]]:
        """
        Infer learning style from interaction patterns.
        
        Returns:
            Detected learning style and confidence scores
        """
        if 'learning_style' in self._cache:
            return self._cache['learning_style']
        
        style_scores = {
            LearningStyle.VISUAL: 0.0,
            LearningStyle.AUDITORY: 0.0,
            LearningStyle.KINESTHETIC: 0.0,
            LearningStyle.READING_WRITING: 0.0
        }
        
        total_sessions = len(self.sessions)
        if total_sessions == 0:
            return {'style': LearningStyle.MIXED, 'confidence': 0.0}
        
        # Analyze interaction types
        for session in self.sessions:
            performance_weight = (session.score or 50) / 100.0
            
            if 'visual' in session.interaction_type.lower():
                style_scores[LearningStyle.VISUAL] += performance_weight
            elif 'audio' in session.interaction_type.lower():
                style_scores[LearningStyle.AUDITORY] += performance_weight
            elif 'interactive' in session.interaction_type.lower():
                style_scores[LearningStyle.KINESTHETIC] += performance_weight
            elif 'text' in session.interaction_type.lower():
                style_scores[LearningStyle.READING_WRITING] += performance_weight
        
        # Normalize scores
        total_score = sum(style_scores.values())
        if total_score > 0:
            for style in style_scores:
                style_scores[style] /= total_score
        
        # Determine primary style
        primary_style = max(style_scores.keys(), key=lambda s: style_scores[s])
        confidence = style_scores[primary_style]
        
        # If no clear preference, mark as mixed
        if confidence < 0.4:
            primary_style = LearningStyle.MIXED
            confidence = 1.0 - max(style_scores.values())
        
        result = {
            'style': primary_style,
            'confidence': round(confidence, 3),
            'scores': {style.value: round(score, 3) for style, score in style_scores.items()}
        }
        
        self._cache['learning_style'] = result
        return result
    
    def get_comprehensive_report(self) -> Dict:
        """
        Generate a comprehensive analytics report for the student.
        
        Returns:
            Complete analytics report with all metrics
        """
        return {
            'student_id': self.student_id,
            'generated_at': datetime.now().isoformat(),
            'learning_velocity': self.get_learning_velocity(),
            'retention_rate': self.get_retention_rate(),
            'time_on_task': self.get_time_on_task_analysis(),
            'difficulty_progress': self.get_difficulty_curve_tracking(),
            'optimal_study_time': self.detect_optimal_study_time(),
            'engagement_score': self.calculate_engagement_score(),
            'predicted_mastery': {k: v.isoformat() for k, v in self.predict_mastery_dates().items()},
            'learning_style': self.infer_learning_style(),
            'total_sessions': len(self.sessions),
            'active_topics': len(self.masteries)
        }