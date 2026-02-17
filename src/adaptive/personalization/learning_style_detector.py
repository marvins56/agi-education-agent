"""Learning style detection based on interaction patterns."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import statistics
import numpy as np

from src.adaptive.schemas import LearningStyleProfile, StudentInteraction

logger = logging.getLogger(__name__)


class LearningStyleDetector:
    """Detect student learning styles from interaction patterns."""
    
    def __init__(self):
        # Minimum interactions needed for reliable detection
        self.min_interactions = 10
        
        # Weight factors for different indicators
        self.weights = {
            "response_time": 0.3,
            "hint_usage": 0.2,
            "question_type_preference": 0.25,
            "session_patterns": 0.15,
            "error_patterns": 0.1
        }
    
    async def detect_style(
        self,
        student_id: str,
        interaction_history: List[StudentInteraction] = None
    ) -> Dict[str, float]:
        """Detect learning style preferences from interaction patterns."""
        
        if not interaction_history or len(interaction_history) < self.min_interactions:
            # Return default neutral preferences
            return {
                "visual": 0.5,
                "auditory": 0.5,
                "kinesthetic": 0.5,
                "reading": 0.5,
                "sequential": 0.5,
                "global": 0.5,
                "active": 0.5,
                "reflective": 0.5,
                "sensing": 0.5,
                "intuitive": 0.5
            }
        
        # Analyze different aspects of learning behavior
        visual_score = await self._analyze_visual_preferences(interaction_history)
        auditory_score = await self._analyze_auditory_preferences(interaction_history)
        kinesthetic_score = await self._analyze_kinesthetic_preferences(interaction_history)
        reading_score = await self._analyze_reading_preferences(interaction_history)
        
        # Processing style analysis
        sequential_score = await self._analyze_sequential_vs_global(interaction_history)
        active_score = await self._analyze_active_vs_reflective(interaction_history)
        sensing_score = await self._analyze_sensing_vs_intuitive(interaction_history)
        
        return {
            "visual": visual_score,
            "auditory": auditory_score,
            "kinesthetic": kinesthetic_score,
            "reading": reading_score,
            "sequential": sequential_score,
            "global": 1.0 - sequential_score,  # Global is opposite of sequential
            "active": active_score,
            "reflective": 1.0 - active_score,  # Reflective is opposite of active
            "sensing": sensing_score,
            "intuitive": 1.0 - sensing_score,  # Intuitive is opposite of sensing
        }
    
    async def _analyze_visual_preferences(self, interactions: List[StudentInteraction]) -> float:
        """Analyze visual learning preferences."""
        
        visual_indicators = []
        
        for interaction in interactions:
            score = 0.5  # Start neutral
            
            # Look for visual-related context features
            context = interaction.context_features
            
            # Visual content types perform better
            if context.get("content_type") == "timeline":
                score += 0.2
            elif context.get("content_type") == "map":
                score += 0.2
            elif context.get("content_type") == "chart":
                score += 0.2
            elif context.get("content_type") == "diagram":
                score += 0.2
            
            # Performance on visual questions
            if interaction.question_type in ["timeline", "map_based", "chart_analysis"]:
                # Higher correctness on visual questions indicates visual preference
                score += (interaction.correctness - 0.5) * 0.3
            
            # Response time patterns for visual content
            if context.get("has_visual_elements", False):
                # Faster response times might indicate comfort with visual content
                if interaction.response_time_seconds < 15:
                    score += 0.1
                elif interaction.response_time_seconds > 45:
                    score -= 0.1
            
            visual_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(visual_indicators) if visual_indicators else 0.5
    
    async def _analyze_auditory_preferences(self, interactions: List[StudentInteraction]) -> float:
        """Analyze auditory learning preferences."""
        
        # Since we don't have audio interaction data yet, we infer from other patterns
        auditory_indicators = []
        
        for interaction in interactions:
            score = 0.5  # Start neutral
            
            # Longer response times might indicate internal verbalization (auditory processing)
            if interaction.response_time_seconds > 30:
                score += 0.1
            
            # Better performance on explanation-heavy content
            if interaction.question_type in ["explanation", "discussion", "debate"]:
                score += (interaction.correctness - 0.5) * 0.2
            
            # Context clues
            context = interaction.context_features
            if context.get("content_type") == "lecture":
                score += 0.1
            elif context.get("content_type") == "discussion":
                score += 0.15
            
            auditory_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(auditory_indicators) if auditory_indicators else 0.5
    
    async def _analyze_kinesthetic_preferences(self, interactions: List[StudentInteraction]) -> float:
        """Analyze kinesthetic learning preferences."""
        
        kinesthetic_indicators = []
        
        for interaction in interactions:
            score = 0.5  # Start neutral
            
            # Better performance on interactive/hands-on content
            if interaction.question_type in ["simulation", "role_play", "case_study"]:
                score += (interaction.correctness - 0.5) * 0.3
            
            # Context clues
            context = interaction.context_features
            if context.get("content_type") == "interactive":
                score += 0.2
            elif context.get("content_type") == "simulation":
                score += 0.25
            
            # Shorter response times on kinesthetic content might indicate comfort
            if context.get("is_interactive", False) and interaction.response_time_seconds < 20:
                score += 0.1
            
            kinesthetic_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(kinesthetic_indicators) if kinesthetic_indicators else 0.5
    
    async def _analyze_reading_preferences(self, interactions: List[StudentInteraction]) -> float:
        """Analyze reading/writing learning preferences."""
        
        reading_indicators = []
        
        for interaction in interactions:
            score = 0.5  # Start neutral
            
            # Better performance on text-heavy content
            if interaction.question_type in ["essay", "reading_comprehension", "analysis"]:
                score += (interaction.correctness - 0.5) * 0.3
            
            # Context clues
            context = interaction.context_features
            if context.get("content_type") == "text":
                score += 0.1
            elif context.get("content_type") == "document":
                score += 0.15
            
            # Longer response times might indicate careful reading
            if interaction.question_type == "reading_comprehension" and interaction.response_time_seconds > 25:
                score += 0.1
            
            reading_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(reading_indicators) if reading_indicators else 0.5
    
    async def _analyze_sequential_vs_global(self, interactions: List[StudentInteraction]) -> float:
        """Analyze sequential vs global processing preference."""
        
        sequential_indicators = []
        
        # Look at learning path patterns
        concept_sequence = [i.concept_name for i in interactions]
        
        # Sequential learners tend to follow logical progressions
        for i, interaction in enumerate(interactions[1:], 1):
            score = 0.5
            
            # Check if concepts build logically on previous ones
            prev_concept = interactions[i-1].concept_name
            curr_concept = interaction.concept_name
            
            # If jumping around topics frequently, more global
            if prev_concept != curr_concept:
                score -= 0.1
            
            # Performance patterns - sequential learners struggle more with advanced concepts
            # if prerequisites aren't mastered
            if interaction.difficulty_level > 0.7 and interaction.correctness < 0.6:
                # Check if student had success with prerequisites
                prereq_performance = self._get_prerequisite_performance(
                    interactions[:i], curr_concept
                )
                if prereq_performance < 0.6:  # Struggled despite weak prerequisites
                    score += 0.2  # More sequential
            
            sequential_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(sequential_indicators) if sequential_indicators else 0.5
    
    async def _analyze_active_vs_reflective(self, interactions: List[StudentInteraction]) -> float:
        """Analyze active vs reflective learning preference."""
        
        active_indicators = []
        
        for interaction in interactions:
            score = 0.5
            
            # Active learners tend to respond more quickly
            if interaction.response_time_seconds < 15:
                score += 0.2
            elif interaction.response_time_seconds > 45:
                score -= 0.2  # More reflective
            
            # Active learners prefer collaborative/interactive content
            if interaction.question_type in ["group_discussion", "debate", "role_play"]:
                score += (interaction.correctness - 0.5) * 0.3
            
            # Reflective learners prefer individual analysis
            elif interaction.question_type in ["analysis", "reflection", "essay"]:
                score -= (interaction.correctness - 0.5) * 0.3  # Good at reflective = less active
            
            # Hint usage patterns
            if interaction.hint_count > 2:
                score -= 0.1  # Reflective learners more likely to use hints
            elif interaction.hint_count == 0:
                score += 0.1  # Active learners jump in without hints
            
            active_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(active_indicators) if active_indicators else 0.5
    
    async def _analyze_sensing_vs_intuitive(self, interactions: List[StudentInteraction]) -> float:
        """Analyze sensing vs intuitive learning preference."""
        
        sensing_indicators = []
        
        for interaction in interactions:
            score = 0.5
            
            # Sensing learners prefer concrete, factual content
            if interaction.question_type in ["factual", "definition", "dates", "names"]:
                score += (interaction.correctness - 0.5) * 0.3
            
            # Intuitive learners prefer abstract, conceptual content
            elif interaction.question_type in ["conceptual", "theoretical", "analysis", "synthesis"]:
                score -= (interaction.correctness - 0.5) * 0.3
            
            # Response time patterns
            if interaction.question_type in ["factual", "definition"] and interaction.response_time_seconds < 10:
                score += 0.1  # Quick on facts = sensing
            elif interaction.question_type in ["analysis", "synthesis"] and interaction.response_time_seconds > 30:
                score -= 0.1  # Takes time for abstract = intuitive
            
            sensing_indicators.append(max(0.0, min(1.0, score)))
        
        return statistics.mean(sensing_indicators) if sensing_indicators else 0.5
    
    def _get_prerequisite_performance(
        self,
        prior_interactions: List[StudentInteraction],
        concept_name: str
    ) -> float:
        """Get average performance on prerequisite concepts."""
        
        # This is a simplified version - would need knowledge graph integration
        # for real prerequisite detection
        
        concept_interactions = [
            i for i in prior_interactions 
            if concept_name.lower() in i.concept_name.lower()
        ]
        
        if not concept_interactions:
            return 0.5  # Neutral if no prior interactions
        
        return statistics.mean(i.correctness for i in concept_interactions)
    
    async def create_learning_style_profile(
        self,
        student_id: str,
        interaction_history: List[StudentInteraction]
    ) -> LearningStyleProfile:
        """Create comprehensive learning style profile."""
        
        style_scores = await self.detect_style(student_id, interaction_history)
        
        # Analyze session patterns for additional insights
        session_insights = await self._analyze_session_patterns(interaction_history)
        
        profile = LearningStyleProfile(
            student_id=student_id,
            visual_preference=style_scores["visual"],
            auditory_preference=style_scores["auditory"],
            kinesthetic_preference=style_scores["kinesthetic"],
            reading_preference=style_scores["reading"],
            sequential_vs_global=style_scores["sequential"],
            active_vs_reflective=style_scores["active"],
            sensing_vs_intuitive=style_scores["sensing"],
            preferred_session_length_minutes=session_insights["preferred_session_length"],
            optimal_difficulty_preference=session_insights["optimal_difficulty"],
            feedback_frequency_preference=session_insights["feedback_frequency"],
            attention_span_indicator=session_insights["attention_span"],
            motivation_level=session_insights["motivation_level"],
            self_regulation_skill=session_insights["self_regulation"]
        )
        
        return profile
    
    async def _analyze_session_patterns(self, interactions: List[StudentInteraction]) -> Dict[str, float]:
        """Analyze session patterns for additional learning insights."""
        
        if not interactions:
            return {
                "preferred_session_length": 30,
                "optimal_difficulty": 0.6,
                "feedback_frequency": 0.8,
                "attention_span": 0.5,
                "motivation_level": 0.7,
                "self_regulation": 0.5
            }
        
        # Group by session (assuming session_id groups interactions)
        sessions = {}
        for interaction in interactions:
            session_id = interaction.session_id
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(interaction)
        
        session_lengths = []
        session_performances = []
        
        for session_interactions in sessions.values():
            if len(session_interactions) < 2:
                continue
                
            # Calculate session length in minutes
            start_time = min(i.timestamp for i in session_interactions)
            end_time = max(i.timestamp for i in session_interactions)
            session_length = (end_time - start_time).total_seconds() / 60
            
            if session_length > 0:
                session_lengths.append(session_length)
                
                # Session performance
                avg_performance = statistics.mean(i.correctness for i in session_interactions)
                session_performances.append(avg_performance)
        
        # Preferred session length (length with best performance)
        if session_lengths and session_performances:
            best_performance_idx = session_performances.index(max(session_performances))
            preferred_length = session_lengths[best_performance_idx]
        else:
            preferred_length = 30
        
        # Optimal difficulty preference
        difficulties = [i.difficulty_level for i in interactions]
        performances = [i.correctness for i in interactions]
        
        # Find difficulty level with best performance
        optimal_difficulty = 0.6  # Default
        if difficulties and performances:
            # Group by difficulty ranges and find optimal
            difficulty_performance = {}
            for diff, perf in zip(difficulties, performances):
                diff_bucket = round(diff * 10) / 10  # Round to 1 decimal
                if diff_bucket not in difficulty_performance:
                    difficulty_performance[diff_bucket] = []
                difficulty_performance[diff_bucket].append(perf)
            
            best_diff = None
            best_avg_perf = 0
            for diff_bucket, perfs in difficulty_performance.items():
                avg_perf = statistics.mean(perfs)
                if avg_perf > best_avg_perf:
                    best_avg_perf = avg_perf
                    best_diff = diff_bucket
            
            if best_diff is not None:
                optimal_difficulty = best_diff
        
        # Other metrics (simplified)
        hint_usage_rate = statistics.mean(i.hint_count for i in interactions)
        avg_response_time = statistics.mean(i.response_time_seconds for i in interactions)
        
        return {
            "preferred_session_length": min(60, max(15, preferred_length)),
            "optimal_difficulty": optimal_difficulty,
            "feedback_frequency": min(1.0, hint_usage_rate / 2),  # More hints = wants more feedback
            "attention_span": max(0.1, min(1.0, 60 / max(30, avg_response_time))),  # Longer times = shorter span
            "motivation_level": statistics.mean(performances) if performances else 0.7,
            "self_regulation": max(0.0, min(1.0, 1.0 - (hint_usage_rate / 3)))  # Less hints = better self-regulation
        }
    
    def recommend_teaching_strategy(self, profile: LearningStyleProfile) -> Dict[str, Any]:
        """Recommend teaching strategies based on learning style profile."""
        
        recommendations = {
            "content_delivery": [],
            "interaction_methods": [],
            "assessment_types": [],
            "session_structure": {}
        }
        
        # Content delivery recommendations
        if profile.visual_preference > 0.6:
            recommendations["content_delivery"].extend([
                "timeline_visualizations",
                "concept_maps", 
                "historical_maps",
                "infographics"
            ])
        
        if profile.auditory_preference > 0.6:
            recommendations["content_delivery"].extend([
                "discussion_based_learning",
                "storytelling_approach",
                "audio_content"
            ])
        
        if profile.kinesthetic_preference > 0.6:
            recommendations["content_delivery"].extend([
                "interactive_simulations",
                "role_playing",
                "hands_on_activities"
            ])
        
        if profile.reading_preference > 0.6:
            recommendations["content_delivery"].extend([
                "primary_source_analysis",
                "text_based_explanations",
                "written_exercises"
            ])
        
        # Interaction method recommendations
        if profile.active_vs_reflective > 0.6:  # More active
            recommendations["interaction_methods"].extend([
                "quick_response_questions",
                "group_discussions",
                "immediate_feedback"
            ])
        else:  # More reflective
            recommendations["interaction_methods"].extend([
                "time_for_consideration",
                "individual_analysis",
                "delayed_feedback"
            ])
        
        # Assessment type recommendations
        if profile.sensing_vs_intuitive > 0.6:  # More sensing
            recommendations["assessment_types"].extend([
                "factual_questions",
                "concrete_examples",
                "step_by_step_problems"
            ])
        else:  # More intuitive
            recommendations["assessment_types"].extend([
                "conceptual_questions",
                "pattern_recognition",
                "abstract_thinking"
            ])
        
        # Session structure
        recommendations["session_structure"] = {
            "preferred_length_minutes": profile.preferred_session_length_minutes,
            "break_frequency": "high" if profile.attention_span_indicator < 0.5 else "normal",
            "difficulty_progression": "gradual" if profile.sequential_vs_global > 0.6 else "varied",
            "feedback_timing": "immediate" if profile.feedback_frequency_preference > 0.7 else "periodic"
        }
        
        return recommendations