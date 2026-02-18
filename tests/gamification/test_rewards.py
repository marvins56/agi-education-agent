"""Tests for gamification rewards system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import uuid

from src.gamification.rewards import (
    RewardSystem,
    VirtualCurrency,
    RewardCatalog,
    RewardScheduler,
    PowerUpType
)
from src.models import StudentProfile


class TestVirtualCurrency:
    """Test virtual currency operations."""
    
    @pytest.fixture
    def mock_profile(self):
        profile = MagicMock()
        profile.preferences = {'educoins': 100, 'coin_transactions': []}
        return profile
    
    @pytest.mark.asyncio
    async def test_get_balance(self, mock_profile):
        """Test getting user coin balance."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        
        balance = await VirtualCurrency.get_balance(db, user_id)
        assert balance == 100
    
    @pytest.mark.asyncio
    async def test_get_balance_new_user(self):
        """Test getting balance for user with no coins."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        profile = MagicMock()
        profile.preferences = {}  # No coins key
        db.get.return_value = profile
        
        balance = await VirtualCurrency.get_balance(db, user_id)
        assert balance == 0
    
    @pytest.mark.asyncio
    async def test_award_coins(self, mock_profile):
        """Test awarding coins to user."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        result = await VirtualCurrency.award_coins(db, user_id, 50, "Test reward")
        
        assert result['coins_awarded'] == 50
        assert result['new_balance'] == 150  # 100 + 50
        assert result['reason'] == "Test reward"
        
        # Verify profile was updated
        assert mock_profile.preferences['educoins'] == 150
        assert len(mock_profile.preferences['coin_transactions']) == 1
    
    @pytest.mark.asyncio
    async def test_spend_coins_success(self, mock_profile):
        """Test successful coin spending."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        result = await VirtualCurrency.spend_coins(db, user_id, 30, "power_up")
        
        assert result['coins_spent'] == 30
        assert result['new_balance'] == 70  # 100 - 30
        assert result['item'] == "power_up"
    
    @pytest.mark.asyncio
    async def test_spend_coins_insufficient(self, mock_profile):
        """Test spending more coins than available."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        
        result = await VirtualCurrency.spend_coins(db, user_id, 150, "expensive_item")
        
        assert 'error' in result
        assert result['error'] == "Insufficient coins"
        assert result['required'] == 150
        assert result['balance'] == 100
    
    @pytest.mark.asyncio
    async def test_transaction_history_limit(self):
        """Test that transaction history is limited to 50 entries."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Profile with 50 existing transactions
        profile = MagicMock()
        profile.preferences = {
            'educoins': 1000,
            'coin_transactions': [{'amount': 10} for _ in range(50)]
        }
        
        db.get.return_value = profile
        db.commit = AsyncMock()
        
        await VirtualCurrency.award_coins(db, user_id, 100, "Test")
        
        # Should still have exactly 50 transactions (oldest removed)
        assert len(profile.preferences['coin_transactions']) == 50


class TestRewardCatalog:
    """Test reward catalog functionality."""
    
    def test_get_catalog(self):
        """Test getting full catalog."""
        catalog = RewardCatalog.get_catalog()
        
        assert 'avatar_frames' in catalog
        assert 'themes' in catalog
        assert 'voice_styles' in catalog
        assert 'power_ups' in catalog
        
        # Check that items have required fields
        for category, items in catalog.items():
            for item_id, item in items.items():
                assert 'name' in item
                assert 'cost' in item
                assert 'description' in item
    
    def test_get_item_cost(self):
        """Test getting cost of specific items."""
        # Test existing items
        assert RewardCatalog.get_item_cost('power_ups', 'hint_token') == 50
        assert RewardCatalog.get_item_cost('avatar_frames', 'golden_border') == 500
        
        # Test non-existing items
        assert RewardCatalog.get_item_cost('fake_category', 'fake_item') is None
        assert RewardCatalog.get_item_cost('power_ups', 'fake_power_up') is None
    
    def test_power_up_uses(self):
        """Test that power-ups have 'uses' field."""
        power_ups = RewardCatalog.POWER_UPS
        
        for power_up_id, power_up in power_ups.items():
            assert 'uses' in power_up
            assert power_up['uses'] >= 1


class TestRewardScheduler:
    """Test behavioral reward scheduling."""
    
    @pytest.fixture
    def scheduler(self):
        return RewardScheduler()
    
    @pytest.fixture
    def mock_profile(self):
        profile = MagicMock()
        profile.preferences = {'educoins': 500}
        profile.streak_days = 5
        return profile
    
    def test_base_coin_awards(self, scheduler):
        """Test base coin award amounts."""
        assert scheduler.base_coin_awards['lesson_complete'] > 0
        assert scheduler.base_coin_awards['problem_solve'] > 0
        assert scheduler.base_coin_awards['perfect_score'] > 0
    
    def test_calculate_coin_reward_base(self, scheduler, mock_profile):
        """Test basic coin reward calculation."""
        reward = scheduler.calculate_coin_reward('lesson_complete', {}, mock_profile)
        
        # Should be at least the base amount
        assert reward >= scheduler.base_coin_awards['lesson_complete']
    
    def test_bonus_for_struggling_students(self, scheduler, mock_profile):
        """Test bonus rewards for struggling students."""
        context = {'recent_performance': 0.3}  # Poor performance
        
        # Run multiple times to check for bonus probability
        rewards = []
        for _ in range(20):
            reward = scheduler.calculate_coin_reward('lesson_complete', context, mock_profile)
            rewards.append(reward)
        
        # Should have some bonus rewards (higher than base)
        base_reward = scheduler.base_coin_awards['lesson_complete']
        bonus_rewards = [r for r in rewards if r > base_reward]
        assert len(bonus_rewards) > 0  # Should have some bonuses for struggling student
    
    def test_special_deal_for_inactive_user(self, scheduler):
        """Test special deals for returning users."""
        profile = MagicMock()
        profile.last_study_date = datetime.utcnow() - timedelta(days=5)  # 5 days ago
        
        deal = scheduler.should_offer_special_deal(profile)
        
        assert deal is not None
        assert deal['title'] == "Welcome Back Special!"
        assert deal['discount'] == 0.5
        assert 'expires' in deal
    
    def test_no_deal_for_active_user(self, scheduler):
        """Test no special deals for recently active users."""
        profile = MagicMock()
        profile.last_study_date = datetime.utcnow() - timedelta(hours=2)  # Recent activity
        
        deal = scheduler.should_offer_special_deal(profile)
        
        # Should be None most of the time (except random weekend deals)
        if deal is not None:
            assert 'weekend' in deal['title'].lower()


class TestRewardSystem:
    """Test main reward system coordination."""
    
    @pytest.fixture
    def reward_system(self):
        return RewardSystem()
    
    @pytest.fixture
    def mock_profile(self):
        profile = MagicMock()
        profile.preferences = {
            'educoins': 200,
            'inventory': {
                'avatar_frames': [],
                'themes': [],
                'voice_styles': [],
                'power_ups': {}
            },
            'special_offers': []
        }
        return profile
    
    @pytest.mark.asyncio
    async def test_award_coins_for_event(self, reward_system, mock_profile):
        """Test awarding coins for learning events."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        reward_system.currency.award_coins = AsyncMock(return_value={
            'coins_awarded': 30,
            'new_balance': 230,
            'reason': 'Earned from lesson_complete'
        })
        
        result = await reward_system.award_coins_for_event(db, user_id, 'lesson_complete')
        
        assert result['coins_awarded'] == 30
        assert result['new_balance'] == 230
    
    @pytest.mark.asyncio
    async def test_purchase_item_success(self, reward_system, mock_profile):
        """Test successful item purchase."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        # Mock successful coin spending
        reward_system.currency.spend_coins = AsyncMock(return_value={
            'coins_spent': 50,
            'new_balance': 150,
            'item': 'power_ups:hint_token'
        })
        
        result = await reward_system.purchase_item(db, user_id, 'power_ups', 'hint_token')
        
        assert 'error' not in result
        assert result['item_id'] == 'hint_token'
        assert result['category'] == 'power_ups'
        
        # Check inventory was updated
        inventory = mock_profile.preferences['inventory']
        assert inventory['power_ups']['hint_token'] == 1
    
    @pytest.mark.asyncio
    async def test_purchase_item_insufficient_coins(self, reward_system, mock_profile):
        """Test purchase failure due to insufficient coins."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        
        # Mock insufficient coins
        reward_system.currency.spend_coins = AsyncMock(return_value={
            'error': 'Insufficient coins',
            'required': 1000,
            'balance': 200
        })
        
        result = await reward_system.purchase_item(db, user_id, 'voice_styles', 'storyteller')
        
        assert 'error' in result
        assert result['error'] == 'Insufficient coins'
    
    @pytest.mark.asyncio
    async def test_purchase_nonexistent_item(self, reward_system):
        """Test purchase of non-existent item."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        result = await reward_system.purchase_item(db, user_id, 'fake_category', 'fake_item')
        
        assert result['error'] == "Item not found"
    
    @pytest.mark.asyncio
    async def test_use_power_up_success(self, reward_system, mock_profile):
        """Test successful power-up usage."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Add power-up to inventory
        mock_profile.preferences['inventory']['power_ups']['hint_token'] = 2
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        result = await reward_system.use_power_up(db, user_id, 'hint_token')
        
        assert result['power_up_used'] == 'hint_token'
        assert result['remaining'] == 1  # Should decrement
        assert 'effect' in result
        
        # Check active effects were stored
        active_effects = mock_profile.preferences['active_power_ups']
        assert len(active_effects) == 1
        assert active_effects[0]['power_up'] == 'hint_token'
    
    @pytest.mark.asyncio
    async def test_use_power_up_not_available(self, reward_system, mock_profile):
        """Test using power-up not in inventory."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        
        result = await reward_system.use_power_up(db, user_id, 'double_xp')
        
        assert result['error'] == "Power-up not available"
    
    @pytest.mark.asyncio
    async def test_get_user_inventory(self, reward_system, mock_profile):
        """Test getting user's complete inventory."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        db.get.return_value = mock_profile
        reward_system.currency.get_balance = AsyncMock(return_value=200)
        reward_system.scheduler.should_offer_special_deal = MagicMock(return_value=None)
        
        inventory = await reward_system.get_user_inventory(db, user_id)
        
        assert inventory['coin_balance'] == 200
        assert 'inventory' in inventory
        assert 'catalog' in inventory
        assert inventory['special_offer'] is None
    
    @pytest.mark.asyncio
    async def test_get_active_power_ups(self, reward_system, mock_profile):
        """Test getting active power-ups and filtering expired ones."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        now = datetime.utcnow()
        
        # Add active effects (one expired, one active)
        mock_profile.preferences['active_power_ups'] = [
            {
                'power_up': 'expired_effect',
                'activated_at': (now - timedelta(hours=2)).isoformat(),
                'expires_at': (now - timedelta(hours=1)).isoformat()  # Expired
            },
            {
                'power_up': 'active_effect',
                'activated_at': now.isoformat(),
                'expires_at': (now + timedelta(hours=1)).isoformat()  # Active
            },
            {
                'power_up': 'permanent_effect',
                'activated_at': now.isoformat()
                # No expires_at = permanent
            }
        ]
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        active_effects = await reward_system.get_active_power_ups(db, user_id)
        
        # Should filter out expired effect
        assert len(active_effects) == 2
        power_ups = [effect['power_up'] for effect in active_effects]
        assert 'expired_effect' not in power_ups
        assert 'active_effect' in power_ups
        assert 'permanent_effect' in power_ups
    
    @pytest.mark.asyncio
    async def test_purchase_with_discount(self, reward_system, mock_profile):
        """Test purchasing item with active special offer."""
        db = AsyncMock()
        user_id = str(uuid.uuid4())
        
        # Add special offer
        mock_profile.preferences['special_offers'] = [{
            'title': 'Weekend Deal',
            'discount': 0.25,
            'expires': (datetime.utcnow() + timedelta(days=1)).isoformat(),
            'categories': ['power_ups']
        }]
        
        db.get.return_value = mock_profile
        db.commit = AsyncMock()
        
        # Mock discounted purchase
        reward_system.currency.spend_coins = AsyncMock(return_value={
            'coins_spent': 38,  # 50 * 0.75 (25% discount)
            'new_balance': 162,
            'item': 'power_ups:hint_token'
        })
        
        result = await reward_system.purchase_item(db, user_id, 'power_ups', 'hint_token')
        
        assert 'discount' in result
        assert result['discount']['original_cost'] == 50
        assert result['discount']['discount'] == 0.25
        assert result['discount']['final_cost'] == 38


@pytest.mark.asyncio
async def test_integration_reward_workflow():
    """Integration test for complete reward workflow."""
    reward_system = RewardSystem()
    db = AsyncMock()
    user_id = str(uuid.uuid4())
    
    # Mock profile with some coins
    profile = MagicMock()
    profile.preferences = {
        'educoins': 0,
        'inventory': {'power_ups': {}},
        'coin_transactions': []
    }
    profile.streak_days = 1
    profile.last_study_date = datetime.utcnow()
    
    db.get.return_value = profile
    db.commit = AsyncMock()
    
    # Step 1: Award coins for learning activity
    reward_system.currency.award_coins = AsyncMock(return_value={
        'coins_awarded': 75,
        'new_balance': 75,
        'reason': 'Earned from lesson_complete'
    })
    
    coin_result = await reward_system.award_coins_for_event(
        db, user_id, 'lesson_complete', {'score': 95}
    )
    
    assert coin_result['coins_awarded'] == 75
    
    # Step 2: Purchase a power-up
    profile.preferences['educoins'] = 75  # Update balance
    
    reward_system.currency.spend_coins = AsyncMock(return_value={
        'coins_spent': 50,
        'new_balance': 25,
        'item': 'power_ups:hint_token'
    })
    
    purchase_result = await reward_system.purchase_item(db, user_id, 'power_ups', 'hint_token')
    
    assert purchase_result['item_id'] == 'hint_token'
    
    # Step 3: Use the power-up
    profile.preferences['inventory']['power_ups']['hint_token'] = 1
    profile.preferences['active_power_ups'] = []
    
    use_result = await reward_system.use_power_up(db, user_id, 'hint_token')
    
    assert use_result['power_up_used'] == 'hint_token'
    assert use_result['remaining'] == 0