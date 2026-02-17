"""Main adaptive learning engine orchestrating all components."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

from src.adaptive.schemas import (
    StudentInteraction, KnowledgeState, AdaptiveRecommendation,
    FSRSCard, ConceptEmbedding, LearningStyleProfile
)
from src.adaptive.dkt.predictor import RuleBasedBKTPredictor
from src.adaptive.fsrs.scheduler import FSRSScheduler
from src.adaptive.knowledge_graph.history_graph import build_history_knowledge_graph
from src.adaptive.difficulty.calibrator import DifficultyCalibrator
from src.adaptive.personalization.learning_style_detector import LearningStyleDetector
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """Main engine for personalized adaptive learning."""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        
        # Initialize components
        self.knowledge_predictor = RuleBasedBKTPredictor()
        self.fsrs_scheduler = FSRSScheduler()
        self.knowledge_graph = build_history_knowledge_graph()
        self.difficulty_calibrator = DifficultyCalibrator(self.knowledge_graph)
        self.learning_style_detector = LearningStyleDetector()
        
        # Cache for performance
        self._knowledge_state_cache: Dict[str, KnowledgeState] = {}
        self._fsrs_card_cache: Dict[str, List[FSRSCard]] = {}
        self._cache_ttl_minutes = 15
    
    async def update_student_knowledge(
        self,
        student_id: str,
        interaction: StudentInteraction
    ) -> KnowledgeState:
        """Update student's knowledge state after a learning interaction."""
        
        try:
            # Get interaction history
            interaction_history = await self._get_interaction_history(student_id, limit=50)
            interaction_history.append(interaction)
            
            # Predict updated knowledge state using BKT
            concept_masteries = await self.knowledge_predictor.predict_mastery(
                student_id, interaction_history
            )
            
            # Calculate learning metrics
            growth_rate = self._calculate_knowledge_growth_rate(interaction_history)
            forgetting_rate = self._calculate_forgetting_rate(interaction_history)
            efficiency = self._calculate_learning_efficiency(interaction_history)
            
            # Create updated knowledge state
            knowledge_state = KnowledgeState(
                student_id=student_id,
                concept_probabilities=concept_masteries,
                confidence_intervals=self._calculate_confidence_intervals(concept_masteries),
                knowledge_growth_rate=growth_rate,
                forgetting_rate=forgetting_rate,
                learning_efficiency=efficiency,
                last_updated=datetime.now(),
                interaction_count=len(interaction_history)
            )
            
            # Update FSRS cards based on interaction
            if interaction.correctness is not None:
                await self._update_fsrs_card(student_id, interaction)
            
            # Cache the updated knowledge state
            self._knowledge_state_cache[student_id] = knowledge_state
            
            # Store in database
            await self._store_knowledge_state(knowledge_state)
            
            logger.info(f"Updated knowledge state for student {student_id}")
            return knowledge_state
            
        except Exception as e:
            logger.error(f"Error updating student knowledge: {e}")
            # Return cached or default knowledge state
            return await self._get_knowledge_state(student_id)
    
    async def get_adaptive_recommendations(
        self,
        student_id: str,
        current_topic: Optional[str] = None,
        session_time_budget_minutes: int = 30,
        learning_objectives: List[str] = None
    ) -> AdaptiveRecommendation:
        """Generate personalized learning recommendations."""
        
        try:
            # Get current knowledge state
            knowledge_state = await self._get_knowledge_state(student_id)
            
            # Get FSRS cards for spaced repetition
            fsrs_cards = await self._get_student_fsrs_cards(student_id)
            
            # Detect learning style
            interaction_history = await self._get_interaction_history(student_id)
            learning_style = await self.learning_style_detector.detect_style(
                student_id, interaction_history
            )
            
            # Initialize recommendation
            recommendation = AdaptiveRecommendation(
                student_id=student_id,
                next_difficulty=0.5,
                teaching_strategy="explanation",
                concepts_to_review=[],
                difficulty_adjustments={},
                recommended_sequence=[],
                recommendation_confidence=0.5
            )
            
            # 1. Determine next concept to learn
            next_concept = await self._recommend_next_concept(
                knowledge_state, current_topic, learning_objectives
            )
            
            if next_concept:
                recommendation.next_concept = next_concept
                recommendation.next_difficulty = await self._calibrate_difficulty(
                    student_id, next_concept, knowledge_state
                )
                recommendation.teaching_strategy = await self._select_teaching_strategy(
                    student_id, next_concept, learning_style
                )
            
            # 2. Schedule reviews using FSRS
            review_cards = self.fsrs_scheduler.optimize_study_session(
                fsrs_cards, session_time_budget_minutes // 2  # Half time for reviews
            )
            recommendation.concepts_to_review = [
                (card.concept_name, card.due_date) for card in review_cards
            ]
            
            # 3. Generate learning path
            recommendation.recommended_sequence = await self._generate_learning_path(
                student_id, knowledge_state, target_concepts=5
            )
            
            # 4. Calculate recommendation confidence
            recommendation.recommendation_confidence = self._calculate_recommendation_confidence(
                knowledge_state, len(interaction_history)
            )
            
            # 5. Add reasoning
            recommendation.reasoning = self._generate_recommendation_reasoning(
                knowledge_state, next_concept, len(review_cards)
            )
            
            # 6. Suggest difficulty adjustments
            recommendation.difficulty_adjustments = await self._suggest_difficulty_adjustments(
                student_id, knowledge_state
            )
            
            logger.info(f"Generated recommendations for student {student_id}")
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return AdaptiveRecommendation(
                student_id=student_id,
                teaching_strategy="explanation",
                concepts_to_review=[],
                difficulty_adjustments={},
                recommended_sequence=[],
                reasoning="Error occurred during recommendation generation"
            )
    
    async def _get_interaction_history(
        self, 
        student_id: str, 
        limit: int = 100
    ) -> List[StudentInteraction]:
        """Get student's interaction history from memory."""
        
        try:
            # This would typically query from PostgreSQL
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.error(f"Error getting interaction history: {e}")
            return []
    
    async def _get_knowledge_state(self, student_id: str) -> KnowledgeState:
        """Get current knowledge state, from cache or storage."""
        
        # Check cache first
        if student_id in self._knowledge_state_cache:
            cached_state = self._knowledge_state_cache[student_id]
            cache_age = (datetime.now() - cached_state.last_updated).total_seconds() / 60
            if cache_age < self._cache_ttl_minutes:
                return cached_state
        
        try:
            # Load from database
            stored_state = await self._load_knowledge_state(student_id)
            if stored_state:
                self._knowledge_state_cache[student_id] = stored_state
                return stored_state
        except Exception as e:
            logger.error(f"Error loading knowledge state: {e}")
        
        # Return default knowledge state for new students
        return KnowledgeState(
            student_id=student_id,
            concept_probabilities={},
            confidence_intervals={},
            knowledge_growth_rate=0.5,
            forgetting_rate=0.1,
            learning_efficiency=0.5,
            last_updated=datetime.now(),
            interaction_count=0
        )
    
    async def _get_student_fsrs_cards(self, student_id: str) -> List[FSRSCard]:
        """Get FSRS cards for student."""
        
        # Check cache
        if student_id in self._fsrs_card_cache:
            return self._fsrs_card_cache[student_id]
        
        try:
            # Load from database
            cards = await self._load_fsrs_cards(student_id)
            self._fsrs_card_cache[student_id] = cards
            return cards
        except Exception as e:
            logger.error(f"Error loading FSRS cards: {e}")
            return []
    
    async def _recommend_next_concept(
        self,
        knowledge_state: KnowledgeState,
        current_topic: Optional[str] = None,
        learning_objectives: List[str] = None
    ) -> Optional[str]:
        """Recommend the next concept to learn."""
        
        # Get concepts with low mastery but prerequisites met
        candidate_concepts = []
        
        for concept_name, mastery in knowledge_state.concept_probabilities.items():
            if mastery < 0.7:  # Below mastery threshold
                # Check if prerequisites are met
                concept_id = self._get_concept_id(concept_name)
                if concept_id is not None:
                    prerequisites_met = self._check_prerequisites_met(
                        concept_id, knowledge_state.concept_probabilities
                    )
                    if prerequisites_met:
                        importance = self._get_concept_importance(concept_id)
                        candidate_concepts.append((concept_name, mastery, importance))
        
        if not candidate_concepts:
            # If all concepts are mastered, suggest advanced concepts
            return self._suggest_advanced_concept(current_topic)
        
        # Sort by importance and low mastery
        candidate_concepts.sort(key=lambda x: (-x[2], x[1]))  # High importance, low mastery
        
        # Consider topic context if provided
        if current_topic:
            topic_concepts = [
                concept for concept, mastery, importance in candidate_concepts
                if current_topic.lower() in concept.lower()
            ]
            if topic_concepts:
                return topic_concepts[0]
        
        return candidate_concepts[0][0]
    
    async def _calibrate_difficulty(
        self,
        student_id: str,
        concept_name: str,
        knowledge_state: KnowledgeState
    ) -> float:
        """Calibrate difficulty for a concept."""
        return await self.difficulty_calibrator.calibrate_difficulty(
            concept_name=concept_name,
            student_knowledge_state=knowledge_state,
            student_id=student_id
        )
    
    async def _select_teaching_strategy(
        self,
        student_id: str,
        concept_name: str,
        learning_style: Dict[str, float]
    ) -> str:
        """Select optimal teaching strategy."""
        
        # Strategy selection based on learning style
        visual_pref = learning_style.get("visual", 0.5)
        auditory_pref = learning_style.get("auditory", 0.5)
        kinesthetic_pref = learning_style.get("kinesthetic", 0.5)
        
        # Get concept characteristics
        concept_id = self._get_concept_id(concept_name)
        if concept_id:
            concept = self.knowledge_graph.concepts.get(concept_id)
            if concept and concept.difficulty > 0.7:  # Complex concept
                if visual_pref > 0.6:
                    return "timeline_visualization"
                elif kinesthetic_pref > 0.6:
                    return "interactive_exploration"
                else:
                    return "scaffolded_explanation"
        
        # Default strategies based on learning style
        if visual_pref > max(auditory_pref, kinesthetic_pref):
            return "visual_explanation"
        elif auditory_pref > max(visual_pref, kinesthetic_pref):
            return "socratic_dialogue"
        elif kinesthetic_pref > max(visual_pref, auditory_pref):
            return "interactive_exploration"
        else:
            return "explanation"
    
    async def _generate_learning_path(
        self,
        student_id: str,
        knowledge_state: KnowledgeState,
        target_concepts: int = 5
    ) -> List[str]:
        """Generate optimal learning sequence."""
        
        # Get concepts ready to learn (prerequisites met, not yet mastered)
        ready_concepts = []
        
        for concept_id, concept in self.knowledge_graph.concepts.items():
            mastery = knowledge_state.concept_probabilities.get(concept.concept_name, 0.0)
            
            if mastery < 0.7:  # Not yet mastered
                prerequisites_met = self._check_prerequisites_met(
                    concept_id, knowledge_state.concept_probabilities
                )
                if prerequisites_met:
                    ready_concepts.append((
                        concept.concept_name,
                        concept.importance,
                        mastery,
                        concept.difficulty
                    ))
        
        # Sort by importance, current mastery, and difficulty
        ready_concepts.sort(key=lambda x: (-x[1], x[2], x[3]))  # High importance, low mastery, manageable difficulty
        
        return [concept[0] for concept in ready_concepts[:target_concepts]]
    
    def _calculate_recommendation_confidence(
        self,
        knowledge_state: KnowledgeState,
        interaction_count: int
    ) -> float:
        """Calculate confidence in recommendations."""
        
        base_confidence = 0.5
        
        # More interactions = higher confidence
        interaction_bonus = min(0.3, interaction_count / 50)
        base_confidence += interaction_bonus
        
        # Recent updates = higher confidence
        hours_since_update = (datetime.now() - knowledge_state.last_updated).total_seconds() / 3600
        recency_bonus = max(0.0, 0.2 * (24 - hours_since_update) / 24)
        base_confidence += recency_bonus
        
        return min(1.0, base_confidence)
    
    def _generate_recommendation_reasoning(
        self,
        knowledge_state: KnowledgeState,
        next_concept: Optional[str],
        review_count: int
    ) -> str:
        """Generate human-readable reasoning for recommendations."""
        
        reasoning_parts = []
        
        if next_concept:
            mastery = knowledge_state.concept_probabilities.get(next_concept, 0.0)
            reasoning_parts.append(
                f"Recommended '{next_concept}' as next concept to learn "
                f"(current mastery: {mastery:.1%})"
            )
        
        if review_count > 0:
            reasoning_parts.append(
                f"Scheduled {review_count} concepts for review based on spaced repetition"
            )
        
        if knowledge_state.learning_efficiency > 0.7:
            reasoning_parts.append("Student shows high learning efficiency")
        elif knowledge_state.learning_efficiency < 0.4:
            reasoning_parts.append("Student may benefit from additional support")
        
        return ". ".join(reasoning_parts) + "."
    
    async def _suggest_difficulty_adjustments(
        self,
        student_id: str,
        knowledge_state: KnowledgeState
    ) -> Dict[str, float]:
        """Suggest difficulty adjustments for concepts."""
        
        adjustments = {}
        
        # Check concepts with very low or very high mastery
        for concept_name, mastery in knowledge_state.concept_probabilities.items():
            if mastery < 0.3:  # Struggling concept
                adjustments[concept_name] = -0.1  # Decrease difficulty
            elif mastery > 0.9:  # Mastered concept
                adjustments[concept_name] = 0.1   # Increase difficulty slightly
        
        return adjustments
    
    # Helper methods
    def _get_concept_id(self, concept_name: str) -> Optional[int]:
        """Get concept ID by name."""
        for concept_id, concept in self.knowledge_graph.concepts.items():
            if concept.concept_name == concept_name:
                return concept_id
        return None
    
    def _get_concept_importance(self, concept_id: int) -> float:
        """Get concept importance."""
        concept = self.knowledge_graph.concepts.get(concept_id)
        return concept.importance if concept else 0.5
    
    def _check_prerequisites_met(
        self,
        concept_id: int,
        concept_masteries: Dict[str, float],
        threshold: float = 0.6
    ) -> bool:
        """Check if prerequisites for a concept are met."""
        
        concept = self.knowledge_graph.concepts.get(concept_id)
        if not concept or not concept.prerequisites:
            return True
        
        for prereq_id in concept.prerequisites:
            prereq_concept = self.knowledge_graph.concepts.get(prereq_id)
            if prereq_concept:
                prereq_mastery = concept_masteries.get(prereq_concept.concept_name, 0.0)
                if prereq_mastery < threshold:
                    return False
        
        return True
    
    def _suggest_advanced_concept(self, current_topic: Optional[str] = None) -> Optional[str]:
        """Suggest an advanced concept when all basics are mastered."""
        
        # Find high-difficulty concepts
        advanced_concepts = [
            concept.concept_name for concept in self.knowledge_graph.concepts.values()
            if concept.difficulty > 0.8
        ]
        
        if current_topic and advanced_concepts:
            # Filter by topic relevance
            topic_concepts = [
                concept for concept in advanced_concepts
                if current_topic.lower() in concept.lower()
            ]
            if topic_concepts:
                return topic_concepts[0]
        
        return advanced_concepts[0] if advanced_concepts else None
    
    def _calculate_knowledge_growth_rate(self, interactions: List[StudentInteraction]) -> float:
        """Calculate knowledge growth rate from interactions."""
        if len(interactions) < 5:
            return 0.5
        
        # Calculate performance trend
        recent_performance = [i.correctness for i in interactions[-10:]]
        early_performance = [i.correctness for i in interactions[:10]]
        
        recent_avg = sum(recent_performance) / len(recent_performance)
        early_avg = sum(early_performance) / len(early_performance)
        
        growth_rate = (recent_avg - early_avg) / 2 + 0.5  # Normalize around 0.5
        return max(0.0, min(1.0, growth_rate))
    
    def _calculate_forgetting_rate(self, interactions: List[StudentInteraction]) -> float:
        """Calculate forgetting rate (simplified)."""
        # Placeholder implementation
        return 0.1
    
    def _calculate_learning_efficiency(self, interactions: List[StudentInteraction]) -> float:
        """Calculate learning efficiency from interactions."""
        if not interactions:
            return 0.5
        
        # Simple efficiency: correctness / average_response_time
        total_correctness = sum(i.correctness for i in interactions)
        total_time = sum(i.response_time_seconds for i in interactions)
        
        if total_time == 0:
            return 0.5
        
        efficiency = (total_correctness / len(interactions)) / (total_time / len(interactions) / 30)
        return max(0.0, min(1.0, efficiency))
    
    def _calculate_confidence_intervals(self, masteries: Dict[str, float]) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for mastery predictions."""
        intervals = {}
        for concept, mastery in masteries.items():
            # Simple confidence interval based on uncertainty
            uncertainty = 0.1  # Fixed uncertainty for now
            lower = max(0.0, mastery - uncertainty)
            upper = min(1.0, mastery + uncertainty)
            intervals[concept] = (lower, upper)
        return intervals
    
    # Storage methods (placeholders)
    async def _store_knowledge_state(self, knowledge_state: KnowledgeState):
        """Store knowledge state in database."""
        # Placeholder - would store in PostgreSQL
        pass
    
    async def _load_knowledge_state(self, student_id: str) -> Optional[KnowledgeState]:
        """Load knowledge state from database."""
        # Placeholder - would load from PostgreSQL
        return None
    
    async def _update_fsrs_card(self, student_id: str, interaction: StudentInteraction):
        """Update FSRS card based on interaction."""
        # Convert interaction to rating
        if interaction.correctness >= 0.8:
            rating = 4  # Easy
        elif interaction.correctness >= 0.6:
            rating = 3  # Good
        elif interaction.correctness >= 0.3:
            rating = 2  # Hard
        else:
            rating = 1  # Again
        
        # Find or create card
        card = FSRSCard(
            concept_id=interaction.concept_id,
            concept_name=interaction.concept_name,
            student_id=student_id,
            stability=1.0,
            difficulty=5.0,
            retrievability=1.0,
            due_date=datetime.now()
        )
        
        # Update card
        updated_card = self.fsrs_scheduler.schedule_review(card, rating)
        
        # Store updated card (would store in database)
        await self._store_fsrs_card(updated_card)
    
    async def _load_fsrs_cards(self, student_id: str) -> List[FSRSCard]:
        """Load FSRS cards from database."""
        # Placeholder - would load from PostgreSQL
        return []
    
    async def _store_fsrs_card(self, card: FSRSCard):
        """Store FSRS card in database."""
        # Placeholder - would store in PostgreSQL
        pass