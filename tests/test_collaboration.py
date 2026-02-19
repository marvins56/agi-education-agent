"""
Tests for the EduAGI collaboration package.

Comprehensive tests for classroom management, assignments, discussions, 
and peer learning functionality.
"""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Import collaboration modules
from src.collaboration import Classroom, AssignmentManager, DiscussionBoard, PeerLearningManager
from src.collaboration.classroom import (
    UserRole, GradeLevel, ClassroomSettings, ClassroomMember, Announcement
)
from src.collaboration.assignments import (
    AssignmentType, SubmissionStatus, GradingStatus, QuizQuestion, Submission, Assignment
)
from src.collaboration.discussion import (
    PostType, PostStatus, DiscussionPost, DiscussionThread
)
from src.collaboration.peer_learning import (
    MatchingCriteria, SessionType, SessionStatus, LearnerProfile, StudyBuddy, LearningSession
)


class TestClassroom:
    """Test cases for Classroom management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.owner_id = "teacher_123"
        self.owner_username = "mr_smith"
        self.classroom = Classroom(
            name="Advanced Python Programming",
            owner_id=self.owner_id,
            owner_username=self.owner_username,
            description="Learn advanced Python concepts"
        )
        
    def test_classroom_creation(self):
        """Test basic classroom creation."""
        assert self.classroom.name == "Advanced Python Programming"
        assert self.classroom.owner_id == self.owner_id
        assert len(self.classroom.members) == 1
        assert self.classroom.members[self.owner_id].role == UserRole.OWNER
        assert len(self.classroom.invite_code) == 8
        
    def test_add_member(self):
        """Test adding members to classroom."""
        student_id = "student_456"
        member = self.classroom.add_member(
            student_id, "alice", "Alice Johnson", UserRole.STUDENT, "alice@example.com"
        )
        
        assert member.user_id == student_id
        assert member.role == UserRole.STUDENT
        assert member.email == "alice@example.com"
        assert len(self.classroom.members) == 2
        
    def test_join_with_invite_code(self):
        """Test joining classroom with invite code."""
        invite_code = self.classroom.invite_code
        student_id = "student_789"
        
        member = self.classroom.join_with_invite(
            invite_code, student_id, "bob", "Bob Wilson"
        )
        
        assert member.user_id == student_id
        assert member.role == UserRole.STUDENT
        assert len(self.classroom.members) == 2
        
    def test_invalid_invite_code(self):
        """Test joining with invalid invite code."""
        with pytest.raises(ValueError, match="Invalid invite code"):
            self.classroom.join_with_invite(
                "INVALID", "student_999", "charlie", "Charlie Brown"
            )
            
    def test_promote_to_co_teacher(self):
        """Test promoting student to co-teacher."""
        student_id = "student_456"
        self.classroom.add_member(student_id, "alice", "Alice", UserRole.STUDENT)
        
        success = self.classroom.promote_to_co_teacher(student_id, self.owner_id)
        assert success
        assert self.classroom.members[student_id].role == UserRole.CO_TEACHER
        
    def test_promote_permission_denied(self):
        """Test promotion by non-owner fails."""
        student_id = "student_456"
        co_teacher_id = "teacher_789"
        
        self.classroom.add_member(student_id, "alice", "Alice", UserRole.STUDENT)
        self.classroom.add_member(co_teacher_id, "jane", "Jane", UserRole.CO_TEACHER)
        
        with pytest.raises(PermissionError):
            self.classroom.promote_to_co_teacher(student_id, co_teacher_id)
            
    def test_create_announcement(self):
        """Test creating classroom announcements."""
        announcement = self.classroom.create_announcement(
            title="Welcome to Class",
            content="Looking forward to a great semester!",
            author_id=self.owner_id,
            priority="high"
        )
        
        assert announcement.title == "Welcome to Class"
        assert announcement.priority == "high"
        assert len(self.classroom.announcements) == 1
        
    def test_get_announcements_filtering(self):
        """Test announcement filtering by role."""
        # Create announcements for different roles
        student_announcement = self.classroom.create_announcement(
            "Student Info", "Info for students", self.owner_id,
            target_roles={UserRole.STUDENT}
        )
        
        teacher_announcement = self.classroom.create_announcement(
            "Teacher Info", "Info for teachers", self.owner_id,
            target_roles={UserRole.OWNER, UserRole.CO_TEACHER}
        )
        
        # Add student
        student_id = "student_123"
        self.classroom.add_member(student_id, "student", "Student", UserRole.STUDENT)
        
        # Check student sees only student announcement
        student_announcements = self.classroom.get_announcements(student_id)
        assert len(student_announcements) == 1
        assert student_announcements[0].title == "Student Info"
        
        # Check teacher sees both
        teacher_announcements = self.classroom.get_announcements(self.owner_id)
        assert len(teacher_announcements) == 2


class TestAssignmentManager:
    """Test cases for Assignment management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classroom_id = "classroom_123"
        self.teacher_id = "teacher_456"
        self.student_id = "student_789"
        self.assignment_manager = AssignmentManager(self.classroom_id)
        
    def test_create_assignment(self):
        """Test basic assignment creation."""
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
        assignment = self.assignment_manager.create_assignment(
            title="Python Homework 1",
            description="Complete exercises 1-5",
            assignment_type=AssignmentType.HOMEWORK,
            created_by=self.teacher_id,
            due_date=due_date,
            max_points=100.0
        )
        
        assert assignment.title == "Python Homework 1"
        assert assignment.assignment_type == AssignmentType.HOMEWORK
        assert assignment.max_points == 100.0
        assert assignment.due_date == due_date
        
    def test_create_quiz(self):
        """Test quiz creation with questions."""
        questions = [
            QuizQuestion(
                question="What is 2+2?",
                question_type="multiple_choice",
                options=["3", "4", "5", "6"],
                correct_answer="4",
                points=10.0
            ),
            QuizQuestion(
                question="Python is interpreted",
                question_type="true_false", 
                correct_answer="true",
                points=10.0
            )
        ]
        
        quiz = self.assignment_manager.create_quiz(
            title="Python Basics Quiz",
            created_by=self.teacher_id,
            questions=questions,
            time_limit_minutes=30
        )
        
        assert quiz.assignment_type == AssignmentType.QUIZ
        assert len(quiz.quiz_questions) == 2
        assert quiz.max_points == 20.0
        assert quiz.auto_grade is True
        
    def test_publish_assignment(self):
        """Test publishing assignment to students."""
        assignment = self.assignment_manager.create_assignment(
            "Test Assignment", "Description", AssignmentType.HOMEWORK, self.teacher_id
        )
        
        success = self.assignment_manager.publish_assignment(
            assignment.id, self.teacher_id, {self.student_id}
        )
        
        assert success
        assert assignment.published is True
        assert self.student_id in assignment.assigned_students
        
    def test_submit_assignment(self):
        """Test assignment submission."""
        # Create and publish assignment
        assignment = self.assignment_manager.create_assignment(
            "Test Assignment", "Description", AssignmentType.HOMEWORK, self.teacher_id
        )
        self.assignment_manager.publish_assignment(assignment.id, self.teacher_id)
        
        # Submit assignment
        submission = self.assignment_manager.submit_assignment(
            assignment_id=assignment.id,
            student_id=self.student_id,
            content={"text": "My solution to the homework"},
            attachments=["solution.py"]
        )
        
        assert submission.student_id == self.student_id
        assert submission.status == SubmissionStatus.SUBMITTED
        assert submission.content["text"] == "My solution to the homework"
        
    def test_late_submission(self):
        """Test late assignment submission."""
        # Create assignment with past due date
        past_due = datetime.now(timezone.utc) - timedelta(hours=1)
        assignment = self.assignment_manager.create_assignment(
            "Late Assignment", "Description", AssignmentType.HOMEWORK, 
            self.teacher_id, due_date=past_due
        )
        self.assignment_manager.publish_assignment(assignment.id, self.teacher_id)
        
        submission = self.assignment_manager.submit_assignment(
            assignment.id, self.student_id, {"text": "Late submission"}
        )
        
        assert submission.status == SubmissionStatus.LATE
        
    def test_auto_grade_quiz(self):
        """Test automatic quiz grading."""
        # Create quiz
        questions = [
            QuizQuestion(
                question="What is 2+2?",
                options=["3", "4", "5"],
                correct_answer="4",
                points=10.0
            )
        ]
        quiz = self.assignment_manager.create_quiz(
            "Auto-Grade Quiz", self.teacher_id, questions
        )
        self.assignment_manager.publish_assignment(quiz.id, self.teacher_id)
        
        # Submit answers
        submission = self.assignment_manager.submit_assignment(
            quiz.id, self.student_id, 
            {"answers": {questions[0].id: "4"}}
        )
        
        assert submission.auto_graded is True
        assert submission.grade == 10.0
        assert submission.status == SubmissionStatus.GRADED
        
    def test_manual_grading(self):
        """Test manual assignment grading."""
        assignment = self.assignment_manager.create_assignment(
            "Essay Assignment", "Write an essay", AssignmentType.ESSAY, self.teacher_id
        )
        self.assignment_manager.publish_assignment(assignment.id, self.teacher_id)
        
        # Submit assignment
        self.assignment_manager.submit_assignment(
            assignment.id, self.student_id, {"essay": "My essay content"}
        )
        
        # Grade manually
        success = self.assignment_manager.grade_submission(
            assignment.id, self.student_id, grade=85.0, 
            feedback="Good work, but could use more examples"
        )
        
        assert success
        submission = assignment.submissions[self.student_id]
        assert submission.grade == 85.0
        assert submission.feedback == "Good work, but could use more examples"
        
    def test_gradebook_generation(self):
        """Test gradebook generation."""
        # Create multiple assignments
        hw1 = self.assignment_manager.create_assignment(
            "HW1", "Homework 1", AssignmentType.HOMEWORK, self.teacher_id, 
            max_points=50, grade_category="homework"
        )
        quiz1 = self.assignment_manager.create_assignment(
            "Quiz1", "Quiz 1", AssignmentType.QUIZ, self.teacher_id,
            max_points=25, grade_category="quizzes"
        )
        
        # Publish and submit
        for assignment in [hw1, quiz1]:
            self.assignment_manager.publish_assignment(assignment.id, self.teacher_id)
            self.assignment_manager.submit_assignment(
                assignment.id, self.student_id, {"answer": "solution"}
            )
            
        # Grade submissions
        self.assignment_manager.grade_submission(hw1.id, self.student_id, 45.0)  # 90%
        self.assignment_manager.grade_submission(quiz1.id, self.student_id, 20.0)  # 80%
        
        # Generate gradebook
        gradebook = self.assignment_manager.generate_gradebook([self.student_id])
        
        assert self.student_id in gradebook["students"]
        student_data = gradebook["students"][self.student_id]
        assert "category_averages" in student_data
        assert student_data["category_averages"]["homework"] == 90.0
        assert student_data["category_averages"]["quizzes"] == 80.0


class TestDiscussionBoard:
    """Test cases for Discussion board."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classroom_id = "classroom_123"
        self.teacher_id = "teacher_456"
        self.student_id = "student_789"
        self.discussion_board = DiscussionBoard(self.classroom_id)
        
    def test_create_thread(self):
        """Test discussion thread creation."""
        thread = self.discussion_board.create_thread(
            title="Python Help",
            description="General Python questions",
            creator_id=self.teacher_id,
            category="homework",
            qa_mode=True
        )
        
        assert thread.title == "Python Help"
        assert thread.category == "homework"
        assert thread.qa_mode is True
        assert len(self.discussion_board.threads) == 1
        
    def test_create_post(self):
        """Test creating discussion posts."""
        thread = self.discussion_board.create_thread(
            "Help Thread", "Description", self.teacher_id
        )
        
        post = self.discussion_board.create_post(
            thread_id=thread.id,
            title="Need help with loops",
            content="How do I use for loops in Python?",
            author_id=self.student_id,
            post_type=PostType.QUESTION
        )
        
        assert post.title == "Need help with loops"
        assert post.post_type == PostType.QUESTION
        assert post.author_id == self.student_id
        assert thread.total_posts == 1
        
    def test_reply_to_post(self):
        """Test replying to posts."""
        thread = self.discussion_board.create_thread("Test Thread", "", self.teacher_id)
        
        question_post = self.discussion_board.create_post(
            thread.id, "Question", "How do I do X?", 
            self.student_id, post_type=PostType.QUESTION
        )
        
        reply = self.discussion_board.reply_to_post(
            thread.id, question_post.id, 
            "Here's how you do X: ...", self.teacher_id, "teacher"
        )
        
        assert reply.parent_id == question_post.id
        assert reply.post_type == PostType.ANSWER
        assert thread.total_posts == 2
        
    def test_vote_on_post(self):
        """Test voting on posts."""
        thread = self.discussion_board.create_thread("Test Thread", "", self.teacher_id)
        post = self.discussion_board.create_post(
            thread.id, "Test Post", "Content", self.student_id
        )
        
        success = self.discussion_board.vote_on_post(
            thread.id, post.id, "voter_123", "up"
        )
        
        assert success
        assert "voter_123" in post.votes
        assert post.votes["voter_123"].vote_type == "up"
        
    def test_mark_as_solution(self):
        """Test marking post as solution."""
        thread = self.discussion_board.create_thread(
            "Q&A Thread", "", self.teacher_id, qa_mode=True
        )
        
        question = self.discussion_board.create_post(
            thread.id, "Question", "How to X?", self.student_id, post_type=PostType.QUESTION
        )
        
        answer = self.discussion_board.reply_to_post(
            thread.id, question.id, "Do Y", self.teacher_id, "teacher"
        )
        
        success = self.discussion_board.mark_as_solution(
            thread.id, answer.id, self.teacher_id
        )
        
        assert success
        assert answer.is_solution is True
        assert answer.solution_confirmed_by == self.teacher_id
        
    def test_search_discussions(self):
        """Test searching through discussions."""
        thread = self.discussion_board.create_thread("Python Thread", "", self.teacher_id)
        
        self.discussion_board.create_post(
            thread.id, "Python Loops", "Question about for loops", 
            self.student_id, tags=["loops", "python"]
        )
        
        self.discussion_board.create_post(
            thread.id, "Java Arrays", "Question about arrays", self.student_id
        )
        
        results = self.discussion_board.search_discussions("python")
        
        assert len(results) == 1
        assert results[0]["thread"].id == thread.id
        assert len(results[0]["matching_posts"]) == 1


class TestPeerLearningManager:
    """Test cases for Peer Learning management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classroom_id = "classroom_123"
        self.peer_manager = PeerLearningManager(self.classroom_id)
        self.student1_id = "student_1"
        self.student2_id = "student_2"
        
    def test_create_learner_profile(self):
        """Test learner profile creation."""
        profile = self.peer_manager.create_learner_profile(
            user_id=self.student1_id,
            subjects=["python", "mathematics"],
            skill_levels={"python": 3, "mathematics": 4},
            learning_style="visual",
            availability_hours=[9, 10, 11, 14, 15, 16]
        )
        
        assert profile.user_id == self.student1_id
        assert "python" in profile.subjects
        assert profile.skill_levels["python"] == 3
        assert profile.learning_style == "visual"
        
    def test_find_study_buddies(self):
        """Test study buddy matching algorithm."""
        # Create profiles for two students
        self.peer_manager.create_learner_profile(
            self.student1_id,
            subjects=["python", "math"],
            skill_levels={"python": 2, "math": 3},
            availability_hours=[9, 10, 14, 15]
        )
        
        self.peer_manager.create_learner_profile(
            self.student2_id,
            subjects=["python", "science"],
            skill_levels={"python": 3, "science": 4},
            availability_hours=[9, 10, 11, 12]
        )
        
        matches = self.peer_manager.find_study_buddies(self.student1_id, "python")
        
        assert len(matches) == 1
        assert matches[0]["user_id"] == self.student2_id
        assert matches[0]["compatibility_score"] > 0.3
        assert "python" in matches[0]["common_subjects"]
        
    def test_create_study_buddy_pair(self):
        """Test creating study buddy pairs."""
        # Create profiles first
        self.peer_manager.create_learner_profile(self.student1_id, subjects=["python"])
        self.peer_manager.create_learner_profile(self.student2_id, subjects=["python"])
        
        buddy_pair = self.peer_manager.create_study_buddy_pair(
            self.student1_id, self.student2_id, ["python"]
        )
        
        assert buddy_pair.user1_id == self.student1_id
        assert buddy_pair.user2_id == self.student2_id
        assert "python" in buddy_pair.subjects
        assert buddy_pair.active is True
        
    def test_schedule_learning_session(self):
        """Test scheduling collaborative sessions."""
        start_time = datetime.now(timezone.utc) + timedelta(hours=2)
        session = self.peer_manager.schedule_learning_session(
            organizer_id=self.student1_id,
            title="Python Study Session",
            session_type=SessionType.STUDY_SESSION,
            subject="python",
            scheduled_start=start_time,
            duration_minutes=90
        )
        
        assert session.title == "Python Study Session"
        assert session.session_type == SessionType.STUDY_SESSION
        assert session.subject == "python"
        assert session.scheduled_duration == 90
        assert session.status == SessionStatus.SCHEDULED
        
    def test_join_learning_session(self):
        """Test joining learning sessions."""
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        session = self.peer_manager.schedule_learning_session(
            self.student1_id, "Study Session", SessionType.STUDY_SESSION,
            "python", start_time
        )
        
        success = self.peer_manager.join_learning_session(session.id, self.student2_id)
        
        assert success
        assert self.student2_id in session.participants
        assert len(session.participants) == 1
        
    def test_complete_learning_session_xp_award(self):
        """Test completing session and XP rewards."""
        # Set up session
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        session = self.peer_manager.schedule_learning_session(
            self.student1_id, "Study Session", SessionType.STUDY_SESSION,
            "python", start_time
        )
        self.peer_manager.join_learning_session(session.id, self.student2_id)
        
        # Start and complete session
        self.peer_manager.start_learning_session(session.id, self.student1_id)
        success = self.peer_manager.complete_learning_session(
            session.id, self.student1_id,
            outcomes=["Learned about loops", "Practiced debugging"],
            session_notes="Great collaborative session"
        )
        
        assert success
        assert session.status == SessionStatus.COMPLETED
        assert len(session.outcomes) == 2
        assert len(session.xp_awarded) == 2  # Both participants get XP
        
    def test_create_peer_review(self):
        """Test peer review creation."""
        review = self.peer_manager.create_peer_review(
            assignment_id="assignment_123",
            reviewer_id=self.student1_id,
            reviewee_id=self.student2_id,
            criteria=["clarity", "completeness", "accuracy"]
        )
        
        assert review.assignment_id == "assignment_123"
        assert review.reviewer_id == self.student1_id
        assert review.reviewee_id == self.student2_id
        assert len(review.criteria) == 3
        
    def test_submit_peer_review(self):
        """Test submitting peer review feedback."""
        review = self.peer_manager.create_peer_review(
            "assignment_123", self.student1_id, self.student2_id, ["clarity"]
        )
        
        success = self.peer_manager.submit_peer_review(
            review.id,
            scores={"clarity": 4.0},
            feedback="Good work overall, clear explanations",
            suggestions=["Add more examples"],
            strengths=["Well organized"]
        )
        
        assert success
        assert review.scores["clarity"] == 4.0
        assert "clear explanations" in review.feedback
        assert "Add more examples" in review.suggestions
        
    def test_create_group_project(self):
        """Test group project creation."""
        due_date = datetime.now(timezone.utc) + timedelta(days=14)
        project = self.peer_manager.create_group_project(
            title="Python Web App",
            description="Build a web application using Flask",
            creator_id=self.student1_id,
            due_date=due_date,
            max_members=3
        )
        
        assert project.title == "Python Web App"
        assert project.due_date == due_date
        assert project.max_members == 3
        assert self.student1_id in project.members
        assert project.members[self.student1_id] == ProjectRole.LEADER
        
    def test_join_group_project(self):
        """Test joining group projects."""
        project = self.peer_manager.create_group_project(
            "Test Project", "Description", self.student1_id
        )
        
        success = self.peer_manager.join_group_project(
            project.id, self.student2_id, ProjectRole.RESEARCHER
        )
        
        assert success
        assert self.student2_id in project.members
        assert project.members[self.student2_id] == ProjectRole.RESEARCHER
        assert len(project.members) == 2
        
    def test_learning_analytics(self):
        """Test comprehensive learning analytics."""
        # Create profile and some activity
        profile = self.peer_manager.create_learner_profile(
            self.student1_id, subjects=["python"], help_given_count=5
        )
        
        # Create a completed session
        start_time = datetime.now(timezone.utc) - timedelta(hours=1)
        session = self.peer_manager.schedule_learning_session(
            self.student1_id, "Past Session", SessionType.STUDY_SESSION,
            "python", start_time
        )
        session.status = SessionStatus.COMPLETED
        session.participants = [self.student1_id]
        
        analytics = self.peer_manager.get_learning_analytics(self.student1_id)
        
        assert "profile" in analytics
        assert "session_analytics" in analytics
        assert "collaboration_analytics" in analytics
        assert analytics["profile"].help_given_count == 5
        
    def test_collaboration_recommendations(self):
        """Test getting personalized recommendations."""
        # Set up profiles
        self.peer_manager.create_learner_profile(
            self.student1_id, subjects=["python"], skill_levels={"python": 2}
        )
        self.peer_manager.create_learner_profile(
            self.student2_id, subjects=["python"], skill_levels={"python": 3}
        )
        
        recommendations = self.peer_manager.get_collaboration_recommendations(self.student1_id)
        
        assert "study_buddies" in recommendations
        assert "open_sessions" in recommendations
        assert "peer_review_opportunities" in recommendations
        assert len(recommendations["study_buddies"]) > 0


class TestIntegration:
    """Integration tests between collaboration modules."""
    
    def setup_method(self):
        """Set up integrated test environment."""
        self.classroom_id = "classroom_123"
        self.teacher_id = "teacher_456"
        self.student1_id = "student_1"
        self.student2_id = "student_2"
        
        # Initialize all managers
        self.classroom = Classroom("Integration Test Class", self.teacher_id, "teacher")
        self.assignment_manager = AssignmentManager(self.classroom_id)
        self.discussion_board = DiscussionBoard(self.classroom_id)
        self.peer_manager = PeerLearningManager(self.classroom_id)
        
    def test_assignment_discussion_integration(self):
        """Test integration between assignments and discussions."""
        # Create assignment
        assignment = self.assignment_manager.create_assignment(
            "Integrated Assignment", "Test assignment", 
            AssignmentType.PROJECT, self.teacher_id
        )
        
        # Create related discussion thread
        thread = self.discussion_board.create_thread(
            title="Assignment Help",
            description="Discuss the integrated assignment",
            creator_id=self.teacher_id,
            assignment_id=assignment.id,
            qa_mode=True
        )
        
        # Post question about assignment
        question = self.discussion_board.create_post(
            thread.id, "Need Help", "How do I approach this assignment?",
            self.student1_id, post_type=PostType.QUESTION
        )
        
        # Teacher provides answer
        answer = self.discussion_board.reply_to_post(
            thread.id, question.id,
            "Break it down into smaller steps...",
            self.teacher_id, "teacher"
        )
        
        assert thread.assignment_id == assignment.id
        assert answer.post_type == PostType.ANSWER
        
    def test_peer_learning_assignment_integration(self):
        """Test integration between peer learning and assignments."""
        # Create assignment
        assignment = self.assignment_manager.create_assignment(
            "Peer Review Assignment", "Essay assignment", 
            AssignmentType.ESSAY, self.teacher_id
        )
        self.assignment_manager.publish_assignment(assignment.id, self.teacher_id)
        
        # Students submit assignments
        self.assignment_manager.submit_assignment(
            assignment.id, self.student1_id, {"essay": "Student 1 essay"}
        )
        self.assignment_manager.submit_assignment(
            assignment.id, self.student2_id, {"essay": "Student 2 essay"}
        )
        
        # Create peer review
        review = self.peer_manager.create_peer_review(
            assignment.id, self.student1_id, self.student2_id,
            criteria=["clarity", "depth"]
        )
        
        # Submit review
        self.peer_manager.submit_peer_review(
            review.id,
            scores={"clarity": 4.0, "depth": 3.5},
            feedback="Good essay, well structured"
        )
        
        assert review.assignment_id == assignment.id
        assert review.scores["clarity"] == 4.0
        
    def test_full_collaborative_workflow(self):
        """Test complete collaborative learning workflow."""
        # 1. Set up classroom with members
        self.classroom.add_member(self.student1_id, "alice", "Alice", UserRole.STUDENT)
        self.classroom.add_member(self.student2_id, "bob", "Bob", UserRole.STUDENT)
        
        # 2. Create learner profiles
        self.peer_manager.create_learner_profile(
            self.student1_id, subjects=["python"], skill_levels={"python": 2}
        )
        self.peer_manager.create_learner_profile(
            self.student2_id, subjects=["python"], skill_levels={"python": 3}
        )
        
        # 3. Create study buddy pair
        buddy_pair = self.peer_manager.create_study_buddy_pair(
            self.student1_id, self.student2_id, ["python"]
        )
        
        # 4. Schedule collaborative session
        start_time = datetime.now(timezone.utc) + timedelta(hours=1)
        session = self.peer_manager.schedule_learning_session(
            self.student1_id, "Python Study", SessionType.STUDY_SESSION,
            "python", start_time
        )
        self.peer_manager.join_learning_session(session.id, self.student2_id)
        
        # 5. Create assignment with discussion
        assignment = self.assignment_manager.create_assignment(
            "Collaborative Project", "Group coding project",
            AssignmentType.PROJECT, self.teacher_id
        )
        
        thread = self.discussion_board.create_thread(
            "Project Discussion", "Discuss the project",
            self.teacher_id, assignment_id=assignment.id
        )
        
        # 6. Create group project
        project = self.peer_manager.create_group_project(
            "Python Calculator", "Build a calculator app",
            self.student1_id, max_members=2
        )
        self.peer_manager.join_group_project(project.id, self.student2_id)
        
        # Verify integration
        assert buddy_pair.active is True
        assert len(session.participants) == 1  # student2 joined
        assert thread.assignment_id == assignment.id
        assert len(project.members) == 2
        assert self.student1_id in project.members
        assert self.student2_id in project.members


if __name__ == "__main__":
    pytest.main([__file__, "-v"])