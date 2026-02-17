"""Causal chain analysis for historical events and processes."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, date
import uuid
from collections import defaultdict, deque

from langchain_core.messages import SystemMessage, HumanMessage

from src.history.schemas import (
    HistoricalEvent, CausalRelationship, HistoricalArgument,
    HistoricalThinkingSkill, EventType
)
from src.llm.factory import LLMFactory
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class CausalChainAnalyzer:
    """Analyzes cause-and-effect relationships in historical events."""
    
    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever
    ):
        self.retriever = knowledge_retriever
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Causal relationship types and their properties
        self.causation_types = self._initialize_causation_types()
        
        # Pattern recognition for different types of causation
        self.causal_patterns = self._initialize_causal_patterns()
        
        # Historical periods and their causal characteristics
        self.period_characteristics = self._initialize_period_characteristics()
    
    def _initialize_causation_types(self) -> Dict[str, Dict[str, Any]]:
        """Initialize different types of causal relationships."""
        return {
            "immediate": {
                "description": "Direct, short-term cause with clear connection",
                "time_span": "days to months",
                "certainty": "high",
                "examples": ["assassination triggers war declaration", "economic crash causes bank runs"]
            },
            "underlying": {
                "description": "Deep structural causes that create conditions for events",
                "time_span": "years to decades",
                "certainty": "medium-high",
                "examples": ["nationalism creates tensions", "economic inequality breeds revolution"]
            },
            "contributing": {
                "description": "Factors that increase likelihood but don't guarantee outcome",
                "time_span": "variable",
                "certainty": "medium",
                "examples": ["alliance system escalates conflict", "technological advances enable expansion"]
            },
            "necessary": {
                "description": "Conditions required for event but not sufficient alone",
                "time_span": "variable",
                "certainty": "high",
                "examples": ["industrial capacity required for modern war", "literacy needed for mass democracy"]
            },
            "sufficient": {
                "description": "Conditions that alone could cause the outcome",
                "time_span": "variable",
                "certainty": "high",
                "examples": ["nuclear attack forces surrender", "plague decimates population"]
            },
            "catalyst": {
                "description": "Triggers that unleash pre-existing tensions",
                "time_span": "immediate",
                "certainty": "medium-high",
                "examples": ["incident sparks riot", "rumor precipitates panic"]
            }
        }
    
    def _initialize_causal_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that indicate different types of causation."""
        return {
            "immediate_indicators": [
                "immediately after", "directly caused", "triggered by", "resulted from",
                "sparked", "prompted", "led directly to", "precipitated"
            ],
            "underlying_indicators": [
                "rooted in", "stemmed from", "underlying cause", "fundamental reason",
                "deep-seated", "long-term factor", "structural cause", "created conditions"
            ],
            "contributing_indicators": [
                "contributed to", "played a role", "factor in", "helped cause",
                "influenced", "increased likelihood", "made possible"
            ],
            "necessary_indicators": [
                "required for", "prerequisite", "necessary condition", "could not have happened without",
                "depended on", "needed", "essential for"
            ],
            "sufficient_indicators": [
                "sufficient to cause", "alone caused", "enough to trigger", "single cause",
                "by itself led to", "sufficient condition"
            ],
            "catalyst_indicators": [
                "spark that lit", "final straw", "tipping point", "breaking point",
                "catalyst for", "trigger event", "precipitated crisis"
            ]
        }
    
    def _initialize_period_characteristics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize characteristics of different historical periods affecting causation."""
        return {
            "medieval": {
                "dominant_factors": ["religious authority", "feudal relationships", "agricultural cycles"],
                "communication_speed": "slow",
                "typical_causes": ["dynastic disputes", "religious conflicts", "harvest failures"],
                "causal_complexity": "low-medium"
            },
            "early_modern": {
                "dominant_factors": ["state building", "religious reformation", "global trade"],
                "communication_speed": "slow-medium",
                "typical_causes": ["religious wars", "colonial expansion", "dynastic politics"],
                "causal_complexity": "medium"
            },
            "industrial_age": {
                "dominant_factors": ["industrialization", "nationalism", "class conflict"],
                "communication_speed": "medium",
                "typical_causes": ["economic changes", "social upheaval", "technological disruption"],
                "causal_complexity": "medium-high"
            },
            "modern_era": {
                "dominant_factors": ["total war", "ideological conflict", "global economics"],
                "communication_speed": "fast",
                "typical_causes": ["ideological tensions", "economic crises", "geopolitical rivalry"],
                "causal_complexity": "high"
            },
            "contemporary": {
                "dominant_factors": ["globalization", "technology", "environmental issues"],
                "communication_speed": "instant",
                "typical_causes": ["technological disruption", "global interconnection", "environmental change"],
                "causal_complexity": "very high"
            }
        }
    
    async def analyze_causal_chain(
        self,
        target_event: HistoricalEvent,
        context_events: List[HistoricalEvent],
        depth_limit: int = 3,
        time_window_years: int = 50
    ) -> Dict[str, Any]:
        """Analyze the causal chain leading to a target event."""
        
        logger.info(f"Analyzing causal chain for event: {target_event.title}")
        
        analysis_results = {
            "target_event": target_event.event_id,
            "causal_relationships": [],
            "causal_chain_summary": {},
            "alternative_explanations": [],
            "historical_debate": {},
            "complexity_assessment": {}
        }
        
        try:
            # 1. Identify potential causal relationships
            potential_causes = await self._identify_potential_causes(
                target_event, context_events, time_window_years
            )
            
            # 2. Analyze each potential causal relationship
            for potential_cause in potential_causes:
                relationship = await self._analyze_causal_relationship(
                    potential_cause, target_event
                )
                if relationship:
                    analysis_results["causal_relationships"].append(relationship)
            
            # 3. Build causal chain structure
            analysis_results["causal_chain_summary"] = await self._build_causal_chain_summary(
                target_event, analysis_results["causal_relationships"], depth_limit
            )
            
            # 4. Identify alternative explanations
            analysis_results["alternative_explanations"] = await self._identify_alternative_explanations(
                target_event, analysis_results["causal_relationships"]
            )
            
            # 5. Analyze historical debate
            analysis_results["historical_debate"] = await self._analyze_historical_debate(
                target_event, analysis_results["causal_relationships"]
            )
            
            # 6. Assess causal complexity
            analysis_results["complexity_assessment"] = self._assess_causal_complexity(
                target_event, analysis_results["causal_relationships"]
            )
            
            logger.info(f"Causal analysis complete for {target_event.title}")
            
        except Exception as e:
            logger.error(f"Error in causal chain analysis: {e}")
            analysis_results["error"] = str(e)
        
        return analysis_results
    
    async def _identify_potential_causes(
        self,
        target_event: HistoricalEvent,
        context_events: List[HistoricalEvent],
        time_window_years: int
    ) -> List[HistoricalEvent]:
        """Identify events that could potentially be causes of the target event."""
        
        potential_causes = []
        
        target_date = self._parse_event_date(target_event.date_start)
        if not target_date:
            return context_events  # If no date, consider all events
        
        # Filter events that occurred before the target event within time window
        for event in context_events:
            event_date = self._parse_event_date(event.date_start)
            if not event_date:
                continue
            
            # Check if event occurred before target event
            if event_date < target_date:
                # Check if within time window
                years_difference = target_date.year - event_date.year
                if years_difference <= time_window_years:
                    potential_causes.append(event)
            
            # Also consider events explicitly listed as causes
            if event.event_id in target_event.causes:
                potential_causes.append(event)
        
        # Sort by proximity to target event
        potential_causes.sort(
            key=lambda e: abs((target_date - self._parse_event_date(e.date_start)).days) 
            if self._parse_event_date(e.date_start) else float('inf')
        )
        
        return potential_causes
    
    def _parse_event_date(self, date_input) -> Optional[date]:
        """Parse various date formats into a date object."""
        
        if isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, str):
            # Try to extract year from string
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', date_input)
            if year_match:
                year = int(year_match.group())
                return date(year, 1, 1)  # Default to January 1st
        
        return None
    
    async def _analyze_causal_relationship(
        self,
        cause_event: HistoricalEvent,
        effect_event: HistoricalEvent
    ) -> Optional[Dict[str, Any]]:
        """Analyze the causal relationship between two events."""
        
        analysis_prompt = f"""
        Analyze the potential causal relationship between these two historical events:

        CAUSE EVENT:
        Title: {cause_event.title}
        Date: {cause_event.date_start}
        Description: {cause_event.description}
        Type: {cause_event.event_type.value}

        EFFECT EVENT:
        Title: {effect_event.title}  
        Date: {effect_event.date_start}
        Description: {effect_event.description}
        Type: {effect_event.event_type.value}

        Analyze:
        1. Is there a causal relationship? (Yes/No)
        2. If yes, what type of causation is it?
           - immediate (direct, short-term cause)
           - underlying (structural, long-term cause)
           - contributing (factor that increased likelihood)
           - necessary (required condition)
           - sufficient (alone could cause outcome)
           - catalyst (trigger for pre-existing conditions)

        3. How strong is the causal connection? (1-10 scale)
        4. What is the mechanism of causation? (How did the cause lead to the effect?)
        5. What evidence supports this causal relationship?
        6. Are there alternative explanations?
        7. Do historians generally agree on this causation?

        Respond in JSON format.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert historian analyzing causal relationships between historical events."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse LLM response (simplified for now)
            relationship_data = self._parse_causal_analysis_response(response.content)
            
            # Only return if there's a confirmed causal relationship
            if relationship_data.get("has_causal_relationship", False):
                relationship = {
                    "cause_event_id": cause_event.event_id,
                    "effect_event_id": effect_event.event_id,
                    "causation_type": relationship_data.get("causation_type", "contributing"),
                    "strength": relationship_data.get("strength", 5),
                    "mechanism": relationship_data.get("mechanism", "Causal mechanism not specified"),
                    "evidence": relationship_data.get("evidence", []),
                    "alternatives": relationship_data.get("alternatives", []),
                    "historian_agreement": relationship_data.get("historian_agreement", "mixed"),
                    "confidence": relationship_data.get("confidence", 0.5)
                }
                
                return relationship
            
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing causal relationship: {e}")
            return None
    
    def _parse_causal_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for causal analysis (simplified implementation)."""
        
        # This would implement proper JSON parsing in a real system
        # For now, return a basic structure
        
        response_lower = response_text.lower()
        
        # Detect if causal relationship exists
        has_relationship = any(phrase in response_lower for phrase in [
            "yes", "causal relationship exists", "causes", "leads to", "results in"
        ])
        
        # Detect causation type
        causation_type = "contributing"  # default
        for c_type, indicators in self.causal_patterns.items():
            if any(indicator.lower() in response_lower for indicator in indicators):
                causation_type = c_type.replace("_indicators", "")
                break
        
        # Estimate strength (simplified)
        strength = 5
        if any(word in response_lower for word in ["strong", "direct", "clear"]):
            strength = 8
        elif any(word in response_lower for word in ["weak", "indirect", "minimal"]):
            strength = 3
        
        return {
            "has_causal_relationship": has_relationship,
            "causation_type": causation_type,
            "strength": strength,
            "mechanism": "Analysis of causal mechanism",
            "evidence": ["Historical evidence supporting causation"],
            "alternatives": ["Alternative explanations considered"],
            "historian_agreement": "generally accepted",
            "confidence": 0.7
        }
    
    async def _build_causal_chain_summary(
        self,
        target_event: HistoricalEvent,
        causal_relationships: List[Dict[str, Any]],
        depth_limit: int
    ) -> Dict[str, Any]:
        """Build a summary of the causal chain structure."""
        
        # Build directed graph of causal relationships
        graph = defaultdict(list)
        all_events = {target_event.event_id}
        
        for relationship in causal_relationships:
            cause_id = relationship["cause_event_id"]
            effect_id = relationship["effect_event_id"]
            
            graph[cause_id].append({
                "effect": effect_id,
                "type": relationship["causation_type"],
                "strength": relationship["strength"]
            })
            
            all_events.add(cause_id)
            all_events.add(effect_id)
        
        # Identify levels in the causal chain
        chain_levels = self._identify_causal_levels(graph, target_event.event_id, depth_limit)
        
        # Categorize causes by type
        cause_categories = defaultdict(list)
        for relationship in causal_relationships:
            if relationship["effect_event_id"] == target_event.event_id:
                cause_categories[relationship["causation_type"]].append({
                    "cause_id": relationship["cause_event_id"],
                    "strength": relationship["strength"],
                    "mechanism": relationship["mechanism"]
                })
        
        summary = {
            "total_causal_relationships": len(causal_relationships),
            "chain_depth": len(chain_levels),
            "chain_levels": chain_levels,
            "direct_causes": len([r for r in causal_relationships if r["effect_event_id"] == target_event.event_id]),
            "cause_categories": dict(cause_categories),
            "strongest_causes": self._identify_strongest_causes(causal_relationships, target_event.event_id),
            "causal_network_density": len(causal_relationships) / max(len(all_events), 1)
        }
        
        return summary
    
    def _identify_causal_levels(
        self,
        graph: Dict[str, List[Dict[str, Any]]],
        target_event_id: str,
        depth_limit: int
    ) -> Dict[int, List[str]]:
        """Identify levels in the causal chain using breadth-first search."""
        
        levels = defaultdict(list)
        visited = set()
        queue = deque([(target_event_id, 0)])
        
        # Work backwards from target event
        reverse_graph = defaultdict(list)
        for cause_id, effects in graph.items():
            for effect_info in effects:
                reverse_graph[effect_info["effect"]].append(cause_id)
        
        while queue and len(levels) <= depth_limit:
            event_id, level = queue.popleft()
            
            if event_id in visited:
                continue
            
            visited.add(event_id)
            levels[level].append(event_id)
            
            # Add causes at the next level
            for cause_id in reverse_graph.get(event_id, []):
                if cause_id not in visited:
                    queue.append((cause_id, level + 1))
        
        return dict(levels)
    
    def _identify_strongest_causes(
        self,
        causal_relationships: List[Dict[str, Any]],
        target_event_id: str
    ) -> List[Dict[str, Any]]:
        """Identify the strongest direct causes of the target event."""
        
        direct_causes = [
            r for r in causal_relationships 
            if r["effect_event_id"] == target_event_id
        ]
        
        # Sort by strength and return top 3
        direct_causes.sort(key=lambda x: x["strength"], reverse=True)
        
        strongest = []
        for cause in direct_causes[:3]:
            strongest.append({
                "cause_id": cause["cause_event_id"],
                "type": cause["causation_type"],
                "strength": cause["strength"],
                "mechanism": cause["mechanism"]
            })
        
        return strongest
    
    async def _identify_alternative_explanations(
        self,
        target_event: HistoricalEvent,
        causal_relationships: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify alternative explanations for the target event."""
        
        alternative_prompt = f"""
        Given this historical event and its identified causes, what are alternative explanations historians have proposed?

        EVENT: {target_event.title}
        DATE: {target_event.date_start}
        DESCRIPTION: {target_event.description}

        IDENTIFIED CAUSES:
        {chr(10).join([f"- {r['causation_type']}: {r['mechanism']}" for r in causal_relationships[:5]])}

        Provide 2-3 alternative historical interpretations or explanations that:
        1. Emphasize different factors
        2. Come from different historiographical schools
        3. Challenge the mainstream interpretation

        For each alternative, explain:
        - The alternative explanation
        - What evidence supports it
        - Which historians or schools of thought propose it
        - How it differs from the standard interpretation
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a historian familiar with different historiographical interpretations and debates."),
                HumanMessage(content=alternative_prompt)
            ])
            
            # Parse alternatives from response
            alternatives = self._parse_alternative_explanations(response.content)
            
            return alternatives
            
        except Exception as e:
            logger.error(f"Error identifying alternative explanations: {e}")
            return []
    
    def _parse_alternative_explanations(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse alternative explanations from LLM response."""
        
        # Simplified parsing - in reality would be more sophisticated
        alternatives = []
        
        # Split by numbered items or bullet points
        sections = response_text.split('\n\n')
        
        for i, section in enumerate(sections[:3]):  # Limit to 3 alternatives
            if section.strip():
                alternatives.append({
                    "id": f"alt_{i+1}",
                    "explanation": section.strip()[:200] + "...",
                    "evidence": ["Historical evidence supporting this view"],
                    "proponents": ["Historical scholars"],
                    "key_differences": ["How this differs from standard interpretation"]
                })
        
        return alternatives
    
    async def _analyze_historical_debate(
        self,
        target_event: HistoricalEvent,
        causal_relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the historical debate around the causation of this event."""
        
        debate_prompt = f"""
        Analyze the historical debate about the causes of this event:

        EVENT: {target_event.title} ({target_event.date_start})
        
        PROPOSED CAUSES:
        {chr(10).join([f"- {r['causation_type']}: {r['mechanism']}" for r in causal_relationships[:5]])}

        Analyze:
        1. What aspects of causation do historians debate most?
        2. Which causes have strong consensus vs. which are disputed?
        3. How has historical interpretation changed over time?
        4. What new evidence has influenced the debate?
        5. Are there unresolved questions about causation?

        Provide a structured analysis of the historiographical debate.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in historiography and historical debates."),
                HumanMessage(content=debate_prompt)
            ])
            
            debate_analysis = {
                "main_points_of_debate": ["Primary areas of historical disagreement"],
                "consensus_areas": ["Aspects historians generally agree on"],
                "disputed_areas": ["Aspects still under debate"],
                "evolution_of_interpretation": "How understanding has changed over time",
                "key_evidence": ["Important evidence that has shaped the debate"],
                "unresolved_questions": ["Questions that remain open"],
                "contemporary_relevance": "Why this debate matters today"
            }
            
            return debate_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing historical debate: {e}")
            return {"error": str(e)}
    
    def _assess_causal_complexity(
        self,
        target_event: HistoricalEvent,
        causal_relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess the complexity of the causal network."""
        
        # Count different types of causes
        causation_types = defaultdict(int)
        for relationship in causal_relationships:
            causation_types[relationship["causation_type"]] += 1
        
        # Calculate complexity metrics
        total_causes = len(causal_relationships)
        unique_types = len(causation_types)
        
        # Complexity score based on various factors
        complexity_score = 0.0
        
        # Number of causes
        complexity_score += min(total_causes / 5, 1.0) * 0.3
        
        # Diversity of causation types
        complexity_score += min(unique_types / 6, 1.0) * 0.3
        
        # Presence of underlying/structural causes increases complexity
        if "underlying" in causation_types:
            complexity_score += 0.2
        
        # Multiple necessary conditions increase complexity
        if causation_types.get("necessary", 0) > 1:
            complexity_score += 0.1
        
        # Time span of causation
        if self._has_long_term_causation(causal_relationships):
            complexity_score += 0.1
        
        complexity_score = min(1.0, complexity_score)
        
        # Determine complexity level
        if complexity_score < 0.3:
            complexity_level = "Simple"
        elif complexity_score < 0.6:
            complexity_level = "Moderate"
        elif complexity_score < 0.8:
            complexity_level = "Complex"
        else:
            complexity_level = "Highly Complex"
        
        return {
            "complexity_score": complexity_score,
            "complexity_level": complexity_level,
            "total_causes": total_causes,
            "causation_type_distribution": dict(causation_types),
            "dominant_causation_types": [
                c_type for c_type, count in causation_types.items() 
                if count == max(causation_types.values())
            ],
            "complexity_factors": self._identify_complexity_factors(causal_relationships),
            "teaching_implications": self._get_teaching_implications(complexity_score, target_event)
        }
    
    def _has_long_term_causation(self, causal_relationships: List[Dict[str, Any]]) -> bool:
        """Check if the causation involves long-term processes."""
        
        long_term_types = ["underlying", "structural", "necessary"]
        return any(
            relationship["causation_type"] in long_term_types 
            for relationship in causal_relationships
        )
    
    def _identify_complexity_factors(self, causal_relationships: List[Dict[str, Any]]) -> List[str]:
        """Identify factors that contribute to causal complexity."""
        
        factors = []
        
        causation_types = [r["causation_type"] for r in causal_relationships]
        
        if len(set(causation_types)) > 3:
            factors.append("Multiple types of causation present")
        
        if "underlying" in causation_types and "immediate" in causation_types:
            factors.append("Both long-term and short-term causes involved")
        
        if causation_types.count("contributing") > 2:
            factors.append("Multiple contributing factors interact")
        
        if any(r["strength"] < 5 for r in causal_relationships):
            factors.append("Some causal relationships are uncertain or disputed")
        
        if len(causal_relationships) > 6:
            factors.append("Large number of causal factors")
        
        return factors
    
    def _get_teaching_implications(self, complexity_score: float, event: HistoricalEvent) -> Dict[str, Any]:
        """Get teaching implications based on causal complexity."""
        
        implications = {
            "student_level": "intermediate",
            "recommended_approach": "guided analysis",
            "key_learning_objectives": [],
            "potential_difficulties": [],
            "scaffolding_suggestions": []
        }
        
        if complexity_score < 0.3:  # Simple causation
            implications.update({
                "student_level": "beginner",
                "recommended_approach": "direct instruction",
                "key_learning_objectives": [
                    "Identify main cause of " + event.title,
                    "Understand basic cause-effect relationships"
                ],
                "potential_difficulties": ["Understanding chronology"],
                "scaffolding_suggestions": ["Use timeline to show sequence"]
            })
        
        elif complexity_score < 0.6:  # Moderate complexity
            implications.update({
                "student_level": "intermediate",
                "recommended_approach": "guided analysis",
                "key_learning_objectives": [
                    "Analyze multiple causes of " + event.title,
                    "Compare importance of different causes",
                    "Understand cause-effect relationships"
                ],
                "potential_difficulties": ["Weighing relative importance of causes"],
                "scaffolding_suggestions": [
                    "Provide cause categorization framework",
                    "Use graphic organizers for multiple causes"
                ]
            })
        
        else:  # Complex causation
            implications.update({
                "student_level": "advanced",
                "recommended_approach": "inquiry-based learning",
                "key_learning_objectives": [
                    "Analyze complex causation in " + event.title,
                    "Evaluate different historical interpretations",
                    "Understand historiographical debate",
                    "Synthesize multiple perspectives"
                ],
                "potential_difficulties": [
                    "Managing multiple variables",
                    "Understanding interaction effects",
                    "Dealing with uncertainty and debate"
                ],
                "scaffolding_suggestions": [
                    "Break down into sub-questions",
                    "Provide explicit instruction on historical thinking skills",
                    "Use collaborative analysis activities",
                    "Introduce primary source evidence gradually"
                ]
            })
        
        return implications
    
    async def create_causal_argument_template(
        self,
        target_event: HistoricalEvent,
        causal_analysis: Dict[str, Any],
        argument_type: str = "multi_causal"
    ) -> HistoricalArgument:
        """Create a template for constructing arguments about causation."""
        
        strongest_causes = causal_analysis.get("causal_chain_summary", {}).get("strongest_causes", [])
        
        # Build argument structure
        if argument_type == "single_cause":
            # Focus on the strongest cause
            main_cause = strongest_causes[0] if strongest_causes else None
            claim = f"The primary cause of {target_event.title} was {main_cause['mechanism'] if main_cause else 'unknown factor'}."
            
        elif argument_type == "multi_causal":
            # Address multiple causes
            claim = f"{target_event.title} resulted from the interaction of multiple factors including {', '.join([c['mechanism'] for c in strongest_causes[:3]])}."
            
        else:  # comparative
            # Compare different causes
            claim = f"While multiple factors contributed to {target_event.title}, {strongest_causes[0]['mechanism'] if strongest_causes else 'the primary factor'} was most significant."
        
        # Generate evidence points
        evidence_points = []
        for cause in strongest_causes[:3]:
            evidence_points.append(f"Evidence for {cause['type']} causation: {cause['mechanism']}")
        
        # Generate reasoning
        reasoning = f"These causes interact to create the conditions that led to {target_event.title}. The {strongest_causes[0]['type'] if strongest_causes else 'primary'} factor was particularly important because it {strongest_causes[0]['mechanism'] if strongest_causes else 'created necessary conditions'}."
        
        argument = HistoricalArgument(
            argument_id=str(uuid.uuid4()),
            claim=claim,
            evidence=evidence_points,
            reasoning=reasoning,
            historical_context=f"During the {target_event.period.value} period, {target_event.description[:100]}...",
            counterarguments=causal_analysis.get("alternative_explanations", [])[:2],
            evidence_quality=0.7,  # Based on analysis quality
            reasoning_quality=0.7,
            historical_accuracy=0.8
        )
        
        return argument
    
    async def generate_causal_analysis_questions(
        self,
        target_event: HistoricalEvent,
        causal_analysis: Dict[str, Any],
        student_level: str = "intermediate"
    ) -> List[Dict[str, Any]]:
        """Generate questions for students to analyze causation."""
        
        complexity_score = causal_analysis.get("complexity_assessment", {}).get("complexity_score", 0.5)
        strongest_causes = causal_analysis.get("causal_chain_summary", {}).get("strongest_causes", [])
        
        questions = []
        
        # Basic causation questions
        questions.append({
            "question": f"What were the main causes of {target_event.title}?",
            "type": "identification",
            "difficulty": "easy",
            "thinking_skill": HistoricalThinkingSkill.CAUSATION,
            "expected_answer_points": [cause["mechanism"] for cause in strongest_causes[:3]]
        })
        
        # Categorization questions
        if complexity_score > 0.3:
            questions.append({
                "question": f"Categorize the causes of {target_event.title} as immediate, underlying, or contributing factors.",
                "type": "categorization",
                "difficulty": "medium",
                "thinking_skill": HistoricalThinkingSkill.CAUSATION,
                "categories": ["immediate", "underlying", "contributing"]
            })
        
        # Evaluation questions
        if complexity_score > 0.5:
            questions.append({
                "question": f"Which cause was most important in bringing about {target_event.title}? Justify your answer.",
                "type": "evaluation",
                "difficulty": "hard",
                "thinking_skill": HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
                "requires_justification": True
            })
        
        # Alternative explanations
        if causal_analysis.get("alternative_explanations"):
            questions.append({
                "question": f"Some historians argue that {target_event.title} was primarily caused by [alternative explanation]. How would you respond to this argument?",
                "type": "argumentation", 
                "difficulty": "hard",
                "thinking_skill": HistoricalThinkingSkill.HISTORICAL_INTERPRETATION,
                "requires_evidence": True
            })
        
        # Counterfactual questions (for advanced students)
        if student_level == "advanced" and complexity_score > 0.6:
            questions.append({
                "question": f"How might history have been different if [key cause] had not occurred? Would {target_event.title} still have happened?",
                "type": "counterfactual",
                "difficulty": "very_hard",
                "thinking_skill": HistoricalThinkingSkill.HISTORICAL_INTERPRETATION,
                "requires_speculation": True,
                "scaffolding_needed": True
            })
        
        return questions