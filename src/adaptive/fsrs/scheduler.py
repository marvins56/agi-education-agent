"""Free-Spaced Repetition Scheduler (FSRS) implementation."""
import math
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import numpy as np

from src.adaptive.schemas import FSRSCard


@dataclass
class FSRSParameters:
    """FSRS algorithm parameters optimized for educational content."""
    # Request retention rate (target recall probability)
    request_retention: float = 0.9
    
    # Maximum interval in days
    maximum_interval: float = 36500.0  # ~100 years
    
    # FSRS-4.5 parameters (optimized for spaced repetition)
    w: List[float] = None
    
    def __post_init__(self):
        if self.w is None:
            # Default parameters optimized for educational content
            self.w = [
                0.4072,   # initial_stability_good
                1.1829,   # initial_stability_easy  
                3.1262,   # initial_stability_hard
                15.4722,  # initial_stability_again
                7.2102,   # initial_difficulty
                0.5316,   # difficulty_decay_factor
                1.0651,   # stability_decay_factor
                0.0234,   # increasing_factor
                1.616,    # hard_penalty
                0.1544,   # easy_bonus
            ]


class FSRSScheduler:
    """Free-Spaced Repetition Scheduler for optimal review timing."""
    
    def __init__(self, parameters: FSRSParameters = None):
        self.params = parameters or FSRSParameters()
        self.history_concept_weights = self._get_history_concept_weights()
    
    def _get_history_concept_weights(self) -> Dict[str, float]:
        """Get importance weights for different History concept types."""
        return {
            "political_causes": 1.3,      # High importance
            "economic_factors": 1.2,      
            "social_movements": 1.1,
            "military_strategy": 1.0,     # Base importance
            "cultural_aspects": 0.9,
            "biographical": 0.8,          # Lower priority for memorization
            "dates_specific": 0.7,        # Dates less critical than concepts
        }
    
    def schedule_review(
        self,
        card: FSRSCard,
        rating: int,        # 1=Again, 2=Hard, 3=Good, 4=Easy
        now: datetime = None
    ) -> FSRSCard:
        """Schedule next review for a concept card."""
        if now is None:
            now = datetime.now()
        
        # Update card state based on performance
        updated_card = self._update_card_state(card, rating, now)
        
        # Calculate new interval
        interval_days = self._calculate_interval(updated_card, rating)
        
        # Apply History-specific adjustments
        interval_days = self._apply_history_adjustments(
            updated_card, interval_days, rating
        )
        
        # Set due date
        updated_card.due_date = now + timedelta(days=interval_days)
        updated_card.last_review = now
        updated_card.review_count += 1
        
        # Update performance tracking
        updated_card = self._update_performance_metrics(updated_card, rating)
        
        return updated_card
    
    def _update_card_state(self, card: FSRSCard, rating: int, now: datetime) -> FSRSCard:
        """Update card's memory parameters based on performance."""
        # Create new card instance to avoid modifying original
        new_card = FSRSCard(
            concept_id=card.concept_id,
            concept_name=card.concept_name,
            student_id=card.student_id,
            stability=card.stability,
            difficulty=card.difficulty,
            retrievability=card.retrievability,
            due_date=card.due_date,
            last_review=card.last_review,
            review_count=card.review_count,
            average_response_time=card.average_response_time,
            success_rate=card.success_rate,
            consecutive_successes=card.consecutive_successes
        )
        
        # Calculate elapsed days since last review
        if card.last_review:
            elapsed_days = (now - card.last_review).total_seconds() / 86400
            # Update retrievability based on elapsed time
            new_card.retrievability = self._calculate_retrievability(
                card.stability, elapsed_days
            )
        else:
            elapsed_days = 0
            new_card.retrievability = 1.0
        
        # Update difficulty based on performance
        if card.review_count > 0:  # Not first review
            new_card.difficulty = self._update_difficulty(card.difficulty, rating)
        
        return new_card
    
    def _calculate_retrievability(self, stability: float, elapsed_days: float) -> float:
        """Calculate current retrievability based on forgetting curve."""
        if elapsed_days <= 0:
            return 1.0
        
        # Exponential forgetting curve
        retrievability = math.pow(1 + elapsed_days / (9 * stability), -1)
        return max(0.01, min(1.0, retrievability))
    
    def _calculate_interval(self, card: FSRSCard, rating: int) -> float:
        """Calculate the next review interval."""
        if card.review_count == 0:
            # First review - use initial stability
            return self._get_initial_stability(rating)
        
        # Calculate new stability based on current state and performance
        current_retrievability = card.retrievability
        new_stability = self._calculate_new_stability(
            card.stability, card.difficulty, rating, current_retrievability
        )
        
        # Calculate interval to reach target retention
        interval = new_stability * (
            math.pow(self.params.request_retention, 1/9) - 1
        ) * 9
        
        # Apply bounds
        interval = max(1.0, min(self.params.maximum_interval, interval))
        
        return interval
    
    def _get_initial_stability(self, rating: int) -> float:
        """Get initial stability for first review."""
        stability_map = {
            1: self.params.w[3],  # again - very short interval
            2: self.params.w[2],  # hard - short interval
            3: self.params.w[0],  # good - medium interval
            4: self.params.w[1],  # easy - longer interval
        }
        return stability_map.get(rating, self.params.w[0])
    
    def _calculate_new_stability(
        self,
        old_stability: float,
        difficulty: float,
        rating: int,
        retrievability: float
    ) -> float:
        """Calculate new memory stability after review."""
        # Base stability calculation from FSRS algorithm
        if rating == 1:  # Again
            new_stability = old_stability * math.pow(
                self.params.w[6], math.pow(difficulty - 1, self.params.w[5])
            )
        else:  # Hard, Good, Easy
            success_rate = 1.0  # Successful recall
            if rating == 2:  # Hard
                success_rate *= self.params.w[8]  # Apply hard penalty
            elif rating == 4:  # Easy
                success_rate *= self.params.w[9]  # Apply easy bonus
            
            new_stability = old_stability * (
                1 + (math.exp(self.params.w[7]) - 1) * 
                success_rate * math.pow(retrievability, self.params.w[4])
            )
        
        return max(0.1, new_stability)  # Minimum stability
    
    def _update_difficulty(self, old_difficulty: float, rating: int) -> float:
        """Update concept difficulty based on performance."""
        # FSRS difficulty update formula
        difficulty_change = {
            1: 0.2,   # Again - increase difficulty
            2: 0.1,   # Hard - slight increase
            3: -0.05, # Good - slight decrease
            4: -0.15, # Easy - decrease difficulty
        }
        
        change = difficulty_change.get(rating, 0)
        new_difficulty = old_difficulty + change
        
        # Clamp difficulty between 1 and 10
        return max(1.0, min(10.0, new_difficulty))
    
    def _apply_history_adjustments(
        self,
        card: FSRSCard,
        base_interval: float,
        rating: int
    ) -> float:
        """Apply History-specific scheduling adjustments."""
        
        # Determine concept type from name
        concept_type = self._classify_history_concept(card.concept_name)
        weight = self.history_concept_weights.get(concept_type, 1.0)
        
        # High-importance concepts reviewed more frequently
        if weight > 1.1:
            base_interval *= 0.8  # 20% shorter intervals
        elif weight < 0.9:
            base_interval *= 1.3  # 30% longer intervals
        
        # Adjust based on concept complexity patterns
        if "cause" in card.concept_name.lower() or "effect" in card.concept_name.lower():
            # Causal relationships need more frequent review
            base_interval *= 0.9
        
        if "timeline" in card.concept_name.lower() or "chronol" in card.concept_name.lower():
            # Chronological concepts benefit from regular practice
            base_interval *= 0.85
        
        # Performance-based adjustments
        if card.success_rate < 0.6 and card.review_count > 2:
            # Struggling concepts need more frequent review
            base_interval *= 0.7
        elif card.success_rate > 0.9 and card.consecutive_successes > 3:
            # Well-mastered concepts can wait longer
            base_interval *= 1.2
        
        return base_interval
    
    def _classify_history_concept(self, concept_name: str) -> str:
        """Classify History concept type for scheduling adjustments."""
        name_lower = concept_name.lower()
        
        political_keywords = ["government", "politics", "power", "ruler", "revolution"]
        economic_keywords = ["economy", "trade", "money", "wealth", "commerce"]
        social_keywords = ["society", "culture", "people", "movement", "rights"]
        military_keywords = ["war", "battle", "military", "army", "weapon"]
        
        if any(keyword in name_lower for keyword in political_keywords):
            return "political_causes"
        elif any(keyword in name_lower for keyword in economic_keywords):
            return "economic_factors"
        elif any(keyword in name_lower for keyword in social_keywords):
            return "social_movements"
        elif any(keyword in name_lower for keyword in military_keywords):
            return "military_strategy"
        elif any(char.isdigit() for char in concept_name):
            return "dates_specific"
        else:
            return "cultural_aspects"
    
    def _update_performance_metrics(self, card: FSRSCard, rating: int) -> FSRSCard:
        """Update performance tracking metrics."""
        # Update success rate (exponential moving average)
        success = 1.0 if rating >= 3 else 0.0  # Good or Easy = success
        alpha = 0.1  # Learning rate for moving average
        card.success_rate = (1 - alpha) * card.success_rate + alpha * success
        
        # Update consecutive successes
        if rating >= 3:
            card.consecutive_successes += 1
        else:
            card.consecutive_successes = 0
        
        return card
    
    def get_due_cards(
        self,
        cards: List[FSRSCard],
        now: datetime = None
    ) -> List[FSRSCard]:
        """Get all cards due for review."""
        if now is None:
            now = datetime.now()
        
        due_cards = [card for card in cards if card.due_date <= now]
        
        # Sort by priority (overdue first, then by importance)
        due_cards.sort(key=lambda card: (
            (now - card.due_date).total_seconds(),  # How overdue
            -self.history_concept_weights.get(
                self._classify_history_concept(card.concept_name), 1.0
            )  # Importance (negative for descending sort)
        ))
        
        return due_cards
    
    def optimize_study_session(
        self,
        available_cards: List[FSRSCard],
        session_duration_minutes: int = 30,
        now: datetime = None
    ) -> List[FSRSCard]:
        """Select optimal cards for a study session."""
        if now is None:
            now = datetime.now()
        
        # Get due cards
        due_cards = self.get_due_cards(available_cards, now)
        
        # Estimate time per card (average 2-3 minutes)
        avg_time_per_card = 2.5
        max_cards = int(session_duration_minutes / avg_time_per_card)
        
        # Select high-priority cards that fit in time budget
        selected_cards = due_cards[:max_cards]
        
        # Fill remaining time with preview cards (new concepts)
        remaining_time = session_duration_minutes - len(selected_cards) * avg_time_per_card
        if remaining_time >= avg_time_per_card:
            new_cards = [card for card in available_cards if card.review_count == 0]
            additional_cards = min(
                int(remaining_time / avg_time_per_card),
                len(new_cards)
            )
            selected_cards.extend(new_cards[:additional_cards])
        
        return selected_cards