"""Tests for gamification engine."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import uuid

from src.gamification.engine import (
    GamificationEngine, 
    LevelSystem, 
    AchievementSystem,
    DailyChallengeSystem,
    XPSource,
    DifficultyLevel
)
from src.models import User, StudentProfile, LearningEvent


class TestLevelSystem:
    """Test level system calculations."""
    
    def test_calculate_level_basic(self):
        """Test basic level calculations."""
        assert LevelSystem.calculate_level(0) == 1
        assert LevelSystem.calculate_level(50) == 1
        assert LevelSystem.calculate_level(100) == 2
        assert LevelSystem.calculate_level(500) == 5
        assert LevelSystem.calculate_level(10000) >= 25
    
    def test_level_titles(self):
        """Test level title assignments."""
        assert LevelSystem.get_level_title(1) == "Curious Cub"
        assert LevelSystem.get_level_title(5) == "Eager Explorer"
        assert LevelSystem.get_level_title(25) == "Skilled Apprentice"
        assert LevelSystem.get_level_title(100) == "Education Ancestor"
        
        # Test intermediate levels get lower title
        assert LevelSystem.get_level_title(12) == "Eager Explorer"
    
    def test_xp_for_next_level(self):
        """Test XP requirements for next level."""
        assert LevelSystem.xp_for_next_level(1) > 0
        assert LevelSystem.xp_for_next_level(50) > LevelSystem.xp_for_next_level(1)
        assert LevelSystem.xp_for_next_level(100) == 0  # Max level


class TestAchievementSystem:
    """Test achievement system."""
    
    @pytest.fixture
    def achievement_system(self):
        return AchievementSystem()
    
    @pytest.fixture
    def mock_profile(self):
        profile = MagicMock()
        profile.preferences = {'achievements': []}
        profile.streak_days = 0
        profile.last_study_date = None
        return profile
    
    @pytest.mark.asyncio
    async def test_first_lesson_achievement(self, achievement_system, mock_profile):
        """Test first lesson achievement detection."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Mock database query to return a lesson completion
        db.get.return_value = mock_profile
        db.query.return_value.filter.return_value.limit.return_value = MagicMock()
        db.execute.return_value.first.return_value = MagicMock()  # Has lesson
        
        achievements = await achievement_system.check_achievements(db, user_id)
        
        # Should detect first lesson achievement
        achievement_keys = [a['key'] for a in achievements]
        assert 'first_lesson' in achievement_keys
    
    @pytest.mark.asyncio
    async def test_streak_achievements(self, achievement_system):
        """Test streak-based achievements."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Mock profile with 7-day streak
        mock_profile = MagicMock()
        mock_profile.preferences = {'achievements': []}
        mock_profile.streak_days = 7
        mock_profile.last_study_date = datetime.utcnow()
        
        db.get.return_value = mock_profile
        
        achievements = await achievement_system.check_achievements(db, user_id)
        
        # Should get 7-day streak achievement
        achievement_keys = [a['key'] for a in achievements]
        assert 'streak_7' in achievement_keys
    
    @pytest.mark.asyncio
    async def test_no_duplicate_achievements(self, achievement_system):
        """Test that achievements aren't awarded twice."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Mock profile with existing achievement
        mock_profile = MagicMock()
        mock_profile.preferences = {'achievements': ['first_lesson']}
        mock_profile.streak_days = 7
        
        db.get.return_value = mock_profile
        
        achievements = await achievement_system.check_achievements(db, user_id)
        
        # Should not include already earned achievements
        achievement_keys = [a['key'] for a in achievements]
        assert 'first_lesson' not in achievement_keys


class TestDailyChallengeSystem:
    """Test daily challenge system."""
    
    @pytest.fixture
    def challenge_system(self):
        return DailyChallengeSystem()
    
    @pytest.fixture
    def mock_profile_with_weaknesses(self):
        profile = MagicMock()
        profile.weaknesses = ['mathematics', 'science']
        profile.streak_days = 3
        return profile
    
    @pytest.mark.asyncio
    async def test_generate_weakness_challenge(self, challenge_system, mock_profile_with_weaknesses):
        """Test challenge generation for user weaknesses."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile_with_weaknesses
        db.execute.return_value.all.return_value = []  # No recent events
        
        challenge = await challenge_system.generate_daily_challenge(db, user_id)
        
        assert challenge['type'] == 'weakness_focus'
        assert challenge['target']['subject'] in ['mathematics', 'science']
        assert 'xp_reward' in challenge
        assert 'expires_at' in challenge
    
    @pytest.mark.asyncio
    async def test_streak_building_challenge(self, challenge_system):
        """Test streak building challenge generation."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Profile with short streak (encourages continuation)
        profile = MagicMock()
        profile.weaknesses = []
        profile.streak_days = 3
        
        db.get.return_value = profile
        db.execute.return_value.all.return_value = []
        
        challenge = await challenge_system.generate_daily_challenge(db, user_id)
        
        assert challenge['type'] == 'streak_building'
        assert challenge['target']['study_minutes'] == 20


class TestGamificationEngine:
    """Test main gamification engine."""
    
    @pytest.fixture
    def engine(self):
        return GamificationEngine()
    
    @pytest.fixture
    def mock_profile(self):
        profile = MagicMock()
        profile.preferences = {'total_xp': 100, 'achievements': []}
        profile.streak_days = 1
        return profile
    
    @pytest.mark.asyncio
    async def test_award_basic_xp(self, engine, mock_profile):
        """Test basic XP awarding."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        result = await engine.award_xp(db, user_id, 50, XPSource.LESSON_COMPLETE)
        
        assert result['xp_awarded'] == 50
        assert result['total_xp'] == 150  # 100 + 50
        assert result['old_level'] == 2   # Level from 100 XP
        assert result['new_level'] >= 2
    
    @pytest.mark.asyncio
    async def test_bonus_xp_calculation(self, engine, mock_profile):
        """Test bonus XP for various conditions."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Profile with long streak for bonus
        mock_profile.streak_days = 10
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        # Award XP for difficult content with perfect score
        context = {
            'difficulty': DifficultyLevel.HARD.value,
            'score': 100,
            'fast_completion': True
        }
        
        result = await engine.award_xp(db, user_id, 100, XPSource.LESSON_COMPLETE, context)
        
        # Should have bonus XP due to streak, difficulty, perfect score, speed
        assert result['bonus_xp'] > 0
        assert result['xp_awarded'] > 100
    
    @pytest.mark.asyncio
    async def test_level_up_detection(self, engine, mock_profile):
        """Test level up detection and handling."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Profile close to level up
        mock_profile.preferences = {'total_xp': 95}
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        result = await engine.award_xp(db, user_id, 50, XPSource.LESSON_COMPLETE)
        
        assert result['level_up'] == True
        assert result['new_level'] > result['old_level']
        assert 'level_title' in result
    
    @pytest.mark.asyncio
    async def test_streak_update_consecutive(self, engine):
        """Test streak update for consecutive days."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Profile with yesterday's study
        profile = MagicMock()
        profile.streak_days = 5
        profile.last_study_date = datetime.utcnow() - timedelta(days=1)
        
        db.get.return_value = profile
        db.commit = AsyncMock()
        
        result = await engine.update_streak(db, user_id)
        
        assert result['streak_days'] == 6  # Should increment
    
    @pytest.mark.asyncio
    async def test_streak_break(self, engine):
        """Test streak reset when broken."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Profile with study from 3 days ago (broken streak)
        profile = MagicMock()
        profile.streak_days = 10
        profile.last_study_date = datetime.utcnow() - timedelta(days=3)
        
        db.get.return_value = profile
        db.commit = AsyncMock()
        
        result = await engine.update_streak(db, user_id)
        
        assert result['streak_days'] == 1  # Should reset to 1
    
    @pytest.mark.asyncio
    async def test_leaderboard_privacy(self, engine):
        """Test leaderboard respects privacy settings."""
        db = AsyncMock()
        
        # Mock query results with privacy settings
        mock_results = [
            MagicMock(user_id='user1', name='Alice', total_xp=1000),
            MagicMock(user_id='user2', name='Bob', total_xp=800),
        ]
        
        db.execute.return_value.all.return_value = mock_results
        
        result = await engine.get_leaderboard(db, 'global', 10, 'user1')
        
        assert 'leaderboard' in result
        assert result['privacy_note'] == "Only users who opted in are shown"
        
        # Check that only user's own ID is shown
        for entry in result['leaderboard']:
            if entry['user_id'] is not None:
                assert entry['user_id'] == 'user1'
    
    @pytest.mark.asyncio
    async def test_achievement_xp_bonus(self, engine, mock_profile):
        """Test that achievement XP is added to total."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        # Mock achievement system to return achievements
        engine.achievement_system.check_achievements = AsyncMock(
            return_value=[{'xp_reward': 100, 'key': 'test_achievement'}]
        )
        
        result = await engine.award_xp(db, user_id, 50, XPSource.LESSON_COMPLETE)
        
        assert result['achievement_xp'] == 100
        assert result['total_xp'] == 250  # 100 base + 50 awarded + 100 achievement


@pytest.mark.asyncio
async def test_integration_full_learning_session():
    """Integration test simulating a complete learning session."""
    engine = GamificationEngine()
    db = AsyncMock()
    user_id = str(uuid.uuid4())
    
    # Mock user profile
    profile = MagicMock()
    profile.preferences = {'total_xp': 0, 'achievements': []}
    profile.streak_days = 0
    profile.last_study_date = None
    
    db.get.return_value = profile
    db.commit = AsyncMock()
    
    # Mock achievement system to return first lesson achievement
    engine.achievement_system.check_achievements = AsyncMock(
        return_value=[{
            'key': 'first_lesson',
            'name': 'First Steps',
            'xp_reward': 50
        }]
    )
    
    # Simulate completing first lesson
    result = await engine.award_xp(
        db, 
        user_id, 
        25, 
        XPSource.LESSON_COMPLETE,
        {'score': 85, 'study_minutes': 15}
    )
    
    # Update streak
    streak_result = await engine.update_streak(db, user_id)
    
    # Verify results
    assert result['xp_awarded'] == 25
    assert result['achievement_xp'] == 50
    assert result['total_xp'] == 75
    assert result['new_achievements'][0]['key'] == 'first_lesson'
    assert streak_result['streak_days'] == 1
    
    # Verify database was updated
    assert db.commit.call_count >= 2  # Once for XP, once for streak