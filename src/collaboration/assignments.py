"""
Assignment Management System

Comprehensive assignment creation, distribution, collection, and grading
system for EduAGI classrooms.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import json


class AssignmentType(Enum):
    """Types of assignments."""
    HOMEWORK = "homework"
    QUIZ = "quiz"
    PROJECT = "project"
    READING = "reading"
    ESSAY = "essay"
    PRESENTATION = "presentation"
    LAB = "lab"


class SubmissionStatus(Enum):
    """Status of student submissions."""
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    RETURNED = "returned"


class GradingStatus(Enum):
    """Status of assignment grading."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    AUTO_GRADED = "auto_graded"


@dataclass
class GradeCategory:
    """Grade book category with weighting."""
    name: str
    weight: float  # 0.0 to 1.0
    description: str = ""
    drop_lowest: int = 0  # Number of lowest scores to drop


@dataclass
class RubricCriterion:
    """Rubric criterion for essay/project grading."""
    name: str
    description: str
    max_points: float
    levels: Dict[str, Dict[str, Union[str, float]]]  # level_name -> {description, points}


@dataclass
class QuizQuestion:
    """Quiz question with auto-grading support."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    question_type: str = "multiple_choice"  # multiple_choice, true_false, short_answer, essay
    options: List[str] = field(default_factory=list)  # For multiple choice
    correct_answer: Optional[Union[str, List[str]]] = None
    points: float = 1.0
    explanation: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class Submission:
    """Student assignment submission."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assignment_id: str = ""
    student_id: str = ""
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: SubmissionStatus = SubmissionStatus.SUBMITTED
    content: Dict[str, Any] = field(default_factory=dict)  # Text, files, quiz answers
    attachments: List[str] = field(default_factory=list)  # File paths/URLs
    
    # Grading
    grade: Optional[float] = None
    max_grade: Optional[float] = None
    feedback: str = ""
    rubric_scores: Dict[str, float] = field(default_factory=dict)
    graded_by: Optional[str] = None
    graded_at: Optional[datetime] = None
    auto_graded: bool = False
    
    # Metadata
    attempt_number: int = 1
    time_spent_minutes: Optional[int] = None
    draft_saves: List[datetime] = field(default_factory=list)


@dataclass
class Assignment:
    """Assignment with full configuration and tracking."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    classroom_id: str = ""
    title: str = ""
    description: str = ""
    assignment_type: AssignmentType = AssignmentType.HOMEWORK
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Timing
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    
    # Configuration
    max_points: float = 100.0
    allow_late_submission: bool = True
    late_penalty_percent: float = 10.0  # Per day late
    max_attempts: int = 1
    time_limit_minutes: Optional[int] = None
    
    # Content
    instructions: str = ""
    resources: List[Dict[str, str]] = field(default_factory=list)  # {name, url, type}
    quiz_questions: List[QuizQuestion] = field(default_factory=list)
    rubric: List[RubricCriterion] = field(default_factory=list)
    
    # Distribution
    assigned_students: Set[str] = field(default_factory=set)  # If empty, assigned to all
    group_assignment: bool = False
    groups: Dict[str, List[str]] = field(default_factory=dict)  # group_id -> student_ids
    
    # Grading
    grading_status: GradingStatus = GradingStatus.NOT_STARTED
    auto_grade: bool = False
    release_grades_immediately: bool = False
    grade_category: Optional[str] = None
    
    # Tracking
    submissions: Dict[str, Submission] = field(default_factory=dict)  # student_id -> submission
    published: bool = False
    archived: bool = False


class AssignmentManager:
    """
    Comprehensive assignment management system.
    
    Handles assignment creation, distribution, collection, grading,
    and grade book management for EduAGI classrooms.
    """
    
    def __init__(self, classroom_id: str):
        """Initialize assignment manager for a classroom."""
        self.classroom_id = classroom_id
        self.assignments: Dict[str, Assignment] = {}
        
        # Grade book setup
        self.grade_categories: Dict[str, GradeCategory] = {
            "homework": GradeCategory("Homework", 0.3, "Daily assignments and practice"),
            "quizzes": GradeCategory("Quizzes", 0.2, "Short assessments"),
            "projects": GradeCategory("Projects", 0.3, "Long-term projects"),
            "participation": GradeCategory("Participation", 0.2, "Class participation")
        }
        
        # Templates and defaults
        self.quiz_templates: Dict[str, List[QuizQuestion]] = {}
        self.rubric_templates: Dict[str, List[RubricCriterion]] = {}

    def create_assignment(self, title: str, description: str, 
                         assignment_type: AssignmentType, created_by: str,
                         due_date: Optional[datetime] = None,
                         max_points: float = 100.0,
                         instructions: str = "",
                         **kwargs) -> Assignment:
        """Create a new assignment."""
        assignment = Assignment(
            classroom_id=self.classroom_id,
            title=title,
            description=description,
            assignment_type=assignment_type,
            created_by=created_by,
            due_date=due_date,
            max_points=max_points,
            instructions=instructions
        )
        
        # Apply additional configuration
        for key, value in kwargs.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)
                
        # Auto-configure based on type
        if assignment_type == AssignmentType.QUIZ:
            assignment.auto_grade = True
            assignment.release_grades_immediately = True
            assignment.max_attempts = 1
            assignment.time_limit_minutes = 30
            
        elif assignment_type == AssignmentType.READING:
            assignment.grade_category = "homework"
            assignment.max_points = 10.0
            
        self.assignments[assignment.id] = assignment
        return assignment

    def create_quiz(self, title: str, created_by: str, questions: List[QuizQuestion],
                   due_date: Optional[datetime] = None, time_limit_minutes: int = 30) -> Assignment:
        """Create a quiz assignment with questions."""
        assignment = self.create_assignment(
            title=title,
            description="Quiz assignment",
            assignment_type=AssignmentType.QUIZ,
            created_by=created_by,
            due_date=due_date,
            max_points=sum(q.points for q in questions),
            auto_grade=True,
            time_limit_minutes=time_limit_minutes,
            quiz_questions=questions
        )
        return assignment

    def add_quiz_question(self, assignment_id: str, question: QuizQuestion,
                         requester_id: str) -> bool:
        """Add a question to a quiz."""
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return False
            
        if assignment.assignment_type != AssignmentType.QUIZ:
            raise ValueError("Can only add questions to quiz assignments")
            
        if assignment.published:
            raise ValueError("Cannot modify published assignment")
            
        assignment.quiz_questions.append(question)
        assignment.max_points = sum(q.points for q in assignment.quiz_questions)
        return True

    def create_rubric_criterion(self, name: str, description: str, 
                              max_points: float, levels: Dict[str, Dict[str, Union[str, float]]]) -> RubricCriterion:
        """Create a rubric criterion."""
        return RubricCriterion(
            name=name,
            description=description,
            max_points=max_points,
            levels=levels
        )

    def add_rubric_to_assignment(self, assignment_id: str, rubric: List[RubricCriterion],
                               requester_id: str) -> bool:
        """Add rubric to assignment."""
        assignment = self.assignments.get(assignment_id)
        if not assignment or assignment.published:
            return False
            
        assignment.rubric = rubric
        assignment.max_points = sum(criterion.max_points for criterion in rubric)
        return True

    def publish_assignment(self, assignment_id: str, requester_id: str, 
                          assigned_students: Optional[Set[str]] = None) -> bool:
        """Publish assignment to students."""
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return False
            
        if assignment.published:
            raise ValueError("Assignment already published")
            
        # Set distribution
        if assigned_students:
            assignment.assigned_students = assigned_students
            
        # Set availability
        if not assignment.available_from:
            assignment.available_from = datetime.now(timezone.utc)
            
        assignment.published = True
        return True

    def submit_assignment(self, assignment_id: str, student_id: str, 
                         content: Dict[str, Any], attachments: List[str] = None) -> Submission:
        """Submit assignment solution."""
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            raise ValueError("Assignment not found")
            
        if not assignment.published:
            raise ValueError("Assignment not published")
            
        # Check if student can submit
        now = datetime.now(timezone.utc)
        if assignment.available_from and now < assignment.available_from:
            raise ValueError("Assignment not yet available")
            
        if assignment.available_until and now > assignment.available_until:
            raise ValueError("Assignment no longer available")
            
        # Check existing submission
        existing = assignment.submissions.get(student_id)
        if existing and existing.attempt_number >= assignment.max_attempts:
            raise ValueError("Maximum attempts exceeded")
            
        # Determine submission status
        status = SubmissionStatus.SUBMITTED
        if assignment.due_date and now > assignment.due_date:
            status = SubmissionStatus.LATE
            
        # Create submission
        attempt_number = existing.attempt_number + 1 if existing else 1
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student_id,
            status=status,
            content=content,
            attachments=attachments or [],
            attempt_number=attempt_number
        )
        
        # Auto-grade if possible
        if assignment.auto_grade and assignment.assignment_type == AssignmentType.QUIZ:
            self._auto_grade_quiz(assignment, submission)
            
        assignment.submissions[student_id] = submission
        return submission

    def _auto_grade_quiz(self, assignment: Assignment, submission: Submission) -> float:
        """Auto-grade a quiz submission."""
        if not assignment.quiz_questions:
            return 0.0
            
        total_score = 0.0
        max_score = 0.0
        
        answers = submission.content.get("answers", {})
        
        for question in assignment.quiz_questions:
            max_score += question.points
            student_answer = answers.get(question.id, "")
            
            if question.question_type in ["multiple_choice", "true_false"]:
                if student_answer == question.correct_answer:
                    total_score += question.points
            elif question.question_type == "short_answer":
                # Simple string matching (could be enhanced with fuzzy matching)
                if isinstance(question.correct_answer, list):
                    if any(ans.lower() in student_answer.lower() 
                          for ans in question.correct_answer):
                        total_score += question.points
                elif question.correct_answer and question.correct_answer.lower() in student_answer.lower():
                    total_score += question.points
                    
        # Apply late penalty
        if submission.status == SubmissionStatus.LATE and assignment.due_date:
            days_late = (submission.submitted_at - assignment.due_date).days
            penalty = min(assignment.late_penalty_percent * days_late, 100.0)
            total_score *= (1.0 - penalty / 100.0)
            
        submission.grade = total_score
        submission.max_grade = max_score
        submission.auto_graded = True
        submission.graded_at = datetime.now(timezone.utc)
        submission.status = SubmissionStatus.GRADED
        
        return total_score

    def grade_submission(self, assignment_id: str, student_id: str, 
                        grade: float, feedback: str = "", 
                        rubric_scores: Dict[str, float] = None,
                        graded_by: str = "") -> bool:
        """Manually grade a submission."""
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return False
            
        submission = assignment.submissions.get(student_id)
        if not submission:
            return False
            
        submission.grade = min(grade, assignment.max_points)
        submission.max_grade = assignment.max_points
        submission.feedback = feedback
        submission.rubric_scores = rubric_scores or {}
        submission.graded_by = graded_by
        submission.graded_at = datetime.now(timezone.utc)
        submission.status = SubmissionStatus.GRADED
        
        return True

    def bulk_grade_submissions(self, assignment_id: str, grades: Dict[str, Dict[str, Any]],
                              graded_by: str = "") -> Dict[str, bool]:
        """Bulk grade multiple submissions."""
        results = {}
        assignment = self.assignments.get(assignment_id)
        
        if not assignment:
            return {student_id: False for student_id in grades.keys()}
            
        for student_id, grade_data in grades.items():
            success = self.grade_submission(
                assignment_id=assignment_id,
                student_id=student_id,
                grade=grade_data.get("grade", 0),
                feedback=grade_data.get("feedback", ""),
                rubric_scores=grade_data.get("rubric_scores", {}),
                graded_by=graded_by
            )
            results[student_id] = success
            
        return results

    def get_student_submissions(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all submissions for a student."""
        submissions = []
        for assignment in self.assignments.values():
            if student_id in assignment.submissions:
                submission = assignment.submissions[student_id]
                submissions.append({
                    "assignment_id": assignment.id,
                    "assignment_title": assignment.title,
                    "assignment_type": assignment.assignment_type.value,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                    "submission": submission,
                    "grade_percentage": (submission.grade / submission.max_grade * 100) 
                                      if submission.grade and submission.max_grade else None
                })
        
        return sorted(submissions, key=lambda x: x["submission"].submitted_at, reverse=True)

    def get_assignment_statistics(self, assignment_id: str) -> Dict[str, Any]:
        """Get statistics for an assignment."""
        assignment = self.assignments.get(assignment_id)
        if not assignment:
            return {}
            
        total_assigned = len(assignment.assigned_students) if assignment.assigned_students else 0
        submissions = list(assignment.submissions.values())
        
        submitted_count = len([s for s in submissions if s.status != SubmissionStatus.NOT_SUBMITTED])
        graded_count = len([s for s in submissions if s.status == SubmissionStatus.GRADED])
        late_count = len([s for s in submissions if s.status == SubmissionStatus.LATE])
        
        grades = [s.grade for s in submissions if s.grade is not None]
        avg_grade = sum(grades) / len(grades) if grades else 0.0
        
        return {
            "assignment_id": assignment_id,
            "total_assigned": total_assigned,
            "submitted_count": submitted_count,
            "graded_count": graded_count,
            "late_count": late_count,
            "submission_rate": (submitted_count / total_assigned * 100) if total_assigned else 0,
            "average_grade": avg_grade,
            "grade_distribution": self._calculate_grade_distribution(grades),
            "needs_grading": submitted_count - graded_count
        }

    def _calculate_grade_distribution(self, grades: List[float]) -> Dict[str, int]:
        """Calculate grade distribution."""
        if not grades:
            return {}
            
        distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        
        for grade in grades:
            percentage = grade
            if grade <= 1.0:  # Assume normalized to 1.0
                percentage *= 100
                
            if percentage >= 90:
                distribution["A"] += 1
            elif percentage >= 80:
                distribution["B"] += 1
            elif percentage >= 70:
                distribution["C"] += 1
            elif percentage >= 60:
                distribution["D"] += 1
            else:
                distribution["F"] += 1
                
        return distribution

    def generate_gradebook(self, student_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate complete gradebook for the classroom."""
        gradebook = {
            "classroom_id": self.classroom_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "categories": {name: {
                "weight": cat.weight,
                "description": cat.description,
                "drop_lowest": cat.drop_lowest
            } for name, cat in self.grade_categories.items()},
            "students": {}
        }
        
        # Get all students from assignments
        all_students = set()
        for assignment in self.assignments.values():
            all_students.update(assignment.submissions.keys())
            
        target_students = student_ids if student_ids else list(all_students)
        
        for student_id in target_students:
            student_grades = {}
            category_totals = {cat: [] for cat in self.grade_categories.keys()}
            
            for assignment in self.assignments.values():
                if not assignment.published:
                    continue
                    
                submission = assignment.submissions.get(student_id)
                grade_info = {
                    "assignment_id": assignment.id,
                    "title": assignment.title,
                    "type": assignment.assignment_type.value,
                    "max_points": assignment.max_points,
                    "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                    "grade": submission.grade if submission else None,
                    "percentage": (submission.grade / assignment.max_points * 100) 
                                 if submission and submission.grade else None,
                    "status": submission.status.value if submission else "not_submitted",
                    "late": submission.status == SubmissionStatus.LATE if submission else False
                }
                
                student_grades[assignment.id] = grade_info
                
                # Add to category total
                category = assignment.grade_category or "homework"
                if submission and submission.grade is not None:
                    category_totals[category].append(submission.grade / assignment.max_points)
                    
            # Calculate category averages
            category_averages = {}
            for category, grades in category_totals.items():
                if grades:
                    # Apply drop lowest if configured
                    drop_count = self.grade_categories[category].drop_lowest
                    if drop_count > 0 and len(grades) > drop_count:
                        grades = sorted(grades, reverse=True)[:-drop_count]
                    category_averages[category] = sum(grades) / len(grades) * 100
                else:
                    category_averages[category] = 0.0
                    
            # Calculate overall grade
            overall_grade = sum(avg * self.grade_categories[cat].weight 
                              for cat, avg in category_averages.items())
            
            gradebook["students"][student_id] = {
                "assignments": student_grades,
                "category_averages": category_averages,
                "overall_grade": overall_grade,
                "letter_grade": self._get_letter_grade(overall_grade)
            }
            
        return gradebook

    def _get_letter_grade(self, percentage: float) -> str:
        """Convert percentage to letter grade."""
        if percentage >= 97:
            return "A+"
        elif percentage >= 93:
            return "A"
        elif percentage >= 90:
            return "A-"
        elif percentage >= 87:
            return "B+"
        elif percentage >= 83:
            return "B"
        elif percentage >= 80:
            return "B-"
        elif percentage >= 77:
            return "C+"
        elif percentage >= 73:
            return "C"
        elif percentage >= 70:
            return "C-"
        elif percentage >= 67:
            return "D+"
        elif percentage >= 65:
            return "D"
        elif percentage >= 60:
            return "D-"
        else:
            return "F"

    def get_overdue_assignments(self) -> List[Dict[str, Any]]:
        """Get assignments past due date with incomplete submissions."""
        overdue = []
        now = datetime.now(timezone.utc)
        
        for assignment in self.assignments.values():
            if (assignment.published and assignment.due_date and 
                assignment.due_date < now):
                
                missing_submissions = []
                if assignment.assigned_students:
                    for student_id in assignment.assigned_students:
                        if student_id not in assignment.submissions:
                            missing_submissions.append(student_id)
                
                if missing_submissions:
                    overdue.append({
                        "assignment": assignment,
                        "days_overdue": (now - assignment.due_date).days,
                        "missing_submissions": missing_submissions
                    })
                    
        return sorted(overdue, key=lambda x: x["days_overdue"], reverse=True)

    def send_reminder_notifications(self, assignment_id: str) -> List[str]:
        """Generate reminder notifications for assignment."""
        assignment = self.assignments.get(assignment_id)
        if not assignment or not assignment.published:
            return []
            
        notifications = []
        now = datetime.now(timezone.utc)
        
        # Due soon reminders
        if assignment.due_date:
            time_until_due = assignment.due_date - now
            if timedelta(hours=1) <= time_until_due <= timedelta(hours=24):
                for student_id in assignment.assigned_students or []:
                    if student_id not in assignment.submissions:
                        notifications.append({
                            "type": "assignment_due_soon",
                            "student_id": student_id,
                            "assignment_id": assignment_id,
                            "title": assignment.title,
                            "due_in_hours": int(time_until_due.total_seconds() / 3600)
                        })
                        
        return notifications