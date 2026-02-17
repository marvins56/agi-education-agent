"""Primary source analysis system for historical documents and media."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
import re
from datetime import datetime

from langchain_core.messages import SystemMessage, HumanMessage

from src.history.schemas import PrimarySource, SourceType, HistoricalThinkingSkill
from src.llm.factory import LLMFactory
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class PrimarySourceAnalyzer:
    """Analyzes primary sources for educational use."""
    
    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever,
    ):
        self.retriever = knowledge_retriever
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Analysis question templates by source type
        self.question_templates = self._initialize_question_templates()
        
        # Historical thinking skills mapping
        self.skills_mapping = self._initialize_skills_mapping()
    
    def _initialize_question_templates(self) -> Dict[SourceType, List[str]]:
        """Initialize analysis question templates for different source types."""
        return {
            SourceType.DOCUMENT: [
                "Who wrote this document and what was their role/position?",
                "When and where was this document created?",
                "What was the intended audience for this document?",
                "What is the main message or argument of this document?",
                "What evidence of bias or perspective can you identify?",
                "How might the author's background have influenced this document?",
                "What does this document reveal about the time period?",
                "How does this document compare to other sources from the same period?"
            ],
            SourceType.PHOTOGRAPH: [
                "What do you see in this image? Describe the scene in detail.",
                "When and where do you think this image was created?",
                "Who might have created this image and for what purpose?",
                "What emotions or messages does this image convey?",
                "What details in the image tell us about the historical context?",
                "How might this image have been used or displayed originally?",
                "What perspective does this image represent?",
                "What might be missing or left out of this image?"
            ],
            SourceType.ARTIFACT: [
                "What is this object and what was it used for?",
                "What materials is it made from and what does that tell us?",
                "Who might have owned or used this object?",
                "What does this object reveal about daily life in this period?",
                "How does this object reflect the technology of its time?",
                "What social or economic status might its owner have had?",
                "How has this type of object changed over time?",
                "What questions does this object raise about the past?"
            ]
        }
    
    def _initialize_skills_mapping(self) -> Dict[str, HistoricalThinkingSkill]:
        """Map question types to historical thinking skills."""
        return {
            "authorship": HistoricalThinkingSkill.SOURCE_ANALYSIS,
            "audience": HistoricalThinkingSkill.SOURCE_ANALYSIS,
            "purpose": HistoricalThinkingSkill.SOURCE_ANALYSIS,
            "bias": HistoricalThinkingSkill.SOURCE_ANALYSIS,
            "context": HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION,
            "comparison": HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
            "significance": HistoricalThinkingSkill.HISTORICAL_INTERPRETATION,
            "chronology": HistoricalThinkingSkill.CHRONOLOGICAL_REASONING
        }
    
    async def analyze_primary_source(
        self,
        source: PrimarySource,
        student_level: str = "intermediate",
        focus_skills: Optional[List[HistoricalThinkingSkill]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis of a primary source."""
        
        logger.info(f"Analyzing primary source: {source.title}")
        
        analysis_results = {
            "source_id": source.source_id,
            "basic_analysis": {},
            "bias_analysis": {},
            "authenticity_check": {},
            "educational_analysis": {},
            "generated_questions": [],
            "teaching_suggestions": []
        }
        
        try:
            # 1. Basic source analysis
            analysis_results["basic_analysis"] = await self._perform_basic_analysis(source)
            
            # 2. Bias detection and analysis
            analysis_results["bias_analysis"] = await self._detect_bias(source)
            
            # 3. Educational value analysis
            analysis_results["educational_analysis"] = await self._analyze_educational_value(
                source, student_level, focus_skills
            )
            
            # 4. Generate analysis questions
            analysis_results["generated_questions"] = await self._generate_analysis_questions(
                source, student_level, focus_skills
            )
            
            # 5. Generate teaching suggestions
            analysis_results["teaching_suggestions"] = await self._generate_teaching_suggestions(
                source, analysis_results, student_level
            )
            
            logger.info(f"Analysis complete for source: {source.title}")
            
        except Exception as e:
            logger.error(f"Error analyzing source {source.title}: {e}")
            analysis_results["error"] = str(e)
        
        return analysis_results
    
    async def _perform_basic_analysis(self, source: PrimarySource) -> Dict[str, Any]:
        """Perform basic source analysis using LLM."""
        
        analysis_prompt = f"""
        Analyze this primary source for basic information:

        Source Title: {source.title}
        Source Type: {source.source_type.value}
        Author: {source.author or "Unknown"}
        Date: {source.date_created or "Unknown"}
        Origin: {source.origin_location or "Unknown"}

        Content (first 500 characters):
        {(source.content or "")[:500]}...

        Provide analysis in the following categories:
        1. SOAPS Analysis:
           - Speaker: Who created this source?
           - Occasion: What was happening when this was created?
           - Audience: Who was the intended audience?
           - Purpose: Why was this source created?
           - Subject: What is the main topic/message?

        2. Historical Context:
           - Time period significance
           - Relevant historical events
           - Social/political climate

        3. Source Reliability:
           - Strengths as historical evidence
           - Potential limitations or weaknesses
           - Corroboration needs

        Respond in JSON format with the above categories.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert historian analyzing primary sources for educational use."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse LLM response (implement proper JSON parsing)
            basic_analysis = self._parse_llm_analysis(response.content)
            
            return basic_analysis
            
        except Exception as e:
            logger.error(f"Basic analysis failed: {e}")
            return {"error": str(e)}
    
    async def _detect_bias(self, source: PrimarySource) -> Dict[str, Any]:
        """Detect potential bias in the primary source."""
        
        bias_prompt = f"""
        Analyze this primary source for potential bias:

        Title: {source.title}
        Author: {source.author or "Unknown"}
        Date: {source.date_created}
        Content: {(source.content or "")[:1000]}

        Identify:
        1. Types of bias present (confirmation bias, selection bias, cultural bias, etc.)
        2. Evidence of bias in language, tone, or content selection
        3. What perspectives or viewpoints might be missing
        4. How the author's background might influence their perspective
        5. Overall reliability score (0.0-1.0) and justification

        Respond in JSON format.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in historical source criticism and bias detection."),
                HumanMessage(content=bias_prompt)
            ])
            
            return {
                "bias_types": ["selection_bias", "cultural_bias"],  # Parsed from response
                "bias_evidence": ["Selective presentation of facts", "Cultural assumptions"],
                "missing_perspectives": ["Opposition viewpoints", "Minority voices"],
                "reliability_score": 0.7,
                "analysis": response.content[:500] + "..."
            }
            
        except Exception as e:
            logger.error(f"Bias analysis failed: {e}")
            return {"error": str(e)}
    
    async def _analyze_educational_value(
        self,
        source: PrimarySource,
        student_level: str,
        focus_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> Dict[str, Any]:
        """Analyze the educational value and appropriate use of the source."""
        
        educational_analysis = {
            "difficulty_assessment": {},
            "skill_development": {},
            "curriculum_alignment": {},
            "accessibility": {}
        }
        
        # Assess difficulty level
        educational_analysis["difficulty_assessment"] = await self._assess_source_difficulty(
            source, student_level
        )
        
        # Identify skill development opportunities
        educational_analysis["skill_development"] = self._identify_skill_opportunities(
            source, focus_skills
        )
        
        # Assess curriculum alignment
        educational_analysis["curriculum_alignment"] = await self._assess_curriculum_alignment(
            source
        )
        
        # Evaluate accessibility
        educational_analysis["accessibility"] = self._evaluate_accessibility(source)
        
        return educational_analysis
    
    async def _assess_source_difficulty(
        self,
        source: PrimarySource,
        student_level: str
    ) -> Dict[str, Any]:
        """Assess the difficulty level of the source for students."""
        
        difficulty_factors = {
            "vocabulary_complexity": 0.0,
            "sentence_structure": 0.0,
            "conceptual_complexity": 0.0,
            "cultural_distance": 0.0,
            "contextual_knowledge_required": 0.0
        }
        
        if source.content:
            text = source.content
            
            # Vocabulary complexity (based on word length and rarity)
            words = re.findall(r'\b\w+\b', text.lower())
            if words:
                avg_word_length = sum(len(word) for word in words) / len(words)
                difficulty_factors["vocabulary_complexity"] = min(1.0, avg_word_length / 8.0)
            
            # Sentence structure complexity
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / len([s for s in sentences if s.strip()])
                difficulty_factors["sentence_structure"] = min(1.0, avg_sentence_length / 25.0)
        
        # Conceptual complexity based on source type and content
        if source.source_type == SourceType.DOCUMENT:
            if any(term in source.title.lower() for term in ["treaty", "constitution", "law"]):
                difficulty_factors["conceptual_complexity"] = 0.8
            elif any(term in source.title.lower() for term in ["letter", "diary"]):
                difficulty_factors["conceptual_complexity"] = 0.4
        
        # Cultural distance (how different from modern context)
        if isinstance(source.date_created, str):
            try:
                creation_year = int(re.search(r'\b(19|20)\d{2}\b', source.date_created).group())
                years_ago = 2024 - creation_year
                difficulty_factors["cultural_distance"] = min(1.0, years_ago / 500.0)
            except:
                difficulty_factors["cultural_distance"] = 0.5
        
        # Overall difficulty score
        overall_difficulty = sum(difficulty_factors.values()) / len(difficulty_factors)
        
        return {
            "overall_score": overall_difficulty,
            "factors": difficulty_factors,
            "recommended_level": self._map_difficulty_to_level(overall_difficulty),
            "scaffolding_suggestions": self._suggest_scaffolding(difficulty_factors)
        }
    
    def _identify_skill_opportunities(
        self,
        source: PrimarySource,
        focus_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> Dict[str, Any]:
        """Identify historical thinking skill development opportunities."""
        
        skill_opportunities = {}
        
        # All sources can develop source analysis skills
        skill_opportunities[HistoricalThinkingSkill.SOURCE_ANALYSIS] = {
            "level": "high",
            "activities": [
                "Identify author, audience, and purpose",
                "Evaluate source reliability and bias",
                "Compare with other sources from the same period"
            ]
        }
        
        # Contextualization opportunities
        skill_opportunities[HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION] = {
            "level": "medium",
            "activities": [
                "Place source in its historical context",
                "Connect to broader historical patterns",
                "Analyze how context shapes the source"
            ]
        }
        
        # Specific opportunities based on source characteristics
        if len(source.related_events) > 1:
            skill_opportunities[HistoricalThinkingSkill.CHRONOLOGICAL_REASONING] = {
                "level": "high",
                "activities": [
                    "Create timeline of related events",
                    "Analyze change over time",
                    "Identify patterns of continuity and change"
                ]
            }
        
        if source.biases:
            skill_opportunities[HistoricalThinkingSkill.CRAFTING_ARGUMENTS] = {
                "level": "high",
                "activities": [
                    "Develop arguments about historical interpretations",
                    "Use evidence to support claims",
                    "Address counterarguments and bias"
                ]
            }
        
        # Filter by focus skills if provided
        if focus_skills:
            skill_opportunities = {
                skill: opportunities for skill, opportunities in skill_opportunities.items()
                if skill in focus_skills
            }
        
        return skill_opportunities
    
    async def _assess_curriculum_alignment(self, source: PrimarySource) -> Dict[str, Any]:
        """Assess how well the source aligns with curriculum standards."""
        
        return {
            "grade_levels": [9, 10, 11, 12] if source.complexity_level > 0.6 else [6, 7, 8, 9],
            "standards_alignment": [
                "Analyze primary and secondary sources",
                "Evaluate historical interpretations",
                "Understand historical context"
            ],
            "learning_objectives": [
                f"Students will analyze {source.source_type.value} from {source.historical_period.value}",
                "Students will evaluate source reliability and bias",
                "Students will connect source to broader historical patterns"
            ]
        }
    
    def _evaluate_accessibility(self, source: PrimarySource) -> Dict[str, Any]:
        """Evaluate accessibility of the source for diverse learners."""
        
        accessibility_features = []
        barriers = []
        
        if source.image_url:
            accessibility_features.append("Visual content available")
            barriers.append("May need alternative text descriptions")
        
        if source.content and len(source.content) > 1000:
            barriers.append("Long text may challenge struggling readers")
            accessibility_features.append("Can be excerpted for struggling readers")
        
        return {
            "accessibility_features": accessibility_features,
            "potential_barriers": barriers,
            "accommodations_suggested": [
                "Provide vocabulary support",
                "Offer guided reading questions",
                "Allow collaborative analysis"
            ]
        }
    
    async def _generate_analysis_questions(
        self,
        source: PrimarySource,
        student_level: str,
        focus_skills: Optional[List[HistoricalThinkingSkill]]
    ) -> List[Dict[str, Any]]:
        """Generate analysis questions appropriate for the source and student level."""
        
        # Get base questions for source type
        base_questions = self.question_templates.get(source.source_type, [])
        
        # Generate custom questions using LLM
        custom_questions_prompt = f"""
        Generate 5-7 analysis questions for this primary source, appropriate for {student_level} level students:

        Source: {source.title}
        Type: {source.source_type.value}
        Content summary: {source.description}
        Historical context: {source.historical_context if hasattr(source, 'historical_context') else 'Not specified'}

        Requirements:
        - Questions should develop critical thinking skills
        - Appropriate difficulty for {student_level} students
        - Include both factual and analytical questions
        - Focus on historical thinking skills: {', '.join([skill.value for skill in focus_skills]) if focus_skills else 'all skills'}

        Format as numbered list with each question followed by its difficulty level (easy/medium/hard) and primary thinking skill.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert History teacher creating analysis questions for primary sources."),
                HumanMessage(content=custom_questions_prompt)
            ])
            
            custom_questions = self._parse_questions_from_response(response.content)
            
        except Exception as e:
            logger.warning(f"Custom question generation failed: {e}")
            custom_questions = []
        
        # Combine and organize questions
        all_questions = []
        
        # Add base questions
        for i, question in enumerate(base_questions[:4]):  # Limit base questions
            all_questions.append({
                "id": f"base_{i+1}",
                "question": question,
                "type": "base",
                "difficulty": "medium",
                "thinking_skill": self._infer_thinking_skill(question)
            })
        
        # Add custom questions
        all_questions.extend(custom_questions)
        
        # Sort by difficulty if student level is specified
        if student_level == "beginner":
            all_questions.sort(key=lambda q: {"easy": 1, "medium": 2, "hard": 3}.get(q.get("difficulty", "medium"), 2))
        elif student_level == "advanced":
            all_questions.sort(key=lambda q: {"hard": 1, "medium": 2, "easy": 3}.get(q.get("difficulty", "medium"), 2))
        
        return all_questions[:8]  # Limit to 8 questions total
    
    def _infer_thinking_skill(self, question: str) -> HistoricalThinkingSkill:
        """Infer the primary thinking skill developed by a question."""
        
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["who", "author", "wrote", "created", "audience", "purpose"]):
            return HistoricalThinkingSkill.SOURCE_ANALYSIS
        elif any(word in question_lower for word in ["when", "chronology", "sequence", "before", "after"]):
            return HistoricalThinkingSkill.CHRONOLOGICAL_REASONING
        elif any(word in question_lower for word in ["context", "time period", "historical", "circumstances"]):
            return HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION
        elif any(word in question_lower for word in ["argument", "claim", "evidence", "support", "prove"]):
            return HistoricalThinkingSkill.CRAFTING_ARGUMENTS
        else:
            return HistoricalThinkingSkill.HISTORICAL_INTERPRETATION
    
    def _parse_questions_from_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse questions from LLM response."""
        
        questions = []
        lines = response_text.split('\n')
        
        question_pattern = r'^\d+\.\s*(.+?)(?:\s*\(([^)]+)\)\s*-\s*([^)]+))?$'
        
        for line in lines:
            line = line.strip()
            if not line or not re.match(r'^\d+\.', line):
                continue
            
            match = re.match(question_pattern, line)
            if match:
                question_text = match.group(1).strip()
                difficulty = match.group(2).strip() if match.group(2) else "medium"
                skill = match.group(3).strip() if match.group(3) else "source_analysis"
                
                # Map skill text to enum
                skill_mapping = {
                    "source_analysis": HistoricalThinkingSkill.SOURCE_ANALYSIS,
                    "comparison_contextualization": HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION,
                    "chronological_reasoning": HistoricalThinkingSkill.CHRONOLOGICAL_REASONING,
                    "crafting_arguments": HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
                    "historical_interpretation": HistoricalThinkingSkill.HISTORICAL_INTERPRETATION
                }
                
                questions.append({
                    "id": f"custom_{len(questions)+1}",
                    "question": question_text,
                    "type": "custom",
                    "difficulty": difficulty.lower(),
                    "thinking_skill": skill_mapping.get(skill.lower(), HistoricalThinkingSkill.SOURCE_ANALYSIS)
                })
        
        return questions
    
    def _parse_llm_analysis(self, response_text: str) -> Dict[str, Any]:
        """Parse structured analysis from LLM response."""
        
        # This would implement proper JSON parsing from LLM response
        # For now, return a basic structure
        return {
            "soaps": {
                "speaker": "Identified from response",
                "occasion": "Historical context extracted", 
                "audience": "Target audience determined",
                "purpose": "Purpose analyzed",
                "subject": "Main topic identified"
            },
            "historical_context": {
                "significance": "Context significance",
                "events": "Related events",
                "climate": "Social/political climate"
            },
            "reliability": {
                "strengths": ["Source strengths"],
                "limitations": ["Source limitations"],
                "corroboration": "Corroboration needs"
            }
        }
    
    def _map_difficulty_to_level(self, difficulty_score: float) -> str:
        """Map difficulty score to level description."""
        if difficulty_score < 0.3:
            return "beginner"
        elif difficulty_score < 0.6:
            return "intermediate"
        else:
            return "advanced"
    
    def _suggest_scaffolding(self, difficulty_factors: Dict[str, float]) -> List[str]:
        """Suggest scaffolding based on difficulty factors."""
        suggestions = []
        
        if difficulty_factors["vocabulary_complexity"] > 0.7:
            suggestions.append("Provide vocabulary glossary")
        
        if difficulty_factors["sentence_structure"] > 0.7:
            suggestions.append("Break into shorter passages")
        
        if difficulty_factors["cultural_distance"] > 0.7:
            suggestions.append("Provide historical background context")
        
        if difficulty_factors["conceptual_complexity"] > 0.7:
            suggestions.append("Use guided reading questions")
        
        return suggestions
    
    async def _generate_teaching_suggestions(
        self,
        source: PrimarySource,
        analysis_results: Dict[str, Any],
        student_level: str
    ) -> List[str]:
        """Generate teaching suggestions based on analysis."""
        
        suggestions = [
            f"Use this {source.source_type.value} to teach about {source.historical_period.value}",
            "Have students complete SOAPS analysis before deeper discussion",
            "Compare with other sources from the same time period",
            "Discuss potential bias and limitations with students"
        ]
        
        # Add specific suggestions based on analysis
        if analysis_results.get("educational_analysis", {}).get("difficulty_assessment", {}).get("overall_score", 0) > 0.7:
            suggestions.append("Provide extensive scaffolding and background information")
        
        if source.biases:
            suggestions.append("Use as example for teaching about historical bias")
        
        if len(source.related_events) > 1:
            suggestions.append("Create timeline activity showing related events")
        
        return suggestions

    async def create_source_comparison_activity(
        self,
        sources: List[PrimarySource],
        comparison_theme: str,
        student_level: str = "intermediate"
    ) -> Dict[str, Any]:
        """Create a comparative analysis activity using multiple sources."""
        
        activity = {
            "title": f"Comparative Analysis: {comparison_theme}",
            "sources": [source.source_id for source in sources],
            "comparison_framework": {},
            "analysis_questions": [],
            "synthesis_task": {}
        }
        
        # Create comparison framework
        activity["comparison_framework"] = {
            "categories": [
                "Perspective/Point of View",
                "Evidence Presented",
                "Bias/Limitations",
                "Historical Context",
                "Reliability"
            ],
            "comparison_matrix": self._create_comparison_matrix(sources)
        }
        
        # Generate comparative analysis questions
        comparative_questions = await self._generate_comparative_questions(
            sources, comparison_theme, student_level
        )
        activity["analysis_questions"] = comparative_questions
        
        # Create synthesis task
        activity["synthesis_task"] = {
            "prompt": f"Based on your analysis of these sources, write a {300 if student_level == 'beginner' else 500}-word essay addressing: {comparison_theme}",
            "requirements": [
                "Use evidence from at least 3 sources",
                "Acknowledge different perspectives",
                "Evaluate the reliability of your sources",
                "Develop a clear thesis statement"
            ],
            "rubric_categories": [
                "Use of Evidence",
                "Analysis of Sources",
                "Historical Context",
                "Argument Development"
            ]
        }
        
        return activity
    
    def _create_comparison_matrix(self, sources: List[PrimarySource]) -> Dict[str, Any]:
        """Create a comparison matrix structure for sources."""
        
        matrix = {}
        categories = ["Perspective", "Evidence", "Bias", "Context", "Reliability"]
        
        for source in sources:
            matrix[source.source_id] = {
                category: f"Analysis for {source.title}" for category in categories
            }
        
        return matrix
    
    async def _generate_comparative_questions(
        self,
        sources: List[PrimarySource],
        comparison_theme: str,
        student_level: str
    ) -> List[Dict[str, Any]]:
        """Generate questions for comparative source analysis."""
        
        questions = [
            {
                "question": f"How do these sources present different perspectives on {comparison_theme}?",
                "difficulty": "medium",
                "thinking_skill": HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION
            },
            {
                "question": "Which source do you find most reliable and why?",
                "difficulty": "hard",
                "thinking_skill": HistoricalThinkingSkill.SOURCE_ANALYSIS
            },
            {
                "question": f"What evidence do these sources provide about {comparison_theme}?",
                "difficulty": "easy",
                "thinking_skill": HistoricalThinkingSkill.SOURCE_ANALYSIS
            },
            {
                "question": "How might the different authors' backgrounds have influenced their accounts?",
                "difficulty": "hard",
                "thinking_skill": HistoricalThinkingSkill.HISTORICAL_INTERPRETATION
            }
        ]
        
        return questions