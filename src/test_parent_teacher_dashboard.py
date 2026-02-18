"""
Tests for parent_teacher_dashboard.py module

Comprehensive tests for parent/teacher dashboard including progress tracking,
IEP goal management, alert system, and weekly report generation.
"""

import pytest
import sqlite3
import tempfile
import json
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from parent_teacher_dashboard import (
    ParentTeacherDashboard, DashboardDatabase, ProgressAnalyzer, WeeklyReportGenerator,
    StudentProgress, IEPGoal, Alert, AlertLevel, ProgressStatus, IEPGoalStatus
)
from accessibility_engine import AccessibilityProfile, ImpairmentType, SeverityLevel
from offline_learning import ProgressEntry


class TestProgressStatus:
    """Test ProgressStatus enum"""
    
    def test_progress_status_values(self):
        """Test progress status enum values"""
        assert ProgressStatus.EXCELLENT.value == "excellent"
        assert ProgressStatus.GOOD.value == "good"
        assert ProgressStatus.STRUGGLING.value == "struggling"
        assert ProgressStatus.AT_RISK.value == "at_risk"


class TestAlertLevel:
    """Test AlertLevel enum"""
    
    def test_alert_level_values(self):
        """Test alert level enum values"""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.URGENT.value == "urgent"
        assert AlertLevel.CRITICAL.value == "critical"


class TestIEPGoalStatus:
    """Test IEPGoalStatus enum"""
    
    def test_iep_goal_status_values(self):
        """Test IEP goal status enum values"""
        assert IEPGoalStatus.NOT_STARTED.value == "not_started"
        assert IEPGoalStatus.IN_PROGRESS.value == "in_progress"
        assert IEPGoalStatus.ACHIEVED.value == "achieved"
        assert IEPGoalStatus.NEEDS_MODIFICATION.value == "needs_modification"
        assert IEPGoalStatus.ON_HOLD.value == "on_hold"


class TestStudentProgress:
    """Test StudentProgress dataclass"""
    
    def test_student_progress_creation(self):
        """Test basic student progress creation"""
        progress = StudentProgress(
            student_id="test_student",
            name="Test Student",
            grade_level=4,
            total_lessons_completed=15,
            total_time_spent_minutes=900,
            success_rate=85.0,
            subject_scores={"Mathematics": 88.5, "Science": 82.0},
            subject_time_spent={"Mathematics": 450, "Science": 450}
        )
        
        assert progress.student_id == "test_student"
        assert progress.name == "Test Student"
        assert progress.grade_level == 4
        assert progress.success_rate == 85.0
        assert len(progress.subject_scores) == 2
        assert progress.subject_scores["Mathematics"] == 88.5
    
    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        progress = StudentProgress(
            student_id="score_test",
            name="Score Test",
            grade_level=3,
            subject_scores={"Math": 90.0, "Science": 80.0, "English": 85.0}
        )
        
        overall_score = progress.calculate_overall_score()
        expected_score = (90.0 + 80.0 + 85.0) / 3
        assert overall_score == expected_score
        
        # Test with no subjects
        empty_progress = StudentProgress(student_id="empty", name="Empty", grade_level=1)
        assert empty_progress.calculate_overall_score() == 0.0
    
    def test_update_progress_status(self):
        """Test progress status update based on scores"""
        # Test excellent status
        excellent_progress = StudentProgress(
            student_id="excellent", name="Excellent", grade_level=5,
            subject_scores={"Math": 95.0, "Science": 92.0}
        )
        excellent_progress.update_progress_status()
        assert excellent_progress.progress_status == ProgressStatus.EXCELLENT
        assert not excellent_progress.needs_attention
        
        # Test struggling status with low engagement
        struggling_progress = StudentProgress(
            student_id="struggling", name="Struggling", grade_level=3,
            subject_scores={"Math": 60.0, "Science": 65.0},
            login_frequency=1.5  # Low frequency
        )
        struggling_progress.update_progress_status()
        assert struggling_progress.progress_status == ProgressStatus.STRUGGLING
        assert struggling_progress.needs_attention
        assert "Low academic performance" in struggling_progress.alert_reasons[0]
        assert "Low engagement" in struggling_progress.alert_reasons[1]
        
        # Test at-risk status
        at_risk_progress = StudentProgress(
            student_id="at_risk", name="At Risk", grade_level=2,
            subject_scores={"Math": 40.0, "Science": 35.0},
            last_active=datetime.now() - timedelta(days=5)
        )
        at_risk_progress.update_progress_status()
        assert at_risk_progress.progress_status == ProgressStatus.AT_RISK
        assert at_risk_progress.needs_attention
        assert len(at_risk_progress.alert_reasons) >= 2  # Low performance + inactive


class TestIEPGoal:
    """Test IEPGoal dataclass"""
    
    def test_iep_goal_creation(self):
        """Test IEP goal creation"""
        target_date = datetime.now() + timedelta(days=90)
        goal = IEPGoal(
            goal_id="goal_001",
            student_id="student_123",
            title="Improve Reading Comprehension",
            description="Student will improve reading comprehension skills",
            target_date=target_date,
            measurable_objective="Achieve 80% accuracy on grade-level reading passages",
            current_level=25.0,
            target_level=80.0
        )
        
        assert goal.goal_id == "goal_001"
        assert goal.student_id == "student_123"
        assert goal.title == "Improve Reading Comprehension"
        assert goal.current_level == 25.0
        assert goal.target_level == 80.0
        assert goal.status == IEPGoalStatus.NOT_STARTED
    
    def test_add_progress_note(self):
        """Test adding progress notes to IEP goal"""
        goal = IEPGoal(
            goal_id="progress_test",
            student_id="student_456",
            title="Test Goal",
            description="Test Description",
            target_date=datetime.now() + timedelta(days=60),
            measurable_objective="Test Objective"
        )
        
        # Add progress note with value
        goal.add_progress_note("Good progress this week", 45.0, "teacher")
        
        assert len(goal.progress_notes) == 1
        assert goal.progress_notes[0]["note"] == "Good progress this week"
        assert goal.progress_notes[0]["progress_value"] == 45.0
        assert goal.progress_notes[0]["author"] == "teacher"
        assert goal.current_level == 45.0
    
    def test_update_status_based_on_progress(self):
        """Test automatic status update based on progress"""
        goal = IEPGoal(
            goal_id="status_test",
            student_id="student_789",
            title="Status Test Goal",
            description="Test Description",
            target_date=datetime.now() + timedelta(days=30),
            measurable_objective="Test Objective",
            target_level=100.0
        )
        
        # Test not started (0% progress)
        goal.current_level = 0.0
        goal.update_status()
        assert goal.status == IEPGoalStatus.NOT_STARTED
        
        # Test in progress (50% progress)
        goal.current_level = 50.0
        goal.update_status()
        assert goal.status == IEPGoalStatus.IN_PROGRESS
        
        # Test achieved (100% progress)
        goal.current_level = 100.0
        goal.update_status()
        assert goal.status == IEPGoalStatus.ACHIEVED
        
        # Test needs modification (overdue with low progress)
        goal.current_level = 30.0
        goal.target_date = datetime.now() - timedelta(days=10)  # Past due
        goal.update_status()
        assert goal.status == IEPGoalStatus.NEEDS_MODIFICATION
    
    def test_get_progress_percentage(self):
        """Test progress percentage calculation"""
        goal = IEPGoal(
            goal_id="percentage_test",
            student_id="student_abc",
            title="Percentage Test",
            description="Test",
            target_date=datetime.now() + timedelta(days=30),
            measurable_objective="Test",
            current_level=60.0,
            target_level=80.0
        )
        
        percentage = goal.get_progress_percentage()
        expected = (60.0 / 80.0) * 100
        assert percentage == expected
    
    def test_is_overdue(self):
        """Test overdue detection"""
        # Not overdue
        future_goal = IEPGoal(
            goal_id="future_goal",
            student_id="student_def",
            title="Future Goal",
            description="Test",
            target_date=datetime.now() + timedelta(days=30),
            measurable_objective="Test"
        )
        assert not future_goal.is_overdue()
        
        # Overdue but achieved
        achieved_goal = IEPGoal(
            goal_id="achieved_goal",
            student_id="student_ghi",
            title="Achieved Goal",
            description="Test",
            target_date=datetime.now() - timedelta(days=10),
            measurable_objective="Test",
            status=IEPGoalStatus.ACHIEVED
        )
        assert not achieved_goal.is_overdue()  # Achieved goals are not overdue
        
        # Overdue and not achieved
        overdue_goal = IEPGoal(
            goal_id="overdue_goal",
            student_id="student_jkl",
            title="Overdue Goal",
            description="Test",
            target_date=datetime.now() - timedelta(days=5),
            measurable_objective="Test",
            status=IEPGoalStatus.IN_PROGRESS
        )
        assert overdue_goal.is_overdue()


class TestAlert:
    """Test Alert dataclass"""
    
    def test_alert_creation(self):
        """Test alert creation"""
        alert = Alert(
            alert_id="alert_001",
            student_id="student_alert",
            alert_level=AlertLevel.WARNING,
            title="Low Success Rate",
            description="Student has 45% success rate, below threshold",
            category="academic",
            suggested_actions=["Review materials", "Schedule tutoring"]
        )
        
        assert alert.alert_id == "alert_001"
        assert alert.student_id == "student_alert"
        assert alert.alert_level == AlertLevel.WARNING
        assert alert.title == "Low Success Rate"
        assert not alert.acknowledged
        assert not alert.resolved
        assert len(alert.suggested_actions) == 2
    
    def test_acknowledge_alert(self):
        """Test alert acknowledgment"""
        alert = Alert(
            alert_id="ack_test",
            student_id="student_ack",
            alert_level=AlertLevel.INFO,
            title="Test Alert",
            description="Test Description"
        )
        
        assert not alert.acknowledged
        
        alert.acknowledge("teacher_123", "Reviewing with student")
        
        assert alert.acknowledged
        assert alert.acknowledged_by == "teacher_123"
        assert alert.resolution_notes == "Reviewing with student"
        assert alert.acknowledged_at is not None
    
    def test_resolve_alert(self):
        """Test alert resolution"""
        alert = Alert(
            alert_id="resolve_test",
            student_id="student_resolve",
            alert_level=AlertLevel.URGENT,
            title="Urgent Alert",
            description="Urgent Description"
        )
        
        assert not alert.resolved
        
        alert.resolve("teacher_456", "Issue has been addressed")
        
        assert alert.resolved
        assert alert.acknowledged  # Should be acknowledged when resolved
        assert alert.acknowledged_by == "teacher_456"
        assert alert.resolution_notes == "Issue has been addressed"


class TestProgressAnalyzer:
    """Test ProgressAnalyzer class"""
    
    def test_progress_analyzer_initialization(self):
        """Test progress analyzer initialization"""
        analyzer = ProgressAnalyzer()
        
        assert hasattr(analyzer, 'alert_thresholds')
        assert 'low_success_rate' in analyzer.alert_thresholds
        assert 'inactivity_days' in analyzer.alert_thresholds
    
    def test_analyze_student_progress_basic(self):
        """Test basic student progress analysis"""
        analyzer = ProgressAnalyzer()
        
        # Create sample progress entries
        progress_entries = [
            ProgressEntry(
                student_id="analyze_student",
                lesson_id="lesson_001",
                timestamp=datetime.now() - timedelta(days=1),
                interaction_type="lesson_completed",
                data={"success": True, "score": 85, "time_spent_seconds": 1200, "grade_level": 4, "subject": "math"}
            ),
            ProgressEntry(
                student_id="analyze_student",
                lesson_id="lesson_002",
                timestamp=datetime.now(),
                interaction_type="quiz_completed",
                data={"success": True, "score": 92, "time_spent_seconds": 800, "grade_level": 4, "subject": "science"}
            ),
            ProgressEntry(
                student_id="analyze_student",
                lesson_id="lesson_003",
                timestamp=datetime.now(),
                interaction_type="exercise_completed",
                data={"success": False, "score": 55, "time_spent_seconds": 600, "grade_level": 4, "subject": "math"}
            )
        ]
        
        progress = analyzer.analyze_student_progress("analyze_student", progress_entries)
        
        assert progress.student_id == "analyze_student"
        assert progress.total_lessons_completed == 3  # 3 unique lessons
        assert progress.success_rate == (2/3) * 100  # 2 out of 3 successful
        assert progress.total_time_spent_minutes == (1200 + 800 + 600) // 60
        assert "math" in progress.subject_scores
        assert "science" in progress.subject_scores
        assert progress.last_active is not None
    
    def test_analyze_empty_progress_entries(self):
        """Test analysis with no progress entries"""
        analyzer = ProgressAnalyzer()
        
        progress = analyzer.analyze_student_progress("empty_student", [])
        
        assert progress.student_id == "empty_student"
        assert progress.total_lessons_completed == 0
        assert progress.success_rate == 0
        assert progress.total_time_spent_minutes == 0
    
    def test_analyze_with_accessibility_profile(self):
        """Test analysis with accessibility profile"""
        analyzer = ProgressAnalyzer()
        
        # Create accessibility profile
        accessibility_profile = AccessibilityProfile(user_id="accessible_student")
        accessibility_profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MODERATE)
        accessibility_profile.add_impairment(ImpairmentType.VISUAL, "low_vision", SeverityLevel.MILD)
        
        progress_entries = [
            ProgressEntry(
                student_id="accessible_student",
                lesson_id="lesson_001",
                timestamp=datetime.now(),
                interaction_type="lesson_completed",
                data={"success": True, "score": 75, "time_spent_seconds": 900}
            )
        ]
        
        progress = analyzer.analyze_student_progress("accessible_student", progress_entries, accessibility_profile)
        
        assert len(progress.accessibility_accommodations_active) > 0
        assert "simplified_language" in progress.accessibility_accommodations_active
        assert "patience_mode" in progress.accessibility_accommodations_active
    
    def test_generate_alerts(self):
        """Test alert generation"""
        analyzer = ProgressAnalyzer()
        
        # Create progress with low success rate
        low_success_progress = StudentProgress(
            student_id="low_success_student",
            name="Low Success Student",
            grade_level=3,
            success_rate=45.0,  # Below threshold
            login_frequency=1.0,  # Low frequency
            last_active=datetime.now() - timedelta(days=5)  # Inactive
        )
        
        alerts = analyzer.generate_alerts(low_success_progress)
        
        assert len(alerts) >= 3  # Should generate multiple alerts
        
        # Check for low success rate alert
        success_alert = next((a for a in alerts if "Low Success Rate" in a.title), None)
        assert success_alert is not None
        assert success_alert.alert_level in [AlertLevel.WARNING, AlertLevel.URGENT]
        
        # Check for inactivity alert
        inactive_alert = next((a for a in alerts if "Inactive" in a.title), None)
        assert inactive_alert is not None
        
        # Check for low engagement alert
        engagement_alert = next((a for a in alerts if "Low Engagement" in a.title), None)
        assert engagement_alert is not None
    
    def test_streak_calculations(self):
        """Test streak calculation methods"""
        analyzer = ProgressAnalyzer()
        
        # Create entries with success pattern
        progress_entries = [
            ProgressEntry("student", "lesson_1", datetime.now() - timedelta(days=5), "completed", {"success": True}),
            ProgressEntry("student", "lesson_2", datetime.now() - timedelta(days=4), "completed", {"success": True}),
            ProgressEntry("student", "lesson_3", datetime.now() - timedelta(days=3), "completed", {"success": False}),
            ProgressEntry("student", "lesson_4", datetime.now() - timedelta(days=2), "completed", {"success": True}),
            ProgressEntry("student", "lesson_5", datetime.now() - timedelta(days=1), "completed", {"success": True}),
        ]
        
        current_streak = analyzer._calculate_current_streak(progress_entries)
        assert current_streak == 2  # Last 2 are successful
        
        longest_streak = analyzer._calculate_longest_streak(progress_entries)
        assert longest_streak == 2  # Longest consecutive streak is 2


class TestDashboardDatabase:
    """Test DashboardDatabase class"""
    
    def test_database_initialization(self):
        """Test database initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            
            # Check that tables were created
            with sqlite3.connect(temp_db.name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                expected_tables = ['student_progress', 'iep_goals', 'alerts', 'weekly_reports', 'dashboard_users']
                for table in expected_tables:
                    assert table in tables
    
    def test_store_and_retrieve_student_progress(self):
        """Test storing and retrieving student progress"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            
            # Create test progress
            progress = StudentProgress(
                student_id="db_test_student",
                name="DB Test Student",
                grade_level=4,
                success_rate=82.5,
                subject_scores={"Math": 85.0, "Science": 80.0},
                last_active=datetime.now() - timedelta(hours=2)
            )
            
            # Store progress
            success = db.store_student_progress(progress)
            assert success is True
            
            # Retrieve progress
            retrieved = db.get_student_progress("db_test_student")
            assert retrieved is not None
            assert retrieved.student_id == "db_test_student"
            assert retrieved.name == "DB Test Student"
            assert retrieved.success_rate == 82.5
            assert "Math" in retrieved.subject_scores
            assert isinstance(retrieved.last_active, datetime)
    
    def test_store_and_retrieve_iep_goal(self):
        """Test storing and retrieving IEP goals"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            
            # Create test IEP goal
            goal = IEPGoal(
                goal_id="db_iep_test",
                student_id="iep_student",
                title="Test IEP Goal",
                description="Test Description",
                target_date=datetime.now() + timedelta(days=90),
                measurable_objective="Achieve 80% accuracy"
            )
            
            # Store goal
            success = db.store_iep_goal(goal)
            assert success is True
            
            # Retrieve goals for student
            goals = db.get_student_iep_goals("iep_student")
            assert len(goals) == 1
            assert goals[0].goal_id == "db_iep_test"
            assert goals[0].title == "Test IEP Goal"
            assert isinstance(goals[0].target_date, datetime)
    
    def test_store_and_retrieve_alerts(self):
        """Test storing and retrieving alerts"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            
            # Create test alert
            alert = Alert(
                alert_id="db_alert_test",
                student_id="alert_student",
                alert_level=AlertLevel.WARNING,
                title="Test Alert",
                description="Test Alert Description",
                category="academic"
            )
            
            # Store alert
            success = db.store_alert(alert)
            assert success is True
            
            # Retrieve active alerts
            alerts = db.get_active_alerts("alert_student")
            assert len(alerts) == 1
            assert alerts[0].alert_id == "db_alert_test"
            assert alerts[0].alert_level == AlertLevel.WARNING
            
            # Retrieve alerts by level
            warning_alerts = db.get_active_alerts(alert_level=AlertLevel.WARNING)
            assert len(warning_alerts) >= 1
    
    def test_get_all_students_progress(self):
        """Test retrieving all students' progress"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            
            # Store multiple students
            students = [
                StudentProgress("student_1", "Student One", 3, success_rate=85.0),
                StudentProgress("student_2", "Student Two", 4, success_rate=72.0),
                StudentProgress("student_3", "Student Three", 5, success_rate=91.0)
            ]
            
            for student in students:
                db.store_student_progress(student)
            
            # Retrieve all students
            all_students = db.get_all_students_progress()
            assert len(all_students) == 3
            
            student_ids = [s.student_id for s in all_students]
            assert "student_1" in student_ids
            assert "student_2" in student_ids
            assert "student_3" in student_ids


class TestWeeklyReportGenerator:
    """Test WeeklyReportGenerator class"""
    
    def test_weekly_report_generator_initialization(self):
        """Test report generator initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            generator = WeeklyReportGenerator(db)
            
            assert generator.database == db
    
    def test_generate_student_weekly_report(self):
        """Test student weekly report generation"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            generator = WeeklyReportGenerator(db)
            
            # Store test student
            progress = StudentProgress(
                student_id="report_student",
                name="Report Student",
                grade_level=4,
                success_rate=78.5,
                subject_scores={"Math": 82.0, "Science": 75.0},
                mastered_topics=["fractions", "plants"],
                struggling_topics=["geometry"],
                weekly_progress=[70.0, 75.0, 80.0, 78.5],
                daily_activity=[45, 60, 30, 50, 40, 55, 35]
            )
            db.store_student_progress(progress)
            
            # Generate report
            week_start = datetime.now() - timedelta(days=7)
            report = generator.generate_student_weekly_report("report_student", week_start)
            
            assert "error" not in report
            assert report["student_id"] == "report_student"
            assert report["student_name"] == "Report Student"
            assert "overall_progress" in report
            assert "weekly_summary" in report
            assert "subject_performance" in report
            assert "recommendations" in report
            
            # Check overall progress data
            overall = report["overall_progress"]
            assert overall["success_rate"] == 78.5
            assert overall["progress_status"] == "good"  # Should be good for 78.5%
    
    def test_generate_teacher_weekly_report(self):
        """Test teacher weekly report generation"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            generator = WeeklyReportGenerator(db)
            
            # Store multiple students
            students = [
                StudentProgress("teacher_student_1", "Student One", 3, success_rate=85.0, 
                              subject_scores={"Math": 88.0, "Science": 82.0}, needs_attention=False),
                StudentProgress("teacher_student_2", "Student Two", 3, success_rate=45.0,
                              subject_scores={"Math": 40.0, "Science": 50.0}, needs_attention=True,
                              progress_status=ProgressStatus.AT_RISK),
                StudentProgress("teacher_student_3", "Student Three", 3, success_rate=92.0,
                              subject_scores={"Math": 95.0, "Science": 89.0}, needs_attention=False,
                              progress_status=ProgressStatus.EXCELLENT)
            ]
            
            for student in students:
                db.store_student_progress(student)
            
            # Create alerts for testing
            alert = Alert("alert_1", "teacher_student_2", AlertLevel.URGENT, "Low Performance", "Urgent alert")
            db.store_alert(alert)
            
            # Mock teacher with managed students (this would normally be in dashboard_users table)
            with patch.object(db, 'get_all_students_progress', return_value=students):
                report = generator.generate_teacher_weekly_report("teacher_123")
            
            assert "error" not in report
            assert report["teacher_id"] == "teacher_123"
            assert "class_overview" in report
            assert "urgent_attention_required" in report
            assert "subject_performance" in report
            assert "recommendations" in report
            
            # Check class overview
            class_overview = report["class_overview"]
            assert class_overview["total_students"] == 3
            assert class_overview["students_needing_attention"] == 1
            
            # Check urgent students
            urgent_students = report["urgent_attention_required"]
            assert len(urgent_students) >= 1
            urgent_student = urgent_students[0]
            assert urgent_student["student_id"] == "teacher_student_2"  # At-risk student should be first
    
    def test_report_error_handling(self):
        """Test report error handling for non-existent entities"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db = DashboardDatabase(temp_db.name)
            generator = WeeklyReportGenerator(db)
            
            # Test non-existent student
            report = generator.generate_student_weekly_report("non_existent_student")
            assert "error" in report
            assert "Student not found" in report["error"]
            
            # Test teacher with no students
            teacher_report = generator.generate_teacher_weekly_report("empty_teacher")
            assert "error" in teacher_report
            assert "No students found" in teacher_report["error"]


class TestParentTeacherDashboard:
    """Test main ParentTeacherDashboard class"""
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            assert dashboard.database is not None
            assert dashboard.progress_analyzer is not None
            assert dashboard.report_generator is not None
            assert hasattr(dashboard, 'email_config')
    
    def test_update_student_progress(self):
        """Test updating student progress from learning data"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Create sample progress entries
            progress_entries = [
                ProgressEntry(
                    student_id="dashboard_student",
                    lesson_id="lesson_001",
                    timestamp=datetime.now() - timedelta(days=1),
                    interaction_type="lesson_completed",
                    data={"success": True, "score": 85, "time_spent_seconds": 1200, "subject": "math"}
                ),
                ProgressEntry(
                    student_id="dashboard_student",
                    lesson_id="lesson_002",
                    timestamp=datetime.now(),
                    interaction_type="quiz_completed",
                    data={"success": False, "score": 45, "time_spent_seconds": 800, "subject": "science"}
                )
            ]
            
            # Create accessibility profile
            accessibility_profile = AccessibilityProfile(user_id="dashboard_student")
            accessibility_profile.add_impairment(ImpairmentType.COGNITIVE, "adhd", SeverityLevel.MILD)
            
            # Update progress
            success = dashboard.update_student_progress("dashboard_student", progress_entries, accessibility_profile)
            assert success is True
            
            # Verify progress was stored
            progress = dashboard.database.get_student_progress("dashboard_student")
            assert progress is not None
            assert progress.student_id == "dashboard_student"
            assert len(progress.accessibility_accommodations_active) > 0
            
            # Check that alerts were generated (low success rate should trigger alert)
            alerts = dashboard.database.get_active_alerts("dashboard_student")
            assert len(alerts) > 0  # Should have generated alerts for poor performance
    
    def test_get_student_dashboard(self):
        """Test getting comprehensive student dashboard"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Store test student progress
            progress = StudentProgress(
                student_id="dashboard_view_student",
                name="Dashboard View Student",
                grade_level=4,
                success_rate=78.5,
                total_lessons_completed=12,
                subject_scores={"Math": 82.0, "Science": 75.0},
                mastered_topics=["fractions", "plants"],
                struggling_topics=["geometry"],
                accessibility_accommodations_active=["simplified_language"]
            )
            dashboard.database.store_student_progress(progress)
            
            # Create IEP goal
            iep_goal = IEPGoal(
                goal_id="dashboard_iep_goal",
                student_id="dashboard_view_student",
                title="Improve Math Skills",
                description="Focus on geometry",
                target_date=datetime.now() + timedelta(days=90),
                measurable_objective="80% accuracy on geometry problems",
                current_level=45.0
            )
            dashboard.database.store_iep_goal(iep_goal)
            
            # Create alert
            alert = Alert(
                alert_id="dashboard_alert",
                student_id="dashboard_view_student",
                alert_level=AlertLevel.WARNING,
                title="Struggling with Geometry",
                description="Student needs extra help",
                category="academic"
            )
            dashboard.database.store_alert(alert)
            
            # Get dashboard
            student_dashboard = dashboard.get_student_dashboard("dashboard_view_student")
            
            assert "error" not in student_dashboard
            assert student_dashboard["student_info"]["student_id"] == "dashboard_view_student"
            assert "academic_performance" in student_dashboard
            assert "engagement_metrics" in student_dashboard
            assert "accessibility_status" in student_dashboard
            assert len(student_dashboard["iep_goals"]) == 1
            assert len(student_dashboard["active_alerts"]) == 1
            
            # Check accessibility status
            accessibility = student_dashboard["accessibility_status"]
            assert "simplified_language" in accessibility["active_accommodations"]
    
    def test_get_teacher_dashboard(self):
        """Test getting teacher dashboard overview"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Store multiple students
            students = [
                StudentProgress("teacher_dash_1", "Student One", 3, success_rate=85.0, needs_attention=False),
                StudentProgress("teacher_dash_2", "Student Two", 3, success_rate=45.0, needs_attention=True,
                              progress_status=ProgressStatus.AT_RISK, alert_reasons=["Low performance"]),
                StudentProgress("teacher_dash_3", "Student Three", 3, success_rate=92.0, needs_attention=False,
                              progress_status=ProgressStatus.EXCELLENT)
            ]
            
            for student in students:
                dashboard.database.store_student_progress(student)
            
            # Create urgent alert
            urgent_alert = Alert("urgent_1", "teacher_dash_2", AlertLevel.CRITICAL, "Critical Issue", "Urgent attention needed")
            dashboard.database.store_alert(urgent_alert)
            
            # Mock teacher-student relationship
            with patch.object(dashboard.database, 'get_all_students_progress', return_value=students):
                teacher_dashboard = dashboard.get_teacher_dashboard("teacher_123")
            
            assert "error" not in teacher_dashboard
            assert teacher_dashboard["teacher_id"] == "teacher_123"
            
            # Check class summary
            class_summary = teacher_dashboard["class_summary"]
            assert class_summary["total_students"] == 3
            assert class_summary["students_needing_attention"] == 1
            
            # Check alert summary
            alert_summary = teacher_dashboard["alert_summary"]
            assert alert_summary["critical"] >= 1  # Should have the critical alert
            
            # Check student distribution
            distribution = teacher_dashboard["student_distribution"]
            assert distribution["excellent"] == 1
            assert distribution["at_risk"] == 1
    
    def test_create_iep_goal(self):
        """Test creating IEP goals"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            target_date = datetime.now() + timedelta(days=120)
            goal_id = dashboard.create_iep_goal(
                "iep_test_student",
                "Improve Reading Fluency",
                "Student will improve reading speed and comprehension",
                target_date,
                "Read 100 words per minute with 90% comprehension"
            )
            
            assert goal_id != ""
            assert "iep_" in goal_id
            
            # Verify goal was stored
            goals = dashboard.database.get_student_iep_goals("iep_test_student")
            assert len(goals) == 1
            assert goals[0].title == "Improve Reading Fluency"
    
    def test_generate_weekly_report_integration(self):
        """Test weekly report generation integration"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Store test student with comprehensive data
            progress = StudentProgress(
                student_id="weekly_report_student",
                name="Weekly Report Student",
                grade_level=4,
                success_rate=75.0,
                total_lessons_completed=8,
                subject_scores={"Math": 78.0, "Science": 72.0},
                mastered_topics=["addition", "subtraction"],
                struggling_topics=["division"],
                weekly_progress=[68.0, 70.0, 73.0, 75.0],
                daily_activity=[30, 45, 35, 50, 40, 55, 25]
            )
            dashboard.database.store_student_progress(progress)
            
            # Generate student report
            student_report = dashboard.generate_weekly_report("weekly_report_student", "student")
            
            assert "error" not in student_report
            assert student_report["student_id"] == "weekly_report_student"
            assert "overall_progress" in student_report
            assert "weekly_summary" in student_report
            assert "recommendations" in student_report
            
            # Check that recommendations were generated
            recommendations = student_report["recommendations"]
            assert len(recommendations) > 0
            assert any("division" in rec.lower() for rec in recommendations)  # Should mention struggling topic
    
    def test_dashboard_error_handling(self):
        """Test dashboard error handling"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Test non-existent student dashboard
            result = dashboard.get_student_dashboard("non_existent_student")
            assert "error" in result
            assert "Student not found" in result["error"]
            
            # Test non-existent teacher dashboard
            teacher_result = dashboard.get_teacher_dashboard("non_existent_teacher")
            assert "error" in teacher_result
            assert "No students found" in teacher_result["error"]
            
            # Test invalid report type
            invalid_report = dashboard.generate_weekly_report("test_id", "invalid_type")
            assert "error" in invalid_report
            assert "Invalid target type" in invalid_report["error"]
    
    @patch('parent_teacher_dashboard.smtplib.SMTP')
    def test_send_alert_notification(self, mock_smtp):
        """Test sending alert notifications via email"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Configure email
            dashboard.email_config.update({
                "username": "test@example.com",
                "password": "testpass",
                "from_address": "eduagi@example.com"
            })
            
            # Mock SMTP server
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            # Create test alert
            alert = Alert(
                alert_id="email_test",
                student_id="email_student",
                alert_level=AlertLevel.URGENT,
                title="Urgent: Student Needs Help",
                description="Student has been struggling",
                suggested_actions=["Contact parent", "Schedule tutoring"]
            )
            
            # Send notification
            success = dashboard.send_alert_notification(alert, "parent@example.com")
            
            assert success is True
            
            # Verify SMTP was called
            mock_smtp.assert_called_once()
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()


class TestIntegration:
    """Integration tests for the dashboard system"""
    
    def test_full_dashboard_workflow(self):
        """Test complete dashboard workflow from progress to reports"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            dashboard = ParentTeacherDashboard(temp_db.name)
            
            # Step 1: Update student progress with learning data
            progress_entries = [
                ProgressEntry("integration_student", "lesson_1", datetime.now() - timedelta(days=7),
                             "completed", {"success": True, "score": 90, "subject": "math", "time_spent_seconds": 1800}),
                ProgressEntry("integration_student", "lesson_2", datetime.now() - timedelta(days=6),
                             "completed", {"success": True, "score": 85, "subject": "science", "time_spent_seconds": 1500}),
                ProgressEntry("integration_student", "lesson_3", datetime.now() - timedelta(days=5),
                             "completed", {"success": False, "score": 45, "subject": "math", "time_spent_seconds": 1200}),
                ProgressEntry("integration_student", "lesson_4", datetime.now() - timedelta(days=4),
                             "completed", {"success": True, "score": 88, "subject": "science", "time_spent_seconds": 1600}),
                ProgressEntry("integration_student", "lesson_5", datetime.now() - timedelta(days=3),
                             "completed", {"success": True, "score": 92, "subject": "math", "time_spent_seconds": 1700})
            ]
            
            accessibility_profile = AccessibilityProfile(user_id="integration_student")
            accessibility_profile.add_impairment(ImpairmentType.VISUAL, "low_vision", SeverityLevel.MILD)
            
            success = dashboard.update_student_progress("integration_student", progress_entries, accessibility_profile)
            assert success is True
            
            # Step 2: Create IEP goals
            iep_goal_id = dashboard.create_iep_goal(
                "integration_student",
                "Improve Math Problem Solving",
                "Focus on multi-step problems",
                datetime.now() + timedelta(days=90),
                "Achieve 85% accuracy on multi-step problems"
            )
            assert iep_goal_id != ""
            
            # Step 3: Update IEP goal progress
            dashboard.update_iep_goal_progress(iep_goal_id, 35.0, "Student showing gradual improvement")
            
            # Step 4: Get comprehensive student dashboard
            student_dashboard = dashboard.get_student_dashboard("integration_student")
            assert "error" not in student_dashboard
            assert student_dashboard["student_info"]["student_id"] == "integration_student"
            assert student_dashboard["academic_performance"]["success_rate"] == 80.0  # 4/5 success
            assert len(student_dashboard["iep_goals"]) == 1
            assert len(student_dashboard["accessibility_status"]["active_accommodations"]) > 0
            
            # Step 5: Generate weekly report
            weekly_report = dashboard.generate_weekly_report("integration_student", "student")
            assert "error" not in weekly_report
            assert weekly_report["student_id"] == "integration_student"
            assert "overall_progress" in weekly_report
            assert "iep_goals_progress" in weekly_report
            assert len(weekly_report["iep_goals_progress"]) == 1
            
            # Step 6: Check alerts were generated appropriately
            alerts = dashboard.database.get_active_alerts("integration_student")
            # With 80% success rate, should not have low performance alerts, but might have others
            
            # Verify the system works end-to-end
            assert student_dashboard["academic_performance"]["lessons_completed"] == 5
            assert "math" in student_dashboard["academic_performance"]["subject_scores"]
            assert "science" in student_dashboard["academic_performance"]["subject_scores"]


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])