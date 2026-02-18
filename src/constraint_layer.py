"""
Constraint Layering (Permission Zones) for EduAGI Agents

This module implements a three-tier permission system for AI tutoring agents:
- GREEN zone: Full autonomy for safe educational actions
- YELLOW zone: Autonomous actions with mandatory logging for teacher review
- RED zone: Actions requiring explicit human approval before execution

The system is designed for real school deployments where different schools
have varying comfort levels with AI autonomy.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PermissionZone(str, Enum):
    """Permission zones for AI agent actions."""
    GREEN = "green"    # Full autonomy - safe educational actions
    YELLOW = "yellow"  # Autonomous + logging - requires teacher review
    RED = "red"        # Requires approval - sensitive/high-impact actions


class ActionCategory(str, Enum):
    """Categories of actions that can be performed by AI agents."""
    CONTENT_DELIVERY = "content_delivery"
    ASSESSMENT = "assessment"
    PERSONALIZATION = "personalization"
    COMMUNICATION = "communication"
    DATA_HANDLING = "data_handling"
    ADMINISTRATIVE = "administrative"


@dataclass
class AgentAction:
    """Represents an action that an AI agent wants to perform."""
    id: str
    action_type: str
    category: ActionCategory
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    student_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    reasoning: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary for logging/storage."""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "category": self.category.value,
            "description": self.description,
            "parameters": self.parameters,
            "student_id": self.student_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "reasoning": self.reasoning
        }


class ActionClassifier(ABC):
    """Abstract base class for action classification."""
    
    @abstractmethod
    def classify_action(self, action: AgentAction) -> PermissionZone:
        """Classify an action into a permission zone."""
        pass


class DefaultActionClassifier(ActionClassifier):
    """Default action classifier with production-ready educational action rules."""
    
    def __init__(self):
        # GREEN zone actions - safe for full autonomy
        self.green_actions = {
            # Content delivery
            "explain_concept", "provide_examples", "clarify_confusion", 
            "give_hints", "show_step_by_step", "provide_encouragement",
            "adapt_language_level", "simplify_explanation", "use_analogies",
            
            # Basic personalization
            "adjust_difficulty_level", "change_teaching_strategy",
            "customize_presentation", "adapt_to_learning_style",
            
            # Practice and reinforcement
            "generate_practice_problems", "create_quiz_questions",
            "provide_immediate_feedback", "suggest_study_materials",
            "recommend_review_topics"
        }
        
        # YELLOW zone actions - autonomous but require logging
        self.yellow_actions = {
            # Assessment creation
            "create_formal_assessment", "generate_test_questions",
            "design_rubric", "create_performance_tasks",
            
            # Learning path modification
            "modify_learning_sequence", "suggest_curriculum_adjustments",
            "recommend_advanced_topics", "identify_prerequisite_gaps",
            
            # Student progress tracking
            "flag_learning_difficulties", "identify_misconceptions",
            "generate_progress_reports", "suggest_intervention_strategies",
            
            # Parent/teacher communication preparation
            "draft_progress_summary", "prepare_concern_notification",
            "generate_achievement_highlights"
        }
        
        # RED zone actions - require explicit approval
        self.red_actions = {
            # Grade-related
            "submit_final_grade", "modify_official_grade", "override_assessment_score",
            
            # External communication
            "contact_parents", "send_email_to_teacher", "notify_administration",
            "escalate_to_human_teacher", "request_intervention",
            
            # Sensitive student data
            "access_iep_document", "modify_iep_goals", "share_student_data",
            "export_learning_analytics", "create_official_report",
            
            # Administrative actions
            "change_class_enrollment", "modify_school_record",
            "flag_behavioral_concern", "request_counselor_meeting"
        }
    
    def classify_action(self, action: AgentAction) -> PermissionZone:
        """Classify action based on predefined rules."""
        action_type = action.action_type.lower()
        
        if action_type in self.green_actions:
            return PermissionZone.GREEN
        elif action_type in self.yellow_actions:
            return PermissionZone.YELLOW
        elif action_type in self.red_actions:
            return PermissionZone.RED
        
        # Default classification based on category
        if action.category == ActionCategory.CONTENT_DELIVERY:
            return PermissionZone.GREEN
        elif action.category == ActionCategory.PERSONALIZATION:
            return PermissionZone.GREEN
        elif action.category == ActionCategory.ASSESSMENT:
            return PermissionZone.YELLOW
        elif action.category in [ActionCategory.COMMUNICATION, ActionCategory.ADMINISTRATIVE]:
            return PermissionZone.RED
        elif action.category == ActionCategory.DATA_HANDLING:
            return PermissionZone.RED
        
        # Conservative default - require approval for unknown actions
        return PermissionZone.RED


class ConstraintProfile(BaseModel):
    """Configurable constraint profile for different school deployments."""
    
    school_id: str
    profile_name: str = "standard"
    strict_mode: bool = False
    
    # Zone overrides - allow schools to be more restrictive
    force_yellow_to_red: Set[str] = Field(default_factory=set)
    force_green_to_yellow: Set[str] = Field(default_factory=set)
    force_green_to_red: Set[str] = Field(default_factory=set)
    
    # Category-level restrictions
    restrict_assessment_creation: bool = False
    restrict_parent_communication: bool = True
    restrict_grade_modifications: bool = True
    restrict_data_export: bool = True
    
    # Time-based restrictions
    require_approval_after_hours: bool = False
    business_hours_start: int = 8  # 8 AM
    business_hours_end: int = 17   # 5 PM
    
    # Custom approval requirements
    custom_approval_rules: Dict[str, Any] = Field(default_factory=dict)
    
    def apply_restrictions(self, action: AgentAction, zone: PermissionZone) -> PermissionZone:
        """Apply school-specific restrictions to an action's zone classification."""
        action_type = action.action_type.lower()
        
        # Apply direct overrides
        if action_type in self.force_green_to_red:
            return PermissionZone.RED
        if action_type in self.force_green_to_yellow and zone == PermissionZone.GREEN:
            return PermissionZone.YELLOW
        if action_type in self.force_yellow_to_red and zone == PermissionZone.YELLOW:
            return PermissionZone.RED
        
        # Apply category-level restrictions
        if self.restrict_assessment_creation and action.category == ActionCategory.ASSESSMENT:
            return PermissionZone.RED
        
        if self.restrict_parent_communication and "parent" in action_type:
            return PermissionZone.RED
            
        if self.restrict_grade_modifications and "grade" in action_type:
            return PermissionZone.RED
            
        if self.restrict_data_export and "export" in action_type or "share_data" in action_type:
            return PermissionZone.RED
        
        # Time-based restrictions
        if self.require_approval_after_hours:
            current_hour = datetime.now().hour
            if current_hour < self.business_hours_start or current_hour >= self.business_hours_end:
                if zone in [PermissionZone.GREEN, PermissionZone.YELLOW]:
                    return PermissionZone.RED
        
        # Strict mode - escalate everything by one level
        if self.strict_mode:
            if zone == PermissionZone.GREEN:
                return PermissionZone.YELLOW
            elif zone == PermissionZone.YELLOW:
                return PermissionZone.RED
        
        return zone


@dataclass
class ActionLog:
    """Log entry for a yellow zone action."""
    action: AgentAction
    zone: PermissionZone
    timestamp: datetime = field(default_factory=datetime.now)
    teacher_reviewed: bool = False
    review_timestamp: Optional[datetime] = None
    review_comments: str = ""
    flagged_for_attention: bool = False


class ActionLogger:
    """Logs all yellow zone actions for teacher review."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path("eduagi_action_logs.jsonl")
        self.logs: List[ActionLog] = []
    
    async def log_action(self, action: AgentAction, zone: PermissionZone) -> None:
        """Log a yellow zone action."""
        log_entry = ActionLog(action=action, zone=zone)
        self.logs.append(log_entry)
        
        # Persist to file
        await self._write_to_file(log_entry)
        
        logger.info(f"Logged {zone.value} zone action: {action.action_type} for student {action.student_id}")
    
    async def _write_to_file(self, log_entry: ActionLog) -> None:
        """Write log entry to file."""
        try:
            log_data = {
                "action": log_entry.action.to_dict(),
                "zone": log_entry.zone.value,
                "timestamp": log_entry.timestamp.isoformat(),
                "teacher_reviewed": log_entry.teacher_reviewed,
                "review_timestamp": log_entry.review_timestamp.isoformat() if log_entry.review_timestamp else None,
                "review_comments": log_entry.review_comments,
                "flagged_for_attention": log_entry.flagged_for_attention
            }
            
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write action log: {e}")
    
    async def get_unreviewed_actions(self, days_back: int = 7) -> List[ActionLog]:
        """Get all unreviewed yellow zone actions from the last N days."""
        cutoff = datetime.now() - timedelta(days=days_back)
        return [
            log for log in self.logs 
            if not log.teacher_reviewed and log.timestamp >= cutoff
        ]
    
    async def mark_reviewed(self, action_id: str, comments: str = "") -> bool:
        """Mark an action as reviewed by a teacher."""
        for log in self.logs:
            if log.action.id == action_id:
                log.teacher_reviewed = True
                log.review_timestamp = datetime.now()
                log.review_comments = comments
                return True
        return False


@dataclass
class PendingApproval:
    """Represents an action pending approval."""
    action: AgentAction
    requested_at: datetime = field(default_factory=datetime.now)
    approver_id: Optional[str] = None
    approved: Optional[bool] = None
    approval_timestamp: Optional[datetime] = None
    approval_comments: str = ""
    timeout_minutes: int = 60
    
    @property
    def is_expired(self) -> bool:
        """Check if the approval request has expired."""
        return (datetime.now() - self.requested_at).total_seconds() > (self.timeout_minutes * 60)


class ApprovalQueue:
    """Manages red zone actions requiring human approval."""
    
    def __init__(self):
        self.pending: Dict[str, PendingApproval] = {}
        self.approval_callbacks: Dict[str, Callable[[bool, str], None]] = {}
    
    async def request_approval(
        self, 
        action: AgentAction,
        timeout_minutes: int = 60,
        callback: Optional[Callable[[bool, str], None]] = None
    ) -> str:
        """Request approval for a red zone action."""
        approval = PendingApproval(
            action=action,
            timeout_minutes=timeout_minutes
        )
        
        self.pending[action.id] = approval
        if callback:
            self.approval_callbacks[action.id] = callback
        
        # In a real implementation, this would notify teachers/admins
        await self._notify_approvers(action)
        
        logger.info(f"Approval requested for action: {action.action_type} (ID: {action.id})")
        return action.id
    
    async def approve_action(self, action_id: str, approver_id: str, comments: str = "") -> bool:
        """Approve a pending action."""
        if action_id not in self.pending:
            return False
        
        approval = self.pending[action_id]
        if approval.is_expired:
            logger.warning(f"Approval request {action_id} has expired")
            return False
        
        approval.approved = True
        approval.approval_timestamp = datetime.now()
        approval.approver_id = approver_id
        approval.approval_comments = comments
        
        # Trigger callback if available
        if action_id in self.approval_callbacks:
            self.approval_callbacks[action_id](True, comments)
            del self.approval_callbacks[action_id]
        
        logger.info(f"Action {action_id} approved by {approver_id}")
        return True
    
    async def reject_action(self, action_id: str, approver_id: str, comments: str = "") -> bool:
        """Reject a pending action."""
        if action_id not in self.pending:
            return False
        
        approval = self.pending[action_id]
        approval.approved = False
        approval.approval_timestamp = datetime.now()
        approval.approver_id = approver_id
        approval.approval_comments = comments
        
        # Trigger callback if available
        if action_id in self.approval_callbacks:
            self.approval_callbacks[action_id](False, comments)
            del self.approval_callbacks[action_id]
        
        logger.info(f"Action {action_id} rejected by {approver_id}")
        return True
    
    async def get_pending_approvals(self, filter_expired: bool = True) -> List[PendingApproval]:
        """Get all pending approval requests."""
        pending_list = list(self.pending.values())
        
        if filter_expired:
            # Remove expired approvals
            current_time = datetime.now()
            valid_pending = []
            expired_ids = []
            
            for approval in pending_list:
                if approval.is_expired:
                    expired_ids.append(approval.action.id)
                else:
                    valid_pending.append(approval)
            
            # Clean up expired approvals
            for exp_id in expired_ids:
                if exp_id in self.pending:
                    del self.pending[exp_id]
                if exp_id in self.approval_callbacks:
                    self.approval_callbacks[exp_id](False, "Approval request expired")
                    del self.approval_callbacks[exp_id]
            
            return valid_pending
        
        return pending_list
    
    async def _notify_approvers(self, action: AgentAction) -> None:
        """Notify teachers/admins of approval request."""
        # In a real implementation, this would:
        # - Send email/SMS to designated approvers
        # - Create dashboard notifications
        # - Log to monitoring systems
        logger.info(f"Notifying approvers for action: {action.description}")


class PolicyEngine:
    """Rule-based policy engine for dynamic constraint configuration."""
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("eduagi_policies.json")
        self.rules: Dict[str, Any] = {}
        self.dynamic_classifiers: List[Callable[[AgentAction], Optional[PermissionZone]]] = []
    
    async def load_policies(self) -> None:
        """Load policies from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file) as f:
                    self.rules = json.load(f)
                logger.info(f"Loaded {len(self.rules)} policy rules")
            else:
                logger.info("No policy file found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")
    
    def add_dynamic_classifier(self, classifier: Callable[[AgentAction], Optional[PermissionZone]]) -> None:
        """Add a dynamic classification rule."""
        self.dynamic_classifiers.append(classifier)
    
    def evaluate_action(self, action: AgentAction, base_zone: PermissionZone) -> PermissionZone:
        """Evaluate action against dynamic policy rules."""
        # Try dynamic classifiers first
        for classifier in self.dynamic_classifiers:
            result = classifier(action)
            if result is not None:
                return result
        
        # Check configuration rules
        action_rules = self.rules.get("action_overrides", {})
        if action.action_type in action_rules:
            override_zone = action_rules[action.action_type]
            return PermissionZone(override_zone)
        
        # Check category rules
        category_rules = self.rules.get("category_overrides", {})
        if action.category.value in category_rules:
            override_zone = category_rules[action.category.value]
            return PermissionZone(override_zone)
        
        return base_zone


class ConstraintLayer:
    """Main constraint layer coordinating all permission zone functionality."""
    
    def __init__(
        self,
        constraint_profile: Optional[ConstraintProfile] = None,
        action_classifier: Optional[ActionClassifier] = None,
        logger_instance: Optional[ActionLogger] = None,
        approval_queue: Optional[ApprovalQueue] = None,
        policy_engine: Optional[PolicyEngine] = None
    ):
        self.constraint_profile = constraint_profile
        self.action_classifier = action_classifier or DefaultActionClassifier()
        self.action_logger = logger_instance or ActionLogger()
        self.approval_queue = approval_queue or ApprovalQueue()
        self.policy_engine = policy_engine or PolicyEngine()
        
        # Integration hooks
        self.accessibility_engine = None
        self.adaptive_engine = None
        
        # Performance tracking
        self.action_stats = {
            "green_count": 0,
            "yellow_count": 0,  
            "red_count": 0,
            "approvals_granted": 0,
            "approvals_rejected": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the constraint layer."""
        await self.policy_engine.load_policies()
        logger.info("Constraint layer initialized")
    
    def integrate_accessibility_engine(self, accessibility_engine) -> None:
        """Integrate with the accessibility engine."""
        self.accessibility_engine = accessibility_engine
        logger.info("Accessibility engine integrated")
    
    def integrate_adaptive_engine(self, adaptive_engine) -> None:
        """Integrate with the adaptive learning engine."""
        self.adaptive_engine = adaptive_engine
        logger.info("Adaptive learning engine integrated")
    
    async def check_action_permission(self, action: AgentAction) -> PermissionZone:
        """Determine the permission zone for an action."""
        # Base classification
        base_zone = self.action_classifier.classify_action(action)
        
        # Apply policy engine rules
        policy_zone = self.policy_engine.evaluate_action(action, base_zone)
        
        # Apply constraint profile restrictions
        if self.constraint_profile:
            final_zone = self.constraint_profile.apply_restrictions(action, policy_zone)
        else:
            final_zone = policy_zone
        
        # Consider accessibility requirements
        if self.accessibility_engine and hasattr(self.accessibility_engine, 'get_profile'):
            try:
                profile = self.accessibility_engine.get_profile(action.student_id)
                if profile and profile.requires_patience_mode:
                    # For students needing patience mode, avoid time-pressured actions
                    if action.action_type in ["timed_assessment", "quick_response_required"]:
                        final_zone = PermissionZone.RED
            except Exception as e:
                logger.warning(f"Accessibility integration error: {e}")
        
        return final_zone
    
    async def execute_action(
        self, 
        action: AgentAction,
        callback: Optional[Callable[[bool, str], None]] = None
    ) -> Dict[str, Any]:
        """Execute an action through the constraint layer."""
        start_time = time.time()
        
        # Check permissions
        zone = await self.check_action_permission(action)
        
        result = {
            "action_id": action.id,
            "action_type": action.action_type,
            "zone": zone.value,
            "executed": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        if zone == PermissionZone.GREEN:
            # Execute immediately
            result["executed"] = True
            result["message"] = "Action executed immediately (GREEN zone)"
            self.action_stats["green_count"] += 1
            
        elif zone == PermissionZone.YELLOW:
            # Execute with logging
            await self.action_logger.log_action(action, zone)
            result["executed"] = True
            result["message"] = "Action executed with logging (YELLOW zone)"
            self.action_stats["yellow_count"] += 1
            
        elif zone == PermissionZone.RED:
            # Queue for approval
            approval_id = await self.approval_queue.request_approval(action, callback=callback)
            result["message"] = f"Action queued for approval (RED zone). Approval ID: {approval_id}"
            result["approval_id"] = approval_id
            self.action_stats["red_count"] += 1
        
        processing_time = time.time() - start_time
        result["processing_time_ms"] = round(processing_time * 1000, 2)
        
        logger.debug(f"Processed action {action.id} in {zone.value} zone ({processing_time:.3f}s)")
        return result
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for administrative dashboard."""
        pending_approvals = await self.approval_queue.get_pending_approvals()
        unreviewed_actions = await self.action_logger.get_unreviewed_actions()
        
        return {
            "action_stats": self.action_stats,
            "pending_approvals": len(pending_approvals),
            "unreviewed_actions": len(unreviewed_actions),
            "constraint_profile": self.constraint_profile.dict() if self.constraint_profile else None,
            "last_updated": datetime.now().isoformat()
        }
    
    async def create_school_profile(
        self,
        school_id: str,
        profile_name: str = "standard",
        strict_mode: bool = False,
        custom_restrictions: Optional[Dict[str, Any]] = None
    ) -> ConstraintProfile:
        """Create a constraint profile for a school deployment."""
        profile = ConstraintProfile(
            school_id=school_id,
            profile_name=profile_name,
            strict_mode=strict_mode
        )
        
        if custom_restrictions:
            # Apply custom restrictions
            if "force_yellow_to_red" in custom_restrictions:
                profile.force_yellow_to_red.update(custom_restrictions["force_yellow_to_red"])
            if "force_green_to_yellow" in custom_restrictions:
                profile.force_green_to_yellow.update(custom_restrictions["force_green_to_yellow"])
            if "restrict_assessment_creation" in custom_restrictions:
                profile.restrict_assessment_creation = custom_restrictions["restrict_assessment_creation"]
        
        logger.info(f"Created constraint profile '{profile_name}' for school {school_id}")
        return profile


# Example constraint profiles for different school types
def create_elementary_school_profile(school_id: str) -> ConstraintProfile:
    """Create a constraint profile suitable for elementary schools."""
    return ConstraintProfile(
        school_id=school_id,
        profile_name="elementary_strict",
        strict_mode=True,
        restrict_assessment_creation=True,
        restrict_parent_communication=True,
        force_green_to_yellow={"adjust_difficulty_level", "generate_practice_problems"}
    )


def create_high_school_profile(school_id: str) -> ConstraintProfile:
    """Create a constraint profile suitable for high schools."""
    return ConstraintProfile(
        school_id=school_id,
        profile_name="high_school_balanced",
        strict_mode=False,
        restrict_assessment_creation=False,
        restrict_parent_communication=True,
        require_approval_after_hours=True
    )


def create_university_profile(school_id: str) -> ConstraintProfile:
    """Create a constraint profile suitable for universities."""
    return ConstraintProfile(
        school_id=school_id,
        profile_name="university_permissive",
        strict_mode=False,
        restrict_assessment_creation=False,
        restrict_parent_communication=False,
        require_approval_after_hours=False
    )


# Utility functions for integration
async def integrate_with_tutor_agent(constraint_layer: ConstraintLayer, tutor_agent) -> None:
    """Integrate constraint layer with the existing tutor agent."""
    # This would modify the tutor agent to check permissions before actions
    original_process = tutor_agent.process
    
    async def constrained_process(input_text: str, context) -> Any:
        """Wrapped process method that checks constraints."""
        # Create action for the tutoring response
        action = AgentAction(
            id=f"tutor_{int(time.time() * 1000)}",
            action_type="provide_tutoring_response",
            category=ActionCategory.CONTENT_DELIVERY,
            description=f"Provide tutoring response to: {input_text[:100]}...",
            student_id=context.student_id,
            session_id=context.session_id,
            reasoning="Standard tutoring interaction"
        )
        
        # Check if this action is permitted
        permission_result = await constraint_layer.execute_action(action)
        
        if permission_result["executed"]:
            # Action approved, proceed with original processing
            return await original_process(input_text, context)
        else:
            # Action not approved, return appropriate response
            return {
                "text": "I need approval to respond to that request. A teacher will review it shortly.",
                "metadata": {"constraint_blocked": True, "zone": permission_result["zone"]},
                "processing_time": 0.1
            }
    
    # Replace the process method
    tutor_agent.process = constrained_process
    logger.info("Tutor agent integrated with constraint layer")