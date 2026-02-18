"""
Disability-Aware FSRS - Modified spaced repetition system for inclusive learning

This module adapts the FSRS (Free Spaced Repetition Scheduler) algorithm to
account for different cognitive profiles and learning disabilities, providing
more appropriate scheduling for students with diverse needs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math
import time
import random
from datetime import datetime, timedelta

from accessibility_engine import AccessibilityProfile, ImpairmentType, SeverityLevel


class ReviewOutcome(Enum):
    """Possible outcomes of a review session"""
    AGAIN = 1      # Complete failure, needs immediate review
    HARD = 2       # Difficult, but passed
    GOOD = 3       # Normal difficulty
    EASY = 4       # Too easy
    

class CognitiveProfile(Enum):
    """Cognitive profiles for different learning patterns"""
    STANDARD = "standard"
    SLOW_PROCESSING = "slow_processing"
    WORKING_MEMORY_DEFICIT = "working_memory_deficit"
    ATTENTION_DEFICIT = "attention_deficit"
    LEARNING_DISABILITY = "learning_disability"
    AUTISM_SPECTRUM = "autism_spectrum"


@dataclass
class CardState:
    """State of a flashcard in the FSRS system"""
    due_date: datetime
    stability: float  # How stable the memory is
    difficulty: float  # Inherent difficulty of the card
    elapsed_days: int = 0
    scheduled_days: int = 0
    review_count: int = 0
    lapses: int = 0
    last_review: Optional[datetime] = None
    
    # Disability-specific tracking
    encouragement_needed: bool = False
    simplified_version_used: bool = False
    voice_presentation_used: bool = False


@dataclass
class CognitiveMemoryProfile:
    """Memory curve profile for different cognitive conditions"""
    profile_type: CognitiveProfile
    
    # Base FSRS parameters (modified for cognitive profile)
    retention_target: float = 0.9  # Target retention rate
    maximum_interval: int = 36500  # Maximum days between reviews
    
    # Cognitive-specific modifiers
    stability_modifier: float = 1.0  # How quickly memories stabilize
    difficulty_sensitivity: float = 1.0  # How much difficulty affects scheduling
    interference_resistance: float = 1.0  # Resistance to interference
    consolidation_speed: float = 1.0  # Speed of memory consolidation
    
    # Encouragement and support parameters
    encouragement_threshold: float = 0.6  # When to provide extra encouragement
    max_difficulty_ceiling: float = 8.0  # Maximum difficulty allowed
    frequent_review_multiplier: float = 1.5  # Extra review frequency
    
    @classmethod
    def create_for_condition(cls, condition: str, severity: SeverityLevel) -> 'CognitiveMemoryProfile':
        """Create memory profile for specific learning condition"""
        
        # Base profiles for different conditions
        profiles = {
            "adhd": CognitiveProfile.ATTENTION_DEFICIT,
            "dyslexia": CognitiveProfile.LEARNING_DISABILITY,
            "autism": CognitiveProfile.AUTISM_SPECTRUM,
            "intellectual_disability": CognitiveProfile.LEARNING_DISABILITY,
            "processing_speed": CognitiveProfile.SLOW_PROCESSING,
            "working_memory": CognitiveProfile.WORKING_MEMORY_DEFICIT
        }
        
        profile_type = profiles.get(condition, CognitiveProfile.STANDARD)
        profile = cls(profile_type=profile_type)
        
        # Adjust parameters based on severity
        severity_multipliers = {
            SeverityLevel.MILD: 0.9,
            SeverityLevel.MODERATE: 0.7,
            SeverityLevel.SEVERE: 0.5
        }
        
        multiplier = severity_multipliers.get(severity, 1.0)
        
        # Apply condition-specific modifications
        if condition == "adhd":
            profile.stability_modifier = 0.8 * multiplier
            profile.interference_resistance = 0.7 * multiplier
            profile.frequent_review_multiplier = 2.0
            profile.max_difficulty_ceiling = 6.0
            
        elif condition == "dyslexia":
            profile.consolidation_speed = 0.8 * multiplier
            profile.difficulty_sensitivity = 0.6 * multiplier
            profile.max_difficulty_ceiling = 7.0
            
        elif condition == "autism":
            profile.stability_modifier = 1.2 * multiplier  # Often good memory
            profile.difficulty_sensitivity = 0.8 * multiplier
            profile.encouragement_threshold = 0.7  # Need more positive reinforcement
            
        elif condition == "intellectual_disability":
            profile.stability_modifier = 0.6 * multiplier
            profile.consolidation_speed = 0.5 * multiplier
            profile.max_difficulty_ceiling = 5.0
            profile.frequent_review_multiplier = 2.5
            
        elif condition == "processing_speed":
            profile.consolidation_speed = 0.7 * multiplier
            profile.encouragement_threshold = 0.5
            
        elif condition == "working_memory":
            profile.interference_resistance = 0.6 * multiplier
            profile.frequent_review_multiplier = 1.8
            
        return profile


class DisabilityAwareFSRS:
    """
    Modified FSRS scheduler that adapts to cognitive profiles and disabilities
    """
    
    # Base FSRS algorithm parameters
    DEFAULT_PARAMETERS = [
        0.4072,  # w[0]: initial stability for new cards
        1.1829,  # w[1]: initial stability growth
        3.1262,  # w[2]: initial difficulty decay
        15.4722, # w[3]: difficulty weight on stability
        7.2102,  # w[4]: difficulty weight on retrievability
        0.5316,  # w[5]: retrievability decay
        1.0651,  # w[6]: difficulty growth on failure
        0.0234,  # w[7]: stability growth on success
        1.616,   # w[8]: stability decay on failure
        0.1544,  # w[9]: retrievability threshold
        1.0824,  # w[10]: stability growth modifier
        2.0063,  # w[11]: easy bonus
        0.2335,  # w[12]: hard penalty
        2.2698,  # w[13]: new card bonus
        0.0953,  # w[14]: review bonus
        0.3024,  # w[15]: lapse bonus
        1.1474,  # w[16]: minimum stability
        0.0953,  # w[17]: stability oscillation
    ]
    
    def __init__(self, parameters: List[float] = None):
        self.parameters = parameters or self.DEFAULT_PARAMETERS.copy()
        self.cognitive_profiles: Dict[str, CognitiveMemoryProfile] = {}
        self.encouragement_messages: List[str] = [
            "You're doing great! Keep going!",
            "Every mistake is a step toward learning!",
            "Take your time - you've got this!",
            "Progress, not perfection!",
            "You're improving with each try!",
        ]
        
    def register_cognitive_profile(self, user_id: str, 
                                 accessibility_profile: AccessibilityProfile):
        """Register cognitive profile for a user"""
        # Determine primary cognitive condition
        primary_condition = None
        primary_severity = SeverityLevel.MILD
        
        for condition, severity in accessibility_profile.cognitive_impairments.items():
            if primary_condition is None or severity.value > primary_severity.value:
                primary_condition = condition
                primary_severity = severity
                
        if primary_condition:
            self.cognitive_profiles[user_id] = CognitiveMemoryProfile.create_for_condition(
                primary_condition, primary_severity)
        else:
            # Default profile
            self.cognitive_profiles[user_id] = CognitiveMemoryProfile(
                profile_type=CognitiveProfile.STANDARD)
                
    def get_cognitive_profile(self, user_id: str) -> CognitiveMemoryProfile:
        """Get cognitive profile for user, creating default if needed"""
        if user_id not in self.cognitive_profiles:
            self.cognitive_profiles[user_id] = CognitiveMemoryProfile(
                profile_type=CognitiveProfile.STANDARD)
        return self.cognitive_profiles[user_id]
        
    def schedule_new_card(self, user_id: str, initial_difficulty: float = None) -> CardState:
        """Schedule a new card for first review"""
        profile = self.get_cognitive_profile(user_id)
        
        # Adjust initial difficulty based on profile
        if initial_difficulty is None:
            initial_difficulty = 5.0  # Standard difficulty
            
        # Apply difficulty ceiling
        initial_difficulty = min(initial_difficulty, profile.max_difficulty_ceiling)
        
        # Calculate initial stability
        stability = (self.parameters[0] * 
                    (initial_difficulty - 1) * 
                    self.parameters[1] + 
                    self.parameters[2]) * profile.stability_modifier
        
        # Schedule first review (shorter for learning disabilities)
        base_interval = max(1, int(stability))
        if profile.profile_type in [CognitiveProfile.LEARNING_DISABILITY, 
                                   CognitiveProfile.WORKING_MEMORY_DEFICIT]:
            base_interval = max(1, base_interval // 2)
            
        due_date = datetime.now() + timedelta(days=base_interval)
        
        return CardState(
            due_date=due_date,
            stability=stability,
            difficulty=initial_difficulty,
            scheduled_days=base_interval
        )
        
    def schedule_review(self, user_id: str, card: CardState, 
                       outcome: ReviewOutcome, review_duration: float = None) -> CardState:
        """Schedule next review based on outcome and cognitive profile"""
        profile = self.get_cognitive_profile(user_id)
        
        # Update card state
        card.last_review = datetime.now()
        card.review_count += 1
        card.elapsed_days = (datetime.now() - card.due_date).days + card.scheduled_days
        
        # Calculate retrievability
        retrievability = self._calculate_retrievability(card, profile)
        
        # Update difficulty based on outcome
        new_difficulty = self._update_difficulty(card.difficulty, outcome, profile)
        
        # Update stability
        if outcome == ReviewOutcome.AGAIN:
            new_stability = self._calculate_failure_stability(card, profile)
            card.lapses += 1
        else:
            new_stability = self._calculate_success_stability(card, outcome, retrievability, profile)
            
        # Calculate next interval
        interval = self._calculate_interval(new_stability, profile)
        
        # Apply cognitive-specific adjustments
        interval = self._apply_cognitive_adjustments(interval, outcome, profile, card)
        
        # Update card state
        card.stability = new_stability
        card.difficulty = new_difficulty
        card.scheduled_days = interval
        card.due_date = datetime.now() + timedelta(days=interval)
        
        # Check if encouragement is needed
        card.encouragement_needed = (retrievability < profile.encouragement_threshold or 
                                   outcome == ReviewOutcome.AGAIN)
        
        return card
        
    def _calculate_retrievability(self, card: CardState, 
                                profile: CognitiveMemoryProfile) -> float:
        """Calculate current retrievability of the card"""
        if card.elapsed_days <= 0:
            return 1.0
            
        # Apply cognitive profile modifiers
        effective_elapsed = card.elapsed_days / profile.interference_resistance
        
        return (1 + self.parameters[5] * effective_elapsed / card.stability) ** (-1)
        
    def _update_difficulty(self, current_difficulty: float, outcome: ReviewOutcome,
                          profile: CognitiveMemoryProfile) -> float:
        """Update card difficulty based on review outcome"""
        difficulty_change = 0
        
        if outcome == ReviewOutcome.AGAIN:
            difficulty_change = self.parameters[6]
        elif outcome == ReviewOutcome.HARD:
            difficulty_change = self.parameters[12] * profile.difficulty_sensitivity
        elif outcome == ReviewOutcome.EASY:
            difficulty_change = -self.parameters[11] * profile.difficulty_sensitivity
            
        new_difficulty = current_difficulty + difficulty_change
        
        # Apply difficulty ceiling for cognitive impairments
        new_difficulty = min(new_difficulty, profile.max_difficulty_ceiling)
        new_difficulty = max(1.0, new_difficulty)  # Minimum difficulty of 1
        
        return new_difficulty
        
    def _calculate_failure_stability(self, card: CardState, 
                                   profile: CognitiveMemoryProfile) -> float:
        """Calculate new stability after failure"""
        new_stability = (self.parameters[16] + 
                        card.stability * self.parameters[8] * 
                        profile.stability_modifier)
        return max(self.parameters[16], new_stability)
        
    def _calculate_success_stability(self, card: CardState, outcome: ReviewOutcome,
                                   retrievability: float, 
                                   profile: CognitiveMemoryProfile) -> float:
        """Calculate new stability after success"""
        success_multiplier = 1.0
        
        if outcome == ReviewOutcome.HARD:
            success_multiplier = 1 + (self.parameters[7] - 1) * 0.5
        elif outcome == ReviewOutcome.EASY:
            success_multiplier = self.parameters[11]
            
        # Apply cognitive profile modifiers
        stability_growth = (card.stability * success_multiplier * 
                          profile.stability_modifier * 
                          profile.consolidation_speed)
        
        return max(card.stability, stability_growth)
        
    def _calculate_interval(self, stability: float, 
                           profile: CognitiveMemoryProfile) -> int:
        """Calculate review interval from stability"""
        interval = stability / math.log(1 / profile.retention_target)
        
        # Apply maximum interval limit
        interval = min(interval, profile.maximum_interval)
        
        return max(1, int(interval))
        
    def _apply_cognitive_adjustments(self, interval: int, outcome: ReviewOutcome,
                                   profile: CognitiveMemoryProfile, 
                                   card: CardState) -> int:
        """Apply cognitive-specific adjustments to interval"""
        
        # More frequent reviews for learning disabilities
        if profile.profile_type in [CognitiveProfile.LEARNING_DISABILITY,
                                   CognitiveProfile.WORKING_MEMORY_DEFICIT,
                                   CognitiveProfile.ATTENTION_DEFICIT]:
            interval = int(interval / profile.frequent_review_multiplier)
            
        # Reduce interval after failures for encouragement
        if outcome == ReviewOutcome.AGAIN:
            if profile.profile_type == CognitiveProfile.LEARNING_DISABILITY:
                interval = max(1, interval // 3)
            else:
                interval = max(1, interval // 2)
                
        # Ensure minimum interval for severe impairments
        if (card.lapses > 3 and 
            profile.profile_type == CognitiveProfile.LEARNING_DISABILITY):
            interval = min(interval, 3)  # Never more than 3 days after multiple lapses
            
        return max(1, interval)
        
    def get_encouragement_review_cards(self, user_id: str, 
                                     all_cards: List[CardState]) -> List[CardState]:
        """Get cards that need encouragement reviews"""
        profile = self.get_cognitive_profile(user_id)
        
        # Only apply for profiles that benefit from extra encouragement
        if profile.profile_type not in [CognitiveProfile.LEARNING_DISABILITY,
                                       CognitiveProfile.ATTENTION_DEFICIT,
                                       CognitiveProfile.AUTISM_SPECTRUM]:
            return []
            
        encouragement_cards = []
        current_time = datetime.now()
        
        for card in all_cards:
            # Cards with recent lapses
            if (card.lapses > 0 and 
                card.last_review and
                (current_time - card.last_review).days <= 7):
                encouragement_cards.append(card)
                continue
                
            # Cards marked for encouragement
            if card.encouragement_needed:
                encouragement_cards.append(card)
                
        return encouragement_cards[:5]  # Limit to 5 encouragement reviews
        
    def get_encouragement_message(self, user_id: str, card: CardState, 
                                outcome: ReviewOutcome) -> str:
        """Get appropriate encouragement message"""
        profile = self.get_cognitive_profile(user_id)
        
        if outcome == ReviewOutcome.AGAIN:
            messages = [
                "That's okay! Learning takes time and practice.",
                "Mistakes help us learn. Let's try again!",
                "You're building your understanding step by step.",
                "Every attempt makes you stronger!"
            ]
        elif outcome in [ReviewOutcome.HARD, ReviewOutcome.GOOD]:
            messages = [
                "Great effort! You're making progress!",
                "Well done! You stuck with it!",
                "Excellent! Your hard work is paying off!",
                "You should be proud of that improvement!"
            ]
        else:  # EASY
            messages = [
                "Fantastic! You've really mastered this!",
                "Outstanding! You make it look easy!",
                "Brilliant! Your knowledge is solid!",
                "Perfect! You're becoming an expert!"
            ]
            
        return random.choice(messages)
        
    def adapt_difficulty_ceiling(self, user_id: str, success_rate: float):
        """Adapt difficulty ceiling based on user's success rate"""
        if user_id not in self.cognitive_profiles:
            self.cognitive_profiles[user_id] = CognitiveMemoryProfile(
                profile_type=CognitiveProfile.STANDARD)
        
        profile = self.cognitive_profiles[user_id]
        
        if success_rate > 0.8:  # High success rate - can handle more difficulty
            profile.max_difficulty_ceiling = min(10.0, profile.max_difficulty_ceiling + 0.5)
        elif success_rate < 0.6:  # Low success rate - reduce difficulty
            profile.max_difficulty_ceiling = max(3.0, profile.max_difficulty_ceiling - 0.5)
            
    def get_review_session_config(self, user_id: str) -> Dict[str, Any]:
        """Get review session configuration based on cognitive profile"""
        profile = self.get_cognitive_profile(user_id)
        
        config = {
            "max_new_cards": 10,
            "max_review_cards": 20,
            "session_time_limit": 30,  # minutes
            "break_frequency": 10,  # cards between breaks
            "encouragement_frequency": 5,  # positive messages every N cards
            "allow_hints": False,
            "show_progress": True
        }
        
        # Adjust for cognitive profiles
        if profile.profile_type == CognitiveProfile.ATTENTION_DEFICIT:
            config.update({
                "max_new_cards": 5,
                "max_review_cards": 15,
                "session_time_limit": 20,
                "break_frequency": 5,
                "encouragement_frequency": 3
            })
            
        elif profile.profile_type == CognitiveProfile.LEARNING_DISABILITY:
            config.update({
                "max_new_cards": 3,
                "max_review_cards": 10,
                "session_time_limit": 25,
                "break_frequency": 5,
                "encouragement_frequency": 2,
                "allow_hints": True
            })
            
        elif profile.profile_type == CognitiveProfile.WORKING_MEMORY_DEFICIT:
            config.update({
                "max_new_cards": 5,
                "max_review_cards": 12,
                "break_frequency": 7,
                "encouragement_frequency": 4
            })
            
        elif profile.profile_type == CognitiveProfile.AUTISM_SPECTRUM:
            config.update({
                "encouragement_frequency": 3,
                "show_progress": True,  # Clear progress indication is helpful
                "allow_hints": True
            })
            
        return config
        
    def generate_performance_report(self, user_id: str, 
                                  cards: List[CardState]) -> Dict[str, Any]:
        """Generate performance report adapted for cognitive profile"""
        profile = self.get_cognitive_profile(user_id)
        
        # Basic statistics
        total_reviews = sum(card.review_count for card in cards)
        total_lapses = sum(card.lapses for card in cards)
        
        success_rate = 1.0 - (total_lapses / max(1, total_reviews))
        
        # Cognitive-specific insights
        report = {
            "total_cards": len(cards),
            "total_reviews": total_reviews,
            "success_rate": success_rate,
            "average_difficulty": sum(card.difficulty for card in cards) / max(1, len(cards)),
            "profile_type": profile.profile_type.value,
            "encouragement_cards": len([c for c in cards if c.encouragement_needed]),
            "recommendations": []
        }
        
        # Add recommendations based on performance
        if success_rate < 0.7:
            report["recommendations"].append(
                "Consider using simplified explanations and more frequent reviews."
            )
            
        if profile.profile_type == CognitiveProfile.ATTENTION_DEFICIT and total_reviews > 0:
            avg_reviews_per_card = total_reviews / len(cards)
            if avg_reviews_per_card > 5:
                report["recommendations"].append(
                    "Try shorter, more frequent study sessions to improve focus."
                )
                
        return report