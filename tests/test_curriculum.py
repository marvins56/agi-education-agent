"""
Comprehensive test suite for the EduAGI Curriculum System.

Tests all components of the curriculum alignment system including
CurriculumEngine, LessonGenerator, AssessmentGenerator, and ProgressTracker.
"""

import pytest
from datetime import datetime
from typing import Set

from src.curriculum import (
    CurriculumEngine, LessonGenerator, AssessmentGenerator, ProgressTracker
)
from src.curriculum.engine import (
    Subject, Country, DifficultyLevel, Topic, LearningObjective
)
from src.curriculum.lesson_generator import LessonFormat, Lesson
from src.curriculum.assessment_generator import AssessmentType, QuestionType
from src.curriculum.progress_tracker import MasteryLevel, ProgressStatus


class TestCurriculumEngine:
    """Test the CurriculumEngine core functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CurriculumEngine()
    
    def test_initialization(self):
        """Test that curriculum engine initializes correctly."""
        assert self.engine is not None
        assert len(self.engine.topics) > 0
        assert Country.UGANDA in self.engine.grade_levels
        assert Country.KENYA in self.engine.grade_levels
    
    def test_grade_levels_uganda(self):
        """Test Uganda grade level structure."""
        uganda_grades = self.engine.grade_levels[Country.UGANDA]
        
        # Test Primary levels (1-7)
        for grade in range(1, 8):
            assert grade in uganda_grades
            grade_info = uganda_grades[grade]
            assert grade_info.display_name == f"Primary {grade}"
            assert grade_info.cycle == "primary"
        
        # Test Secondary levels (8-13 for Senior 1-6)
        for grade in range(8, 14):
            assert grade in uganda_grades
            grade_info = uganda_grades[grade]
            senior_level = grade - 7
            assert grade_info.display_name == f"Senior {senior_level}"
            assert grade_info.cycle == "secondary"
    
    def test_grade_levels_kenya(self):
        """Test Kenya grade level structure."""
        kenya_grades = self.engine.grade_levels[Country.KENYA]
        
        # Test Standard levels (1-8)
        for grade in range(1, 9):
            assert grade in kenya_grades
            grade_info = kenya_grades[grade]
            assert grade_info.display_name == f"Standard {grade}"
            assert grade_info.cycle == "primary"
        
        # Test Form levels (9-12 for Form 1-4)
        for grade in range(9, 13):
            assert grade in kenya_grades
            grade_info = kenya_grades[grade]
            form_level = grade - 8
            assert grade_info.display_name == f"Form {form_level}"
            assert grade_info.cycle == "secondary"
    
    def test_subjects_coverage(self):
        """Test that all subjects are covered in curriculum."""
        expected_subjects = {Subject.MATHEMATICS, Subject.SCIENCE, Subject.ENGLISH, 
                           Subject.HISTORY, Subject.GEOGRAPHY, Subject.ICT}
        
        # Check that all subjects have curriculum content
        for subject in expected_subjects:
            assert subject in self.engine.subject_trees
            for country in [Country.UGANDA, Country.KENYA]:
                assert country in self.engine.subject_trees[subject]
                # Each subject should have content for multiple grade levels
                assert len(self.engine.subject_trees[subject][country]) > 0
    
    def test_topic_structure(self):
        """Test topic structure and content."""
        # Get a sample topic
        topic_id = list(self.engine.topics.keys())[0]
        topic = self.engine.topics[topic_id]
        
        assert isinstance(topic, Topic)
        assert topic.id == topic_id
        assert topic.name is not None
        assert topic.description is not None
        assert isinstance(topic.subject, Subject)
        assert isinstance(topic.country, Country)
        assert topic.grade_level > 0
        assert len(topic.learning_objectives) > 0
    
    def test_learning_objectives(self):
        """Test learning objectives structure."""
        topic = list(self.engine.topics.values())[0]
        
        for objective in topic.learning_objectives:
            assert isinstance(objective, LearningObjective)
            assert objective.id is not None
            assert objective.description is not None
            assert isinstance(objective.difficulty, DifficultyLevel)
            assert objective.estimated_hours > 0
    
    def test_get_topics_for_grade(self):
        """Test retrieving topics by grade, subject, and country."""
        topics = self.engine.get_topics_for_grade(Subject.MATHEMATICS, 1, Country.UGANDA)
        
        assert len(topics) >= 10  # Should have 10+ topics per grade
        for topic in topics:
            assert topic.subject == Subject.MATHEMATICS
            assert topic.grade_level == 1
            assert topic.country == Country.UGANDA
    
    def test_prerequisite_validation(self):
        """Test prerequisite checking functionality."""
        # Get a topic with prerequisites
        topics_with_prereqs = [t for t in self.engine.topics.values() if len(t.prerequisites) > 0]
        
        if topics_with_prereqs:
            topic = topics_with_prereqs[0]
            
            # Test with no completed topics
            is_valid, missing = self.engine.validate_prerequisites(topic.id, set())
            assert not is_valid
            assert len(missing) > 0
            
            # Test with all prerequisites completed
            is_valid, missing = self.engine.validate_prerequisites(topic.id, topic.prerequisites)
            assert is_valid
            assert len(missing) == 0
    
    def test_learning_pathway(self):
        """Test learning pathway generation."""
        pathway = self.engine.get_learning_pathway(Subject.MATHEMATICS, 1, 3, Country.UGANDA)
        
        assert len(pathway) > 0
        
        # Verify pathway is ordered by grade level
        current_grade = 0
        for topic in pathway:
            assert topic.grade_level >= current_grade
            current_grade = topic.grade_level
    
    def test_curriculum_summary(self):
        """Test curriculum coverage summary."""
        summary = self.engine.get_curriculum_summary(Country.UGANDA)
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        
        # Check that all subjects are represented
        for subject in Subject:
            assert subject.value in summary
            subject_summary = summary[subject.value]
            assert isinstance(subject_summary, dict)
            assert len(subject_summary) > 0


class TestLessonGenerator:
    """Test the LessonGenerator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CurriculumEngine()
        self.generator = LessonGenerator()
        self.sample_topic = list(self.engine.topics.values())[0]
    
    def test_basic_lesson_generation(self):
        """Test basic lesson generation."""
        lesson = self.generator.generate_lesson(self.sample_topic)
        
        assert isinstance(lesson, Lesson)
        assert lesson.title is not None
        assert lesson.topic_id == self.sample_topic.id
        assert lesson.subject == self.sample_topic.subject
        assert lesson.grade_level == self.sample_topic.grade_level
    
    def test_lesson_structure(self):
        """Test that lessons have all required sections."""
        lesson = self.generator.generate_lesson(self.sample_topic)
        
        # Check all sections exist and have content
        assert len(lesson.introduction.activities) > 0
        assert len(lesson.explanation.activities) > 0
        assert len(lesson.examples.activities) > 0
        assert len(lesson.practice.activities) > 0
        assert len(lesson.summary.activities) > 0
    
    def test_lesson_duration(self):
        """Test lesson duration calculation."""
        lesson = self.generator.generate_lesson(self.sample_topic, duration_target=30)
        
        assert lesson.duration_minutes > 0
        # Should be close to target duration (within 50% variance)
        assert 15 <= lesson.duration_minutes <= 60
    
    def test_voice_friendly_format(self):
        """Test voice-friendly lesson format."""
        lesson = self.generator.generate_lesson(
            self.sample_topic, 
            format=LessonFormat.VOICE_FRIENDLY
        )
        
        assert lesson.format == LessonFormat.VOICE_FRIENDLY
        assert len(lesson.voice_prompts) > 0
        assert len(lesson.interaction_cues) > 0
    
    def test_accessibility_features(self):
        """Test accessibility adaptations."""
        lesson = self.generator.generate_lesson(
            self.sample_topic,
            format=LessonFormat.ACCESSIBILITY
        )
        
        assert len(lesson.accessibility_adaptations) > 0
        assert "visual_impairment" in lesson.accessibility_adaptations
        assert "hearing_impairment" in lesson.accessibility_adaptations
    
    def test_difficulty_variants(self):
        """Test difficulty variant generation."""
        lesson = self.generator.generate_lesson(self.sample_topic)
        
        assert len(lesson.difficulty_variants) > 0
        for difficulty, content in lesson.difficulty_variants.items():
            assert isinstance(difficulty, DifficultyLevel)
            assert isinstance(content, str)
            assert len(content) > 0
    
    def test_materials_list(self):
        """Test materials list generation."""
        lesson = self.generator.generate_lesson(self.sample_topic)
        
        materials = lesson.get_all_materials()
        assert isinstance(materials, list)
        assert len(materials) > 0


class TestAssessmentGenerator:
    """Test the AssessmentGenerator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CurriculumEngine()
        self.generator = AssessmentGenerator()
        self.sample_topic = list(self.engine.topics.values())[0]
    
    def test_basic_assessment_generation(self):
        """Test basic assessment generation."""
        assessment = self.generator.generate_assessment(self.sample_topic)
        
        assert assessment.title is not None
        assert assessment.topic_id == self.sample_topic.id
        assert assessment.subject == self.sample_topic.subject
        assert len(assessment.sections) > 0
    
    def test_quiz_generation(self):
        """Test quiz-type assessment generation."""
        assessment = self.generator.generate_assessment(
            self.sample_topic,
            assessment_type=AssessmentType.QUIZ,
            question_count=5
        )
        
        assert assessment.assessment_type == AssessmentType.QUIZ
        total_questions = sum(len(section.questions) for section in assessment.sections)
        assert total_questions == 5
    
    def test_question_types(self):
        """Test different question type generation."""
        assessment = self.generator.generate_assessment(
            self.sample_topic,
            question_count=10
        )
        
        question_types_found = set()
        for section in assessment.sections:
            for question in section.questions:
                question_types_found.add(question.type)
        
        # Should have multiple question types
        assert len(question_types_found) >= 2
    
    def test_multiple_choice_questions(self):
        """Test multiple choice question structure."""
        assessment = self.generator.generate_assessment(self.sample_topic)
        
        mcq_questions = []
        for section in assessment.sections:
            mcq_questions.extend([q for q in section.questions if q.type == QuestionType.MULTIPLE_CHOICE])
        
        if mcq_questions:
            question = mcq_questions[0]
            assert len(question.options) >= 3  # Should have multiple options
            assert question.correct_answer is not None
            assert question.answer_key is not None
    
    def test_answer_key_generation(self):
        """Test answer key generation."""
        assessment = self.generator.generate_assessment(self.sample_topic)
        
        assert len(assessment.answer_key) > 0
        
        # Verify answer key has entries for all questions
        total_questions = sum(len(section.questions) for section in assessment.sections)
        assert len(assessment.answer_key) == total_questions
    
    def test_grading_scale(self):
        """Test grading scale assignment."""
        assessment = self.generator.generate_assessment(self.sample_topic)
        
        assert len(assessment.grading_scale) > 0
        for grade, (min_pts, max_pts) in assessment.grading_scale.items():
            assert min_pts <= max_pts
            assert min_pts >= 0
    
    def test_accessibility_adaptations(self):
        """Test accessibility features in assessments."""
        assessment = self.generator.generate_assessment(self.sample_topic)
        
        assert len(assessment.accessibility_adaptations) > 0
        assert "visual_impairment" in assessment.accessibility_adaptations


class TestProgressTracker:
    """Test the ProgressTracker functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker()
        self.sample_topic_id = "math_uganda_g1_01"
    
    def test_student_profile_creation(self):
        """Test student profile creation."""
        profile = self.tracker.create_student_profile(
            student_id="student_001",
            name="Test Student",
            grade_level=3,
            country=Country.UGANDA
        )
        
        assert profile.student_id == "student_001"
        assert profile.name == "Test Student"
        assert profile.grade_level == 3
        assert profile.country == Country.UGANDA
    
    def test_learning_attempt_recording(self):
        """Test recording learning attempts."""
        # Create student profile
        self.tracker.create_student_profile("student_001", "Test", 3, Country.UGANDA)
        
        # Record attempt
        progress = self.tracker.record_learning_attempt(
            student_id="student_001",
            topic_id=self.sample_topic_id,
            score=0.8,
            time_spent=30,
            assessment_type="quiz"
        )
        
        assert progress.topic_id == self.sample_topic_id
        assert progress.student_id == "student_001"
        assert progress.current_score == 0.8
        assert len(progress.attempts) == 1
    
    def test_mastery_level_progression(self):
        """Test mastery level updates."""
        self.tracker.create_student_profile("student_001", "Test", 3, Country.UGANDA)
        
        # Record low score attempt
        self.tracker.record_learning_attempt("student_001", self.sample_topic_id, 0.3, 20)
        mastery = self.tracker.check_mastery("student_001", self.sample_topic_id)
        assert mastery == MasteryLevel.INTRODUCED
        
        # Record high score attempt
        self.tracker.record_learning_attempt("student_001", self.sample_topic_id, 0.9, 25)
        mastery = self.tracker.check_mastery("student_001", self.sample_topic_id)
        assert mastery == MasteryLevel.MASTERED
    
    def test_prerequisite_checking(self):
        """Test prerequisite validation."""
        self.tracker.create_student_profile("student_001", "Test", 3, Country.UGANDA)
        
        prerequisite_topics = {"prereq_1", "prereq_2"}
        
        # Without prerequisites met
        is_valid, missing = self.tracker.validate_prerequisites(
            "student_001", 
            "target_topic",
            prerequisite_topics
        )
        assert not is_valid
        assert len(missing) == 2
        
        # With prerequisites met (simulate by recording high scores)
        for prereq in prerequisite_topics:
            self.tracker.record_learning_attempt("student_001", prereq, 0.8, 30)
        
        is_valid, missing = self.tracker.validate_prerequisites(
            "student_001",
            "target_topic", 
            prerequisite_topics
        )
        assert is_valid
        assert len(missing) == 0
    
    def test_progress_analysis(self):
        """Test student progress analysis."""
        self.tracker.create_student_profile("student_001", "Test", 3, Country.UGANDA)
        
        # Record multiple attempts
        for i in range(3):
            self.tracker.record_learning_attempt(
                "student_001",
                f"topic_{i}",
                0.7 + (i * 0.1),  # Improving scores
                30
            )
        
        analysis = self.tracker.analyze_student_progress("student_001")
        
        assert analysis["student_id"] == "student_001"
        assert analysis["total_topics_attempted"] == 3
        assert analysis["mastery_rate"] > 0
        assert "progress_trend" in analysis
    
    def test_recommendation_system(self):
        """Test topic recommendation system."""
        self.tracker.create_student_profile("student_001", "Test", 3, Country.UGANDA)
        
        # Record some progress
        self.tracker.record_learning_attempt("student_001", "completed_topic", 0.8, 30)
        
        recommendations = self.tracker.get_recommended_topics("student_001", max_recommendations=3)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
        
        for topic_id, score in recommendations:
            assert isinstance(topic_id, str)
            assert 0.0 <= score <= 1.0
    
    def test_class_analytics(self):
        """Test class-level analytics."""
        # Create multiple student profiles
        for i in range(5):
            student_id = f"student_{i:03d}"
            self.tracker.create_student_profile(student_id, f"Student {i}", 3, Country.UGANDA)
            
            # Record some progress
            self.tracker.record_learning_attempt(student_id, "topic_1", 0.6 + (i * 0.1), 30)
        
        analytics = self.tracker.get_class_analytics(3, Country.UGANDA)
        
        assert analytics["grade_level"] == 3
        assert analytics["country"] == "uganda"
        assert analytics["total_students"] == 5
        assert "average_mastery_rate" in analytics
        assert "students_on_track" in analytics


class TestIntegration:
    """Test integration between all curriculum components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = CurriculumEngine()
        self.lesson_generator = LessonGenerator()
        self.assessment_generator = AssessmentGenerator()
        self.progress_tracker = ProgressTracker()
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from curriculum to progress tracking."""
        # 1. Get a topic from curriculum
        topic = list(self.engine.topics.values())[0]
        
        # 2. Generate lesson for topic
        lesson = self.lesson_generator.generate_lesson(topic)
        assert lesson.topic_id == topic.id
        
        # 3. Generate assessment for topic
        assessment = self.assessment_generator.generate_assessment(topic)
        assert assessment.topic_id == topic.id
        
        # 4. Create student and record progress
        student_id = "integration_test_student"
        self.progress_tracker.create_student_profile(
            student_id, "Integration Test", topic.grade_level, topic.country
        )
        
        # 5. Record learning attempt
        progress = self.progress_tracker.record_learning_attempt(
            student_id, topic.id, 0.75, 45, "lesson_assessment"
        )
        
        assert progress.topic_id == topic.id
        assert progress.current_score == 0.75
        
        # 6. Analyze progress
        analysis = self.progress_tracker.analyze_student_progress(student_id)
        assert analysis["total_topics_attempted"] == 1
    
    def test_prerequisite_workflow(self):
        """Test prerequisite checking workflow."""
        # Get topics with prerequisites
        topics_with_prereqs = [t for t in self.engine.topics.values() 
                             if len(t.prerequisites) > 0]
        
        if topics_with_prereqs:
            target_topic = topics_with_prereqs[0]
            prerequisite_ids = list(target_topic.prerequisites)
            
            # Create student
            student_id = "prereq_test_student"
            self.progress_tracker.create_student_profile(
                student_id, "Prerequisite Test", target_topic.grade_level, target_topic.country
            )
            
            # Check prerequisites before completion
            is_valid, missing = self.progress_tracker.validate_prerequisites(
                student_id, target_topic.id, target_topic.prerequisites
            )
            assert not is_valid
            
            # Complete prerequisites
            for prereq_id in prerequisite_ids[:1]:  # Complete at least one
                if prereq_id in self.engine.topics:
                    self.progress_tracker.record_learning_attempt(
                        student_id, prereq_id, 0.8, 30
                    )
            
            # Generate lesson after prerequisites
            lesson = self.lesson_generator.generate_lesson(target_topic)
            assert lesson is not None


if __name__ == "__main__":
    pytest.main([__file__])