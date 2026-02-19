"""
Content Review - Quality assurance pipeline for educational content

This module provides content review capabilities including automated quality checks,
human review workflows, and content improvement suggestions.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
import re
import statistics

from .library import ContentItem, ContentLibrary

logger = logging.getLogger(__name__)


class ReviewStatus(Enum):
    """Content review status"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class QualityMetric(Enum):
    """Quality assessment metrics"""
    GRAMMAR = "grammar"
    READABILITY = "readability"
    CURRICULUM_ALIGNMENT = "curriculum_alignment"
    ACCURACY = "accuracy"
    ENGAGEMENT = "engagement"
    ACCESSIBILITY = "accessibility"


@dataclass
class QualityScore:
    """Quality score for content"""
    metric: QualityMetric
    score: float  # 0.0 to 1.0
    details: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ReviewEntry:
    """Review entry for content"""
    review_id: str
    content_id: str
    reviewer_id: str
    reviewer_type: str  # "auto" or "human"
    status: ReviewStatus
    quality_scores: List[QualityScore]
    overall_score: float
    comments: str
    suggestions: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def get_average_score(self) -> float:
        """Calculate average quality score"""
        if not self.quality_scores:
            return 0.0
        return statistics.mean([score.score for score in self.quality_scores])


@dataclass
class StudentFeedback:
    """Student feedback on content"""
    feedback_id: str
    content_id: str
    student_id: str
    rating: float  # 1.0 to 5.0
    helpfulness_rating: float  # 1.0 to 5.0
    difficulty_rating: float  # 1.0 to 5.0 (1=too easy, 5=too hard)
    comments: str
    tags: Set[str] = field(default_factory=set)
    submitted_at: datetime = field(default_factory=datetime.now)


class ReadabilityAnalyzer:
    """Analyze text readability"""
    
    @staticmethod
    def flesch_reading_ease(text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        if not text.strip():
            return 0.0
        
        # Count sentences, words, and syllables
        sentences = len(re.split(r'[.!?]+', text))
        words = len(text.split())
        
        if sentences == 0 or words == 0:
            return 0.0
        
        # Simple syllable counting (approximation)
        syllables = sum([ReadabilityAnalyzer._count_syllables(word) for word in text.split()])
        
        # Flesch Reading Ease formula
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def _count_syllables(word: str) -> int:
        """Count syllables in a word (approximation)"""
        word = word.lower().strip('.,!?";')
        if not word:
            return 0
        
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not previous_was_vowel:
                    syllable_count += 1
                previous_was_vowel = True
            else:
                previous_was_vowel = False
        
        # Handle silent e
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    @staticmethod
    def grade_level(text: str) -> int:
        """Estimate reading grade level"""
        flesch_score = ReadabilityAnalyzer.flesch_reading_ease(text)
        
        # Convert Flesch score to grade level (approximation)
        if flesch_score >= 90:
            return 5
        elif flesch_score >= 80:
            return 6
        elif flesch_score >= 70:
            return 7
        elif flesch_score >= 60:
            return 8
        elif flesch_score >= 50:
            return 9
        elif flesch_score >= 40:
            return 10
        elif flesch_score >= 30:
            return 11
        else:
            return 12


class GrammarChecker:
    """Basic grammar checking functionality"""
    
    @staticmethod
    def check_grammar(text: str) -> Tuple[float, List[str]]:
        """
        Perform basic grammar checks
        
        Returns:
            Tuple of (score, issues_found)
        """
        issues = []
        
        # Check for common issues
        if re.search(r'\b(there|their|they\'re)\b', text, re.IGNORECASE):
            # Could add more sophisticated there/their/they're checking
            pass
        
        # Check for sentence structure
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # Check for very long sentences
                if len(sentence.split()) > 30:
                    issues.append(f"Long sentence detected: {sentence[:50]}...")
                
                # Check for sentence fragments
                if len(sentence.split()) < 3:
                    issues.append(f"Possible sentence fragment: {sentence}")
        
        # Calculate score based on issues found
        total_sentences = len([s for s in sentences if s.strip()])
        if total_sentences == 0:
            return 0.0, issues
        
        error_rate = len(issues) / total_sentences
        score = max(0.0, 1.0 - error_rate)
        
        return score, issues


class ContentReview:
    """Content review and quality assurance system"""
    
    def __init__(self, content_library: Optional[ContentLibrary] = None):
        """
        Initialize content review system
        
        Args:
            content_library: Content library for accessing content
        """
        self.content_library = content_library
        self.reviews: Dict[str, ReviewEntry] = {}
        self.feedback: Dict[str, List[StudentFeedback]] = {}
        self.reviewers: Dict[str, Dict[str, Any]] = {}
        
    def add_reviewer(self, 
                    reviewer_id: str,
                    name: str,
                    reviewer_type: str = "human",
                    specializations: List[str] = None,
                    qualifications: List[str] = None):
        """Add a reviewer to the system"""
        self.reviewers[reviewer_id] = {
            "name": name,
            "type": reviewer_type,
            "specializations": specializations or [],
            "qualifications": qualifications or [],
            "reviews_completed": 0,
            "average_review_time": 0.0
        }
        logger.info(f"Added reviewer: {name} ({reviewer_id})")
    
    async def auto_review_content(self, content_item: ContentItem) -> ReviewEntry:
        """
        Perform automated content review
        
        Args:
            content_item: Content to review
            
        Returns:
            Review entry with quality scores
        """
        logger.info(f"Auto-reviewing content: {content_item.metadata.content_id}")
        
        quality_scores = []
        
        # Extract text content for analysis
        text_content = self._extract_text_content(content_item.content_data)
        
        # Grammar check
        grammar_score, grammar_issues = GrammarChecker.check_grammar(text_content)
        grammar_quality = QualityScore(
            metric=QualityMetric.GRAMMAR,
            score=grammar_score,
            details=f"Grammar check completed. Issues found: {len(grammar_issues)}",
            suggestions=[f"Fix grammar issue: {issue}" for issue in grammar_issues[:3]]
        )
        quality_scores.append(grammar_quality)
        
        # Readability check
        readability_score = ReadabilityAnalyzer.flesch_reading_ease(text_content)
        grade_level = ReadabilityAnalyzer.grade_level(text_content)
        expected_grade = int(content_item.metadata.grade) if isinstance(content_item.metadata.grade, str) and content_item.metadata.grade.isdigit() else content_item.metadata.grade
        
        # Score based on how close the grade level is to expected
        if isinstance(expected_grade, int):
            grade_diff = abs(grade_level - expected_grade)
            readability_quality_score = max(0.0, 1.0 - (grade_diff / 5.0))
        else:
            readability_quality_score = 0.5  # Neutral score if can't determine expected grade
        
        readability_quality = QualityScore(
            metric=QualityMetric.READABILITY,
            score=readability_quality_score,
            details=f"Readability: Grade {grade_level}, Flesch: {readability_score:.1f}",
            suggestions=self._get_readability_suggestions(grade_level, expected_grade)
        )
        quality_scores.append(readability_quality)
        
        # Curriculum alignment check (basic implementation)
        alignment_score, alignment_suggestions = self._check_curriculum_alignment(content_item)
        alignment_quality = QualityScore(
            metric=QualityMetric.CURRICULUM_ALIGNMENT,
            score=alignment_score,
            details=f"Curriculum alignment assessment completed",
            suggestions=alignment_suggestions
        )
        quality_scores.append(alignment_quality)
        
        # Accessibility check
        accessibility_score, accessibility_suggestions = self._check_accessibility(content_item)
        accessibility_quality = QualityScore(
            metric=QualityMetric.ACCESSIBILITY,
            score=accessibility_score,
            details=f"Accessibility assessment completed",
            suggestions=accessibility_suggestions
        )
        quality_scores.append(accessibility_quality)
        
        # Calculate overall score
        overall_score = statistics.mean([score.score for score in quality_scores])
        
        # Determine status based on score
        if overall_score >= 0.8:
            status = ReviewStatus.APPROVED
        elif overall_score >= 0.6:
            status = ReviewStatus.NEEDS_REVISION
        else:
            status = ReviewStatus.REJECTED
        
        # Compile suggestions
        all_suggestions = []
        for score in quality_scores:
            all_suggestions.extend(score.suggestions)
        
        review_entry = ReviewEntry(
            review_id=f"auto_{content_item.metadata.content_id}_{int(datetime.now().timestamp())}",
            content_id=content_item.metadata.content_id,
            reviewer_id="auto_system",
            reviewer_type="auto",
            status=status,
            quality_scores=quality_scores,
            overall_score=overall_score,
            comments=f"Automated review completed. Overall quality: {overall_score:.2f}",
            suggestions=all_suggestions
        )
        
        self.reviews[review_entry.review_id] = review_entry
        
        # Update content quality score
        if self.content_library:
            self.content_library.update_content(
                content_item.metadata.content_id,
                metadata_updates={"quality_score": overall_score}
            )
        
        logger.info(f"Auto-review completed for {content_item.metadata.content_id}: {overall_score:.2f}")
        return review_entry
    
    def submit_human_review(self,
                           content_id: str,
                           reviewer_id: str,
                           status: ReviewStatus,
                           overall_score: float,
                           quality_scores: List[QualityScore],
                           comments: str,
                           suggestions: List[str] = None) -> ReviewEntry:
        """Submit a human review"""
        if reviewer_id not in self.reviewers:
            raise ValueError(f"Reviewer not found: {reviewer_id}")
        
        review_entry = ReviewEntry(
            review_id=f"human_{content_id}_{reviewer_id}_{int(datetime.now().timestamp())}",
            content_id=content_id,
            reviewer_id=reviewer_id,
            reviewer_type="human",
            status=status,
            quality_scores=quality_scores,
            overall_score=overall_score,
            comments=comments,
            suggestions=suggestions or []
        )
        
        self.reviews[review_entry.review_id] = review_entry
        
        # Update reviewer stats
        self.reviewers[reviewer_id]["reviews_completed"] += 1
        
        # Update content quality score
        if self.content_library:
            self.content_library.update_content(
                content_id,
                metadata_updates={"quality_score": overall_score}
            )
        
        logger.info(f"Human review submitted for {content_id} by {reviewer_id}")
        return review_entry
    
    def add_student_feedback(self,
                           content_id: str,
                           student_id: str,
                           rating: float,
                           helpfulness_rating: float,
                           difficulty_rating: float,
                           comments: str,
                           tags: Set[str] = None) -> str:
        """Add student feedback for content"""
        feedback = StudentFeedback(
            feedback_id=f"feedback_{content_id}_{student_id}_{int(datetime.now().timestamp())}",
            content_id=content_id,
            student_id=student_id,
            rating=rating,
            helpfulness_rating=helpfulness_rating,
            difficulty_rating=difficulty_rating,
            comments=comments,
            tags=tags or set()
        )
        
        if content_id not in self.feedback:
            self.feedback[content_id] = []
        self.feedback[content_id].append(feedback)
        
        # Update content rating in library
        if self.content_library:
            self.content_library.add_rating(content_id, rating)
        
        logger.info(f"Student feedback added for {content_id}")
        return feedback.feedback_id
    
    def get_content_reviews(self, content_id: str) -> List[ReviewEntry]:
        """Get all reviews for content"""
        return [review for review in self.reviews.values() if review.content_id == content_id]
    
    def get_content_feedback(self, content_id: str) -> List[StudentFeedback]:
        """Get student feedback for content"""
        return self.feedback.get(content_id, [])
    
    def get_review_queue(self, reviewer_id: Optional[str] = None) -> List[str]:
        """Get content IDs pending review"""
        pending_reviews = [
            review.content_id for review in self.reviews.values()
            if review.status in [ReviewStatus.PENDING, ReviewStatus.IN_REVIEW]
        ]
        
        if reviewer_id:
            # Filter by reviewer specialization if applicable
            if reviewer_id in self.reviewers:
                specializations = self.reviewers[reviewer_id]["specializations"]
                # TODO: Filter based on content subject matching specializations
        
        return list(set(pending_reviews))
    
    def generate_improvement_suggestions(self, content_id: str) -> List[str]:
        """Generate improvement suggestions based on reviews and feedback"""
        suggestions = []
        
        # Get reviews
        reviews = self.get_content_reviews(content_id)
        for review in reviews:
            suggestions.extend(review.suggestions)
        
        # Get feedback
        feedback_list = self.get_content_feedback(content_id)
        
        # Analyze feedback patterns
        if feedback_list:
            avg_difficulty = statistics.mean([f.difficulty_rating for f in feedback_list])
            if avg_difficulty > 4.0:
                suggestions.append("Content may be too difficult - consider simplifying language or adding more examples")
            elif avg_difficulty < 2.0:
                suggestions.append("Content may be too easy - consider adding more challenging elements")
            
            avg_helpfulness = statistics.mean([f.helpfulness_rating for f in feedback_list])
            if avg_helpfulness < 3.0:
                suggestions.append("Content helpfulness is low - consider adding more practical examples or clearer explanations")
        
        return list(set(suggestions))  # Remove duplicates
    
    def _extract_text_content(self, content_data: Dict[str, Any]) -> str:
        """Extract text content from content data"""
        text_parts = []
        
        def extract_text_recursive(obj):
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_text_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text_recursive(item)
        
        extract_text_recursive(content_data)
        return " ".join(text_parts)
    
    def _get_readability_suggestions(self, current_grade: int, target_grade: Union[int, str]) -> List[str]:
        """Get readability improvement suggestions"""
        suggestions = []
        
        if isinstance(target_grade, int):
            if current_grade > target_grade + 2:
                suggestions.append("Simplify sentence structure and use shorter words")
                suggestions.append("Break down complex concepts into smaller parts")
            elif current_grade < target_grade - 2:
                suggestions.append("Add more sophisticated vocabulary")
                suggestions.append("Include more detailed explanations")
        
        return suggestions
    
    def _check_curriculum_alignment(self, content_item: ContentItem) -> Tuple[float, List[str]]:
        """Check curriculum alignment (basic implementation)"""
        # This is a simplified implementation
        # In practice, this would check against curriculum standards
        
        suggestions = []
        score = 0.7  # Default moderate score
        
        # Check if learning objectives are present
        content_text = json.dumps(content_item.content_data).lower()
        if "objective" in content_text or "goal" in content_text:
            score += 0.1
        else:
            suggestions.append("Add clear learning objectives")
        
        # Check for assessment elements
        if "question" in content_text or "exercise" in content_text or "practice" in content_text:
            score += 0.1
        else:
            suggestions.append("Include practice exercises or assessment questions")
        
        return min(1.0, score), suggestions
    
    def _check_accessibility(self, content_item: ContentItem) -> Tuple[float, List[str]]:
        """Check accessibility features"""
        suggestions = []
        score = 0.5  # Default score
        
        content_text = json.dumps(content_item.content_data).lower()
        
        # Check for alt text or descriptions for visual content
        if content_item.metadata.content_type.value in ["video", "image"]:
            if "description" in content_text or "alt" in content_text:
                score += 0.2
            else:
                suggestions.append("Add descriptions for visual content")
        
        # Check for structured content
        if any(keyword in content_text for keyword in ["heading", "title", "section"]):
            score += 0.2
        else:
            suggestions.append("Use clear headings and structure")
        
        # Check for simple language indicators
        readability_score = ReadabilityAnalyzer.flesch_reading_ease(self._extract_text_content(content_item.content_data))
        if readability_score >= 60:
            score += 0.3
        else:
            suggestions.append("Use simpler language for better accessibility")
        
        return min(1.0, score), suggestions