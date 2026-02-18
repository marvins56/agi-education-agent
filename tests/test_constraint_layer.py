"""
Comprehensive tests for the constraint layer (permission zones) system.
"""

import asyncio
import json
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.constraint_layer import (
    ActionCategory,
    ActionClassifier,
    ActionLog,
    ActionLogger,
    AgentAction,
    ApprovalQueue,
    ConstraintLayer,
    ConstraintProfile,
    DefaultActionClassifier,
    PendingApproval,
    PermissionZone,
    PolicyEngine,
    create_elementary_school_profile,
    create_high_school_profile,
    create_university_profile,
    integrate_with_tutor_agent,
)


class TestAgentAction:
    """Test the AgentAction dataclass."""
    
    def test_agent_action_creation(self):
        """Test basic AgentAction creation and properties."""
        action = AgentAction(
            id="test_123",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Explain photosynthesis to student",
            student_id="student_456",
            session_id="session_789"
        )
        
        assert action.id == "test_123"
        assert action.action_type == "explain_concept"
        assert action.category == ActionCategory.CONTENT_DELIVERY
        assert action.student_id == "student_456"
        assert isinstance(action.timestamp, datetime)
    
    def test_agent_action_to_dict(self):
        """Test AgentAction conversion to dictionary."""
        action = AgentAction(
            id="test_123",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Explain photosynthesis",
            parameters={"topic": "photosynthesis", "difficulty": 5},
            reasoning="Student asked about plants"
        )
        
        action_dict = action.to_dict()
        
        assert action_dict["id"] == "test_123"
        assert action_dict["action_type"] == "explain_concept"
        assert action_dict["category"] == "content_delivery"
        assert action_dict["parameters"]["topic"] == "photosynthesis"
        assert action_dict["reasoning"] == "Student asked about plants"
        assert "timestamp" in action_dict


class TestDefaultActionClassifier:
    """Test the default action classifier."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = DefaultActionClassifier()
    
    def test_green_zone_classification(self):
        """Test classification of GREEN zone actions."""
        green_actions = [
            ("explain_concept", ActionCategory.CONTENT_DELIVERY),
            ("provide_examples", ActionCategory.CONTENT_DELIVERY), 
            ("give_hints", ActionCategory.CONTENT_DELIVERY),
            ("adjust_difficulty_level", ActionCategory.PERSONALIZATION),
            ("generate_practice_problems", ActionCategory.CONTENT_DELIVERY)
        ]
        
        for action_type, category in green_actions:
            action = AgentAction(
                id=f"test_{action_type}",
                action_type=action_type,
                category=category,
                description=f"Test {action_type}"
            )
            
            zone = self.classifier.classify_action(action)
            assert zone == PermissionZone.GREEN, f"{action_type} should be GREEN zone"
    
    def test_yellow_zone_classification(self):
        """Test classification of YELLOW zone actions."""
        yellow_actions = [
            ("create_formal_assessment", ActionCategory.ASSESSMENT),
            ("modify_learning_sequence", ActionCategory.PERSONALIZATION),
            ("flag_learning_difficulties", ActionCategory.ASSESSMENT),
            ("generate_progress_reports", ActionCategory.ASSESSMENT)
        ]
        
        for action_type, category in yellow_actions:
            action = AgentAction(
                id=f"test_{action_type}",
                action_type=action_type,
                category=category,
                description=f"Test {action_type}"
            )
            
            zone = self.classifier.classify_action(action)
            assert zone == PermissionZone.YELLOW, f"{action_type} should be YELLOW zone"
    
    def test_red_zone_classification(self):
        """Test classification of RED zone actions."""
        red_actions = [
            ("submit_final_grade", ActionCategory.ADMINISTRATIVE),
            ("contact_parents", ActionCategory.COMMUNICATION),
            ("modify_iep_goals", ActionCategory.ADMINISTRATIVE),
            ("share_student_data", ActionCategory.DATA_HANDLING),
            ("escalate_to_human_teacher", ActionCategory.COMMUNICATION)
        ]
        
        for action_type, category in red_actions:
            action = AgentAction(
                id=f"test_{action_type}",
                action_type=action_type,
                category=category,
                description=f"Test {action_type}"
            )
            
            zone = self.classifier.classify_action(action)
            assert zone == PermissionZone.RED, f"{action_type} should be RED zone"
    
    def test_unknown_action_classification(self):
        """Test that unknown actions default to conservative classification."""
        unknown_action = AgentAction(
            id="test_unknown",
            action_type="unknown_action_type",
            category=ActionCategory.DATA_HANDLING,
            description="Unknown action"
        )
        
        zone = self.classifier.classify_action(unknown_action)
        assert zone == PermissionZone.RED, "Unknown actions should default to RED zone"


class TestConstraintProfile:
    """Test the ConstraintProfile functionality."""
    
    def test_basic_constraint_profile(self):
        """Test basic constraint profile creation."""
        profile = ConstraintProfile(
            school_id="school_123",
            profile_name="test_profile"
        )
        
        assert profile.school_id == "school_123"
        assert profile.profile_name == "test_profile"
        assert not profile.strict_mode
        assert profile.restrict_parent_communication
    
    def test_strict_mode_escalation(self):
        """Test that strict mode escalates permissions appropriately."""
        profile = ConstraintProfile(
            school_id="school_123",
            strict_mode=True
        )
        
        green_action = AgentAction(
            id="test_green",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Test green action"
        )
        
        yellow_action = AgentAction(
            id="test_yellow",
            action_type="create_assessment",
            category=ActionCategory.ASSESSMENT,
            description="Test yellow action"
        )
        
        # In strict mode, GREEN becomes YELLOW, YELLOW becomes RED
        assert profile.apply_restrictions(green_action, PermissionZone.GREEN) == PermissionZone.YELLOW
        assert profile.apply_restrictions(yellow_action, PermissionZone.YELLOW) == PermissionZone.RED
    
    def test_direct_overrides(self):
        """Test direct action type overrides."""
        profile = ConstraintProfile(
            school_id="school_123",
            force_green_to_red={"explain_concept"},
            force_green_to_yellow={"provide_examples"}
        )
        
        explain_action = AgentAction(
            id="test_explain",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Explain concept"
        )
        
        examples_action = AgentAction(
            id="test_examples", 
            action_type="provide_examples",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Provide examples"
        )
        
        assert profile.apply_restrictions(explain_action, PermissionZone.GREEN) == PermissionZone.RED
        assert profile.apply_restrictions(examples_action, PermissionZone.GREEN) == PermissionZone.YELLOW
    
    def test_time_based_restrictions(self):
        """Test after-hours restrictions."""
        profile = ConstraintProfile(
            school_id="school_123",
            require_approval_after_hours=True,
            business_hours_start=9,
            business_hours_end=17
        )
        
        action = AgentAction(
            id="test_time",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Time-based test"
        )
        
        # Mock current time to be after hours (e.g., 20:00)
        with patch('src.constraint_layer.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 20, 0)  # 8 PM
            zone = profile.apply_restrictions(action, PermissionZone.GREEN)
            assert zone == PermissionZone.RED, "After hours should escalate to RED"


class TestActionLogger:
    """Test the action logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl")
        self.temp_path = Path(self.temp_file.name)
        self.temp_file.close()
        
        self.logger = ActionLogger(log_file=self.temp_path)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_path.exists():
            self.temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_log_action(self):
        """Test logging a yellow zone action."""
        action = AgentAction(
            id="test_log",
            action_type="create_assessment",
            category=ActionCategory.ASSESSMENT,
            description="Create test assessment",
            student_id="student_123"
        )
        
        await self.logger.log_action(action, PermissionZone.YELLOW)
        
        # Check that action was added to logs
        assert len(self.logger.logs) == 1
        log_entry = self.logger.logs[0]
        assert log_entry.action.id == "test_log"
        assert log_entry.zone == PermissionZone.YELLOW
        assert not log_entry.teacher_reviewed
        
        # Check that log was written to file
        assert self.temp_path.exists()
        with open(self.temp_path) as f:
            log_lines = f.readlines()
            assert len(log_lines) == 1
            log_data = json.loads(log_lines[0])
            assert log_data["action"]["id"] == "test_log"
            assert log_data["zone"] == "yellow"
    
    @pytest.mark.asyncio
    async def test_get_unreviewed_actions(self):
        """Test getting unreviewed actions."""
        # Create some test actions
        actions = [
            AgentAction(id="action1", action_type="test1", category=ActionCategory.ASSESSMENT, description="Test 1"),
            AgentAction(id="action2", action_type="test2", category=ActionCategory.ASSESSMENT, description="Test 2"),
            AgentAction(id="action3", action_type="test3", category=ActionCategory.ASSESSMENT, description="Test 3")
        ]
        
        # Log the actions
        for action in actions:
            await self.logger.log_action(action, PermissionZone.YELLOW)
        
        # Mark one as reviewed
        await self.logger.mark_reviewed("action2", "Looks good")
        
        # Get unreviewed actions
        unreviewed = await self.logger.get_unreviewed_actions()
        unreviewed_ids = [log.action.id for log in unreviewed]
        
        assert len(unreviewed) == 2
        assert "action1" in unreviewed_ids
        assert "action3" in unreviewed_ids
        assert "action2" not in unreviewed_ids
    
    @pytest.mark.asyncio
    async def test_mark_reviewed(self):
        """Test marking an action as reviewed."""
        action = AgentAction(
            id="review_test",
            action_type="test_action",
            category=ActionCategory.ASSESSMENT,
            description="Review test"
        )
        
        await self.logger.log_action(action, PermissionZone.YELLOW)
        
        # Mark as reviewed
        success = await self.logger.mark_reviewed("review_test", "Approved by teacher")
        assert success
        
        log_entry = self.logger.logs[0]
        assert log_entry.teacher_reviewed
        assert log_entry.review_comments == "Approved by teacher"
        assert log_entry.review_timestamp is not None


class TestApprovalQueue:
    """Test the approval queue functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.queue = ApprovalQueue()
    
    @pytest.mark.asyncio
    async def test_request_approval(self):
        """Test requesting approval for an action."""
        action = AgentAction(
            id="approval_test",
            action_type="contact_parents",
            category=ActionCategory.COMMUNICATION,
            description="Contact parents about student progress"
        )
        
        with patch.object(self.queue, '_notify_approvers') as mock_notify:
            approval_id = await self.queue.request_approval(action, timeout_minutes=30)
            
            assert approval_id == action.id
            assert action.id in self.queue.pending
            assert self.queue.pending[action.id].timeout_minutes == 30
            mock_notify.assert_called_once_with(action)
    
    @pytest.mark.asyncio
    async def test_approve_action(self):
        """Test approving a pending action."""
        action = AgentAction(
            id="approve_test",
            action_type="submit_grade",
            category=ActionCategory.ADMINISTRATIVE,
            description="Submit final grade"
        )
        
        # Request approval
        with patch.object(self.queue, '_notify_approvers'):
            await self.queue.request_approval(action)
        
        # Approve the action
        success = await self.queue.approve_action("approve_test", "teacher_123", "Approved")
        
        assert success
        approval = self.queue.pending["approve_test"]
        assert approval.approved is True
        assert approval.approver_id == "teacher_123"
        assert approval.approval_comments == "Approved"
    
    @pytest.mark.asyncio
    async def test_reject_action(self):
        """Test rejecting a pending action."""
        action = AgentAction(
            id="reject_test",
            action_type="share_data",
            category=ActionCategory.DATA_HANDLING,
            description="Share student data"
        )
        
        # Request approval
        with patch.object(self.queue, '_notify_approvers'):
            await self.queue.request_approval(action)
        
        # Reject the action
        success = await self.queue.reject_action("reject_test", "teacher_456", "Not authorized")
        
        assert success
        approval = self.queue.pending["reject_test"]
        assert approval.approved is False
        assert approval.approver_id == "teacher_456"
        assert approval.approval_comments == "Not authorized"
    
    @pytest.mark.asyncio
    async def test_approval_callback(self):
        """Test callback functionality for approvals."""
        action = AgentAction(
            id="callback_test",
            action_type="test_callback",
            category=ActionCategory.COMMUNICATION,
            description="Callback test"
        )
        
        callback_called = False
        callback_approved = None
        callback_comments = None
        
        def test_callback(approved: bool, comments: str):
            nonlocal callback_called, callback_approved, callback_comments
            callback_called = True
            callback_approved = approved
            callback_comments = comments
        
        # Request approval with callback
        with patch.object(self.queue, '_notify_approvers'):
            await self.queue.request_approval(action, callback=test_callback)
        
        # Approve the action
        await self.queue.approve_action("callback_test", "teacher_789", "Callback test approved")
        
        assert callback_called
        assert callback_approved is True
        assert callback_comments == "Callback test approved"
    
    @pytest.mark.asyncio
    async def test_expired_approvals(self):
        """Test handling of expired approval requests."""
        action = AgentAction(
            id="expire_test",
            action_type="test_expire",
            category=ActionCategory.COMMUNICATION,
            description="Expiration test"
        )
        
        # Create approval with very short timeout
        approval = PendingApproval(action=action, timeout_minutes=0)  # Immediate expiration
        approval.requested_at = datetime.now() - timedelta(minutes=1)  # Already expired
        
        self.queue.pending[action.id] = approval
        
        # Try to approve expired request
        success = await self.queue.approve_action("expire_test", "teacher_123", "Too late")
        assert not success
        
        # Get pending approvals should filter out expired ones
        pending = await self.queue.get_pending_approvals(filter_expired=True)
        assert len(pending) == 0
        assert "expire_test" not in self.queue.pending


class TestPolicyEngine:
    """Test the policy engine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_config = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_path = Path(self.temp_config.name)
        
        # Write test policy configuration
        test_config = {
            "action_overrides": {
                "test_action": "red"
            },
            "category_overrides": {
                "content_delivery": "green"
            }
        }
        json.dump(test_config, self.temp_config)
        self.temp_config.close()
        
        self.policy_engine = PolicyEngine(config_file=self.temp_path)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_path.exists():
            self.temp_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_policies(self):
        """Test loading policies from configuration file."""
        await self.policy_engine.load_policies()
        
        assert "action_overrides" in self.policy_engine.rules
        assert "test_action" in self.policy_engine.rules["action_overrides"]
        assert self.policy_engine.rules["action_overrides"]["test_action"] == "red"
    
    def test_evaluate_action_with_override(self):
        """Test action evaluation with policy overrides."""
        # Load policies first
        asyncio.run(self.policy_engine.load_policies())
        
        action = AgentAction(
            id="policy_test",
            action_type="test_action",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Policy test"
        )
        
        # Should override to RED despite content delivery usually being GREEN
        zone = self.policy_engine.evaluate_action(action, PermissionZone.GREEN)
        assert zone == PermissionZone.RED
    
    def test_dynamic_classifier(self):
        """Test dynamic classification rules."""
        def custom_classifier(action: AgentAction) -> Optional[PermissionZone]:
            if action.action_type == "special_action":
                return PermissionZone.YELLOW
            return None
        
        self.policy_engine.add_dynamic_classifier(custom_classifier)
        
        action = AgentAction(
            id="dynamic_test",
            action_type="special_action",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Dynamic test"
        )
        
        zone = self.policy_engine.evaluate_action(action, PermissionZone.GREEN)
        assert zone == PermissionZone.YELLOW


class TestConstraintLayer:
    """Test the main ConstraintLayer functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.constraint_layer = ConstraintLayer()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test constraint layer initialization."""
        await self.constraint_layer.initialize()
        # Should not raise any exceptions
    
    @pytest.mark.asyncio
    async def test_check_action_permission(self):
        """Test action permission checking."""
        green_action = AgentAction(
            id="green_test",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Green zone test"
        )
        
        yellow_action = AgentAction(
            id="yellow_test",
            action_type="create_assessment",
            category=ActionCategory.ASSESSMENT,
            description="Yellow zone test"
        )
        
        red_action = AgentAction(
            id="red_test",
            action_type="contact_parents",
            category=ActionCategory.COMMUNICATION,
            description="Red zone test"
        )
        
        assert await self.constraint_layer.check_action_permission(green_action) == PermissionZone.GREEN
        assert await self.constraint_layer.check_action_permission(yellow_action) == PermissionZone.YELLOW
        assert await self.constraint_layer.check_action_permission(red_action) == PermissionZone.RED
    
    @pytest.mark.asyncio
    async def test_execute_green_action(self):
        """Test execution of GREEN zone action."""
        action = AgentAction(
            id="execute_green",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Execute green test"
        )
        
        result = await self.constraint_layer.execute_action(action)
        
        assert result["executed"] is True
        assert result["zone"] == "green"
        assert "immediately" in result["message"]
        assert self.constraint_layer.action_stats["green_count"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_yellow_action(self):
        """Test execution of YELLOW zone action."""
        action = AgentAction(
            id="execute_yellow",
            action_type="create_assessment",
            category=ActionCategory.ASSESSMENT,
            description="Execute yellow test"
        )
        
        result = await self.constraint_layer.execute_action(action)
        
        assert result["executed"] is True
        assert result["zone"] == "yellow"
        assert "logging" in result["message"]
        assert self.constraint_layer.action_stats["yellow_count"] == 1
        
        # Check that action was logged
        logs = await self.constraint_layer.action_logger.get_unreviewed_actions()
        assert len(logs) == 1
        assert logs[0].action.id == "execute_yellow"
    
    @pytest.mark.asyncio
    async def test_execute_red_action(self):
        """Test execution of RED zone action."""
        action = AgentAction(
            id="execute_red",
            action_type="contact_parents",
            category=ActionCategory.COMMUNICATION,
            description="Execute red test"
        )
        
        result = await self.constraint_layer.execute_action(action)
        
        assert result["executed"] is False
        assert result["zone"] == "red"
        assert "approval" in result["message"]
        assert "approval_id" in result
        assert self.constraint_layer.action_stats["red_count"] == 1
        
        # Check that action is in approval queue
        pending = await self.constraint_layer.approval_queue.get_pending_approvals()
        assert len(pending) == 1
        assert pending[0].action.id == "execute_red"
    
    @pytest.mark.asyncio
    async def test_accessibility_integration(self):
        """Test integration with accessibility engine."""
        # Mock accessibility engine
        mock_accessibility = MagicMock()
        mock_profile = MagicMock()
        mock_profile.requires_patience_mode = True
        mock_accessibility.get_profile.return_value = mock_profile
        
        self.constraint_layer.integrate_accessibility_engine(mock_accessibility)
        
        # Test action that would be affected by patience mode
        action = AgentAction(
            id="accessibility_test",
            action_type="timed_assessment",
            category=ActionCategory.ASSESSMENT,
            description="Timed assessment test",
            student_id="student_123"
        )
        
        zone = await self.constraint_layer.check_action_permission(action)
        # Should escalate to RED due to patience mode requirement
        assert zone == PermissionZone.RED
    
    @pytest.mark.asyncio
    async def test_dashboard_data(self):
        """Test dashboard data generation."""
        # Execute some actions to generate stats
        actions = [
            AgentAction(id="dash1", action_type="explain_concept", category=ActionCategory.CONTENT_DELIVERY, description="Test 1"),
            AgentAction(id="dash2", action_type="create_assessment", category=ActionCategory.ASSESSMENT, description="Test 2"),
            AgentAction(id="dash3", action_type="contact_parents", category=ActionCategory.COMMUNICATION, description="Test 3")
        ]
        
        for action in actions:
            await self.constraint_layer.execute_action(action)
        
        dashboard_data = await self.constraint_layer.get_dashboard_data()
        
        assert dashboard_data["action_stats"]["green_count"] == 1
        assert dashboard_data["action_stats"]["yellow_count"] == 1
        assert dashboard_data["action_stats"]["red_count"] == 1
        assert dashboard_data["pending_approvals"] == 1
        assert dashboard_data["unreviewed_actions"] == 1
        assert "last_updated" in dashboard_data


class TestSchoolProfiles:
    """Test predefined school constraint profiles."""
    
    def test_elementary_school_profile(self):
        """Test elementary school constraint profile."""
        profile = create_elementary_school_profile("elem_school_123")
        
        assert profile.school_id == "elem_school_123"
        assert profile.profile_name == "elementary_strict"
        assert profile.strict_mode is True
        assert profile.restrict_assessment_creation is True
        assert "adjust_difficulty_level" in profile.force_green_to_yellow
    
    def test_high_school_profile(self):
        """Test high school constraint profile."""
        profile = create_high_school_profile("high_school_456")
        
        assert profile.school_id == "high_school_456"
        assert profile.profile_name == "high_school_balanced"
        assert profile.strict_mode is False
        assert profile.restrict_assessment_creation is False
        assert profile.require_approval_after_hours is True
    
    def test_university_profile(self):
        """Test university constraint profile."""
        profile = create_university_profile("university_789")
        
        assert profile.school_id == "university_789"
        assert profile.profile_name == "university_permissive"
        assert profile.strict_mode is False
        assert profile.restrict_parent_communication is False
        assert profile.require_approval_after_hours is False


class TestIntegration:
    """Test integration with existing EduAGI components."""
    
    @pytest.mark.asyncio
    async def test_tutor_agent_integration(self):
        """Test integration with tutor agent."""
        # Create mock tutor agent
        mock_tutor = MagicMock()
        mock_tutor.process = AsyncMock(return_value={
            "text": "Here's the explanation...",
            "metadata": {},
            "processing_time": 0.5
        })
        
        # Create constraint layer with permissive profile
        constraint_layer = ConstraintLayer()
        await constraint_layer.initialize()
        
        # Integrate with tutor agent
        await integrate_with_tutor_agent(constraint_layer, mock_tutor)
        
        # Create mock context
        mock_context = MagicMock()
        mock_context.student_id = "student_123"
        mock_context.session_id = "session_456"
        
        # Test that the integration works
        result = await mock_tutor.process("Explain photosynthesis", mock_context)
        
        # Should execute normally for safe content delivery
        assert "explanation" in result["text"] or result["text"] == "Here's the explanation..."
    
    def test_custom_school_profile_creation(self):
        """Test creating custom school profiles."""
        constraint_layer = ConstraintLayer()
        
        custom_restrictions = {
            "force_yellow_to_red": ["create_assessment", "generate_quiz"],
            "restrict_assessment_creation": True
        }
        
        profile = constraint_layer.create_school_profile(
            school_id="custom_school_999",
            profile_name="custom_strict",
            strict_mode=True,
            custom_restrictions=custom_restrictions
        )
        
        assert profile.school_id == "custom_school_999"
        assert profile.strict_mode is True
        assert "create_assessment" in profile.force_yellow_to_red
        assert profile.restrict_assessment_creation is True


class TestRealWorldScenarios:
    """Test realistic scenarios that would occur in school deployments."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.constraint_layer = ConstraintLayer()
    
    @pytest.mark.asyncio
    async def test_tutoring_session_workflow(self):
        """Test a complete tutoring session workflow."""
        await self.constraint_layer.initialize()
        
        # Sequence of actions in a typical tutoring session
        tutoring_actions = [
            ("explain_concept", ActionCategory.CONTENT_DELIVERY, "Explain algebra basics"),
            ("generate_practice_problems", ActionCategory.CONTENT_DELIVERY, "Generate practice problems"),
            ("provide_immediate_feedback", ActionCategory.CONTENT_DELIVERY, "Give feedback on student work"),
            ("adjust_difficulty_level", ActionCategory.PERSONALIZATION, "Make problems easier"),
            ("create_assessment", ActionCategory.ASSESSMENT, "Create quiz to test understanding"),
            ("flag_learning_difficulties", ActionCategory.ASSESSMENT, "Student struggling with concepts")
        ]
        
        results = []
        for i, (action_type, category, description) in enumerate(tutoring_actions):
            action = AgentAction(
                id=f"session_action_{i}",
                action_type=action_type,
                category=category,
                description=description,
                student_id="student_123",
                session_id="session_456"
            )
            
            result = await self.constraint_layer.execute_action(action)
            results.append((action_type, result))
        
        # Verify expected behavior
        assert results[0][1]["executed"] is True  # explain_concept - GREEN
        assert results[1][1]["executed"] is True  # generate_practice_problems - GREEN
        assert results[2][1]["executed"] is True  # provide_immediate_feedback - GREEN
        assert results[3][1]["executed"] is True  # adjust_difficulty_level - GREEN
        assert results[4][1]["executed"] is True  # create_assessment - YELLOW (logged)
        assert results[5][1]["executed"] is True  # flag_learning_difficulties - YELLOW (logged)
        
        # Should have 2 yellow zone actions logged
        logs = await self.constraint_layer.action_logger.get_unreviewed_actions()
        assert len(logs) == 2
    
    @pytest.mark.asyncio
    async def test_strict_school_scenario(self):
        """Test behavior in a strict school environment."""
        # Create strict elementary school profile
        strict_profile = create_elementary_school_profile("strict_elem_123")
        constraint_layer = ConstraintLayer(constraint_profile=strict_profile)
        await constraint_layer.initialize()
        
        # Even basic actions should be escalated in strict mode
        basic_action = AgentAction(
            id="strict_test",
            action_type="explain_concept",
            category=ActionCategory.CONTENT_DELIVERY,
            description="Basic explanation",
            student_id="student_123"
        )
        
        result = await constraint_layer.execute_action(basic_action)
        
        # In strict mode, GREEN becomes YELLOW (executed but logged)
        assert result["executed"] is True
        assert result["zone"] == "yellow"
        
        # Should be logged for teacher review
        logs = await constraint_layer.action_logger.get_unreviewed_actions()
        assert len(logs) == 1
    
    @pytest.mark.asyncio
    async def test_emergency_escalation_scenario(self):
        """Test emergency escalation scenario."""
        await self.constraint_layer.initialize()
        
        # Actions that would require immediate human intervention
        emergency_actions = [
            ("flag_behavioral_concern", ActionCategory.ADMINISTRATIVE, "Student showing concerning behavior"),
            ("request_counselor_meeting", ActionCategory.ADMINISTRATIVE, "Student needs counseling"),
            ("escalate_to_human_teacher", ActionCategory.COMMUNICATION, "Situation beyond AI capability")
        ]
        
        for i, (action_type, category, description) in enumerate(emergency_actions):
            action = AgentAction(
                id=f"emergency_{i}",
                action_type=action_type,
                category=category,
                description=description,
                student_id="student_emergency"
            )
            
            result = await self.constraint_layer.execute_action(action)
            
            # All should require approval (RED zone)
            assert result["executed"] is False
            assert result["zone"] == "red"
            assert "approval" in result["message"]
        
        # Should have 3 pending approvals
        pending = await self.constraint_layer.approval_queue.get_pending_approvals()
        assert len(pending) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])