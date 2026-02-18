"""
EduAGI Gamification System

A comprehensive gamification package featuring:
- XP and leveling system
- Achievement system with 20+ badges
- Social features (study groups, leaderboards, peer tutoring)
- Rewards system with EduCoins and power-ups
- Variable ratio reward scheduling for psychological engagement
"""

# Core XP & Level System
from .engine import (
    XPManager,
    StreakTracker, 
    DailyChallenge,
    XPSource,
    LevelTier,
    XPEvent
)

# Achievement System
from .achievements import (
    AchievementEngine,
    Achievement,
    AchievementProgress,
    AchievementCategory,
    AchievementRarity
)

# Social Features
from .social import (
    StudyGroupManager,
    StudyGroup,
    StudyGroupMember,
    StudyGroupRole,
    Leaderboard,
    LeaderboardEntry,
    LeaderboardScope,
    PeerTutoringMatcher,
    PeerTutoringRequest,
    ActivityFeed,
    ActivityFeedItem,
    ActivityType,
    SocialGamificationManager
)

# Rewards System
from .rewards import (
    RewardsManager,
    Currency,
    UnlockableItem,
    PowerUp,
    ActivePowerUp,
    CurrencyType,
    ItemType,
    PowerUpType,
    RewardTrigger,
    VariableRatioScheduler
)

# Main gamification class that integrates everything
class GamificationEngine:
    """
    Main gamification engine that coordinates all systems
    """
    
    def __init__(self):
        self.xp_manager = XPManager()
        self.streak_tracker = StreakTracker()
        self.daily_challenge = DailyChallenge()
        self.achievement_engine = AchievementEngine()
        self.social_manager = SocialGamificationManager()
        self.rewards_manager = RewardsManager()
        
        # Connect achievement notifications to reward system
        self.achievement_engine.add_notification_hook(self._on_achievement_unlocked)
        
    def _on_achievement_unlocked(self, user_id: str, achievement: Achievement, progress: AchievementProgress):
        """Handle achievement unlock notifications"""
        # Award currency for achievement
        currency_rewards = {
            AchievementRarity.COMMON: (CurrencyType.EDUCOINS, 50),
            AchievementRarity.UNCOMMON: (CurrencyType.EDUCOINS, 100),
            AchievementRarity.RARE: (CurrencyType.EDUCOINS, 200),
            AchievementRarity.EPIC: (CurrencyType.GEMS, 1),
            AchievementRarity.LEGENDARY: (CurrencyType.GEMS, 3)
        }
        
        currency_type, amount = currency_rewards.get(achievement.rarity, (CurrencyType.EDUCOINS, 50))
        self.rewards_manager.award_currency(user_id, currency_type, amount, f"Achievement: {achievement.name}")
        
        # Trigger social activity
        self.social_manager.handle_user_event(
            user_id, "user", "achievement_unlocked", 
            {'achievement_name': achievement.name, 'achievement_id': achievement.id}
        )
        
    def complete_lesson(self, user_id: str, lesson_data: dict) -> dict:
        """
        Handle lesson completion - awards XP, checks achievements, triggers rewards
        """
        username = lesson_data.get('username', 'Student')
        
        # Award XP
        xp_result = self.xp_manager.award_xp(user_id, XPSource.LESSON_COMPLETE)
        
        # Update streak
        streak_result = self.streak_tracker.update_streak(user_id)
        
        # Check achievements
        newly_unlocked = self.achievement_engine.check_achievement_triggers(
            user_id, 'lesson_completed', lesson_data
        )
        
        # Check level-based achievements if level up occurred
        if xp_result['level_up']:
            level_achievements = self.achievement_engine.check_achievement_triggers(
                user_id, 'level_gained', {'new_level': xp_result['new_level']}
            )
            newly_unlocked.extend(level_achievements)
            
        # Check streak achievements
        streak_achievements = self.achievement_engine.check_achievement_triggers(
            user_id, 'streak_updated', streak_result
        )
        newly_unlocked.extend(streak_achievements)
        
        # Trigger reward drops
        lesson_reward = self.rewards_manager.trigger_reward_drop(user_id, RewardTrigger.LESSON_COMPLETE)
        level_reward = None
        
        if xp_result['level_up']:
            level_reward = self.rewards_manager.trigger_reward_drop(user_id, RewardTrigger.LEVEL_UP)
            
        # Update social activity
        self.social_manager.handle_user_event(
            user_id, username, 'lesson_completed', 
            {**lesson_data, 'xp_earned': xp_result['xp_awarded']}
        )
        
        if xp_result['level_up']:
            self.social_manager.handle_user_event(
                user_id, username, 'level_up',
                {'new_level': xp_result['new_level'], 'new_title': xp_result['new_title']}
            )
            
        return {
            'xp': xp_result,
            'streak': streak_result, 
            'achievements': newly_unlocked,
            'rewards': {
                'lesson_reward': lesson_reward,
                'level_reward': level_reward
            }
        }
        
    def daily_login(self, user_id: str) -> dict:
        """Handle daily login rewards"""
        login_reward = self.rewards_manager.trigger_reward_drop(user_id, RewardTrigger.DAILY_LOGIN)
        
        return {
            'login_reward': login_reward,
            'streak_info': self.streak_tracker.get_streak(user_id),
            'daily_challenge': self.daily_challenge.get_today_challenge()
        }
        
    def complete_daily_challenge(self, user_id: str, username: str = "Student") -> dict:
        """Handle daily challenge completion"""
        # Award XP
        xp_result = self.xp_manager.award_xp(user_id, XPSource.DAILY_CHALLENGE)
        
        # Mark challenge as complete
        challenge_result = self.daily_challenge.complete_challenge(user_id)
        
        # Check achievements
        newly_unlocked = self.achievement_engine.check_achievement_triggers(
            user_id, 'daily_challenge_completed', challenge_result
        )
        
        # Trigger rewards
        reward = self.rewards_manager.trigger_reward_drop(user_id, RewardTrigger.CHALLENGE_COMPLETE)
        
        # Update social activity
        self.social_manager.handle_user_event(
            user_id, username, 'completed_challenge',
            {'xp_earned': xp_result['xp_awarded']}
        )
        
        return {
            'xp': xp_result,
            'challenge': challenge_result,
            'achievements': newly_unlocked,
            'reward': reward
        }
        
    def get_user_dashboard(self, user_id: str) -> dict:
        """Get comprehensive user dashboard data"""
        user_stats = self.xp_manager.get_user_stats(user_id)
        streak_info = self.streak_tracker.get_streak(user_id)
        achievements = self.achievement_engine.get_user_achievements(user_id)
        social_dashboard = self.social_manager.get_social_dashboard(user_id)
        inventory = self.rewards_manager.get_user_inventory(user_id)
        active_power_ups = self.rewards_manager.get_active_power_ups(user_id)
        today_challenge = self.daily_challenge.get_today_challenge()
        
        return {
            'user_stats': user_stats,
            'streak': streak_info,
            'achievements': achievements,
            'social': social_dashboard,
            'inventory': inventory,
            'active_power_ups': active_power_ups,
            'daily_challenge': {
                'challenge': today_challenge,
                'completed': self.daily_challenge.is_completed(user_id)
            }
        }

# Export the main engine for easy access
__all__ = [
    'GamificationEngine',
    'XPManager', 'StreakTracker', 'DailyChallenge', 'XPSource', 'LevelTier',
    'AchievementEngine', 'Achievement', 'AchievementCategory', 'AchievementRarity',
    'StudyGroupManager', 'StudyGroup', 'Leaderboard', 'PeerTutoringMatcher', 'ActivityFeed',
    'RewardsManager', 'Currency', 'UnlockableItem', 'PowerUp', 'CurrencyType', 'PowerUpType'
]