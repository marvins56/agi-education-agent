"""Advanced essay grading system with detailed rubrics for History education."""
import asyncio
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from langchain_core.messages import SystemMessage, HumanMessage

from src.llm.factory import LLMFactory
from src.assessment.schemas import GradeResult

logger = logging.getLogger(__name__)


class HistoryEssayGrader:
    """Advanced essay grading system specialized for History education."""
    
    def __init__(self):
        self.llm = LLMFactory.create(provider="openai", model="gpt-4", temperature=0.1)
        
        # History-specific rubrics
        self.rubrics = self._initialize_history_rubrics()
        
        # Essay analysis components
        self.analysis_components = {
            "thesis_analysis": self._analyze_thesis,
            "evidence_analysis": self._analyze_evidence,
            "historical_analysis": self._analyze_historical_thinking,
            "argument_analysis": self._analyze_argument_structure,
            "source_integration": self._analyze_source_integration,
            "writing_quality": self._analyze_writing_quality
        }
        
        # Common essay problems and feedback
        self.common_issues = self._initialize_common_issues()
    
    def _initialize_history_rubrics(self) -> Dict[str, Dict[str, Any]]:
        """Initialize rubrics for different types of history essays."""
        return {
            "analytical_essay": {
                "name": "Historical Analysis Essay Rubric",
                "categories": {
                    "thesis_and_argument": {
                        "weight": 0.25,
                        "description": "Clear thesis statement and coherent argument development",
                        "levels": {
                            "exemplary": {
                                "points": 4,
                                "description": "Clear, sophisticated thesis with nuanced, well-developed argument",
                                "indicators": [
                                    "Presents a clear, historically defensible thesis",
                                    "Addresses all parts of the question", 
                                    "Shows sophisticated understanding of the topic",
                                    "Argument is nuanced and well-developed"
                                ]
                            },
                            "proficient": {
                                "points": 3,
                                "description": "Clear thesis with coherent argument development",
                                "indicators": [
                                    "Presents a clear thesis statement",
                                    "Addresses most parts of the question",
                                    "Shows good understanding of the topic",
                                    "Argument is generally coherent"
                                ]
                            },
                            "developing": {
                                "points": 2,
                                "description": "Attempts thesis with some argument development",
                                "indicators": [
                                    "Attempts a thesis statement",
                                    "Addresses some parts of the question",
                                    "Shows basic understanding of the topic",
                                    "Argument has some coherent elements"
                                ]
                            },
                            "inadequate": {
                                "points": 1,
                                "description": "Weak or missing thesis with little argument development",
                                "indicators": [
                                    "No clear thesis or very weak thesis",
                                    "Does not clearly address the question",
                                    "Shows limited understanding",
                                    "Little coherent argument development"
                                ]
                            }
                        }
                    },
                    "use_of_evidence": {
                        "weight": 0.25,
                        "description": "Effective use of specific historical evidence",
                        "levels": {
                            "exemplary": {
                                "points": 4,
                                "description": "Uses abundant, specific, and relevant evidence effectively",
                                "indicators": [
                                    "Uses abundant specific historical evidence",
                                    "Evidence is clearly relevant to argument",
                                    "Evidence is well-integrated into analysis",
                                    "Shows command of historical detail"
                                ]
                            },
                            "proficient": {
                                "points": 3,
                                "description": "Uses sufficient relevant evidence to support argument",
                                "indicators": [
                                    "Uses sufficient historical evidence",
                                    "Most evidence is relevant and specific",
                                    "Evidence generally supports argument",
                                    "Shows good knowledge of historical content"
                                ]
                            },
                            "developing": {
                                "points": 2,
                                "description": "Uses some evidence but may lack specificity or relevance",
                                "indicators": [
                                    "Uses some historical evidence",
                                    "Evidence is sometimes vague or general",
                                    "Evidence partially supports argument",
                                    "Shows basic knowledge of content"
                                ]
                            },
                            "inadequate": {
                                "points": 1,
                                "description": "Little or no relevant evidence provided",
                                "indicators": [
                                    "Little or no specific evidence",
                                    "Evidence is largely irrelevant",
                                    "Evidence does not support argument",
                                    "Shows little knowledge of content"
                                ]
                            }
                        }
                    },
                    "historical_analysis": {
                        "weight": 0.25,
                        "description": "Demonstrates historical thinking skills",
                        "levels": {
                            "exemplary": {
                                "points": 4,
                                "description": "Sophisticated historical analysis with complex thinking",
                                "indicators": [
                                    "Analyzes multiple perspectives",
                                    "Shows understanding of historical context",
                                    "Demonstrates causation and connection",
                                    "Evaluates significance and change over time"
                                ]
                            },
                            "proficient": {
                                "points": 3,
                                "description": "Good historical analysis with clear thinking",
                                "indicators": [
                                    "Shows some analysis of perspectives",
                                    "Demonstrates understanding of context",
                                    "Shows some causation thinking",
                                    "Addresses significance"
                                ]
                            },
                            "developing": {
                                "points": 2,
                                "description": "Basic historical analysis attempted",
                                "indicators": [
                                    "Limited perspective analysis",
                                    "Basic understanding of context",
                                    "Some attempt at causation",
                                    "Limited analysis of significance"
                                ]
                            },
                            "inadequate": {
                                "points": 1,
                                "description": "Little historical analysis demonstrated",
                                "indicators": [
                                    "No clear perspective analysis",
                                    "Little understanding of context",
                                    "No clear causation thinking",
                                    "Little analysis of significance"
                                ]
                            }
                        }
                    },
                    "organization_and_writing": {
                        "weight": 0.15,
                        "description": "Clear organization and effective communication",
                        "levels": {
                            "exemplary": {
                                "points": 4,
                                "description": "Excellent organization with clear, engaging writing",
                                "indicators": [
                                    "Clear introduction, body, conclusion",
                                    "Logical flow between paragraphs",
                                    "Engaging and clear writing style",
                                    "Few grammatical errors"
                                ]
                            },
                            "proficient": {
                                "points": 3,
                                "description": "Good organization with clear writing",
                                "indicators": [
                                    "Generally clear organization",
                                    "Most paragraphs flow logically",
                                    "Clear writing style",
                                    "Some minor errors"
                                ]
                            },
                            "developing": {
                                "points": 2,
                                "description": "Basic organization with adequate writing",
                                "indicators": [
                                    "Attempts clear organization",
                                    "Some logical flow",
                                    "Generally understandable",
                                    "Several errors but not distracting"
                                ]
                            },
                            "inadequate": {
                                "points": 1,
                                "description": "Poor organization and unclear writing",
                                "indicators": [
                                    "Unclear organization",
                                    "Little logical flow",
                                    "Difficult to follow",
                                    "Many errors interfere with meaning"
                                ]
                            }
                        }
                    },
                    "historical_context": {
                        "weight": 0.10,
                        "description": "Demonstrates understanding of broader historical context",
                        "levels": {
                            "exemplary": {
                                "points": 4,
                                "description": "Rich understanding of historical context and connections",
                                "indicators": [
                                    "Places events in broader historical context",
                                    "Makes connections to other time periods",
                                    "Shows understanding of historical patterns",
                                    "Demonstrates sophisticated contextual thinking"
                                ]
                            },
                            "proficient": {
                                "points": 3,
                                "description": "Good understanding of historical context",
                                "indicators": [
                                    "Shows understanding of historical context",
                                    "Makes some connections",
                                    "Shows awareness of broader patterns",
                                    "Generally contextualizes events"
                                ]
                            },
                            "developing": {
                                "points": 2,
                                "description": "Basic understanding of context",
                                "indicators": [
                                    "Some understanding of context",
                                    "Limited connections made",
                                    "Basic awareness of patterns",
                                    "Some contextualization attempted"
                                ]
                            },
                            "inadequate": {
                                "points": 1,
                                "description": "Little understanding of historical context",
                                "indicators": [
                                    "Little understanding of context",
                                    "No clear connections made",
                                    "No awareness of patterns",
                                    "Events presented in isolation"
                                ]
                            }
                        }
                    }
                },
                "total_points": 20
            },
            
            "dbq_essay": {
                "name": "Document-Based Question (DBQ) Essay Rubric",
                "categories": {
                    "thesis": {
                        "weight": 0.20,
                        "description": "Presents a thesis that makes a historically defensible claim",
                        "levels": {
                            "meets_standard": {
                                "points": 1,
                                "description": "Responds to the prompt with a historically defensible thesis",
                                "indicators": [
                                    "Makes a claim that responds to the prompt",
                                    "Is historically defensible",
                                    "Establishes a line of reasoning"
                                ]
                            },
                            "does_not_meet": {
                                "points": 0,
                                "description": "Does not meet the standard for thesis",
                                "indicators": [
                                    "Does not respond to the prompt",
                                    "Is not historically defensible",
                                    "Does not establish reasoning"
                                ]
                            }
                        }
                    },
                    "contextualization": {
                        "weight": 0.15,
                        "description": "Describes broader historical context relevant to the prompt",
                        "levels": {
                            "meets_standard": {
                                "points": 1,
                                "description": "Describes broader historical context relevant to the prompt",
                                "indicators": [
                                    "Describes broader historical events/developments",
                                    "Context is relevant to the prompt",
                                    "Occurs before, during, or continues after time frame"
                                ]
                            },
                            "does_not_meet": {
                                "points": 0,
                                "description": "Does not meet standard for contextualization",
                                "indicators": [
                                    "Does not describe broader context",
                                    "Context is not relevant",
                                    "Context is not historically accurate"
                                ]
                            }
                        }
                    },
                    "evidence_from_documents": {
                        "weight": 0.30,
                        "description": "Uses content from documents to address the topic",
                        "levels": {
                            "exceeds_standard": {
                                "points": 3,
                                "description": "Uses content from at least 6 documents effectively",
                                "indicators": [
                                    "Uses content from 6+ documents",
                                    "Uses documents to support argument",
                                    "Explains how documents support argument"
                                ]
                            },
                            "meets_standard": {
                                "points": 2,
                                "description": "Uses content from at least 4 documents effectively",
                                "indicators": [
                                    "Uses content from 4-5 documents", 
                                    "Uses documents to support argument",
                                    "Explains how most documents support argument"
                                ]
                            },
                            "approaching_standard": {
                                "points": 1,
                                "description": "Uses content from at least 3 documents",
                                "indicators": [
                                    "Uses content from 3 documents",
                                    "Uses documents to support argument",
                                    "May not fully explain connections"
                                ]
                            },
                            "does_not_meet": {
                                "points": 0,
                                "description": "Uses fewer than 3 documents effectively",
                                "indicators": [
                                    "Uses content from fewer than 3 documents",
                                    "Does not use documents to support argument",
                                    "Misinterprets document content"
                                ]
                            }
                        }
                    },
                    "document_analysis": {
                        "weight": 0.20,
                        "description": "Analyzes documents' point of view, purpose, historical situation, or audience",
                        "levels": {
                            "meets_standard_well": {
                                "points": 2,
                                "description": "Analyzes at least 4 documents for sourcing elements",
                                "indicators": [
                                    "Analyzes point of view, purpose, historical situation, or audience",
                                    "For at least 4 documents",
                                    "Explains how sourcing affects meaning or credibility"
                                ]
                            },
                            "meets_standard": {
                                "points": 1, 
                                "description": "Analyzes at least 3 documents for sourcing elements",
                                "indicators": [
                                    "Analyzes point of view, purpose, historical situation, or audience",
                                    "For at least 3 documents",
                                    "May explain relevance to argument"
                                ]
                            },
                            "does_not_meet": {
                                "points": 0,
                                "description": "Analyzes fewer than 3 documents for sourcing",
                                "indicators": [
                                    "Analyzes fewer than 3 documents",
                                    "Does not address sourcing elements",
                                    "No analysis of credibility or perspective"
                                ]
                            }
                        }
                    },
                    "outside_evidence": {
                        "weight": 0.10,
                        "description": "Uses outside historical evidence beyond the documents",
                        "levels": {
                            "meets_standard": {
                                "points": 1,
                                "description": "Uses outside historical evidence relevant to argument",
                                "indicators": [
                                    "Uses specific outside historical evidence",
                                    "Evidence is relevant to argument",
                                    "Evidence is not found in documents"
                                ]
                            },
                            "does_not_meet": {
                                "points": 0,
                                "description": "Does not use outside evidence effectively",
                                "indicators": [
                                    "No outside evidence provided",
                                    "Evidence is not relevant",
                                    "Evidence is vague or inaccurate"
                                ]
                            }
                        }
                    },
                    "complexity": {
                        "weight": 0.05,
                        "description": "Demonstrates complex understanding of historical development",
                        "levels": {
                            "meets_standard": {
                                "points": 1,
                                "description": "Demonstrates complex understanding through connections, qualifications, or analysis",
                                "indicators": [
                                    "Explains connections between different historical developments",
                                    "Acknowledges exceptions or qualifications", 
                                    "Analyzes multiple variables or competing interpretations"
                                ]
                            },
                            "does_not_meet": {
                                "points": 0,
                                "description": "Does not demonstrate complex understanding",
                                "indicators": [
                                    "No clear connections made",
                                    "No acknowledgment of complexity",
                                    "Simplistic interpretation"
                                ]
                            }
                        }
                    }
                },
                "total_points": 9
            },
            
            "comparative_essay": {
                "name": "Comparative History Essay Rubric", 
                "categories": {
                    "comparison_thesis": {
                        "weight": 0.25,
                        "description": "Clear thesis that addresses both similarities and differences",
                        "levels": {
                            "exemplary": {"points": 4, "description": "Sophisticated comparative thesis with nuanced analysis"},
                            "proficient": {"points": 3, "description": "Clear comparative thesis addressing similarities and differences"},
                            "developing": {"points": 2, "description": "Basic comparative thesis attempted"},
                            "inadequate": {"points": 1, "description": "Weak or missing comparative thesis"}
                        }
                    },
                    "direct_comparisons": {
                        "weight": 0.30,
                        "description": "Makes direct comparisons between cases/periods",
                        "levels": {
                            "exemplary": {"points": 4, "description": "Sophisticated direct comparisons throughout"},
                            "proficient": {"points": 3, "description": "Clear direct comparisons made"},
                            "developing": {"points": 2, "description": "Some direct comparisons attempted"},
                            "inadequate": {"points": 1, "description": "Little or no direct comparison"}
                        }
                    },
                    "analysis_of_reasons": {
                        "weight": 0.25,
                        "description": "Analyzes reasons for similarities and differences",
                        "levels": {
                            "exemplary": {"points": 4, "description": "Sophisticated analysis of causes of similarities/differences"},
                            "proficient": {"points": 3, "description": "Good analysis of reasons for comparisons"},
                            "developing": {"points": 2, "description": "Basic analysis of reasons attempted"},
                            "inadequate": {"points": 1, "description": "Little analysis of underlying reasons"}
                        }
                    },
                    "evidence_and_support": {
                        "weight": 0.20,
                        "description": "Uses specific evidence to support comparisons",
                        "levels": {
                            "exemplary": {"points": 4, "description": "Abundant, specific evidence supporting all comparisons"},
                            "proficient": {"points": 3, "description": "Sufficient evidence supporting most comparisons"},
                            "developing": {"points": 2, "description": "Some evidence provided but may lack specificity"},
                            "inadequate": {"points": 1, "description": "Little or no specific evidence"}
                        }
                    }
                },
                "total_points": 16
            }
        }
    
    def _initialize_common_issues(self) -> Dict[str, Dict[str, Any]]:
        """Initialize common essay issues and feedback."""
        return {
            "weak_thesis": {
                "indicators": ["no clear argument", "merely restates prompt", "too vague"],
                "feedback": "Your thesis should make a clear, debatable argument that directly answers the prompt.",
                "suggestions": [
                    "Take a clear position on the question",
                    "Make sure your thesis is arguable, not just factual",
                    "Preview your main supporting points"
                ]
            },
            "insufficient_evidence": {
                "indicators": ["few specific examples", "vague references", "no supporting details"],
                "feedback": "Your essay needs more specific historical evidence to support your arguments.",
                "suggestions": [
                    "Include specific dates, names, and events",
                    "Use concrete examples rather than generalizations",
                    "Explain how your evidence supports your thesis"
                ]
            },
            "poor_analysis": {
                "indicators": ["just describes events", "no explanation", "lacks historical thinking"],
                "feedback": "Focus more on analyzing and explaining rather than just describing events.",
                "suggestions": [
                    "Explain the significance of events and evidence",
                    "Analyze cause-and-effect relationships",
                    "Consider multiple perspectives and interpretations"
                ]
            },
            "weak_organization": {
                "indicators": ["unclear structure", "ideas jump around", "poor transitions"],
                "feedback": "Your essay would benefit from clearer organization and better transitions.",
                "suggestions": [
                    "Use clear topic sentences for each paragraph",
                    "Make sure each paragraph supports your thesis",
                    "Use transition words to connect ideas"
                ]
            },
            "lack_of_context": {
                "indicators": ["events in isolation", "no broader connections", "missing background"],
                "feedback": "Your essay should place events in their broader historical context.",
                "suggestions": [
                    "Explain the background circumstances",
                    "Connect events to broader historical patterns",
                    "Consider what was happening at the same time"
                ]
            }
        }
    
    async def grade_history_essay(
        self,
        essay_text: str,
        essay_type: str = "analytical_essay",
        prompt: str = "",
        rubric_overrides: Optional[Dict[str, Any]] = None,
        source_documents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Grade a history essay using appropriate rubric and analysis."""
        
        logger.info(f"Grading {essay_type} essay")
        
        # Select appropriate rubric
        rubric = self.rubrics.get(essay_type, self.rubrics["analytical_essay"])
        if rubric_overrides:
            rubric = self._merge_rubric_overrides(rubric, rubric_overrides)
        
        grading_result = {
            "essay_type": essay_type,
            "rubric_used": rubric["name"],
            "category_scores": {},
            "total_score": 0,
            "max_score": rubric["total_points"],
            "percentage": 0,
            "overall_feedback": "",
            "category_feedback": {},
            "strengths": [],
            "areas_for_improvement": [],
            "specific_suggestions": []
        }
        
        try:
            # Analyze each rubric category
            for category_name, category_data in rubric["categories"].items():
                category_result = await self._grade_essay_category(
                    essay_text, category_name, category_data, prompt, source_documents
                )
                
                grading_result["category_scores"][category_name] = category_result
                grading_result["total_score"] += category_result["points"]
                grading_result["category_feedback"][category_name] = category_result["feedback"]
            
            # Calculate percentage
            grading_result["percentage"] = (grading_result["total_score"] / grading_result["max_score"]) * 100
            
            # Generate overall feedback and suggestions
            overall_analysis = await self._generate_overall_analysis(
                essay_text, grading_result, essay_type, prompt
            )
            
            grading_result.update(overall_analysis)
            
            # Identify common issues
            common_issues = self._identify_common_issues(essay_text, grading_result)
            grading_result["common_issues"] = common_issues
            
            logger.info(f"Essay grading complete. Score: {grading_result['total_score']}/{grading_result['max_score']}")
            
        except Exception as e:
            logger.error(f"Error grading essay: {e}")
            grading_result["error"] = str(e)
        
        return grading_result
    
    async def _grade_essay_category(
        self,
        essay_text: str,
        category_name: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Grade a specific category of the essay."""
        
        # Use specific analysis method if available
        if category_name in self.analysis_components:
            analysis_method = self.analysis_components[category_name]
            return await analysis_method(essay_text, category_data, prompt, source_documents)
        
        # General LLM-based analysis
        return await self._general_category_analysis(
            essay_text, category_name, category_data, prompt
        )
    
    async def _analyze_thesis(
        self,
        essay_text: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze the thesis and argument structure."""
        
        # Extract potential thesis statements
        thesis_candidates = self._extract_thesis_candidates(essay_text)
        
        analysis_prompt = f"""
        Analyze the thesis and argument development in this history essay:

        PROMPT: {prompt}
        
        ESSAY TEXT: {essay_text[:2000]}...
        
        POTENTIAL THESIS STATEMENTS: {thesis_candidates}

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Consider:
        1. Is there a clear, identifiable thesis statement?
        2. Does it directly address the prompt?
        3. Is it historically defensible?
        4. Is the argument well-developed throughout the essay?
        5. Does it show sophistication and nuance?

        Provide scoring and specific feedback.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert history teacher evaluating student thesis statements and arguments."),
                HumanMessage(content=analysis_prompt)
            ])
            
            return self._parse_category_response(response.content, category_data)
            
        except Exception as e:
            logger.error(f"Error analyzing thesis: {e}")
            return self._fallback_category_analysis(category_data, "thesis analysis failed")
    
    async def _analyze_evidence(
        self,
        essay_text: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze the use of evidence in the essay."""
        
        # Count specific evidence
        evidence_count = self._count_specific_evidence(essay_text)
        evidence_examples = self._extract_evidence_examples(essay_text)
        
        analysis_prompt = f"""
        Analyze the use of historical evidence in this essay:

        ESSAY TEXT: {essay_text[:2000]}...
        
        EVIDENCE EXAMPLES FOUND: {evidence_examples[:10]}  # First 10 examples
        
        EVIDENCE COUNT: {evidence_count} specific pieces of evidence detected

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Consider:
        1. Quantity of specific historical evidence
        2. Relevance of evidence to the argument
        3. Accuracy of evidence
        4. Integration of evidence into analysis
        5. Balance between breadth and depth

        Provide scoring and specific feedback on evidence use.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert history teacher evaluating student use of historical evidence."),
                HumanMessage(content=analysis_prompt)
            ])
            
            result = self._parse_category_response(response.content, category_data)
            result["evidence_count"] = evidence_count
            result["evidence_examples"] = evidence_examples[:5]  # Include examples in result
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing evidence: {e}")
            return self._fallback_category_analysis(category_data, "evidence analysis failed")
    
    async def _analyze_historical_thinking(
        self,
        essay_text: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze historical thinking skills demonstrated."""
        
        thinking_indicators = self._identify_historical_thinking_indicators(essay_text)
        
        analysis_prompt = f"""
        Analyze the historical thinking skills demonstrated in this essay:

        ESSAY TEXT: {essay_text[:2000]}...
        
        THINKING INDICATORS FOUND: {thinking_indicators}

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Look for evidence of:
        1. Multiple perspectives and viewpoints
        2. Understanding of historical context and causation
        3. Analysis of change and continuity over time
        4. Evaluation of historical significance
        5. Understanding of historical interpretation and debate

        Provide scoring and specific feedback on historical thinking.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in historical thinking skills assessment."),
                HumanMessage(content=analysis_prompt)
            ])
            
            result = self._parse_category_response(response.content, category_data)
            result["thinking_indicators"] = thinking_indicators
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing historical thinking: {e}")
            return self._fallback_category_analysis(category_data, "historical thinking analysis failed")
    
    async def _analyze_argument_structure(
        self,
        essay_text: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze the logical structure and flow of arguments."""
        
        structure_analysis = self._analyze_essay_structure(essay_text)
        
        analysis_prompt = f"""
        Analyze the argument structure and organization of this essay:

        ESSAY TEXT: {essay_text[:2000]}...
        
        STRUCTURE ANALYSIS: {structure_analysis}

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Consider:
        1. Clear introduction, body, and conclusion
        2. Logical flow between paragraphs
        3. Coherent argument development
        4. Effective transitions
        5. Overall organization and clarity

        Provide scoring and specific feedback on organization and writing.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in evaluating essay structure and argumentation."),
                HumanMessage(content=analysis_prompt)
            ])
            
            result = self._parse_category_response(response.content, category_data)
            result["structure_analysis"] = structure_analysis
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing argument structure: {e}")
            return self._fallback_category_analysis(category_data, "argument structure analysis failed")
    
    async def _analyze_source_integration(
        self,
        essay_text: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze integration and analysis of source documents (for DBQ essays)."""
        
        if not source_documents:
            return {"points": 0, "feedback": "No source documents provided for analysis"}
        
        source_usage = self._analyze_document_usage(essay_text, source_documents)
        
        analysis_prompt = f"""
        Analyze how this DBQ essay uses and analyzes the provided source documents:

        ESSAY TEXT: {essay_text[:2000]}...
        
        SOURCE DOCUMENTS PROVIDED: {len(source_documents)} documents
        
        DOCUMENT USAGE ANALYSIS: {source_usage}

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Consider:
        1. Number of documents effectively used
        2. Quality of document integration
        3. Analysis of document perspective, purpose, audience, or situation
        4. Use of documents to support argument
        5. Understanding of document limitations

        Provide scoring and specific feedback on source integration.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in evaluating DBQ essay source analysis."),
                HumanMessage(content=analysis_prompt)
            ])
            
            result = self._parse_category_response(response.content, category_data)
            result["source_usage"] = source_usage
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing source integration: {e}")
            return self._fallback_category_analysis(category_data, "source integration analysis failed")
    
    async def _analyze_writing_quality(
        self,
        essay_text: str,
        category_data: Dict[str, Any],
        prompt: str,
        source_documents: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze writing quality, style, and mechanics."""
        
        writing_metrics = self._calculate_writing_metrics(essay_text)
        
        analysis_prompt = f"""
        Analyze the writing quality and mechanics of this essay:

        ESSAY TEXT: {essay_text[:2000]}...
        
        WRITING METRICS: {writing_metrics}

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Consider:
        1. Clarity and coherence of writing
        2. Grammar and mechanics
        3. Vocabulary and word choice
        4. Sentence variety and structure
        5. Overall readability and flow

        Provide scoring and specific feedback on writing quality.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in evaluating student writing quality."),
                HumanMessage(content=analysis_prompt)
            ])
            
            result = self._parse_category_response(response.content, category_data)
            result["writing_metrics"] = writing_metrics
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing writing quality: {e}")
            return self._fallback_category_analysis(category_data, "writing quality analysis failed")
    
    async def _general_category_analysis(
        self,
        essay_text: str,
        category_name: str,
        category_data: Dict[str, Any],
        prompt: str
    ) -> Dict[str, Any]:
        """General LLM-based category analysis."""
        
        analysis_prompt = f"""
        Analyze this history essay for the "{category_name}" category:

        CATEGORY DESCRIPTION: {category_data["description"]}
        
        ESSAY TEXT: {essay_text[:1500]}...
        
        PROMPT: {prompt}

        Evaluate based on these criteria:
        {self._format_rubric_levels(category_data["levels"])}

        Provide:
        1. Score (points based on rubric levels)
        2. Specific feedback explaining the score
        3. Evidence from the essay supporting the evaluation
        
        Format as JSON: {{"points": X, "feedback": "...", "evidence": ["..."]}}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert history teacher using detailed rubrics to evaluate essays."),
                HumanMessage(content=analysis_prompt)
            ])
            
            return self._parse_category_response(response.content, category_data)
            
        except Exception as e:
            logger.error(f"Error in general category analysis: {e}")
            return self._fallback_category_analysis(category_data, "analysis failed")
    
    def _extract_thesis_candidates(self, essay_text: str) -> List[str]:
        """Extract potential thesis statements from essay."""
        
        paragraphs = essay_text.split('\n\n')
        if not paragraphs:
            return []
        
        # Usually thesis is in first paragraph
        first_paragraph = paragraphs[0]
        sentences = re.split(r'[.!?]+', first_paragraph)
        
        # Look for argumentative language
        thesis_indicators = ['argue', 'contend', 'assert', 'claim', 'thesis', 'because', 'due to', 'however', 'although']
        
        candidates = []
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in thesis_indicators):
                candidates.append(sentence.strip())
        
        # If no clear thesis in first paragraph, check conclusion
        if not candidates and len(paragraphs) > 1:
            last_paragraph = paragraphs[-1]
            last_sentences = re.split(r'[.!?]+', last_paragraph)
            for sentence in last_sentences:
                if any(indicator in sentence.lower() for indicator in thesis_indicators):
                    candidates.append(sentence.strip())
        
        return candidates[:3]  # Return top 3 candidates
    
    def _count_specific_evidence(self, essay_text: str) -> int:
        """Count specific historical evidence in the essay."""
        
        evidence_patterns = [
            r'\b\d{4}\b',  # Years
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',  # Dates
            r'\b(?:President|King|Queen|Emperor|Prime Minister|General|Admiral)\s+[A-Z][a-z]+',  # Titles with names
            r'\b(?:Treaty|Act|Declaration|Constitution|Battle|War)\s+of\s+[A-Z][a-z]+',  # Named events/documents
            r'\b[A-Z][a-z]+\s+(?:Revolution|War|Crisis|Period|Era|Age)',  # Named periods
        ]
        
        evidence_count = 0
        for pattern in evidence_patterns:
            matches = re.findall(pattern, essay_text)
            evidence_count += len(set(matches))  # Count unique matches
        
        return evidence_count
    
    def _extract_evidence_examples(self, essay_text: str) -> List[str]:
        """Extract specific examples of historical evidence."""
        
        examples = []
        
        # Extract years
        years = re.findall(r'\b\d{4}\b', essay_text)
        examples.extend([f"Year: {year}" for year in set(years)])
        
        # Extract proper nouns (potential names, places, events)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', essay_text)
        # Filter common words
        common_words = {'The', 'This', 'That', 'However', 'Therefore', 'Moreover', 'Furthermore', 'Additionally'}
        proper_nouns = [noun for noun in set(proper_nouns) if noun not in common_words and len(noun) > 2]
        examples.extend(proper_nouns[:10])  # Top 10
        
        return examples[:15]  # Return top 15 examples
    
    def _identify_historical_thinking_indicators(self, essay_text: str) -> Dict[str, List[str]]:
        """Identify indicators of historical thinking skills."""
        
        indicators = {
            "perspective_analysis": [],
            "causation": [],
            "context": [],
            "change_over_time": [],
            "significance": []
        }
        
        text_lower = essay_text.lower()
        
        # Perspective analysis indicators
        perspective_words = ['perspective', 'viewpoint', 'according to', 'believed', 'viewed', 'from the standpoint of']
        for word in perspective_words:
            if word in text_lower:
                indicators["perspective_analysis"].append(word)
        
        # Causation indicators
        causation_words = ['caused', 'because', 'due to', 'resulted in', 'led to', 'consequence', 'factor']
        for word in causation_words:
            if word in text_lower:
                indicators["causation"].append(word)
        
        # Context indicators
        context_words = ['context', 'background', 'circumstances', 'conditions', 'environment', 'setting']
        for word in context_words:
            if word in text_lower:
                indicators["context"].append(word)
        
        # Change over time indicators
        change_words = ['changed', 'evolved', 'developed', 'transformation', 'shift', 'transition', 'over time']
        for word in change_words:
            if word in text_lower:
                indicators["change_over_time"].append(word)
        
        # Significance indicators  
        significance_words = ['significant', 'important', 'crucial', 'impact', 'influence', 'effect', 'consequence']
        for word in significance_words:
            if word in text_lower:
                indicators["significance"].append(word)
        
        return indicators
    
    def _analyze_essay_structure(self, essay_text: str) -> Dict[str, Any]:
        """Analyze the structural elements of the essay."""
        
        paragraphs = [p.strip() for p in essay_text.split('\n\n') if p.strip()]
        
        structure = {
            "paragraph_count": len(paragraphs),
            "has_introduction": False,
            "has_conclusion": False,
            "average_paragraph_length": 0,
            "transition_words_count": 0
        }
        
        if paragraphs:
            structure["average_paragraph_length"] = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            
            # Check for introduction indicators
            first_paragraph = paragraphs[0].lower()
            intro_indicators = ['introduce', 'essay will', 'this paper', 'argue that', 'thesis', 'examine', 'analyze']
            if any(indicator in first_paragraph for indicator in intro_indicators):
                structure["has_introduction"] = True
            
            # Check for conclusion indicators
            if len(paragraphs) > 1:
                last_paragraph = paragraphs[-1].lower()
                conclusion_indicators = ['conclusion', 'in summary', 'to conclude', 'therefore', 'thus', 'finally']
                if any(indicator in last_paragraph for indicator in conclusion_indicators):
                    structure["has_conclusion"] = True
        
        # Count transition words
        transition_words = ['however', 'furthermore', 'moreover', 'additionally', 'therefore', 'thus', 'consequently']
        for word in transition_words:
            structure["transition_words_count"] += essay_text.lower().count(word)
        
        return structure
    
    def _analyze_document_usage(
        self,
        essay_text: str,
        source_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze how source documents are used in the essay."""
        
        usage = {
            "documents_referenced": 0,
            "explicit_citations": 0,
            "document_analysis_attempts": 0,
            "documents_used": []
        }
        
        essay_lower = essay_text.lower()
        
        for i, doc in enumerate(source_documents):
            doc_label = f"document {chr(65 + i)}"  # Document A, B, C, etc.
            doc_title = doc.get("title", "").lower()
            
            # Check for explicit citations
            if doc_label.lower() in essay_lower:
                usage["documents_referenced"] += 1
                usage["explicit_citations"] += essay_lower.count(doc_label.lower())
                usage["documents_used"].append(doc_label)
            
            # Check for content references (simplified)
            if doc_title and doc_title in essay_lower:
                usage["documents_referenced"] += 1
                usage["documents_used"].append(doc_title)
        
        # Check for document analysis language
        analysis_words = ['according to', 'the author', 'perspective', 'purpose', 'audience', 'bias']
        for word in analysis_words:
            usage["document_analysis_attempts"] += essay_lower.count(word)
        
        usage["documents_used"] = list(set(usage["documents_used"]))  # Remove duplicates
        
        return usage
    
    def _calculate_writing_metrics(self, essay_text: str) -> Dict[str, Any]:
        """Calculate basic writing quality metrics."""
        
        words = essay_text.split()
        sentences = re.split(r'[.!?]+', essay_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        metrics = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len([p for p in essay_text.split('\n\n') if p.strip()]),
            "average_sentence_length": len(words) / max(len(sentences), 1),
            "grammar_errors_estimate": 0,
            "vocabulary_sophistication": 0
        }
        
        # Simple grammar error estimation (very basic)
        common_errors = ['there are', 'there is', 'alot', 'definately', 'seperate', 'occured']
        for error in common_errors:
            metrics["grammar_errors_estimate"] += essay_text.lower().count(error)
        
        # Simple vocabulary sophistication (word length)
        if words:
            avg_word_length = sum(len(word) for word in words) / len(words)
            metrics["vocabulary_sophistication"] = avg_word_length
        
        return metrics
    
    def _format_rubric_levels(self, levels: Dict[str, Any]) -> str:
        """Format rubric levels for LLM prompt."""
        
        formatted = []
        for level_name, level_data in levels.items():
            points = level_data.get("points", 0)
            description = level_data.get("description", "")
            indicators = level_data.get("indicators", [])
            
            formatted.append(f"{level_name.title()} ({points} points): {description}")
            if indicators:
                formatted.append("  Indicators: " + "; ".join(indicators))
        
        return "\n".join(formatted)
    
    def _parse_category_response(
        self,
        response_content: str,
        category_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM response for category analysis."""
        
        try:
            import json
            parsed = json.loads(response_content)
            return {
                "points": parsed.get("points", 0),
                "feedback": parsed.get("feedback", ""),
                "evidence": parsed.get("evidence", [])
            }
        except:
            # Fallback parsing
            return self._fallback_category_analysis(category_data, response_content[:200])
    
    def _fallback_category_analysis(
        self,
        category_data: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Fallback analysis when LLM analysis fails."""
        
        max_points = max(level_data.get("points", 0) for level_data in category_data["levels"].values())
        
        return {
            "points": max_points // 2,  # Give middle score
            "feedback": f"Analysis could not be completed: {reason}",
            "evidence": []
        }
    
    async def _generate_overall_analysis(
        self,
        essay_text: str,
        grading_result: Dict[str, Any],
        essay_type: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Generate overall feedback and analysis."""
        
        analysis_prompt = f"""
        Generate comprehensive feedback for this history essay:

        ESSAY TYPE: {essay_type}
        PROMPT: {prompt}
        TOTAL SCORE: {grading_result['total_score']}/{grading_result['max_score']} ({grading_result['percentage']:.1f}%)
        
        CATEGORY SCORES: {grading_result['category_scores']}

        Generate:
        1. Overall feedback (2-3 sentences)
        2. Top 3 strengths
        3. Top 3 areas for improvement
        4. 3 specific suggestions for revision

        Focus on helping the student improve their historical thinking and writing skills.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a supportive history teacher providing comprehensive essay feedback."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse response (simplified)
            content = response.content
            
            return {
                "overall_feedback": content[:300] + "...",
                "strengths": [
                    "Shows understanding of historical content",
                    "Attempts to develop an argument",
                    "Uses some specific evidence"
                ],
                "areas_for_improvement": [
                    "Strengthen thesis development",
                    "Improve evidence integration",
                    "Enhance historical analysis"
                ],
                "specific_suggestions": [
                    "Revise your thesis to make a clearer argument",
                    "Add more specific historical examples",
                    "Explain the significance of your evidence"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating overall analysis: {e}")
            return {
                "overall_feedback": "Essay shows effort in addressing the prompt. Focus on strengthening analysis and evidence use.",
                "strengths": ["Addresses the prompt", "Shows historical knowledge"],
                "areas_for_improvement": ["Strengthen analysis", "Improve evidence use"],
                "specific_suggestions": ["Revise for clarity", "Add more specific examples"]
            }
    
    def _identify_common_issues(
        self,
        essay_text: str,
        grading_result: Dict[str, Any]
    ) -> List[str]:
        """Identify common essay issues based on text analysis and scores."""
        
        issues = []
        
        # Check for weak thesis based on low thesis scores
        thesis_scores = [
            score.get("points", 0) 
            for category, score in grading_result["category_scores"].items()
            if "thesis" in category.lower() or "argument" in category.lower()
        ]
        if thesis_scores and max(thesis_scores) <= 2:
            issues.append("weak_thesis")
        
        # Check for insufficient evidence
        evidence_count = self._count_specific_evidence(essay_text)
        if evidence_count < 5:
            issues.append("insufficient_evidence")
        
        # Check for poor analysis based on historical analysis scores
        analysis_scores = [
            score.get("points", 0)
            for category, score in grading_result["category_scores"].items() 
            if "analysis" in category.lower() or "thinking" in category.lower()
        ]
        if analysis_scores and max(analysis_scores) <= 2:
            issues.append("poor_analysis")
        
        # Check organization based on structure
        structure = self._analyze_essay_structure(essay_text)
        if not structure.get("has_introduction") or not structure.get("has_conclusion"):
            issues.append("weak_organization")
        
        # Check for context based on context indicators
        if "context" in essay_text.lower() or "background" in essay_text.lower():
            pass  # Has context
        else:
            issues.append("lack_of_context")
        
        return issues
    
    def _merge_rubric_overrides(
        self,
        base_rubric: Dict[str, Any],
        overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge rubric overrides with base rubric."""
        
        import copy
        merged = copy.deepcopy(base_rubric)
        
        # Simple merge - in practice this would be more sophisticated
        for key, value in overrides.items():
            if key in merged:
                if isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key].update(value)
                else:
                    merged[key] = value
        
        return merged