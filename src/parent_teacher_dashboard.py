"""
Parent/Teacher Dashboard - Comprehensive monitoring and reporting system

This module provides comprehensive progress tracking, accessibility monitoring,
IEP goal tracking, alert systems, and dashboard functionality designed for 
East African educational contexts with large class sizes and shared devices.
"""

import json
import sqlite3
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set, Union
from enum import Enum
from datetime import datetime, timedelta, time
from pathlib import Path
import logging
import statistics

from accessibility_engine import AccessibilityProfile, ImpairmentType, SeverityLevel
from disability_aware_fsrs import CardState, ReviewOutcome, CognitiveProfile
from offline_learning import ProgressEntry

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"
    CRITICAL = "critical"


class ProgressStatus(Enum):
    """Student progress status levels"""
    EXCELLENT = "excellent"      # >90% success rate
    GOOD = "good"               # 75-90% success rate
    STRUGGLING = "struggling"    # 50-75% success rate
    AT_RISK = "at_risk"         # <50% success rate


class IEPGoalStatus(Enum):
    """IEP goal achievement status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    NEEDS_MODIFICATION = "needs_modification"
    ON_HOLD = "on_hold"


@dataclass
class StudentProgress:
    """Comprehensive student progress tracking"""
    student_id: str
    name: str
    grade_level: int
    
    # Academic performance
    total_lessons_completed: int = 0
    total_time_spent_minutes: int = 0
    success_rate: float = 0.0
    current_streak: int = 0
    longest_streak: int = 0
    
    # Subject-specific progress
    subject_scores: Dict[str, float] = field(default_factory=dict)  # Subject -> average score
    subject_time_spent: Dict[str, int] = field(default_factory=dict)  # Subject -> minutes
    mastered_topics: List[str] = field(default_factory=list)
    struggling_topics: List[str] = field(default_factory=list)
    
    # Engagement metrics
    login_frequency: float = 0.0  # Logins per week
    avg_session_duration: float = 0.0  # Minutes per session
    last_active: Optional[datetime] = None
    
    # Progress trends (last 30 days)
    weekly_progress: List[float] = field(default_factory=list)  # Weekly success rates
    daily_activity: List[int] = field(default_factory=list)    # Daily minutes active
    
    # Status and alerts
    progress_status: ProgressStatus = ProgressStatus.GOOD
    needs_attention: bool = False
    alert_reasons: List[str] = field(default_factory=list)
    
    # Accessibility tracking
    accessibility_accommodations_active: List[str] = field(default_factory=list)
    accommodation_usage_frequency: Dict[str, int] = field(default_factory=dict)
    
    def calculate_overall_score(self) -> float:
        """Calculate overall academic score across all subjects"""
        if not self.subject_scores:
            return 0.0
        return sum(self.subject_scores.values()) / len(self.subject_scores)
    
    def update_progress_status(self):
        """Update progress status based on current metrics"""
        overall_score = self.calculate_overall_score()
        
        if overall_score >= 90:
            self.progress_status = ProgressStatus.EXCELLENT
        elif overall_score >= 75:
            self.progress_status = ProgressStatus.GOOD
        elif overall_score >= 50:
            self.progress_status = ProgressStatus.STRUGGLING
        else:
            self.progress_status = ProgressStatus.AT_RISK
        
        # Update alert status
        self.alert_reasons.clear()
        self.needs_attention = False
        
        if self.progress_status in [ProgressStatus.STRUGGLING, ProgressStatus.AT_RISK]:
            self.needs_attention = True
            self.alert_reasons.append(f"Low academic performance: {overall_score:.1f}%")
        
        if self.login_frequency < 2:  # Less than 2 logins per week
            self.needs_attention = True
            self.alert_reasons.append("Low engagement: infrequent logins")
        
        if self.current_streak == 0 and self.last_active:
            days_inactive = (datetime.now() - self.last_active).days
            if days_inactive > 3:
                self.needs_attention = True
                self.alert_reasons.append(f"Inactive for {days_inactive} days")


@dataclass
class IEPGoal:
    """Individual Education Program goal tracking"""
    goal_id: str
    student_id: str
    title: str
    description: str
    target_date: datetime
    
    # Goal specifics
    measurable_objective: str
    current_level: float = 0.0  # 0-100% completion
    target_level: float = 100.0
    measurement_frequency: str = "weekly"  # daily, weekly, monthly
    
    # Progress tracking
    status: IEPGoalStatus = IEPGoalStatus.NOT_STARTED
    milestones_achieved: List[str] = field(default_factory=list)
    progress_notes: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Related accessibility accommodations
    required_accommodations: List[str] = field(default_factory=list)
    accommodation_effectiveness: Dict[str, float] = field(default_factory=dict)
    
    def add_progress_note(self, note: str, progress_value: float = None, author: str = "system"):
        """Add a progress note for this goal"""
        note_entry = {
            "timestamp": datetime.now().isoformat(),
            "author": author,
            "note": note,
            "progress_value": progress_value,
            "current_level": self.current_level
        }
        self.progress_notes.append(note_entry)
        
        if progress_value is not None:
            self.current_level = progress_value
            self.update_status()
        
        self.last_updated = datetime.now()
    
    def update_status(self):
        """Update goal status based on current progress"""
        if self.current_level == 0:
            self.status = IEPGoalStatus.NOT_STARTED
        elif self.current_level >= self.target_level:
            self.status = IEPGoalStatus.ACHIEVED
        elif self.current_level >= self.target_level * 0.7:  # 70% of target
            self.status = IEPGoalStatus.IN_PROGRESS
        elif datetime.now() > self.target_date and self.current_level < self.target_level * 0.5:
            self.status = IEPGoalStatus.NEEDS_MODIFICATION
        else:
            self.status = IEPGoalStatus.IN_PROGRESS
    
    def is_overdue(self) -> bool:
        """Check if goal is overdue"""
        return datetime.now() > self.target_date and self.status != IEPGoalStatus.ACHIEVED
    
    def get_progress_percentage(self) -> float:
        """Get progress as percentage of target"""
        return (self.current_level / self.target_level) * 100 if self.target_level > 0 else 0


@dataclass
class Alert:
    """System alert for student concerns"""
    alert_id: str
    student_id: str
    alert_level: AlertLevel
    title: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    
    # Alert specifics
    category: str = "academic"  # academic, behavioral, attendance, accessibility
    suggested_actions: List[str] = field(default_factory=list)
    related_data: Dict[str, Any] = field(default_factory=dict)
    
    # Status tracking
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolution_notes: str = ""
    
    def acknowledge(self, user_id: str, notes: str = ""):
        """Acknowledge the alert"""
        self.acknowledged = True
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now()
        if notes:
            self.resolution_notes = notes
    
    def resolve(self, user_id: str, resolution_notes: str = ""):
        """Mark alert as resolved"""
        if not self.acknowledged:
            self.acknowledge(user_id)
        self.resolved = True
        self.resolution_notes = resolution_notes


class ProgressAnalyzer:
    """Analyzes student progress data and generates insights"""
    
    def __init__(self):
        self.alert_thresholds = {
            'low_success_rate': 0.6,     # Below 60% success rate
            'inactivity_days': 3,        # Inactive for 3+ days
            'session_duration_low': 10,  # Sessions under 10 minutes
            'login_frequency_low': 2,    # Less than 2 logins per week
            'streak_broken_days': 5      # Streak broken for 5+ days
        }
    
    def analyze_student_progress(self, student_id: str, 
                               progress_entries: List[ProgressEntry],
                               accessibility_profile: AccessibilityProfile = None) -> StudentProgress:
        """Analyze progress entries to generate comprehensive student progress"""
        
        if not progress_entries:
            return StudentProgress(student_id=student_id, name=f"Student {student_id}", grade_level=1)
        
        # Basic metrics calculation
        total_interactions = len(progress_entries)
        successful_interactions = len([p for p in progress_entries 
                                     if p.data.get('success', False) or p.data.get('correct', False)])
        
        success_rate = (successful_interactions / total_interactions * 100) if total_interactions > 0 else 0
        
        # Time calculations
        total_time = sum(p.data.get('time_spent_seconds', 0) for p in progress_entries) // 60
        
        # Subject-specific analysis
        subject_data = {}
        for entry in progress_entries:
            subject = entry.data.get('subject', 'unknown')
            if subject not in subject_data:
                subject_data[subject] = {'scores': [], 'time': 0}
            
            if 'score' in entry.data:
                subject_data[subject]['scores'].append(entry.data['score'])
            subject_data[subject]['time'] += entry.data.get('time_spent_seconds', 0) // 60
        
        subject_scores = {}
        subject_time_spent = {}
        for subject, data in subject_data.items():
            if data['scores']:
                subject_scores[subject] = statistics.mean(data['scores'])
            subject_time_spent[subject] = data['time']
        
        # Activity patterns
        recent_entries = [p for p in progress_entries 
                         if (datetime.now() - p.timestamp).days <= 30]
        
        # Calculate streaks
        current_streak = self._calculate_current_streak(progress_entries)
        longest_streak = self._calculate_longest_streak(progress_entries)
        
        # Engagement metrics
        last_active = max(p.timestamp for p in progress_entries) if progress_entries else None
        login_frequency = self._calculate_login_frequency(progress_entries)
        avg_session_duration = self._calculate_avg_session_duration(progress_entries)
        
        # Weekly progress trends
        weekly_progress = self._calculate_weekly_progress(progress_entries)
        daily_activity = self._calculate_daily_activity(progress_entries)
        
        # Accessibility tracking
        accessibility_accommodations = []
        accommodation_usage = {}
        if accessibility_profile:
            if accessibility_profile.requires_voice_only:
                accessibility_accommodations.append("voice_only_mode")
            if accessibility_profile.needs_simplified_language:
                accessibility_accommodations.append("simplified_language")
            if accessibility_profile.requires_patience_mode:
                accessibility_accommodations.append("patience_mode")
        
        # Create progress object
        progress = StudentProgress(
            student_id=student_id,
            name=f"Student {student_id}",
            grade_level=progress_entries[0].data.get('grade_level', 1),
            total_lessons_completed=len(set(p.lesson_id for p in progress_entries)),
            total_time_spent_minutes=total_time,
            success_rate=success_rate,
            current_streak=current_streak,
            longest_streak=longest_streak,
            subject_scores=subject_scores,
            subject_time_spent=subject_time_spent,
            login_frequency=login_frequency,
            avg_session_duration=avg_session_duration,
            last_active=last_active,
            weekly_progress=weekly_progress,
            daily_activity=daily_activity,
            accessibility_accommodations_active=accessibility_accommodations,
            accommodation_usage_frequency=accommodation_usage
        )
        
        # Update status and alerts
        progress.update_progress_status()
        
        return progress
    
    def _calculate_current_streak(self, progress_entries: List[ProgressEntry]) -> int:
        """Calculate current consecutive success streak"""
        if not progress_entries:
            return 0
        
        sorted_entries = sorted(progress_entries, key=lambda x: x.timestamp, reverse=True)
        streak = 0
        
        for entry in sorted_entries:
            if entry.data.get('success', False) or entry.data.get('correct', False):
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_longest_streak(self, progress_entries: List[ProgressEntry]) -> int:
        """Calculate longest consecutive success streak"""
        if not progress_entries:
            return 0
        
        sorted_entries = sorted(progress_entries, key=lambda x: x.timestamp)
        max_streak = 0
        current_streak = 0
        
        for entry in sorted_entries:
            if entry.data.get('success', False) or entry.data.get('correct', False):
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_login_frequency(self, progress_entries: List[ProgressEntry]) -> float:
        """Calculate average logins per week"""
        if not progress_entries:
            return 0.0
        
        # Get unique days with activity
        activity_dates = set(p.timestamp.date() for p in progress_entries)
        
        if not activity_dates:
            return 0.0
        
        # Calculate weeks covered
        earliest = min(activity_dates)
        latest = max(activity_dates)
        weeks = max(1, (latest - earliest).days / 7)
        
        return len(activity_dates) / weeks
    
    def _calculate_avg_session_duration(self, progress_entries: List[ProgressEntry]) -> float:
        """Calculate average session duration in minutes"""
        if not progress_entries:
            return 0.0
        
        # Group entries by session (assuming entries within 30 minutes are same session)
        sessions = []
        current_session_time = 0
        last_timestamp = None
        
        sorted_entries = sorted(progress_entries, key=lambda x: x.timestamp)
        
        for entry in sorted_entries:
            if last_timestamp and (entry.timestamp - last_timestamp).seconds > 1800:  # 30 minutes
                if current_session_time > 0:
                    sessions.append(current_session_time)
                current_session_time = entry.data.get('time_spent_seconds', 60)
            else:
                current_session_time += entry.data.get('time_spent_seconds', 60)
            
            last_timestamp = entry.timestamp
        
        if current_session_time > 0:
            sessions.append(current_session_time)
        
        return statistics.mean(sessions) / 60 if sessions else 0.0  # Convert to minutes
    
    def _calculate_weekly_progress(self, progress_entries: List[ProgressEntry]) -> List[float]:
        """Calculate weekly success rates for the last 4 weeks"""
        if not progress_entries:
            return []
        
        now = datetime.now()
        weekly_progress = []
        
        for week_offset in range(4):
            week_start = now - timedelta(days=(week_offset + 1) * 7)
            week_end = now - timedelta(days=week_offset * 7)
            
            week_entries = [p for p in progress_entries 
                           if week_start <= p.timestamp < week_end]
            
            if week_entries:
                successful = len([p for p in week_entries 
                                if p.data.get('success', False) or p.data.get('correct', False)])
                success_rate = (successful / len(week_entries)) * 100
                weekly_progress.append(success_rate)
            else:
                weekly_progress.append(0.0)
        
        return list(reversed(weekly_progress))  # Oldest to newest
    
    def _calculate_daily_activity(self, progress_entries: List[ProgressEntry]) -> List[int]:
        """Calculate daily activity minutes for the last 7 days"""
        if not progress_entries:
            return []
        
        now = datetime.now()
        daily_activity = []
        
        for day_offset in range(7):
            day_start = (now - timedelta(days=day_offset + 1)).replace(hour=0, minute=0, second=0)
            day_end = day_start + timedelta(days=1)
            
            day_entries = [p for p in progress_entries 
                          if day_start <= p.timestamp < day_end]
            
            total_minutes = sum(p.data.get('time_spent_seconds', 0) for p in day_entries) // 60
            daily_activity.append(total_minutes)
        
        return list(reversed(daily_activity))  # Oldest to newest
    
    def generate_alerts(self, progress: StudentProgress) -> List[Alert]:
        """Generate alerts based on student progress"""
        alerts = []
        
        # Low success rate alert
        if progress.success_rate < self.alert_thresholds['low_success_rate'] * 100:
            alert = Alert(
                alert_id=f"low_success_{progress.student_id}_{datetime.now().strftime('%Y%m%d')}",
                student_id=progress.student_id,
                alert_level=AlertLevel.WARNING if progress.success_rate > 40 else AlertLevel.URGENT,
                title=f"Low Success Rate: {progress.success_rate:.1f}%",
                description=f"Student has a success rate of {progress.success_rate:.1f}%, below the threshold of {self.alert_thresholds['low_success_rate']*100:.1f}%",
                category="academic",
                suggested_actions=[
                    "Review struggling topics and provide additional support",
                    "Consider adjusting difficulty level",
                    "Check if accessibility accommodations are adequate",
                    "Schedule one-on-one session"
                ],
                related_data={
                    "success_rate": progress.success_rate,
                    "struggling_topics": progress.struggling_topics
                }
            )
            alerts.append(alert)
        
        # Inactivity alert
        if progress.last_active:
            days_inactive = (datetime.now() - progress.last_active).days
            if days_inactive >= self.alert_thresholds['inactivity_days']:
                alert = Alert(
                    alert_id=f"inactive_{progress.student_id}_{datetime.now().strftime('%Y%m%d')}",
                    student_id=progress.student_id,
                    alert_level=AlertLevel.WARNING if days_inactive < 7 else AlertLevel.URGENT,
                    title=f"Student Inactive for {days_inactive} Days",
                    description=f"Student has been inactive since {progress.last_active.strftime('%Y-%m-%d')}",
                    category="attendance",
                    suggested_actions=[
                        "Contact student/parent to check on availability",
                        "Check for technical issues or device access problems",
                        "Provide offline learning materials if needed"
                    ],
                    related_data={
                        "last_active": progress.last_active.isoformat(),
                        "days_inactive": days_inactive
                    }
                )
                alerts.append(alert)
        
        # Low engagement alert
        if progress.login_frequency < self.alert_thresholds['login_frequency_low']:
            alert = Alert(
                alert_id=f"low_engagement_{progress.student_id}_{datetime.now().strftime('%Y%m%d')}",
                student_id=progress.student_id,
                alert_level=AlertLevel.INFO,
                title=f"Low Engagement: {progress.login_frequency:.1f} logins/week",
                description=f"Student logs in {progress.login_frequency:.1f} times per week, below recommended frequency",
                category="behavioral",
                suggested_actions=[
                    "Discuss learning schedule with student",
                    "Identify barriers to regular access",
                    "Consider gamification or motivation strategies"
                ],
                related_data={
                    "login_frequency": progress.login_frequency,
                    "avg_session_duration": progress.avg_session_duration
                }
            )
            alerts.append(alert)
        
        return alerts


class DashboardDatabase:
    """Database for storing dashboard data"""
    
    def __init__(self, db_path: str = "dashboard.db"):
        self.db_path = db_path
        self.conn_lock = threading.Lock()
        self._init_database()
    
    def _init_database(self):
        """Initialize dashboard database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS student_progress (
                    student_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    grade_level INTEGER,
                    progress_data TEXT NOT NULL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS iep_goals (
                    goal_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    goal_data TEXT NOT NULL,
                    status TEXT DEFAULT 'not_started',
                    target_date DATETIME,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES student_progress (student_id)
                );
                
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    student_id TEXT NOT NULL,
                    alert_data TEXT NOT NULL,
                    alert_level TEXT NOT NULL,
                    category TEXT DEFAULT 'academic',
                    acknowledged BOOLEAN DEFAULT FALSE,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS weekly_reports (
                    report_id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    week_start_date DATE NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS dashboard_users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    email TEXT,
                    managed_students TEXT DEFAULT '[]',
                    notification_preferences TEXT DEFAULT '{}',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_alerts_student ON alerts(student_id);
                CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(alert_level);
                CREATE INDEX IF NOT EXISTS idx_iep_student ON iep_goals(student_id);
                CREATE INDEX IF NOT EXISTS idx_reports_target ON weekly_reports(target_id);
            """)
    
    def store_student_progress(self, progress: StudentProgress) -> bool:
        """Store student progress data"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    progress_data = json.dumps(asdict(progress), default=str)
                    conn.execute("""
                        INSERT OR REPLACE INTO student_progress 
                        (student_id, name, grade_level, progress_data, last_updated)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (progress.student_id, progress.name, progress.grade_level, progress_data))
            return True
        except Exception as e:
            logger.error(f"Failed to store student progress: {e}")
            return False
    
    def get_student_progress(self, student_id: str) -> Optional[StudentProgress]:
        """Retrieve student progress data"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT progress_data FROM student_progress WHERE student_id = ?
                    """, (student_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        progress_data = json.loads(row['progress_data'])
                        # Convert datetime strings back to datetime objects
                        if progress_data.get('last_active'):
                            progress_data['last_active'] = datetime.fromisoformat(progress_data['last_active'])
                        
                        return StudentProgress(**progress_data)
        except Exception as e:
            logger.error(f"Failed to get student progress: {e}")
        
        return None
    
    def get_all_students_progress(self, teacher_id: str = None) -> List[StudentProgress]:
        """Get progress for all students or students managed by a teacher"""
        students = []
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    if teacher_id:
                        # Get students managed by this teacher
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT managed_students FROM dashboard_users WHERE user_id = ?
                        """, (teacher_id,))
                        row = cursor.fetchone()
                        
                        if row:
                            managed_student_ids = json.loads(row['managed_students'])
                            if managed_student_ids:
                                placeholders = ','.join(['?' for _ in managed_student_ids])
                                cursor.execute(f"""
                                    SELECT progress_data FROM student_progress 
                                    WHERE student_id IN ({placeholders})
                                """, managed_student_ids)
                            else:
                                return []
                        else:
                            return []
                    else:
                        cursor = conn.cursor()
                        cursor.execute("SELECT progress_data FROM student_progress")
                    
                    for row in cursor.fetchall():
                        progress_data = json.loads(row['progress_data'])
                        if progress_data.get('last_active'):
                            progress_data['last_active'] = datetime.fromisoformat(progress_data['last_active'])
                        students.append(StudentProgress(**progress_data))
                        
        except Exception as e:
            logger.error(f"Failed to get all students progress: {e}")
        
        return students
    
    def store_iep_goal(self, goal: IEPGoal) -> bool:
        """Store IEP goal"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    goal_data = json.dumps(asdict(goal), default=str)
                    conn.execute("""
                        INSERT OR REPLACE INTO iep_goals 
                        (goal_id, student_id, goal_data, status, target_date, last_updated)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (goal.goal_id, goal.student_id, goal_data, goal.status.value, goal.target_date))
            return True
        except Exception as e:
            logger.error(f"Failed to store IEP goal: {e}")
            return False
    
    def get_student_iep_goals(self, student_id: str) -> List[IEPGoal]:
        """Get all IEP goals for a student"""
        goals = []
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT goal_data FROM iep_goals WHERE student_id = ?
                        ORDER BY target_date ASC
                    """, (student_id,))
                    
                    for row in cursor.fetchall():
                        goal_data = json.loads(row['goal_data'])
                        # Convert datetime strings back to datetime objects
                        goal_data['target_date'] = datetime.fromisoformat(goal_data['target_date'])
                        goal_data['last_updated'] = datetime.fromisoformat(goal_data['last_updated'])
                        
                        goal = IEPGoal(**goal_data)
                        goals.append(goal)
                        
        except Exception as e:
            logger.error(f"Failed to get IEP goals: {e}")
        
        return goals
    
    def store_alert(self, alert: Alert) -> bool:
        """Store alert"""
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    alert_data = json.dumps(asdict(alert), default=str)
                    conn.execute("""
                        INSERT OR REPLACE INTO alerts 
                        (alert_id, student_id, alert_data, alert_level, category, 
                         acknowledged, resolved, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        alert.alert_id, alert.student_id, alert_data, alert.alert_level.value,
                        alert.category, alert.acknowledged, alert.resolved, alert.created_at
                    ))
            return True
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
            return False
    
    def get_active_alerts(self, student_id: str = None, alert_level: AlertLevel = None) -> List[Alert]:
        """Get active (unresolved) alerts"""
        alerts = []
        try:
            with self.conn_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    
                    query = "SELECT alert_data FROM alerts WHERE resolved = FALSE"
                    params = []
                    
                    if student_id:
                        query += " AND student_id = ?"
                        params.append(student_id)
                    
                    if alert_level:
                        query += " AND alert_level = ?"
                        params.append(alert_level.value)
                    
                    query += " ORDER BY created_at DESC"
                    
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    
                    for row in cursor.fetchall():
                        alert_data = json.loads(row['alert_data'])
                        # Convert datetime strings back to datetime objects
                        alert_data['created_at'] = datetime.fromisoformat(alert_data['created_at'])
                        if alert_data.get('acknowledged_at'):
                            alert_data['acknowledged_at'] = datetime.fromisoformat(alert_data['acknowledged_at'])
                        
                        alert = Alert(**alert_data)
                        alerts.append(alert)
                        
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
        
        return alerts


class WeeklyReportGenerator:
    """Generates comprehensive weekly reports for parents and teachers"""
    
    def __init__(self, database: DashboardDatabase):
        self.database = database
    
    def generate_student_weekly_report(self, student_id: str, week_start: datetime = None) -> dict:
        """Generate weekly report for a single student"""
        if week_start is None:
            # Get start of current week (Monday)
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=7)
        
        # Get student progress
        progress = self.database.get_student_progress(student_id)
        if not progress:
            return {"error": "Student not found"}
        
        # Get IEP goals
        iep_goals = self.database.get_student_iep_goals(student_id)
        
        # Get alerts for the week
        all_alerts = self.database.get_active_alerts(student_id)
        week_alerts = [alert for alert in all_alerts 
                      if week_start <= alert.created_at < week_end]
        
        # Calculate weekly metrics
        weekly_summary = self._calculate_weekly_summary(progress, week_start, week_end)
        
        report = {
            "student_id": student_id,
            "student_name": progress.name,
            "week_start": week_start.strftime('%Y-%m-%d'),
            "week_end": week_end.strftime('%Y-%m-%d'),
            "overall_progress": {
                "success_rate": progress.success_rate,
                "progress_status": progress.progress_status.value,
                "lessons_completed": progress.total_lessons_completed,
                "total_time_minutes": progress.total_time_spent_minutes,
                "current_streak": progress.current_streak
            },
            "weekly_summary": weekly_summary,
            "subject_performance": progress.subject_scores,
            "mastered_topics": progress.mastered_topics,
            "struggling_topics": progress.struggling_topics,
            "accessibility_accommodations": {
                "active_accommodations": progress.accessibility_accommodations_active,
                "usage_frequency": progress.accommodation_usage_frequency
            },
            "iep_goals_progress": [
                {
                    "title": goal.title,
                    "status": goal.status.value,
                    "progress_percentage": goal.get_progress_percentage(),
                    "target_date": goal.target_date.strftime('%Y-%m-%d'),
                    "is_overdue": goal.is_overdue()
                } for goal in iep_goals
            ],
            "alerts_this_week": [
                {
                    "title": alert.title,
                    "level": alert.alert_level.value,
                    "category": alert.category,
                    "suggested_actions": alert.suggested_actions
                } for alert in week_alerts
            ],
            "recommendations": self._generate_recommendations(progress, iep_goals, week_alerts),
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def generate_teacher_weekly_report(self, teacher_id: str, week_start: datetime = None) -> dict:
        """Generate weekly report for a teacher with overview of all students"""
        if week_start is None:
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=7)
        
        # Get all students managed by this teacher
        students = self.database.get_all_students_progress(teacher_id)
        
        if not students:
            return {"error": "No students found for this teacher"}
        
        # Aggregate statistics
        total_students = len(students)
        students_needing_attention = len([s for s in students if s.needs_attention])
        
        # Progress distribution
        progress_distribution = {status.value: 0 for status in ProgressStatus}
        for student in students:
            progress_distribution[student.progress_status.value] += 1
        
        # Subject performance overview
        subject_performance = {}
        for student in students:
            for subject, score in student.subject_scores.items():
                if subject not in subject_performance:
                    subject_performance[subject] = []
                subject_performance[subject].append(score)
        
        # Calculate average scores per subject
        subject_averages = {}
        for subject, scores in subject_performance.items():
            if scores:
                subject_averages[subject] = {
                    "average_score": statistics.mean(scores),
                    "students_count": len(scores),
                    "min_score": min(scores),
                    "max_score": max(scores)
                }
        
        # Get all alerts
        all_alerts = []
        for student in students:
            student_alerts = self.database.get_active_alerts(student.student_id)
            week_alerts = [alert for alert in student_alerts 
                          if week_start <= alert.created_at < week_end]
            all_alerts.extend(week_alerts)
        
        # Alert distribution
        alert_distribution = {level.value: 0 for level in AlertLevel}
        for alert in all_alerts:
            alert_distribution[alert.alert_level.value] += 1
        
        # Students requiring immediate attention
        urgent_students = []
        for student in students:
            student_alerts = [a for a in all_alerts if a.student_id == student.student_id]
            urgent_alerts = [a for a in student_alerts if a.alert_level in [AlertLevel.URGENT, AlertLevel.CRITICAL]]
            
            if urgent_alerts or student.progress_status == ProgressStatus.AT_RISK:
                urgent_students.append({
                    "student_id": student.student_id,
                    "student_name": student.name,
                    "progress_status": student.progress_status.value,
                    "success_rate": student.success_rate,
                    "urgent_alerts": len(urgent_alerts),
                    "days_inactive": (datetime.now() - student.last_active).days if student.last_active else 999
                })
        
        # Sort urgent students by priority (most urgent first)
        urgent_students.sort(key=lambda x: (x["urgent_alerts"], -x["success_rate"], x["days_inactive"]), reverse=True)
        
        report = {
            "teacher_id": teacher_id,
            "week_start": week_start.strftime('%Y-%m-%d'),
            "week_end": week_end.strftime('%Y-%m-%d'),
            "class_overview": {
                "total_students": total_students,
                "students_needing_attention": students_needing_attention,
                "progress_distribution": progress_distribution,
                "overall_class_success_rate": statistics.mean([s.success_rate for s in students]) if students else 0
            },
            "subject_performance": subject_averages,
            "alerts_summary": {
                "total_alerts": len(all_alerts),
                "alert_distribution": alert_distribution,
                "students_with_alerts": len(set(a.student_id for a in all_alerts))
            },
            "urgent_attention_required": urgent_students[:10],  # Top 10 most urgent
            "accessibility_insights": self._generate_accessibility_insights(students),
            "weekly_trends": self._calculate_class_trends(students),
            "recommendations": self._generate_teacher_recommendations(students, all_alerts),
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    def _calculate_weekly_summary(self, progress: StudentProgress, week_start: datetime, week_end: datetime) -> dict:
        """Calculate weekly summary metrics"""
        # This would typically analyze progress entries from the week
        # For now, using existing aggregated data
        
        current_week_index = len(progress.weekly_progress) - 1 if progress.weekly_progress else 0
        current_week_success = progress.weekly_progress[current_week_index] if progress.weekly_progress else 0
        
        previous_week_success = 0
        if len(progress.weekly_progress) > 1:
            previous_week_success = progress.weekly_progress[current_week_index - 1]
        
        improvement = current_week_success - previous_week_success
        
        return {
            "success_rate_this_week": current_week_success,
            "improvement_from_last_week": improvement,
            "total_time_this_week": sum(progress.daily_activity),
            "average_daily_activity": statistics.mean(progress.daily_activity) if progress.daily_activity else 0,
            "login_count_this_week": progress.login_frequency * 1,  # Approximation
            "streak_maintained": progress.current_streak > 0
        }
    
    def _generate_recommendations(self, progress: StudentProgress, iep_goals: List[IEPGoal], alerts: List[Alert]) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Academic recommendations
        if progress.success_rate < 70:
            recommendations.append("Consider reviewing fundamental concepts and providing additional practice")
            
        if progress.struggling_topics:
            recommendations.append(f"Focus extra attention on: {', '.join(progress.struggling_topics[:3])}")
        
        # Engagement recommendations
        if progress.login_frequency < 3:
            recommendations.append("Encourage more regular study sessions - aim for daily engagement")
        
        if progress.avg_session_duration < 15:
            recommendations.append("Consider longer study sessions with breaks to improve learning retention")
        
        # IEP goal recommendations
        overdue_goals = [goal for goal in iep_goals if goal.is_overdue()]
        if overdue_goals:
            recommendations.append(f"Review and potentially modify {len(overdue_goals)} overdue IEP goals")
        
        # Alert-based recommendations
        critical_alerts = [alert for alert in alerts if alert.alert_level == AlertLevel.CRITICAL]
        if critical_alerts:
            recommendations.append("Immediate intervention required - contact student/parent urgently")
        
        # Accessibility recommendations
        if progress.accessibility_accommodations_active:
            recommendations.append("Continue monitoring effectiveness of current accessibility accommodations")
        
        return recommendations
    
    def _generate_accessibility_insights(self, students: List[StudentProgress]) -> dict:
        """Generate insights about accessibility accommodation usage"""
        total_students = len(students)
        students_with_accommodations = len([s for s in students if s.accessibility_accommodations_active])
        
        # Count accommodation types
        accommodation_usage = {}
        for student in students:
            for accommodation in student.accessibility_accommodations_active:
                accommodation_usage[accommodation] = accommodation_usage.get(accommodation, 0) + 1
        
        return {
            "total_students_with_accommodations": students_with_accommodations,
            "percentage_using_accommodations": (students_with_accommodations / total_students * 100) if total_students > 0 else 0,
            "most_common_accommodations": dict(sorted(accommodation_usage.items(), key=lambda x: x[1], reverse=True)),
            "accommodation_effectiveness": "Monitor individual student progress to assess effectiveness"
        }
    
    def _calculate_class_trends(self, students: List[StudentProgress]) -> dict:
        """Calculate class-wide trends"""
        if not students:
            return {}
        
        # Success rate trends
        all_weekly_progress = []
        for student in students:
            all_weekly_progress.extend(student.weekly_progress)
        
        avg_weekly_progress = statistics.mean(all_weekly_progress) if all_weekly_progress else 0
        
        # Activity trends
        all_daily_activity = []
        for student in students:
            all_daily_activity.extend(student.daily_activity)
        
        avg_daily_activity = statistics.mean(all_daily_activity) if all_daily_activity else 0
        
        return {
            "class_average_success_rate": statistics.mean([s.success_rate for s in students]),
            "class_average_weekly_progress": avg_weekly_progress,
            "class_average_daily_activity": avg_daily_activity,
            "most_mastered_topics": self._get_most_common_topics([s.mastered_topics for s in students]),
            "most_struggling_topics": self._get_most_common_topics([s.struggling_topics for s in students])
        }
    
    def _get_most_common_topics(self, topic_lists: List[List[str]]) -> List[str]:
        """Get most commonly appearing topics across all students"""
        topic_counts = {}
        for topics in topic_lists:
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return [topic for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)][:5]
    
    def _generate_teacher_recommendations(self, students: List[StudentProgress], alerts: List[Alert]) -> List[str]:
        """Generate recommendations for teachers managing multiple students"""
        recommendations = []
        
        at_risk_count = len([s for s in students if s.progress_status == ProgressStatus.AT_RISK])
        if at_risk_count > 0:
            recommendations.append(f"Priority: {at_risk_count} students are at risk and need immediate support")
        
        struggling_count = len([s for s in students if s.progress_status == ProgressStatus.STRUGGLING])
        if struggling_count > 0:
            recommendations.append(f"{struggling_count} students are struggling - consider small group interventions")
        
        # Alert-based recommendations
        urgent_alerts = [a for a in alerts if a.alert_level in [AlertLevel.URGENT, AlertLevel.CRITICAL]]
        if urgent_alerts:
            recommendations.append(f"Address {len(urgent_alerts)} urgent alerts requiring immediate attention")
        
        # Class-wide patterns
        inactive_students = len([s for s in students if s.login_frequency < 2])
        if inactive_students > len(students) * 0.3:  # More than 30% inactive
            recommendations.append("High number of inactive students - consider outreach campaign")
        
        return recommendations


class ParentTeacherDashboard:
    """Main dashboard system for parents and teachers"""
    
    def __init__(self, db_path: str = "dashboard.db"):
        self.database = DashboardDatabase(db_path)
        self.progress_analyzer = ProgressAnalyzer()
        self.report_generator = WeeklyReportGenerator(self.database)
        
        # Email configuration for alerts
        self.email_config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "",
            "password": "",
            "from_address": ""
        }
    
    def update_student_progress(self, student_id: str, progress_entries: List[ProgressEntry],
                               accessibility_profile: AccessibilityProfile = None) -> bool:
        """Update comprehensive student progress from learning data"""
        
        # Analyze progress
        progress = self.progress_analyzer.analyze_student_progress(
            student_id, progress_entries, accessibility_profile
        )
        
        # Store progress
        success = self.database.store_student_progress(progress)
        
        if success:
            # Generate and store alerts
            alerts = self.progress_analyzer.generate_alerts(progress)
            for alert in alerts:
                self.database.store_alert(alert)
            
            logger.info(f"Updated progress for student {student_id}: {len(alerts)} alerts generated")
        
        return success
    
    def get_student_dashboard(self, student_id: str) -> dict:
        """Get comprehensive dashboard data for a student"""
        progress = self.database.get_student_progress(student_id)
        if not progress:
            return {"error": "Student not found"}
        
        iep_goals = self.database.get_student_iep_goals(student_id)
        active_alerts = self.database.get_active_alerts(student_id)
        
        return {
            "student_info": {
                "student_id": progress.student_id,
                "name": progress.name,
                "grade_level": progress.grade_level,
                "progress_status": progress.progress_status.value
            },
            "academic_performance": {
                "overall_success_rate": progress.success_rate,
                "lessons_completed": progress.total_lessons_completed,
                "total_time_spent": progress.total_time_spent_minutes,
                "subject_scores": progress.subject_scores,
                "mastered_topics": progress.mastered_topics,
                "struggling_topics": progress.struggling_topics
            },
            "engagement_metrics": {
                "login_frequency": progress.login_frequency,
                "avg_session_duration": progress.avg_session_duration,
                "current_streak": progress.current_streak,
                "longest_streak": progress.longest_streak,
                "last_active": progress.last_active.isoformat() if progress.last_active else None
            },
            "progress_trends": {
                "weekly_progress": progress.weekly_progress,
                "daily_activity": progress.daily_activity
            },
            "accessibility_status": {
                "active_accommodations": progress.accessibility_accommodations_active,
                "usage_frequency": progress.accommodation_usage_frequency
            },
            "iep_goals": [
                {
                    "goal_id": goal.goal_id,
                    "title": goal.title,
                    "description": goal.description,
                    "status": goal.status.value,
                    "progress_percentage": goal.get_progress_percentage(),
                    "target_date": goal.target_date.strftime('%Y-%m-%d'),
                    "is_overdue": goal.is_overdue(),
                    "recent_notes": goal.progress_notes[-3:] if goal.progress_notes else []
                } for goal in iep_goals
            ],
            "active_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "title": alert.title,
                    "description": alert.description,
                    "level": alert.alert_level.value,
                    "category": alert.category,
                    "created_at": alert.created_at.strftime('%Y-%m-%d %H:%M'),
                    "suggested_actions": alert.suggested_actions
                } for alert in active_alerts
            ]
        }
    
    def get_teacher_dashboard(self, teacher_id: str) -> dict:
        """Get teacher dashboard with overview of all managed students"""
        students = self.database.get_all_students_progress(teacher_id)
        
        if not students:
            return {"error": "No students found for this teacher"}
        
        # Summary statistics
        total_students = len(students)
        students_needing_attention = [s for s in students if s.needs_attention]
        
        # Get all active alerts
        all_alerts = []
        for student in students:
            student_alerts = self.database.get_active_alerts(student.student_id)
            all_alerts.extend(student_alerts)
        
        # Priority students (need immediate attention)
        priority_students = []
        for student in students:
            if student.needs_attention:
                student_alerts = [a for a in all_alerts if a.student_id == student.student_id]
                urgent_alerts = [a for a in student_alerts if a.alert_level in [AlertLevel.URGENT, AlertLevel.CRITICAL]]
                
                priority_students.append({
                    "student_id": student.student_id,
                    "name": student.name,
                    "progress_status": student.progress_status.value,
                    "success_rate": student.success_rate,
                    "alert_count": len(student_alerts),
                    "urgent_alerts": len(urgent_alerts),
                    "main_concerns": student.alert_reasons[:2]  # Top 2 concerns
                })
        
        # Sort by urgency
        priority_students.sort(key=lambda x: (x["urgent_alerts"], -x["success_rate"]), reverse=True)
        
        return {
            "teacher_id": teacher_id,
            "class_summary": {
                "total_students": total_students,
                "students_needing_attention": len(students_needing_attention),
                "total_active_alerts": len(all_alerts),
                "average_class_success_rate": statistics.mean([s.success_rate for s in students]) if students else 0
            },
            "priority_students": priority_students[:10],  # Top 10 priority students
            "alert_summary": {
                "critical": len([a for a in all_alerts if a.alert_level == AlertLevel.CRITICAL]),
                "urgent": len([a for a in all_alerts if a.alert_level == AlertLevel.URGENT]),
                "warning": len([a for a in all_alerts if a.alert_level == AlertLevel.WARNING]),
                "info": len([a for a in all_alerts if a.alert_level == AlertLevel.INFO])
            },
            "student_distribution": {
                "excellent": len([s for s in students if s.progress_status == ProgressStatus.EXCELLENT]),
                "good": len([s for s in students if s.progress_status == ProgressStatus.GOOD]),
                "struggling": len([s for s in students if s.progress_status == ProgressStatus.STRUGGLING]),
                "at_risk": len([s for s in students if s.progress_status == ProgressStatus.AT_RISK])
            },
            "recent_activity": [
                {
                    "student_id": s.student_id,
                    "name": s.name,
                    "last_active": s.last_active.strftime('%Y-%m-%d') if s.last_active else "Never",
                    "success_rate": s.success_rate
                } for s in sorted(students, key=lambda x: x.last_active or datetime.min, reverse=True)[:10]
            ]
        }
    
    def acknowledge_alert(self, alert_id: str, user_id: str, notes: str = "") -> bool:
        """Acknowledge an alert"""
        # This would typically update the alert in the database
        # For now, return success
        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        return True
    
    def create_iep_goal(self, student_id: str, title: str, description: str,
                       target_date: datetime, measurable_objective: str) -> str:
        """Create a new IEP goal for a student"""
        
        goal_id = f"iep_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        goal = IEPGoal(
            goal_id=goal_id,
            student_id=student_id,
            title=title,
            description=description,
            target_date=target_date,
            measurable_objective=measurable_objective
        )
        
        success = self.database.store_iep_goal(goal)
        
        if success:
            logger.info(f"Created IEP goal {goal_id} for student {student_id}")
            return goal_id
        else:
            return ""
    
    def update_iep_goal_progress(self, goal_id: str, progress_value: float,
                                note: str, author: str = "teacher") -> bool:
        """Update progress on an IEP goal"""
        # This would typically load the goal, update it, and save it back
        # For now, log the update
        logger.info(f"Updated IEP goal {goal_id}: {progress_value}% - {note}")
        return True
    
    def generate_weekly_report(self, target_id: str, target_type: str = "student") -> dict:
        """Generate weekly report for student or teacher"""
        
        if target_type == "student":
            return self.report_generator.generate_student_weekly_report(target_id)
        elif target_type == "teacher":
            return self.report_generator.generate_teacher_weekly_report(target_id)
        else:
            return {"error": "Invalid target type"}
    
    def send_alert_notification(self, alert: Alert, recipient_email: str) -> bool:
        """Send email notification for urgent alerts"""
        
        if not self.email_config["username"]:
            logger.warning("Email not configured - cannot send alert notification")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config["from_address"]
            msg['To'] = recipient_email
            msg['Subject'] = f"EduAGI Alert: {alert.title}"
            
            body = f"""
            Student Alert: {alert.title}
            
            Student ID: {alert.student_id}
            Alert Level: {alert.alert_level.value.upper()}
            Category: {alert.category}
            
            Description: {alert.description}
            
            Suggested Actions:
            """
            
            for action in alert.suggested_actions:
                body += f"• {action}\n"
            
            body += f"""
            
            Created: {alert.created_at.strftime('%Y-%m-%d %H:%M')}
            
            Please log into the EduAGI dashboard to acknowledge this alert.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            text = msg.as_string()
            server.sendmail(self.email_config["from_address"], recipient_email, text)
            server.quit()
            
            logger.info(f"Alert notification sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize dashboard
    dashboard = ParentTeacherDashboard()
    
    # Create sample progress entries
    sample_progress = [
        ProgressEntry(
            student_id="student_123",
            lesson_id="math_001",
            timestamp=datetime.now() - timedelta(days=1),
            interaction_type="lesson_completed",
            data={
                "subject": "mathematics",
                "success": True,
                "score": 85,
                "time_spent_seconds": 1200,
                "grade_level": 4
            }
        ),
        ProgressEntry(
            student_id="student_123",
            lesson_id="math_002",
            timestamp=datetime.now(),
            interaction_type="quiz_completed",
            data={
                "subject": "mathematics",
                "success": False,
                "score": 45,
                "time_spent_seconds": 800,
                "grade_level": 4
            }
        )
    ]
    
    # Update student progress
    dashboard.update_student_progress("student_123", sample_progress)
    
    # Create IEP goal
    iep_goal_id = dashboard.create_iep_goal(
        "student_123",
        "Improve Math Problem Solving",
        "Student will solve multi-step word problems involving fractions",
        datetime.now() + timedelta(days=90),
        "Achieve 80% accuracy on grade-level word problems"
    )
    
    # Get student dashboard
    student_dashboard = dashboard.get_student_dashboard("student_123")
    print("Student Dashboard:")
    print(json.dumps(student_dashboard, indent=2, default=str))
    
    # Generate weekly report
    weekly_report = dashboard.generate_weekly_report("student_123", "student")
    print("\nWeekly Report:")
    print(json.dumps(weekly_report, indent=2, default=str))