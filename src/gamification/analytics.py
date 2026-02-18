"""Engagement Analytics for EduAGI Gamification.

Comprehensive analytics system for tracking engagement, retention,
churn prediction, and A/B testing for gamification features.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import statistics
from collections import defaultdict

from sqlalchemy import and_, func, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User, StudentProfile, LearningEvent
from src.models.database import get_db

logger = logging.getLogger(__name__)


class EngagementLevel(Enum):
    VERY_LOW = "very_low"      # < 5 minutes/week
    LOW = "low"                # 5-30 minutes/week
    MODERATE = "moderate"      # 30-120 minutes/week
    HIGH = "high"              # 2-5 hours/week
    VERY_HIGH = "very_high"    # > 5 hours/week


class ChurnRisk(Enum):
    LOW = "low"               # Active, engaged user
    MEDIUM = "medium"         # Some warning signs
    HIGH = "high"             # At risk of leaving
    CRITICAL = "critical"     # Likely to churn soon


class ExperimentStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class RetentionMetrics:
    """Calculates and tracks user retention metrics."""
    
    @staticmethod
    async def calculate_dau_mau(db: AsyncSession, date_range: int = 30) -> Dict:
        """Calculate Daily Active Users and Monthly Active Users."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=date_range)
        
        # Daily Active Users (last 24 hours)
        dau_query = await db.execute(
            db.query(distinct(LearningEvent.student_id))
            .filter(LearningEvent.created_at >= end_date - timedelta(days=1))
        )
        dau = len(dau_query.all())
        
        # Monthly Active Users (last 30 days)
        mau_query = await db.execute(
            db.query(distinct(LearningEvent.student_id))
            .filter(LearningEvent.created_at >= end_date - timedelta(days=30))
        )
        mau = len(mau_query.all())
        
        # Weekly Active Users (last 7 days)
        wau_query = await db.execute(
            db.query(distinct(LearningEvent.student_id))
            .filter(LearningEvent.created_at >= end_date - timedelta(days=7))
        )
        wau = len(wau_query.all())
        
        # Calculate ratios
        dau_mau_ratio = (dau / mau) if mau > 0 else 0
        wau_mau_ratio = (wau / mau) if mau > 0 else 0
        
        return {
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "dau_mau_ratio": dau_mau_ratio,
            "wau_mau_ratio": wau_mau_ratio,
            "calculation_date": end_date.isoformat()
        }
    
    @staticmethod
    async def calculate_retention_cohorts(db: AsyncSession, period_days: int = 7) -> Dict:
        """Calculate cohort retention analysis."""
        # Get users by registration week
        users_query = await db.execute(
            db.query(User.id, User.created_at)
            .filter(User.created_at >= datetime.utcnow() - timedelta(days=90))  # Last 3 months
            .order_by(User.created_at)
        )
        users = users_query.all()
        
        # Group users into cohorts by week
        cohorts = defaultdict(list)
        for user in users:
            week_start = user.created_at - timedelta(days=user.created_at.weekday())
            cohorts[week_start.date()].append(user.id)
        
        # Calculate retention for each cohort
        cohort_retention = {}
        
        for cohort_date, user_ids in cohorts.items():
            if len(user_ids) < 5:  # Skip small cohorts
                continue
                
            cohort_start = datetime.combine(cohort_date, datetime.min.time())
            retention_periods = {}
            
            # Check retention at 1, 7, 14, 30 days
            for days in [1, 7, 14, 30]:
                period_start = cohort_start + timedelta(days=days)
                period_end = period_start + timedelta(days=period_days)
                
                # Count users who were active in this period
                active_query = await db.execute(
                    db.query(distinct(LearningEvent.student_id))
                    .filter(and_(
                        LearningEvent.student_id.in_(user_ids),
                        LearningEvent.created_at >= period_start,
                        LearningEvent.created_at < period_end
                    ))
                )
                active_users = len(active_query.all())
                
                retention_rate = (active_users / len(user_ids)) * 100
                retention_periods[f"day_{days}"] = {
                    "active_users": active_users,
                    "retention_rate": retention_rate
                }
            
            cohort_retention[cohort_date.isoformat()] = {
                "total_users": len(user_ids),
                "periods": retention_periods
            }
        
        return {
            "cohorts": cohort_retention,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def calculate_session_metrics(db: AsyncSession, days: int = 30) -> Dict:
        """Calculate session length and frequency metrics."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all learning events in the period
        events_query = await db.execute(
            db.query(LearningEvent.student_id, LearningEvent.created_at, LearningEvent.data)
            .filter(LearningEvent.created_at >= start_date)
            .order_by(LearningEvent.student_id, LearningEvent.created_at)
        )
        events = events_query.all()
        
        # Group events by user and calculate sessions
        user_sessions = defaultdict(list)
        current_session = None
        
        for event in events:
            if (current_session is None or 
                current_session['user_id'] != event.student_id or
                (event.created_at - current_session['last_activity']).seconds > 1800):  # 30 min gap = new session
                
                if current_session:
                    user_sessions[current_session['user_id']].append(current_session)
                
                current_session = {
                    'user_id': event.student_id,
                    'start_time': event.created_at,
                    'last_activity': event.created_at,
                    'event_count': 1,
                    'study_minutes': event.data.get('study_minutes', 0) if event.data else 0
                }
            else:
                current_session['last_activity'] = event.created_at
                current_session['event_count'] += 1
                current_session['study_minutes'] += event.data.get('study_minutes', 0) if event.data else 0
        
        # Add last session
        if current_session:
            user_sessions[current_session['user_id']].append(current_session)
        
        # Calculate metrics
        all_session_lengths = []
        all_session_frequencies = []
        
        for user_id, sessions in user_sessions.items():
            session_lengths = [(s['last_activity'] - s['start_time']).seconds / 60 for s in sessions]  # minutes
            all_session_lengths.extend(session_lengths)
            all_session_frequencies.append(len(sessions))
        
        if all_session_lengths:
            avg_session_length = statistics.mean(all_session_lengths)
            median_session_length = statistics.median(all_session_lengths)
        else:
            avg_session_length = median_session_length = 0
        
        if all_session_frequencies:
            avg_sessions_per_user = statistics.mean(all_session_frequencies)
        else:
            avg_sessions_per_user = 0
        
        return {
            "total_sessions": len(all_session_lengths),
            "active_users": len(user_sessions),
            "avg_session_length_minutes": round(avg_session_length, 2),
            "median_session_length_minutes": round(median_session_length, 2),
            "avg_sessions_per_user": round(avg_sessions_per_user, 2),
            "analysis_period_days": days
        }


class EngagementScoring:
    """Calculates engagement scores for students."""
    
    def __init__(self):
        self.weights = {
            'study_time': 0.3,
            'consistency': 0.25,
            'social_activity': 0.2,
            'progress': 0.15,
            'gamification_usage': 0.1
        }
    
    async def calculate_engagement_score(self, db: AsyncSession, user_id: str, days: int = 30) -> Dict:
        """Calculate comprehensive engagement score for a user."""
        profile = await db.get(StudentProfile, user_id)
        if not profile:
            return {"error": "User not found"}
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get user's learning events in the period
        events_query = await db.execute(
            db.query(LearningEvent)
            .filter(and_(
                LearningEvent.student_id == user_id,
                LearningEvent.created_at >= start_date
            ))
            .order_by(LearningEvent.created_at)
        )
        events = events_query.all()
        
        # Calculate component scores
        components = {}
        components['study_time'] = self._calculate_study_time_score(events, days)
        components['consistency'] = self._calculate_consistency_score(events, days, profile)
        components['social_activity'] = self._calculate_social_score(events, profile)
        components['progress'] = self._calculate_progress_score(events, profile)
        components['gamification_usage'] = self._calculate_gamification_score(events, profile)
        
        # Calculate weighted total score
        total_score = sum(
            components[component] * self.weights[component]
            for component in components
        )
        
        # Determine engagement level
        engagement_level = self._determine_engagement_level(total_score, components)
        
        return {
            "user_id": user_id,
            "total_score": round(total_score, 2),
            "engagement_level": engagement_level.value,
            "components": {k: round(v, 2) for k, v in components.items()},
            "analysis_period_days": days,
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    def _calculate_study_time_score(self, events: List[LearningEvent], days: int) -> float:
        """Calculate score based on study time (0-100)."""
        total_minutes = 0
        for event in events:
            if event.data and 'study_minutes' in event.data:
                total_minutes += event.data['study_minutes']
        
        # Score based on minutes per day
        minutes_per_day = total_minutes / days
        
        # Target: 30 minutes/day = 100 points
        score = min((minutes_per_day / 30) * 100, 100)
        return score
    
    def _calculate_consistency_score(self, events: List[LearningEvent], days: int, profile: StudentProfile) -> float:
        """Calculate score based on learning consistency (0-100)."""
        if not events:
            return 0
        
        # Count unique days with activity
        active_dates = set(event.created_at.date() for event in events)
        active_days = len(active_dates)
        
        # Consistency score based on percentage of days active
        consistency_ratio = active_days / days
        
        # Bonus for current streak
        streak_bonus = min(profile.streak_days * 2, 20)  # Up to 20 bonus points
        
        score = min(consistency_ratio * 80 + streak_bonus, 100)
        return score
    
    def _calculate_social_score(self, events: List[LearningEvent], profile: StudentProfile) -> float:
        """Calculate score based on social learning activity (0-100)."""
        social_events = [
            e for e in events 
            if e.event_type in ['group_joined', 'help_provided', 'challenge_completed']
        ]
        
        # Base score from social events
        social_score = min(len(social_events) * 10, 60)
        
        # Bonus for being in study groups
        groups = profile.preferences.get('study_groups', [])
        group_bonus = min(len(groups) * 15, 30)
        
        # Bonus for being a tutor
        if profile.preferences.get('tutor_profile'):
            tutor_bonus = 10
        else:
            tutor_bonus = 0
        
        score = min(social_score + group_bonus + tutor_bonus, 100)
        return score
    
    def _calculate_progress_score(self, events: List[LearningEvent], profile: StudentProfile) -> float:
        """Calculate score based on learning progress (0-100)."""
        lesson_completions = len([e for e in events if e.event_type == 'lesson_complete'])
        achievement_events = len([e for e in events if e.event_type == 'achievement_earned'])
        
        # Score based on completions and achievements
        completion_score = min(lesson_completions * 5, 70)
        achievement_score = min(achievement_events * 15, 30)
        
        score = completion_score + achievement_score
        return min(score, 100)
    
    def _calculate_gamification_score(self, events: List[LearningEvent], profile: StudentProfile) -> float:
        """Calculate score based on gamification feature usage (0-100)."""
        gamification_events = [
            e for e in events 
            if e.event_type in ['xp_awarded', 'power_up_used', 'coin_transaction']
        ]
        
        # Base score from gamification interactions
        interaction_score = min(len(gamification_events) * 3, 60)
        
        # Bonus for having power-ups or cosmetic items
        inventory = profile.preferences.get('inventory', {})
        item_bonus = 0
        for category in ['avatar_frames', 'themes', 'voice_styles']:
            item_bonus += min(len(inventory.get(category, [])) * 5, 15)
        
        # Bonus for coin balance (shows engagement with economy)
        coin_balance = profile.preferences.get('educoins', 0)
        coin_bonus = min(coin_balance / 100, 25)  # 1 point per 100 coins, max 25
        
        score = min(interaction_score + item_bonus + coin_bonus, 100)
        return score
    
    def _determine_engagement_level(self, score: float, components: Dict) -> EngagementLevel:
        """Determine engagement level based on total score."""
        if score >= 80:
            return EngagementLevel.VERY_HIGH
        elif score >= 60:
            return EngagementLevel.HIGH
        elif score >= 40:
            return EngagementLevel.MODERATE
        elif score >= 20:
            return EngagementLevel.LOW
        else:
            return EngagementLevel.VERY_LOW


class ChurnPredictor:
    """Predicts which students are at risk of churning."""
    
    def __init__(self):
        self.risk_factors = {
            'days_since_last_activity': {'weight': 0.25, 'thresholds': [3, 7, 14, 30]},
            'declining_session_frequency': {'weight': 0.2, 'thresholds': [0.5, 0.3, 0.1, 0]},
            'low_engagement_score': {'weight': 0.2, 'thresholds': [60, 40, 25, 15]},
            'streak_broken': {'weight': 0.15, 'thresholds': [False, True, True, True]},
            'no_social_activity': {'weight': 0.1, 'thresholds': [5, 2, 1, 0]},
            'unused_power_ups': {'weight': 0.1, 'thresholds': [0, 3, 5, 10]}
        }
    
    async def predict_churn_risk(self, db: AsyncSession, user_id: str) -> Dict:
        """Predict churn risk for a specific user."""
        profile = await db.get(StudentProfile, user_id)
        if not profile:
            return {"error": "User not found"}
        
        # Calculate risk factors
        risk_scores = {}
        risk_reasons = []
        
        # Days since last activity
        if profile.last_study_date:
            days_inactive = (datetime.utcnow() - profile.last_study_date).days
            risk_scores['days_since_last_activity'] = self._calculate_risk_score(
                'days_since_last_activity', days_inactive
            )
            if days_inactive > 7:
                risk_reasons.append(f"Inactive for {days_inactive} days")
        else:
            risk_scores['days_since_last_activity'] = 100  # Never studied = high risk
            risk_reasons.append("No learning activity recorded")
        
        # Get recent engagement data
        engagement_scorer = EngagementScoring()
        engagement_data = await engagement_scorer.calculate_engagement_score(db, user_id, 14)
        
        if not engagement_data.get('error'):
            engagement_score = engagement_data['total_score']
            risk_scores['low_engagement_score'] = self._calculate_risk_score(
                'low_engagement_score', engagement_score, reverse=True
            )
            
            if engagement_score < 30:
                risk_reasons.append(f"Low engagement score ({engagement_score:.1f})")
        
        # Streak analysis
        current_streak = profile.streak_days
        if current_streak == 0:
            # Check if streak was recently broken
            recent_events = await db.execute(
                db.query(LearningEvent)
                .filter(and_(
                    LearningEvent.student_id == user_id,
                    LearningEvent.created_at >= datetime.utcnow() - timedelta(days=7)
                ))
                .limit(10)
            )
            
            has_recent_activity = len(recent_events.all()) > 0
            risk_scores['streak_broken'] = 75 if has_recent_activity else 25
            
            if has_recent_activity:
                risk_reasons.append("Learning streak broken")
        else:
            risk_scores['streak_broken'] = 0
        
        # Social activity analysis
        social_events = await db.execute(
            db.query(LearningEvent)
            .filter(and_(
                LearningEvent.student_id == user_id,
                LearningEvent.event_type.in_(['group_joined', 'help_provided', 'challenge_completed']),
                LearningEvent.created_at >= datetime.utcnow() - timedelta(days=30)
            ))
        )
        social_activity_count = len(social_events.all())
        risk_scores['no_social_activity'] = self._calculate_risk_score(
            'no_social_activity', social_activity_count, reverse=True
        )
        
        if social_activity_count == 0:
            risk_reasons.append("No social learning activity")
        
        # Power-up usage (indicates engagement with gamification)
        inventory = profile.preferences.get('inventory', {})
        unused_power_ups = inventory.get('power_ups', {})
        total_unused = sum(unused_power_ups.values())
        risk_scores['unused_power_ups'] = self._calculate_risk_score(
            'unused_power_ups', total_unused
        )
        
        if total_unused > 5:
            risk_reasons.append("Accumulating unused power-ups")
        
        # Calculate overall risk score
        total_risk = sum(
            risk_scores[factor] * self.risk_factors[factor]['weight']
            for factor in risk_scores
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(total_risk)
        
        return {
            "user_id": user_id,
            "risk_level": risk_level.value,
            "risk_score": round(total_risk, 2),
            "risk_factors": {k: round(v, 2) for k, v in risk_scores.items()},
            "risk_reasons": risk_reasons,
            "calculated_at": datetime.utcnow().isoformat()
        }
    
    async def get_at_risk_users(self, db: AsyncSession, limit: int = 50) -> List[Dict]:
        """Get list of users at risk of churning."""
        # Get users who were active in the past but not recently
        cutoff_date = datetime.utcnow() - timedelta(days=3)
        
        at_risk_query = await db.execute(
            db.query(StudentProfile)
            .join(User, StudentProfile.user_id == User.id)
            .filter(and_(
                User.is_active == True,
                or_(
                    StudentProfile.last_study_date < cutoff_date,
                    StudentProfile.last_study_date.is_(None)
                )
            ))
            .limit(limit * 2)  # Get more than needed for filtering
        )
        
        profiles = at_risk_query.all()
        at_risk_users = []
        
        for profile in profiles:
            risk_data = await self.predict_churn_risk(db, profile.user_id)
            
            if (not risk_data.get('error') and 
                risk_data['risk_level'] in ['high', 'critical']):
                
                user = await db.get(User, profile.user_id)
                if user:
                    at_risk_users.append({
                        "user_id": profile.user_id,
                        "name": user.name,
                        "email": user.email,
                        "risk_level": risk_data['risk_level'],
                        "risk_score": risk_data['risk_score'],
                        "primary_risks": risk_data['risk_reasons'][:3],  # Top 3 reasons
                        "last_activity": profile.last_study_date.isoformat() if profile.last_study_date else None
                    })
        
        # Sort by risk score (highest first)
        at_risk_users.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return at_risk_users[:limit]
    
    def _calculate_risk_score(self, factor: str, value: float, reverse: bool = False) -> float:
        """Calculate risk score for a specific factor."""
        thresholds = self.risk_factors[factor]['thresholds']
        
        if reverse:
            # For factors where lower values = higher risk
            thresholds = sorted(thresholds, reverse=True)
        
        for i, threshold in enumerate(thresholds):
            if (not reverse and value >= threshold) or (reverse and value <= threshold):
                return (i / (len(thresholds) - 1)) * 100
        
        return 100  # Highest risk if beyond all thresholds
    
    def _determine_risk_level(self, risk_score: float) -> ChurnRisk:
        """Determine risk level based on overall score."""
        if risk_score >= 75:
            return ChurnRisk.CRITICAL
        elif risk_score >= 50:
            return ChurnRisk.HIGH
        elif risk_score >= 25:
            return ChurnRisk.MEDIUM
        else:
            return ChurnRisk.LOW


class ABTesting:
    """A/B testing framework for gamification experiments."""
    
    async def create_experiment(self, db: AsyncSession, creator_id: str, experiment_data: Dict) -> Dict:
        """Create a new A/B test experiment."""
        # Validate experiment data
        required_fields = ['name', 'description', 'variants', 'success_metric']
        for field in required_fields:
            if not experiment_data.get(field):
                return {"error": f"Missing required field: {field}"}
        
        experiment_id = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        experiment = {
            "id": experiment_id,
            "name": experiment_data['name'],
            "description": experiment_data['description'],
            "creator_id": creator_id,
            "variants": experiment_data['variants'],  # [{"name": "control", "config": {}}, {"name": "variant_a", "config": {}}]
            "success_metric": experiment_data['success_metric'],  # e.g., "engagement_score", "retention_rate"
            "target_audience": experiment_data.get('target_audience', {}),  # User filtering criteria
            "traffic_allocation": experiment_data.get('traffic_allocation', 50),  # % of users in experiment
            "status": ExperimentStatus.DRAFT.value,
            "start_date": experiment_data.get('start_date'),
            "end_date": experiment_data.get('end_date'),
            "created_at": datetime.utcnow().isoformat(),
            "participants": {},  # {user_id: variant_name}
            "results": {"conversion_data": {}, "statistical_significance": None}
        }
        
        # Store experiment (in real app, this would be a separate table)
        creator_profile = await db.get(StudentProfile, creator_id)
        if creator_profile:
            experiments = creator_profile.preferences.get('ab_experiments', [])
            experiments.append(experiment)
            creator_profile.preferences = {
                **creator_profile.preferences,
                'ab_experiments': experiments
            }
            await db.commit()
        
        return {"experiment": experiment, "success": True}
    
    async def assign_user_to_experiment(self, db: AsyncSession, user_id: str, experiment_id: str) -> Optional[str]:
        """Assign a user to an experiment variant."""
        experiment = await self._get_experiment(db, experiment_id)
        
        if (not experiment or 
            experiment['status'] != ExperimentStatus.ACTIVE.value or
            user_id in experiment['participants']):
            return None
        
        # Check if user meets target audience criteria
        if not await self._user_meets_criteria(db, user_id, experiment['target_audience']):
            return None
        
        # Randomly assign to variant based on traffic allocation
        import hashlib
        hash_input = f"{experiment_id}_{user_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
        
        # Simple hash-based assignment for consistency
        variant_index = hash_value % len(experiment['variants'])
        assigned_variant = experiment['variants'][variant_index]['name']
        
        # Update experiment with new participant
        experiment['participants'][user_id] = assigned_variant
        await self._update_experiment(db, experiment)
        
        return assigned_variant
    
    async def track_experiment_event(self, db: AsyncSession, user_id: str, event_type: str, event_data: Dict):
        """Track an event for A/B test analysis."""
        # Find all experiments the user is participating in
        user_experiments = await self._get_user_experiments(db, user_id)
        
        for experiment in user_experiments:
            if experiment['status'] == ExperimentStatus.ACTIVE.value:
                variant = experiment['participants'][user_id]
                
                # Check if this event is relevant to the experiment's success metric
                if self._is_relevant_event(event_type, experiment['success_metric']):
                    # Store the event for analysis
                    event_key = f"{experiment['id']}_{user_id}_{event_type}"
                    
                    # In a real implementation, you'd store this in a dedicated events table
                    # For now, we'll add it to the experiment data
                    if 'events' not in experiment:
                        experiment['events'] = []
                    
                    experiment['events'].append({
                        'user_id': user_id,
                        'variant': variant,
                        'event_type': event_type,
                        'event_data': event_data,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
                    await self._update_experiment(db, experiment)
    
    async def analyze_experiment_results(self, db: AsyncSession, experiment_id: str) -> Dict:
        """Analyze A/B test results and calculate statistical significance."""
        experiment = await self._get_experiment(db, experiment_id)
        if not experiment:
            return {"error": "Experiment not found"}
        
        events = experiment.get('events', [])
        if not events:
            return {"error": "No events to analyze"}
        
        # Group events by variant
        variant_data = defaultdict(lambda: {'users': set(), 'conversions': 0, 'total_events': 0})
        
        for event in events:
            variant = event['variant']
            user_id = event['user_id']
            variant_data[variant]['users'].add(user_id)
            variant_data[variant]['total_events'] += 1
            
            # Count conversions based on success metric
            if self._is_conversion_event(event, experiment['success_metric']):
                variant_data[variant]['conversions'] += 1
        
        # Calculate conversion rates
        results = {}
        for variant, data in variant_data.items():
            total_users = len(data['users'])
            conversion_rate = (data['conversions'] / total_users) if total_users > 0 else 0
            
            results[variant] = {
                'total_users': total_users,
                'total_events': data['total_events'],
                'conversions': data['conversions'],
                'conversion_rate': round(conversion_rate * 100, 2)
            }
        
        # Calculate statistical significance (simplified)
        significance = self._calculate_statistical_significance(results)
        
        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment['name'],
            "results": results,
            "statistical_significance": significance,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def _calculate_statistical_significance(self, results: Dict) -> Dict:
        """Calculate statistical significance between variants (simplified)."""
        if len(results) != 2:
            return {"error": "Statistical significance calculation requires exactly 2 variants"}
        
        variants = list(results.keys())
        control = results[variants[0]]
        treatment = results[variants[1]]
        
        # Simple z-test for proportions (in real implementation, use proper statistical library)
        p1 = control['conversion_rate'] / 100
        p2 = treatment['conversion_rate'] / 100
        n1 = control['total_users']
        n2 = treatment['total_users']
        
        if n1 < 30 or n2 < 30:
            return {"error": "Insufficient sample size for significance testing"}
        
        # Pooled proportion
        p_pool = (control['conversions'] + treatment['conversions']) / (n1 + n2)
        
        # Standard error
        se = (p_pool * (1 - p_pool) * (1/n1 + 1/n2)) ** 0.5
        
        if se == 0:
            return {"significant": False, "confidence": 0, "note": "No variance in results"}
        
        # Z-score
        z_score = abs(p2 - p1) / se
        
        # Simplified significance levels
        if z_score >= 2.58:  # 99% confidence
            confidence = 99
        elif z_score >= 1.96:  # 95% confidence
            confidence = 95
        elif z_score >= 1.65:  # 90% confidence
            confidence = 90
        else:
            confidence = 0
        
        return {
            "significant": confidence >= 95,
            "confidence_level": confidence,
            "z_score": round(z_score, 3),
            "effect_size": round((p2 - p1) * 100, 2),  # Percentage point difference
            "winner": variants[1] if p2 > p1 else variants[0]
        }
    
    async def _get_experiment(self, db: AsyncSession, experiment_id: str) -> Optional[Dict]:
        """Get experiment by ID."""
        # Search through profiles for the experiment (simplified)
        profiles_query = db.query(StudentProfile).filter(
            StudentProfile.preferences['ab_experiments'].astext.contains(experiment_id)
        )
        
        profiles = await db.execute(profiles_query)
        
        for profile in profiles.all():
            experiments = profile.preferences.get('ab_experiments', [])
            for experiment in experiments:
                if experiment['id'] == experiment_id:
                    return experiment
        
        return None
    
    async def _update_experiment(self, db: AsyncSession, updated_experiment: Dict):
        """Update experiment data."""
        experiment_id = updated_experiment['id']
        creator_id = updated_experiment['creator_id']
        
        profile = await db.get(StudentProfile, creator_id)
        if profile:
            experiments = profile.preferences.get('ab_experiments', [])
            for i, experiment in enumerate(experiments):
                if experiment['id'] == experiment_id:
                    experiments[i] = updated_experiment
                    break
            
            profile.preferences = {
                **profile.preferences,
                'ab_experiments': experiments
            }
    
    async def _get_user_experiments(self, db: AsyncSession, user_id: str) -> List[Dict]:
        """Get all experiments a user is participating in."""
        all_experiments = []
        
        # This is a simplified search - in production, use proper indexing
        profiles_query = db.query(StudentProfile).filter(
            StudentProfile.preferences['ab_experiments'].astext.contains(user_id)
        )
        
        profiles = await db.execute(profiles_query)
        
        for profile in profiles.all():
            experiments = profile.preferences.get('ab_experiments', [])
            for experiment in experiments:
                if user_id in experiment.get('participants', {}):
                    all_experiments.append(experiment)
        
        return all_experiments
    
    async def _user_meets_criteria(self, db: AsyncSession, user_id: str, criteria: Dict) -> bool:
        """Check if user meets experiment target audience criteria."""
        if not criteria:
            return True  # No criteria = all users eligible
        
        profile = await db.get(StudentProfile, user_id)
        if not profile:
            return False
        
        # Check various criteria
        if 'min_level' in criteria:
            user_level = profile.preferences.get('total_xp', 0) // 100  # Simplified level calculation
            if user_level < criteria['min_level']:
                return False
        
        if 'subjects' in criteria:
            user_subjects = set(profile.strengths or []) | set(profile.weaknesses or [])
            required_subjects = set(criteria['subjects'])
            if not user_subjects & required_subjects:  # No overlap
                return False
        
        return True
    
    def _is_relevant_event(self, event_type: str, success_metric: str) -> bool:
        """Check if an event type is relevant to the experiment's success metric."""
        relevant_events = {
            'engagement_score': ['lesson_complete', 'xp_awarded', 'achievement_earned'],
            'retention_rate': ['lesson_complete', 'daily_activity'],
            'social_engagement': ['group_joined', 'help_provided', 'challenge_completed'],
            'gamification_usage': ['power_up_used', 'coin_transaction', 'achievement_earned']
        }
        
        return event_type in relevant_events.get(success_metric, [])
    
    def _is_conversion_event(self, event: Dict, success_metric: str) -> bool:
        """Determine if an event counts as a conversion for the success metric."""
        event_type = event['event_type']
        
        conversion_events = {
            'engagement_score': ['lesson_complete', 'achievement_earned'],
            'retention_rate': ['daily_activity'],
            'social_engagement': ['group_joined', 'help_provided'],
            'gamification_usage': ['power_up_used', 'achievement_earned']
        }
        
        return event_type in conversion_events.get(success_metric, [])


class EngagementAnalytics:
    """Main analytics coordinator that brings together all analytics features."""
    
    def __init__(self):
        self.retention_metrics = RetentionMetrics()
        self.engagement_scoring = EngagementScoring()
        self.churn_predictor = ChurnPredictor()
        self.ab_testing = ABTesting()
    
    async def generate_comprehensive_report(self, db: AsyncSession, days: int = 30) -> Dict:
        """Generate a comprehensive engagement analytics report."""
        report = {
            "report_period_days": days,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Overall metrics
        report["retention_metrics"] = await self.retention_metrics.calculate_dau_mau(db, days)
        report["session_metrics"] = await self.retention_metrics.calculate_session_metrics(db, days)
        
        # At-risk users
        at_risk_users = await self.churn_predictor.get_at_risk_users(db, 20)
        report["churn_analysis"] = {
            "total_at_risk_users": len(at_risk_users),
            "critical_risk_count": len([u for u in at_risk_users if u['risk_level'] == 'critical']),
            "high_risk_count": len([u for u in at_risk_users if u['risk_level'] == 'high']),
            "top_at_risk_users": at_risk_users[:5]  # Top 5 for summary
        }
        
        # Engagement distribution
        # In a real implementation, you'd sample users or use aggregated data
        engagement_distribution = {
            "very_high": 0, "high": 0, "moderate": 0, "low": 0, "very_low": 0
        }
        
        # Sample recent users for engagement analysis
        recent_users_query = await db.execute(
            db.query(distinct(LearningEvent.student_id))
            .filter(LearningEvent.created_at >= datetime.utcnow() - timedelta(days=days))
            .limit(100)  # Sample for performance
        )
        recent_users = [row[0] for row in recent_users_query.all()]
        
        for user_id in recent_users[:50]:  # Analyze subset for performance
            engagement_data = await self.engagement_scoring.calculate_engagement_score(db, user_id, days)
            if not engagement_data.get('error'):
                level = engagement_data['engagement_level']
                engagement_distribution[level] += 1
        
        report["engagement_distribution"] = engagement_distribution
        
        return report
    
    async def get_user_insights(self, db: AsyncSession, user_id: str, days: int = 30) -> Dict:
        """Get comprehensive insights for a specific user."""
        insights = {"user_id": user_id, "analysis_period_days": days}
        
        # Engagement analysis
        engagement_data = await self.engagement_scoring.calculate_engagement_score(db, user_id, days)
        insights["engagement"] = engagement_data
        
        # Churn risk analysis
        churn_data = await self.churn_predictor.predict_churn_risk(db, user_id)
        insights["churn_risk"] = churn_data
        
        # Recommendations based on analysis
        recommendations = []
        
        if not engagement_data.get('error'):
            if engagement_data['engagement_level'] in ['low', 'very_low']:
                recommendations.append("Consider offering streak freeze power-ups to re-engage")
            
            components = engagement_data.get('components', {})
            if components.get('social_activity', 0) < 30:
                recommendations.append("Encourage joining study groups for peer support")
            if components.get('consistency', 0) < 50:
                recommendations.append("Send daily reminders to build study habits")
        
        if not churn_data.get('error') and churn_data['risk_level'] in ['high', 'critical']:
            recommendations.append("Priority intervention needed - at high risk of churning")
        
        insights["recommendations"] = recommendations
        
        return insights