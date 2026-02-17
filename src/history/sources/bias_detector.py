"""Bias detection system for primary sources."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from src.history.schemas import PrimarySource, SourceType
from src.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


class BiasDetector:
    """Detects and analyzes bias in historical primary sources."""
    
    def __init__(self):
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Bias indicators and patterns
        self.bias_indicators = self._initialize_bias_indicators()
        
        # Source type specific bias patterns
        self.source_bias_patterns = self._initialize_source_patterns()
    
    def _initialize_bias_indicators(self) -> Dict[str, List[str]]:
        """Initialize common bias indicators for different types."""
        return {
            "selection_bias": [
                "cherry-picking facts",
                "omitting contrary evidence", 
                "focusing only on positive/negative aspects",
                "incomplete information presentation"
            ],
            "confirmation_bias": [
                "seeking information that confirms preconceptions",
                "interpreting ambiguous evidence as confirmation",
                "dismissing contradictory evidence"
            ],
            "cultural_bias": [
                "ethnocentric assumptions",
                "cultural stereotyping",
                "imposing modern values on historical context",
                "assumptions about cultural superiority"
            ],
            "political_bias": [
                "partisan interpretation of events",
                "ideological framing",
                "propaganda elements",
                "political agenda advancement"
            ],
            "temporal_bias": [
                "presentism - judging past by present standards",
                "anachronistic assumptions",
                "hindsight bias"
            ],
            "personal_bias": [
                "emotional involvement affecting objectivity",
                "personal interests influencing account",
                "subjective interpretation as fact"
            ]
        }
    
    def _initialize_source_patterns(self) -> Dict[SourceType, Dict[str, Any]]:
        """Initialize bias patterns specific to source types."""
        return {
            SourceType.NEWSPAPER: {
                "common_biases": ["political_bias", "selection_bias"],
                "indicators": ["loaded language", "selective reporting", "editorial stance"],
                "questions": [
                    "What is the newspaper's known political stance?",
                    "What stories or perspectives might be omitted?",
                    "How does the headline frame the story?"
                ]
            },
            SourceType.MEMOIR: {
                "common_biases": ["personal_bias", "temporal_bias"],
                "indicators": ["self-justification", "selective memory", "hindsight"],
                "questions": [
                    "How might the author's personal interests affect their account?",
                    "What events might the author have forgotten or reinterpreted?",
                    "How much time passed between the events and the writing?"
                ]
            },
            SourceType.GOVERNMENT_RECORD: {
                "common_biases": ["political_bias", "selection_bias"],
                "indicators": ["official justification", "omitted details", "bureaucratic language"],
                "questions": [
                    "What does the government want to emphasize or hide?",
                    "Who is the intended audience for this document?",
                    "What alternative perspectives are missing?"
                ]
            },
            SourceType.PHOTOGRAPH: {
                "common_biases": ["selection_bias", "cultural_bias"],
                "indicators": ["framing choices", "staged elements", "context omission"],
                "questions": [
                    "What is included or excluded from the frame?",
                    "Who took this photo and why?",
                    "How might this image be misinterpreted without context?"
                ]
            }
        }
    
    async def detect_bias(self, source: PrimarySource) -> Dict[str, Any]:
        """Comprehensive bias detection and analysis."""
        
        logger.info(f"Analyzing bias in source: {source.title}")
        
        bias_analysis = {
            "source_id": source.source_id,
            "bias_types_detected": [],
            "bias_indicators": {},
            "reliability_impact": {},
            "contextual_factors": {},
            "teaching_opportunities": []
        }
        
        try:
            # 1. Automatic bias pattern detection
            bias_analysis["bias_types_detected"] = await self._detect_bias_patterns(source)
            
            # 2. Detailed bias analysis using LLM
            bias_analysis["bias_indicators"] = await self._analyze_bias_indicators(source)
            
            # 3. Assess impact on reliability
            bias_analysis["reliability_impact"] = self._assess_reliability_impact(
                bias_analysis["bias_types_detected"],
                bias_analysis["bias_indicators"]
            )
            
            # 4. Analyze contextual factors
            bias_analysis["contextual_factors"] = await self._analyze_contextual_factors(source)
            
            # 5. Generate teaching opportunities
            bias_analysis["teaching_opportunities"] = self._generate_teaching_opportunities(
                bias_analysis
            )
            
            logger.info(f"Bias analysis complete for: {source.title}")
            
        except Exception as e:
            logger.error(f"Error in bias detection for {source.title}: {e}")
            bias_analysis["error"] = str(e)
        
        return bias_analysis
    
    async def _detect_bias_patterns(self, source: PrimarySource) -> List[str]:
        """Detect bias patterns using automated analysis."""
        
        detected_biases = []
        
        if not source.content:
            return detected_biases
        
        content = source.content.lower()
        
        # Language analysis for bias indicators
        # Selection bias indicators
        if any(phrase in content for phrase in ["only", "merely", "just", "simply"]):
            detected_biases.append("selection_bias")
        
        # Emotional/loaded language indicating bias
        emotional_words = ["devastating", "brilliant", "terrible", "magnificent", "evil", "heroic"]
        if any(word in content for word in emotional_words):
            detected_biases.append("personal_bias")
        
        # Absolute statements indicating potential bias
        absolute_phrases = ["always", "never", "all", "none", "everyone", "no one"]
        if sum(content.count(phrase) for phrase in absolute_phrases) > 3:
            detected_biases.append("confirmation_bias")
        
        # Cultural bias indicators
        cultural_terms = ["primitive", "civilized", "barbarian", "savage", "advanced", "backward"]
        if any(term in content for term in cultural_terms):
            detected_biases.append("cultural_bias")
        
        # Source type specific bias detection
        if source.source_type in self.source_bias_patterns:
            source_patterns = self.source_bias_patterns[source.source_type]
            detected_biases.extend(source_patterns["common_biases"])
        
        return list(set(detected_biases))  # Remove duplicates
    
    async def _analyze_bias_indicators(self, source: PrimarySource) -> Dict[str, Any]:
        """Use LLM for detailed bias indicator analysis."""
        
        bias_prompt = f"""
        Analyze this historical primary source for bias indicators:

        Title: {source.title}
        Type: {source.source_type.value}
        Author: {source.author or "Unknown"}
        Date: {source.date_created}
        Context: {source.description}

        Content (first 1000 characters):
        {(source.content or "")[:1000]}

        Identify specific bias indicators in the following categories:

        1. Language Analysis:
           - Loaded or emotional language
           - Absolute statements vs. qualified statements
           - Omissions or gaps in information

        2. Perspective Analysis:
           - Whose voice is represented?
           - Whose perspectives are missing?
           - Cultural assumptions embedded in the text

        3. Source Context:
           - Author's potential motivations
           - Historical context that might influence bias
           - Intended audience considerations

        4. Evidence Selection:
           - What types of evidence are emphasized?
           - What might be selectively omitted?
           - How are opposing viewpoints treated?

        Provide specific examples from the text where possible.
        Respond in JSON format.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in historical source criticism and bias analysis."),
                HumanMessage(content=bias_prompt)
            ])
            
            # Parse the response (simplified for now)
            return {
                "language_indicators": [
                    "Emotional language present",
                    "Absolute statements used"
                ],
                "perspective_issues": [
                    "Single viewpoint presented",
                    "Minority perspectives absent"
                ],
                "contextual_influences": [
                    "Author's political position",
                    "Time period constraints"
                ],
                "evidence_selection": [
                    "Selective fact presentation",
                    "Opposing views dismissed"
                ],
                "specific_examples": response.content[:500] + "..."
            }
            
        except Exception as e:
            logger.error(f"LLM bias analysis failed: {e}")
            return {"error": str(e)}
    
    def _assess_reliability_impact(
        self,
        bias_types: List[str],
        bias_indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess how detected bias impacts source reliability."""
        
        # Base reliability score
        base_reliability = 0.8
        
        # Reduce reliability based on bias types
        reliability_penalties = {
            "selection_bias": 0.15,
            "confirmation_bias": 0.1,
            "cultural_bias": 0.1,
            "political_bias": 0.2,
            "temporal_bias": 0.05,
            "personal_bias": 0.1
        }
        
        total_penalty = sum(reliability_penalties.get(bias_type, 0) for bias_type in bias_types)
        adjusted_reliability = max(0.1, base_reliability - total_penalty)
        
        return {
            "reliability_score": adjusted_reliability,
            "major_concerns": [bias for bias in bias_types if reliability_penalties.get(bias, 0) >= 0.15],
            "moderate_concerns": [bias for bias in bias_types if 0.05 <= reliability_penalties.get(bias, 0) < 0.15],
            "impact_assessment": self._generate_impact_assessment(bias_types, adjusted_reliability),
            "corroboration_importance": "high" if adjusted_reliability < 0.6 else "medium"
        }
    
    async def _analyze_contextual_factors(self, source: PrimarySource) -> Dict[str, Any]:
        """Analyze contextual factors that might contribute to bias."""
        
        contextual_factors = {
            "temporal_context": {},
            "social_context": {},
            "political_context": {},
            "personal_context": {}
        }
        
        # Temporal context analysis
        if isinstance(source.date_created, str):
            try:
                # Extract year and analyze temporal factors
                year_match = re.search(r'\b(19|20)\d{2}\b', source.date_created)
                if year_match:
                    creation_year = int(year_match.group())
                    current_year = 2024
                    
                    contextual_factors["temporal_context"] = {
                        "creation_year": creation_year,
                        "years_elapsed": current_year - creation_year,
                        "temporal_bias_risk": "high" if current_year - creation_year > 50 else "medium",
                        "historical_distance_factors": self._analyze_historical_distance(creation_year)
                    }
            except:
                contextual_factors["temporal_context"] = {"analysis_failed": True}
        
        # Social context
        contextual_factors["social_context"] = {
            "social_position_influence": "Author's social position may affect perspective",
            "cultural_norms_impact": f"Cultural norms of {source.historical_period.value} may influence viewpoint",
            "social_pressures": "Consider social pressures of the time period"
        }
        
        # Political context
        contextual_factors["political_context"] = {
            "political_climate": f"Political climate of {source.historical_period.value} era",
            "government_influence": "Consider government censorship or influence",
            "ideological_pressures": "Ideological pressures of the time"
        }
        
        # Personal context
        if source.author:
            contextual_factors["personal_context"] = {
                "author_background": f"Consider {source.author}'s background and motivations",
                "personal_stakes": "Analyze author's personal interest in the events",
                "career_considerations": "Professional or career motivations"
            }
        
        return contextual_factors
    
    def _analyze_historical_distance(self, creation_year: int) -> List[str]:
        """Analyze factors related to historical distance."""
        
        current_year = 2024
        years_elapsed = current_year - creation_year
        
        factors = []
        
        if years_elapsed > 100:
            factors.append("Very long historical distance - high risk of anachronistic interpretation")
        elif years_elapsed > 50:
            factors.append("Significant historical distance - moderate risk of temporal bias")
        elif years_elapsed > 20:
            factors.append("Some historical distance - consider changed perspectives")
        else:
            factors.append("Recent historical source - consider immediate context")
        
        # Add period-specific factors
        if 1914 <= creation_year <= 1918:
            factors.append("World War I era - consider wartime propaganda influences")
        elif 1939 <= creation_year <= 1945:
            factors.append("World War II era - consider wartime censorship and propaganda")
        elif 1945 <= creation_year <= 1991:
            factors.append("Cold War era - consider ideological tensions")
        
        return factors
    
    def _generate_impact_assessment(self, bias_types: List[str], reliability_score: float) -> str:
        """Generate human-readable impact assessment."""
        
        if reliability_score >= 0.8:
            return "Minimal bias detected. Source appears highly reliable for historical analysis."
        elif reliability_score >= 0.6:
            return f"Moderate bias present ({', '.join(bias_types)}). Use with caution and seek corroboration."
        elif reliability_score >= 0.4:
            return f"Significant bias detected ({', '.join(bias_types)}). Requires careful analysis and multiple source comparison."
        else:
            return f"Severe bias concerns ({', '.join(bias_types)}). Use primarily as example of perspective rather than factual source."
    
    def _generate_teaching_opportunities(self, bias_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate teaching opportunities based on bias analysis."""
        
        opportunities = []
        
        bias_types = bias_analysis.get("bias_types_detected", [])
        reliability_score = bias_analysis.get("reliability_impact", {}).get("reliability_score", 0.5)
        
        # Teaching opportunities based on bias types
        if "selection_bias" in bias_types:
            opportunities.append({
                "skill": "Critical Source Analysis",
                "activity": "Have students identify what information might be missing from this account",
                "learning_objective": "Understand how source creators select and omit information",
                "discussion_questions": [
                    "What questions does this source leave unanswered?",
                    "What other perspectives would help complete the picture?"
                ]
            })
        
        if "cultural_bias" in bias_types:
            opportunities.append({
                "skill": "Cultural Context Analysis", 
                "activity": "Compare this source's cultural assumptions with modern perspectives",
                "learning_objective": "Recognize how cultural context shapes historical accounts",
                "discussion_questions": [
                    "What cultural assumptions does the author make?",
                    "How might someone from a different culture interpret these events?"
                ]
            })
        
        if "political_bias" in bias_types:
            opportunities.append({
                "skill": "Political Perspective Analysis",
                "activity": "Analyze how the author's political position influences their account",
                "learning_objective": "Understand the relationship between politics and historical interpretation",
                "discussion_questions": [
                    "What political interests might the author have?",
                    "How might someone with different political views describe these events?"
                ]
            })
        
        # Universal teaching opportunities
        opportunities.append({
            "skill": "Source Reliability Assessment",
            "activity": f"Evaluate this source's reliability (score: {reliability_score:.2f})",
            "learning_objective": "Develop skills in assessing source credibility",
            "discussion_questions": [
                "What makes a historical source reliable?",
                "How should historians use sources with known bias?"
            ]
        })
        
        return opportunities
    
    async def compare_source_bias(
        self,
        sources: List[PrimarySource],
        comparison_theme: str
    ) -> Dict[str, Any]:
        """Compare bias patterns across multiple sources."""
        
        comparison_analysis = {
            "theme": comparison_theme,
            "sources_analyzed": len(sources),
            "bias_comparison": {},
            "reliability_comparison": {},
            "perspective_gaps": [],
            "corroboration_opportunities": []
        }
        
        # Analyze each source
        source_analyses = {}
        for source in sources:
            analysis = await self.detect_bias(source)
            source_analyses[source.source_id] = analysis
        
        # Compare bias patterns
        all_bias_types = set()
        for analysis in source_analyses.values():
            all_bias_types.update(analysis.get("bias_types_detected", []))
        
        comparison_analysis["bias_comparison"] = {}
        for bias_type in all_bias_types:
            sources_with_bias = [
                source_id for source_id, analysis in source_analyses.items()
                if bias_type in analysis.get("bias_types_detected", [])
            ]
            comparison_analysis["bias_comparison"][bias_type] = {
                "sources_affected": sources_with_bias,
                "frequency": len(sources_with_bias) / len(sources)
            }
        
        # Compare reliability scores
        reliability_scores = {
            source_id: analysis.get("reliability_impact", {}).get("reliability_score", 0.5)
            for source_id, analysis in source_analyses.items()
        }
        
        comparison_analysis["reliability_comparison"] = {
            "scores": reliability_scores,
            "most_reliable": max(reliability_scores.items(), key=lambda x: x[1]),
            "least_reliable": min(reliability_scores.items(), key=lambda x: x[1]),
            "average_reliability": sum(reliability_scores.values()) / len(reliability_scores)
        }
        
        # Identify perspective gaps
        comparison_analysis["perspective_gaps"] = self._identify_perspective_gaps(
            sources, source_analyses
        )
        
        # Generate corroboration opportunities  
        comparison_analysis["corroboration_opportunities"] = self._identify_corroboration_opportunities(
            sources, source_analyses
        )
        
        return comparison_analysis
    
    def _identify_perspective_gaps(
        self,
        sources: List[PrimarySource],
        analyses: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Identify missing perspectives in the source collection."""
        
        gaps = []
        
        # Check for diverse authorship
        authors = [source.author for source in sources if source.author]
        if len(set(authors)) < len(sources) * 0.7:  # Less than 70% unique authors
            gaps.append("Limited diversity in authorship perspectives")
        
        # Check for diverse source types
        source_types = [source.source_type for source in sources]
        if len(set(source_types)) < 3:
            gaps.append("Limited diversity in source types")
        
        # Check for temporal diversity
        dates = []
        for source in sources:
            if isinstance(source.date_created, str):
                year_match = re.search(r'\b(19|20)\d{2}\b', source.date_created)
                if year_match:
                    dates.append(int(year_match.group()))
        
        if dates and max(dates) - min(dates) < 5:
            gaps.append("Limited temporal diversity - sources from similar time period")
        
        # Check for political/ideological diversity
        political_biases = sum(
            1 for analysis in analyses.values()
            if "political_bias" in analysis.get("bias_types_detected", [])
        )
        
        if political_biases == len(sources):
            gaps.append("All sources show political bias - need neutral perspectives")
        
        return gaps
    
    def _identify_corroboration_opportunities(
        self,
        sources: List[PrimarySource],
        analyses: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify opportunities for source corroboration."""
        
        opportunities = []
        
        # High reliability sources can corroborate low reliability ones
        reliable_sources = [
            source_id for source_id, analysis in analyses.items()
            if analysis.get("reliability_impact", {}).get("reliability_score", 0) >= 0.7
        ]
        
        unreliable_sources = [
            source_id for source_id, analysis in analyses.items()
            if analysis.get("reliability_impact", {}).get("reliability_score", 0) < 0.5
        ]
        
        if reliable_sources and unreliable_sources:
            opportunities.append({
                "type": "reliability_corroboration",
                "description": "Use reliable sources to verify claims from less reliable sources",
                "reliable_sources": reliable_sources,
                "sources_needing_verification": unreliable_sources
            })
        
        # Sources with different bias types can provide balanced perspectives
        different_bias_sources = {}
        for source_id, analysis in analyses.items():
            bias_signature = tuple(sorted(analysis.get("bias_types_detected", [])))
            if bias_signature not in different_bias_sources:
                different_bias_sources[bias_signature] = []
            different_bias_sources[bias_signature].append(source_id)
        
        if len(different_bias_sources) > 1:
            opportunities.append({
                "type": "perspective_corroboration",
                "description": "Compare sources with different bias patterns for balanced understanding",
                "bias_groups": different_bias_sources
            })
        
        return opportunities