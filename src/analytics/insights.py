"""
Insights Engine Module

AI-powered learning insights and recommendations system.
Provides actionable recommendations for teachers and identifies learning trends.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import defaultdict, Counter

from .student_analytics import StudentAnalytics, LearningStyle, StudySession
from .class_analytics import ClassAnalytics, RiskLevel


class InsightType(Enum):
    """Types of insights generated"""
    LEARNING_PATTERN = "learning_pattern"
    PERFORMANCE_TREND = "performance_trend"
    ENGAGEMENT_ALERT = "engagement_alert"
    TEACHING_RECOMMENDATION = "teaching_recommendation"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    INTERVENTION_SUGGESTION = "intervention_suggestion"


class TrendDirection(Enum):
    """Direction of trends"""
    IMPROVING = "improving"
    DECLINING = "declining"
    PLATEAU = "plateau"
    VOLATILE = "volatile"
    INSUFFICIENT_DATA = "insufficient_data"


class Priority(Enum):
    """Priority levels for insights"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Insight:
    """Represents a generated insight"""
    insight_id: str
    type: InsightType
    priority: Priority
    title: str
    description: str
    evidence: List[str]
    recommendations: List[str]
    affected_entities: List[str]  # Student IDs, Class IDs, etc.
    confidence: float  # 0.0 to 1.0
    generated_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class LearningPattern:
    """Represents a detected learning pattern"""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: float
    confidence: float
    examples: List[str]


class InsightsEngine:
    """
    AI-powered learning insights engine that analyzes student and class data
    to provide actionable recommendations and trend detection.
    """
    
    def __init__(self):
        self.insights_cache: Dict[str, List[Insight]] = {}
        self.pattern_library: Dict[str, LearningPattern] = {}
        self._load_pattern_library()
    
    def _load_pattern_library(self):
        """Load predefined learning patterns"""
        patterns = [
            LearningPattern(
                pattern_id="morning_peak",
                pattern_type="time_preference",
                description="Student shows consistently higher performance during morning hours",
                frequency=0.0,
                confidence=0.8,
                examples=["8-10 AM sessions show 20% higher scores"]
            ),
            LearningPattern(
                pattern_id="monday_dip", 
                pattern_type="weekly_cycle",
                description="Class performance consistently drops on Mondays",
                frequency=0.0,
                confidence=0.75,
                examples=["Monday average: 72%, Rest of week: 83%"]
            ),
            LearningPattern(
                pattern_id="difficulty_frustration",
                pattern_type="difficulty_response",
                description="Student shows signs of frustration when difficulty increases too quickly",
                frequency=0.0,
                confidence=0.7,
                examples=["Completion rate drops from 90% to 45% when difficulty jumps 2 levels"]
            ),
            LearningPattern(
                pattern_id="visual_preference",
                pattern_type="learning_modality",
                description="Student performs significantly better with visual content",
                frequency=0.0,
                confidence=0.85,
                examples=["Visual content: 88% avg, Text-only: 67% avg"]
            ),
            LearningPattern(
                pattern_id="short_session_preference",
                pattern_type="session_duration",
                description="Student maintains higher engagement with shorter, frequent sessions",
                frequency=0.0,
                confidence=0.8,
                examples=["15-20 min sessions: 92% completion, 45+ min sessions: 63% completion"]
            )
        ]
        
        for pattern in patterns:
            self.pattern_library[pattern.pattern_id] = pattern
    
    def analyze_student_insights(self, student_analytics: StudentAnalytics) -> List[Insight]:
        """
        Generate comprehensive insights for an individual student.
        
        Args:
            student_analytics: Student's analytics data
            
        Returns:
            List of actionable insights
        """
        insights = []
        student_id = student_analytics.student_id
        
        # Learning pattern insights
        insights.extend(self._detect_learning_patterns(student_analytics))
        
        # Performance trend insights
        insights.extend(self._analyze_performance_trends(student_analytics))
        
        # Engagement insights
        insights.extend(self._analyze_engagement_patterns(student_analytics))
        
        # Learning optimization insights
        insights.extend(self._generate_optimization_insights(student_analytics))
        
        # Intervention suggestions
        insights.extend(self._suggest_interventions(student_analytics))
        
        # Cache results
        self.insights_cache[student_id] = insights
        
        return sorted(insights, key=lambda x: (x.priority.value, -x.confidence), reverse=True)
    
    def analyze_class_insights(self, class_analytics: ClassAnalytics) -> List[Insight]:
        """
        Generate insights for an entire class.
        
        Args:
            class_analytics: Class analytics data
            
        Returns:
            List of class-level insights
        """
        insights = []
        class_id = class_analytics.class_id
        
        # Class performance patterns
        insights.extend(self._detect_class_patterns(class_analytics))
        
        # Teaching effectiveness insights
        insights.extend(self._analyze_teaching_effectiveness(class_analytics))
        
        # Resource utilization insights
        insights.extend(self._analyze_resource_effectiveness(class_analytics))
        
        # At-risk student insights
        insights.extend(self._analyze_at_risk_patterns(class_analytics))
        
        # Comparative insights
        insights.extend(self._generate_comparative_insights(class_analytics))
        
        # Cache results
        self.insights_cache[class_id] = insights
        
        return sorted(insights, key=lambda x: (x.priority.value, -x.confidence), reverse=True)
    
    def _detect_learning_patterns(self, student_analytics: StudentAnalytics) -> List[Insight]:
        """Detect individual learning patterns for a student"""
        insights = []
        student_id = student_analytics.student_id
        
        # Detect optimal study time pattern
        optimal_time = student_analytics.detect_optimal_study_time()
        if optimal_time.get("optimal_period") != "insufficient_data":
            period = optimal_time["optimal_period"]
            performance_score = optimal_time.get("performance_score", 0)
            
            if performance_score > 0.7:
                insights.append(Insight(
                    insight_id=f"{student_id}_optimal_time",
                    type=InsightType.LEARNING_PATTERN,
                    priority=Priority.MEDIUM,
                    title=f"Student learns best during {period}",
                    description=f"Analysis shows {period} sessions yield {int(performance_score*100)}% better results",
                    evidence=[
                        f"Performance score: {performance_score:.2f}",
                        f"Best hour: {optimal_time.get('best_hour', 'unknown')}:00",
                        "Based on session timing and performance correlation"
                    ],
                    recommendations=[
                        f"Schedule most challenging topics during {period}",
                        f"Consider lighter content during off-peak hours",
                        f"Communicate optimal study times to parents"
                    ],
                    affected_entities=[student_id],
                    confidence=0.8,
                    generated_at=datetime.now()
                ))
        
        # Detect learning style patterns
        learning_style = student_analytics.infer_learning_style()
        if learning_style["confidence"] > 0.6:
            style = learning_style["style"]
            if hasattr(style, 'value'):
                style_name = style.value
            else:
                style_name = str(style)
                
            style_recommendations = self._get_style_specific_recommendations(style_name)
            
            insights.append(Insight(
                insight_id=f"{student_id}_learning_style",
                type=InsightType.LEARNING_PATTERN,
                priority=Priority.MEDIUM,
                title=f"Student shows {style_name} learning preference",
                description=f"Strong preference detected for {style_name} learning approach",
                evidence=[
                    f"Confidence: {learning_style['confidence']:.2f}",
                    f"Style breakdown: {learning_style['scores']}",
                    "Based on interaction patterns and performance"
                ],
                recommendations=style_recommendations,
                affected_entities=[student_id],
                confidence=learning_style["confidence"],
                generated_at=datetime.now()
            ))
        
        # Detect difficulty progression patterns
        difficulty_curve = student_analytics.get_difficulty_curve_tracking()
        for subject, progression in difficulty_curve.items():
            if len(progression) >= 5:  # Need sufficient data
                # Analyze if student struggles with difficulty increases
                difficulty_struggles = self._analyze_difficulty_struggles(progression)
                if difficulty_struggles:
                    insights.append(Insight(
                        insight_id=f"{student_id}_{subject}_difficulty",
                        type=InsightType.LEARNING_PATTERN,
                        priority=Priority.HIGH,
                        title=f"Student shows difficulty adjustment challenges in {subject}",
                        description="Performance drops significantly when difficulty increases",
                        evidence=difficulty_struggles["evidence"],
                        recommendations=[
                            "Implement gradual difficulty progression",
                            "Provide additional practice at current level before advancing",
                            "Consider scaffolding for difficult concepts",
                            "Monitor closely during difficulty transitions"
                        ],
                        affected_entities=[student_id],
                        confidence=difficulty_struggles["confidence"],
                        generated_at=datetime.now()
                    ))
        
        return insights
    
    def _analyze_performance_trends(self, student_analytics: StudentAnalytics) -> List[Insight]:
        """Analyze performance trends for a student"""
        insights = []
        student_id = student_analytics.student_id
        
        # Analyze recent performance trends by subject
        for subject in set(session.subject for session in student_analytics.sessions):
            subject_sessions = [s for s in student_analytics.sessions 
                             if s.subject == subject and s.score is not None]
            
            if len(subject_sessions) >= 6:  # Need sufficient data for trend analysis
                trend_analysis = self._calculate_trend(
                    [(s.start_time, s.score) for s in subject_sessions[-10:]]  # Last 10 sessions
                )
                
                if trend_analysis["direction"] == TrendDirection.DECLINING:
                    priority = Priority.HIGH if trend_analysis["slope"] < -2 else Priority.MEDIUM
                    
                    insights.append(Insight(
                        insight_id=f"{student_id}_{subject}_declining",
                        type=InsightType.PERFORMANCE_TREND,
                        priority=priority,
                        title=f"Declining performance trend in {subject}",
                        description=f"Student's {subject} scores have decreased by {abs(trend_analysis['slope']):.1f} points over recent sessions",
                        evidence=[
                            f"Trend slope: {trend_analysis['slope']:.2f} points per session",
                            f"Recent average: {trend_analysis['recent_avg']:.1f}",
                            f"Sessions analyzed: {len(subject_sessions[-10:])}"
                        ],
                        recommendations=[
                            f"Review recent {subject} topics for understanding gaps",
                            "Provide additional practice and support",
                            "Consider one-on-one tutoring for this subject",
                            "Check for external factors affecting performance"
                        ],
                        affected_entities=[student_id],
                        confidence=trend_analysis["confidence"],
                        generated_at=datetime.now()
                    ))
                
                elif trend_analysis["direction"] == TrendDirection.IMPROVING:
                    insights.append(Insight(
                        insight_id=f"{student_id}_{subject}_improving",
                        type=InsightType.PERFORMANCE_TREND,
                        priority=Priority.LOW,
                        title=f"Strong improvement in {subject}",
                        description=f"Student's {subject} performance has improved significantly",
                        evidence=[
                            f"Trend slope: +{trend_analysis['slope']:.2f} points per session",
                            f"Recent average: {trend_analysis['recent_avg']:.1f}",
                            f"Improvement rate: {trend_analysis['improvement_rate']:.1f}%"
                        ],
                        recommendations=[
                            "Continue current teaching approach for this subject",
                            "Consider this student as a peer tutor for struggling classmates",
                            "Gradually increase difficulty to maintain challenge",
                            "Celebrate and acknowledge this progress"
                        ],
                        affected_entities=[student_id],
                        confidence=trend_analysis["confidence"],
                        generated_at=datetime.now()
                    ))
        
        return insights
    
    def _analyze_engagement_patterns(self, student_analytics: StudentAnalytics) -> List[Insight]:
        """Analyze engagement patterns and generate insights"""
        insights = []
        student_id = student_analytics.student_id
        
        engagement = student_analytics.calculate_engagement_score()
        
        # Low engagement alert
        if engagement["overall"] < 0.4:
            priority = Priority.URGENT if engagement["overall"] < 0.25 else Priority.HIGH
            
            # Identify specific engagement issues
            issues = []
            if engagement["frequency"] < 0.4:
                issues.append("infrequent study sessions")
            if engagement["duration"] < 0.4:
                issues.append("sessions too short or too long")
            if engagement["completion"] < 0.4:
                issues.append("low completion rates")
            
            insights.append(Insight(
                insight_id=f"{student_id}_low_engagement",
                type=InsightType.ENGAGEMENT_ALERT,
                priority=priority,
                title="Student shows low engagement",
                description=f"Overall engagement score of {engagement['overall']:.2f} indicates risk",
                evidence=[
                    f"Overall score: {engagement['overall']:.2f}",
                    f"Frequency: {engagement['frequency']:.2f}",
                    f"Duration: {engagement['duration']:.2f}",
                    f"Completion: {engagement['completion']:.2f}",
                    f"Primary issues: {', '.join(issues)}"
                ],
                recommendations=[
                    "Schedule immediate one-on-one meeting",
                    "Investigate external factors affecting engagement",
                    "Try different content formats to spark interest",
                    "Consider shortened session lengths",
                    "Provide more interactive and gamified content"
                ],
                affected_entities=[student_id],
                confidence=0.9,
                generated_at=datetime.now()
            ))
        
        # Engagement pattern changes
        recent_sessions = [s for s in student_analytics.sessions 
                          if s.start_time >= datetime.now() - timedelta(weeks=2)]
        older_sessions = [s for s in student_analytics.sessions 
                         if s.start_time < datetime.now() - timedelta(weeks=2) 
                         and s.start_time >= datetime.now() - timedelta(weeks=4)]
        
        if len(recent_sessions) >= 3 and len(older_sessions) >= 3:
            recent_completion = np.mean([s.completion_rate for s in recent_sessions])
            older_completion = np.mean([s.completion_rate for s in older_sessions])
            
            if recent_completion < older_completion - 0.2:  # Significant drop
                insights.append(Insight(
                    insight_id=f"{student_id}_engagement_drop",
                    type=InsightType.ENGAGEMENT_ALERT,
                    priority=Priority.HIGH,
                    title="Recent drop in engagement detected",
                    description="Student's completion rates have decreased significantly",
                    evidence=[
                        f"Recent completion rate: {recent_completion:.2f}",
                        f"Previous completion rate: {older_completion:.2f}",
                        f"Drop: {(older_completion - recent_completion):.2f}"
                    ],
                    recommendations=[
                        "Check in with student about recent changes",
                        "Review recent content difficulty and format",
                        "Consider external factors affecting motivation",
                        "Provide additional encouragement and support"
                    ],
                    affected_entities=[student_id],
                    confidence=0.85,
                    generated_at=datetime.now()
                ))
        
        return insights
    
    def _generate_optimization_insights(self, student_analytics: StudentAnalytics) -> List[Insight]:
        """Generate insights for optimizing student learning"""
        insights = []
        student_id = student_analytics.student_id
        
        # Session duration optimization
        time_analysis = student_analytics.get_time_on_task_analysis()
        for subject, data in time_analysis["by_subject"].items():
            avg_duration = data["avg_minutes"]
            
            if avg_duration > 60:  # Very long sessions
                insights.append(Insight(
                    insight_id=f"{student_id}_{subject}_duration_optimize",
                    type=InsightType.RESOURCE_OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    title=f"Sessions too long for optimal learning in {subject}",
                    description=f"Average session length of {avg_duration:.1f} minutes may lead to fatigue",
                    evidence=[
                        f"Average duration: {avg_duration:.1f} minutes",
                        f"Recommended range: 20-45 minutes",
                        f"Total sessions: {data['total_sessions']}"
                    ],
                    recommendations=[
                        "Break long sessions into smaller chunks",
                        "Include breaks every 25-30 minutes",
                        "Focus on one concept per session",
                        "Use varied activities to maintain attention"
                    ],
                    affected_entities=[student_id],
                    confidence=0.7,
                    generated_at=datetime.now()
                ))
            elif avg_duration < 15:  # Very short sessions
                insights.append(Insight(
                    insight_id=f"{student_id}_{subject}_duration_extend",
                    type=InsightType.RESOURCE_OPTIMIZATION,
                    priority=Priority.LOW,
                    title=f"Sessions might be too short for depth in {subject}",
                    description=f"Average session of {avg_duration:.1f} minutes may limit learning depth",
                    evidence=[
                        f"Average duration: {avg_duration:.1f} minutes",
                        f"Recommended minimum: 15-20 minutes",
                        f"Total sessions: {data['total_sessions']}"
                    ],
                    recommendations=[
                        "Encourage slightly longer focused sessions",
                        "Combine related topics in single sessions",
                        "Ensure sufficient time for concept consolidation"
                    ],
                    affected_entities=[student_id],
                    confidence=0.6,
                    generated_at=datetime.now()
                ))
        
        return insights
    
    def _suggest_interventions(self, student_analytics: StudentAnalytics) -> List[Insight]:
        """Suggest specific interventions based on student data"""
        insights = []
        student_id = student_analytics.student_id
        
        # Check for subjects with low retention
        retention_rates = student_analytics.get_retention_rate()
        for subject, retention in retention_rates.items():
            if retention < 0.5:  # Very low retention
                insights.append(Insight(
                    insight_id=f"{student_id}_{subject}_intervention",
                    type=InsightType.INTERVENTION_SUGGESTION,
                    priority=Priority.HIGH,
                    title=f"Urgent intervention needed for {subject}",
                    description=f"Retention rate of {retention:.2f} indicates serious learning gaps",
                    evidence=[
                        f"Retention rate: {retention:.2f}",
                        f"Target rate: >0.70",
                        "Low retention suggests concepts are not being consolidated"
                    ],
                    recommendations=[
                        f"Assess foundational knowledge in {subject}",
                        "Implement spaced repetition for key concepts",
                        "Provide additional practice materials",
                        "Consider alternative teaching methods",
                        "Schedule regular progress check-ins"
                    ],
                    affected_entities=[student_id],
                    confidence=0.9,
                    generated_at=datetime.now(),
                    expires_at=datetime.now() + timedelta(weeks=2)
                ))
        
        return insights
    
    def _detect_class_patterns(self, class_analytics: ClassAnalytics) -> List[Insight]:
        """Detect patterns across the entire class"""
        insights = []
        class_id = class_analytics.class_id
        
        # Analyze class-wide performance heatmap
        heatmap = class_analytics.get_performance_heatmap()
        
        # Find topics where >50% of students are struggling
        struggling_topics = []
        for subject, topics in heatmap.items():
            for topic, metric in topics.items():
                struggle_rate = metric.struggle_count / metric.student_count if metric.student_count > 0 else 0
                if struggle_rate > 0.5 and metric.student_count >= 3:
                    struggling_topics.append({
                        "subject": subject,
                        "topic": topic,
                        "struggle_rate": struggle_rate,
                        "avg_score": metric.avg_score,
                        "student_count": metric.student_count
                    })
        
        if struggling_topics:
            # Sort by struggle rate and take top issues
            struggling_topics.sort(key=lambda x: x["struggle_rate"], reverse=True)
            
            for topic_data in struggling_topics[:3]:  # Top 3 struggling topics
                insights.append(Insight(
                    insight_id=f"{class_id}_{topic_data['subject']}_{topic_data['topic']}_struggle",
                    type=InsightType.TEACHING_RECOMMENDATION,
                    priority=Priority.HIGH,
                    title=f"Class struggling with {topic_data['subject']}: {topic_data['topic']}",
                    description=f"{topic_data['struggle_rate']:.0%} of students need additional support",
                    evidence=[
                        f"Students struggling: {int(topic_data['struggle_rate'] * topic_data['student_count'])}/{topic_data['student_count']}",
                        f"Average score: {topic_data['avg_score']:.1f}",
                        f"Struggle rate: {topic_data['struggle_rate']:.1%}"
                    ],
                    recommendations=[
                        f"Re-teach {topic_data['topic']} using different approach",
                        "Provide additional practice materials",
                        "Consider breaking topic into smaller components",
                        "Use peer tutoring for this topic",
                        "Check prerequisite knowledge gaps"
                    ],
                    affected_entities=[class_id],
                    confidence=0.85,
                    generated_at=datetime.now()
                ))
        
        # Detect weekly patterns (e.g., Monday performance dips)
        weekly_pattern = self._analyze_weekly_patterns(class_analytics)
        if weekly_pattern:
            insights.append(weekly_pattern)
        
        return insights
    
    def _analyze_weekly_patterns(self, class_analytics: ClassAnalytics) -> Optional[Insight]:
        """Analyze weekly performance patterns"""
        # Collect all sessions with scores
        all_sessions = []
        for analytics in class_analytics.student_analytics.values():
            all_sessions.extend([s for s in analytics.sessions if s.score is not None])
        
        if len(all_sessions) < 20:  # Need sufficient data
            return None
        
        # Group by day of week
        day_scores = defaultdict(list)
        for session in all_sessions:
            day = session.start_time.strftime("%A")  # Monday, Tuesday, etc.
            day_scores[day].append(session.score)
        
        # Calculate averages
        day_averages = {}
        for day, scores in day_scores.items():
            if len(scores) >= 3:  # Minimum sessions per day
                day_averages[day] = np.mean(scores)
        
        if len(day_averages) < 3:
            return None
        
        # Check for Monday dip pattern
        if "Monday" in day_averages:
            monday_avg = day_averages["Monday"]
            other_days_avg = np.mean([avg for day, avg in day_averages.items() if day != "Monday"])
            
            if monday_avg < other_days_avg - 5:  # Significant Monday dip
                return Insight(
                    insight_id=f"{class_analytics.class_id}_monday_dip",
                    type=InsightType.LEARNING_PATTERN,
                    priority=Priority.MEDIUM,
                    title="Class average drops on Monday",
                    description="Students consistently perform worse on Mondays",
                    evidence=[
                        f"Monday average: {monday_avg:.1f}",
                        f"Other days average: {other_days_avg:.1f}",
                        f"Performance gap: {other_days_avg - monday_avg:.1f} points"
                    ],
                    recommendations=[
                        "Consider lighter content on Mondays",
                        "Start Monday with review or warm-up activities",
                        "Use more engaging, interactive content on Mondays",
                        "Check if weekend activities affect Monday readiness"
                    ],
                    affected_entities=[class_analytics.class_id],
                    confidence=0.8,
                    generated_at=datetime.now()
                )
        
        return None
    
    def _analyze_teaching_effectiveness(self, class_analytics: ClassAnalytics) -> List[Insight]:
        """Analyze teaching effectiveness and suggest improvements"""
        insights = []
        
        effectiveness = class_analytics.analyze_teacher_effectiveness()
        
        if "overall_score" in effectiveness:
            overall_score = effectiveness["overall_score"]
            
            if overall_score < 0.6:  # Low effectiveness
                insights.append(Insight(
                    insight_id=f"{class_analytics.teacher_id}_effectiveness_concern",
                    type=InsightType.TEACHING_RECOMMENDATION,
                    priority=Priority.HIGH,
                    title="Teaching effectiveness needs attention",
                    description=f"Overall effectiveness score of {overall_score:.2f} suggests areas for improvement",
                    evidence=[
                        f"Overall score: {overall_score:.2f}",
                        f"Student engagement: {effectiveness.get('student_engagement', 'N/A')}",
                        f"Learning velocity: {effectiveness.get('learning_velocity', 'N/A')}",
                        f"Retention effectiveness: {effectiveness.get('retention_effectiveness', 'N/A')}"
                    ],
                    recommendations=[
                        "Review and adjust teaching methods",
                        "Seek mentoring or professional development",
                        "Focus on increasing student engagement",
                        "Implement formative assessment strategies",
                        "Consider classroom observation and feedback"
                    ],
                    affected_entities=[class_analytics.teacher_id, class_analytics.class_id],
                    confidence=0.75,
                    generated_at=datetime.now()
                ))
        
        return insights
    
    def _analyze_resource_effectiveness(self, class_analytics: ClassAnalytics) -> List[Insight]:
        """Analyze resource utilization and effectiveness"""
        insights = []
        
        resource_data = class_analytics.analyze_resource_utilization()
        
        # Find most effective interaction types
        interaction_effectiveness = resource_data.get("interaction_effectiveness", {})
        if interaction_effectiveness:
            best_type = max(interaction_effectiveness.items(), 
                          key=lambda x: x[1]["avg_score"])
            worst_type = min(interaction_effectiveness.items(), 
                           key=lambda x: x[1]["avg_score"])
            
            score_diff = best_type[1]["avg_score"] - worst_type[1]["avg_score"]
            
            if score_diff > 10:  # Significant difference
                insights.append(Insight(
                    insight_id=f"{class_analytics.class_id}_interaction_optimization",
                    type=InsightType.RESOURCE_OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    title=f"{best_type[0]} content shows superior results",
                    description=f"Students score {score_diff:.1f} points higher with {best_type[0]} vs {worst_type[0]}",
                    evidence=[
                        f"{best_type[0]} average: {best_type[1]['avg_score']:.1f}",
                        f"{worst_type[0]} average: {worst_type[1]['avg_score']:.1f}",
                        f"Performance difference: {score_diff:.1f} points"
                    ],
                    recommendations=[
                        f"Increase use of {best_type[0]} content",
                        f"Convert more {worst_type[0]} content to {best_type[0]} format",
                        "Analyze why this format works better for this class",
                        "Share effective content types with other teachers"
                    ],
                    affected_entities=[class_analytics.class_id],
                    confidence=0.7,
                    generated_at=datetime.now()
                ))
        
        return insights
    
    def _analyze_at_risk_patterns(self, class_analytics: ClassAnalytics) -> List[Insight]:
        """Analyze patterns in at-risk students"""
        insights = []
        
        at_risk_students = class_analytics.identify_at_risk_students()
        critical_count = sum(1 for s in at_risk_students if s.risk_level == RiskLevel.CRITICAL)
        high_count = sum(1 for s in at_risk_students if s.risk_level == RiskLevel.HIGH)
        
        total_students = len(class_analytics.student_analytics)
        
        if critical_count > 0:
            insights.append(Insight(
                insight_id=f"{class_analytics.class_id}_critical_students",
                type=InsightType.INTERVENTION_SUGGESTION,
                priority=Priority.URGENT,
                title=f"{critical_count} students need immediate intervention",
                description="Multiple students showing critical risk factors",
                evidence=[
                    f"Critical risk: {critical_count} students",
                    f"High risk: {high_count} students", 
                    f"Class size: {total_students}",
                    f"Risk rate: {((critical_count + high_count) / total_students * 100):.1f}%"
                ],
                recommendations=[
                    "Schedule immediate individual meetings with critical risk students",
                    "Contact parents/guardians for high-risk students",
                    "Develop individualized intervention plans",
                    "Consider additional support resources",
                    "Monitor progress weekly"
                ],
                affected_entities=[class_analytics.class_id] + [s.student_id for s in at_risk_students if s.risk_level == RiskLevel.CRITICAL],
                confidence=0.95,
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            ))
        
        # Analyze common risk factors
        all_risk_factors = []
        for student in at_risk_students:
            all_risk_factors.extend(student.risk_factors)
        
        if all_risk_factors:
            factor_counts = Counter(all_risk_factors)
            most_common = factor_counts.most_common(3)
            
            for factor, count in most_common:
                if count >= 2:  # At least 2 students with this factor
                    insights.append(Insight(
                        insight_id=f"{class_analytics.class_id}_common_risk_{factor.replace(' ', '_')}",
                        type=InsightType.TEACHING_RECOMMENDATION,
                        priority=Priority.MEDIUM,
                        title=f"Common risk factor: {factor}",
                        description=f"{count} students showing '{factor}' - suggests systemic issue",
                        evidence=[
                            f"Students affected: {count}",
                            f"Risk factor: {factor}",
                            "Multiple students with same issue suggests class-wide intervention needed"
                        ],
                        recommendations=self._get_risk_factor_recommendations(factor),
                        affected_entities=[class_analytics.class_id],
                        confidence=0.8,
                        generated_at=datetime.now()
                    ))
        
        return insights
    
    def _generate_comparative_insights(self, class_analytics: ClassAnalytics) -> List[Insight]:
        """Generate insights based on comparative performance"""
        insights = []
        
        comparative = class_analytics.get_comparative_analytics()
        
        for subject, data in comparative.items():
            if isinstance(data, dict) and "difference" in data:
                difference = data["difference"]
                
                if difference < -10:  # Significantly below national average
                    insights.append(Insight(
                        insight_id=f"{class_analytics.class_id}_{subject}_below_benchmark",
                        type=InsightType.PERFORMANCE_TREND,
                        priority=Priority.HIGH,
                        title=f"Class performing below national average in {subject}",
                        description=f"Class average is {abs(difference):.1f} points below national benchmark",
                        evidence=[
                            f"Class average: {data['class_average']}",
                            f"National average: {data['national_average']}",
                            f"Gap: {difference:.1f} points",
                            f"Estimated percentile: {data.get('percentile_estimate', 'N/A')}"
                        ],
                        recommendations=[
                            f"Focus additional attention on {subject}",
                            "Review curriculum alignment for this subject",
                            "Consider additional resources or training",
                            "Analyze successful classes for best practices",
                            "Implement targeted improvement plan"
                        ],
                        affected_entities=[class_analytics.class_id],
                        confidence=0.8,
                        generated_at=datetime.now()
                    ))
                elif difference > 10:  # Significantly above national average
                    insights.append(Insight(
                        insight_id=f"{class_analytics.class_id}_{subject}_above_benchmark",
                        type=InsightType.PERFORMANCE_TREND,
                        priority=Priority.LOW,
                        title=f"Exceptional performance in {subject}",
                        description=f"Class exceeds national average by {difference:.1f} points",
                        evidence=[
                            f"Class average: {data['class_average']}",
                            f"National average: {data['national_average']}",
                            f"Advantage: +{difference:.1f} points",
                            f"Estimated percentile: {data.get('percentile_estimate', 'N/A')}"
                        ],
                        recommendations=[
                            "Document successful teaching strategies for this subject",
                            "Share best practices with other teachers",
                            "Consider this teacher as a mentor for the subject",
                            "Maintain current approach while monitoring",
                            "Explore opportunities for advanced content"
                        ],
                        affected_entities=[class_analytics.class_id, class_analytics.teacher_id],
                        confidence=0.8,
                        generated_at=datetime.now()
                    ))
        
        return insights
    
    # Helper methods
    def _get_style_specific_recommendations(self, style: str) -> List[str]:
        """Get recommendations specific to learning style"""
        recommendations = {
            "visual": [
                "Use more diagrams, charts, and visual aids",
                "Incorporate color coding in materials",
                "Provide graphic organizers and mind maps",
                "Use videos and visual demonstrations"
            ],
            "auditory": [
                "Include more discussions and verbal explanations", 
                "Use audio recordings and music for learning",
                "Encourage student to explain concepts aloud",
                "Implement group discussions and peer explanations"
            ],
            "kinesthetic": [
                "Incorporate hands-on activities and experiments",
                "Use manipulatives and physical models",
                "Allow movement during learning",
                "Include interactive and tactile experiences"
            ],
            "reading_writing": [
                "Provide detailed written instructions",
                "Encourage note-taking and written summaries",
                "Use text-based learning materials",
                "Assign written reflection activities"
            ],
            "mixed": [
                "Combine multiple teaching modalities",
                "Vary presentation formats regularly",
                "Allow student choice in learning approach",
                "Use multi-sensory learning activities"
            ]
        }
        
        return recommendations.get(style, recommendations["mixed"])
    
    def _analyze_difficulty_struggles(self, progression: List[Dict]) -> Optional[Dict]:
        """Analyze if student struggles with difficulty increases"""
        if len(progression) < 5:
            return None
        
        # Sort by date
        progression = sorted(progression, key=lambda x: x["date"])
        
        # Find difficulty jumps and score changes
        struggles = []
        for i in range(1, len(progression)):
            current = progression[i]
            previous = progression[i-1]
            
            difficulty_jump = current["difficulty"] - previous["difficulty"]
            score_change = current["score"] - previous["score"]
            
            if difficulty_jump >= 2 and score_change < -15:  # Big difficulty jump, significant score drop
                struggles.append({
                    "difficulty_jump": difficulty_jump,
                    "score_drop": abs(score_change),
                    "topic": current["topic"]
                })
        
        if len(struggles) >= 2:  # Pattern of struggle with difficulty
            avg_drop = np.mean([s["score_drop"] for s in struggles])
            evidence = [
                f"Difficulty jumps cause average {avg_drop:.1f} point score drops",
                f"Pattern observed in {len(struggles)} instances",
                f"Topics affected: {[s['topic'] for s in struggles[-3:]]}"  # Last 3 instances
            ]
            
            return {
                "evidence": evidence,
                "confidence": min(0.9, 0.5 + len(struggles) * 0.1)
            }
        
        return None
    
    def _calculate_trend(self, time_score_pairs: List[Tuple[datetime, float]]) -> Dict:
        """Calculate trend direction and statistics"""
        if len(time_score_pairs) < 3:
            return {"direction": TrendDirection.INSUFFICIENT_DATA, "confidence": 0.0}
        
        # Convert dates to numeric values for regression
        dates = [pair[0] for pair in time_score_pairs]
        scores = [pair[1] for pair in time_score_pairs]
        
        # Simple linear regression
        x = np.arange(len(scores))
        slope = np.polyfit(x, scores, 1)[0]
        
        # Determine trend direction
        if abs(slope) < 0.5:
            direction = TrendDirection.PLATEAU
        elif slope > 0.5:
            direction = TrendDirection.IMPROVING
        elif slope < -0.5:
            direction = TrendDirection.DECLINING
        else:
            direction = TrendDirection.VOLATILE
        
        # Calculate confidence based on R-squared
        correlation = np.corrcoef(x, scores)[0, 1]
        confidence = abs(correlation) if not np.isnan(correlation) else 0.0
        
        recent_avg = np.mean(scores[-3:]) if len(scores) >= 3 else np.mean(scores)
        improvement_rate = ((scores[-1] / scores[0]) - 1) * 100 if scores[0] != 0 else 0
        
        return {
            "direction": direction,
            "slope": slope,
            "confidence": confidence,
            "recent_avg": recent_avg,
            "improvement_rate": improvement_rate
        }
    
    def _get_risk_factor_recommendations(self, risk_factor: str) -> List[str]:
        """Get recommendations for specific risk factors"""
        recommendations = {
            "Low engagement score": [
                "Implement more interactive and gamified content",
                "Vary teaching methods and content formats",
                "Provide more frequent positive feedback",
                "Check for external factors affecting engagement"
            ],
            "Declining performance trend": [
                "Review recent teaching methods and content difficulty",
                "Provide additional support and practice materials", 
                "Consider prerequisite knowledge gaps",
                "Schedule individual student consultations"
            ],
            "Poor retention rate": [
                "Implement spaced repetition strategies",
                "Focus on deeper understanding vs. memorization",
                "Provide more frequent review sessions",
                "Use multiple modalities to reinforce concepts"
            ],
            "Insufficient recent activity": [
                "Reach out to inactive students immediately",
                "Investigate barriers to participation",
                "Provide flexible learning options",
                "Consider family outreach and support"
            ]
        }
        
        return recommendations.get(risk_factor, [
            "Monitor student closely",
            "Provide additional support",
            "Consider individualized intervention"
        ])
    
    def get_insight_by_id(self, insight_id: str) -> Optional[Insight]:
        """Retrieve a specific insight by ID"""
        for insights_list in self.insights_cache.values():
            for insight in insights_list:
                if insight.insight_id == insight_id:
                    return insight
        return None
    
    def get_insights_by_priority(self, priority: Priority) -> List[Insight]:
        """Get all insights of a specific priority level"""
        filtered_insights = []
        for insights_list in self.insights_cache.values():
            filtered_insights.extend([i for i in insights_list if i.priority == priority])
        return filtered_insights
    
    def get_active_insights(self) -> List[Insight]:
        """Get all insights that haven't expired"""
        now = datetime.now()
        active_insights = []
        
        for insights_list in self.insights_cache.values():
            for insight in insights_list:
                if insight.expires_at is None or insight.expires_at > now:
                    active_insights.append(insight)
        
        return sorted(active_insights, key=lambda x: (x.priority.value, -x.confidence), reverse=True)