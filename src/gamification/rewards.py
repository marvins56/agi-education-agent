"""
Rewards system: EduCoins, unlockable items, study power-ups, variable ratio rewards
"""

import datetime
import random
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import json


class CurrencyType(Enum):
    """Types of in-game currency"""
    EDUCOINS = "educoins"  # Main currency earned through activities
    GEMS = "gems"  # Premium currency (rare rewards/purchases)
    TOKENS = "tokens"  # Special event currency


class ItemType(Enum):
    """Types of unlockable items"""
    AVATAR = "avatar"
    THEME = "theme"
    POWER_UP = "power_up"
    BADGE = "badge"
    ACCESSORY = "accessory"
    TITLE = "title"


class PowerUpType(Enum):
    """Types of study power-ups"""
    XP_BOOST = "xp_boost"  # Double XP for period
    STREAK_FREEZE = "streak_freeze"  # Protect streak for one day
    HINT_REVEAL = "hint_reveal"  # Reveal hints in problems
    TIME_EXTEND = "time_extend"  # Extra time for timed activities
    SECOND_CHANCE = "second_chance"  # Retry failed assessment
    FOCUS_MODE = "focus_mode"  # Distraction-free studying
    
    
class RewardTrigger(Enum):
    """Events that can trigger rewards"""
    LESSON_COMPLETE = "lesson_complete"
    DAILY_LOGIN = "daily_login"
    STREAK_MILESTONE = "streak_milestone"
    ACHIEVEMENT_UNLOCK = "achievement_unlock"
    RANDOM_DROP = "random_drop"
    LEVEL_UP = "level_up"
    PERFECT_SCORE = "perfect_score"
    CHALLENGE_COMPLETE = "challenge_complete"


@dataclass
class Currency:
    """User's currency holdings"""
    educoins: int = 0
    gems: int = 0
    tokens: int = 0
    
    def can_afford(self, cost: Dict[CurrencyType, int]) -> bool:
        """Check if user can afford a purchase"""
        currency_map = {
            CurrencyType.EDUCOINS: self.educoins,
            CurrencyType.GEMS: self.gems,
            CurrencyType.TOKENS: self.tokens
        }
        
        for currency_type, amount in cost.items():
            if currency_map[currency_type] < amount:
                return False
        return True
        
    def spend(self, cost: Dict[CurrencyType, int]) -> bool:
        """Spend currency if available"""
        if not self.can_afford(cost):
            return False
            
        for currency_type, amount in cost.items():
            if currency_type == CurrencyType.EDUCOINS:
                self.educoins -= amount
            elif currency_type == CurrencyType.GEMS:
                self.gems -= amount
            elif currency_type == CurrencyType.TOKENS:
                self.tokens -= amount
                
        return True
        
    def add(self, currency_type: CurrencyType, amount: int):
        """Add currency"""
        if currency_type == CurrencyType.EDUCOINS:
            self.educoins += amount
        elif currency_type == CurrencyType.GEMS:
            self.gems += amount
        elif currency_type == CurrencyType.TOKENS:
            self.tokens += amount


@dataclass
class UnlockableItem:
    """Item that can be unlocked/purchased"""
    id: str
    name: str
    description: str
    item_type: ItemType
    cost: Dict[CurrencyType, int]
    unlock_level: int = 1  # Minimum level to purchase
    is_limited: bool = False  # Limited time/quantity item
    rarity: str = "common"  # common, rare, epic, legendary
    metadata: Dict = field(default_factory=dict)  # Item-specific data
    
    def is_available_for_user(self, user_level: int, current_time: datetime.datetime = None) -> bool:
        """Check if item is available for user to purchase"""
        if user_level < self.unlock_level:
            return False
            
        if self.is_limited and current_time:
            # Check if within limited time window
            start_date = self.metadata.get('available_from')
            end_date = self.metadata.get('available_until')
            
            if start_date and current_time < datetime.datetime.fromisoformat(start_date):
                return False
            if end_date and current_time > datetime.datetime.fromisoformat(end_date):
                return False
                
        return True


@dataclass
class PowerUp:
    """Study power-up item"""
    id: str
    name: str
    description: str
    power_type: PowerUpType
    duration_minutes: int  # How long the power-up lasts
    effect_strength: float = 1.0  # Multiplier for effect (e.g., 2.0 = double XP)
    cost: Dict[CurrencyType, int] = field(default_factory=dict)
    cooldown_hours: int = 0  # Hours before can use again
    
    def get_effect_description(self) -> str:
        """Get user-friendly effect description"""
        descriptions = {
            PowerUpType.XP_BOOST: f"Earn {int(self.effect_strength * 100)}% XP for {self.duration_minutes} minutes",
            PowerUpType.STREAK_FREEZE: "Protect your learning streak for 1 day",
            PowerUpType.HINT_REVEAL: "Reveal hints for all problems",
            PowerUpType.TIME_EXTEND: f"Get {int(self.effect_strength * 100)}% more time on timed activities",
            PowerUpType.SECOND_CHANCE: "Retry a failed assessment without penalty",
            PowerUpType.FOCUS_MODE: f"Distraction-free studying for {self.duration_minutes} minutes"
        }
        return descriptions.get(self.power_type, self.description)


@dataclass
class ActivePowerUp:
    """Currently active power-up"""
    power_up_id: str
    user_id: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    uses_remaining: int = 1  # For consumable power-ups
    
    def is_active(self, current_time: datetime.datetime = None) -> bool:
        """Check if power-up is still active"""
        if current_time is None:
            current_time = datetime.datetime.now()
        return current_time <= self.end_time and self.uses_remaining > 0
        
    def use(self) -> bool:
        """Use the power-up (decrements uses)"""
        if self.uses_remaining > 0:
            self.uses_remaining -= 1
            return True
        return False


@dataclass
class RewardDrop:
    """Random reward drop"""
    items: List[str]  # Item IDs
    currency_rewards: Dict[CurrencyType, int]
    power_ups: List[str]  # Power-up IDs
    drop_chance: float  # 0.0 to 1.0
    message: str = "Surprise reward!"


class VariableRatioScheduler:
    """Implements variable ratio reward schedules for psychological engagement"""
    
    def __init__(self):
        self.user_activity_counts: Dict[str, Dict[str, int]] = {}  # user_id -> activity -> count
        self.last_reward_counts: Dict[str, Dict[str, int]] = {}  # user_id -> activity -> count when last rewarded
        
    def should_reward(self, user_id: str, activity: str, base_ratio: int = 5) -> bool:
        """Determine if user should receive reward based on variable ratio schedule"""
        if user_id not in self.user_activity_counts:
            self.user_activity_counts[user_id] = {}
            self.last_reward_counts[user_id] = {}
            
        # Increment activity count
        current_count = self.user_activity_counts[user_id].get(activity, 0) + 1
        self.user_activity_counts[user_id][activity] = current_count
        
        # Get last reward count
        last_reward = self.last_reward_counts[user_id].get(activity, 0)
        
        # Calculate activities since last reward
        since_last_reward = current_count - last_reward
        
        # Variable ratio: base_ratio ± random variance
        target_ratio = base_ratio + random.randint(-2, 2)
        target_ratio = max(1, target_ratio)  # Minimum 1
        
        if since_last_reward >= target_ratio:
            # Give reward and update last reward count
            self.last_reward_counts[user_id][activity] = current_count
            return True
            
        return False
        
    def get_next_reward_estimate(self, user_id: str, activity: str, base_ratio: int = 5) -> int:
        """Estimate activities until next reward (for UI display)"""
        if user_id not in self.user_activity_counts:
            return base_ratio
            
        current_count = self.user_activity_counts[user_id].get(activity, 0)
        last_reward = self.last_reward_counts[user_id].get(activity, 0)
        since_last_reward = current_count - last_reward
        
        # Conservative estimate
        return max(1, base_ratio - since_last_reward)


class RewardsManager:
    """Main rewards system manager"""
    
    def __init__(self):
        self.user_currencies: Dict[str, Currency] = {}
        self.user_items: Dict[str, Set[str]] = {}  # user_id -> set of owned item_ids
        self.user_power_ups: Dict[str, List[ActivePowerUp]] = {}
        self.store_items = self._initialize_store_items()
        self.power_ups = self._initialize_power_ups()
        self.reward_drops = self._initialize_reward_drops()
        self.scheduler = VariableRatioScheduler()
        self.power_up_cooldowns: Dict[str, Dict[str, datetime.datetime]] = {}  # user_id -> power_up_id -> last_used
        
    def _initialize_store_items(self) -> Dict[str, UnlockableItem]:
        """Initialize store items"""
        items = [
            # Avatars
            UnlockableItem("avatar_student", "Student Avatar", "Classic student look",
                         ItemType.AVATAR, {CurrencyType.EDUCOINS: 100}),
            UnlockableItem("avatar_wizard", "Wizard Avatar", "Mystical learning wizard",
                         ItemType.AVATAR, {CurrencyType.EDUCOINS: 500}, unlock_level=15, rarity="rare"),
            UnlockableItem("avatar_scientist", "Scientist Avatar", "Lab coat and safety goggles",
                         ItemType.AVATAR, {CurrencyType.EDUCOINS: 300}, unlock_level=10),
            
            # Themes
            UnlockableItem("theme_dark", "Dark Mode Theme", "Easy on the eyes",
                         ItemType.THEME, {CurrencyType.EDUCOINS: 200}),
            UnlockableItem("theme_nature", "Nature Theme", "Calming forest vibes",
                         ItemType.THEME, {CurrencyType.EDUCOINS: 400}, unlock_level=20),
            UnlockableItem("theme_space", "Space Theme", "Study among the stars",
                         ItemType.THEME, {CurrencyType.GEMS: 5}, rarity="epic"),
            
            # Titles
            UnlockableItem("title_scholar", "Scholar Title", "Display 'Scholar' as your title",
                         ItemType.TITLE, {CurrencyType.EDUCOINS: 150}, unlock_level=25),
            UnlockableItem("title_genius", "Genius Title", "For the truly exceptional",
                         ItemType.TITLE, {CurrencyType.EDUCOINS: 1000}, unlock_level=50, rarity="legendary"),
            
            # Accessories  
            UnlockableItem("accessory_cap", "Graduation Cap", "Academic achievement symbol",
                         ItemType.ACCESSORY, {CurrencyType.EDUCOINS: 250}, unlock_level=30),
            UnlockableItem("accessory_trophy", "Golden Trophy", "Show off your success",
                         ItemType.ACCESSORY, {CurrencyType.GEMS: 3}, rarity="rare"),
        ]
        
        return {item.id: item for item in items}
        
    def _initialize_power_ups(self) -> Dict[str, PowerUp]:
        """Initialize power-ups"""
        power_ups = [
            PowerUp("xp_double", "2x XP Boost", "Double XP for 30 minutes", 
                   PowerUpType.XP_BOOST, 30, 2.0, {CurrencyType.EDUCOINS: 50}),
            PowerUp("xp_triple", "3x XP Boost", "Triple XP for 15 minutes",
                   PowerUpType.XP_BOOST, 15, 3.0, {CurrencyType.GEMS: 1}, cooldown_hours=24),
            PowerUp("streak_save", "Streak Freeze", "Protect your streak for 1 day",
                   PowerUpType.STREAK_FREEZE, 1440, 1.0, {CurrencyType.EDUCOINS: 75}),  # 1440 minutes = 1 day
            PowerUp("hint_master", "Hint Revealer", "See hints for 1 hour",
                   PowerUpType.HINT_REVEAL, 60, 1.0, {CurrencyType.EDUCOINS: 40}),
            PowerUp("time_lord", "Time Extender", "50% more time for 2 hours", 
                   PowerUpType.TIME_EXTEND, 120, 1.5, {CurrencyType.EDUCOINS: 60}),
            PowerUp("second_shot", "Second Chance", "Retry any assessment",
                   PowerUpType.SECOND_CHANCE, 0, 1.0, {CurrencyType.GEMS: 2}),
            PowerUp("focus_zone", "Focus Mode", "Distraction-free for 45 minutes",
                   PowerUpType.FOCUS_MODE, 45, 1.0, {CurrencyType.EDUCOINS: 30})
        ]
        
        return {pu.id: pu for pu in power_ups}
        
    def _initialize_reward_drops(self) -> Dict[RewardTrigger, List[RewardDrop]]:
        """Initialize random reward drops for different triggers"""
        return {
            RewardTrigger.LESSON_COMPLETE: [
                RewardDrop([], {CurrencyType.EDUCOINS: 25}, [], 0.1, "Bonus coins!"),
                RewardDrop([], {CurrencyType.EDUCOINS: 10}, ["hint_master"], 0.05, "Study boost!"),
            ],
            RewardTrigger.DAILY_LOGIN: [
                RewardDrop([], {CurrencyType.EDUCOINS: 50}, [], 1.0, "Daily login bonus!"),
                RewardDrop([], {CurrencyType.GEMS: 1}, [], 0.1, "Lucky gem!"),
            ],
            RewardTrigger.STREAK_MILESTONE: [
                RewardDrop([], {CurrencyType.EDUCOINS: 100}, ["streak_save"], 0.3, "Streak reward!"),
                RewardDrop([], {CurrencyType.GEMS: 2}, [], 0.2, "Dedication pays off!"),
            ],
            RewardTrigger.LEVEL_UP: [
                RewardDrop([], {CurrencyType.EDUCOINS: 200}, ["xp_double"], 0.4, "Level up bonus!"),
                RewardDrop(["avatar_wizard"], {}, [], 0.05, "New avatar unlocked!"),
            ],
            RewardTrigger.PERFECT_SCORE: [
                RewardDrop([], {CurrencyType.EDUCOINS: 150}, [], 0.6, "Perfect performance!"),
                RewardDrop([], {CurrencyType.GEMS: 1}, ["second_shot"], 0.2, "Flawless execution!"),
            ]
        }
        
    def get_user_currency(self, user_id: str) -> Currency:
        """Get user's currency"""
        if user_id not in self.user_currencies:
            self.user_currencies[user_id] = Currency()
        return self.user_currencies[user_id]
        
    def award_currency(self, user_id: str, currency_type: CurrencyType, amount: int, reason: str = "") -> Dict:
        """Award currency to user"""
        currency = self.get_user_currency(user_id)
        currency.add(currency_type, amount)
        
        return {
            'currency_type': currency_type.value,
            'amount': amount,
            'new_total': getattr(currency, currency_type.value),
            'reason': reason
        }
        
    def purchase_item(self, user_id: str, item_id: str) -> Dict:
        """Purchase an item from the store"""
        if item_id not in self.store_items:
            return {'success': False, 'message': 'Item not found'}
            
        item = self.store_items[item_id]
        currency = self.get_user_currency(user_id)
        
        # Check if user already owns item
        if user_id in self.user_items and item_id in self.user_items[user_id]:
            return {'success': False, 'message': 'Item already owned'}
            
        # Check if user can afford item
        if not currency.can_afford(item.cost):
            return {'success': False, 'message': 'Insufficient funds'}
            
        # Process purchase
        currency.spend(item.cost)
        
        # Add item to user's inventory
        if user_id not in self.user_items:
            self.user_items[user_id] = set()
        self.user_items[user_id].add(item_id)
        
        return {
            'success': True,
            'item': item,
            'remaining_currency': currency
        }
        
    def purchase_power_up(self, user_id: str, power_up_id: str) -> Dict:
        """Purchase and activate a power-up"""
        if power_up_id not in self.power_ups:
            return {'success': False, 'message': 'Power-up not found'}
            
        power_up = self.power_ups[power_up_id]
        currency = self.get_user_currency(user_id)
        
        # Check cooldown
        if self.is_power_up_on_cooldown(user_id, power_up_id):
            cooldown_end = self.power_up_cooldowns[user_id][power_up_id]
            return {
                'success': False, 
                'message': f'Power-up on cooldown until {cooldown_end.strftime("%H:%M")}'
            }
            
        # Check if user can afford power-up
        if not currency.can_afford(power_up.cost):
            return {'success': False, 'message': 'Insufficient funds'}
            
        # Process purchase and activation
        currency.spend(power_up.cost)
        active_power_up = self.activate_power_up(user_id, power_up_id)
        
        return {
            'success': True,
            'power_up': power_up,
            'active_until': active_power_up.end_time,
            'remaining_currency': currency
        }
        
    def activate_power_up(self, user_id: str, power_up_id: str) -> ActivePowerUp:
        """Activate a power-up for a user"""
        power_up = self.power_ups[power_up_id]
        
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(minutes=power_up.duration_minutes)
        
        active_power_up = ActivePowerUp(
            power_up_id=power_up_id,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if user_id not in self.user_power_ups:
            self.user_power_ups[user_id] = []
        self.user_power_ups[user_id].append(active_power_up)
        
        # Set cooldown
        if power_up.cooldown_hours > 0:
            if user_id not in self.power_up_cooldowns:
                self.power_up_cooldowns[user_id] = {}
            self.power_up_cooldowns[user_id][power_up_id] = (
                datetime.datetime.now() + datetime.timedelta(hours=power_up.cooldown_hours)
            )
        
        return active_power_up
        
    def get_active_power_ups(self, user_id: str) -> List[Tuple[PowerUp, ActivePowerUp]]:
        """Get user's currently active power-ups"""
        if user_id not in self.user_power_ups:
            return []
            
        active_power_ups = []
        current_time = datetime.datetime.now()
        
        for active in self.user_power_ups[user_id]:
            if active.is_active(current_time):
                power_up = self.power_ups[active.power_up_id]
                active_power_ups.append((power_up, active))
                
        return active_power_ups
        
    def is_power_up_on_cooldown(self, user_id: str, power_up_id: str) -> bool:
        """Check if power-up is on cooldown"""
        if user_id not in self.power_up_cooldowns:
            return False
        if power_up_id not in self.power_up_cooldowns[user_id]:
            return False
            
        cooldown_end = self.power_up_cooldowns[user_id][power_up_id]
        return datetime.datetime.now() < cooldown_end
        
    def trigger_reward_drop(self, user_id: str, trigger: RewardTrigger) -> Optional[Dict]:
        """Trigger potential reward drop based on activity"""
        if trigger not in self.reward_drops:
            return None
            
        # Variable ratio check
        if not self.scheduler.should_reward(user_id, trigger.value):
            return None
            
        # Select reward drop
        possible_drops = self.reward_drops[trigger]
        
        for drop in possible_drops:
            if random.random() <= drop.drop_chance:
                # Award the reward
                rewards_awarded = {
                    'currency': {},
                    'items': [],
                    'power_ups': [],
                    'message': drop.message
                }
                
                # Award currency
                currency = self.get_user_currency(user_id)
                for currency_type, amount in drop.currency_rewards.items():
                    currency.add(currency_type, amount)
                    rewards_awarded['currency'][currency_type.value] = amount
                    
                # Award items
                if user_id not in self.user_items:
                    self.user_items[user_id] = set()
                    
                for item_id in drop.items:
                    if item_id not in self.user_items[user_id]:
                        self.user_items[user_id].add(item_id)
                        rewards_awarded['items'].append(self.store_items[item_id])
                        
                # Award power-ups (activate them)
                for power_up_id in drop.power_ups:
                    active_power_up = self.activate_power_up(user_id, power_up_id)
                    rewards_awarded['power_ups'].append({
                        'power_up': self.power_ups[power_up_id],
                        'active_until': active_power_up.end_time
                    })
                    
                return rewards_awarded
                
        return None
        
    def get_store_items(self, user_id: str, item_type: ItemType = None) -> List[Dict]:
        """Get available store items for user"""
        # This would integrate with user level system
        user_level = 50  # Placeholder - would come from XP system
        
        available_items = []
        user_currency = self.get_user_currency(user_id)
        owned_items = self.user_items.get(user_id, set())
        
        for item_id, item in self.store_items.items():
            if item_type and item.item_type != item_type:
                continue
                
            if not item.is_available_for_user(user_level):
                continue
                
            available_items.append({
                'item': item,
                'can_afford': user_currency.can_afford(item.cost),
                'already_owned': item_id in owned_items
            })
            
        return available_items
        
    def get_power_up_shop(self, user_id: str) -> List[Dict]:
        """Get available power-ups for purchase"""
        available_power_ups = []
        user_currency = self.get_user_currency(user_id)
        
        for power_up_id, power_up in self.power_ups.items():
            available_power_ups.append({
                'power_up': power_up,
                'can_afford': user_currency.can_afford(power_up.cost),
                'on_cooldown': self.is_power_up_on_cooldown(user_id, power_up_id),
                'cooldown_end': self.power_up_cooldowns.get(user_id, {}).get(power_up_id),
                'effect_description': power_up.get_effect_description()
            })
            
        return available_power_ups
        
    def use_consumable_power_up(self, user_id: str, power_up_type: PowerUpType) -> bool:
        """Use a consumable power-up (like second chance)"""
        active_power_ups = self.get_active_power_ups(user_id)
        
        for power_up, active in active_power_ups:
            if power_up.power_type == power_up_type:
                return active.use()
                
        return False
        
    def get_user_inventory(self, user_id: str) -> Dict:
        """Get user's complete inventory and status"""
        currency = self.get_user_currency(user_id)
        owned_items = self.user_items.get(user_id, set())
        active_power_ups = self.get_active_power_ups(user_id)
        
        # Calculate total value of owned items
        total_value = sum(
            sum(item.cost.get(CurrencyType.EDUCOINS, 0) for item in self.store_items.values()
                if item.id in owned_items)
        )
        
        return {
            'currency': currency,
            'owned_items': [self.store_items[item_id] for item_id in owned_items 
                          if item_id in self.store_items],
            'active_power_ups': active_power_ups,
            'total_items': len(owned_items),
            'inventory_value': total_value
        }