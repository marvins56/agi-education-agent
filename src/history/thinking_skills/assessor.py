"""Historical thinking skills assessment system."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
from collections import defaultdict

from langchain_core.messages import SystemMessage, HumanMessage

from src.history.schemas import (
    HistoricalThinkingSkill, ThinkingSkillAssessment, 
    HistoricalEvent, PrimarySource, HistoricalPeriod
)
from src.llm.factory import LLMFactory
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class HistoricalThinkingSkillsAssessor:
    """Assesses and tracks development of historical thinking skills."""
    
    def __init__(
        self,
        memory_manager: MemoryManager
    ):
        self.memory = memory_manager
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Skill progression frameworks
        self.skill_progressions = self._initialize_skill_progressions()
        
        # Assessment rubrics for each skill
        self.assessment_rubrics = self._initialize_assessment_rubrics()
        
        # Skill development activities
        self.skill_activities = self._initialize_skill_activities()
        
        # Performance indicators for each skill level
        self.performance_indicators = self._initialize_performance_indicators()
    
    def _initialize_skill_progressions(self) -> Dict[HistoricalThinkingSkill, Dict[int, Dict[str, Any]]]:
        """Initialize progression frameworks for each historical thinking skill."""
        return {
            HistoricalThinkingSkill.CHRONOLOGICAL_REASONING: {
                1: {  # Inadequate
                    "description": "Shows little understanding of chronology",
                    "indicators": [
                        "Cannot place events in correct chronological order",
                        "Confused about time periods and sequences",
                        "Limited understanding of cause-effect relationships over time"
                    ],
                    "common_errors": ["Anachronistic thinking", "Confusion about historical sequence"]
                },
                2: {  # Developing
                    "description": "Basic understanding of chronological sequence",
                    "indicators": [
                        "Can place major events in chronological order",
                        "Understands basic before/after relationships",
                        "Beginning to identify patterns over time"
                    ],
                    "common_errors": ["Imprecise dating", "Limited understanding of periodization"]
                },
                3: {  # Proficient
                    "description": "Good understanding of chronological patterns",
                    "indicators": [
                        "Accurately sequences events and explains relationships",
                        "Identifies changes and continuities over time",
                        "Uses periodization effectively"
                    ],
                    "strengths": ["Clear timeline construction", "Understanding of historical periods"]
                },
                4: {  # Advanced
                    "description": "Sophisticated chronological analysis",
                    "indicators": [
                        "Analyzes complex patterns of change over time",
                        "Evaluates different periodization schemes",
                        "Synthesizes multiple chronological frameworks"
                    ],
                    "strengths": ["Complex temporal analysis", "Critical evaluation of periodization"]
                }
            },
            
            HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION: {
                1: {  # Inadequate
                    "description": "Minimal understanding of historical context",
                    "indicators": [
                        "Cannot place events in broader historical context",
                        "Limited ability to make historical comparisons",
                        "Shows presentism in historical analysis"
                    ],
                    "common_errors": ["Anachronistic judgments", "Isolated event analysis"]
                },
                2: {  # Developing
                    "description": "Basic contextualization skills",
                    "indicators": [
                        "Can identify some historical context",
                        "Makes simple comparisons between events/periods",
                        "Beginning to avoid presentist assumptions"
                    ],
                    "common_errors": ["Surface-level comparisons", "Limited context awareness"]
                },
                3: {  # Proficient
                    "description": "Effective contextualization and comparison",
                    "indicators": [
                        "Places events in rich historical context",
                        "Makes meaningful comparisons across time/place",
                        "Understands historical actors' perspectives"
                    ],
                    "strengths": ["Rich contextual analysis", "Effective historical comparisons"]
                },
                4: {  # Advanced
                    "description": "Sophisticated contextualization",
                    "indicators": [
                        "Analyzes multiple layers of historical context",
                        "Makes complex, nuanced comparisons",
                        "Evaluates different contextual frameworks"
                    ],
                    "strengths": ["Multi-dimensional context analysis", "Complex comparative thinking"]
                }
            },
            
            HistoricalThinkingSkill.CRAFTING_ARGUMENTS: {
                1: {  # Inadequate
                    "description": "Weak argument construction",
                    "indicators": [
                        "No clear thesis or argument",
                        "Little or no evidence to support claims",
                        "Cannot address counterarguments"
                    ],
                    "common_errors": ["Unsupported assertions", "Circular reasoning"]
                },
                2: {  # Developing
                    "description": "Basic argument skills",
                    "indicators": [
                        "Attempts to make an argument with some evidence",
                        "Basic use of historical evidence",
                        "Limited consideration of alternative views"
                    ],
                    "common_errors": ["Weak evidence selection", "One-sided arguments"]
                },
                3: {  # Proficient
                    "description": "Clear, evidence-based arguments",
                    "indicators": [
                        "Develops clear arguments with relevant evidence",
                        "Uses historical evidence effectively",
                        "Acknowledges alternative perspectives"
                    ],
                    "strengths": ["Clear argumentation", "Effective evidence use"]
                },
                4: {  # Advanced
                    "description": "Sophisticated historical argumentation",
                    "indicators": [
                        "Constructs complex, nuanced arguments",
                        "Uses diverse evidence strategically",
                        "Addresses counterarguments effectively"
                    ],
                    "strengths": ["Nuanced argumentation", "Strategic evidence deployment"]
                }
            },
            
            HistoricalThinkingSkill.HISTORICAL_INTERPRETATION: {
                1: {  # Inadequate
                    "description": "Single perspective understanding",
                    "indicators": [
                        "Accepts historical accounts uncritically",
                        "Cannot identify different interpretations",
                        "Limited understanding of historical perspective"
                    ],
                    "common_errors": ["Historical absolutism", "Ignoring multiple perspectives"]
                },
                2: {  # Developing
                    "description": "Awareness of multiple perspectives",
                    "indicators": [
                        "Recognizes that history can be interpreted differently",
                        "Beginning to identify bias and perspective",
                        "Can compare different accounts"
                    ],
                    "common_errors": ["Simplistic perspective analysis", "Limited interpretation skills"]
                },
                3: {  # Proficient
                    "description": "Critical evaluation of interpretations",
                    "indicators": [
                        "Analyzes different historical interpretations",
                        "Evaluates evidence for different viewpoints",
                        "Understands how perspective shapes interpretation"
                    ],
                    "strengths": ["Critical interpretation analysis", "Perspective awareness"]
                },
                4: {  # Advanced
                    "description": "Sophisticated interpretation analysis",
                    "indicators": [
                        "Evaluates historiographical debates",
                        "Synthesizes multiple interpretations",
                        "Creates original interpretive frameworks"
                    ],
                    "strengths": ["Historiographical analysis", "Original interpretation"]
                }
            },
            
            HistoricalThinkingSkill.SOURCE_ANALYSIS: {
                1: {  # Inadequate
                    "description": "Uncritical source use",
                    "indicators": [
                        "Takes sources at face value",
                        "Cannot identify source type or purpose",
                        "No understanding of source limitations"
                    ],
                    "common_errors": ["Source credulity", "Ignoring source context"]
                },
                2: {  # Developing
                    "description": "Basic source evaluation",
                    "indicators": [
                        "Can identify basic source information (author, date)",
                        "Beginning to question source reliability",
                        "Understands primary vs. secondary sources"
                    ],
                    "common_errors": ["Superficial source analysis", "Limited evaluation criteria"]
                },
                3: {  # Proficient
                    "description": "Effective source analysis",
                    "indicators": [
                        "Analyzes sources for purpose, audience, bias",
                        "Evaluates source reliability and limitations",
                        "Uses multiple sources effectively"
                    ],
                    "strengths": ["Systematic source analysis", "Critical evaluation"]
                },
                4: {  # Advanced
                    "description": "Sophisticated source criticism",
                    "indicators": [
                        "Conducts complex source analysis and criticism",
                        "Evaluates source collections strategically",
                        "Identifies gaps and silences in source base"
                    ],
                    "strengths": ["Advanced source criticism", "Strategic source evaluation"]
                }
            },
            
            HistoricalThinkingSkill.CAUSATION: {
                1: {  # Inadequate
                    "description": "Simplistic cause-effect understanding",
                    "indicators": [
                        "Identifies single causes only",
                        "Cannot distinguish types of causes",
                        "Limited understanding of complex causation"
                    ],
                    "common_errors": ["Monocausal explanations", "Confusion about causation types"]
                },
                2: {  # Developing
                    "description": "Multiple cause awareness",
                    "indicators": [
                        "Recognizes multiple causes exist",
                        "Can identify immediate vs. long-term causes",
                        "Beginning to analyze cause interactions"
                    ],
                    "common_errors": ["Limited causation analysis", "Weak cause prioritization"]
                },
                3: {  # Proficient
                    "description": "Complex causation analysis",
                    "indicators": [
                        "Analyzes multiple, interacting causes",
                        "Distinguishes different types of causation",
                        "Evaluates relative importance of causes"
                    ],
                    "strengths": ["Multi-causal analysis", "Cause evaluation"]
                },
                4: {  # Advanced
                    "description": "Sophisticated causal reasoning",
                    "indicators": [
                        "Analyzes complex causal networks",
                        "Evaluates competing causal explanations",
                        "Understands contingency and historical alternatives"
                    ],
                    "strengths": ["Complex causal networks", "Contingency analysis"]
                }
            },
            
            HistoricalThinkingSkill.PATTERNS_OF_CONTINUITY: {
                1: {  # Inadequate
                    "description": "Limited pattern recognition",
                    "indicators": [
                        "Cannot identify historical patterns",
                        "Sees only change or only continuity",
                        "Limited understanding of historical development"
                    ],
                    "common_errors": ["Pattern blindness", "Change/continuity confusion"]
                },
                2: {  # Developing
                    "description": "Basic pattern identification",
                    "indicators": [
                        "Can identify some patterns of change/continuity",
                        "Beginning to understand historical development",
                        "Recognizes both change and continuity exist"
                    ],
                    "common_errors": ["Simplistic pattern analysis", "Limited synthesis"]
                },
                3: {  # Proficient
                    "description": "Effective pattern analysis",
                    "indicators": [
                        "Analyzes patterns of change and continuity",
                        "Evaluates significance of historical patterns",
                        "Synthesizes change/continuity analysis"
                    ],
                    "strengths": ["Change/continuity analysis", "Pattern evaluation"]
                },
                4: {  # Advanced
                    "description": "Sophisticated pattern synthesis",
                    "indicators": [
                        "Analyzes complex patterns across multiple contexts",
                        "Evaluates competing pattern interpretations",
                        "Creates original pattern frameworks"
                    ],
                    "strengths": ["Complex pattern analysis", "Original frameworks"]
                }
            }
        }
    
    def _initialize_assessment_rubrics(self) -> Dict[HistoricalThinkingSkill, Dict[str, Any]]:
        """Initialize detailed rubrics for assessing each skill."""
        return {
            skill: {
                "criteria": [
                    "Understanding of skill concept",
                    "Application in historical analysis", 
                    "Quality of reasoning",
                    "Use of evidence",
                    "Sophistication of thinking"
                ],
                "evidence_types": [
                    "Written responses",
                    "Discussion participation",
                    "Document analysis",
                    "Essay construction",
                    "Question formulation"
                ],
                "assessment_methods": [
                    "Performance task",
                    "Portfolio review",
                    "Observation",
                    "Self-reflection",
                    "Peer assessment"
                ]
            }
            for skill in HistoricalThinkingSkill
        }
    
    def _initialize_skill_activities(self) -> Dict[HistoricalThinkingSkill, List[Dict[str, Any]]]:
        """Initialize activities for developing each skill."""
        return {
            HistoricalThinkingSkill.CHRONOLOGICAL_REASONING: [
                {
                    "name": "Timeline Construction",
                    "description": "Create detailed timelines showing cause-effect relationships",
                    "level": "beginner",
                    "materials_needed": ["historical events list", "timeline template"]
                },
                {
                    "name": "Periodization Analysis",
                    "description": "Compare different ways historians periodize the same era",
                    "level": "intermediate",
                    "materials_needed": ["multiple periodization schemes", "comparison chart"]
                },
                {
                    "name": "Change Over Time Essay",
                    "description": "Analyze changes and continuities in a theme over time",
                    "level": "advanced",
                    "materials_needed": ["primary sources", "essay rubric"]
                }
            ],
            
            HistoricalThinkingSkill.COMPARISON_CONTEXTUALIZATION: [
                {
                    "name": "Context Web",
                    "description": "Create visual web showing multiple contexts affecting an event",
                    "level": "beginner",
                    "materials_needed": ["event description", "context categories"]
                },
                {
                    "name": "Comparative Case Studies",
                    "description": "Compare similar events in different historical contexts",
                    "level": "intermediate",
                    "materials_needed": ["case study materials", "comparison framework"]
                },
                {
                    "name": "Multiple Context Analysis",
                    "description": "Analyze how different contexts shape interpretation of same event",
                    "level": "advanced",
                    "materials_needed": ["diverse source materials", "analysis template"]
                }
            ],
            
            HistoricalThinkingSkill.CRAFTING_ARGUMENTS: [
                {
                    "name": "Claim-Evidence-Reasoning",
                    "description": "Practice basic argument structure with historical content",
                    "level": "beginner",
                    "materials_needed": ["argument template", "evidence bank"]
                },
                {
                    "name": "Counterargument Address",
                    "description": "Develop arguments while addressing opposing views",
                    "level": "intermediate",
                    "materials_needed": ["debate topics", "evidence sources"]
                },
                {
                    "name": "Historiographical Argument",
                    "description": "Take position in historical debate using evidence",
                    "level": "advanced",
                    "materials_needed": ["historiographical sources", "argument rubric"]
                }
            ],
            
            HistoricalThinkingSkill.HISTORICAL_INTERPRETATION: [
                {
                    "name": "Multiple Perspectives",
                    "description": "Examine same event from different viewpoints",
                    "level": "beginner",
                    "materials_needed": ["perspective cards", "source materials"]
                },
                {
                    "name": "Interpretation Comparison",
                    "description": "Compare how different historians interpret same evidence",
                    "level": "intermediate",
                    "materials_needed": ["historian excerpts", "comparison chart"]
                },
                {
                    "name": "Historiographical Analysis",
                    "description": "Analyze how historical interpretation has changed over time",
                    "level": "advanced",
                    "materials_needed": ["historiographical timeline", "interpretation examples"]
                }
            ],
            
            HistoricalThinkingSkill.SOURCE_ANALYSIS: [
                {
                    "name": "SOAPS Analysis",
                    "description": "Analyze sources using Speaker, Occasion, Audience, Purpose, Subject framework",
                    "level": "beginner",
                    "materials_needed": ["primary sources", "SOAPS template"]
                },
                {
                    "name": "Source Reliability Assessment",
                    "description": "Evaluate reliability of sources using multiple criteria",
                    "level": "intermediate",
                    "materials_needed": ["diverse sources", "reliability rubric"]
                },
                {
                    "name": "Source Set Analysis",
                    "description": "Analyze collection of sources to construct historical understanding",
                    "level": "advanced",
                    "materials_needed": ["curated source set", "analysis framework"]
                }
            ],
            
            HistoricalThinkingSkill.CAUSATION: [
                {
                    "name": "Cause Categorization",
                    "description": "Sort causes into immediate, underlying, and contributing categories",
                    "level": "beginner",
                    "materials_needed": ["cause cards", "category chart"]
                },
                {
                    "name": "Causal Chain Construction",
                    "description": "Build causal chains showing how events connect",
                    "level": "intermediate",
                    "materials_needed": ["event cards", "chain template"]
                },
                {
                    "name": "Causal Network Analysis",
                    "description": "Analyze complex networks of interacting causes",
                    "level": "advanced",
                    "materials_needed": ["network diagram", "causation analysis tools"]
                }
            ],
            
            HistoricalThinkingSkill.PATTERNS_OF_CONTINUITY: [
                {
                    "name": "Change/Continuity Chart",
                    "description": "Identify what changed and what stayed the same over time",
                    "level": "beginner",
                    "materials_needed": ["before/after materials", "comparison chart"]
                },
                {
                    "name": "Pattern Identification",
                    "description": "Identify recurring patterns across different historical periods",
                    "level": "intermediate",
                    "materials_needed": ["pattern examples", "analysis template"]
                },
                {
                    "name": "Turning Point Analysis",
                    "description": "Evaluate whether events represent turning points or continuity",
                    "level": "advanced",
                    "materials_needed": ["event analysis", "turning point criteria"]
                }
            ]
        }
    
    def _initialize_performance_indicators(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize performance indicators for different levels."""
        return {
            "language_indicators": {
                "inadequate": [
                    "Vague, imprecise language",
                    "Simple sentence structure",
                    "Limited historical vocabulary",
                    "Absolute statements without qualification"
                ],
                "developing": [
                    "Some historical terminology",
                    "Basic analytical language",
                    "Beginning to qualify statements",
                    "Simple comparisons"
                ],
                "proficient": [
                    "Appropriate historical terminology",
                    "Clear analytical language",
                    "Qualified statements and nuance",
                    "Effective comparisons and connections"
                ],
                "advanced": [
                    "Sophisticated historical vocabulary",
                    "Complex analytical language",
                    "Nuanced, qualified analysis",
                    "Complex synthesis and evaluation"
                ]
            },
            "reasoning_indicators": {
                "inadequate": [
                    "Illogical connections",
                    "Circular reasoning",
                    "Unsupported conclusions",
                    "Ignores contradictory evidence"
                ],
                "developing": [
                    "Some logical connections",
                    "Basic cause-effect reasoning",
                    "Conclusions with minimal support",
                    "Limited consideration of complexity"
                ],
                "proficient": [
                    "Clear logical progression",
                    "Sound cause-effect analysis",
                    "Well-supported conclusions",
                    "Acknowledges complexity"
                ],
                "advanced": [
                    "Sophisticated logical analysis",
                    "Complex causal reasoning",
                    "Nuanced, well-supported conclusions",
                    "Embraces and analyzes complexity"
                ]
            }
        }
    
    async def assess_student_skill(
        self,
        student_id: str,
        skill: HistoricalThinkingSkill,
        evidence: Dict[str, Any],
        assessment_context: Optional[Dict[str, Any]] = None
    ) -> ThinkingSkillAssessment:
        """Assess a student's proficiency in a specific historical thinking skill."""
        
        logger.info(f"Assessing {skill.value} for student {student_id}")
        
        try:
            # Get student's historical performance in this skill
            previous_assessments = await self._get_previous_assessments(student_id, skill)
            
            # Analyze the provided evidence
            skill_analysis = await self._analyze_skill_evidence(
                skill, evidence, assessment_context or {}
            )
            
            # Determine proficiency level
            proficiency_level = self._determine_proficiency_level(
                skill, skill_analysis, previous_assessments
            )
            
            # Generate specific feedback
            feedback = await self._generate_skill_feedback(
                skill, proficiency_level, skill_analysis, evidence
            )
            
            # Create assessment record
            assessment = ThinkingSkillAssessment(
                assessment_id=str(uuid.uuid4()),
                student_id=student_id,
                skill=skill,
                task_description=evidence.get("task_description", "Historical thinking skill assessment"),
                student_response=evidence.get("student_response", ""),
                proficiency_level=proficiency_level,
                specific_scores=skill_analysis.get("specific_scores", {}),
                strengths=feedback.get("strengths", []),
                areas_for_improvement=feedback.get("areas_for_improvement", []),
                next_steps=feedback.get("next_steps", []),
                previous_assessments=[a.assessment_id for a in previous_assessments],
                growth_indicators=self._calculate_growth_indicators(previous_assessments, proficiency_level)
            )
            
            # Store assessment
            await self._store_assessment(assessment)
            
            logger.info(f"Assessment complete. Level: {proficiency_level}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing skill {skill.value}: {e}")
            raise
    
    async def _get_previous_assessments(
        self,
        student_id: str,
        skill: HistoricalThinkingSkill
    ) -> List[ThinkingSkillAssessment]:
        """Retrieve previous assessments for this skill."""
        
        try:
            # Get assessments from memory manager
            assessment_records = await self.memory.get_student_assessments(
                student_id=student_id,
                subject="history",
                skill_filter=skill.value
            )
            
            # Convert to ThinkingSkillAssessment objects (simplified)
            assessments = []
            for record in assessment_records[-5:]:  # Last 5 assessments
                assessment = ThinkingSkillAssessment(
                    assessment_id=record.get("assessment_id", str(uuid.uuid4())),
                    student_id=student_id,
                    skill=skill,
                    task_description=record.get("task", "Previous assessment"),
                    student_response=record.get("response", ""),
                    proficiency_level=record.get("level", 2),
                    assessed_at=datetime.fromisoformat(record.get("date", datetime.now().isoformat()))
                )
                assessments.append(assessment)
            
            return assessments
            
        except Exception as e:
            logger.warning(f"Could not retrieve previous assessments: {e}")
            return []
    
    async def _analyze_skill_evidence(
        self,
        skill: HistoricalThinkingSkill,
        evidence: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze evidence for skill proficiency indicators."""
        
        skill_progression = self.skill_progressions[skill]
        
        analysis_prompt = f"""
        Analyze this student work for evidence of {skill.value} proficiency:

        TASK: {evidence.get('task_description', 'Historical analysis task')}
        
        STUDENT RESPONSE: {evidence.get('student_response', '')[:1000]}
        
        CONTEXT: {context.get('assignment_context', 'General historical analysis')}

        SKILL BEING ASSESSED: {skill.value}
        
        PROFICIENCY LEVELS:
        {chr(10).join([f"Level {level}: {data['description']}" for level, data in skill_progression.items()])}

        Analyze the student work for:
        1. Evidence of skill understanding and application
        2. Quality of historical reasoning
        3. Use of evidence and examples
        4. Sophistication of thinking
        5. Specific indicators of proficiency level

        Rate each criterion on 1-4 scale and provide specific evidence from student work.
        Identify the overall proficiency level with justification.
        
        Respond in JSON format with scores and evidence.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in assessing historical thinking skills with detailed rubrics."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse analysis (simplified for now)
            analysis = {
                "specific_scores": {
                    "understanding": 3,
                    "application": 2,
                    "reasoning": 3,
                    "evidence_use": 2,
                    "sophistication": 2
                },
                "evidence_found": [
                    "Student demonstrates understanding of basic concept",
                    "Application is developing but inconsistent",
                    "Some evidence of analytical thinking"
                ],
                "language_analysis": self._analyze_language_indicators(evidence.get("student_response", "")),
                "reasoning_analysis": self._analyze_reasoning_indicators(evidence.get("student_response", "")),
                "overall_indicators": response.content[:200] + "..."
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing skill evidence: {e}")
            return {"error": str(e)}
    
    def _analyze_language_indicators(self, student_response: str) -> Dict[str, Any]:
        """Analyze language indicators in student response."""
        
        response_lower = student_response.lower()
        
        # Count sophisticated vocabulary
        advanced_terms = ["however", "furthermore", "consequently", "nevertheless", "moreover"]
        advanced_count = sum(1 for term in advanced_terms if term in response_lower)
        
        # Count qualification language
        qualifying_terms = ["some", "many", "often", "generally", "tends to", "appears to"]
        qualification_count = sum(1 for term in qualifying_terms if term in response_lower)
        
        # Count analytical language
        analytical_terms = ["analyze", "evaluate", "compare", "contrast", "assess", "examine"]
        analytical_count = sum(1 for term in analytical_terms if term in response_lower)
        
        language_sophistication = (advanced_count + qualification_count + analytical_count) / max(len(student_response.split()), 1) * 100
        
        return {
            "sophistication_score": min(language_sophistication * 10, 4),  # Scale to 1-4
            "advanced_vocabulary": advanced_count,
            "qualification_language": qualification_count,
            "analytical_language": analytical_count,
            "indicators": []
        }
    
    def _analyze_reasoning_indicators(self, student_response: str) -> Dict[str, Any]:
        """Analyze reasoning indicators in student response."""
        
        response_lower = student_response.lower()
        
        # Count causal language
        causal_terms = ["because", "therefore", "as a result", "led to", "caused", "due to"]
        causal_count = sum(1 for term in causal_terms if term in response_lower)
        
        # Count evidence language
        evidence_terms = ["evidence", "shows", "demonstrates", "indicates", "suggests", "proves"]
        evidence_count = sum(1 for term in evidence_terms if term in response_lower)
        
        # Count comparison language
        comparison_terms = ["similar", "different", "like", "unlike", "whereas", "while"]
        comparison_count = sum(1 for term in comparison_terms if term in response_lower)
        
        reasoning_sophistication = (causal_count + evidence_count + comparison_count) / max(len(student_response.split()), 1) * 100
        
        return {
            "reasoning_score": min(reasoning_sophistication * 15, 4),  # Scale to 1-4
            "causal_reasoning": causal_count,
            "evidence_use": evidence_count,
            "comparative_thinking": comparison_count,
            "indicators": []
        }
    
    def _determine_proficiency_level(
        self,
        skill: HistoricalThinkingSkill,
        skill_analysis: Dict[str, Any],
        previous_assessments: List[ThinkingSkillAssessment]
    ) -> int:
        """Determine overall proficiency level based on analysis."""
        
        specific_scores = skill_analysis.get("specific_scores", {})
        
        # Calculate average of specific scores
        if specific_scores:
            average_score = sum(specific_scores.values()) / len(specific_scores)
        else:
            average_score = 2.0  # Default to developing
        
        # Consider language and reasoning analysis
        language_score = skill_analysis.get("language_analysis", {}).get("sophistication_score", 2)
        reasoning_score = skill_analysis.get("reasoning_analysis", {}).get("reasoning_score", 2)
        
        # Weight the components
        weighted_score = (average_score * 0.6) + (language_score * 0.2) + (reasoning_score * 0.2)
        
        # Consider growth trend from previous assessments
        if previous_assessments:
            recent_levels = [a.proficiency_level for a in previous_assessments[-3:]]
            if len(recent_levels) >= 2:
                trend = sum(recent_levels[-2:]) / 2  # Average of last 2 assessments
                weighted_score = (weighted_score * 0.7) + (trend * 0.3)  # Blend with trend
        
        # Round to nearest integer and constrain to 1-4 range
        proficiency_level = max(1, min(4, round(weighted_score)))
        
        return proficiency_level
    
    async def _generate_skill_feedback(
        self,
        skill: HistoricalThinkingSkill,
        proficiency_level: int,
        skill_analysis: Dict[str, Any],
        evidence: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Generate specific feedback for the skill assessment."""
        
        skill_progression = self.skill_progressions[skill][proficiency_level]
        
        feedback_prompt = f"""
        Generate constructive feedback for a student's {skill.value} performance:

        PROFICIENCY LEVEL: {proficiency_level} - {skill_progression['description']}
        
        STUDENT WORK ANALYSIS:
        {skill_analysis.get('evidence_found', [])}
        
        SPECIFIC SCORES:
        {skill_analysis.get('specific_scores', {})}

        SKILL PROGRESSION INDICATORS:
        Current Level: {skill_progression.get('indicators', [])}

        Generate feedback in three categories:
        1. STRENGTHS: What the student does well in this skill (2-3 specific points)
        2. AREAS FOR IMPROVEMENT: Specific aspects to work on (2-3 points)  
        3. NEXT STEPS: Concrete actions for skill development (2-3 actionable items)

        Make feedback specific, encouraging, and actionable.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a supportive History teacher providing specific skill development feedback."),
                HumanMessage(content=feedback_prompt)
            ])
            
            # Parse feedback (simplified parsing)
            feedback_text = response.content
            
            # Extract sections (this would be more sophisticated in practice)
            feedback = {
                "strengths": [
                    f"Shows understanding of {skill.value} concepts",
                    "Demonstrates analytical thinking in response"
                ],
                "areas_for_improvement": [
                    f"Could strengthen evidence use in {skill.value} analysis",
                    "Work on more sophisticated reasoning connections"
                ],
                "next_steps": [
                    f"Practice {skill.value} with scaffolded activities",
                    "Focus on strengthening analytical language use",
                    "Work with primary source materials"
                ]
            }
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return {
                "strengths": [f"Shows developing {skill.value} skills"],
                "areas_for_improvement": ["Continue practicing with guided support"],
                "next_steps": ["Engage with skill-building activities"]
            }
    
    def _calculate_growth_indicators(
        self,
        previous_assessments: List[ThinkingSkillAssessment],
        current_level: int
    ) -> Dict[str, float]:
        """Calculate growth indicators based on assessment history."""
        
        if not previous_assessments:
            return {"growth_rate": 0.0, "consistency": 0.0, "trajectory": "new"}
        
        # Calculate growth rate
        levels = [a.proficiency_level for a in previous_assessments] + [current_level]
        if len(levels) >= 2:
            growth_rate = (levels[-1] - levels[0]) / max(len(levels) - 1, 1)
        else:
            growth_rate = 0.0
        
        # Calculate consistency (how stable the performance is)
        if len(levels) >= 3:
            consistency = 1.0 - (sum(abs(levels[i] - levels[i-1]) for i in range(1, len(levels))) / (len(levels) - 1))
        else:
            consistency = 0.5  # Neutral for insufficient data
        
        # Determine trajectory
        if growth_rate > 0.2:
            trajectory = "improving"
        elif growth_rate < -0.2:
            trajectory = "declining"
        else:
            trajectory = "stable"
        
        return {
            "growth_rate": growth_rate,
            "consistency": max(0.0, min(1.0, consistency)),
            "trajectory": trajectory,
            "total_assessments": len(previous_assessments) + 1
        }
    
    async def _store_assessment(self, assessment: ThinkingSkillAssessment) -> None:
        """Store assessment in memory system."""
        
        try:
            assessment_data = {
                "assessment_id": assessment.assessment_id,
                "student_id": assessment.student_id,
                "skill": assessment.skill.value,
                "level": assessment.proficiency_level,
                "task": assessment.task_description,
                "response": assessment.student_response[:500],  # Truncate for storage
                "strengths": assessment.strengths,
                "improvements": assessment.areas_for_improvement,
                "next_steps": assessment.next_steps,
                "date": assessment.assessed_at.isoformat(),
                "growth": assessment.growth_indicators
            }
            
            await self.memory.store_assessment_data(
                student_id=assessment.student_id,
                subject="history",
                assessment_type="thinking_skills",
                assessment_data=assessment_data
            )
            
        except Exception as e:
            logger.error(f"Error storing assessment: {e}")
    
    async def generate_skill_development_plan(
        self,
        student_id: str,
        target_skills: Optional[List[HistoricalThinkingSkill]] = None,
        time_frame_weeks: int = 8
    ) -> Dict[str, Any]:
        """Generate a personalized skill development plan."""
        
        logger.info(f"Generating skill development plan for student {student_id}")
        
        # Get current skill levels
        current_levels = {}
        for skill in target_skills or list(HistoricalThinkingSkill):
            assessments = await self._get_previous_assessments(student_id, skill)
            if assessments:
                current_levels[skill] = assessments[-1].proficiency_level
            else:
                current_levels[skill] = 1  # Assume beginner if no assessments
        
        # Identify priority skills (lowest levels first)
        priority_skills = sorted(current_levels.items(), key=lambda x: x[1])
        
        # Create development sequence
        development_sequence = []
        weeks_per_skill = max(1, time_frame_weeks // len(priority_skills))
        
        for i, (skill, current_level) in enumerate(priority_skills):
            target_level = min(4, current_level + 1)  # Aim to improve by 1 level
            
            skill_plan = {
                "skill": skill,
                "current_level": current_level,
                "target_level": target_level,
                "weeks_allocated": weeks_per_skill,
                "activities": self._select_appropriate_activities(skill, current_level, target_level),
                "assessment_checkpoints": self._plan_assessment_checkpoints(weeks_per_skill),
                "success_indicators": self.skill_progressions[skill][target_level]["indicators"]
            }
            
            development_sequence.append(skill_plan)
        
        # Create overall plan
        development_plan = {
            "student_id": student_id,
            "plan_id": str(uuid.uuid4()),
            "time_frame_weeks": time_frame_weeks,
            "current_skill_profile": current_levels,
            "development_sequence": development_sequence,
            "overall_goals": self._generate_overall_goals(priority_skills),
            "progress_tracking": {
                "weekly_check_ins": True,
                "portfolio_development": True,
                "peer_collaboration": True,
                "self_reflection": True
            },
            "created_at": datetime.now()
        }
        
        return development_plan
    
    def _select_appropriate_activities(
        self,
        skill: HistoricalThinkingSkill,
        current_level: int,
        target_level: int
    ) -> List[Dict[str, Any]]:
        """Select appropriate activities for skill development."""
        
        skill_activities = self.skill_activities.get(skill, [])
        
        # Map levels to difficulty
        level_to_difficulty = {1: "beginner", 2: "beginner", 3: "intermediate", 4: "advanced"}
        current_difficulty = level_to_difficulty.get(current_level, "beginner")
        target_difficulty = level_to_difficulty.get(target_level, "intermediate")
        
        # Select activities appropriate for progression
        appropriate_activities = []
        
        for activity in skill_activities:
            activity_level = activity["level"]
            
            # Include current level activities and target level activities
            if activity_level == current_difficulty or activity_level == target_difficulty:
                appropriate_activities.append(activity)
        
        # Ensure we have at least one activity
        if not appropriate_activities and skill_activities:
            appropriate_activities = [skill_activities[0]]
        
        return appropriate_activities[:3]  # Limit to 3 activities per skill
    
    def _plan_assessment_checkpoints(self, weeks_allocated: int) -> List[Dict[str, Any]]:
        """Plan assessment checkpoints during skill development."""
        
        checkpoints = []
        
        # Formative checkpoint at midpoint
        if weeks_allocated >= 3:
            checkpoints.append({
                "week": weeks_allocated // 2,
                "type": "formative",
                "purpose": "Check progress and adjust activities",
                "methods": ["portfolio review", "self-reflection", "peer feedback"]
            })
        
        # Summative checkpoint at end
        checkpoints.append({
            "week": weeks_allocated,
            "type": "summative", 
            "purpose": "Assess skill development and set next goals",
            "methods": ["performance task", "portfolio review", "skill demonstration"]
        })
        
        return checkpoints
    
    def _generate_overall_goals(self, priority_skills: List[Tuple[HistoricalThinkingSkill, int]]) -> List[str]:
        """Generate overall learning goals for the development plan."""
        
        goals = []
        
        # General goal
        goals.append("Develop proficiency in historical thinking skills essential for historical analysis")
        
        # Specific skill goals
        for skill, current_level in priority_skills[:3]:  # Top 3 priority skills
            skill_name = skill.value.replace("_", " ").title()
            if current_level <= 2:
                goals.append(f"Build foundational skills in {skill_name}")
            else:
                goals.append(f"Advance proficiency in {skill_name}")
        
        # Integration goal
        goals.append("Integrate multiple thinking skills in complex historical analysis tasks")
        
        return goals
    
    async def create_skill_assessment_activity(
        self,
        skill: HistoricalThinkingSkill,
        student_level: str = "intermediate",
        historical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create an assessment activity for a specific skill."""
        
        skill_activities = self.skill_activities.get(skill, [])
        
        # Select appropriate activity based on student level
        level_activities = [a for a in skill_activities if a["level"] == student_level]
        if not level_activities:
            level_activities = skill_activities  # Fall back to all activities
        
        if not level_activities:
            raise ValueError(f"No activities available for skill {skill.value}")
        
        # Select activity (could be more sophisticated selection logic)
        selected_activity = level_activities[0]
        
        # Create assessment task
        assessment_activity = {
            "activity_id": str(uuid.uuid4()),
            "skill": skill,
            "activity_name": selected_activity["name"],
            "description": selected_activity["description"],
            "student_level": student_level,
            "materials_needed": selected_activity.get("materials_needed", []),
            "instructions": await self._generate_activity_instructions(skill, selected_activity, historical_context),
            "assessment_rubric": self._create_activity_rubric(skill, student_level),
            "expected_outcomes": self._define_expected_outcomes(skill, student_level),
            "time_estimate_minutes": self._estimate_activity_time(selected_activity, student_level),
            "scaffolding_options": self._generate_scaffolding_options(skill, student_level)
        }
        
        return assessment_activity
    
    async def _generate_activity_instructions(
        self,
        skill: HistoricalThinkingSkill,
        activity: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate detailed instructions for the assessment activity."""
        
        context_info = context or {}
        historical_period = context_info.get("period", "Modern Era")
        topic = context_info.get("topic", "Historical Analysis")
        
        instructions_prompt = f"""
        Generate clear, detailed instructions for this historical thinking skills activity:

        SKILL: {skill.value}
        ACTIVITY: {activity['name']} - {activity['description']}
        HISTORICAL CONTEXT: {topic} in the {historical_period}
        
        Create instructions that:
        1. Clearly explain the task
        2. Provide step-by-step guidance
        3. Include specific historical content related to {topic}
        4. Explain how the activity develops {skill.value}
        5. Give clear success criteria
        
        Make instructions clear and engaging for students.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an experienced History teacher creating student activity instructions."),
                HumanMessage(content=instructions_prompt)
            ])
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating activity instructions: {e}")
            return f"""
            {activity['name']} Activity Instructions:
            
            1. Focus on developing {skill.value} skills
            2. {activity['description']}
            3. Use the provided materials: {', '.join(activity.get('materials_needed', []))}
            4. Complete the analysis following historical thinking principles
            5. Document your reasoning and evidence
            """
    
    def _create_activity_rubric(self, skill: HistoricalThinkingSkill, student_level: str) -> Dict[str, Any]:
        """Create assessment rubric for the activity."""
        
        skill_progression = self.skill_progressions[skill]
        
        rubric = {
            "criteria": [
                "Understanding of Historical Thinking Skill",
                "Quality of Analysis",
                "Use of Evidence",
                "Communication of Ideas"
            ],
            "performance_levels": {
                "Inadequate (1)": skill_progression[1]["indicators"][:2],
                "Developing (2)": skill_progression[2]["indicators"][:2],
                "Proficient (3)": skill_progression[3]["indicators"][:2],
                "Advanced (4)": skill_progression[4]["indicators"][:2]
            },
            "scoring_guide": {
                "total_points": 16,  # 4 criteria × 4 points each
                "weighting": {
                    "Understanding of Historical Thinking Skill": 0.3,
                    "Quality of Analysis": 0.3,
                    "Use of Evidence": 0.25,
                    "Communication of Ideas": 0.15
                }
            }
        }
        
        return rubric
    
    def _define_expected_outcomes(self, skill: HistoricalThinkingSkill, student_level: str) -> List[str]:
        """Define expected learning outcomes for the activity."""
        
        level_mapping = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
        target_level = level_mapping.get(student_level, 2)
        
        skill_progression = self.skill_progressions[skill]
        target_indicators = skill_progression[min(target_level + 1, 4)]["indicators"]
        
        outcomes = [
            f"Students will demonstrate {skill.value} at the {student_level} level",
            f"Students will show evidence of: {target_indicators[0] if target_indicators else 'skill development'}",
            "Students will communicate their analysis clearly and effectively"
        ]
        
        return outcomes
    
    def _estimate_activity_time(self, activity: Dict[str, Any], student_level: str) -> int:
        """Estimate time needed for the activity."""
        
        base_times = {
            "beginner": 30,
            "intermediate": 45,
            "advanced": 60,
            "expert": 75
        }
        
        base_time = base_times.get(student_level, 45)
        
        # Adjust based on activity complexity
        activity_name = activity.get("name", "").lower()
        
        if "essay" in activity_name or "analysis" in activity_name:
            base_time += 30
        elif "construction" in activity_name or "creation" in activity_name:
            base_time += 15
        
        return base_time
    
    def _generate_scaffolding_options(self, skill: HistoricalThinkingSkill, student_level: str) -> List[Dict[str, Any]]:
        """Generate scaffolding options for different student needs."""
        
        scaffolding_options = []
        
        # Universal scaffolding
        scaffolding_options.append({
            "type": "graphic_organizer",
            "description": f"Provide {skill.value} analysis template",
            "when_to_use": "For students who need structure"
        })
        
        scaffolding_options.append({
            "type": "sentence_starters",
            "description": "Provide sentence starters for analytical writing",
            "when_to_use": "For students struggling with academic language"
        })
        
        # Skill-specific scaffolding
        if skill == HistoricalThinkingSkill.SOURCE_ANALYSIS:
            scaffolding_options.append({
                "type": "soaps_framework",
                "description": "Provide SOAPS analysis framework",
                "when_to_use": "For systematic source analysis"
            })
        
        elif skill == HistoricalThinkingSkill.CAUSATION:
            scaffolding_options.append({
                "type": "cause_categories",
                "description": "Provide cause categorization chart",
                "when_to_use": "For organizing multiple causes"
            })
        
        # Level-specific scaffolding
        if student_level in ["beginner", "developing"]:
            scaffolding_options.append({
                "type": "guided_questions",
                "description": "Provide step-by-step guiding questions",
                "when_to_use": "For students new to this skill"
            })
        
        return scaffolding_options