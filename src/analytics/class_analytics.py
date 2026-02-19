"""
Class Analytics Module

Provides comprehensive class-wide performance metrics and teacher effectiveness insights.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import statistics
from collections import defaultdict, Counter

from .student_analytics import StudentAnalytics, StudySession, DifficultyLevel


class RiskLevel(Enum):
    """Risk levels for student identification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TeachingApproach:
    """Represents a teaching approach/method"""
    approach_id: str
    name: str
    description: str
    subjects: List[str]
    difficulty_levels: List[DifficultyLevel]


@dataclass
class ClassPerformanceMetric:
    """Class performance metrics for a specific topic/subject"""
    subject: str
    topic: str
    avg_score: float
    median_score: float
    completion_rate: float
    student_count: int
    struggle_count: int  # Students scoring below threshold
    date_range: Tuple[datetime, datetime]


@dataclass
class AtRiskStudent:
    """Information about a student identified as at-risk"""
    student_id: str
    risk_level: RiskLevel
    risk_factors: List[str]
    recent_performance_trend: str  # declining, stable, improving
    engagement_score: float
    recommended_interventions: List[str]
    last_active: datetime


class ClassAnalytics:
    """
    Comprehensive analytics for class-wide performance and teacher effectiveness.
    """
    
    def __init__(self, class_id: str, teacher_id: str):
        self.class_id = class_id
        self.teacher_id = teacher_id
        self.student_analytics: Dict[str, StudentAnalytics] = {}
        self.teaching_approaches: List[TeachingApproach] = []
        self.national_benchmarks: Dict[str, float] = {}  # Subject -> average score
        self._cache = {}
    
    def add_student(self, student_analytics: StudentAnalytics):
        """Add a student's analytics to the class"""
        self.student_analytics[student_analytics.student_id] = student_analytics
        self._invalidate_cache()
    
    def add_teaching_approach(self, approach: TeachingApproach):
        """Add a teaching approach used by the teacher"""
        self.teaching_approaches.append(approach)
        self._invalidate_cache()
    
    def set_national_benchmarks(self, benchmarks: Dict[str, float]):
        """Set national average benchmarks for comparison"""
        self.national_benchmarks = benchmarks
        self._invalidate_cache()
    
    def _invalidate_cache(self):
        """Clear cached calculations when new data is added"""
        self._cache.clear()
    
    def get_performance_heatmap(self, days_back: int = 30) -> Dict[str, Dict[str, ClassPerformanceMetric]]:
        """
        Generate class-wide performance heatmap showing which topics students are struggling with.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dict mapping subject -> topic -> performance metrics
        """
        cache_key = f"performance_heatmap_{days_back}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        heatmap = defaultdict(lambda: defaultdict(list))
        
        # Collect all sessions for analysis
        for student_id, analytics in self.student_analytics.items():
            for session in analytics.sessions:
                if session.start_time >= cutoff_date and session.score is not None:
                    heatmap[session.subject][session.topic].append({
                        'student_id': student_id,
                        'score': session.score,
                        'completion_rate': session.completion_rate,
                        'date': session.start_time
                    })
        
        # Calculate metrics for each topic
        performance_metrics = {}
        for subject, topics in heatmap.items():
            performance_metrics[subject] = {}
            
            for topic, sessions in topics.items():
                if sessions:
                    scores = [s['score'] for s in sessions]
                    completion_rates = [s['completion_rate'] for s in sessions]
                    dates = [s['date'] for s in sessions]
                    
                    avg_score = np.mean(scores)
                    struggle_threshold = 70  # Students scoring below 70% are struggling
                    struggle_count = sum(1 for score in scores if score < struggle_threshold)
                    
                    metric = ClassPerformanceMetric(
                        subject=subject,
                        topic=topic,
                        avg_score=avg_score,
                        median_score=np.median(scores),
                        completion_rate=np.mean(completion_rates),
                        student_count=len(set(s['student_id'] for s in sessions)),
                        struggle_count=struggle_count,
                        date_range=(min(dates), max(dates))
                    )
                    
                    performance_metrics[subject][topic] = metric
        
        self._cache[cache_key] = performance_metrics
        return performance_metrics
    
    def identify_at_risk_students(self, days_back: int = 21) -> List[AtRiskStudent]:
        """
        Identify students who are at risk based on declining engagement and performance.
        
        Args:
            days_back: Number of days to analyze for trends
            
        Returns:
            List of at-risk students with risk factors and recommendations
        """
        cache_key = f"at_risk_students_{days_back}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        at_risk_students = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for student_id, analytics in self.student_analytics.items():
            risk_factors = []
            risk_score = 0
            
            # Check engagement score
            engagement = analytics.calculate_engagement_score()
            if engagement['overall'] < 0.4:
                risk_factors.append("Low engagement score")
                risk_score += 2
            elif engagement['overall'] < 0.6:
                risk_factors.append("Moderate engagement concerns")
                risk_score += 1
            
            # Check recent performance trend
            recent_sessions = [s for s in analytics.sessions 
                             if s.start_time >= cutoff_date and s.score is not None]
            
            if len(recent_sessions) < 3:
                risk_factors.append("Insufficient recent activity")
                risk_score += 3
                trend = "inactive"
            else:
                # Analyze performance trend
                recent_scores = [s.score for s in recent_sessions[-5:]]
                if len(recent_scores) >= 3:
                    # Simple trend analysis
                    first_half_avg = np.mean(recent_scores[:len(recent_scores)//2])
                    second_half_avg = np.mean(recent_scores[len(recent_scores)//2:])
                    
                    if second_half_avg < first_half_avg - 10:
                        risk_factors.append("Declining performance trend")
                        risk_score += 2
                        trend = "declining"
                    elif second_half_avg > first_half_avg + 5:
                        trend = "improving"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"
            
            # Check retention rate
            retention = analytics.get_retention_rate(days_back)
            if retention:
                avg_retention = np.mean(list(retention.values()))
                if avg_retention < 0.5:
                    risk_factors.append("Poor retention rate")
                    risk_score += 2
                elif avg_retention < 0.7:
                    risk_factors.append("Moderate retention concerns")
                    risk_score += 1
            
            # Check last activity
            if analytics.sessions:
                last_session = max(analytics.sessions, key=lambda s: s.start_time)
                days_since_last = (datetime.now() - last_session.start_time).days
                
                if days_since_last > 7:
                    risk_factors.append(f"No activity for {days_since_last} days")
                    risk_score += min(days_since_last // 3, 4)
                
                last_active = last_session.start_time
            else:
                risk_factors.append("No recorded sessions")
                risk_score += 5
                last_active = datetime.min
            
            # Determine risk level and recommendations
            if risk_score >= 6:
                risk_level = RiskLevel.CRITICAL
                recommendations = [
                    "Schedule immediate one-on-one meeting",
                    "Contact parents/guardians",
                    "Develop personalized intervention plan",
                    "Consider additional support resources"
                ]
            elif risk_score >= 4:
                risk_level = RiskLevel.HIGH
                recommendations = [
                    "Schedule weekly check-ins",
                    "Provide additional practice materials",
                    "Consider peer tutoring",
                    "Monitor closely for next 2 weeks"
                ]
            elif risk_score >= 2:
                risk_level = RiskLevel.MEDIUM
                recommendations = [
                    "Increase engagement with interactive content",
                    "Provide encouragement and positive feedback",
                    "Check understanding of recent topics"
                ]
            else:
                risk_level = RiskLevel.LOW
                recommendations = ["Continue current approach", "Monitor periodically"]
            
            # Only include students with medium risk or higher
            if risk_level != RiskLevel.LOW or risk_score > 0:
                at_risk_student = AtRiskStudent(
                    student_id=student_id,
                    risk_level=risk_level,
                    risk_factors=risk_factors,
                    recent_performance_trend=trend,
                    engagement_score=engagement['overall'],
                    recommended_interventions=recommendations,
                    last_active=last_active
                )
                at_risk_students.append(at_risk_student)
        
        # Sort by risk level and score
        risk_order = {RiskLevel.CRITICAL: 4, RiskLevel.HIGH: 3, RiskLevel.MEDIUM: 2, RiskLevel.LOW: 1}
        at_risk_students.sort(key=lambda x: risk_order[x.risk_level], reverse=True)
        
        self._cache[cache_key] = at_risk_students
        return at_risk_students
    
    def get_comparative_analytics(self) -> Dict[str, Dict[str, float]]:
        """
        Compare class performance vs national averages.
        
        Returns:
            Comparative metrics showing how class performs relative to benchmarks
        """
        if 'comparative_analytics' in self._cache:
            return self._cache['comparative_analytics']
        
        comparison = {}
        
        if not self.national_benchmarks:
            return {'error': 'No national benchmarks available for comparison'}
        
        # Calculate class averages by subject
        subject_scores = defaultdict(list)
        
        for analytics in self.student_analytics.values():
            for session in analytics.sessions:
                if session.score is not None:
                    subject_scores[session.subject].append(session.score)
        
        # Compare with national benchmarks
        for subject, scores in subject_scores.items():
            if subject in self.national_benchmarks and scores:
                class_avg = np.mean(scores)
                national_avg = self.national_benchmarks[subject]
                
                comparison[subject] = {
                    'class_average': round(class_avg, 2),
                    'national_average': round(national_avg, 2),
                    'difference': round(class_avg - national_avg, 2),
                    'performance_ratio': round(class_avg / national_avg, 3),
                    'percentile_estimate': self._estimate_percentile(class_avg, national_avg),
                    'student_count': len(set(analytics.student_id for analytics in self.student_analytics.values())),
                    'sessions_analyzed': len(scores)
                }
        
        self._cache['comparative_analytics'] = comparison
        return comparison
    
    def _estimate_percentile(self, class_avg: float, national_avg: float) -> int:
        """Rough percentile estimation based on difference from national average"""
        ratio = class_avg / national_avg
        if ratio >= 1.2:
            return 85
        elif ratio >= 1.1:
            return 75
        elif ratio >= 1.05:
            return 65
        elif ratio >= 0.95:
            return 50
        elif ratio >= 0.9:
            return 35
        elif ratio >= 0.8:
            return 25
        else:
            return 15
    
    def analyze_teacher_effectiveness(self) -> Dict[str, float]:
        """
        Analyze teacher effectiveness based on various metrics.
        
        Returns:
            Teacher effectiveness scores and insights
        """
        if 'teacher_effectiveness' in self._cache:
            return self._cache['teacher_effectiveness']
        
        effectiveness = {}
        
        if not self.student_analytics:
            return {'error': 'No student data available for analysis'}
        
        # Student engagement metric
        engagement_scores = []
        for analytics in self.student_analytics.values():
            engagement = analytics.calculate_engagement_score()
            engagement_scores.append(engagement['overall'])
        
        if engagement_scores:
            effectiveness['student_engagement'] = round(np.mean(engagement_scores), 3)
        
        # Learning velocity metric
        velocity_scores = []
        for analytics in self.student_analytics.values():
            velocities = analytics.get_learning_velocity()
            if velocities:
                avg_velocity = np.mean(list(velocities.values()))
                velocity_scores.append(avg_velocity)
        
        if velocity_scores:
            effectiveness['learning_velocity'] = round(np.mean(velocity_scores), 3)
        
        # Retention effectiveness
        retention_scores = []
        for analytics in self.student_analytics.values():
            retention = analytics.get_retention_rate()
            if retention:
                avg_retention = np.mean(list(retention.values()))
                retention_scores.append(avg_retention)
        
        if retention_scores:
            effectiveness['retention_effectiveness'] = round(np.mean(retention_scores), 3)
        
        # At-risk prevention (inverse of at-risk percentage)
        at_risk = self.identify_at_risk_students()
        high_risk_count = sum(1 for student in at_risk if student.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL])
        total_students = len(self.student_analytics)
        
        if total_students > 0:
            at_risk_prevention = 1 - (high_risk_count / total_students)
            effectiveness['at_risk_prevention'] = round(at_risk_prevention, 3)
        
        # Overall effectiveness score
        if effectiveness:
            scores = [v for v in effectiveness.values() if isinstance(v, (int, float))]
            if scores:
                effectiveness['overall_score'] = round(np.mean(scores), 3)
        
        # Teaching approach effectiveness
        if self.teaching_approaches:
            approach_effectiveness = self._analyze_teaching_approaches()
            effectiveness['teaching_approaches'] = approach_effectiveness
        
        self._cache['teacher_effectiveness'] = effectiveness
        return effectiveness
    
    def _analyze_teaching_approaches(self) -> Dict[str, Dict]:
        """Analyze the effectiveness of different teaching approaches"""
        approach_results = {}
        
        # This would require more detailed session data linking to specific teaching approaches
        # For now, provide a framework
        for approach in self.teaching_approaches:
            # Placeholder analysis - in real implementation, this would correlate
            # specific teaching approaches with student outcomes
            approach_results[approach.name] = {
                'subjects_used': approach.subjects,
                'difficulty_levels': [dl.value for dl in approach.difficulty_levels],
                'effectiveness_score': 0.75,  # Placeholder
                'recommendation': "Continue using this approach"
            }
        
        return approach_results
    
    def analyze_resource_utilization(self) -> Dict[str, Dict]:
        """
        Analyze which content and resources get used most effectively.
        
        Returns:
            Resource utilization metrics and insights
        """
        if 'resource_utilization' in self._cache:
            return self._cache['resource_utilization']
        
        utilization = {
            'content_usage': defaultdict(lambda: {'sessions': 0, 'students': set(), 'avg_score': 0, 'scores': []}),
            'interaction_types': defaultdict(lambda: {'sessions': 0, 'avg_score': 0, 'scores': []}),
            'difficulty_levels': defaultdict(lambda: {'sessions': 0, 'avg_score': 0, 'scores': []})
        }
        
        # Analyze content usage
        for analytics in self.student_analytics.values():
            for session in analytics.sessions:
                content_key = f"{session.subject}_{session.topic}"
                
                # Content usage
                utilization['content_usage'][content_key]['sessions'] += 1
                utilization['content_usage'][content_key]['students'].add(session.student_id)
                if session.score is not None:
                    utilization['content_usage'][content_key]['scores'].append(session.score)
                
                # Interaction types
                if session.score is not None:
                    utilization['interaction_types'][session.interaction_type]['sessions'] += 1
                    utilization['interaction_types'][session.interaction_type]['scores'].append(session.score)
                
                # Difficulty levels
                utilization['difficulty_levels'][session.difficulty_level.value]['sessions'] += 1
                if session.score is not None:
                    utilization['difficulty_levels'][session.difficulty_level.value]['scores'].append(session.score)
        
        # Calculate averages and format results
        result = {
            'most_used_content': {},
            'most_effective_content': {},
            'interaction_effectiveness': {},
            'difficulty_effectiveness': {}
        }
        
        # Most used content
        content_by_usage = sorted(
            utilization['content_usage'].items(),
            key=lambda x: x[1]['sessions'],
            reverse=True
        )[:10]
        
        for content, data in content_by_usage:
            avg_score = np.mean(data['scores']) if data['scores'] else 0
            result['most_used_content'][content] = {
                'sessions': data['sessions'],
                'unique_students': len(data['students']),
                'avg_score': round(avg_score, 2)
            }
        
        # Most effective content (by score)
        content_by_effectiveness = [
            (content, data) for content, data in utilization['content_usage'].items()
            if len(data['scores']) >= 3  # Minimum sessions for reliability
        ]
        content_by_effectiveness.sort(key=lambda x: np.mean(x[1]['scores']), reverse=True)
        
        for content, data in content_by_effectiveness[:10]:
            avg_score = np.mean(data['scores'])
            result['most_effective_content'][content] = {
                'sessions': data['sessions'],
                'unique_students': len(data['students']),
                'avg_score': round(avg_score, 2)
            }
        
        # Interaction type effectiveness
        for interaction_type, data in utilization['interaction_types'].items():
            if data['scores']:
                result['interaction_effectiveness'][interaction_type] = {
                    'sessions': data['sessions'],
                    'avg_score': round(np.mean(data['scores']), 2),
                    'score_std': round(np.std(data['scores']), 2)
                }
        
        # Difficulty level effectiveness
        for difficulty, data in utilization['difficulty_levels'].items():
            if data['scores']:
                result['difficulty_effectiveness'][f"Level_{difficulty}"] = {
                    'sessions': data['sessions'],
                    'avg_score': round(np.mean(data['scores']), 2),
                    'score_std': round(np.std(data['scores']), 2)
                }
        
        self._cache['resource_utilization'] = result
        return result
    
    def get_comprehensive_class_report(self) -> Dict:
        """
        Generate a comprehensive analytics report for the class.
        
        Returns:
            Complete class analytics report
        """
        return {
            'class_id': self.class_id,
            'teacher_id': self.teacher_id,
            'generated_at': datetime.now().isoformat(),
            'total_students': len(self.student_analytics),
            'performance_heatmap': self.get_performance_heatmap(),
            'at_risk_students': [
                {
                    'student_id': student.student_id,
                    'risk_level': student.risk_level.value,
                    'risk_factors': student.risk_factors,
                    'engagement_score': student.engagement_score,
                    'recommendations': student.recommended_interventions[:3]  # Top 3 recommendations
                } 
                for student in self.identify_at_risk_students()
            ],
            'comparative_analytics': self.get_comparative_analytics(),
            'teacher_effectiveness': self.analyze_teacher_effectiveness(),
            'resource_utilization': self.analyze_resource_utilization(),
            'class_summary': self._generate_class_summary()
        }
    
    def _generate_class_summary(self) -> Dict:
        """Generate a summary of key class metrics"""
        if not self.student_analytics:
            return {'error': 'No student data available'}
        
        all_scores = []
        all_engagement = []
        
        for analytics in self.student_analytics.values():
            # Collect scores
            for session in analytics.sessions:
                if session.score is not None:
                    all_scores.append(session.score)
            
            # Collect engagement
            engagement = analytics.calculate_engagement_score()
            all_engagement.append(engagement['overall'])
        
        summary = {
            'total_students': len(self.student_analytics),
            'total_sessions': sum(len(a.sessions) for a in self.student_analytics.values())
        }
        
        if all_scores:
            summary.update({
                'avg_class_score': round(np.mean(all_scores), 2),
                'median_class_score': round(np.median(all_scores), 2),
                'score_std_dev': round(np.std(all_scores), 2)
            })
        
        if all_engagement:
            summary.update({
                'avg_engagement': round(np.mean(all_engagement), 3),
                'engagement_std_dev': round(np.std(all_engagement), 3)
            })
        
        return summary