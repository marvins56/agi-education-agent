"""
Tests for Content Management System

This module contains comprehensive tests for the content management system
including library, creator, review, and import/export functionality.
"""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock

from src.content_management import (
    ContentLibrary, ContentCreator, ContentReview, ContentImporter, ContentExporter,
    ContentType, DifficultyLevel, ContentMetadata, ContentItem
)
from src.content_management.creator import CurriculumObjective, MockGenerationEngine
from src.content_management.review import ReviewStatus, QualityMetric, QualityScore
from src.content_management.import_export import JSONImportFormat, SMSExportFormat


class TestContentLibrary:
    """Test cases for ContentLibrary"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.library = ContentLibrary()
    
    def test_add_content(self):
        """Test adding content to library"""
        content_id = self.library.add_content(
            title="Test Lesson",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={"main_content": "Learn about addition"},
            difficulty=DifficultyLevel.BEGINNER,
            tags={"math", "basic"}
        )
        
        assert content_id is not None
        assert len(content_id) > 0
        
        # Verify content was added
        content_item = self.library.get_content(content_id)
        assert content_item is not None
        assert content_item.metadata.title == "Test Lesson"
        assert content_item.metadata.subject == "Mathematics"
        assert content_item.metadata.grade == 5
        assert "math" in content_item.metadata.tags
    
    def test_search_content(self):
        """Test content search functionality"""
        # Add test content
        id1 = self.library.add_content(
            title="Math Lesson 1",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={"content": "Basic addition"},
            difficulty=DifficultyLevel.BEGINNER
        )
        
        id2 = self.library.add_content(
            title="Science Lesson 1",
            content_type=ContentType.LESSON,
            subject="Science",
            grade=5,
            topic="Plants",
            content_data={"content": "Plant biology"},
            difficulty=DifficultyLevel.INTERMEDIATE
        )
        
        # Search by subject
        math_results = self.library.search_content(subject="Mathematics")
        assert len(math_results) == 1
        assert math_results[0].metadata.content_id == id1
        
        # Search by grade
        grade5_results = self.library.search_content(grade=5)
        assert len(grade5_results) == 2
        
        # Search by multiple criteria
        specific_results = self.library.search_content(
            subject="Science",
            difficulty=DifficultyLevel.INTERMEDIATE
        )
        assert len(specific_results) == 1
        assert specific_results[0].metadata.content_id == id2
    
    def test_update_content(self):
        """Test updating content"""
        # Add content
        content_id = self.library.add_content(
            title="Original Title",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={"content": "Original content"}
        )
        
        # Update content
        success = self.library.update_content(
            content_id,
            content_data={"content": "Updated content"},
            metadata_updates={"title": "Updated Title"},
            changes="Updated for clarity"
        )
        
        assert success is True
        
        # Verify updates
        updated_item = self.library.get_content(content_id)
        assert updated_item.metadata.title == "Updated Title"
        assert updated_item.content_data["content"] == "Updated content"
        assert updated_item.metadata.version == 2
        assert len(updated_item.versions) == 2
    
    def test_delete_content(self):
        """Test deleting content"""
        content_id = self.library.add_content(
            title="To Delete",
            content_type=ContentType.LESSON,
            subject="Test",
            grade=1,
            topic="Test",
            content_data={"content": "test"}
        )
        
        # Verify content exists
        assert self.library.get_content(content_id) is not None
        
        # Delete content
        success = self.library.delete_content(content_id)
        assert success is True
        
        # Verify content is deleted
        assert self.library.get_content(content_id) is None
    
    def test_rating_system(self):
        """Test content rating system"""
        content_id = self.library.add_content(
            title="Test Content",
            content_type=ContentType.LESSON,
            subject="Test",
            grade=1,
            topic="Test",
            content_data={"content": "test"}
        )
        
        # Add ratings
        assert self.library.add_rating(content_id, 5.0) is True
        assert self.library.add_rating(content_id, 4.0) is True
        assert self.library.add_rating(content_id, 3.0) is True
        
        # Check updated rating
        content_item = self.library.get_content(content_id)
        assert content_item.metadata.rating_count == 3
        assert content_item.metadata.rating == 4.0  # (5+4+3)/3
    
    def test_statistics(self):
        """Test library statistics"""
        # Add various content
        self.library.add_content(
            title="Math Lesson",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={"content": "test"}
        )
        
        self.library.add_content(
            title="Math Quiz",
            content_type=ContentType.QUIZ,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={"content": "test"}
        )
        
        stats = self.library.get_statistics()
        
        assert stats['total_content'] == 2
        assert 'lesson' in stats['content_by_type']
        assert 'quiz' in stats['content_by_type']
        assert stats['content_by_type']['lesson'] == 1
        assert stats['content_by_type']['quiz'] == 1
        assert stats['content_by_subject']['Mathematics'] == 2


class TestContentCreator:
    """Test cases for ContentCreator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_engine = MockGenerationEngine()
        self.library = ContentLibrary()
        self.creator = ContentCreator(self.mock_engine, self.library)
    
    @pytest.mark.asyncio
    async def test_generate_lesson(self):
        """Test lesson generation"""
        objectives = [
            CurriculumObjective(
                subject="Mathematics",
                grade=5,
                topic="Addition",
                objective_text="Students will learn basic addition",
                skills=["calculation", "problem_solving"],
                assessment_criteria=["accuracy", "speed"]
            )
        ]
        
        lesson = await self.creator.generate_lesson(
            topic="Basic Addition",
            curriculum_objectives=objectives,
            grade=5,
            subject="Mathematics",
            difficulty=DifficultyLevel.BEGINNER
        )
        
        assert lesson is not None
        assert "title" in lesson
        assert "introduction" in lesson
        assert "main_content" in lesson
        assert lesson["title"].startswith("Basic Addition")
    
    @pytest.mark.asyncio
    async def test_generate_quiz(self):
        """Test quiz generation"""
        quiz = await self.creator.generate_quiz(
            topic="Addition",
            grade=5,
            subject="Mathematics",
            num_questions=5,
            difficulty=DifficultyLevel.BEGINNER
        )
        
        assert quiz is not None
        assert "title" in quiz
        assert "questions" in quiz
        assert quiz["title"].startswith("Addition Quiz")
    
    @pytest.mark.asyncio
    async def test_generate_flashcards(self):
        """Test flashcard generation"""
        flashcards = await self.creator.generate_flashcards(
            topic="Addition Facts",
            grade=5,
            subject="Mathematics",
            num_cards=10,
            difficulty=DifficultyLevel.BEGINNER
        )
        
        assert flashcards is not None
        assert "title" in flashcards
        assert "cards" in flashcards
        assert flashcards["title"].startswith("Addition Facts Flashcards")
    
    def test_template_system(self):
        """Test content template system"""
        templates = self.creator.list_templates()
        assert len(templates) > 0
        
        # Get lesson template
        lesson_template = self.creator.get_template("lesson_basic")
        assert lesson_template is not None
        assert lesson_template.content_type == ContentType.LESSON
        
        # Test template rendering
        rendered = lesson_template.render({
            "lesson_title": "Test Lesson",
            "topic": "Test Topic",
            "grade": "5",
            "difficulty": "beginner",
            "objectives": "Test objectives",
            "introduction": "Test intro",
            "main_content": "Test content",
            "examples": "Test examples",
            "exercises": "Test exercises",
            "summary": "Test summary",
            "resources": "Test resources"
        })
        
        assert rendered["title"] == "Test Lesson"
        assert rendered["introduction"] == "Test intro"


class TestContentReview:
    """Test cases for ContentReview"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.library = ContentLibrary()
        self.review = ContentReview(self.library)
    
    def create_test_content(self) -> ContentItem:
        """Create test content item"""
        content_id = self.library.add_content(
            title="Test Content",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={
                "introduction": "This is a test lesson about addition.",
                "main_content": "Addition is the process of combining numbers.",
                "examples": "2 + 3 = 5"
            }
        )
        return self.library.get_content(content_id)
    
    @pytest.mark.asyncio
    async def test_auto_review(self):
        """Test automated content review"""
        content_item = self.create_test_content()
        
        review_entry = await self.review.auto_review_content(content_item)
        
        assert review_entry is not None
        assert review_entry.content_id == content_item.metadata.content_id
        assert review_entry.reviewer_type == "auto"
        assert len(review_entry.quality_scores) > 0
        assert 0.0 <= review_entry.overall_score <= 1.0
        
        # Check specific quality metrics
        metrics = [score.metric for score in review_entry.quality_scores]
        assert QualityMetric.GRAMMAR in metrics
        assert QualityMetric.READABILITY in metrics
        assert QualityMetric.CURRICULUM_ALIGNMENT in metrics
        assert QualityMetric.ACCESSIBILITY in metrics
    
    def test_human_review(self):
        """Test human review submission"""
        content_item = self.create_test_content()
        
        # Add reviewer
        self.review.add_reviewer(
            reviewer_id="teacher1",
            name="Test Teacher",
            reviewer_type="human",
            specializations=["Mathematics"]
        )
        
        # Submit review
        quality_scores = [
            QualityScore(
                metric=QualityMetric.ACCURACY,
                score=0.9,
                details="Content is accurate",
                suggestions=["Add more examples"]
            )
        ]
        
        review_entry = self.review.submit_human_review(
            content_id=content_item.metadata.content_id,
            reviewer_id="teacher1",
            status=ReviewStatus.APPROVED,
            overall_score=0.85,
            quality_scores=quality_scores,
            comments="Good content overall"
        )
        
        assert review_entry is not None
        assert review_entry.reviewer_id == "teacher1"
        assert review_entry.status == ReviewStatus.APPROVED
        assert review_entry.overall_score == 0.85
    
    def test_student_feedback(self):
        """Test student feedback system"""
        content_item = self.create_test_content()
        
        feedback_id = self.review.add_student_feedback(
            content_id=content_item.metadata.content_id,
            student_id="student1",
            rating=4.5,
            helpfulness_rating=4.0,
            difficulty_rating=3.0,
            comments="Very helpful lesson",
            tags={"helpful", "clear"}
        )
        
        assert feedback_id is not None
        
        # Get feedback
        feedback_list = self.review.get_content_feedback(content_item.metadata.content_id)
        assert len(feedback_list) == 1
        assert feedback_list[0].rating == 4.5
        assert feedback_list[0].comments == "Very helpful lesson"
        assert "helpful" in feedback_list[0].tags
    
    def test_improvement_suggestions(self):
        """Test improvement suggestion generation"""
        content_item = self.create_test_content()
        
        # Add some feedback indicating content is too difficult
        self.review.add_student_feedback(
            content_id=content_item.metadata.content_id,
            student_id="student1",
            rating=3.0,
            helpfulness_rating=2.5,
            difficulty_rating=4.5,  # Too difficult
            comments="Too hard to understand"
        )
        
        suggestions = self.review.generate_improvement_suggestions(
            content_item.metadata.content_id
        )
        
        assert len(suggestions) > 0
        # Should suggest simplifying content due to high difficulty rating
        assert any("difficult" in suggestion.lower() for suggestion in suggestions)


class TestImportExport:
    """Test cases for content import/export"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.library = ContentLibrary()
        self.importer = ContentImporter(self.library)
        self.exporter = ContentExporter(self.library)
    
    def test_json_import(self):
        """Test JSON import functionality"""
        # Create test JSON data
        test_data = {
            "title": "Test Lesson",
            "content_type": "lesson",
            "subject": "Mathematics",
            "grade": "5",
            "topic": "Addition",
            "difficulty": "beginner",
            "language": "en",
            "tags": ["math", "basic"],
            "content_data": {
                "introduction": "Learn about addition",
                "main_content": "Addition combines numbers"
            }
        }
        
        json_data = json.dumps(test_data)
        
        # Import content
        successful, failed, errors = self.importer.import_from_data(
            json_data, "json", "test_author"
        )
        
        assert successful == 1
        assert failed == 0
        assert len(errors) == 0
        
        # Verify content was imported
        results = self.library.search_content(subject="Mathematics")
        assert len(results) == 1
        assert results[0].metadata.title == "Test Lesson"
    
    def test_csv_import(self):
        """Test CSV import functionality"""
        # Create test CSV data
        csv_data = """title,content_type,subject,grade,topic,difficulty,introduction,main_content
Test CSV Lesson,lesson,Science,4,Plants,intermediate,Plants are living things,Plants need water and sunlight"""
        
        # Import content
        successful, failed, errors = self.importer.import_from_data(
            csv_data, "csv", "csv_author"
        )
        
        assert successful == 1
        assert failed == 0
        
        # Verify content was imported
        results = self.library.search_content(subject="Science")
        assert len(results) == 1
        assert results[0].metadata.title == "Test CSV Lesson"
        assert results[0].content_data["introduction"] == "Plants are living things"
    
    def test_sms_export(self):
        """Test SMS export functionality"""
        # Add content to library
        content_id = self.library.add_content(
            title="Math Lesson",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={
                "introduction": "Addition is combining numbers together.",
                "main_content": "When we add 2 + 3, we get 5."
            }
        )
        
        # Export to SMS format
        sms_content = self.exporter.export_content([content_id], "sms")
        
        assert isinstance(sms_content, str)
        assert "Addition" in sms_content
        assert len(sms_content) <= 160  # SMS length limit
    
    def test_offline_pack_export(self):
        """Test offline pack export"""
        # Add multiple content items
        content_ids = []
        for i in range(3):
            content_id = self.library.add_content(
                title=f"Lesson {i+1}",
                content_type=ContentType.LESSON,
                subject="Mathematics",
                grade=5,
                topic=f"Topic {i+1}",
                content_data={"content": f"Content {i+1}"}
            )
            content_ids.append(content_id)
        
        # Export as offline pack
        pack_data = self.exporter.export_content(content_ids, "offline_pack")
        
        assert isinstance(pack_data, bytes)
        assert len(pack_data) > 0
        
        # Could test ZIP content extraction here
    
    def test_export_by_criteria(self):
        """Test exporting content by search criteria"""
        # Add test content
        self.library.add_content(
            title="Math Lesson",
            content_type=ContentType.LESSON,
            subject="Mathematics",
            grade=5,
            topic="Addition",
            content_data={"content": "test"}
        )
        
        self.library.add_content(
            title="Science Lesson",
            content_type=ContentType.LESSON,
            subject="Science",
            grade=5,
            topic="Plants",
            content_data={"content": "test"}
        )
        
        # Export only Math content
        exported = self.exporter.export_by_criteria(
            format_type="json",
            subject="Mathematics"
        )
        
        assert isinstance(exported, str)
        exported_data = json.loads(exported)
        assert len(exported_data) == 1
        assert exported_data[0]["subject"] == "Mathematics"
    
    def test_markdown_import(self):
        """Test Markdown import functionality"""
        markdown_content = """---
title: Markdown Test Lesson
content_type: lesson
subject: English
grade: 6
topic: Writing
difficulty: intermediate
tags: writing,grammar
---

# Introduction

This is a test lesson in Markdown format.

## Main Content

Students will learn about writing techniques.

### Examples

- Example 1: Write a paragraph
- Example 2: Use proper grammar
"""
        
        # Import markdown content
        successful, failed, errors = self.importer.import_from_data(
            markdown_content, "markdown", "markdown_author"
        )
        
        assert successful == 1
        assert failed == 0
        
        # Verify content was imported
        results = self.library.search_content(subject="English")
        assert len(results) == 1
        assert results[0].metadata.title == "Markdown Test Lesson"
        assert results[0].metadata.topic == "Writing"


class TestReadabilityAnalyzer:
    """Test cases for readability analysis"""
    
    def test_flesch_reading_ease(self):
        """Test Flesch Reading Ease calculation"""
        from src.content_management.review import ReadabilityAnalyzer
        
        simple_text = "This is simple. It has short words."
        complex_text = "This sophisticated demonstration exemplifies extraordinarily complicated linguistic constructions."
        
        simple_score = ReadabilityAnalyzer.flesch_reading_ease(simple_text)
        complex_score = ReadabilityAnalyzer.flesch_reading_ease(complex_text)
        
        assert simple_score > complex_score
        assert 0 <= simple_score <= 100
        assert 0 <= complex_score <= 100
    
    def test_grade_level(self):
        """Test grade level estimation"""
        from src.content_management.review import ReadabilityAnalyzer
        
        simple_text = "The cat sat on the mat."
        grade_level = ReadabilityAnalyzer.grade_level(simple_text)
        
        assert isinstance(grade_level, int)
        assert 1 <= grade_level <= 12


class TestGrammarChecker:
    """Test cases for grammar checking"""
    
    def test_grammar_check(self):
        """Test basic grammar checking"""
        from src.content_management.review import GrammarChecker
        
        good_text = "This is a well-written sentence. It has proper structure."
        problematic_text = "This sentence is very very very very very very very very very very very very very long and should be flagged. Fragment."
        
        good_score, good_issues = GrammarChecker.check_grammar(good_text)
        problem_score, problem_issues = GrammarChecker.check_grammar(problematic_text)
        
        assert 0.0 <= good_score <= 1.0
        assert 0.0 <= problem_score <= 1.0
        assert len(problem_issues) > len(good_issues)


if __name__ == "__main__":
    pytest.main([__file__])