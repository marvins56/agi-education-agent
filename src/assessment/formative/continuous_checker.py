"""Continuous assessment system for real-time understanding checks."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid
import re

from langchain_core.messages import SystemMessage, HumanMessage

from src.llm.factory import LLMFactory
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class ContinuousAssessmentChecker:
    """Provides real-time understanding checks during learning sessions."""
    
    def __init__(
        self,
        memory_manager: MemoryManager
    ):
        self.memory = memory_manager
        self.llm = LLMFactory.create(provider="openai", model="gpt-4")
        
        # Triggers for formative checks
        self.check_triggers = self._initialize_check_triggers()
        
        # Understanding level indicators
        self.understanding_indicators = self._initialize_understanding_indicators()
        
        # Quick check question templates
        self.question_templates = self._initialize_question_templates()
        
        # Session tracking
        self.active_sessions = {}
    
    def _initialize_check_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize triggers that prompt formative checks."""
        return {
            "confusion_indicators": {
                "patterns": [
                    "I don't understand",
                    "I'm confused",
                    "This doesn't make sense",
                    "Can you explain",
                    "What does that mean",
                    "I'm lost"
                ],
                "threshold": 1,  # Number of indicators needed
                "priority": "high"
            },
            "time_based": {
                "interval_minutes": 15,  # Check every 15 minutes
                "priority": "medium"
            },
            "topic_transition": {
                "description": "When moving to a new topic or concept",
                "priority": "medium"
            },
            "error_patterns": {
                "patterns": [
                    "incorrect answer",
                    "misunderstanding",
                    "wrong approach"
                ],
                "threshold": 2,  # Multiple errors
                "priority": "high"
            },
            "engagement_drop": {
                "description": "Decreased participation or response quality",
                "threshold": 3,  # Consecutive low-quality responses
                "priority": "medium"
            }
        }
    
    def _initialize_understanding_indicators(self) -> Dict[str, List[str]]:
        """Initialize indicators of different understanding levels."""
        return {
            "high_understanding": [
                "Explains concepts clearly",
                "Makes connections to prior knowledge",
                "Asks insightful questions",
                "Provides detailed responses",
                "Uses appropriate terminology"
            ],
            "medium_understanding": [
                "Gives basic correct responses",
                "Shows some confusion but recovers",
                "Asks clarifying questions",
                "Demonstrates partial knowledge"
            ],
            "low_understanding": [
                "Incorrect or incomplete responses",
                "Shows confusion about basic concepts", 
                "Asks basic clarification questions",
                "Struggles with terminology"
            ],
            "very_low_understanding": [
                "Unable to respond correctly",
                "Expresses significant confusion",
                "Cannot use appropriate terminology",
                "Makes fundamental errors"
            ]
        }
    
    def _initialize_question_templates(self) -> Dict[str, List[str]]:
        """Initialize quick check question templates."""
        return {
            "understanding_check": [
                "Can you summarize what we just discussed about {topic}?",
                "How would you explain {concept} to a friend?",
                "What's the most important thing to remember about {topic}?",
                "How does {topic} connect to what we learned earlier?"
            ],
            "confusion_probe": [
                "What part of {topic} is most confusing?",
                "Where did you start to feel lost?",
                "What would help clarify {concept} for you?",
                "Is there a specific example that might help?"
            ],
            "application_check": [
                "How would you use {concept} to solve this problem?",
                "Can you give me an example of {topic} in action?",
                "What would happen if we changed {variable}?",
                "How is this similar to {previous_topic}?"
            ],
            "confidence_check": [
                "How confident do you feel about {topic}? (1-5)",
                "What aspects of {topic} do you feel strongest about?",
                "What would you like more practice with?",
                "Are you ready to move on to the next concept?"
            ]
        }
    
    async def monitor_learning_session(
        self,
        student_id: str,
        session_id: str,
        subject: str = "history"
    ) -> Dict[str, Any]:
        """Start monitoring a learning session for formative assessment opportunities."""
        
        logger.info(f"Starting formative assessment monitoring for student {student_id}")
        
        session_data = {
            "student_id": student_id,
            "session_id": session_id,
            "subject": subject,
            "start_time": datetime.now(),
            "last_check_time": datetime.now(),
            "check_count": 0,
            "understanding_history": [],
            "confusion_incidents": [],
            "engagement_level": "high"
        }
        
        self.active_sessions[session_id] = session_data
        
        return {
            "status": "monitoring_started",
            "session_id": session_id,
            "next_scheduled_check": datetime.now() + timedelta(minutes=15)
        }
    
    async def process_student_input(
        self,
        session_id: str,
        student_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process student input and determine if formative check is needed."""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session_data = self.active_sessions[session_id]
        context = context or {}
        
        # Analyze input for triggers
        trigger_analysis = await self._analyze_triggers(student_input, session_data, context)
        
        # Update session data
        session_data["last_input"] = student_input
        session_data["last_input_time"] = datetime.now()
        
        response = {"session_id": session_id, "triggers_detected": trigger_analysis}
        
        # If high-priority trigger detected, initiate formative check
        if any(trigger["priority"] == "high" for trigger in trigger_analysis):
            formative_check = await self._initiate_formative_check(
                session_data, trigger_analysis, context
            )
            response["formative_check"] = formative_check
        
        # If time-based check is due
        elif self._is_time_check_due(session_data):
            formative_check = await self._initiate_time_based_check(session_data, context)
            response["formative_check"] = formative_check
        
        return response
    
    async def _analyze_triggers(
        self,
        student_input: str,
        session_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze student input for formative assessment triggers."""
        
        detected_triggers = []
        input_lower = student_input.lower()
        
        # Check confusion indicators
        confusion_matches = sum(
            1 for pattern in self.check_triggers["confusion_indicators"]["patterns"]
            if pattern.lower() in input_lower
        )
        
        if confusion_matches >= self.check_triggers["confusion_indicators"]["threshold"]:
            detected_triggers.append({
                "type": "confusion_indicators",
                "priority": "high",
                "evidence": f"Found {confusion_matches} confusion patterns",
                "patterns_matched": confusion_matches
            })
        
        # Check engagement level
        engagement_level = await self._assess_engagement_level(student_input, session_data)
        if engagement_level < 0.3:  # Low engagement threshold
            detected_triggers.append({
                "type": "engagement_drop",
                "priority": "medium", 
                "evidence": f"Low engagement detected: {engagement_level:.2f}",
                "engagement_score": engagement_level
            })
        
        # Check for topic transition
        if context.get("topic_changed", False):
            detected_triggers.append({
                "type": "topic_transition",
                "priority": "medium",
                "evidence": f"New topic introduced: {context.get('new_topic', 'Unknown')}",
                "new_topic": context.get("new_topic")
            })
        
        return detected_triggers
    
    async def _assess_engagement_level(
        self,
        student_input: str,
        session_data: Dict[str, Any]
    ) -> float:
        """Assess student engagement level based on input quality."""
        
        engagement_prompt = f"""
        Assess the engagement level of this student response on a scale of 0.0-1.0:

        Student Response: "{student_input}"
        
        Consider:
        - Response length and detail
        - Enthusiasm and interest indicators
        - Quality of thinking demonstrated
        - Engagement with the material
        
        Provide just a number between 0.0 (disengaged) and 1.0 (highly engaged).
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert in assessing student engagement from their responses."),
                HumanMessage(content=engagement_prompt)
            ])
            
            # Extract numeric score from response
            score_match = re.search(r'(\d+\.?\d*)', response.content)
            if score_match:
                score = float(score_match.group(1))
                return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning(f"Error assessing engagement: {e}")
        
        # Default moderate engagement if assessment fails
        return 0.5
    
    def _is_time_check_due(self, session_data: Dict[str, Any]) -> bool:
        """Check if time-based formative check is due."""
        
        last_check = session_data.get("last_check_time", session_data["start_time"])
        time_since_check = datetime.now() - last_check
        interval = timedelta(minutes=self.check_triggers["time_based"]["interval_minutes"])
        
        return time_since_check >= interval
    
    async def _initiate_formative_check(
        self,
        session_data: Dict[str, Any],
        triggers: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initiate a formative assessment check based on triggers."""
        
        check_id = str(uuid.uuid4())
        current_topic = context.get("current_topic", "the current topic")
        
        # Select appropriate check type based on triggers
        check_type = self._determine_check_type(triggers)
        
        # Generate check question
        question = await self._generate_check_question(check_type, current_topic, context)
        
        formative_check = {
            "check_id": check_id,
            "session_id": session_data["session_id"],
            "student_id": session_data["student_id"],
            "check_type": check_type,
            "triggered_by": [t["type"] for t in triggers],
            "question": question,
            "context": current_topic,
            "initiated_at": datetime.now(),
            "status": "pending_response"
        }
        
        # Update session data
        session_data["last_check_time"] = datetime.now()
        session_data["check_count"] += 1
        
        return formative_check
    
    async def _initiate_time_based_check(
        self,
        session_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Initiate a time-based formative check."""
        
        return await self._initiate_formative_check(
            session_data,
            [{"type": "time_based", "priority": "medium"}],
            context
        )
    
    def _determine_check_type(self, triggers: List[Dict[str, Any]]) -> str:
        """Determine the type of formative check based on triggers."""
        
        # Priority order for check types
        if any(t["type"] == "confusion_indicators" for t in triggers):
            return "confusion_probe"
        elif any(t["type"] == "engagement_drop" for t in triggers):
            return "confidence_check"
        elif any(t["type"] == "topic_transition" for t in triggers):
            return "understanding_check"
        else:
            return "application_check"
    
    async def _generate_check_question(
        self,
        check_type: str,
        topic: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate an appropriate formative check question."""
        
        templates = self.question_templates.get(check_type, self.question_templates["understanding_check"])
        
        # Select template and customize
        import random
        template = random.choice(templates)
        
        # Replace placeholders
        question = template.format(
            topic=topic,
            concept=topic,
            variable="the variables",
            previous_topic=context.get("previous_topic", "previous concepts")
        )
        
        return question
    
    async def process_check_response(
        self,
        check_id: str,
        student_response: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Process student's response to a formative check."""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session_data = self.active_sessions[session_id]
        
        # Analyze the response for understanding level
        understanding_analysis = await self._analyze_understanding_level(
            student_response, check_id, session_data
        )
        
        # Generate feedback and next steps
        feedback = await self._generate_formative_feedback(
            understanding_analysis, student_response
        )
        
        # Update session understanding history
        check_result = {
            "check_id": check_id,
            "response": student_response,
            "understanding_level": understanding_analysis["level"],
            "confidence": understanding_analysis["confidence"],
            "misconceptions": understanding_analysis.get("misconceptions", []),
            "feedback": feedback,
            "timestamp": datetime.now()
        }
        
        session_data["understanding_history"].append(check_result)
        
        # Store in memory for long-term tracking
        await self._store_formative_check_result(session_data["student_id"], check_result)
        
        return {
            "check_id": check_id,
            "understanding_level": understanding_analysis["level"],
            "feedback": feedback,
            "next_action": understanding_analysis.get("recommended_action", "continue"),
            "needs_intervention": understanding_analysis["level"] < 0.5
        }
    
    async def _analyze_understanding_level(
        self,
        student_response: str,
        check_id: str,
        session_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze student response to determine understanding level."""
        
        analysis_prompt = f"""
        Analyze this student's response to a formative assessment question:

        Student Response: "{student_response}"
        
        Session Context: Student has completed {session_data.get('check_count', 0)} checks so far.
        
        Evaluate:
        1. Understanding level (0.0 = no understanding, 1.0 = complete understanding)
        2. Confidence level (0.0 = very uncertain, 1.0 = very confident)
        3. Any misconceptions detected
        4. Recommended next action (continue, review, reteach, provide_example)
        
        Response format:
        {{
            "level": <float 0.0-1.0>,
            "confidence": <float 0.0-1.0>,
            "misconceptions": ["misconception1", "misconception2"],
            "evidence": "Brief explanation of assessment",
            "recommended_action": "continue/review/reteach/provide_example"
        }}
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are an expert at assessing student understanding from their responses."),
                HumanMessage(content=analysis_prompt)
            ])
            
            # Parse JSON response (simplified parsing for now)
            import json
            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback analysis
                analysis = self._fallback_understanding_analysis(student_response)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing understanding level: {e}")
            return self._fallback_understanding_analysis(student_response)
    
    def _fallback_understanding_analysis(self, student_response: str) -> Dict[str, Any]:
        """Fallback analysis if LLM analysis fails."""
        
        response_lower = student_response.lower()
        
        # Simple keyword-based analysis
        understanding_indicators = {
            "high": ["understand", "clear", "makes sense", "i get it", "correct"],
            "low": ["confused", "don't understand", "unclear", "lost", "help"]
        }
        
        high_count = sum(1 for word in understanding_indicators["high"] if word in response_lower)
        low_count = sum(1 for word in understanding_indicators["low"] if word in response_lower)
        
        if high_count > low_count:
            level = 0.7
            confidence = 0.6
            action = "continue"
        elif low_count > high_count:
            level = 0.3
            confidence = 0.4
            action = "review"
        else:
            level = 0.5
            confidence = 0.5
            action = "continue"
        
        return {
            "level": level,
            "confidence": confidence,
            "misconceptions": [],
            "evidence": "Keyword-based analysis",
            "recommended_action": action
        }
    
    async def _generate_formative_feedback(
        self,
        understanding_analysis: Dict[str, Any],
        student_response: str
    ) -> str:
        """Generate appropriate feedback based on understanding analysis."""
        
        level = understanding_analysis["level"]
        action = understanding_analysis.get("recommended_action", "continue")
        misconceptions = understanding_analysis.get("misconceptions", [])
        
        feedback_prompt = f"""
        Generate brief, encouraging feedback for a student based on their formative assessment:
        
        Understanding Level: {level:.1f}/1.0
        Recommended Action: {action}
        Student Response: "{student_response}"
        Misconceptions: {misconceptions}
        
        Feedback should be:
        - Brief (1-2 sentences)
        - Encouraging and supportive
        - Specific to their response
        - Include next step guidance if needed
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a supportive teacher providing formative feedback to students."),
                HumanMessage(content=feedback_prompt)
            ])
            
            return response.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            
            # Fallback feedback based on level
            if level >= 0.7:
                return "Great understanding! You're ready to continue."
            elif level >= 0.5:
                return "Good progress. Let's clarify a few points before moving on."
            else:
                return "Let's review this concept together to strengthen your understanding."
    
    async def _store_formative_check_result(
        self,
        student_id: str,
        check_result: Dict[str, Any]
    ) -> None:
        """Store formative check result in memory for tracking."""
        
        try:
            await self.memory.store_learning_event(
                student_id=student_id,
                event_type="formative_check",
                event_data={
                    "check_id": check_result["check_id"],
                    "understanding_level": check_result["understanding_level"],
                    "confidence": check_result["confidence"],
                    "misconceptions": check_result.get("misconceptions", []),
                    "timestamp": check_result["timestamp"].isoformat()
                },
                subject="history"
            )
        except Exception as e:
            logger.error(f"Error storing formative check result: {e}")
    
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of formative assessment data for a session."""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session_data = self.active_sessions[session_id]
        understanding_history = session_data.get("understanding_history", [])
        
        if not understanding_history:
            return {
                "session_id": session_id,
                "total_checks": 0,
                "average_understanding": 0.0,
                "trend": "no_data"
            }
        
        # Calculate summary statistics
        levels = [check["understanding_level"] for check in understanding_history]
        average_understanding = sum(levels) / len(levels)
        
        # Calculate trend (improving, stable, declining)
        if len(levels) >= 3:
            recent_avg = sum(levels[-3:]) / 3
            early_avg = sum(levels[:3]) / 3
            
            if recent_avg > early_avg + 0.1:
                trend = "improving"
            elif recent_avg < early_avg - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        # Identify common misconceptions
        all_misconceptions = []
        for check in understanding_history:
            all_misconceptions.extend(check.get("misconceptions", []))
        
        misconception_counts = {}
        for misconception in all_misconceptions:
            misconception_counts[misconception] = misconception_counts.get(misconception, 0) + 1
        
        common_misconceptions = [
            {"misconception": m, "frequency": f}
            for m, f in sorted(misconception_counts.items(), key=lambda x: x[1], reverse=True)
        ][:3]  # Top 3
        
        return {
            "session_id": session_id,
            "student_id": session_data["student_id"],
            "session_duration_minutes": (datetime.now() - session_data["start_time"]).total_seconds() / 60,
            "total_checks": len(understanding_history),
            "average_understanding": average_understanding,
            "trend": trend,
            "latest_understanding": levels[-1] if levels else 0.0,
            "common_misconceptions": common_misconceptions,
            "needs_intervention": average_understanding < 0.5,
            "engagement_level": session_data.get("engagement_level", "medium")
        }
    
    async def end_session_monitoring(self, session_id: str) -> Dict[str, Any]:
        """End monitoring for a session and return final summary."""
        
        summary = await self.get_session_summary(session_id)
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return {
            **summary,
            "status": "monitoring_ended",
            "ended_at": datetime.now()
        }