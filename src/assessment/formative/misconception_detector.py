"""Misconception detection and remediation system."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid
from collections import defaultdict

from langchain_core.messages import SystemMessage, HumanMessage

from src.llm.factory import LLMFactory
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class MisconceptionDetector:
    """Detects and addresses common historical misconceptions."""
    
    def __init__(
        self,
        memory_manager: MemoryManager
    ):
        self.memory = memory_manager
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Common historical misconceptions database
        self.known_misconceptions = self._initialize_known_misconceptions()
        
        # Misconception detection patterns
        self.detection_patterns = self._initialize_detection_patterns()
        
        # Remediation strategies
        self.remediation_strategies = self._initialize_remediation_strategies()
        
        # Student misconception tracking
        self.student_misconceptions = defaultdict(list)
    
    def _initialize_known_misconceptions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize database of common historical misconceptions."""
        return {
            "linear_progress": {
                "description": "History is a story of linear progress and improvement",
                "correct_understanding": "History involves complex patterns of change, continuity, progress, and regression",
                "indicators": [
                    "things always get better over time",
                    "history is a straight line of progress",
                    "people in the past were less intelligent",
                    "technology always leads to improvement"
                ],
                "topics": ["historical_development", "social_change", "technological_progress"],
                "severity": "high"
            },
            
            "presentism": {
                "description": "Judging past actions by current moral and social standards",
                "correct_understanding": "Historical actors must be understood within their own time period and context",
                "indicators": [
                    "why didn't they just do what we do now",
                    "people in the past were evil/stupid",
                    "they should have known better",
                    "using modern values to judge past actions"
                ],
                "topics": ["historical_context", "moral_reasoning", "cultural_understanding"],
                "severity": "high"
            },
            
            "great_man_theory": {
                "description": "History is shaped primarily by the actions of great individuals",
                "correct_understanding": "History results from complex interactions of individuals, groups, structures, and forces",
                "indicators": [
                    "if X person hadn't done Y, history would be completely different",
                    "wars are caused by individual leaders",
                    "one person changed everything",
                    "ignoring broader social and economic factors"
                ],
                "topics": ["causation", "historical_change", "leadership"],
                "severity": "medium"
            },
            
            "inevitable_outcomes": {
                "description": "Historical events were inevitable and bound to happen",
                "correct_understanding": "History involves contingency, and different outcomes were often possible",
                "indicators": [
                    "it was bound to happen",
                    "there was no other choice",
                    "it was destiny",
                    "inevitable result"
                ],
                "topics": ["causation", "contingency", "alternative_history"],
                "severity": "medium"
            },
            
            "monocausal_explanations": {
                "description": "Complex historical events have single causes",
                "correct_understanding": "Historical events typically result from multiple interacting causes",
                "indicators": [
                    "the cause of X was Y",
                    "it happened because of one thing",
                    "the reason for the war was...",
                    "if not for X, Y wouldn't have happened"
                ],
                "topics": ["causation", "complexity", "historical_analysis"],
                "severity": "high"
            },
            
            "false_analogies": {
                "description": "Making inappropriate comparisons between historical periods",
                "correct_understanding": "Historical comparisons must account for different contexts and circumstances",
                "indicators": [
                    "just like today",
                    "history repeats itself exactly",
                    "it's the same as when...",
                    "oversimplified historical comparisons"
                ],
                "topics": ["comparison", "contextualization", "historical_thinking"],
                "severity": "medium"
            },
            
            "victim_blaming": {
                "description": "Blaming historical victims for their circumstances",
                "correct_understanding": "Understanding power structures, constraints, and limited agency of historical actors",
                "indicators": [
                    "why didn't they just resist",
                    "they could have fought back",
                    "it's their fault for not...",
                    "they chose their situation"
                ],
                "topics": ["agency", "power_structures", "oppression", "resistance"],
                "severity": "high"
            },
            
            "golden_age_myth": {
                "description": "Belief that there was a perfect time in the past",
                "correct_understanding": "All historical periods had both positive and negative aspects",
                "indicators": [
                    "things were better back then",
                    "the good old days",
                    "perfect society in the past",
                    "romanticizing historical periods"
                ],
                "topics": ["historical_periods", "social_conditions", "change_over_time"],
                "severity": "medium"
            }
        }
    
    def _initialize_detection_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for detecting misconceptions in student responses."""
        return {
            "language_patterns": [
                "absolute statements without qualification",
                "oversimplified cause-effect claims",
                "anachronistic moral judgments",
                "inevitability language",
                "single-factor explanations"
            ],
            "reasoning_patterns": [
                "ignoring historical context",
                "applying modern standards inappropriately",
                "oversimplified causation",
                "lack of multiple perspectives",
                "deterministic thinking"
            ],
            "content_patterns": [
                "factual errors with conceptual implications",
                "misunderstanding of historical processes",
                "confusion about chronology or causation",
                "stereotypical thinking about historical groups"
            ]
        }
    
    def _initialize_remediation_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategies for addressing different misconceptions."""
        return {
            "linear_progress": {
                "strategies": [
                    "Show examples of regression and cyclical change",
                    "Examine different aspects of 'progress' (technology vs. social justice)",
                    "Analyze periods of decline or stagnation",
                    "Compare different civilizations' trajectories"
                ],
                "activities": [
                    "Timeline activity showing progress and regression",
                    "Case study comparing different measures of progress",
                    "Primary source analysis showing period concerns"
                ],
                "questions": [
                    "How might someone from this time period view 'progress'?",
                    "What are different ways to measure historical progress?",
                    "Can you think of examples where change was not improvement?"
                ]
            },
            
            "presentism": {
                "strategies": [
                    "Emphasize historical context and contemporary values",
                    "Use primary sources to show period thinking",
                    "Explain constraints and limited options of historical actors",
                    "Practice perspective-taking exercises"
                ],
                "activities": [
                    "Role-playing historical decision-making",
                    "Primary source analysis for contemporary perspectives",
                    "Context comparison activities",
                    "Values clarification exercises"
                ],
                "questions": [
                    "What values and beliefs guided people in this time period?",
                    "What constraints did historical actors face?",
                    "How might their world look different from ours?"
                ]
            },
            
            "great_man_theory": {
                "strategies": [
                    "Analyze broader social and economic factors",
                    "Examine role of ordinary people in historical change",
                    "Show how structures constrain individual action",
                    "Explore collective movements and group agency"
                ],
                "activities": [
                    "Social history case studies",
                    "Analysis of social movements",
                    "Examination of structural factors",
                    "Counter-factual analysis"
                ],
                "questions": [
                    "What other factors besides individual actions influenced this event?",
                    "How did ordinary people contribute to this change?",
                    "What would have happened if someone else had been in charge?"
                ]
            },
            
            "monocausal_explanations": {
                "strategies": [
                    "Introduce multiple causation frameworks",
                    "Practice identifying different types of causes",
                    "Show how causes interact and reinforce each other",
                    "Use graphic organizers for complex causation"
                ],
                "activities": [
                    "Cause and effect mapping",
                    "Multiple causation analysis",
                    "Fishbone diagram construction",
                    "Prioritizing and weighting causes"
                ],
                "questions": [
                    "What other factors contributed to this outcome?",
                    "How did these different causes interact?",
                    "Which causes were most/least important and why?"
                ]
            }
        }
    
    async def detect_misconceptions(
        self,
        student_id: str,
        student_response: str,
        topic_context: str,
        question_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect misconceptions in student response."""
        
        logger.info(f"Analyzing response for misconceptions - Student: {student_id}")
        
        # Comprehensive analysis using LLM
        detected_misconceptions = await self._analyze_response_for_misconceptions(
            student_response, topic_context, question_context
        )
        
        # Pattern-based detection for known misconceptions
        pattern_detections = self._detect_known_misconception_patterns(
            student_response, topic_context
        )
        
        # Combine results
        all_detections = self._combine_detection_results(
            detected_misconceptions, pattern_detections
        )
        
        # Store detections for tracking
        if all_detections:
            await self._store_misconception_data(student_id, all_detections, student_response)
        
        detection_result = {
            "student_id": student_id,
            "analysis_id": str(uuid.uuid4()),
            "misconceptions_detected": all_detections,
            "severity_level": self._assess_overall_severity(all_detections),
            "needs_immediate_intervention": self._needs_immediate_intervention(all_detections),
            "recommended_actions": await self._generate_remediation_recommendations(all_detections),
            "detected_at": datetime.now()
        }
        
        return detection_result
    
    async def _analyze_response_for_misconceptions(
        self,
        student_response: str,
        topic_context: str,
        question_context: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Use LLM to analyze response for historical misconceptions."""
        
        analysis_prompt = f"""
        Analyze this student response for historical misconceptions:

        Topic Context: {topic_context}
        Question Context: {question_context or "General historical analysis"}
        Student Response: "{student_response}"

        Look for these common historical misconceptions:
        1. Linear progress view (history as steady improvement)
        2. Presentism (judging past by current standards)
        3. Great man theory (overemphasis on individual leaders)
        4. Inevitable outcomes (events had to happen as they did)
        5. Monocausal explanations (single causes for complex events)
        6. False analogies (inappropriate historical comparisons)
        7. Victim blaming (blaming historical victims)
        8. Golden age myths (romanticizing the past)

        For each misconception detected, provide:
        - Type of misconception
        - Specific evidence from the response
        - Severity (low/medium/high)
        - Confidence in detection (0.0-1.0)

        Respond in JSON format with an array of detected misconceptions.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in historical education and common student misconceptions."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse LLM response
            import json
            try:
                detections = json.loads(response.content)
                if isinstance(detections, dict) and "misconceptions" in detections:
                    return detections["misconceptions"]
                elif isinstance(detections, list):
                    return detections
                else:
                    return []
            except json.JSONDecodeError:
                return self._fallback_misconception_analysis(student_response, topic_context)
                
        except Exception as e:
            logger.error(f"Error in LLM misconception analysis: {e}")
            return self._fallback_misconception_analysis(student_response, topic_context)
    
    def _detect_known_misconception_patterns(
        self,
        student_response: str,
        topic_context: str
    ) -> List[Dict[str, Any]]:
        """Detect patterns matching known misconceptions."""
        
        detections = []
        response_lower = student_response.lower()
        
        for misconception_id, misconception_data in self.known_misconceptions.items():
            indicators = misconception_data["indicators"]
            
            # Check if any indicators are present
            matches = []
            for indicator in indicators:
                if indicator.lower() in response_lower:
                    matches.append(indicator)
            
            if matches:
                # Calculate confidence based on number of matches
                confidence = min(len(matches) / len(indicators), 0.9)
                
                detection = {
                    "type": misconception_id,
                    "description": misconception_data["description"],
                    "evidence": matches,
                    "confidence": confidence,
                    "severity": misconception_data["severity"],
                    "detection_method": "pattern_matching"
                }
                
                detections.append(detection)
        
        return detections
    
    def _fallback_misconception_analysis(
        self,
        student_response: str,
        topic_context: str
    ) -> List[Dict[str, Any]]:
        """Fallback analysis when LLM analysis fails."""
        
        # Use pattern matching as fallback
        return self._detect_known_misconception_patterns(student_response, topic_context)
    
    def _combine_detection_results(
        self,
        llm_detections: List[Dict[str, Any]],
        pattern_detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Combine and deduplicate detection results from different methods."""
        
        combined = []
        detected_types = set()
        
        # Add LLM detections first (higher priority)
        for detection in llm_detections:
            misconception_type = detection.get("type", "unknown")
            if misconception_type not in detected_types:
                combined.append(detection)
                detected_types.add(misconception_type)
        
        # Add pattern detections that weren't already detected
        for detection in pattern_detections:
            misconception_type = detection.get("type", "unknown")
            if misconception_type not in detected_types:
                combined.append(detection)
                detected_types.add(misconception_type)
        
        return combined
    
    def _assess_overall_severity(self, detections: List[Dict[str, Any]]) -> str:
        """Assess overall severity of detected misconceptions."""
        
        if not detections:
            return "none"
        
        severity_levels = [d.get("severity", "medium") for d in detections]
        
        if "high" in severity_levels:
            return "high"
        elif "medium" in severity_levels:
            return "medium"
        else:
            return "low"
    
    def _needs_immediate_intervention(self, detections: List[Dict[str, Any]]) -> bool:
        """Determine if misconceptions require immediate intervention."""
        
        # High-severity misconceptions or multiple misconceptions need intervention
        high_severity_count = sum(1 for d in detections if d.get("severity") == "high")
        total_detections = len(detections)
        
        return high_severity_count > 0 or total_detections >= 3
    
    async def _generate_remediation_recommendations(
        self,
        detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for addressing detected misconceptions."""
        
        recommendations = []
        
        for detection in detections:
            misconception_type = detection.get("type", "unknown")
            
            if misconception_type in self.remediation_strategies:
                strategy_data = self.remediation_strategies[misconception_type]
                
                recommendation = {
                    "misconception": misconception_type,
                    "priority": detection.get("severity", "medium"),
                    "immediate_response": await self._generate_immediate_response(detection),
                    "teaching_strategies": strategy_data.get("strategies", [])[:2],  # Top 2
                    "suggested_activities": strategy_data.get("activities", [])[:2],  # Top 2
                    "guiding_questions": strategy_data.get("questions", [])[:2]  # Top 2
                }
                
                recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_immediate_response(self, detection: Dict[str, Any]) -> str:
        """Generate immediate response to address a detected misconception."""
        
        misconception_type = detection.get("type", "unknown")
        evidence = detection.get("evidence", [])
        
        response_prompt = f"""
        Generate a brief, gentle response to address this student misconception:

        Misconception Type: {misconception_type}
        Evidence: {evidence}
        
        The response should:
        - Be supportive and non-judgmental
        - Gently correct the misconception
        - Provide a clearer way of thinking about it
        - Be brief (1-2 sentences)
        - Encourage further thinking
        
        Example format: "I notice you're thinking about this in terms of... A more nuanced way to consider this might be..."
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a supportive history teacher addressing student misconceptions."),
                HumanMessage(content=response_prompt)
            ])
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating immediate response: {e}")
            
            # Fallback responses
            fallback_responses = {
                "linear_progress": "History involves complex patterns of change, not just steady progress.",
                "presentism": "Let's consider how people in that time period might have viewed this situation.",
                "great_man_theory": "Many factors beyond individual leaders shape historical events.",
                "monocausal_explanations": "Historical events usually have multiple interconnected causes."
            }
            
            return fallback_responses.get(misconception_type, 
                "That's an interesting perspective. Let's explore some additional factors that might be important here.")
    
    async def _store_misconception_data(
        self,
        student_id: str,
        detections: List[Dict[str, Any]],
        original_response: str
    ) -> None:
        """Store misconception detection data for tracking."""
        
        try:
            misconception_data = {
                "student_id": student_id,
                "detections": detections,
                "original_response": original_response[:500],  # Truncated
                "timestamp": datetime.now().isoformat(),
                "severity": self._assess_overall_severity(detections)
            }
            
            await self.memory.store_learning_event(
                student_id=student_id,
                event_type="misconception_detected",
                event_data=misconception_data,
                subject="history"
            )
            
            # Update student misconception tracking
            self.student_misconceptions[student_id].extend(detections)
            
        except Exception as e:
            logger.error(f"Error storing misconception data: {e}")
    
    async def get_student_misconception_profile(
        self,
        student_id: str,
        time_window_days: int = 30
    ) -> Dict[str, Any]:
        """Get a student's misconception profile and patterns."""
        
        try:
            # Retrieve recent misconception data
            recent_events = await self.memory.get_student_events(
                student_id=student_id,
                event_type="misconception_detected",
                days_back=time_window_days,
                subject="history"
            )
            
            # Analyze patterns
            profile = self._analyze_misconception_patterns(recent_events)
            
            profile.update({
                "student_id": student_id,
                "analysis_period_days": time_window_days,
                "total_detections": len(recent_events),
                "generated_at": datetime.now()
            })
            
            return profile
            
        except Exception as e:
            logger.error(f"Error generating misconception profile: {e}")
            return {"error": str(e)}
    
    def _analyze_misconception_patterns(
        self,
        misconception_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze patterns in student misconceptions."""
        
        if not misconception_events:
            return {
                "common_misconceptions": [],
                "frequency_analysis": {},
                "severity_distribution": {},
                "trend": "no_data",
                "persistent_issues": []
            }
        
        # Count misconception types
        misconception_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in misconception_events:
            event_data = event.get("event_data", {})
            detections = event_data.get("detections", [])
            
            for detection in detections:
                misconception_type = detection.get("type", "unknown")
                severity = detection.get("severity", "medium")
                
                misconception_counts[misconception_type] += 1
                severity_counts[severity] += 1
        
        # Identify most common misconceptions
        common_misconceptions = [
            {"type": misconception_type, "frequency": count}
            for misconception_type, count in sorted(
                misconception_counts.items(), key=lambda x: x[1], reverse=True
            )
        ][:5]  # Top 5
        
        # Identify persistent issues (appeared multiple times)
        persistent_issues = [
            misconception_type for misconception_type, count in misconception_counts.items()
            if count >= 3
        ]
        
        # Analyze trend
        if len(misconception_events) >= 5:
            recent_half = misconception_events[-len(misconception_events)//2:]
            early_half = misconception_events[:len(misconception_events)//2]
            
            recent_count = sum(len(e.get("event_data", {}).get("detections", [])) for e in recent_half)
            early_count = sum(len(e.get("event_data", {}).get("detections", [])) for e in early_half)
            
            if recent_count < early_count * 0.7:
                trend = "improving"
            elif recent_count > early_count * 1.3:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "common_misconceptions": common_misconceptions,
            "frequency_analysis": dict(misconception_counts),
            "severity_distribution": dict(severity_counts),
            "trend": trend,
            "persistent_issues": persistent_issues,
            "needs_targeted_intervention": len(persistent_issues) > 0,
            "overall_misconception_rate": len(misconception_events) / max(time_window_days, 1)
        }
    
    async def create_targeted_remediation_plan(
        self,
        student_id: str,
        misconception_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a targeted plan to address student's persistent misconceptions."""
        
        common_misconceptions = misconception_profile.get("common_misconceptions", [])
        persistent_issues = misconception_profile.get("persistent_issues", [])
        
        remediation_plan = {
            "student_id": student_id,
            "plan_id": str(uuid.uuid4()),
            "created_at": datetime.now(),
            "priority_misconceptions": [],
            "intervention_sequence": [],
            "assessment_checkpoints": [],
            "expected_duration_weeks": 0
        }
        
        # Prioritize misconceptions to address
        priority_misconceptions = []
        
        # First priority: persistent high-severity issues
        for misconception in common_misconceptions:
            misconception_type = misconception["type"]
            if (misconception_type in persistent_issues and 
                self.known_misconceptions.get(misconception_type, {}).get("severity") == "high"):
                priority_misconceptions.append({
                    "type": misconception_type,
                    "priority": "critical",
                    "frequency": misconception["frequency"]
                })
        
        # Second priority: other persistent issues
        for misconception in common_misconceptions:
            misconception_type = misconception["type"]
            if misconception_type in persistent_issues and misconception_type not in [p["type"] for p in priority_misconceptions]:
                priority_misconceptions.append({
                    "type": misconception_type,
                    "priority": "high",
                    "frequency": misconception["frequency"]
                })
        
        # Third priority: frequent but not persistent
        for misconception in common_misconceptions[:3]:  # Top 3
            misconception_type = misconception["type"]
            if misconception_type not in [p["type"] for p in priority_misconceptions]:
                priority_misconceptions.append({
                    "type": misconception_type,
                    "priority": "medium",
                    "frequency": misconception["frequency"]
                })
        
        remediation_plan["priority_misconceptions"] = priority_misconceptions
        
        # Create intervention sequence
        for i, priority_misconception in enumerate(priority_misconceptions):
            misconception_type = priority_misconception["type"]
            
            if misconception_type in self.remediation_strategies:
                strategy_data = self.remediation_strategies[misconception_type]
                
                intervention = {
                    "week": i + 1,
                    "misconception": misconception_type,
                    "priority": priority_misconception["priority"],
                    "strategies": strategy_data.get("strategies", []),
                    "activities": strategy_data.get("activities", []),
                    "assessment_questions": strategy_data.get("questions", []),
                    "success_criteria": [
                        "Student demonstrates correct understanding in discussion",
                        "Student applies correct thinking in practice activities",
                        "Student catches themselves when falling into misconception"
                    ]
                }
                
                remediation_plan["intervention_sequence"].append(intervention)
        
        remediation_plan["expected_duration_weeks"] = len(remediation_plan["intervention_sequence"])
        
        # Add assessment checkpoints
        for week in range(1, remediation_plan["expected_duration_weeks"] + 1):
            if week % 2 == 0:  # Every other week
                checkpoint = {
                    "week": week,
                    "type": "progress_check",
                    "focus": "Review misconceptions addressed so far",
                    "methods": ["discussion", "practice_activity", "reflection"]
                }
                remediation_plan["assessment_checkpoints"].append(checkpoint)
        
        return remediation_plan
    
    async def assess_misconception_remediation(
        self,
        student_id: str,
        misconception_type: str,
        assessment_response: str
    ) -> Dict[str, Any]:
        """Assess whether a misconception has been successfully addressed."""
        
        assessment_prompt = f"""
        Assess whether this student has overcome the following misconception:

        Misconception: {self.known_misconceptions.get(misconception_type, {}).get('description', 'Unknown misconception')}
        Student Response: "{assessment_response}"

        Evaluate:
        1. Does the response show the misconception is still present? (Yes/No)
        2. Level of understanding (0.0 = misconception still strong, 1.0 = fully corrected)
        3. Evidence for your assessment
        4. Any remaining traces of the misconception
        5. Confidence in your assessment (0.0-1.0)

        Respond in JSON format:
        {{
            "misconception_present": true/false,
            "understanding_level": <float>,
            "evidence": "explanation",
            "remaining_traces": ["trace1", "trace2"],
            "confidence": <float>,
            "remediation_status": "complete/partial/minimal/none"
        }}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert at assessing whether students have overcome historical misconceptions."),
                HumanMessage(content=assessment_prompt)
            ])
            
            import json
            assessment_result = json.loads(response.content)
            
            # Add metadata
            assessment_result.update({
                "student_id": student_id,
                "misconception_type": misconception_type,
                "assessed_at": datetime.now().isoformat(),
                "assessment_response": assessment_response[:200]  # Truncated
            })
            
            return assessment_result
            
        except Exception as e:
            logger.error(f"Error assessing misconception remediation: {e}")
            return {
                "error": str(e),
                "misconception_present": True,  # Conservative default
                "understanding_level": 0.0,
                "confidence": 0.0
            }