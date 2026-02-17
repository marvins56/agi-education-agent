"""Practical knowledge tracing predictor (rule-based BKT for now)."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import math

from src.adaptive.schemas import StudentInteraction, KnowledgeState, ConceptEmbedding

logger = logging.getLogger(__name__)


class RuleBasedBKTPredictor:
    """Rule-based Bayesian Knowledge Tracing predictor.
    
    This is structured to be easily replaceable with a neural DKT model later.
    Uses classical BKT parameters but with History-specific adjustments.
    """
    
    def __init__(self):
        # BKT Parameters (can be tuned per concept type)
        self.default_params = {
            "prior_knowledge": 0.1,        # P(L0) - initial knowledge probability
            "learning_rate": 0.3,          # P(T) - probability of learning
            "slip_rate": 0.1,              # P(S) - probability of slip (know but answer wrong)
            "guess_rate": 0.25,            # P(G) - probability of guess (don't know but answer right)
        }
        
        # History-specific parameter adjustments
        self.history_concept_params = {
            "dates_specific": {
                "prior_knowledge": 0.05,    # Dates start lower
                "learning_rate": 0.4,       # But learn quickly
                "slip_rate": 0.15,          # Higher slip for memorization
                "guess_rate": 0.2,          # Lower guess rate
            },
            "causal_relationships": {
                "prior_knowledge": 0.15,    # Some prior understanding
                "learning_rate": 0.25,      # Slower to learn complex concepts
                "slip_rate": 0.08,          # Less slipping once learned
                "guess_rate": 0.3,          # Higher guess rate for complex
            },
            "political_concepts": {
                "prior_knowledge": 0.12,
                "learning_rate": 0.3,
                "slip_rate": 0.1,
                "guess_rate": 0.25,
            },
            "social_cultural": {
                "prior_knowledge": 0.2,     # More intuitive concepts
                "learning_rate": 0.35,
                "slip_rate": 0.12,
                "guess_rate": 0.2,
            }
        }
        
        # Forgetting curve parameters
        self.forgetting_params = {
            "half_life_days": 14,           # How long to forget 50%
            "minimum_retention": 0.1,       # Minimum retained knowledge
        }
    
    async def predict_mastery(
        self,
        student_id: str,
        interaction_history: List[StudentInteraction]
    ) -> Dict[str, float]:
        """Predict mastery probabilities for all concepts."""
        
        concept_masteries = {}
        
        # Group interactions by concept
        concept_interactions = self._group_by_concept(interaction_history)
        
        for concept_name, interactions in concept_interactions.items():
            mastery_prob = self._calculate_concept_mastery(concept_name, interactions)
            concept_masteries[concept_name] = mastery_prob
        
        return concept_masteries
    
    def _group_by_concept(
        self,
        interactions: List[StudentInteraction]
    ) -> Dict[str, List[StudentInteraction]]:
        """Group interactions by concept name."""
        grouped = {}
        for interaction in interactions:
            if interaction.concept_name not in grouped:
                grouped[interaction.concept_name] = []
            grouped[interaction.concept_name].append(interaction)
        
        # Sort each concept's interactions by timestamp
        for concept_name in grouped:
            grouped[concept_name].sort(key=lambda x: x.timestamp)
        
        return grouped
    
    def _calculate_concept_mastery(
        self,
        concept_name: str,
        interactions: List[StudentInteraction]
    ) -> float:
        """Calculate mastery probability for a single concept using BKT."""
        
        if not interactions:
            return 0.0
        
        # Get concept-specific parameters
        params = self._get_concept_params(concept_name)
        
        # Start with prior knowledge
        mastery_prob = params["prior_knowledge"]
        
        # Process each interaction sequentially
        for interaction in interactions:
            mastery_prob = self._update_mastery_bkt(
                mastery_prob, interaction, params
            )
        
        # Apply forgetting based on time since last interaction
        if interactions:
            last_interaction = interactions[-1]
            mastery_prob = self._apply_forgetting(mastery_prob, last_interaction.timestamp)
        
        return min(0.99, max(0.01, mastery_prob))  # Clamp to reasonable bounds
    
    def _get_concept_params(self, concept_name: str) -> Dict[str, float]:
        """Get BKT parameters for a specific concept type."""
        concept_type = self._classify_concept(concept_name)
        
        if concept_type in self.history_concept_params:
            return self.history_concept_params[concept_type]
        else:
            return self.default_params
    
    def _classify_concept(self, concept_name: str) -> str:
        """Classify concept type for parameter selection."""
        name_lower = concept_name.lower()
        
        # Check for date/year patterns
        if any(char.isdigit() for char in concept_name) and any(
            word in name_lower for word in ["year", "date", "century", "bc", "ad"]
        ):
            return "dates_specific"
        
        # Check for causal relationship keywords
        if any(word in name_lower for word in ["cause", "effect", "led to", "result", "because"]):
            return "causal_relationships"
        
        # Check for political concepts
        if any(word in name_lower for word in ["government", "politics", "power", "rule", "empire"]):
            return "political_concepts"
        
        # Check for social/cultural concepts
        if any(word in name_lower for word in ["culture", "society", "religion", "belief", "custom"]):
            return "social_cultural"
        
        return "default"
    
    def _update_mastery_bkt(
        self,
        prior_mastery: float,
        interaction: StudentInteraction,
        params: Dict[str, float]
    ) -> float:
        """Update mastery probability using BKT update rules."""
        
        # BKT update formula
        # P(L_n+1 = 1 | evidence) 
        
        correctness = interaction.correctness
        learning_rate = params["learning_rate"]
        slip_rate = params["slip_rate"]
        guess_rate = params["guess_rate"]
        
        # Apply difficulty and hint adjustments
        adjusted_learning_rate = self._adjust_learning_rate(
            learning_rate, interaction
        )
        
        # Calculate probability of correct answer given current mastery
        if correctness >= 0.5:  # Correct answer
            # P(correct | learned) * P(learned) + P(correct | not learned) * P(not learned)
            prob_correct_given_evidence = (
                (1 - slip_rate) * prior_mastery + guess_rate * (1 - prior_mastery)
            )
            
            # Bayesian update: P(learned | correct)
            if prob_correct_given_evidence > 0:
                posterior_mastery = (
                    (1 - slip_rate) * prior_mastery / prob_correct_given_evidence
                )
            else:
                posterior_mastery = prior_mastery
        
        else:  # Incorrect answer
            # P(incorrect | learned) * P(learned) + P(incorrect | not learned) * P(not learned)
            prob_incorrect_given_evidence = (
                slip_rate * prior_mastery + (1 - guess_rate) * (1 - prior_mastery)
            )
            
            # Bayesian update: P(learned | incorrect)
            if prob_incorrect_given_evidence > 0:
                posterior_mastery = (
                    slip_rate * prior_mastery / prob_incorrect_given_evidence
                )
            else:
                posterior_mastery = prior_mastery
        
        # Apply learning: P(learned_next) = P(learned_current) + P(not learned) * P(transit)
        final_mastery = posterior_mastery + (1 - posterior_mastery) * adjusted_learning_rate
        
        return min(0.99, max(0.01, final_mastery))
    
    def _adjust_learning_rate(
        self,
        base_learning_rate: float,
        interaction: StudentInteraction
    ) -> float:
        """Adjust learning rate based on interaction context."""
        
        adjusted_rate = base_learning_rate
        
        # Difficulty adjustment - harder questions provide more learning
        difficulty_bonus = (interaction.difficulty_level - 0.5) * 0.1
        adjusted_rate += difficulty_bonus
        
        # Hint penalty - using hints reduces learning
        if interaction.hint_count > 0:
            hint_penalty = min(0.2, interaction.hint_count * 0.05)
            adjusted_rate -= hint_penalty
        
        # Response time adjustment - too quick might be guessing
        if interaction.response_time_seconds < 5:  # Very quick response
            adjusted_rate *= 0.8
        elif interaction.response_time_seconds > 30:  # Very slow, might indicate struggle
            adjusted_rate *= 1.2
        
        return max(0.01, min(0.8, adjusted_rate))
    
    def _apply_forgetting(self, mastery_prob: float, last_interaction_time: datetime) -> float:
        """Apply forgetting curve to mastery probability."""
        
        days_since = (datetime.now() - last_interaction_time).total_seconds() / 86400
        
        if days_since <= 0:
            return mastery_prob
        
        # Exponential decay with configurable half-life
        half_life = self.forgetting_params["half_life_days"]
        min_retention = self.forgetting_params["minimum_retention"]
        
        # Calculate retention based on exponential decay
        retention_factor = math.pow(0.5, days_since / half_life)
        
        # Apply retention, but don't go below minimum
        decayed_mastery = mastery_prob * retention_factor
        final_mastery = max(min_retention, decayed_mastery)
        
        return final_mastery
    
    def predict_performance(
        self,
        concept_name: str,
        current_mastery: float,
        question_difficulty: float = 0.5
    ) -> Tuple[float, Dict[str, float]]:
        """Predict performance on a question given current mastery."""
        
        params = self._get_concept_params(concept_name)
        
        # Adjust parameters based on question difficulty
        adjusted_slip = params["slip_rate"] * (1 + question_difficulty)
        adjusted_guess = params["guess_rate"] * (2 - question_difficulty)
        
        # Probability of correct answer
        prob_correct = (
            (1 - adjusted_slip) * current_mastery + 
            adjusted_guess * (1 - current_mastery)
        )
        
        # Additional metrics
        metrics = {
            "expected_correctness": prob_correct,
            "confidence_interval_lower": max(0.0, prob_correct - 0.1),
            "confidence_interval_upper": min(1.0, prob_correct + 0.1),
            "mastery_probability": current_mastery,
            "difficulty_adjusted_slip": adjusted_slip,
            "difficulty_adjusted_guess": adjusted_guess,
        }
        
        return prob_correct, metrics
    
    def get_learning_trajectory(
        self,
        concept_name: str,
        interactions: List[StudentInteraction]
    ) -> List[Tuple[datetime, float]]:
        """Get the learning trajectory for a concept over time."""
        
        trajectory = []
        params = self._get_concept_params(concept_name)
        mastery_prob = params["prior_knowledge"]
        
        # Add initial point
        if interactions:
            trajectory.append((interactions[0].timestamp, mastery_prob))
        
        # Calculate mastery after each interaction
        for interaction in interactions:
            mastery_prob = self._update_mastery_bkt(mastery_prob, interaction, params)
            trajectory.append((interaction.timestamp, mastery_prob))
        
        return trajectory
    
    def detect_learning_plateau(
        self,
        concept_name: str,
        interactions: List[StudentInteraction],
        window_size: int = 5
    ) -> bool:
        """Detect if student has plateaued in learning a concept."""
        
        if len(interactions) < window_size * 2:
            return False
        
        # Get recent trajectory
        trajectory = self.get_learning_trajectory(concept_name, interactions)
        
        if len(trajectory) < window_size * 2:
            return False
        
        # Check if recent progress is minimal
        recent_points = trajectory[-window_size:]
        earlier_points = trajectory[-window_size*2:-window_size]
        
        recent_avg = sum(point[1] for point in recent_points) / len(recent_points)
        earlier_avg = sum(point[1] for point in earlier_points) / len(earlier_points)
        
        # Plateau if improvement is less than 5% over the window
        improvement = recent_avg - earlier_avg
        plateau_threshold = 0.05
        
        return improvement < plateau_threshold and recent_avg < 0.8  # Not already mastered