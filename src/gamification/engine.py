"""
Core XP & Level system for EduAGI gamification
"""

import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import random


class XPSource(Enum):
    """XP award sources with their point values"""
    LESSON_COMPLETE = 50
    STREAK_BONUS = 25
    HARD_PROBLEM = 100
    DAILY_CHALLENGE = 75
    PEER_HELP = 60


class LevelTier(Enum):
    """Level tiers with ranges"""
    BEGINNER = (1, 10, "Beginner")
    EXPLORER = (11, 25, "Explorer") 
    SCHOLAR = (26, 50, "Scholar")
    MASTER = (51, 75, "Master")
    SAGE = (76, 100, "Sage")
    
    def __init__(self, min_level: int, max_level: int, title: str):
        self.min_level = min_level
        self.max_level = max_level
        self.title = title


@dataclass
class XPEvent:
    """Record of an XP award event"""
    source: XPSource
    amount: int
    timestamp: datetime.datetime
    user_id: str
    metadata: Dict = None


class XPManager:
    """Manages experience points and leveling system"""
    
    def __init__(self):
        # XP required for each level (exponential growth)
        self._level_requirements = self._generate_level_requirements()
        self._xp_events: List[XPEvent] = []
        
    def _generate_level_requirements(self) -> Dict[int, int]:
        """Generate XP requirements for levels 1-100"""
        requirements = {1: 0}  # Level 1 requires 0 XP
        
        for level in range(2, 101):
            # Exponential growth: base XP * (level^1.5)
            base_xp = 100
            required_xp = int(base_xp * (level ** 1.5))
            requirements[level] = required_xp
            
        return requirements
    
    def award_xp(self, user_id: str, source: XPSource, metadata: Dict = None) -> Dict:
        """Award XP to a user and return level change info"""
        current_total = self.get_total_xp(user_id)
        current_level = self.get_level(current_total)
        
        # Record the XP event
        event = XPEvent(
            source=source,
            amount=source.value,
            timestamp=datetime.datetime.now(),
            user_id=user_id,
            metadata=metadata or {}
        )
        self._xp_events.append(event)
        
        # Calculate new totals
        new_total = current_total + source.value
        new_level = self.get_level(new_total)
        
        return {
            'xp_awarded': source.value,
            'total_xp': new_total,
            'previous_level': current_level,
            'new_level': new_level,
            'level_up': new_level > current_level,
            'source': source.name,
            'new_title': self.get_title(new_level) if new_level > current_level else None
        }
    
    def get_total_xp(self, user_id: str) -> int:
        """Get total XP for a user"""
        return sum(event.amount for event in self._xp_events if event.user_id == user_id)
    
    def get_level(self, total_xp: int = None, user_id: str = None) -> int:
        """Get level from XP amount or for a specific user"""
        if total_xp is None and user_id:
            total_xp = self.get_total_xp(user_id)
        elif total_xp is None:
            raise ValueError("Must provide either total_xp or user_id")
            
        level = 1
        for lvl in range(1, 101):
            if total_xp >= self._level_requirements[lvl]:
                level = lvl
            else:
                break
        return level
    
    def get_title(self, level: int) -> str:
        """Get title for a specific level"""
        for tier in LevelTier:
            if tier.min_level <= level <= tier.max_level:
                return tier.title
        return "Sage"  # Max level fallback
    
    def get_xp_to_next_level(self, user_id: str) -> Tuple[int, int]:
        """Get XP needed for next level and current progress"""
        current_xp = self.get_total_xp(user_id)
        current_level = self.get_level(current_xp)
        
        if current_level >= 100:
            return 0, current_xp  # Max level reached
            
        next_level_xp = self._level_requirements[current_level + 1]
        current_level_xp = self._level_requirements[current_level]
        
        needed = next_level_xp - current_xp
        progress = current_xp - current_level_xp
        
        return needed, progress
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive stats for a user"""
        total_xp = self.get_total_xp(user_id)
        level = self.get_level(total_xp)
        title = self.get_title(level)
        xp_needed, xp_progress = self.get_xp_to_next_level(user_id)
        
        # Get XP breakdown by source
        user_events = [e for e in self._xp_events if e.user_id == user_id]
        xp_by_source = {}
        for source in XPSource:
            xp_by_source[source.name] = sum(
                e.amount for e in user_events if e.source == source
            )
            
        return {
            'user_id': user_id,
            'total_xp': total_xp,
            'level': level,
            'title': title,
            'xp_to_next_level': xp_needed,
            'xp_progress_in_level': xp_progress,
            'xp_breakdown': xp_by_source,
            'total_events': len(user_events)
        }


class StreakTracker:
    """Tracks consecutive learning days and streak freezes"""
    
    def __init__(self):
        self._streaks: Dict[str, Dict] = {}  # user_id -> streak_data
        self._freeze_items: Dict[str, int] = {}  # user_id -> freeze_count
        
    def update_streak(self, user_id: str, date: datetime.date = None) -> Dict:
        """Update user's learning streak"""
        if date is None:
            date = datetime.date.today()
            
        if user_id not in self._streaks:
            self._streaks[user_id] = {
                'current_streak': 1,
                'longest_streak': 1,
                'last_activity_date': date,
                'streak_start_date': date
            }
            return self._streaks[user_id]
            
        streak_data = self._streaks[user_id]
        last_date = streak_data['last_activity_date']
        
        # Check if this is consecutive day
        days_diff = (date - last_date).days
        
        if days_diff == 1:
            # Consecutive day - extend streak
            streak_data['current_streak'] += 1
            streak_data['longest_streak'] = max(
                streak_data['longest_streak'], 
                streak_data['current_streak']
            )
        elif days_diff == 0:
            # Same day - no change
            pass
        elif days_diff == 2 and self.has_freeze_items(user_id):
            # One day missed but have freeze item
            self.use_freeze_item(user_id)
            streak_data['current_streak'] += 1
            streak_data['longest_streak'] = max(
                streak_data['longest_streak'], 
                streak_data['current_streak']
            )
        else:
            # Streak broken
            streak_data['current_streak'] = 1
            streak_data['streak_start_date'] = date
            
        streak_data['last_activity_date'] = date
        return streak_data.copy()
    
    def get_streak(self, user_id: str) -> Dict:
        """Get current streak info for user"""
        if user_id not in self._streaks:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'last_activity_date': None,
                'streak_start_date': None,
                'freeze_items': self._freeze_items.get(user_id, 0)
            }
            
        streak_data = self._streaks[user_id].copy()
        streak_data['freeze_items'] = self._freeze_items.get(user_id, 0)
        return streak_data
    
    def add_freeze_item(self, user_id: str, count: int = 1):
        """Add streak freeze items for user"""
        self._freeze_items[user_id] = self._freeze_items.get(user_id, 0) + count
        
    def use_freeze_item(self, user_id: str) -> bool:
        """Use a streak freeze item"""
        if self._freeze_items.get(user_id, 0) > 0:
            self._freeze_items[user_id] -= 1
            return True
        return False
        
    def has_freeze_items(self, user_id: str) -> bool:
        """Check if user has freeze items"""
        return self._freeze_items.get(user_id, 0) > 0


class DailyChallenge:
    """Generates and manages daily challenges based on weak topics"""
    
    def __init__(self):
        self._challenges: Dict[str, Dict] = {}  # date -> challenge_data
        self._completions: Dict[str, List[str]] = {}  # user_id -> [completed_dates]
        
    def generate_challenge(self, date: datetime.date, weak_topics: List[str] = None) -> Dict:
        """Generate daily challenge for a specific date"""
        date_str = date.isoformat()
        
        if date_str in self._challenges:
            return self._challenges[date_str]
            
        # Default challenge types
        challenge_types = [
            "solve_problems", "review_concepts", "practice_quiz", 
            "explain_concept", "find_patterns", "creative_application"
        ]
        
        # Select challenge type and topic
        challenge_type = random.choice(challenge_types)
        
        if weak_topics:
            topic = random.choice(weak_topics)
        else:
            # Fallback topics
            fallback_topics = [
                "mathematics", "science", "language", "history", 
                "critical_thinking", "problem_solving"
            ]
            topic = random.choice(fallback_topics)
            
        # Generate challenge details
        challenge = {
            'id': f"daily_{date_str}_{challenge_type}",
            'date': date_str,
            'type': challenge_type,
            'topic': topic,
            'title': self._generate_title(challenge_type, topic),
            'description': self._generate_description(challenge_type, topic),
            'xp_reward': XPSource.DAILY_CHALLENGE.value,
            'difficulty': random.choice(['easy', 'medium', 'hard']),
            'estimated_time': random.randint(10, 30)  # minutes
        }
        
        self._challenges[date_str] = challenge
        return challenge
        
    def _generate_title(self, challenge_type: str, topic: str) -> str:
        """Generate challenge title"""
        titles = {
            'solve_problems': f"Problem Solver: {topic.title()} Edition",
            'review_concepts': f"Concept Review: {topic.title()} Mastery", 
            'practice_quiz': f"Quick Quiz: {topic.title()} Challenge",
            'explain_concept': f"Teach It: {topic.title()} Explanation",
            'find_patterns': f"Pattern Detective: {topic.title()}",
            'creative_application': f"Creative Challenge: {topic.title()} in Action"
        }
        return titles.get(challenge_type, f"Daily Challenge: {topic.title()}")
        
    def _generate_description(self, challenge_type: str, topic: str) -> str:
        """Generate challenge description"""
        descriptions = {
            'solve_problems': f"Solve 3-5 {topic} problems to strengthen your skills",
            'review_concepts': f"Review and summarize key {topic} concepts you've learned",
            'practice_quiz': f"Take a quick quiz on {topic} fundamentals",
            'explain_concept': f"Explain a {topic} concept in your own words",
            'find_patterns': f"Find patterns and connections in {topic} examples", 
            'creative_application': f"Apply {topic} knowledge to a real-world scenario"
        }
        return descriptions.get(challenge_type, f"Complete today's {topic} challenge")
        
    def complete_challenge(self, user_id: str, date: datetime.date = None) -> Dict:
        """Mark challenge as completed for user"""
        if date is None:
            date = datetime.date.today()
            
        date_str = date.isoformat()
        
        if user_id not in self._completions:
            self._completions[user_id] = []
            
        if date_str not in self._completions[user_id]:
            self._completions[user_id].append(date_str)
            
        return {
            'completed': True,
            'date': date_str,
            'xp_awarded': XPSource.DAILY_CHALLENGE.value,
            'total_completed': len(self._completions[user_id])
        }
        
    def get_today_challenge(self, weak_topics: List[str] = None) -> Dict:
        """Get today's challenge"""
        return self.generate_challenge(datetime.date.today(), weak_topics)
        
    def is_completed(self, user_id: str, date: datetime.date = None) -> bool:
        """Check if user completed challenge for date"""
        if date is None:
            date = datetime.date.today()
            
        date_str = date.isoformat()
        return date_str in self._completions.get(user_id, [])
        
    def get_completion_stats(self, user_id: str) -> Dict:
        """Get user's challenge completion statistics"""
        completions = self._completions.get(user_id, [])
        
        # Calculate streak
        current_streak = 0
        date_check = datetime.date.today()
        
        while date_check.isoformat() in completions:
            current_streak += 1
            date_check -= datetime.timedelta(days=1)
            
        return {
            'total_completed': len(completions),
            'current_streak': current_streak,
            'completion_rate_last_30_days': self._get_recent_completion_rate(user_id, 30)
        }
        
    def _get_recent_completion_rate(self, user_id: str, days: int) -> float:
        """Get completion rate for recent days"""
        completions = self._completions.get(user_id, [])
        recent_dates = []
        
        for i in range(days):
            date = datetime.date.today() - datetime.timedelta(days=i)
            recent_dates.append(date.isoformat())
            
        completed_in_range = sum(1 for date in completions if date in recent_dates)
        return completed_in_range / days if days > 0 else 0.0