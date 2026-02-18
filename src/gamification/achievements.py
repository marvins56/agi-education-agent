"""
Achievement system with 20+ badges and notification hooks for EduAGI
"""

import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import json


class AchievementCategory(Enum):
    """Categories of achievements"""
    PROGRESS = "progress"
    STREAKS = "streaks"
    SOCIAL = "social"
    MASTERY = "mastery"
    TIME_BASED = "time_based"
    SPECIAL = "special"


class AchievementRarity(Enum):
    """Achievement rarity levels"""
    COMMON = ("Common", "#8B5A3C")
    UNCOMMON = ("Uncommon", "#4CAF50") 
    RARE = ("Rare", "#2196F3")
    EPIC = ("Epic", "#9C27B0")
    LEGENDARY = ("Legendary", "#FF9800")


@dataclass
class Achievement:
    """Achievement definition"""
    id: str
    name: str
    description: str
    category: AchievementCategory
    rarity: AchievementRarity
    icon: str = "🏆"
    hidden: bool = False  # Hidden until unlocked
    prerequisites: List[str] = field(default_factory=list)  # Other achievement IDs required
    points: int = 10  # Base points for unlocking
    
    def __post_init__(self):
        # Adjust points based on rarity
        rarity_multipliers = {
            AchievementRarity.COMMON: 1,
            AchievementRarity.UNCOMMON: 2,
            AchievementRarity.RARE: 3,
            AchievementRarity.EPIC: 5,
            AchievementRarity.LEGENDARY: 10
        }
        self.points *= rarity_multipliers[self.rarity]


@dataclass 
class AchievementProgress:
    """User's progress toward an achievement"""
    achievement_id: str
    user_id: str
    progress: float = 0.0  # 0.0 to 1.0
    unlocked: bool = False
    unlock_date: Optional[datetime.datetime] = None
    metadata: Dict = field(default_factory=dict)


class AchievementEngine:
    """Core achievement system with checking and notifications"""
    
    def __init__(self):
        self.achievements = self._initialize_achievements()
        self.user_progress: Dict[str, Dict[str, AchievementProgress]] = {}  # user_id -> achievement_id -> progress
        self.notification_hooks: List[Callable] = []
        
    def _initialize_achievements(self) -> Dict[str, Achievement]:
        """Initialize all 20+ achievements"""
        achievements = [
            # PROGRESS Achievements
            Achievement(
                id="first_steps",
                name="First Steps", 
                description="Complete your first lesson",
                category=AchievementCategory.PROGRESS,
                rarity=AchievementRarity.COMMON,
                icon="👶"
            ),
            Achievement(
                id="quick_learner",
                name="Quick Learner",
                description="Reach level 5",
                category=AchievementCategory.PROGRESS,
                rarity=AchievementRarity.COMMON,
                icon="🚀"
            ),
            Achievement(
                id="knowledge_seeker",
                name="Knowledge Seeker", 
                description="Reach level 15",
                category=AchievementCategory.PROGRESS,
                rarity=AchievementRarity.UNCOMMON,
                icon="📚"
            ),
            Achievement(
                id="scholar_rising",
                name="Scholar Rising",
                description="Reach level 30",
                category=AchievementCategory.PROGRESS,
                rarity=AchievementRarity.RARE,
                icon="🎓"
            ),
            Achievement(
                id="master_student",
                name="Master Student",
                description="Reach level 60",
                category=AchievementCategory.PROGRESS,
                rarity=AchievementRarity.EPIC,
                icon="🏆"
            ),
            Achievement(
                id="sage_wisdom",
                name="Sage Wisdom",
                description="Reach the maximum level 100",
                category=AchievementCategory.PROGRESS,
                rarity=AchievementRarity.LEGENDARY,
                icon="🧙‍♂️"
            ),
            
            # STREAKS Achievements
            Achievement(
                id="consistent_student",
                name="Consistent Student",
                description="Study for 3 days in a row",
                category=AchievementCategory.STREAKS,
                rarity=AchievementRarity.COMMON,
                icon="📅"
            ),
            Achievement(
                id="seven_day_streak",
                name="7-Day Streak",
                description="Study for 7 consecutive days",
                category=AchievementCategory.STREAKS,
                rarity=AchievementRarity.UNCOMMON,
                icon="🔥"
            ),
            Achievement(
                id="dedication",
                name="Dedication",
                description="Study for 30 consecutive days",
                category=AchievementCategory.STREAKS,
                rarity=AchievementRarity.RARE,
                icon="💪"
            ),
            Achievement(
                id="unstoppable",
                name="Unstoppable",
                description="Study for 100 consecutive days",
                category=AchievementCategory.STREAKS,
                rarity=AchievementRarity.LEGENDARY,
                icon="⚡"
            ),
            
            # TIME-BASED Achievements
            Achievement(
                id="night_owl",
                name="Night Owl",
                description="Study after 10 PM",
                category=AchievementCategory.TIME_BASED,
                rarity=AchievementRarity.UNCOMMON,
                icon="🦉"
            ),
            Achievement(
                id="early_bird",
                name="Early Bird", 
                description="Study before 7 AM",
                category=AchievementCategory.TIME_BASED,
                rarity=AchievementRarity.UNCOMMON,
                icon="🐦"
            ),
            Achievement(
                id="weekend_warrior",
                name="Weekend Warrior",
                description="Study on weekends for 4 weeks straight",
                category=AchievementCategory.TIME_BASED,
                rarity=AchievementRarity.RARE,
                icon="⚔️"
            ),
            
            # MASTERY Achievements  
            Achievement(
                id="speed_demon",
                name="Speed Demon",
                description="Complete a lesson in under 5 minutes",
                category=AchievementCategory.MASTERY,
                rarity=AchievementRarity.UNCOMMON,
                icon="💨"
            ),
            Achievement(
                id="perfect_score",
                name="Perfect Score",
                description="Get 100% on 5 assessments",
                category=AchievementCategory.MASTERY,
                rarity=AchievementRarity.RARE,
                icon="🌟"
            ),
            Achievement(
                id="comeback_kid", 
                name="Comeback Kid",
                description="Improve from failing grade to A+",
                category=AchievementCategory.MASTERY,
                rarity=AchievementRarity.EPIC,
                icon="📈"
            ),
            Achievement(
                id="problem_crusher",
                name="Problem Crusher",
                description="Solve 10 hard problems in one session",
                category=AchievementCategory.MASTERY,
                rarity=AchievementRarity.EPIC,
                icon="🔨"
            ),
            
            # SOCIAL Achievements
            Achievement(
                id="helping_hand",
                name="Helping Hand",
                description="Help 5 fellow students",
                category=AchievementCategory.SOCIAL,
                rarity=AchievementRarity.UNCOMMON,
                icon="🤝"
            ),
            Achievement(
                id="mentor",
                name="Mentor",
                description="Help 25 fellow students",
                category=AchievementCategory.SOCIAL,
                rarity=AchievementRarity.RARE,
                icon="👨‍🏫"
            ),
            Achievement(
                id="community_leader",
                name="Community Leader",
                description="Be in top 3 of class leaderboard for 30 days",
                category=AchievementCategory.SOCIAL,
                rarity=AchievementRarity.EPIC,
                icon="👑"
            ),
            
            # SPECIAL Achievements
            Achievement(
                id="challenger",
                name="Daily Challenger",
                description="Complete 10 daily challenges",
                category=AchievementCategory.SPECIAL,
                rarity=AchievementRarity.UNCOMMON,
                icon="⚡"
            ),
            Achievement(
                id="explorer",
                name="Topic Explorer", 
                description="Study 15 different subjects",
                category=AchievementCategory.SPECIAL,
                rarity=AchievementRarity.RARE,
                icon="🗺️"
            ),
            Achievement(
                id="overachiever",
                name="Overachiever",
                description="Earn 10,000 XP in one week", 
                category=AchievementCategory.SPECIAL,
                rarity=AchievementRarity.EPIC,
                icon="🚀"
            ),
            Achievement(
                id="resilient",
                name="Resilient",
                description="Return to studying after 30-day break",
                category=AchievementCategory.SPECIAL,
                rarity=AchievementRarity.RARE,
                icon="🌱"
            ),
            Achievement(
                id="perfectionist",
                name="Perfectionist",
                description="Complete 50 lessons with 100% accuracy",
                category=AchievementCategory.SPECIAL,
                rarity=AchievementRarity.LEGENDARY,
                icon="💎"
            ),
            Achievement(
                id="iron_will",
                name="Iron Will",
                description="Study for 365 consecutive days - The ultimate dedication achievement",
                category=AchievementCategory.STREAKS,
                rarity=AchievementRarity.LEGENDARY,
                icon="🛡️",
                hidden=True
            )
        ]
        
        return {ach.id: ach for ach in achievements}
        
    def add_notification_hook(self, hook: Callable[[str, Achievement, AchievementProgress], None]):
        """Add a notification hook for achievement unlocks"""
        self.notification_hooks.append(hook)
        
    def _notify_achievement_unlocked(self, user_id: str, achievement: Achievement, progress: AchievementProgress):
        """Notify all hooks of achievement unlock"""
        for hook in self.notification_hooks:
            try:
                hook(user_id, achievement, progress)
            except Exception as e:
                print(f"Error in achievement notification hook: {e}")
                
    def get_user_progress(self, user_id: str, achievement_id: str) -> AchievementProgress:
        """Get user's progress for a specific achievement"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
            
        if achievement_id not in self.user_progress[user_id]:
            self.user_progress[user_id][achievement_id] = AchievementProgress(
                achievement_id=achievement_id,
                user_id=user_id
            )
            
        return self.user_progress[user_id][achievement_id]
        
    def update_progress(self, user_id: str, achievement_id: str, progress: float, metadata: Dict = None) -> bool:
        """Update user's progress toward an achievement. Returns True if newly unlocked."""
        if achievement_id not in self.achievements:
            return False
            
        user_progress = self.get_user_progress(user_id, achievement_id)
        achievement = self.achievements[achievement_id]
        
        # Update progress
        old_progress = user_progress.progress
        user_progress.progress = min(progress, 1.0)
        
        if metadata:
            user_progress.metadata.update(metadata)
            
        # Check if achievement is now unlocked
        if not user_progress.unlocked and user_progress.progress >= 1.0:
            # Check prerequisites
            if self._check_prerequisites(user_id, achievement):
                user_progress.unlocked = True
                user_progress.unlock_date = datetime.datetime.now()
                
                # Notify hooks
                self._notify_achievement_unlocked(user_id, achievement, user_progress)
                return True
                
        return False
        
    def _check_prerequisites(self, user_id: str, achievement: Achievement) -> bool:
        """Check if user has met all prerequisites for achievement"""
        for prereq_id in achievement.prerequisites:
            prereq_progress = self.get_user_progress(user_id, prereq_id)
            if not prereq_progress.unlocked:
                return False
        return True
        
    def check_achievement_triggers(self, user_id: str, event_type: str, event_data: Dict) -> List[str]:
        """Check if any achievements should be triggered by an event. Returns list of newly unlocked achievement IDs."""
        newly_unlocked = []
        
        # Define achievement checking logic based on event types
        checkers = {
            'lesson_completed': self._check_lesson_achievements,
            'level_gained': self._check_level_achievements, 
            'streak_updated': self._check_streak_achievements,
            'assessment_completed': self._check_mastery_achievements,
            'daily_challenge_completed': self._check_special_achievements,
            'peer_helped': self._check_social_achievements,
            'study_session_time': self._check_time_achievements,
            'xp_gained': self._check_xp_achievements
        }
        
        if event_type in checkers:
            results = checkers[event_type](user_id, event_data)
            newly_unlocked.extend(results)
            
        return newly_unlocked
        
    def _check_lesson_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check lesson-related achievements"""
        newly_unlocked = []
        
        # First Steps - complete first lesson
        if self.update_progress(user_id, 'first_steps', 1.0):
            newly_unlocked.append('first_steps')
            
        # Speed Demon - complete in under 5 minutes
        if event_data.get('duration_minutes', 999) < 5:
            if self.update_progress(user_id, 'speed_demon', 1.0):
                newly_unlocked.append('speed_demon')
                
        # Track perfect lessons for Perfectionist
        if event_data.get('accuracy', 0) >= 100:
            current_progress = self.get_user_progress(user_id, 'perfectionist')
            perfect_lessons = current_progress.metadata.get('perfect_lessons', 0) + 1
            progress = min(perfect_lessons / 50, 1.0)
            
            if self.update_progress(user_id, 'perfectionist', progress, 
                                 {'perfect_lessons': perfect_lessons}):
                newly_unlocked.append('perfectionist')
                
        return newly_unlocked
        
    def _check_level_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check level-related achievements"""
        newly_unlocked = []
        level = event_data.get('new_level', 0)
        
        level_achievements = [
            ('quick_learner', 5),
            ('knowledge_seeker', 15), 
            ('scholar_rising', 30),
            ('master_student', 60),
            ('sage_wisdom', 100)
        ]
        
        for ach_id, required_level in level_achievements:
            if level >= required_level:
                if self.update_progress(user_id, ach_id, 1.0):
                    newly_unlocked.append(ach_id)
                    
        return newly_unlocked
        
    def _check_streak_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check streak-related achievements"""
        newly_unlocked = []
        streak = event_data.get('current_streak', 0)
        
        streak_achievements = [
            ('consistent_student', 3),
            ('seven_day_streak', 7),
            ('dedication', 30),
            ('unstoppable', 100),
            ('iron_will', 365)
        ]
        
        for ach_id, required_streak in streak_achievements:
            if streak >= required_streak:
                if self.update_progress(user_id, ach_id, 1.0):
                    newly_unlocked.append(ach_id)
                    
        return newly_unlocked
        
    def _check_mastery_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check mastery/assessment achievements"""
        newly_unlocked = []
        
        # Perfect Score - get 100% on 5 assessments
        if event_data.get('score', 0) >= 100:
            current_progress = self.get_user_progress(user_id, 'perfect_score')
            perfect_scores = current_progress.metadata.get('perfect_scores', 0) + 1
            progress = min(perfect_scores / 5, 1.0)
            
            if self.update_progress(user_id, 'perfect_score', progress,
                                 {'perfect_scores': perfect_scores}):
                newly_unlocked.append('perfect_score')
                
        # Comeback Kid - improve from failing to A+
        prev_grade = event_data.get('previous_grade', 'A')
        current_grade = event_data.get('current_grade', 'F')
        
        if prev_grade in ['F', 'D'] and current_grade == 'A+':
            if self.update_progress(user_id, 'comeback_kid', 1.0):
                newly_unlocked.append('comeback_kid')
                
        return newly_unlocked
        
    def _check_social_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check social achievements"""
        newly_unlocked = []
        
        # Helping Hand & Mentor - help other students
        current_progress = self.get_user_progress(user_id, 'helping_hand')
        helps_given = current_progress.metadata.get('helps_given', 0) + 1
        
        # Helping Hand - 5 helps
        if self.update_progress(user_id, 'helping_hand', min(helps_given / 5, 1.0),
                              {'helps_given': helps_given}):
            newly_unlocked.append('helping_hand')
            
        # Mentor - 25 helps  
        if self.update_progress(user_id, 'mentor', min(helps_given / 25, 1.0),
                              {'helps_given': helps_given}):
            newly_unlocked.append('mentor')
            
        return newly_unlocked
        
    def _check_time_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check time-based achievements"""
        newly_unlocked = []
        study_time = event_data.get('study_time', datetime.datetime.now())
        
        # Night Owl - study after 10 PM
        if study_time.hour >= 22:
            if self.update_progress(user_id, 'night_owl', 1.0):
                newly_unlocked.append('night_owl')
                
        # Early Bird - study before 7 AM
        if study_time.hour < 7:
            if self.update_progress(user_id, 'early_bird', 1.0):
                newly_unlocked.append('early_bird')
                
        return newly_unlocked
        
    def _check_special_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check special achievements"""
        newly_unlocked = []
        
        # Daily Challenger
        current_progress = self.get_user_progress(user_id, 'challenger')
        challenges_completed = current_progress.metadata.get('challenges_completed', 0) + 1
        progress = min(challenges_completed / 10, 1.0)
        
        if self.update_progress(user_id, 'challenger', progress,
                              {'challenges_completed': challenges_completed}):
            newly_unlocked.append('challenger')
            
        return newly_unlocked
        
    def _check_xp_achievements(self, user_id: str, event_data: Dict) -> List[str]:
        """Check XP-related achievements"""
        newly_unlocked = []
        
        # Overachiever - 10,000 XP in one week
        current_progress = self.get_user_progress(user_id, 'overachiever')
        week_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        week_start -= datetime.timedelta(days=week_start.weekday())
        
        # This would need integration with XP tracking to work properly
        # For now, just a placeholder implementation
        
        return newly_unlocked
        
    def get_user_achievements(self, user_id: str) -> Dict:
        """Get all achievements and progress for a user"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
            
        achievements_data = {}
        unlocked_count = 0
        total_points = 0
        
        for ach_id, achievement in self.achievements.items():
            progress = self.get_user_progress(user_id, ach_id)
            
            # Don't show hidden achievements until unlocked
            if achievement.hidden and not progress.unlocked:
                continue
                
            achievements_data[ach_id] = {
                'achievement': achievement,
                'progress': progress.progress,
                'unlocked': progress.unlocked,
                'unlock_date': progress.unlock_date,
                'points': achievement.points if progress.unlocked else 0
            }
            
            if progress.unlocked:
                unlocked_count += 1
                total_points += achievement.points
                
        return {
            'achievements': achievements_data,
            'unlocked_count': unlocked_count,
            'total_achievements': len([a for a in self.achievements.values() if not a.hidden]),
            'total_points': total_points,
            'completion_percentage': unlocked_count / len(self.achievements) * 100
        }
        
    def get_recent_achievements(self, user_id: str, days: int = 7) -> List[Dict]:
        """Get recently unlocked achievements for user"""
        if user_id not in self.user_progress:
            return []
            
        recent_achievements = []
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        for ach_id, progress in self.user_progress[user_id].items():
            if (progress.unlocked and progress.unlock_date and 
                progress.unlock_date >= cutoff_date):
                
                achievement = self.achievements[ach_id]
                recent_achievements.append({
                    'achievement': achievement,
                    'unlock_date': progress.unlock_date,
                    'points': achievement.points
                })
                
        # Sort by unlock date (most recent first)
        recent_achievements.sort(key=lambda x: x['unlock_date'], reverse=True)
        return recent_achievements