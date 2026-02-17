"""DBQ workflow orchestrator for managing document-based questions."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid

from langchain_core.messages import SystemMessage, HumanMessage

from src.history.schemas import (
    DBQSet, DBQPrompt, DBQDocument, DBQEssay, PrimarySource, 
    HistoricalThinkingSkill, HistoricalPeriod
)
from src.history.sources.analyzer import PrimarySourceAnalyzer
from src.llm.factory import LLMFactory
from src.rag.retriever import KnowledgeRetriever

logger = logging.getLogger(__name__)


class DBQOrchestrator:
    """Orchestrates the complete DBQ workflow from question generation to essay evaluation."""
    
    def __init__(
        self,
        knowledge_retriever: KnowledgeRetriever,
        source_analyzer: PrimarySourceAnalyzer = None
    ):
        self.retriever = knowledge_retriever
        self.source_analyzer = source_analyzer or PrimarySourceAnalyzer(knowledge_retriever)
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # DBQ templates for different historical periods and themes
        self.dbq_templates = self._initialize_dbq_templates()
        
        # Essay evaluation rubrics
        self.evaluation_rubrics = self._initialize_evaluation_rubrics()
        
        # Thinking skills progression
        self.skills_progression = self._initialize_skills_progression()
    
    def _initialize_dbq_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize DBQ templates for different themes and periods."""
        return {
            "causation": {
                "question_stems": [
                    "To what extent did {factor} cause {outcome}?",
                    "Analyze the causes of {event}. Which cause was most significant?",
                    "Evaluate the relative importance of {factor1}, {factor2}, and {factor3} in causing {outcome}."
                ],
                "thinking_skills": [
                    HistoricalThinkingSkill.CAUSATION,
                    HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
                    HistoricalThinkingSkill.SOURCE_ANALYSIS
                ],
                "document_requirements": {
                    "minimum": 4,
                    "types": ["primary", "secondary", "statistical"],
                    "perspectives": "multiple"
                }
            },
            "change_continuity": {
                "question_stems": [
                    "Analyze changes and continuities in {theme} from {period1} to {period2}.",
                    "To what extent did {event} represent a turning point in {theme}?",
                    "Evaluate the statement: '{quote}' in the context of {theme} during {period}."
                ],
                "thinking_skills": [
                    HistoricalThinkingSkill.PATTERNS_OF_CONTINUITY,
                    HistoricalThinkingSkill.CHRONOLOGICAL_REASONING,
                    HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION
                ],
                "document_requirements": {
                    "minimum": 5,
                    "types": ["primary", "visual", "statistical"],
                    "time_span": "extended"
                }
            },
            "comparison": {
                "question_stems": [
                    "Compare and contrast the {theme} in {region1} and {region2} during {period}.",
                    "Analyze similarities and differences in how {group1} and {group2} responded to {challenge}.",
                    "To what extent were the {events} in {region1} and {region2} similar?"
                ],
                "thinking_skills": [
                    HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION,
                    HistoricalThinkingSkill.CRAFTING_ARGUMENTS,
                    HistoricalThinkingSkill.HISTORICAL_INTERPRETATION
                ],
                "document_requirements": {
                    "minimum": 6,
                    "types": ["primary", "secondary"],
                    "perspectives": "balanced"
                }
            }
        }
    
    def _initialize_evaluation_rubrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rubrics for evaluating DBQ essays."""
        return {
            "ap_history": {
                "categories": {
                    "thesis": {
                        "weight": 0.15,
                        "levels": {
                            "sophisticated": {"points": 1, "description": "Clear, historically defensible thesis that addresses all parts of the question"},
                            "acceptable": {"points": 1, "description": "Historically defensible thesis that addresses the question"},
                            "weak": {"points": 0, "description": "No clear thesis or thesis that doesn't address the question"}
                        }
                    },
                    "contextualization": {
                        "weight": 0.15,
                        "levels": {
                            "sophisticated": {"points": 1, "description": "Explains broader historical context relevant to the question"},
                            "acceptable": {"points": 1, "description": "Provides some relevant historical context"},
                            "weak": {"points": 0, "description": "Little or no relevant historical context"}
                        }
                    },
                    "evidence": {
                        "weight": 0.25,
                        "levels": {
                            "sophisticated": {"points": 3, "description": "Uses at least 6 documents effectively to support argument"},
                            "proficient": {"points": 2, "description": "Uses at least 4 documents effectively to support argument"},
                            "developing": {"points": 1, "description": "Uses at least 3 documents to support argument"},
                            "inadequate": {"points": 0, "description": "Uses fewer than 3 documents or uses them ineffectively"}
                        }
                    },
                    "analysis": {
                        "weight": 0.25,
                        "levels": {
                            "sophisticated": {"points": 2, "description": "Explains how documents' purposes, audiences, or perspectives affect their meaning"},
                            "proficient": {"points": 1, "description": "Explains documents' purposes, audiences, or perspectives"},
                            "weak": {"points": 0, "description": "Little or no analysis of documents"}
                        }
                    },
                    "complexity": {
                        "weight": 0.20,
                        "levels": {
                            "sophisticated": {"points": 2, "description": "Demonstrates complex understanding through multiple perspectives, connections, or qualifications"},
                            "acceptable": {"points": 1, "description": "Demonstrates some complex understanding"},
                            "weak": {"points": 0, "description": "Little evidence of complex understanding"}
                        }
                    }
                },
                "total_points": 9
            }
        }
    
    def _initialize_skills_progression(self) -> Dict[str, List[str]]:
        """Initialize progression of historical thinking skills."""
        return {
            "novice": ["chronological_reasoning", "source_analysis"],
            "developing": ["comparison_contextualization", "crafting_arguments"],
            "proficient": ["historical_interpretation", "causation"],
            "advanced": ["patterns_of_continuity", "synthesis"]
        }
    
    async def create_dbq_set(
        self,
        topic: str,
        historical_period: HistoricalPeriod,
        question_type: str = "causation",
        student_level: str = "intermediate",
        custom_requirements: Optional[Dict[str, Any]] = None
    ) -> DBQSet:
        """Create a complete DBQ set with prompt and supporting documents."""
        
        logger.info(f"Creating DBQ set for topic: {topic}")
        
        try:
            # 1. Generate the DBQ prompt
            prompt = await self._generate_dbq_prompt(
                topic, historical_period, question_type, student_level, custom_requirements
            )
            
            # 2. Curate supporting documents
            documents = await self._curate_documents(
                topic, historical_period, prompt, student_level
            )
            
            # 3. Create the complete DBQ set
            dbq_set = DBQSet(
                dbq_id=str(uuid.uuid4()),
                title=f"DBQ: {topic}",
                prompt=prompt,
                documents=documents,
                historical_period=historical_period,
                theme=topic,
                grade_level=self._map_student_level_to_grade(student_level),
                difficulty_level=self._calculate_dbq_difficulty(prompt, documents, student_level),
                estimated_time_minutes=60 + (len(documents) * 5)  # Base time + reading time
            )
            
            logger.info(f"Created DBQ set with {len(documents)} documents")
            return dbq_set
            
        except Exception as e:
            logger.error(f"Error creating DBQ set for {topic}: {e}")
            raise
    
    async def _generate_dbq_prompt(
        self,
        topic: str,
        historical_period: HistoricalPeriod,
        question_type: str,
        student_level: str,
        custom_requirements: Optional[Dict[str, Any]]
    ) -> DBQPrompt:
        """Generate a DBQ prompt for the given topic and parameters."""
        
        template = self.dbq_templates.get(question_type, self.dbq_templates["causation"])
        
        # Get historical context for the topic
        context_prompt = f"""
        Provide historical context for a DBQ about {topic} during the {historical_period.value} period.
        Include:
        1. Key events and developments
        2. Important figures and groups
        3. Broader historical trends
        4. Relevant social, political, and economic factors
        
        Keep to 2-3 paragraphs suitable for {student_level} level students.
        """
        
        context_response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert History teacher creating educational materials."),
            HumanMessage(content=context_prompt)
        ])
        
        historical_context = context_response.content
        
        # Generate the main question
        question_generation_prompt = f"""
        Create a DBQ question about {topic} during the {historical_period.value} period.
        
        Question type: {question_type}
        Student level: {student_level}
        
        Requirements:
        - Question should encourage {question_type} analysis
        - Appropriate for {student_level} level students
        - Should require use of multiple historical documents
        - Should allow for complex argumentation
        
        Template options: {template['question_stems']}
        
        Generate:
        1. Main question (1 sentence)
        2. Task description (2-3 sentences explaining what students should do)
        3. Required historical thinking skills
        """
        
        question_response = await self.llm.ainvoke([
            SystemMessage(content="You are an expert in creating DBQ questions for History education."),
            HumanMessage(content=question_generation_prompt)
        ])
        
        # Parse response (simplified for now)
        main_question = f"Analyze the causes and consequences of {topic} during the {historical_period.value} period. To what extent was {topic} a turning point in this historical era?"
        
        task_description = f"Using the documents and your knowledge of the {historical_period.value} period, develop an argument about {topic}. In your essay, you should analyze the documents for evidence of the causes, effects, and significance of {topic}."
        
        # Create the prompt
        prompt = DBQPrompt(
            prompt_id=str(uuid.uuid4()),
            title=f"DBQ: {topic}",
            historical_question=main_question,
            task_description=task_description,
            historical_context_provided=historical_context,
            time_period=historical_period.value,
            essay_length_words=800 if student_level == "intermediate" else 1000,
            minimum_documents_required=template["document_requirements"]["minimum"],
            outside_evidence_required=True,
            historical_thinking_skills=template["thinking_skills"],
            concepts_assessed=[topic, f"{historical_period.value} period", question_type]
        )
        
        return prompt
    
    async def _curate_documents(
        self,
        topic: str,
        historical_period: HistoricalPeriod,
        prompt: DBQPrompt,
        student_level: str
    ) -> List[DBQDocument]:
        """Curate a set of documents to support the DBQ."""
        
        logger.info(f"Curating documents for DBQ on {topic}")
        
        # Retrieve relevant sources using RAG
        rag_query = f"primary sources documents {topic} {historical_period.value} period historical evidence"
        rag_results = await self.retriever.retrieve(
            query=rag_query,
            subject="history",
            limit=15
        )
        
        # Convert RAG results to PrimarySources
        potential_sources = []
        for i, result in enumerate(rag_results.get("sources", [])):
            source = await self._convert_rag_to_primary_source(result, topic, historical_period, i)
            if source:
                potential_sources.append(source)
        
        # Add some curated sources if not enough found
        if len(potential_sources) < prompt.minimum_documents_required:
            curated_sources = await self._get_curated_sources(topic, historical_period)
            potential_sources.extend(curated_sources)
        
        # Select the best documents for the DBQ
        selected_sources = await self._select_dbq_documents(
            potential_sources,
            prompt,
            student_level
        )
        
        # Create DBQDocument objects
        dbq_documents = []
        for i, source in enumerate(selected_sources):
            dbq_doc = await self._create_dbq_document(source, i + 1, prompt, student_level)
            dbq_documents.append(dbq_doc)
        
        return dbq_documents
    
    async def _convert_rag_to_primary_source(
        self,
        rag_result: Dict[str, Any],
        topic: str,
        period: HistoricalPeriod,
        index: int
    ) -> Optional[PrimarySource]:
        """Convert RAG result to PrimarySource object."""
        
        try:
            metadata = rag_result.get("metadata", {})
            content = rag_result.get("document", "")
            
            source = PrimarySource(
                source_id=f"rag_{index}_{uuid.uuid4().hex[:8]}",
                title=metadata.get("title", f"Document about {topic}"),
                description=content[:200] + "..." if len(content) > 200 else content,
                source_type=self._infer_source_type_from_content(content),
                content=content,
                date_created=metadata.get("date", f"{period.value} period"),
                author=metadata.get("author", "Unknown"),
                historical_period=period,
                complexity_level=0.5,
                related_events=[topic]
            )
            
            return source
            
        except Exception as e:
            logger.warning(f"Failed to convert RAG result to primary source: {e}")
            return None
    
    def _infer_source_type_from_content(self, content: str) -> Any:
        """Infer source type from content."""
        from src.history.schemas import SourceType
        
        content_lower = content.lower()
        
        if any(phrase in content_lower for phrase in ["dear", "sincerely", "yours"]):
            return SourceType.LETTER
        elif any(phrase in content_lower for phrase in ["article", "section", "clause"]):
            return SourceType.TREATY
        elif "speech" in content_lower or "address" in content_lower:
            return SourceType.SPEECH
        elif "diary" in content_lower or "today i" in content_lower:
            return SourceType.DIARY
        else:
            return SourceType.DOCUMENT
    
    async def _get_curated_sources(
        self,
        topic: str,
        period: HistoricalPeriod
    ) -> List[PrimarySource]:
        """Get curated primary sources for common topics."""
        
        # This would typically load from a curated database
        # For now, create sample sources
        curated = []
        
        topic_lower = topic.lower()
        
        if "world war" in topic_lower:
            curated.extend(await self._get_world_war_sources(period))
        elif "civil rights" in topic_lower:
            curated.extend(await self._get_civil_rights_sources(period))
        elif "industrial" in topic_lower:
            curated.extend(await self._get_industrial_sources(period))
        
        return curated
    
    async def _get_world_war_sources(self, period: HistoricalPeriod) -> List[PrimarySource]:
        """Get World War related sources."""
        return [
            PrimarySource(
                source_id="wwi_001",
                title="Telegram from Kaiser Wilhelm II",
                description="Official telegram discussing mobilization plans",
                source_type=SourceType.GOVERNMENT_RECORD,
                content="Official correspondence regarding military preparations...",
                date_created="July 1914",
                author="Kaiser Wilhelm II",
                historical_period=period,
                complexity_level=0.7
            ),
            PrimarySource(
                source_id="wwi_002",
                title="Soldier's Letter Home",
                description="Personal letter from a soldier describing trench conditions",
                source_type=SourceType.LETTER,
                content="My Dear Mother, The conditions here are worse than I imagined...",
                date_created="October 1916",
                author="Private James Thompson",
                historical_period=period,
                complexity_level=0.5
            )
        ]
    
    async def _get_civil_rights_sources(self, period: HistoricalPeriod) -> List[PrimarySource]:
        """Get Civil Rights related sources."""
        return []  # Implement as needed
    
    async def _get_industrial_sources(self, period: HistoricalPeriod) -> List[PrimarySource]:
        """Get Industrial Revolution related sources.""" 
        return []  # Implement as needed
    
    async def _select_dbq_documents(
        self,
        potential_sources: List[PrimarySource],
        prompt: DBQPrompt,
        student_level: str
    ) -> List[PrimarySource]:
        """Select the best documents for the DBQ from potential sources."""
        
        # Score each source for DBQ suitability
        scored_sources = []
        
        for source in potential_sources:
            score = await self._score_source_for_dbq(source, prompt, student_level)
            scored_sources.append((source, score))
        
        # Sort by score and select top documents
        scored_sources.sort(key=lambda x: x[1], reverse=True)
        
        selected = []
        selected_count = prompt.minimum_documents_required
        
        # Ensure diversity in document types and perspectives
        used_types = set()
        used_authors = set()
        
        for source, score in scored_sources:
            if len(selected) >= selected_count:
                break
            
            # Prefer diverse source types and authors
            type_bonus = 0 if source.source_type in used_types else 0.1
            author_bonus = 0 if source.author in used_authors else 0.1
            
            adjusted_score = score + type_bonus + author_bonus
            
            # Check if this source adds value
            if adjusted_score > 0.3:  # Minimum quality threshold
                selected.append(source)
                used_types.add(source.source_type)
                if source.author:
                    used_authors.add(source.author)
        
        # If we still don't have enough, add the highest scoring remaining sources
        while len(selected) < selected_count and len(selected) < len(potential_sources):
            for source, score in scored_sources:
                if source not in selected and len(selected) < selected_count:
                    selected.append(source)
        
        return selected[:selected_count]
    
    async def _score_source_for_dbq(
        self,
        source: PrimarySource,
        prompt: DBQPrompt,
        student_level: str
    ) -> float:
        """Score a source's suitability for the DBQ."""
        
        base_score = 0.5
        
        # Content relevance (check if content relates to the topic)
        if source.content:
            topic_keywords = prompt.concepts_assessed
            content_lower = source.content.lower()
            
            keyword_matches = sum(1 for keyword in topic_keywords if keyword.lower() in content_lower)
            relevance_score = min(keyword_matches / len(topic_keywords), 1.0) * 0.3
            base_score += relevance_score
        
        # Complexity appropriateness for student level
        level_mapping = {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.7}
        target_complexity = level_mapping.get(student_level, 0.5)
        
        complexity_diff = abs(source.complexity_level - target_complexity)
        complexity_score = (1.0 - complexity_diff) * 0.2
        base_score += complexity_score
        
        # Historical period alignment
        if source.historical_period == prompt.historical_context_provided:
            base_score += 0.15
        
        # Source type diversity bonus (handled in selection)
        
        # Content length (prefer substantial but not overwhelming content)
        if source.content:
            content_length = len(source.content)
            if 200 <= content_length <= 1000:  # Ideal length range
                base_score += 0.1
            elif content_length > 1500:  # Too long
                base_score -= 0.1
        
        return min(1.0, base_score)
    
    async def _create_dbq_document(
        self,
        source: PrimarySource,
        document_number: int,
        prompt: DBQPrompt,
        student_level: str
    ) -> DBQDocument:
        """Create a DBQDocument from a PrimarySource."""
        
        # Generate guiding questions for this document
        guiding_questions = await self._generate_document_questions(source, prompt, student_level)
        
        # Identify key points to highlight
        key_points = await self._identify_key_points(source, prompt)
        
        # Create background context if needed
        background_context = await self._generate_background_context(source, student_level)
        
        dbq_document = DBQDocument(
            document_id=f"doc_{document_number}_{source.source_id}",
            document_label=f"Document {chr(64 + document_number)}",  # Document A, B, C, etc.
            source=source,
            guiding_questions=guiding_questions,
            key_points_highlighted=key_points,
            background_context=background_context
        )
        
        return dbq_document
    
    async def _generate_document_questions(
        self,
        source: PrimarySource,
        prompt: DBQPrompt,
        student_level: str
    ) -> List[str]:
        """Generate guiding questions for a specific document."""
        
        questions_prompt = f"""
        Generate 3-4 guiding questions for students analyzing this primary source in a DBQ:

        DBQ Topic: {prompt.concepts_assessed[0] if prompt.concepts_assessed else 'Historical Analysis'}
        Main Question: {prompt.historical_question}
        
        Source: {source.title}
        Type: {source.source_type.value}
        Author: {source.author or 'Unknown'}
        Date: {source.date_created}
        
        Content (first 300 chars): {(source.content or '')[:300]}...

        Create questions that:
        1. Help students understand the document's context and purpose
        2. Guide analysis relevant to the main DBQ question
        3. Are appropriate for {student_level} level students
        4. Encourage critical thinking about the source

        Format as a numbered list.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert History teacher creating DBQ materials."),
                HumanMessage(content=questions_prompt)
            ])
            
            # Parse questions from response
            questions = []
            for line in response.content.split('\n'):
                line = line.strip()
                if line and (line.startswith(tuple('123456789')) or line.startswith('-')):
                    # Remove numbering and clean up
                    question = re.sub(r'^[\d\-\.\)\s]+', '', line).strip()
                    if question and question.endswith('?'):
                        questions.append(question)
            
            return questions[:4]  # Limit to 4 questions
            
        except Exception as e:
            logger.warning(f"Failed to generate document questions: {e}")
            return [
                "What is the main message or argument of this document?",
                "Who was the intended audience and what was the purpose?",
                f"How does this document relate to {prompt.concepts_assessed[0] if prompt.concepts_assessed else 'the topic'}?"
            ]
    
    async def _identify_key_points(self, source: PrimarySource, prompt: DBQPrompt) -> List[str]:
        """Identify key points to highlight in the document."""
        
        if not source.content:
            return []
        
        # Simple keyword-based identification
        key_points = []
        content = source.content
        
        # Look for sentences containing topic keywords
        topic_keywords = [concept.lower() for concept in prompt.concepts_assessed]
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in topic_keywords):
                if len(sentence) > 20 and len(sentence) < 200:  # Reasonable length
                    key_points.append(sentence + '.')
        
        return key_points[:3]  # Limit to 3 key points
    
    async def _generate_background_context(self, source: PrimarySource, student_level: str) -> str:
        """Generate background context for the document if needed."""
        
        if source.complexity_level > 0.7:  # High complexity sources need more context
            context_prompt = f"""
            Provide brief background context (2-3 sentences) for {student_level} students about this historical source:
            
            Title: {source.title}
            Author: {source.author or 'Unknown'}
            Date: {source.date_created}
            Type: {source.source_type.value}
            Period: {source.historical_period.value}
            
            Focus on information that will help students understand the document's significance and context.
            """
            
            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content="You are a History teacher providing student context."),
                    HumanMessage(content=context_prompt)
                ])
                
                return response.content.strip()
                
            except Exception as e:
                logger.warning(f"Failed to generate background context: {e}")
                return f"This {source.source_type.value} was created during the {source.historical_period.value} period."
        
        return ""
    
    def _map_student_level_to_grade(self, student_level: str) -> int:
        """Map student level to grade number."""
        mapping = {
            "beginner": 9,
            "intermediate": 10,
            "advanced": 11,
            "expert": 12
        }
        return mapping.get(student_level, 11)
    
    def _calculate_dbq_difficulty(
        self,
        prompt: DBQPrompt,
        documents: List[DBQDocument],
        student_level: str
    ) -> float:
        """Calculate overall difficulty of the DBQ."""
        
        base_difficulty = 0.5
        
        # Document complexity factor
        if documents:
            avg_complexity = sum(doc.source.complexity_level for doc in documents) / len(documents)
            complexity_factor = avg_complexity * 0.3
            base_difficulty += complexity_factor
        
        # Number of documents factor
        doc_count = len(documents)
        if doc_count > 6:
            base_difficulty += 0.1
        elif doc_count < 4:
            base_difficulty -= 0.1
        
        # Required skills complexity
        advanced_skills = [
            HistoricalThinkingSkill.HISTORICAL_INTERPRETATION,
            HistoricalThinkingSkill.CAUSATION,
            HistoricalThinkingSkill.PATTERNS_OF_CONTINUITY
        ]
        
        if any(skill in prompt.historical_thinking_skills for skill in advanced_skills):
            base_difficulty += 0.15
        
        # Student level adjustment
        level_adjustments = {
            "beginner": -0.2,
            "intermediate": 0.0,
            "advanced": +0.1,
            "expert": +0.2
        }
        
        base_difficulty += level_adjustments.get(student_level, 0.0)
        
        return min(1.0, max(0.1, base_difficulty))
    
    async def evaluate_dbq_essay(
        self,
        essay: DBQEssay,
        dbq_set: DBQSet,
        rubric_type: str = "ap_history"
    ) -> Dict[str, Any]:
        """Evaluate a DBQ essay using the specified rubric."""
        
        logger.info(f"Evaluating DBQ essay: {essay.essay_id}")
        
        try:
            rubric = self.evaluation_rubrics[rubric_type]
            
            evaluation_results = {
                "essay_id": essay.essay_id,
                "total_score": 0,
                "max_score": rubric["total_points"],
                "category_scores": {},
                "detailed_feedback": {},
                "improvement_suggestions": [],
                "strengths": []
            }
            
            # Evaluate each rubric category
            for category, criteria in rubric["categories"].items():
                category_score = await self._evaluate_essay_category(
                    essay, dbq_set, category, criteria
                )
                
                evaluation_results["category_scores"][category] = category_score
                evaluation_results["total_score"] += category_score["points"]
            
            # Generate overall feedback
            evaluation_results["detailed_feedback"] = await self._generate_overall_feedback(
                essay, dbq_set, evaluation_results
            )
            
            # Calculate percentage and grade
            percentage = (evaluation_results["total_score"] / evaluation_results["max_score"]) * 100
            evaluation_results["percentage"] = percentage
            evaluation_results["letter_grade"] = self._calculate_letter_grade(percentage)
            
            logger.info(f"Essay evaluation complete. Score: {evaluation_results['total_score']}/{evaluation_results['max_score']}")
            
            return evaluation_results
            
        except Exception as e:
            logger.error(f"Error evaluating DBQ essay: {e}")
            return {"error": str(e)}
    
    async def _evaluate_essay_category(
        self,
        essay: DBQEssay,
        dbq_set: DBQSet,
        category: str,
        criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a specific category of the essay."""
        
        evaluation_prompt = f"""
        Evaluate this DBQ essay for the "{category}" category:

        DBQ Question: {dbq_set.prompt.historical_question}
        Essay Content: {essay.full_text[:2000]}...

        Rubric Criteria for {category}:
        {criteria}

        Evaluate based on:
        1. How well does the essay meet the criteria for this category?
        2. What level of performance does it demonstrate?
        3. What specific evidence supports this evaluation?

        Provide:
        - Score (based on rubric levels)
        - Justification
        - Specific examples from the essay
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert History teacher evaluating DBQ essays with a detailed rubric."),
                HumanMessage(content=evaluation_prompt)
            ])
            
            # Parse the response (simplified for now)
            # In a real implementation, you would parse the LLM response more carefully
            
            # For now, assign a score based on essay quality indicators
            score = self._quick_category_assessment(essay, category, criteria)
            
            return {
                "points": score,
                "max_points": max(level["points"] for level in criteria["levels"].values()),
                "justification": response.content[:300] + "...",
                "feedback": f"Evaluation for {category} category"
            }
            
        except Exception as e:
            logger.error(f"Error evaluating category {category}: {e}")
            return {"points": 0, "max_points": 1, "justification": "Evaluation error", "feedback": ""}
    
    def _quick_category_assessment(self, essay: DBQEssay, category: str, criteria: Dict[str, Any]) -> int:
        """Quick assessment for category scoring (placeholder for proper LLM evaluation)."""
        
        text = essay.full_text.lower()
        
        if category == "thesis":
            # Check for thesis indicators
            if any(word in text for word in ["argument", "because", "therefore", "however"]):
                return 1
            return 0
        
        elif category == "evidence":
            # Check document usage
            doc_count = essay.documents_used
            if len(doc_count) >= 4:
                return 3
            elif len(doc_count) >= 3:
                return 2
            elif len(doc_count) >= 2:
                return 1
            return 0
        
        elif category == "contextualization":
            # Check for historical context
            context_indicators = ["period", "era", "during", "context", "background"]
            if any(word in text for word in context_indicators):
                return 1
            return 0
        
        elif category == "analysis":
            # Check for document analysis
            analysis_words = ["because", "purpose", "audience", "perspective", "bias"]
            if sum(1 for word in analysis_words if word in text) >= 2:
                return 1
            return 0
        
        else:  # complexity
            # Check for complex understanding
            complex_indicators = ["however", "although", "while", "multiple", "various"]
            if any(word in text for word in complex_indicators):
                return 1
            return 0
    
    async def _generate_overall_feedback(
        self,
        essay: DBQEssay,
        dbq_set: DBQSet,
        evaluation_results: Dict[str, Any]
    ) -> str:
        """Generate overall feedback for the essay."""
        
        feedback_prompt = f"""
        Generate constructive feedback for this DBQ essay:

        DBQ Topic: {dbq_set.theme}
        Question: {dbq_set.prompt.historical_question}
        
        Student's Performance:
        - Total Score: {evaluation_results['total_score']}/{evaluation_results['max_score']}
        - Category Scores: {evaluation_results['category_scores']}
        
        Essay Length: {essay.word_count} words
        Documents Used: {len(essay.documents_used)} out of {len(dbq_set.documents)} available
        
        Provide:
        1. Overall strengths (2-3 points)
        2. Areas for improvement (2-3 points)
        3. Specific suggestions for revision
        4. Encouragement and next steps
        
        Keep feedback constructive and specific.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a supportive History teacher providing constructive feedback on student work."),
                HumanMessage(content=feedback_prompt)
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return "Good effort on your DBQ essay. Continue working on developing your argument and using document evidence effectively."
    
    def _calculate_letter_grade(self, percentage: float) -> str:
        """Calculate letter grade from percentage."""
        
        if percentage >= 90:
            return "A"
        elif percentage >= 80:
            return "B"  
        elif percentage >= 70:
            return "C"
        elif percentage >= 60:
            return "D"
        else:
            return "F"
    
    async def create_practice_dbq_sequence(
        self,
        student_id: str,
        focus_skills: List[HistoricalThinkingSkill],
        difficulty_progression: bool = True
    ) -> List[DBQSet]:
        """Create a sequence of practice DBQs for skill development."""
        
        logger.info(f"Creating practice DBQ sequence for student {student_id}")
        
        dbq_sequence = []
        
        # Define progression topics and difficulty
        practice_topics = [
            {"topic": "World War I Causes", "period": HistoricalPeriod.MODERN_ERA, "type": "causation"},
            {"topic": "Industrial Revolution Impact", "period": HistoricalPeriod.INDUSTRIAL_AGE, "type": "change_continuity"},
            {"topic": "Cold War Tensions", "period": HistoricalPeriod.CONTEMPORARY, "type": "comparison"}
        ]
        
        difficulty_levels = ["intermediate", "intermediate", "advanced"] if difficulty_progression else ["intermediate"] * 3
        
        for i, (topic_info, difficulty) in enumerate(zip(practice_topics, difficulty_levels)):
            try:
                dbq = await self.create_dbq_set(
                    topic=topic_info["topic"],
                    historical_period=topic_info["period"],
                    question_type=topic_info["type"],
                    student_level=difficulty,
                    custom_requirements={
                        "focus_skills": focus_skills,
                        "sequence_position": i + 1,
                        "total_in_sequence": len(practice_topics)
                    }
                )
                
                dbq_sequence.append(dbq)
                
            except Exception as e:
                logger.error(f"Error creating practice DBQ {i+1}: {e}")
                continue
        
        logger.info(f"Created {len(dbq_sequence)} practice DBQs")
        return dbq_sequence