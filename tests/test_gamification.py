"""
Comprehensive tests for EduAGI gamification system
"""

import pytest
import datetime
from unittest.mock import Mock, patch

from src.gamification import (
    GamificationEngine,
    XPManager, StreakTracker, DailyChallenge, XPSource, LevelTier,
    AchievementEngine, Achievement, AchievementCategory, AchievementRarity,
    StudyGroupManager, StudyGroup, StudyGroupRole,
    Leaderboard, LeaderboardScope, LeaderboardEntry,
    PeerTutoringMatcher, ActivityFeed, ActivityType,
    RewardsManager, CurrencyType, PowerUpType, RewardTrigger
)


class TestXPManager:
    """Test XP management and leveling system"""
    
    def setup_method(self):
        self.xp_manager = XPManager()
        self.user_id = "test_user_123"
        
    def test_award_xp(self):
        """Test awarding XP to user"""
        result = self.xp_manager.award_xp(self.user_id, XPSource.LESSON_COMPLETE)
        
        assert result['xp_awarded'] == 50
        assert result['total_xp'] == 50
        assert result['previous_level'] == 1
        assert result['new_level'] == 1
        assert result['level_up'] is False
        
    def test_level_up(self):
        """Test level up functionality"""
        # Award enough XP to level up (level 2 requires ~141 XP based on formula)
        for _ in range(5):  # 5 * 50 = 250 XP, should reach level 2
            self.xp_manager.award_xp(self.user_id, XPSource.LESSON_COMPLETE)
            
        result = self.xp_manager.award_xp(self.user_id, XPSource.HARD_PROBLEM)
        
        assert result['level_up'] is True
        assert result['new_level'] > result['previous_level']
        assert result['new_title'] is not None
        
    def test_get_level_from_xp(self):
        """Test level calculation from XP amount"""
        level = self.xp_manager.get_level(0)
        assert level == 1
        
        level = self.xp_manager.get_level(1000)
        assert level > 1
        
    def test_get_title(self):
        """Test title assignment based on level"""
        assert self.xp_manager.get_title(5) == "Beginner"
        assert self.xp_manager.get_title(15) == "Explorer"
        assert self.xp_manager.get_title(30) == "Scholar"
        assert self.xp_manager.get_title(60) == "Master"
        assert self.xp_manager.get_title(90) == "Sage"
        
    def test_xp_to_next_level(self):
        """Test XP needed for next level calculation"""
        self.xp_manager.award_xp(self.user_id, XPSource.LESSON_COMPLETE)
        needed, progress = self.xp_manager.get_xp_to_next_level(self.user_id)
        
        assert needed > 0
        assert progress == 50  # XP earned so far in level
        
    def test_user_stats(self):
        """Test comprehensive user statistics"""
        # Award different types of XP
        self.xp_manager.award_xp(self.user_id, XPSource.LESSON_COMPLETE)
        self.xp_manager.award_xp(self.user_id, XPSource.HARD_PROBLEM)
        self.xp_manager.award_xp(self.user_id, XPSource.PEER_HELP)
        
        stats = self.xp_manager.get_user_stats(self.user_id)
        
        assert stats['user_id'] == self.user_id
        assert stats['total_xp'] == 210  # 50 + 100 + 60
        assert stats['level'] >= 1
        assert stats['title'] in ["Beginner", "Explorer", "Scholar", "Master", "Sage"]
        assert 'xp_breakdown' in stats
        assert stats['xp_breakdown']['LESSON_COMPLETE'] == 50
        assert stats['xp_breakdown']['HARD_PROBLEM'] == 100
        assert stats['xp_breakdown']['PEER_HELP'] == 60


class TestStreakTracker:
    """Test streak tracking system"""
    
    def setup_method(self):
        self.streak_tracker = StreakTracker()
        self.user_id = "test_user_123"
        
    def test_first_streak(self):
        """Test first day streak"""
        result = self.streak_tracker.update_streak(self.user_id)
        
        assert result['current_streak'] == 1
        assert result['longest_streak'] == 1
        
    def test_consecutive_streak(self):
        """Test consecutive day streak building"""
        today = datetime.date.today()
        
        # Day 1
        self.streak_tracker.update_streak(self.user_id, today)
        
        # Day 2 
        result = self.streak_tracker.update_streak(self.user_id, today + datetime.timedelta(days=1))
        
        assert result['current_streak'] == 2
        assert result['longest_streak'] == 2
        
    def test_broken_streak(self):
        """Test streak breaking"""
        today = datetime.date.today()
        
        # Build 3-day streak
        self.streak_tracker.update_streak(self.user_id, today)
        self.streak_tracker.update_streak(self.user_id, today + datetime.timedelta(days=1))
        self.streak_tracker.update_streak(self.user_id, today + datetime.timedelta(days=2))
        
        # Break streak (skip a day)
        result = self.streak_tracker.update_streak(self.user_id, today + datetime.timedelta(days=4))
        
        assert result['current_streak'] == 1
        assert result['longest_streak'] == 3  # Previous best preserved
        
    def test_freeze_items(self):
        """Test streak freeze items"""
        today = datetime.date.today()
        
        # Build streak
        self.streak_tracker.update_streak(self.user_id, today)
        self.streak_tracker.update_streak(self.user_id, today + datetime.timedelta(days=1))
        
        # Give freeze item
        self.streak_tracker.add_freeze_item(self.user_id)
        assert self.streak_tracker.has_freeze_items(self.user_id)
        
        # Miss one day but have freeze - should save streak
        result = self.streak_tracker.update_streak(self.user_id, today + datetime.timedelta(days=3))
        
        assert result['current_streak'] == 3
        assert not self.streak_tracker.has_freeze_items(self.user_id)  # Used up
        
    def test_get_streak(self):
        """Test getting streak information"""
        streak_info = self.streak_tracker.get_streak(self.user_id)
        
        assert streak_info['current_streak'] == 0
        assert streak_info['freeze_items'] == 0


class TestDailyChallenge:
    """Test daily challenge system"""
    
    def setup_method(self):
        self.daily_challenge = DailyChallenge()
        self.user_id = "test_user_123"
        
    def test_generate_challenge(self):
        """Test challenge generation"""
        today = datetime.date.today()
        challenge = self.daily_challenge.generate_challenge(today, ["mathematics", "science"])
        
        assert 'id' in challenge
        assert 'title' in challenge
        assert 'description' in challenge
        assert challenge['topic'] in ["mathematics", "science"]
        assert challenge['xp_reward'] == 75
        
    def test_get_today_challenge(self):
        """Test getting today's challenge"""
        challenge = self.daily_challenge.get_today_challenge(["physics"])
        
        assert challenge['date'] == datetime.date.today().isoformat()
        assert challenge['topic'] == "physics"
        
    def test_complete_challenge(self):
        """Test challenge completion"""
        result = self.daily_challenge.complete_challenge(self.user_id)
        
        assert result['completed'] is True
        assert result['xp_awarded'] == 75
        assert result['total_completed'] == 1
        
    def test_is_completed(self):
        """Test checking if challenge is completed"""
        assert not self.daily_challenge.is_completed(self.user_id)
        
        self.daily_challenge.complete_challenge(self.user_id)
        
        assert self.daily_challenge.is_completed(self.user_id)
        
    def test_completion_stats(self):
        """Test completion statistics"""
        # Complete today's challenge
        self.daily_challenge.complete_challenge(self.user_id)
        
        stats = self.daily_challenge.get_completion_stats(self.user_id)
        
        assert stats['total_completed'] == 1
        assert stats['current_streak'] == 1


class TestAchievementEngine:
    """Test achievement system"""
    
    def setup_method(self):
        self.achievement_engine = AchievementEngine()
        self.user_id = "test_user_123"
        
    def test_get_achievements(self):
        """Test getting all achievements"""
        achievements = self.achievement_engine.achievements
        
        assert len(achievements) >= 20  # Should have 20+ achievements
        assert 'first_steps' in achievements
        assert 'seven_day_streak' in achievements
        
    def test_achievement_unlock(self):
        """Test unlocking an achievement"""
        # Manually unlock first_steps
        unlocked = self.achievement_engine.update_progress(self.user_id, 'first_steps', 1.0)
        
        assert unlocked is True
        
        progress = self.achievement_engine.get_user_progress(self.user_id, 'first_steps')
        assert progress.unlocked is True
        assert progress.unlock_date is not None
        
    def test_achievement_triggers(self):
        """Test achievement triggering from events"""
        newly_unlocked = self.achievement_engine.check_achievement_triggers(
            self.user_id, 'lesson_completed', {'duration_minutes': 3, 'accuracy': 100}
        )
        
        # Should unlock first_steps and speed_demon
        assert 'first_steps' in newly_unlocked
        assert 'speed_demon' in newly_unlocked
        
    def test_level_achievements(self):
        """Test level-based achievements"""
        newly_unlocked = self.achievement_engine.check_achievement_triggers(
            self.user_id, 'level_gained', {'new_level': 5}
        )
        
        assert 'quick_learner' in newly_unlocked
        
    def test_streak_achievements(self):
        """Test streak-based achievements"""
        newly_unlocked = self.achievement_engine.check_achievement_triggers(
            self.user_id, 'streak_updated', {'current_streak': 7}
        )
        
        assert 'consistent_student' in newly_unlocked
        assert 'seven_day_streak' in newly_unlocked
        
    def test_notification_hooks(self):
        """Test achievement notification system"""
        hook_called = []
        
        def test_hook(user_id, achievement, progress):
            hook_called.append((user_id, achievement.id))
            
        self.achievement_engine.add_notification_hook(test_hook)
        self.achievement_engine.update_progress(self.user_id, 'first_steps', 1.0)
        
        assert len(hook_called) == 1
        assert hook_called[0][0] == self.user_id
        assert hook_called[0][1] == 'first_steps'
        
    def test_user_achievements(self):
        """Test getting user achievement data"""
        # Unlock a few achievements
        self.achievement_engine.update_progress(self.user_id, 'first_steps', 1.0)
        self.achievement_engine.update_progress(self.user_id, 'quick_learner', 1.0)
        
        user_achievements = self.achievement_engine.get_user_achievements(self.user_id)
        
        assert user_achievements['unlocked_count'] == 2
        assert user_achievements['total_points'] > 0
        assert 'first_steps' in user_achievements['achievements']


class TestStudyGroupManager:
    """Test study group functionality"""
    
    def setup_method(self):
        self.group_manager = StudyGroupManager()
        self.owner_id = "owner_123"
        self.member_id = "member_456"
        
    def test_create_group(self):
        """Test creating a study group"""
        group = self.group_manager.create_group(
            "Math Study Group", 
            "Group for math help", 
            "mathematics",
            self.owner_id,
            "Owner"
        )
        
        assert group.name == "Math Study Group"
        assert group.subject == "mathematics"
        assert group.owner_id == self.owner_id
        assert self.owner_id in group.members
        assert group.members[self.owner_id].role == StudyGroupRole.OWNER
        
    def test_join_group(self):
        """Test joining a study group"""
        group = self.group_manager.create_group(
            "Science Group", "Science help", "science", self.owner_id, "Owner"
        )
        
        success = self.group_manager.join_group(group.id, self.member_id, "Member")
        
        assert success is True
        assert self.member_id in group.members
        assert group.members[self.member_id].role == StudyGroupRole.MEMBER
        
    def test_leave_group(self):
        """Test leaving a study group"""
        group = self.group_manager.create_group(
            "Test Group", "Test", "test", self.owner_id, "Owner"
        )
        
        self.group_manager.join_group(group.id, self.member_id, "Member")
        success = self.group_manager.leave_group(group.id, self.member_id)
        
        assert success is True
        assert self.member_id not in group.members
        
    def test_search_groups(self):
        """Test searching for groups"""
        self.group_manager.create_group(
            "Math Group", "Math help", "mathematics", self.owner_id, "Owner"
        )
        self.group_manager.create_group(
            "Science Group", "Science help", "science", self.owner_id, "Owner"
        )
        
        # Search by subject
        math_groups = self.group_manager.search_groups(subject="mathematics")
        assert len(math_groups) == 1
        assert math_groups[0].subject == "mathematics"
        
        # Search by query
        science_groups = self.group_manager.search_groups(query="Science")
        assert len(science_groups) == 1
        assert "Science" in science_groups[0].name
        
    def test_record_group_activity(self):
        """Test recording group member activity"""
        group = self.group_manager.create_group(
            "Activity Group", "Test", "test", self.owner_id, "Owner"
        )
        
        self.group_manager.record_group_activity(group.id, self.owner_id, 'lesson_completed', 50)
        
        assert group.group_xp == 50
        assert group.members[self.owner_id].contribution_score > 0


class TestLeaderboard:
    """Test leaderboard functionality"""
    
    def setup_method(self):
        self.leaderboard = Leaderboard()
        
    def test_update_leaderboard(self):
        """Test updating leaderboard entries"""
        entries = [
            LeaderboardEntry("user1", "User1", 1000, 0, 20, "Explorer"),
            LeaderboardEntry("user2", "User2", 1500, 0, 25, "Explorer"),
            LeaderboardEntry("user3", "User3", 800, 0, 15, "Beginner")
        ]
        
        self.leaderboard.update_leaderboard(LeaderboardScope.GLOBAL, "global", entries)
        
        # Check ranking
        updated_entries = self.leaderboard.get_leaderboard(LeaderboardScope.GLOBAL, "global")
        
        assert updated_entries[0].user_id == "user2"  # Highest score first
        assert updated_entries[0].rank == 1
        assert updated_entries[1].rank == 2
        assert updated_entries[2].rank == 3
        
    def test_get_user_rank(self):
        """Test getting specific user's rank"""
        entries = [
            LeaderboardEntry("user1", "User1", 1000, 0, 20, "Explorer"),
            LeaderboardEntry("user2", "User2", 1500, 0, 25, "Explorer")
        ]
        
        self.leaderboard.update_leaderboard(LeaderboardScope.GLOBAL, "global", entries)
        
        rank = self.leaderboard.get_user_rank(LeaderboardScope.GLOBAL, "global", "user1")
        assert rank == 2
        
    def test_top_performers(self):
        """Test getting top performers"""
        entries = [
            LeaderboardEntry("user1", "User1", 1000, 0, 20, "Explorer"),
            LeaderboardEntry("user2", "User2", 1500, 0, 25, "Explorer"),
            LeaderboardEntry("user3", "User3", 800, 0, 15, "Beginner")
        ]
        
        self.leaderboard.update_leaderboard(LeaderboardScope.GLOBAL, "global", entries)
        
        top_2 = self.leaderboard.get_top_performers(LeaderboardScope.GLOBAL, "global", 2)
        
        assert len(top_2) == 2
        assert top_2[0].user_id == "user2"  # Highest score


class TestPeerTutoringMatcher:
    """Test peer tutoring system"""
    
    def setup_method(self):
        self.tutoring = PeerTutoringMatcher()
        self.requester_id = "student_123"
        self.tutor_id = "tutor_456"
        
    def test_create_request(self):
        """Test creating tutoring request"""
        request = self.tutoring.create_request(
            self.requester_id, "Student", "mathematics", 
            "algebra", "Need help with quadratic equations", "intermediate"
        )
        
        assert request.requester_id == self.requester_id
        assert request.subject == "mathematics" 
        assert request.difficulty_level == "intermediate"
        assert not request.resolved
        
    def test_find_potential_tutors(self):
        """Test finding potential tutors"""
        request = self.tutoring.create_request(
            self.requester_id, "Student", "mathematics",
            "algebra", "Need help", "beginner"
        )
        
        user_levels = {
            self.tutor_id: 30,  # High enough level
            "low_level_user": 10  # Too low level
        }
        
        user_subjects = {
            self.tutor_id: ["mathematics", "science"],
            "low_level_user": ["mathematics"]
        }
        
        tutors = self.tutoring.find_potential_tutors(request.id, user_levels, user_subjects)
        
        assert len(tutors) == 1
        assert tutors[0]['user_id'] == self.tutor_id
        
    def test_assign_tutor(self):
        """Test assigning tutor to request"""
        request = self.tutoring.create_request(
            self.requester_id, "Student", "mathematics",
            "algebra", "Need help", "beginner"
        )
        
        success = self.tutoring.assign_tutor(request.id, self.tutor_id, "Tutor")
        
        assert success is True
        assert request.tutor_id == self.tutor_id
        
    def test_complete_session(self):
        """Test completing tutoring session"""
        request = self.tutoring.create_request(
            self.requester_id, "Student", "mathematics",
            "algebra", "Need help", "beginner"
        )
        
        self.tutoring.assign_tutor(request.id, self.tutor_id, "Tutor")
        success = self.tutoring.complete_session(request.id, 5)
        
        assert success is True
        assert request.resolved is True
        assert request.rating == 5
        
    def test_tutor_stats(self):
        """Test getting tutor statistics"""
        request = self.tutoring.create_request(
            self.requester_id, "Student", "mathematics",
            "algebra", "Need help", "beginner"
        )
        
        self.tutoring.assign_tutor(request.id, self.tutor_id, "Tutor")
        self.tutoring.complete_session(request.id, 4)
        
        stats = self.tutoring.get_tutor_stats(self.tutor_id)
        
        assert stats['total_sessions'] == 1
        assert stats['avg_rating'] == 4.0


class TestActivityFeed:
    """Test activity feed functionality"""
    
    def setup_method(self):
        self.activity_feed = ActivityFeed()
        self.user_id = "user_123"
        
    def test_add_activity(self):
        """Test adding activity to feed"""
        activity = self.activity_feed.add_activity(
            self.user_id, "TestUser", ActivityType.LEVEL_UP,
            "Level Up!", "Reached level 5", {"level": 5}
        )
        
        assert activity.user_id == self.user_id
        assert activity.activity_type == ActivityType.LEVEL_UP
        assert activity.title == "Level Up!"
        
    def test_get_feed(self):
        """Test getting activity feed"""
        # Add some activities
        for i in range(5):
            self.activity_feed.add_activity(
                f"user_{i}", f"User{i}", ActivityType.LESSON_COMPLETE,
                "Lesson Complete", f"Completed lesson {i}"
            )
            
        feed = self.activity_feed.get_feed(limit=3)
        
        assert len(feed) == 3
        # Should be in reverse chronological order
        assert feed[0].user_id == "user_4"
        
    def test_like_activity(self):
        """Test liking activities"""
        activity = self.activity_feed.add_activity(
            self.user_id, "TestUser", ActivityType.ACHIEVEMENT_UNLOCKED,
            "Achievement!", "Got an achievement"
        )
        
        success = self.activity_feed.like_activity(activity.id, "liker_123")
        assert success is True
        assert "liker_123" in activity.likes
        
        # Try to like again
        success = self.activity_feed.like_activity(activity.id, "liker_123")
        assert success is False  # Already liked
        
    def test_trending_activities(self):
        """Test getting trending activities"""
        # Add activity with likes
        activity = self.activity_feed.add_activity(
            self.user_id, "TestUser", ActivityType.LEVEL_UP,
            "Level Up!", "Big achievement"
        )
        
        # Add likes
        for i in range(5):
            self.activity_feed.like_activity(activity.id, f"user_{i}")
            
        trending = self.activity_feed.get_trending_activities()
        
        assert len(trending) >= 1
        assert activity.id in [t.id for t in trending]


class TestRewardsManager:
    """Test rewards and currency system"""
    
    def setup_method(self):
        self.rewards = RewardsManager()
        self.user_id = "user_123"
        
    def test_award_currency(self):
        """Test awarding currency to user"""
        result = self.rewards.award_currency(
            self.user_id, CurrencyType.EDUCOINS, 100, "Test reward"
        )
        
        assert result['amount'] == 100
        assert result['new_total'] == 100
        
        currency = self.rewards.get_user_currency(self.user_id)
        assert currency.educoins == 100
        
    def test_purchase_item(self):
        """Test purchasing store items"""
        # Give user some money
        self.rewards.award_currency(self.user_id, CurrencyType.EDUCOINS, 200)
        
        # Purchase item
        result = self.rewards.purchase_item(self.user_id, "avatar_student")
        
        assert result['success'] is True
        
        # Check item in inventory
        currency = self.rewards.get_user_currency(self.user_id)
        assert currency.educoins == 100  # 200 - 100 cost
        
        inventory = self.rewards.get_user_inventory(self.user_id)
        assert len(inventory['owned_items']) == 1
        
    def test_purchase_power_up(self):
        """Test purchasing and activating power-ups"""
        # Give user currency
        self.rewards.award_currency(self.user_id, CurrencyType.EDUCOINS, 100)
        
        # Purchase power-up
        result = self.rewards.purchase_power_up(self.user_id, "xp_double")
        
        assert result['success'] is True
        
        # Check active power-ups
        active = self.rewards.get_active_power_ups(self.user_id)
        assert len(active) == 1
        assert active[0][0].power_type == PowerUpType.XP_BOOST
        
    def test_reward_drops(self):
        """Test random reward drop system"""
        # Mock random to ensure reward drops
        with patch('random.random', return_value=0.05):  # Trigger reward
            reward = self.rewards.trigger_reward_drop(self.user_id, RewardTrigger.LESSON_COMPLETE)
            
            assert reward is not None
            assert 'currency' in reward or 'items' in reward or 'power_ups' in reward
            
    def test_power_up_cooldown(self):
        """Test power-up cooldown system"""
        # Give user currency
        self.rewards.award_currency(self.user_id, CurrencyType.GEMS, 5)
        
        # Purchase power-up with cooldown
        result = self.rewards.purchase_power_up(self.user_id, "xp_triple")
        assert result['success'] is True
        
        # Try to purchase again
        self.rewards.award_currency(self.user_id, CurrencyType.GEMS, 5)
        result = self.rewards.purchase_power_up(self.user_id, "xp_triple")
        
        assert result['success'] is False
        assert 'cooldown' in result['message'].lower()


class TestGamificationEngine:
    """Test main gamification engine integration"""
    
    def setup_method(self):
        self.engine = GamificationEngine()
        self.user_id = "user_123"
        
    def test_complete_lesson_integration(self):
        """Test lesson completion with full integration"""
        lesson_data = {
            'username': 'TestUser',
            'subject': 'mathematics',
            'duration_minutes': 15,
            'accuracy': 95
        }
        
        result = self.engine.complete_lesson(self.user_id, lesson_data)
        
        # Check XP was awarded
        assert result['xp']['xp_awarded'] == 50
        
        # Check streak was updated
        assert result['streak']['current_streak'] >= 1
        
        # Check achievements were triggered
        assert 'first_steps' in result['achievements']
        
    def test_daily_login(self):
        """Test daily login functionality"""
        result = self.engine.daily_login(self.user_id)
        
        assert 'login_reward' in result
        assert 'streak_info' in result
        assert 'daily_challenge' in result
        
    def test_daily_challenge_completion(self):
        """Test daily challenge completion"""
        result = self.engine.complete_daily_challenge(self.user_id, "TestUser")
        
        assert result['xp']['xp_awarded'] == 75
        assert result['challenge']['completed'] is True
        
    def test_user_dashboard(self):
        """Test comprehensive user dashboard"""
        # Do some activities first
        self.engine.complete_lesson(self.user_id, {'username': 'TestUser'})
        self.engine.complete_daily_challenge(self.user_id, "TestUser")
        
        dashboard = self.engine.get_user_dashboard(self.user_id)
        
        assert 'user_stats' in dashboard
        assert 'streak' in dashboard
        assert 'achievements' in dashboard
        assert 'social' in dashboard
        assert 'inventory' in dashboard
        assert 'daily_challenge' in dashboard
        
        # Check that data makes sense
        assert dashboard['user_stats']['total_xp'] > 0
        assert dashboard['achievements']['unlocked_count'] > 0


class TestVariableRatioScheduler:
    """Test variable ratio reward scheduling"""
    
    def setup_method(self):
        from src.gamification.rewards import VariableRatioScheduler
        self.scheduler = VariableRatioScheduler()
        self.user_id = "user_123"
        
    def test_reward_scheduling(self):
        """Test variable ratio reward scheduling"""
        rewards_given = 0
        
        # Simulate 20 activities
        for i in range(20):
            if self.scheduler.should_reward(self.user_id, "lesson_complete", base_ratio=5):
                rewards_given += 1
                
        # Should give some rewards, but not every time
        assert 0 < rewards_given < 20
        assert rewards_given >= 2  # Should give at least a few rewards
        
    def test_next_reward_estimate(self):
        """Test reward estimate functionality"""
        # Do a few activities
        for _ in range(3):
            self.scheduler.should_reward(self.user_id, "lesson_complete")
            
        estimate = self.scheduler.get_next_reward_estimate(self.user_id, "lesson_complete")
        
        assert isinstance(estimate, int)
        assert estimate > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])