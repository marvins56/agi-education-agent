"""Dynamic difficulty calibration system."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics

from src.adaptive.schemas import (
    KnowledgeState, DifficultyCalibration, StudentInteraction,
    HistoryKnowledgeGraph, LearningObjective
)

logger = logging.getLogger(__name__)


class DifficultyCalibrator:
    """Dynamic difficulty calibration system for personalized learning."""
    
    def __init__(self, knowledge_graph: HistoryKnowledgeGraph):
        self.knowledge_graph = knowledge_graph
        
        # Calibration parameters
        self.target_success_rate = 0.75  # Target 75% success rate
        self.adjustment_rate = 0.1       # How quickly to adjust difficulty
        self.min_interactions_for_calibration = 3  # Minimum data points
        
        # Bloom's taxonomy difficulty multipliers
        self.bloom_multipliers = {
            LearningObjective.REMEMBER: 0.8,     # Easier
            LearningObjective.UNDERSTAND: 1.0,   # Base difficulty
            LearningObjective.APPLY: 1.2,        # Harder
            LearningObjective.ANALYZE: 1.4,      # Much harder
            LearningObjective.EVALUATE: 1.6,     # Very hard
            LearningObjective.CREATE: 1.8,       # Hardest
        }
    
    async def calibrate_difficulty(
        self,
        concept_name: str,
        student_knowledge_state: KnowledgeState,
        student_id: str,
        learning_objective: LearningObjective = LearningObjective.UNDERSTAND,
        recent_interactions: List[StudentInteraction] = None
    ) -> float:
        """Calibrate difficulty for a specific concept and student."""
        
        # Get base difficulty from knowledge graph
        base_difficulty = self._get_concept_base_difficulty(concept_name)
        
        # Get current student mastery for this concept
        current_mastery = student_knowledge_state.concept_probabilities.get(concept_name, 0.0)
        
        # Adjust based on mastery level
        mastery_adjustment = self._calculate_mastery_adjustment(current_mastery)
        
        # Adjust based on learning objective (Bloom's taxonomy)
        objective_multiplier = self.bloom_multipliers.get(learning_objective, 1.0)
        
        # Adjust based on recent performance
        performance_adjustment = 0.0
        if recent_interactions:
            performance_adjustment = await self._calculate_performance_adjustment(
                concept_name, recent_interactions
            )
        
        # Adjust based on prerequisite mastery
        prerequisite_adjustment = self._calculate_prerequisite_adjustment(
            concept_name, student_knowledge_state
        )
        
        # Adjust based on student learning characteristics
        student_adjustment = self._calculate_student_adjustment(student_knowledge_state)
        
        # Combine all adjustments
        calibrated_difficulty = base_difficulty * objective_multiplier
        calibrated_difficulty += mastery_adjustment
        calibrated_difficulty += performance_adjustment
        calibrated_difficulty += prerequisite_adjustment
        calibrated_difficulty += student_adjustment
        
        # Clamp to valid range
        final_difficulty = max(0.1, min(1.0, calibrated_difficulty))
        
        logger.debug(
            f"Calibrated difficulty for {concept_name}: {final_difficulty:.2f} "
            f"(base: {base_difficulty:.2f}, mastery_adj: {mastery_adjustment:.2f}, "
            f"perf_adj: {performance_adjustment:.2f})"
        )
        
        return final_difficulty
    
    def _get_concept_base_difficulty(self, concept_name: str) -> float:
        """Get base difficulty from knowledge graph."""
        
        for concept_id, concept in self.knowledge_graph.concepts.items():
            if concept.concept_name == concept_name:
                return concept.difficulty
        
        # Default difficulty if concept not found
        return 0.5
    
    def _calculate_mastery_adjustment(self, current_mastery: float) -> float:
        """Calculate difficulty adjustment based on current mastery."""
        
        # If mastery is high, increase difficulty slightly
        # If mastery is low, decrease difficulty
        optimal_mastery = 0.7  # Target mastery level for optimal challenge
        
        mastery_gap = current_mastery - optimal_mastery
        
        # Adjustment is proportional to gap from optimal
        # Positive gap (high mastery) -> increase difficulty
        # Negative gap (low mastery) -> decrease difficulty
        adjustment = mastery_gap * 0.3
        
        return adjustment
    
    async def _calculate_performance_adjustment(
        self,
        concept_name: str,
        interactions: List[StudentInteraction]
    ) -> float:
        """Calculate adjustment based on recent performance."""
        
        # Filter interactions for this concept
        concept_interactions = [
            i for i in interactions if i.concept_name == concept_name
        ]
        
        if len(concept_interactions) < 2:
            return 0.0
        
        # Get recent performance (last 5 interactions)
        recent_interactions = concept_interactions[-5:]
        recent_correctness = [i.correctness for i in recent_interactions]
        avg_correctness = statistics.mean(recent_correctness)
        
        # Calculate adjustment based on performance vs target
        performance_gap = avg_correctness - self.target_success_rate
        
        # If performing too well, increase difficulty
        # If performing poorly, decrease difficulty
        adjustment = -performance_gap * 0.2  # Negative because we want inverse relationship
        
        # Consider response time patterns
        response_times = [i.response_time_seconds for i in recent_interactions]
        avg_response_time = statistics.mean(response_times)
        
        # Very fast responses might indicate too easy
        if avg_response_time < 10:  # Less than 10 seconds average
            adjustment += 0.1  # Make slightly harder
        elif avg_response_time > 60:  # More than 1 minute average
            adjustment -= 0.1  # Make slightly easier
        
        return adjustment
    
    def _calculate_prerequisite_adjustment(
        self,
        concept_name: str,
        knowledge_state: KnowledgeState
    ) -> float:
        """Adjust difficulty based on prerequisite concept mastery."""
        
        # Find concept in knowledge graph
        concept_id = None
        for cid, concept in self.knowledge_graph.concepts.items():
            if concept.concept_name == concept_name:
                concept_id = cid
                break
        
        if concept_id is None:
            return 0.0
        
        concept = self.knowledge_graph.concepts[concept_id]
        
        if not concept.prerequisites:
            return 0.0
        
        # Check mastery of prerequisite concepts
        prerequisite_masteries = []
        for prereq_id in concept.prerequisites:
            prereq_concept = self.knowledge_graph.concepts.get(prereq_id)
            if prereq_concept:
                prereq_mastery = knowledge_state.concept_probabilities.get(
                    prereq_concept.concept_name, 0.0
                )
                prerequisite_masteries.append(prereq_mastery)
        
        if not prerequisite_masteries:
            return 0.0
        
        # If prerequisites are well-mastered, can handle higher difficulty
        # If prerequisites are weak, need lower difficulty
        avg_prerequisite_mastery = statistics.mean(prerequisite_masteries)
        min_prerequisite_mastery = min(prerequisite_masteries)
        
        # Use minimum mastery as it's the weakest link
        if min_prerequisite_mastery < 0.6:  # Weak prerequisites
            return -0.2  # Reduce difficulty significantly
        elif avg_prerequisite_mastery > 0.8:  # Strong prerequisites
            return 0.1   # Can handle slightly more difficulty
        
        return 0.0
    
    def _calculate_student_adjustment(self, knowledge_state: KnowledgeState) -> float:
        """Adjust based on overall student learning characteristics."""
        
        adjustment = 0.0
        
        # Learning efficiency adjustment
        if knowledge_state.learning_efficiency > 0.8:  # Fast learner
            adjustment += 0.1  # Can handle more difficulty
        elif knowledge_state.learning_efficiency < 0.4:  # Slower learner
            adjustment -= 0.1  # Needs easier content
        
        # Knowledge growth rate adjustment
        if knowledge_state.knowledge_growth_rate > 0.7:  # Rapid growth
            adjustment += 0.05
        elif knowledge_state.knowledge_growth_rate < 0.3:  # Slow growth
            adjustment -= 0.05
        
        return adjustment
    
    async def update_calibration_record(
        self,
        student_id: str,
        concept_name: str,
        used_difficulty: float,
        actual_performance: float,
        response_time_seconds: float
    ) -> DifficultyCalibration:
        """Update calibration record with new performance data."""
        
        # This would typically load from database
        calibration = DifficultyCalibration(
            concept_name=concept_name,
            student_id=student_id,
            current_difficulty=used_difficulty,
            actual_success_rate=actual_performance
        )
        
        # Update history
        calibration.difficulty_history.append((datetime.now(), used_difficulty))
        calibration.performance_history.append((datetime.now(), actual_performance))
        
        # Calculate new target difficulty based on performance
        success_gap = actual_performance - self.target_success_rate
        
        if abs(success_gap) > 0.1:  # Significant gap from target
            # Adjust difficulty for next time
            if success_gap > 0.1:  # Too easy
                calibration.current_difficulty = min(1.0, used_difficulty + self.adjustment_rate)
            else:  # Too hard
                calibration.current_difficulty = max(0.1, used_difficulty - self.adjustment_rate)
        
        calibration.last_calibrated = datetime.now()
        
        return calibration
    
    def get_optimal_difficulty_sequence(
        self,
        student_id: str,
        concept_sequence: List[str],
        knowledge_state: KnowledgeState,
        target_session_success_rate: float = 0.75
    ) -> List[Tuple[str, float]]:
        """Get optimal difficulty sequence for a learning session."""
        
        difficulty_sequence = []
        
        # Start slightly easier to build confidence
        difficulty_modifier = -0.1
        
        for i, concept_name in enumerate(concept_sequence):
            base_difficulty = self._get_concept_base_difficulty(concept_name)
            
            # Gradually increase challenge through session
            progress_bonus = (i / len(concept_sequence)) * 0.1
            
            # Adjust based on knowledge state
            mastery_adjustment = self._calculate_mastery_adjustment(
                knowledge_state.concept_probabilities.get(concept_name, 0.0)
            )
            
            optimal_difficulty = base_difficulty + difficulty_modifier + progress_bonus + mastery_adjustment
            optimal_difficulty = max(0.1, min(1.0, optimal_difficulty))
            
            difficulty_sequence.append((concept_name, optimal_difficulty))
        
        return difficulty_sequence
    
    def analyze_difficulty_trends(
        self,
        student_id: str,
        interactions: List[StudentInteraction],
        time_window_days: int = 7
    ) -> Dict[str, float]:
        """Analyze difficulty trends over time."""
        
        # Filter recent interactions
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        recent_interactions = [
            i for i in interactions 
            if i.timestamp >= cutoff_date
        ]
        
        if not recent_interactions:
            return {}
        
        # Group by concept
        concept_trends = {}
        
        for concept_name in set(i.concept_name for i in recent_interactions):
            concept_interactions = [
                i for i in recent_interactions 
                if i.concept_name == concept_name
            ]
            
            if len(concept_interactions) < 2:
                continue
            
            # Sort by timestamp
            concept_interactions.sort(key=lambda x: x.timestamp)
            
            # Calculate trend in performance
            first_half = concept_interactions[:len(concept_interactions)//2]
            second_half = concept_interactions[len(concept_interactions)//2:]
            
            first_avg = statistics.mean(i.correctness for i in first_half)
            second_avg = statistics.mean(i.correctness for i in second_half)
            
            trend = second_avg - first_avg
            concept_trends[concept_name] = trend
        
        return concept_trends
    
    def recommend_difficulty_adjustments(
        self,
        trends: Dict[str, float],
        threshold: float = 0.1
    ) -> Dict[str, str]:
        """Recommend difficulty adjustments based on trends."""
        
        recommendations = {}
        
        for concept_name, trend in trends.items():
            if trend > threshold:  # Improving performance
                recommendations[concept_name] = "increase_difficulty"
            elif trend < -threshold:  # Declining performance
                recommendations[concept_name] = "decrease_difficulty"
            else:  # Stable performance
                recommendations[concept_name] = "maintain_difficulty"
        
        return recommendations