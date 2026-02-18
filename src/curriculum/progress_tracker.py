"""
ProgressTracker: Learning progress and mastery tracking system for EduAGI.

Tracks student learning progress, mastery levels, prerequisite checking,
and provides intelligent recommendations for next topics based on
East African curriculum standards.
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import statistics

from .engine import Topic, Subject, DifficultyLevel, Country


class MasteryLevel(Enum):
    NOT_STARTED = 0
    INTRODUCED = 1
    DEVELOPING = 2
    PROFICIENT = 3
    MASTERED = 4
    EXPERT = 5


class ProgressStatus(Enum):
    ON_TRACK = "on_track"
    AHEAD = "ahead"
    BEHIND = "behind"
    AT_RISK = "at_risk"
    EXCELLENT = "excellent"


@dataclass
class LearningAttempt:
    """Individual learning attempt for a topic."""
    timestamp: datetime
    score: float  # 0.0 to 1.0
    time_spent_minutes: int
    assessment_type: str = ""
    notes: str = ""


@dataclass
class TopicProgress:
    """Progress tracking for a specific topic."""
    topic_id: str
    student_id: str
    mastery_level: MasteryLevel = MasteryLevel.NOT_STARTED
    current_score: float = 0.0
    best_score: float = 0.0
    attempts: List[LearningAttempt] = field(default_factory=list)
    
    # Time tracking
    total_time_minutes: int = 0
    first_attempt: Optional[datetime] = None
    last_attempt: Optional[datetime] = None
    
    # Progress indicators
    consecutive_successes: int = 0
    needs_review: bool = False
    prerequisite_gaps: List[str] = field(default_factory=list)
    
    def add_attempt(self, attempt: LearningAttempt):
        """Add a learning attempt and update progress metrics."""
        self.attempts.append(attempt)
        self.total_time_minutes += attempt.time_spent_minutes
        self.last_attempt = attempt.timestamp
        
        if self.first_attempt is None:
            self.first_attempt = attempt.timestamp
        
        # Update scores
        self.current_score = attempt.score
        if attempt.score > self.best_score:
            self.best_score = attempt.score
        
        # Update mastery level based on score
        self._update_mastery_level(attempt.score)
        
        # Track consecutive successes
        if attempt.score >= 0.7:  # 70% threshold for success
            self.consecutive_successes += 1
        else:
            self.consecutive_successes = 0
            self.needs_review = True
    
    def _update_mastery_level(self, score: float):
        """Update mastery level based on latest score."""
        if score >= 0.95:
            self.mastery_level = MasteryLevel.EXPERT
        elif score >= 0.85:
            self.mastery_level = MasteryLevel.MASTERED
        elif score >= 0.7:
            self.mastery_level = MasteryLevel.PROFICIENT
        elif score >= 0.5:
            self.mastery_level = MasteryLevel.DEVELOPING
        elif score > 0:
            self.mastery_level = MasteryLevel.INTRODUCED
        
    def get_average_score(self) -> float:
        """Calculate average score across all attempts."""
        if not self.attempts:
            return 0.0
        return statistics.mean([attempt.score for attempt in self.attempts])
    
    def get_improvement_rate(self) -> float:
        """Calculate rate of improvement over time."""
        if len(self.attempts) < 2:
            return 0.0
        
        first_score = self.attempts[0].score
        last_score = self.attempts[-1].score
        return (last_score - first_score) / len(self.attempts)


@dataclass
class StudentProfile:
    """Complete learning profile for a student."""
    student_id: str
    name: str
    grade_level: int
    country: Country
    subject_preferences: List[Subject] = field(default_factory=list)
    learning_style: str = "mixed"  # visual, auditory, kinesthetic, mixed
    
    # Progress tracking
    topic_progress: Dict[str, TopicProgress] = field(default_factory=dict)
    completed_topics: Set[str] = field(default_factory=set)
    current_topics: Set[str] = field(default_factory=set)
    
    # Performance metrics
    overall_progress_rate: float = 0.0
    average_mastery_level: float = 0.0
    time_efficiency: float = 1.0  # Compared to expected time
    
    # Goals and recommendations
    learning_goals: List[str] = field(default_factory=list)
    recommended_topics: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)


class ProgressTracker:
    """
    Comprehensive learning progress tracking and recommendation system.
    
    Tracks student progress across topics, calculates mastery levels,
    checks prerequisites, and provides intelligent recommendations for
    optimal learning pathways.
    """
    
    def __init__(self):
        self.student_profiles: Dict[str, StudentProfile] = {}
        self.mastery_thresholds = self._initialize_mastery_thresholds()
        self.prerequisite_weights = self._initialize_prerequisite_weights()
        self.recommendation_engine = self._initialize_recommendation_system()
    
    def create_student_profile(self, student_id: str, name: str, grade_level: int, 
                             country: Country) -> StudentProfile:
        """Create a new student profile."""
        profile = StudentProfile(
            student_id=student_id,
            name=name,
            grade_level=grade_level,
            country=country
        )
        self.student_profiles[student_id] = profile
        return profile
    
    def record_learning_attempt(self, student_id: str, topic_id: str, 
                              score: float, time_spent: int, 
                              assessment_type: str = "") -> TopicProgress:
        """Record a learning attempt and update progress."""
        if student_id not in self.student_profiles:
            raise ValueError(f"Student profile not found: {student_id}")
        
        profile = self.student_profiles[student_id]
        
        # Get or create topic progress
        if topic_id not in profile.topic_progress:
            profile.topic_progress[topic_id] = TopicProgress(
                topic_id=topic_id,
                student_id=student_id
            )
        
        topic_progress = profile.topic_progress[topic_id]
        
        # Create and add attempt
        attempt = LearningAttempt(
            timestamp=datetime.now(),
            score=score,
            time_spent_minutes=time_spent,
            assessment_type=assessment_type
        )
        
        topic_progress.add_attempt(attempt)
        
        # Update student profile metrics
        self._update_student_metrics(profile, topic_id, topic_progress)
        
        return topic_progress
    
    def check_mastery(self, student_id: str, topic_id: str) -> MasteryLevel:
        """Check current mastery level for a topic."""
        if (student_id not in self.student_profiles or 
            topic_id not in self.student_profiles[student_id].topic_progress):
            return MasteryLevel.NOT_STARTED
        
        return self.student_profiles[student_id].topic_progress[topic_id].mastery_level
    
    def validate_prerequisites(self, student_id: str, topic_id: str, 
                             topic_prerequisites: Set[str]) -> Tuple[bool, List[str]]:
        """Check if student has met prerequisites for a topic."""
        if student_id not in self.student_profiles:
            return False, ["Student profile not found"]
        
        profile = self.student_profiles[student_id]
        missing_prerequisites = []
        
        for prereq_id in topic_prerequisites:
            mastery = self.check_mastery(student_id, prereq_id)
            if mastery.value < MasteryLevel.PROFICIENT.value:
                missing_prerequisites.append(prereq_id)
        
        return len(missing_prerequisites) == 0, missing_prerequisites
    
    def get_recommended_topics(self, student_id: str, subject: Optional[Subject] = None,
                             max_recommendations: int = 5) -> List[Tuple[str, float]]:
        """Get recommended next topics for a student."""
        if student_id not in self.student_profiles:
            return []
        
        profile = self.student_profiles[student_id]
        recommendations = []
        
        # Score potential topics based on multiple factors
        for topic_id, topic_info in self._get_available_topics(profile, subject).items():
            score = self._calculate_recommendation_score(profile, topic_id, topic_info)
            recommendations.append((topic_id, score))
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:max_recommendations]
    
    def get_learning_pathway(self, student_id: str, target_topics: List[str]) -> List[str]:
        """Generate optimal learning pathway to reach target topics."""
        if student_id not in self.student_profiles:
            return []
        
        profile = self.student_profiles[student_id]
        pathway = []
        completed = profile.completed_topics.copy()
        
        # Build pathway by resolving dependencies
        while target_topics:
            # Find topics that can be learned now (prerequisites met)
            ready_topics = []
            for topic_id in target_topics:
                prereqs = self._get_topic_prerequisites(topic_id)
                can_learn, _ = self.validate_prerequisites(student_id, topic_id, prereqs)
                if can_learn:
                    ready_topics.append(topic_id)
            
            if not ready_topics:
                # Need to learn prerequisites first
                for topic_id in target_topics:
                    prereqs = self._get_topic_prerequisites(topic_id)
                    missing_prereqs = prereqs - completed
                    if missing_prereqs:
                        # Add missing prerequisites to pathway
                        pathway.extend(list(missing_prereqs))
                        completed.update(missing_prereqs)
                        break
                else:
                    break  # No progress possible
            else:
                # Add ready topics to pathway
                next_topic = self._select_optimal_next_topic(ready_topics, profile)
                pathway.append(next_topic)
                completed.add(next_topic)
                target_topics.remove(next_topic)
        
        return pathway
    
    def analyze_student_progress(self, student_id: str) -> Dict[str, any]:
        """Comprehensive analysis of student progress."""
        if student_id not in self.student_profiles:
            return {}
        
        profile = self.student_profiles[student_id]
        
        # Calculate overall statistics
        total_topics = len(profile.topic_progress)
        mastered_topics = sum(1 for tp in profile.topic_progress.values() 
                            if tp.mastery_level.value >= MasteryLevel.PROFICIENT.value)
        
        mastery_distribution = {}
        for level in MasteryLevel:
            count = sum(1 for tp in profile.topic_progress.values() 
                       if tp.mastery_level == level)
            mastery_distribution[level.name] = count
        
        # Subject-wise analysis
        subject_progress = self._analyze_subject_progress(profile)
        
        # Time analysis
        total_learning_time = sum(tp.total_time_minutes for tp in profile.topic_progress.values())
        average_time_per_topic = total_learning_time / max(1, total_topics)
        
        # Progress trends
        progress_trend = self._calculate_progress_trend(profile)
        
        return {
            "student_id": student_id,
            "total_topics_attempted": total_topics,
            "topics_mastered": mastered_topics,
            "mastery_rate": mastered_topics / max(1, total_topics),
            "mastery_distribution": mastery_distribution,
            "subject_progress": subject_progress,
            "total_learning_time_hours": total_learning_time / 60,
            "average_time_per_topic_minutes": average_time_per_topic,
            "progress_trend": progress_trend,
            "current_status": self._determine_progress_status(profile),
            "areas_for_improvement": profile.areas_for_improvement,
            "recommended_next_steps": profile.recommended_topics[:3]
        }
    
    def get_class_analytics(self, grade_level: int, country: Country, 
                          subject: Optional[Subject] = None) -> Dict[str, any]:
        """Get analytics for a class or grade level."""
        students = [p for p in self.student_profiles.values() 
                   if p.grade_level == grade_level and p.country == country]
        
        if not students:
            return {}
        
        # Aggregate statistics
        total_students = len(students)
        class_mastery_rates = []
        class_progress_rates = []
        
        for student in students:
            student_analysis = self.analyze_student_progress(student.student_id)
            class_mastery_rates.append(student_analysis.get("mastery_rate", 0))
            class_progress_rates.append(student.overall_progress_rate)
        
        return {
            "grade_level": grade_level,
            "country": country.value,
            "subject": subject.value if subject else "all",
            "total_students": total_students,
            "average_mastery_rate": statistics.mean(class_mastery_rates),
            "average_progress_rate": statistics.mean(class_progress_rates),
            "students_on_track": sum(1 for rate in class_progress_rates if rate >= 0.7),
            "students_needing_support": sum(1 for rate in class_progress_rates if rate < 0.5),
            "class_performance_trend": "improving" if statistics.mean(class_progress_rates) > 0.7 else "needs_attention"
        }
    
    def _update_student_metrics(self, profile: StudentProfile, topic_id: str, 
                              topic_progress: TopicProgress):
        """Update overall student metrics based on latest progress."""
        # Update completed topics
        if topic_progress.mastery_level.value >= MasteryLevel.PROFICIENT.value:
            profile.completed_topics.add(topic_id)
        
        # Calculate overall progress metrics
        if profile.topic_progress:
            mastery_levels = [tp.mastery_level.value for tp in profile.topic_progress.values()]
            profile.average_mastery_level = statistics.mean(mastery_levels)
        
        # Update recommendations
        profile.recommended_topics = [topic_id for topic_id, _ in 
                                    self.get_recommended_topics(profile.student_id)]
    
    def _calculate_recommendation_score(self, profile: StudentProfile, 
                                      topic_id: str, topic_info: dict) -> float:
        """Calculate recommendation score for a topic."""
        score = 0.0
        
        # Subject preference boost
        if topic_info.get("subject") in profile.subject_preferences:
            score += 0.3
        
        # Difficulty appropriateness
        student_avg_mastery = profile.average_mastery_level
        topic_difficulty = topic_info.get("difficulty", 1)
        if abs(student_avg_mastery - topic_difficulty) < 1:
            score += 0.2
        
        # Prerequisites met
        prereqs_met = topic_info.get("prerequisites_met", False)
        if prereqs_met:
            score += 0.4
        
        # Avoid recently attempted topics
        if topic_id in profile.topic_progress:
            last_attempt = profile.topic_progress[topic_id].last_attempt
            if last_attempt and (datetime.now() - last_attempt).days < 7:
                score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _get_available_topics(self, profile: StudentProfile, 
                            subject: Optional[Subject]) -> Dict[str, dict]:
        """Get available topics for recommendation."""
        # Simplified implementation - would integrate with CurriculumEngine
        return {}
    
    def _get_topic_prerequisites(self, topic_id: str) -> Set[str]:
        """Get prerequisites for a topic."""
        # Would integrate with CurriculumEngine
        return set()
    
    def _select_optimal_next_topic(self, ready_topics: List[str], 
                                 profile: StudentProfile) -> str:
        """Select the best next topic from ready topics."""
        if len(ready_topics) == 1:
            return ready_topics[0]
        
        # Score each topic and select the best
        scores = []
        for topic_id in ready_topics:
            score = self._calculate_recommendation_score(profile, topic_id, {})
            scores.append((topic_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0]
    
    def _analyze_subject_progress(self, profile: StudentProfile) -> Dict[str, dict]:
        """Analyze progress by subject."""
        subject_stats = {}
        
        for subject in Subject:
            subject_topics = [tp for tp in profile.topic_progress.values() 
                            if self._get_topic_subject(tp.topic_id) == subject]
            
            if subject_topics:
                avg_mastery = statistics.mean([tp.mastery_level.value for tp in subject_topics])
                total_time = sum(tp.total_time_minutes for tp in subject_topics)
                
                subject_stats[subject.value] = {
                    "topics_attempted": len(subject_topics),
                    "average_mastery": avg_mastery,
                    "total_time_minutes": total_time,
                    "mastery_rate": sum(1 for tp in subject_topics 
                                      if tp.mastery_level.value >= MasteryLevel.PROFICIENT.value) / len(subject_topics)
                }
        
        return subject_stats
    
    def _get_topic_subject(self, topic_id: str) -> Subject:
        """Get subject for a topic ID."""
        # Would integrate with CurriculumEngine
        return Subject.MATHEMATICS  # Placeholder
    
    def _calculate_progress_trend(self, profile: StudentProfile) -> str:
        """Calculate overall progress trend."""
        recent_attempts = []
        cutoff_date = datetime.now() - timedelta(days=30)
        
        for tp in profile.topic_progress.values():
            recent = [attempt for attempt in tp.attempts if attempt.timestamp > cutoff_date]
            recent_attempts.extend(recent)
        
        if len(recent_attempts) < 2:
            return "insufficient_data"
        
        scores = [attempt.score for attempt in recent_attempts]
        if len(scores) >= 2:
            trend = scores[-1] - scores[0]
            if trend > 0.1:
                return "improving"
            elif trend < -0.1:
                return "declining"
        
        return "stable"
    
    def _determine_progress_status(self, profile: StudentProfile) -> ProgressStatus:
        """Determine overall progress status."""
        if profile.average_mastery_level >= 4.0:
            return ProgressStatus.EXCELLENT
        elif profile.average_mastery_level >= 3.0:
            return ProgressStatus.ON_TRACK
        elif profile.average_mastery_level >= 2.0:
            return ProgressStatus.BEHIND
        else:
            return ProgressStatus.AT_RISK
    
    # Initialization helper methods
    def _initialize_mastery_thresholds(self) -> Dict:
        """Initialize mastery level thresholds."""
        return {
            MasteryLevel.PROFICIENT: 0.7,
            MasteryLevel.MASTERED: 0.85,
            MasteryLevel.EXPERT: 0.95
        }
    
    def _initialize_prerequisite_weights(self) -> Dict:
        """Initialize prerequisite importance weights."""
        return {}
    
    def _initialize_recommendation_system(self) -> Dict:
        """Initialize recommendation engine parameters."""
        return {}