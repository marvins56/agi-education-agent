"""
Comprehensive tests for the EduAGI Analytics Package
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.analytics.student_analytics import (
    StudentAnalytics, StudySession, TopicMastery, 
    LearningStyle, DifficultyLevel
)
from src.analytics.class_analytics import (
    ClassAnalytics, TeachingApproach, RiskLevel, AtRiskStudent
)
from src.analytics.reporting import (
    ReportGenerator, ReportType, ExportFormat, Language, ScheduledReport
)
from src.analytics.insights import (
    InsightsEngine, Insight, InsightType, Priority, TrendDirection
)


class TestStudentAnalytics:
    """Test cases for StudentAnalytics class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.student_analytics = StudentAnalytics("student_001")
        self.sample_sessions = [
            StudySession(
                session_id="session_1",
                student_id="student_001",
                subject="Math",
                topic="Algebra",
                start_time=datetime.now() - timedelta(days=1),
                duration_minutes=30.0,
                completion_rate=0.9,
                score=85.0,
                difficulty_level=DifficultyLevel.INTERMEDIATE
            ),
            StudySession(
                session_id="session_2",
                student_id="student_001",
                subject="Math",
                topic="Geometry",
                start_time=datetime.now() - timedelta(days=2),
                duration_minutes=25.0,
                completion_rate=0.8,
                score=78.0,
                difficulty_level=DifficultyLevel.BEGINNER
            ),
            StudySession(
                session_id="session_3",
                student_id="student_001",
                subject="Science",
                topic="Physics",
                start_time=datetime.now() - timedelta(hours=2),
                duration_minutes=45.0,
                completion_rate=0.95,
                score=92.0,
                difficulty_level=DifficultyLevel.ADVANCED
            )
        ]
        
        for session in self.sample_sessions:
            self.student_analytics.add_session(session)
    
    def test_student_analytics_initialization(self):
        """Test StudentAnalytics initialization"""
        analytics = StudentAnalytics("test_student")
        assert analytics.student_id == "test_student"
        assert len(analytics.sessions) == 0
        assert len(analytics.masteries) == 0
    
    def test_add_session(self):
        """Test adding study sessions"""
        assert len(self.student_analytics.sessions) == 3
        
        # Test adding session with wrong student_id
        wrong_session = StudySession(
            session_id="wrong_session",
            student_id="wrong_student",
            subject="Math",
            topic="Test",
            start_time=datetime.now(),
            duration_minutes=20.0,
            completion_rate=0.8
        )
        
        with pytest.raises(ValueError):
            self.student_analytics.add_session(wrong_session)
    
    def test_learning_velocity_calculation(self):
        """Test learning velocity calculation"""
        # Add some topic masteries
        mastery1 = TopicMastery(
            topic="Algebra",
            subject="Math",
            mastery_level=1.0,
            first_attempt_date=datetime.now() - timedelta(weeks=2),
            mastery_achieved_date=datetime.now() - timedelta(days=3)
        )
        mastery2 = TopicMastery(
            topic="Geometry",
            subject="Math", 
            mastery_level=1.0,
            first_attempt_date=datetime.now() - timedelta(weeks=3),
            mastery_achieved_date=datetime.now() - timedelta(days=1)
        )
        
        self.student_analytics.add_topic_mastery(mastery1)
        self.student_analytics.add_topic_mastery(mastery2)
        
        velocity = self.student_analytics.get_learning_velocity(weeks=4)
        assert "Math" in velocity
        assert velocity["Math"] == 2.0 / 4  # 2 topics mastered in 4 weeks
    
    def test_retention_rate_calculation(self):
        """Test retention rate calculation"""
        retention = self.student_analytics.get_retention_rate()
        assert "Math" in retention
        assert "Science" in retention
        
        # Math average: (85 + 78) / 2 = 81.5, normalized to 0.815
        assert abs(retention["Math"] - 0.815) < 0.01
        assert abs(retention["Science"] - 0.92) < 0.01
    
    def test_time_on_task_analysis(self):
        """Test time-on-task analysis"""
        time_analysis = self.student_analytics.get_time_on_task_analysis()
        
        assert "by_subject" in time_analysis
        assert "by_lesson" in time_analysis
        
        # Math has 2 sessions: 30 and 25 minutes
        math_avg = time_analysis["by_subject"]["Math"]["avg_minutes"]
        assert abs(math_avg - 27.5) < 0.1
        
        # Science has 1 session: 45 minutes
        science_avg = time_analysis["by_subject"]["Science"]["avg_minutes"]
        assert abs(science_avg - 45.0) < 0.1
    
    def test_engagement_score_calculation(self):
        """Test engagement score calculation"""
        engagement = self.student_analytics.calculate_engagement_score()
        
        assert "overall" in engagement
        assert "frequency" in engagement
        assert "duration" in engagement
        assert "completion" in engagement
        
        # All scores should be between 0 and 1
        for key, value in engagement.items():
            assert 0 <= value <= 1
    
    def test_optimal_study_time_detection(self):
        """Test optimal study time detection"""
        optimal_time = self.student_analytics.detect_optimal_study_time()
        
        assert "optimal_period" in optimal_time
        assert "recommendation" in optimal_time
    
    def test_learning_style_inference(self):
        """Test learning style inference"""
        style_info = self.student_analytics.infer_learning_style()
        
        assert "style" in style_info
        assert "confidence" in style_info
        assert "scores" in style_info
        assert 0 <= style_info["confidence"] <= 1
    
    def test_comprehensive_report(self):
        """Test comprehensive report generation"""
        report = self.student_analytics.get_comprehensive_report()
        
        required_keys = [
            "student_id", "generated_at", "learning_velocity", 
            "retention_rate", "time_on_task", "engagement_score",
            "learning_style", "total_sessions"
        ]
        
        for key in required_keys:
            assert key in report
        
        assert report["student_id"] == "student_001"
        assert report["total_sessions"] == 3


class TestClassAnalytics:
    """Test cases for ClassAnalytics class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.class_analytics = ClassAnalytics("class_001", "teacher_001")
        
        # Create sample student analytics
        self.student1 = StudentAnalytics("student_001")
        self.student2 = StudentAnalytics("student_002")
        
        # Add sample sessions to students
        sessions_student1 = [
            StudySession("s1", "student_001", "Math", "Algebra", 
                        datetime.now() - timedelta(days=1), 30, 0.9, 85.0),
            StudySession("s2", "student_001", "Math", "Geometry",
                        datetime.now() - timedelta(days=2), 25, 0.7, 65.0)
        ]
        
        sessions_student2 = [
            StudySession("s3", "student_002", "Math", "Algebra",
                        datetime.now() - timedelta(days=1), 35, 0.8, 75.0),
            StudySession("s4", "student_002", "Math", "Geometry", 
                        datetime.now() - timedelta(days=2), 40, 0.6, 55.0)
        ]
        
        for session in sessions_student1:
            self.student1.add_session(session)
        for session in sessions_student2:
            self.student2.add_session(session)
            
        self.class_analytics.add_student(self.student1)
        self.class_analytics.add_student(self.student2)
    
    def test_class_analytics_initialization(self):
        """Test ClassAnalytics initialization"""
        analytics = ClassAnalytics("test_class", "test_teacher")
        assert analytics.class_id == "test_class"
        assert analytics.teacher_id == "test_teacher"
        assert len(analytics.student_analytics) == 0
    
    def test_add_student(self):
        """Test adding student analytics"""
        assert len(self.class_analytics.student_analytics) == 2
        assert "student_001" in self.class_analytics.student_analytics
        assert "student_002" in self.class_analytics.student_analytics
    
    def test_performance_heatmap(self):
        """Test performance heatmap generation"""
        heatmap = self.class_analytics.get_performance_heatmap()
        
        assert "Math" in heatmap
        assert "Algebra" in heatmap["Math"]
        assert "Geometry" in heatmap["Math"]
        
        algebra_metric = heatmap["Math"]["Algebra"]
        assert algebra_metric.subject == "Math"
        assert algebra_metric.topic == "Algebra"
        assert algebra_metric.student_count == 2
        # Average of 85 and 75 = 80
        assert abs(algebra_metric.avg_score - 80.0) < 0.1
    
    def test_at_risk_identification(self):
        """Test at-risk student identification"""
        at_risk = self.class_analytics.identify_at_risk_students()
        
        # Should be a list of AtRiskStudent objects
        assert isinstance(at_risk, list)
        
        if at_risk:  # If any students are identified as at-risk
            for student in at_risk:
                assert isinstance(student, AtRiskStudent)
                assert hasattr(student, 'student_id')
                assert hasattr(student, 'risk_level')
                assert isinstance(student.risk_level, RiskLevel)
    
    def test_teacher_effectiveness(self):
        """Test teacher effectiveness analysis"""
        effectiveness = self.class_analytics.analyze_teacher_effectiveness()
        
        assert isinstance(effectiveness, dict)
        # Should have various effectiveness metrics
        if "student_engagement" in effectiveness:
            assert 0 <= effectiveness["student_engagement"] <= 1
    
    def test_resource_utilization(self):
        """Test resource utilization analysis"""
        utilization = self.class_analytics.analyze_resource_utilization()
        
        assert "most_used_content" in utilization
        assert "interaction_effectiveness" in utilization
        assert isinstance(utilization, dict)
    
    def test_comprehensive_class_report(self):
        """Test comprehensive class report generation"""
        report = self.class_analytics.get_comprehensive_class_report()
        
        required_keys = [
            "class_id", "teacher_id", "generated_at", 
            "total_students", "performance_heatmap"
        ]
        
        for key in required_keys:
            assert key in report
        
        assert report["class_id"] == "class_001"
        assert report["teacher_id"] == "teacher_001"
        assert report["total_students"] == 2


class TestReportGenerator:
    """Test cases for ReportGenerator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.report_generator = ReportGenerator()
        
        # Create sample student analytics
        self.student_analytics = StudentAnalytics("student_001")
        sample_session = StudySession(
            "session_1", "student_001", "Math", "Algebra",
            datetime.now(), 30, 0.9, 85.0
        )
        self.student_analytics.add_session(sample_session)
    
    def test_report_generator_initialization(self):
        """Test ReportGenerator initialization"""
        generator = ReportGenerator()
        assert len(generator.templates) > 0
        assert len(generator.scheduled_reports) == 0
    
    def test_student_progress_report(self):
        """Test student progress report generation"""
        report = self.report_generator.generate_student_progress_report(
            self.student_analytics, Language.ENGLISH, ExportFormat.JSON
        )
        
        assert "report_info" in report
        assert "summary" in report
        assert "performance" in report
        assert "learning_style" in report
        assert "recommendations" in report
        
        assert report["report_info"]["type"] == "student_progress"
        assert report["report_info"]["student_id"] == "student_001"
        assert report["report_info"]["language"] == "en"
    
    def test_parent_summary_report(self):
        """Test parent summary report generation"""
        report = self.report_generator.generate_parent_summary_report(
            self.student_analytics, Language.ENGLISH, ExportFormat.JSON
        )
        
        assert "report_info" in report
        assert "overview" in report
        assert "strengths" in report
        assert "areas_for_growth" in report
        assert "home_support" in report
        assert "visual_summary" in report
        
        assert report["report_info"]["type"] == "parent_summary"
    
    def test_multilingual_support(self):
        """Test multilingual report generation"""
        # Test Swahili report
        report_sw = self.report_generator.generate_student_progress_report(
            self.student_analytics, Language.SWAHILI, ExportFormat.JSON
        )
        
        assert report_sw["report_info"]["language"] == "sw"
        assert "Ripoti ya Maendeleo ya Mwanafunzi" in report_sw["report_info"]["title"]
        
        # Test English report
        report_en = self.report_generator.generate_student_progress_report(
            self.student_analytics, Language.ENGLISH, ExportFormat.JSON
        )
        
        assert report_en["report_info"]["language"] == "en"
        assert "Student Progress Report" in report_en["report_info"]["title"]
    
    def test_csv_export_format(self):
        """Test CSV export format"""
        report = self.report_generator.generate_student_progress_report(
            self.student_analytics, Language.ENGLISH, ExportFormat.CSV
        )
        
        assert report["format"] == "csv"
        assert "data" in report
        assert "filename" in report
        assert isinstance(report["data"], str)
    
    def test_pdf_data_format(self):
        """Test PDF data format"""
        report = self.report_generator.generate_student_progress_report(
            self.student_analytics, Language.ENGLISH, ExportFormat.PDF_DATA
        )
        
        assert report["format"] == "pdf_data"
        assert "title" in report
        assert "sections" in report
        assert "charts_data" in report
    
    def test_scheduled_reports(self):
        """Test scheduled report functionality"""
        scheduled_report = ScheduledReport(
            report_id="weekly_001",
            report_type=ReportType.STUDENT_PROGRESS,
            target_ids=["student_001"],
            schedule="weekly",
            format=ExportFormat.JSON,
            language=Language.ENGLISH,
            recipients=["parent@example.com"],
            next_run=datetime.now() - timedelta(hours=1)  # Past due
        )
        
        self.report_generator.add_scheduled_report(scheduled_report)
        
        due_reports = self.report_generator.get_due_reports()
        assert len(due_reports) == 1
        assert due_reports[0].report_id == "weekly_001"
        
        # Test updating next run time
        self.report_generator.update_next_run("weekly_001")
        updated_reports = self.report_generator.get_due_reports()
        assert len(updated_reports) == 0  # Should no longer be due


class TestInsightsEngine:
    """Test cases for InsightsEngine class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.insights_engine = InsightsEngine()
        
        # Create sample student analytics with varied performance
        self.student_analytics = StudentAnalytics("student_001")
        
        # Add sessions showing declining performance in Math
        declining_sessions = [
            StudySession("s1", "student_001", "Math", "Algebra",
                        datetime.now() - timedelta(days=10), 30, 0.9, 90.0),
            StudySession("s2", "student_001", "Math", "Algebra", 
                        datetime.now() - timedelta(days=9), 30, 0.8, 85.0),
            StudySession("s3", "student_001", "Math", "Algebra",
                        datetime.now() - timedelta(days=8), 30, 0.7, 75.0),
            StudySession("s4", "student_001", "Math", "Algebra",
                        datetime.now() - timedelta(days=7), 30, 0.6, 70.0),
            StudySession("s5", "student_001", "Math", "Algebra",
                        datetime.now() - timedelta(days=6), 30, 0.5, 60.0)
        ]
        
        for session in declining_sessions:
            self.student_analytics.add_session(session)
    
    def test_insights_engine_initialization(self):
        """Test InsightsEngine initialization"""
        engine = InsightsEngine()
        assert len(engine.pattern_library) > 0
        assert len(engine.insights_cache) == 0
    
    def test_student_insights_analysis(self):
        """Test student insights analysis"""
        insights = self.insights_engine.analyze_student_insights(self.student_analytics)
        
        assert isinstance(insights, list)
        
        # Should generate some insights
        if insights:
            for insight in insights:
                assert isinstance(insight, Insight)
                assert hasattr(insight, 'insight_id')
                assert hasattr(insight, 'type')
                assert isinstance(insight.type, InsightType)
                assert hasattr(insight, 'priority')
                assert isinstance(insight.priority, Priority)
                assert hasattr(insight, 'title')
                assert hasattr(insight, 'description')
                assert isinstance(insight.recommendations, list)
                assert 0 <= insight.confidence <= 1
    
    def test_class_insights_analysis(self):
        """Test class insights analysis"""
        # Create class analytics with sample data
        class_analytics = ClassAnalytics("class_001", "teacher_001")
        class_analytics.add_student(self.student_analytics)
        
        insights = self.insights_engine.analyze_class_insights(class_analytics)
        
        assert isinstance(insights, list)
        
        # Should cache results
        assert "class_001" in self.insights_engine.insights_cache
    
    def test_insight_filtering(self):
        """Test insight filtering by priority"""
        insights = self.insights_engine.analyze_student_insights(self.student_analytics)
        
        if insights:
            # Test filtering by priority
            high_priority = self.insights_engine.get_insights_by_priority(Priority.HIGH)
            
            for insight in high_priority:
                assert insight.priority == Priority.HIGH
    
    def test_active_insights(self):
        """Test active insights retrieval"""
        insights = self.insights_engine.analyze_student_insights(self.student_analytics)
        
        active_insights = self.insights_engine.get_active_insights()
        assert isinstance(active_insights, list)
        
        # All insights should be active (not expired)
        now = datetime.now()
        for insight in active_insights:
            if insight.expires_at is not None:
                assert insight.expires_at > now
    
    def test_pattern_detection(self):
        """Test learning pattern detection"""
        # The declining performance should trigger a trend insight
        insights = self.insights_engine.analyze_student_insights(self.student_analytics)
        
        # Look for performance trend insights
        trend_insights = [i for i in insights if i.type == InsightType.PERFORMANCE_TREND]
        
        if trend_insights:
            # Should detect declining trend
            declining_insights = [i for i in trend_insights if "declining" in i.title.lower()]
            assert len(declining_insights) > 0


class TestIntegration:
    """Integration tests for the analytics package"""
    
    def test_full_workflow(self):
        """Test complete workflow from data collection to insights"""
        # 1. Create student analytics with comprehensive data
        student = StudentAnalytics("integration_student")
        
        # Add varied sessions over time
        sessions = []
        for i in range(20):
            session = StudySession(
                session_id=f"session_{i}",
                student_id="integration_student",
                subject="Math" if i % 2 == 0 else "Science",
                topic=f"Topic_{i % 5}",
                start_time=datetime.now() - timedelta(days=i),
                duration_minutes=20 + (i % 30),
                completion_rate=0.7 + (i % 3) * 0.1,
                score=60 + (i % 30),
                difficulty_level=DifficultyLevel(1 + (i % 3))
            )
            sessions.append(session)
            student.add_session(session)
        
        # 2. Create class analytics
        class_analytics = ClassAnalytics("integration_class", "integration_teacher")
        class_analytics.add_student(student)
        
        # 3. Generate reports
        report_generator = ReportGenerator()
        student_report = report_generator.generate_student_progress_report(
            student, Language.ENGLISH, ExportFormat.JSON
        )
        class_report = report_generator.generate_teacher_class_report(
            class_analytics, Language.ENGLISH, ExportFormat.JSON
        )
        
        # 4. Generate insights
        insights_engine = InsightsEngine()
        student_insights = insights_engine.analyze_student_insights(student)
        class_insights = insights_engine.analyze_class_insights(class_analytics)
        
        # Verify everything works together
        assert student_report["report_info"]["student_id"] == "integration_student"
        assert class_report["report_info"]["class_id"] == "integration_class"
        assert len(student_insights) >= 0
        assert len(class_insights) >= 0
        
        # Verify data consistency
        assert student_report["metrics"]["total_sessions"] == 20
        assert class_report["class_overview"]["total_students"] == 1
    
    def test_multilingual_integration(self):
        """Test multilingual support integration"""
        student = StudentAnalytics("multilingual_student")
        session = StudySession(
            "s1", "multilingual_student", "Hisabati", "Algebra",
            datetime.now(), 30, 0.9, 85.0
        )
        student.add_session(session)
        
        report_generator = ReportGenerator()
        
        # Test different languages
        languages = [Language.ENGLISH, Language.SWAHILI]
        
        for language in languages:
            report = report_generator.generate_parent_summary_report(
                student, language, ExportFormat.JSON
            )
            
            assert report["report_info"]["language"] == language.value
            assert len(report["overview"]) > 0
            assert len(report["home_support"]) > 0


# Test fixtures and utilities
@pytest.fixture
def sample_student_data():
    """Fixture providing sample student data for tests"""
    student = StudentAnalytics("fixture_student")
    
    sessions = [
        StudySession("f1", "fixture_student", "Math", "Arithmetic",
                    datetime.now() - timedelta(days=5), 25, 0.8, 80.0),
        StudySession("f2", "fixture_student", "Math", "Fractions",
                    datetime.now() - timedelta(days=4), 30, 0.9, 85.0),
        StudySession("f3", "fixture_student", "Science", "Biology", 
                    datetime.now() - timedelta(days=3), 35, 0.7, 75.0)
    ]
    
    for session in sessions:
        student.add_session(session)
    
    return student


def test_with_fixture(sample_student_data):
    """Test using the sample data fixture"""
    assert len(sample_student_data.sessions) == 3
    assert sample_student_data.student_id == "fixture_student"
    
    engagement = sample_student_data.calculate_engagement_score()
    assert 0 <= engagement["overall"] <= 1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])