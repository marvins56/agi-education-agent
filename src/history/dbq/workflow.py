"""DBQ (Document-Based Question) essay workflow manager."""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import re

from src.history.schemas import (
    DBQSet, DBQDocument, DBQPrompt, DBQEssay, PrimarySource,
    HistoricalPeriod, HistoricalThinkingSkill, SourceType
)
from src.history.sources.analyzer import PrimarySourceAnalyzer

logger = logging.getLogger(__name__)


class DBQWorkflowManager:
    """Manage the complete DBQ essay workflow."""
    
    def __init__(self):
        self.source_analyzer = PrimarySourceAnalyzer()
        
        # DBQ templates and prompts
        self.dbq_templates = self._load_dbq_templates()
        
        # Rubric scoring weights
        self.rubric_weights = {
            "thesis": 0.20,          # Clear, defensible thesis
            "document_usage": 0.25,   # Uses documents effectively
            "outside_evidence": 0.15, # Incorporates outside evidence
            "historical_reasoning": 0.25, # Demonstrates historical reasoning
            "writing_quality": 0.15   # Clear writing and organization
        }
    
    def _load_dbq_templates(self) -> Dict[str, DBQSet]:
        """Load pre-built DBQ sets for common topics."""
        
        templates = {}
        
        # World War I Causes DBQ
        wwi_causes_dbq = self._create_wwi_causes_dbq()
        templates["wwi_causes"] = wwi_causes_dbq
        
        # Cold War Origins DBQ
        cold_war_dbq = self._create_cold_war_origins_dbq()
        templates["cold_war_origins"] = cold_war_dbq
        
        return templates
    
    def _create_wwi_causes_dbq(self) -> DBQSet:
        """Create World War I causes DBQ."""
        
        # Create prompt
        prompt = DBQPrompt(
            prompt_id="wwi_causes_prompt",
            title="Causes of World War I",
            historical_question="What were the primary causes of World War I?",
            task_description="""
            Analyze the primary and secondary causes that led to the outbreak of World War I in 1914.
            In your essay, be sure to:
            • Develop a clear thesis that addresses the prompt
            • Use at least 4 of the provided documents to support your argument
            • Incorporate outside historical evidence beyond the documents
            • Demonstrate historical reasoning skills such as comparison, contextualization, or causation
            """,
            historical_context_provided="""
            By 1914, Europe was divided into two major alliance systems. The Triple Alliance consisted of 
            Germany, Austria-Hungary, and Italy, while the Triple Entente included France, Russia, and Britain. 
            Tensions had been building due to imperial competition, nationalism, militarism, and the complex web 
            of alliances. The assassination of Archduke Franz Ferdinand of Austria-Hungary on June 28, 1914, 
            in Sarajevo provided the spark that ignited the powder keg of Europe.
            """,
            time_period="1870-1914",
            essay_length_words=1000,
            minimum_documents_required=4,
            outside_evidence_required=True,
            historical_thinking_skills=[
                HistoricalThinkingSkill.CAUSATION,
                HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION,
                HistoricalThinkingSkill.CRAFTING_ARGUMENTS
            ]
        )
        
        # Create documents
        documents = [
            DBQDocument(
                document_id="wwi_doc_a",
                document_label="Document A",
                source=PrimarySource(
                    source_id="alliance_treaty_1879",
                    title="Dual Alliance Treaty between Germany and Austria-Hungary, 1879",
                    description="Excerpt from the secret military alliance between Germany and Austria-Hungary",
                    source_type=SourceType.TREATY,
                    content="""Article I. Should, contrary to their hope, and against the loyal desire of the two High Contracting Parties, one of the two Empires be attacked by Russia, the High Contracting Parties are bound to come to the assistance one of the other with the whole war strength of their Empires...""",
                    date_created="1879-10-07",
                    author="German and Austro-Hungarian governments",
                    historical_period=HistoricalPeriod.MODERN_ERA,
                    intended_audience="Government officials",
                    purpose="Military alliance for mutual defense"
                ),
                guiding_questions=[
                    "What does this treaty require each nation to do?",
                    "How might this alliance system contribute to war?"
                ]
            ),
            
            DBQDocument(
                document_id="wwi_doc_b", 
                document_label="Document B",
                source=PrimarySource(
                    source_id="german_naval_law_1900",
                    title="German Naval Law, 1900",
                    description="Excerpt from German law expanding naval construction",
                    source_type=SourceType.GOVERNMENT_RECORD,
                    content="""The German Empire must possess a battle fleet of such strength that even for the mightiest naval Power, a war would involve such risks as to make that Power's own supremacy doubtful.""",
                    date_created="1900",
                    author="German Reichstag",
                    historical_period=HistoricalPeriod.MODERN_ERA,
                    intended_audience="German parliament and public",
                    purpose="Justify naval expansion"
                ),
                guiding_questions=[
                    "What is Germany's goal for its navy?",
                    "How might this contribute to international tensions?"
                ]
            ),
            
            DBQDocument(
                document_id="wwi_doc_c",
                document_label="Document C",
                source=PrimarySource(
                    source_id="assassination_report_1914",
                    title="Report on Assassination of Archduke Franz Ferdinand, 1914",
                    description="Contemporary newspaper account of the assassination",
                    source_type=SourceType.NEWSPAPER,
                    content="""Archduke Franz Ferdinand of Austria-Hungary and his wife were shot dead in Sarajevo today by a Bosnian Serb nationalist. The shots were fired by Gavrilo Princip, a member of the secret society known as the Black Hand. The assassination has sent shockwaves throughout Europe...""",
                    date_created="1914-06-28",
                    author="Contemporary journalist",
                    historical_period=HistoricalPeriod.MODERN_ERA,
                    intended_audience="General public",
                    purpose="Report breaking news"
                ),
                guiding_questions=[
                    "Who carried out the assassination and why?",
                    "Why was this event so significant for Europe?"
                ]
            ),
            
            DBQDocument(
                document_id="wwi_doc_d",
                document_label="Document D",
                source=PrimarySource(
                    source_id="imperialism_cartoon_1912",
                    title="Political Cartoon: 'The Boiling Point', 1912",
                    description="Cartoon showing European powers as different animals around a pot labeled 'Balkan Troubles'",
                    source_type=SourceType.ARTWORK,
                    content="[Political cartoon depicting European nations as animals gathered around a boiling pot, with tension evident in their postures and expressions]",
                    date_created="1912",
                    author="Political cartoonist",
                    historical_period=HistoricalPeriod.MODERN_ERA,
                    intended_audience="Newspaper readers",
                    purpose="Comment on European tensions"
                ),
                guiding_questions=[
                    "What does this cartoon suggest about European tensions?",
                    "What role did the Balkans play in pre-war tensions?"
                ]
            )
        ]
        
        return DBQSet(
            dbq_id="wwi_causes_dbq",
            title="Causes of World War I DBQ",
            prompt=prompt,
            documents=documents,
            historical_period=HistoricalPeriod.MODERN_ERA,
            theme="World War I Origins",
            difficulty_level=0.7
        )
    
    def _create_cold_war_origins_dbq(self) -> DBQSet:
        """Create Cold War origins DBQ."""
        
        prompt = DBQPrompt(
            prompt_id="cold_war_origins_prompt",
            title="Origins of the Cold War",
            historical_question="To what extent was the United States responsible for the start of the Cold War?",
            task_description="""
            Analyze the role of the United States in the origins of the Cold War (1945-1947).
            Consider multiple perspectives and evaluate the extent of American responsibility.
            """,
            historical_context_provided="""
            At the end of World War II, the United States and Soviet Union emerged as the world's 
            two superpowers. Despite their wartime alliance, tensions quickly developed over the 
            future of Eastern Europe, nuclear weapons, and competing ideological systems.
            """,
            time_period="1945-1947",
            historical_thinking_skills=[
                HistoricalThinkingSkill.HISTORICAL_INTERPRETATION,
                HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION
            ]
        )
        
        # This would include documents like Truman Doctrine, Stalin speeches, etc.
        # Simplified for this implementation
        documents = [
            DBQDocument(
                document_id="cold_war_doc_a",
                document_label="Document A",
                source=PrimarySource(
                    source_id="truman_doctrine_1947",
                    title="Truman Doctrine Speech, 1947",
                    description="President Truman's speech to Congress requesting aid for Greece and Turkey",
                    source_type=SourceType.SPEECH,
                    content="I believe it must be the policy of the United States to support free peoples who are resisting attempted subjugation...",
                    date_created="1947-03-12",
                    author="President Harry Truman",
                    historical_period=HistoricalPeriod.CONTEMPORARY
                )
            )
        ]
        
        return DBQSet(
            dbq_id="cold_war_origins_dbq",
            title="Cold War Origins DBQ",
            prompt=prompt,
            documents=documents,
            historical_period=HistoricalPeriod.CONTEMPORARY,
            theme="Cold War Origins"
        )
    
    def start_dbq_session(
        self,
        student_id: str,
        dbq_id: str,
        session_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new DBQ session for a student."""
        
        dbq_set = self.dbq_templates.get(dbq_id)
        if not dbq_set:
            raise ValueError(f"DBQ set {dbq_id} not found")
        
        session = {
            "session_id": f"dbq_{student_id}_{dbq_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "student_id": student_id,
            "dbq_id": dbq_id,
            "dbq_set": dbq_set,
            "started_at": datetime.now(),
            "current_phase": "document_analysis",
            "phases_completed": [],
            "document_analyses": {},
            "essay_drafts": [],
            "time_spent_minutes": 0
        }
        
        return session
    
    def analyze_documents_phase(
        self,
        session: Dict[str, Any],
        document_analyses: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process the document analysis phase."""
        
        dbq_set = session["dbq_set"]
        feedback = {}
        
        for doc_label, analysis in document_analyses.items():
            # Find the document
            document = None
            for doc in dbq_set.documents:
                if doc.document_label == doc_label:
                    document = doc
                    break
            
            if not document:
                continue
            
            # Analyze the student's analysis
            source_analysis = self.source_analyzer.analyze_source(
                document.source,
                student_response=analysis,
                guided_analysis=True
            )
            
            feedback[doc_label] = {
                "student_analysis": analysis,
                "source_analysis": source_analysis,
                "suggestions": self._generate_document_analysis_suggestions(
                    document, analysis, source_analysis
                )
            }
        
        session["document_analyses"] = feedback
        session["phases_completed"].append("document_analysis")
        session["current_phase"] = "thesis_development"
        
        return {
            "phase_completed": "document_analysis",
            "next_phase": "thesis_development",
            "document_feedback": feedback,
            "overall_suggestions": self._generate_overall_document_suggestions(feedback)
        }
    
    def _generate_document_analysis_suggestions(
        self,
        document: DBQDocument,
        student_analysis: str,
        source_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate suggestions for document analysis improvement."""
        
        suggestions = []
        
        evaluation = source_analysis.get("student_analysis_feedback", {})
        
        # Check if key elements are addressed
        if evaluation.get("criteria_scores", {}).get("source_identification", {}).get("score", 0) < 0.5:
            suggestions.append("Make sure to identify the author, date, and type of source")
        
        if evaluation.get("criteria_scores", {}).get("bias_recognition", {}).get("score", 0) < 0.5:
            suggestions.append("Consider what biases or limitations this source might have")
        
        # Document-specific suggestions
        for question in document.guiding_questions:
            if not any(keyword in student_analysis.lower() 
                      for keyword in question.lower().split()[:3]):  # Check first 3 words
                suggestions.append(f"Consider addressing: {question}")
        
        return suggestions
    
    def _generate_overall_document_suggestions(
        self,
        document_feedback: Dict[str, Any]
    ) -> List[str]:
        """Generate overall suggestions for the document analysis phase."""
        
        suggestions = []
        
        # Check how many documents were analyzed
        num_analyzed = len(document_feedback)
        if num_analyzed < 4:
            suggestions.append("Analyze at least 4 documents to meet the requirement")
        
        # Check for patterns in analysis quality
        low_quality_analyses = 0
        for doc_feedback in document_feedback.values():
            evaluation = doc_feedback.get("source_analysis", {}).get("student_analysis_feedback", {})
            if evaluation.get("overall_score", 0) < 0.5:
                low_quality_analyses += 1
        
        if low_quality_analyses > 2:
            suggestions.append("Focus on deeper analysis of sources - consider author, purpose, bias, and reliability")
        
        suggestions.append("Think about how these documents can be used together to support an argument")
        
        return suggestions
    
    def thesis_development_phase(
        self,
        session: Dict[str, Any],
        proposed_thesis: str
    ) -> Dict[str, Any]:
        """Process the thesis development phase."""
        
        dbq_set = session["dbq_set"]
        
        # Evaluate thesis quality
        thesis_evaluation = self._evaluate_thesis(proposed_thesis, dbq_set.prompt)
        
        session["proposed_thesis"] = proposed_thesis
        session["thesis_evaluation"] = thesis_evaluation
        
        if thesis_evaluation["score"] >= 0.7:
            session["phases_completed"].append("thesis_development")
            session["current_phase"] = "essay_writing"
        
        return {
            "thesis_evaluation": thesis_evaluation,
            "suggestions": thesis_evaluation.get("suggestions", []),
            "next_phase": "essay_writing" if thesis_evaluation["score"] >= 0.7 else "thesis_development"
        }
    
    def _evaluate_thesis(self, thesis: str, prompt: DBQPrompt) -> Dict[str, Any]:
        """Evaluate the quality of a thesis statement."""
        
        evaluation = {
            "score": 0.0,
            "strengths": [],
            "weaknesses": [],
            "suggestions": []
        }
        
        if not thesis or len(thesis.strip()) < 20:
            evaluation["weaknesses"].append("Thesis is too short or missing")
            evaluation["suggestions"].append("Develop a more substantial thesis statement")
            return evaluation
        
        thesis_lower = thesis.lower()
        prompt_lower = prompt.historical_question.lower()
        
        # Check if thesis addresses the prompt
        key_words = [word for word in prompt_lower.split() if len(word) > 3]
        addresses_prompt = sum(1 for word in key_words if word in thesis_lower) >= len(key_words) // 2
        
        if addresses_prompt:
            evaluation["score"] += 0.3
            evaluation["strengths"].append("Addresses the historical question")
        else:
            evaluation["weaknesses"].append("Does not clearly address the prompt")
            evaluation["suggestions"].append("Make sure your thesis directly answers the historical question")
        
        # Check for defensibility (argument quality)
        argument_indicators = ["because", "since", "due to", "resulted from", "caused by", "led to"]
        has_reasoning = any(indicator in thesis_lower for indicator in argument_indicators)
        
        if has_reasoning:
            evaluation["score"] += 0.25
            evaluation["strengths"].append("Includes causal reasoning")
        else:
            evaluation["suggestions"].append("Include reasoning or causation in your thesis")
        
        # Check for specificity
        vague_words = ["many", "some", "various", "several", "things", "factors"]
        specific_words = ["economic", "political", "social", "military", "nationalism", "imperialism"]
        
        vague_count = sum(1 for word in vague_words if word in thesis_lower)
        specific_count = sum(1 for word in specific_words if word in thesis_lower)
        
        if specific_count > vague_count:
            evaluation["score"] += 0.25
            evaluation["strengths"].append("Uses specific historical terms")
        else:
            evaluation["suggestions"].append("Use more specific historical terms rather than vague language")
        
        # Check for complexity/nuance
        complexity_indicators = ["however", "although", "while", "whereas", "both", "not only"]
        has_complexity = any(indicator in thesis_lower for indicator in complexity_indicators)
        
        if has_complexity:
            evaluation["score"] += 0.2
            evaluation["strengths"].append("Shows historical complexity")
        else:
            evaluation["suggestions"].append("Consider adding nuance or complexity to your argument")
        
        # Overall assessment
        if evaluation["score"] >= 0.8:
            evaluation["overall"] = "Strong thesis statement"
        elif evaluation["score"] >= 0.6:
            evaluation["overall"] = "Good thesis with room for improvement"
        elif evaluation["score"] >= 0.4:
            evaluation["overall"] = "Developing thesis needs strengthening"
        else:
            evaluation["overall"] = "Thesis needs significant revision"
        
        return evaluation
    
    def essay_writing_phase(
        self,
        session: Dict[str, Any],
        essay_draft: str
    ) -> Dict[str, Any]:
        """Process the essay writing phase."""
        
        dbq_set = session["dbq_set"]
        
        # Create DBQ essay object
        essay = DBQEssay(
            essay_id=f"{session['session_id']}_draft_{len(session.get('essay_drafts', []))}",
            student_id=session["student_id"],
            dbq_id=session["dbq_id"],
            thesis_statement=session.get("proposed_thesis", ""),
            full_text=essay_draft,
            word_count=len(essay_draft.split()),
            draft_number=len(session.get("essay_drafts", [])) + 1
        )
        
        # Analyze document usage
        essay = self._analyze_document_usage(essay, dbq_set)
        
        # Grade the essay
        grading_results = self._grade_dbq_essay(essay, dbq_set)
        
        essay.score = grading_results["overall_score"]
        essay.rubric_scores = grading_results["rubric_scores"]
        essay.feedback = grading_results["feedback"]
        
        # Add to session
        if "essay_drafts" not in session:
            session["essay_drafts"] = []
        session["essay_drafts"].append(essay)
        
        session["phases_completed"].append("essay_writing")
        session["current_phase"] = "completed"
        
        return {
            "essay": essay,
            "grading_results": grading_results,
            "next_steps": self._generate_next_steps(grading_results)
        }
    
    def _analyze_document_usage(self, essay: DBQEssay, dbq_set: DBQSet) -> DBQEssay:
        """Analyze how documents are used in the essay."""
        
        essay_lower = essay.full_text.lower()
        
        # Check for document references
        for document in dbq_set.documents:
            doc_label_lower = document.document_label.lower()
            
            # Check for direct references to document
            if doc_label_lower in essay_lower or document.document_id in essay_lower:
                essay.documents_used.append(document.document_id)
                
                # Find citations/references
                citations = []
                # Simple citation detection - would be more sophisticated in production
                sentences = essay.full_text.split('.')
                for sentence in sentences:
                    if doc_label_lower in sentence.lower():
                        citations.append(sentence.strip())
                
                if citations:
                    essay.document_citations[document.document_id] = citations
            
            # Check for content usage without explicit citation
            elif document.source.content:
                # Look for key phrases from the document
                content_phrases = [phrase.strip() for phrase in document.source.content.split('.') 
                                 if len(phrase.strip()) > 10][:3]  # First 3 sentences
                
                for phrase in content_phrases:
                    key_words = [word for word in phrase.split() if len(word) > 4][:3]
                    if len(key_words) >= 2 and all(word.lower() in essay_lower for word in key_words):
                        if document.document_id not in essay.documents_used:
                            essay.documents_used.append(document.document_id)
                        break
        
        return essay
    
    def _grade_dbq_essay(self, essay: DBQEssay, dbq_set: DBQSet) -> Dict[str, Any]:
        """Grade a DBQ essay using rubric."""
        
        rubric_scores = {}
        
        # Thesis evaluation (already done)
        thesis_score = self._evaluate_thesis(essay.thesis_statement, dbq_set.prompt)["score"]
        rubric_scores["thesis"] = thesis_score * 100
        
        # Document usage
        doc_usage_score = self._evaluate_document_usage(essay, dbq_set)
        rubric_scores["document_usage"] = doc_usage_score
        
        # Outside evidence
        outside_evidence_score = self._evaluate_outside_evidence(essay)
        rubric_scores["outside_evidence"] = outside_evidence_score
        
        # Historical reasoning
        reasoning_score = self._evaluate_historical_reasoning(essay, dbq_set)
        rubric_scores["historical_reasoning"] = reasoning_score
        
        # Writing quality
        writing_score = self._evaluate_writing_quality(essay)
        rubric_scores["writing_quality"] = writing_score
        
        # Calculate overall score
        overall_score = sum(
            rubric_scores[criterion] * self.rubric_weights[criterion]
            for criterion in self.rubric_weights
        )
        
        # Generate feedback
        feedback = self._generate_essay_feedback(rubric_scores, overall_score)
        
        return {
            "overall_score": overall_score,
            "rubric_scores": rubric_scores,
            "feedback": feedback,
            "grade_level": self._determine_grade_level(overall_score)
        }
    
    def _evaluate_document_usage(self, essay: DBQEssay, dbq_set: DBQSet) -> float:
        """Evaluate how well documents are used in the essay."""
        
        total_documents = len(dbq_set.documents)
        documents_used = len(essay.documents_used)
        
        # Base score on number of documents used
        usage_score = min(100, (documents_used / max(4, total_documents)) * 80)
        
        # Bonus for effective citation
        if essay.document_citations:
            avg_citations_per_doc = sum(len(citations) for citations in essay.document_citations.values()) / len(essay.document_citations)
            if avg_citations_per_doc >= 2:  # Multiple citations per document
                usage_score += 10
        
        # Check for document grouping/comparison
        essay_lower = essay.full_text.lower()
        comparison_words = ["both", "similar", "different", "whereas", "while", "compared to"]
        
        if any(word in essay_lower for word in comparison_words) and documents_used >= 2:
            usage_score += 10
        
        return min(100, usage_score)
    
    def _evaluate_outside_evidence(self, essay: DBQEssay) -> float:
        """Evaluate use of outside historical evidence."""
        
        essay_lower = essay.full_text.lower()
        
        # Look for indicators of outside evidence
        outside_indicators = [
            "additionally", "furthermore", "also", "another example",
            "historians argue", "scholars believe", "research shows"
        ]
        
        historical_terms = [
            "treaty", "battle", "war", "revolution", "movement", "policy",
            "economic", "political", "social", "cultural", "military"
        ]
        
        specific_names = [
            # This would be expanded with many more historical figures, events, etc.
            "wilson", "roosevelt", "churchill", "stalin", "hitler",
            "versailles", "league of nations", "united nations"
        ]
        
        evidence_score = 0
        
        # Check for outside evidence indicators
        outside_usage = sum(1 for indicator in outside_indicators if indicator in essay_lower)
        if outside_usage > 0:
            evidence_score += 30
        
        # Check for historical terminology beyond documents
        term_usage = sum(1 for term in historical_terms if term in essay_lower)
        evidence_score += min(40, term_usage * 5)
        
        # Check for specific historical references
        specific_usage = sum(1 for name in specific_names if name in essay_lower)
        evidence_score += min(30, specific_usage * 10)
        
        return min(100, evidence_score)
    
    def _evaluate_historical_reasoning(self, essay: DBQEssay, dbq_set: DBQSet) -> float:
        """Evaluate historical reasoning skills demonstrated."""
        
        essay_lower = essay.full_text.lower()
        reasoning_score = 0
        
        # Causation
        causation_words = ["caused", "led to", "resulted in", "because", "due to", "consequence"]
        causation_usage = sum(1 for word in causation_words if word in essay_lower)
        if causation_usage >= 3:
            reasoning_score += 25
        elif causation_usage >= 1:
            reasoning_score += 15
        
        # Comparison/Contextualization
        comparison_words = ["similar", "different", "compared to", "in contrast", "whereas"]
        comparison_usage = sum(1 for word in comparison_words if word in essay_lower)
        if comparison_usage >= 2:
            reasoning_score += 25
        elif comparison_usage >= 1:
            reasoning_score += 15
        
        # Change over time
        time_words = ["before", "after", "during", "by", "until", "from", "to"]
        time_usage = sum(1 for word in time_words if word in essay_lower)
        if time_usage >= 5:
            reasoning_score += 25
        elif time_usage >= 3:
            reasoning_score += 15
        
        # Synthesis
        synthesis_words = ["therefore", "thus", "consequently", "ultimately", "overall"]
        synthesis_usage = sum(1 for word in synthesis_words if word in essay_lower)
        if synthesis_usage >= 2:
            reasoning_score += 25
        elif synthesis_usage >= 1:
            reasoning_score += 15
        
        return min(100, reasoning_score)
    
    def _evaluate_writing_quality(self, essay: DBQEssay) -> float:
        """Evaluate writing quality and organization."""
        
        writing_score = 50  # Base score
        
        # Word count evaluation
        if 800 <= essay.word_count <= 1200:  # Ideal range
            writing_score += 20
        elif 600 <= essay.word_count <= 1400:  # Acceptable range
            writing_score += 10
        elif essay.word_count < 400:  # Too short
            writing_score -= 20
        
        # Paragraph structure (simple check)
        paragraphs = essay.full_text.split('\n\n')
        if 4 <= len(paragraphs) <= 6:  # Good structure
            writing_score += 15
        elif len(paragraphs) < 3:  # Poor structure
            writing_score -= 15
        
        # Sentence variety (simple check)
        sentences = essay.full_text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        if 12 <= avg_sentence_length <= 20:  # Good variety
            writing_score += 15
        elif avg_sentence_length < 8 or avg_sentence_length > 25:  # Poor variety
            writing_score -= 10
        
        return min(100, max(0, writing_score))
    
    def _generate_essay_feedback(self, rubric_scores: Dict[str, float], overall_score: float) -> str:
        """Generate comprehensive feedback for the essay."""
        
        feedback_parts = []
        
        # Overall assessment
        if overall_score >= 80:
            feedback_parts.append("Excellent work! This is a strong DBQ essay.")
        elif overall_score >= 70:
            feedback_parts.append("Good job! This essay demonstrates solid historical thinking.")
        elif overall_score >= 60:
            feedback_parts.append("Developing work. You show understanding but need to strengthen key areas.")
        else:
            feedback_parts.append("This essay needs significant improvement in multiple areas.")
        
        # Specific feedback by category
        if rubric_scores.get("thesis", 0) < 60:
            feedback_parts.append("Strengthen your thesis: make it more specific, defensible, and directly address the prompt.")
        
        if rubric_scores.get("document_usage", 0) < 70:
            feedback_parts.append("Use more documents and cite them more effectively in your argument.")
        
        if rubric_scores.get("outside_evidence", 0) < 60:
            feedback_parts.append("Incorporate more outside historical evidence beyond the provided documents.")
        
        if rubric_scores.get("historical_reasoning", 0) < 70:
            feedback_parts.append("Demonstrate clearer historical reasoning: show causation, make comparisons, analyze change over time.")
        
        if rubric_scores.get("writing_quality", 0) < 70:
            feedback_parts.append("Improve writing organization and clarity.")
        
        return " ".join(feedback_parts)
    
    def _determine_grade_level(self, overall_score: float) -> str:
        """Determine letter grade based on score."""
        
        if overall_score >= 90:
            return "A"
        elif overall_score >= 80:
            return "B"
        elif overall_score >= 70:
            return "C"
        elif overall_score >= 60:
            return "D"
        else:
            return "F"
    
    def _generate_next_steps(self, grading_results: Dict[str, Any]) -> List[str]:
        """Generate next steps for student improvement."""
        
        next_steps = []
        rubric_scores = grading_results["rubric_scores"]
        
        # Identify weakest areas
        weakest_area = min(rubric_scores, key=rubric_scores.get)
        
        if weakest_area == "thesis":
            next_steps.extend([
                "Practice writing clear, defensible thesis statements",
                "Make sure your thesis directly answers the historical question",
                "Include specific historical reasoning in your thesis"
            ])
        elif weakest_area == "document_usage":
            next_steps.extend([
                "Practice analyzing and citing primary sources",
                "Use at least 4 documents in your argument",
                "Group documents by theme or perspective"
            ])
        elif weakest_area == "outside_evidence":
            next_steps.extend([
                "Review key historical facts and concepts for this time period",
                "Practice incorporating outside evidence into arguments",
                "Connect document evidence to broader historical context"
            ])
        elif weakest_area == "historical_reasoning":
            next_steps.extend([
                "Practice identifying cause-and-effect relationships",
                "Work on comparing different perspectives",
                "Analyze how events changed over time"
            ])
        
        return next_steps
    
    def get_dbq_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available DBQ templates."""
        
        return {
            dbq_id: {
                "title": dbq_set.title,
                "theme": dbq_set.theme,
                "period": dbq_set.historical_period.value,
                "difficulty": dbq_set.difficulty_level,
                "estimated_time": dbq_set.estimated_time_minutes,
                "document_count": len(dbq_set.documents),
                "skills_assessed": [skill.value for skill in dbq_set.prompt.historical_thinking_skills]
            }
            for dbq_id, dbq_set in self.dbq_templates.items()
        }
    
    def get_dbq_by_id(self, dbq_id: str) -> Optional[DBQSet]:
        """Get a DBQ set by ID."""
        return self.dbq_templates.get(dbq_id)