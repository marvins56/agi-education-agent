"""
AssessmentGenerator: Comprehensive assessment creation system for EduAGI.

Generates grade-appropriate assessments with multiple question types,
distractor generation, and automatic answer key creation for East African
education contexts.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import random

from .engine import Topic, Subject, DifficultyLevel, LearningObjective


class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    FILL_IN_BLANK = "fill_in_blank"
    MATCHING = "matching"
    ESSAY = "essay"
    PRACTICAL = "practical"
    ORAL = "oral"


class AssessmentType(Enum):
    DIAGNOSTIC = "diagnostic"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    QUIZ = "quiz"
    TEST = "test"
    EXAMINATION = "examination"


@dataclass
class Question:
    """Individual assessment question."""
    id: str
    type: QuestionType
    question_text: str
    difficulty: DifficultyLevel
    points: int = 1
    
    # Multiple choice specific
    options: List[str] = field(default_factory=list)
    correct_answer: str = ""
    
    # Fill in blank specific  
    blanks: List[str] = field(default_factory=list)
    
    # Matching specific
    left_items: List[str] = field(default_factory=list)
    right_items: List[str] = field(default_factory=list)
    correct_matches: Dict[str, str] = field(default_factory=dict)
    
    # Answer key and rubric
    answer_key: str = ""
    rubric: List[str] = field(default_factory=list)
    explanation: str = ""
    
    # Metadata
    learning_objective_id: str = ""
    estimated_time_minutes: int = 2
    tags: List[str] = field(default_factory=list)


@dataclass
class AssessmentSection:
    """Section of an assessment with related questions."""
    name: str
    instructions: str
    questions: List[Question] = field(default_factory=list)
    total_points: int = 0
    time_limit_minutes: int = 0
    
    def add_question(self, question: Question):
        """Add a question to this section."""
        self.questions.append(question)
        self.total_points += question.points
        self.time_limit_minutes += question.estimated_time_minutes


@dataclass
class Assessment:
    """Complete assessment with all questions and metadata."""
    id: str
    title: str
    topic_id: str
    subject: Subject
    grade_level: int
    assessment_type: AssessmentType
    difficulty: DifficultyLevel
    
    sections: List[AssessmentSection] = field(default_factory=list)
    
    # Assessment metadata
    total_points: int = 0
    time_limit_minutes: int = 0
    instructions: str = ""
    materials_needed: List[str] = field(default_factory=list)
    
    # Grading information
    grading_scale: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # Grade: (min_points, max_points)
    answer_key: Dict[str, str] = field(default_factory=dict)
    
    # Accessibility and variants
    accessibility_adaptations: Dict[str, str] = field(default_factory=dict)
    language_variants: Dict[str, str] = field(default_factory=dict)
    
    def calculate_totals(self):
        """Calculate total points and time for the assessment."""
        total_points = 0
        total_time = 0
        for section in self.sections:
            total_points += section.total_points
            total_time += section.time_limit_minutes
        self.total_points = total_points
        self.time_limit_minutes = total_time
    
    def generate_answer_key(self):
        """Generate complete answer key for the assessment."""
        answer_key = {}
        for section in self.sections:
            for question in section.questions:
                if question.type == QuestionType.MULTIPLE_CHOICE:
                    answer_key[question.id] = question.correct_answer
                elif question.type == QuestionType.TRUE_FALSE:
                    answer_key[question.id] = question.correct_answer
                elif question.type in [QuestionType.SHORT_ANSWER, QuestionType.ESSAY]:
                    answer_key[question.id] = question.answer_key
                elif question.type == QuestionType.FILL_IN_BLANK:
                    answer_key[question.id] = ", ".join(question.blanks)
                elif question.type == QuestionType.MATCHING:
                    answer_key[question.id] = str(question.correct_matches)
        self.answer_key = answer_key


class AssessmentGenerator:
    """
    Advanced assessment generation system for East African curricula.
    
    Creates grade-appropriate assessments with multiple question types,
    automatic distractor generation, and comprehensive answer keys.
    """
    
    def __init__(self):
        self.question_templates = self._initialize_question_templates()
        self.distractor_generators = self._initialize_distractor_generators()
        self.grading_scales = self._initialize_grading_scales()
        self.assessment_criteria = self._initialize_assessment_criteria()
    
    def generate_assessment(self, topic: Topic, assessment_type: AssessmentType = AssessmentType.QUIZ,
                          difficulty: Optional[DifficultyLevel] = None,
                          question_count: int = 10, time_limit: int = 30) -> Assessment:
        """
        Generate a complete assessment for the given topic.
        
        Args:
            topic: The curriculum topic to assess
            assessment_type: Type of assessment to create
            difficulty: Override difficulty level
            question_count: Number of questions to generate
            time_limit: Time limit in minutes
            
        Returns:
            Complete Assessment object with questions and answer key
        """
        if difficulty is None:
            difficulty = topic.difficulty_progression[0] if topic.difficulty_progression else DifficultyLevel.BEGINNER
        
        assessment_id = f"assessment_{topic.id}_{assessment_type.value}_{difficulty.value}"
        
        assessment = Assessment(
            id=assessment_id,
            title=self._generate_assessment_title(topic, assessment_type),
            topic_id=topic.id,
            subject=topic.subject,
            grade_level=topic.grade_level,
            assessment_type=assessment_type,
            difficulty=difficulty,
            instructions=self._generate_instructions(assessment_type, topic.grade_level),
            materials_needed=self._get_assessment_materials(topic.subject),
            grading_scale=self._get_grading_scale(topic.grade_level)
        )
        
        # Create assessment sections based on type
        if assessment_type == AssessmentType.QUIZ:
            self._create_quiz_sections(assessment, topic, question_count)
        elif assessment_type == AssessmentType.TEST:
            self._create_test_sections(assessment, topic, question_count)
        elif assessment_type == AssessmentType.EXAMINATION:
            self._create_exam_sections(assessment, topic, question_count)
        else:
            self._create_default_sections(assessment, topic, question_count)
        
        # Add accessibility features
        self._add_accessibility_features(assessment)
        
        # Calculate totals and generate answer key
        assessment.calculate_totals()
        assessment.generate_answer_key()
        
        return assessment
    
    def _generate_assessment_title(self, topic: Topic, assessment_type: AssessmentType) -> str:
        """Generate appropriate title for the assessment."""
        type_titles = {
            AssessmentType.QUIZ: "Quiz",
            AssessmentType.TEST: "Test", 
            AssessmentType.EXAMINATION: "Examination",
            AssessmentType.DIAGNOSTIC: "Diagnostic Assessment",
            AssessmentType.FORMATIVE: "Progress Check",
            AssessmentType.SUMMATIVE: "Unit Assessment"
        }
        
        type_title = type_titles.get(assessment_type, "Assessment")
        return f"{topic.name} {type_title} - Grade {topic.grade_level}"
    
    def _generate_instructions(self, assessment_type: AssessmentType, grade_level: int) -> str:
        """Generate appropriate instructions for the assessment."""
        base_instructions = {
            AssessmentType.QUIZ: "Answer all questions to the best of your ability. Choose the best answer for multiple choice questions.",
            AssessmentType.TEST: "Read each question carefully. Show your work where appropriate. Answer all questions.",
            AssessmentType.EXAMINATION: "This is a formal examination. Read all instructions carefully. Manage your time wisely.",
        }
        
        instruction = base_instructions.get(assessment_type, "Answer all questions carefully.")
        
        if grade_level <= 3:
            instruction += " Ask your teacher if you need help understanding a question."
        elif grade_level <= 7:
            instruction += " Take your time and think before answering."
        else:
            instruction += " Plan your answers and review your work before submitting."
        
        return instruction
    
    def _get_assessment_materials(self, subject: Subject) -> List[str]:
        """Get materials needed for subject-specific assessments."""
        base_materials = ["pencil", "eraser", "question paper"]
        
        subject_materials = {
            Subject.MATHEMATICS: ["calculator (if allowed)", "ruler", "protractor", "compass"],
            Subject.SCIENCE: ["periodic table", "formula sheet", "safety guidelines"],
            Subject.GEOGRAPHY: ["atlas", "maps", "measuring tools"],
            Subject.ICT: ["computer access", "software tools"],
            Subject.ENGLISH: ["dictionary (if allowed)"],
            Subject.HISTORY: ["timeline reference"]
        }
        
        return base_materials + subject_materials.get(subject, [])
    
    def _create_quiz_sections(self, assessment: Assessment, topic: Topic, question_count: int):
        """Create sections for a quiz-type assessment."""
        # Single section for quizzes
        section = AssessmentSection(
            name="Quiz Questions",
            instructions="Answer all questions. Choose the best answer."
        )
        
        # Generate mix of question types appropriate for grade level
        question_distribution = self._get_question_distribution(topic.grade_level, question_count, "quiz")
        
        questions = self._generate_questions_by_type(topic, question_distribution)
        for question in questions:
            section.add_question(question)
        
        assessment.sections.append(section)
    
    def _create_test_sections(self, assessment: Assessment, topic: Topic, question_count: int):
        """Create sections for a test-type assessment."""
        # Part A: Multiple Choice/Objective Questions
        objective_section = AssessmentSection(
            name="Part A: Objective Questions",
            instructions="Choose the best answer for each question."
        )
        
        # Part B: Short Answer Questions
        short_answer_section = AssessmentSection(
            name="Part B: Short Answer Questions",
            instructions="Answer questions in complete sentences."
        )
        
        # Distribute questions between sections
        objective_count = int(question_count * 0.7)  # 70% objective
        short_answer_count = question_count - objective_count
        
        # Generate objective questions
        objective_distribution = {
            QuestionType.MULTIPLE_CHOICE: int(objective_count * 0.6),
            QuestionType.TRUE_FALSE: int(objective_count * 0.3),
            QuestionType.FILL_IN_BLANK: objective_count - int(objective_count * 0.9)
        }
        
        objective_questions = self._generate_questions_by_type(topic, objective_distribution)
        for question in objective_questions:
            objective_section.add_question(question)
        
        # Generate short answer questions
        short_answer_distribution = {QuestionType.SHORT_ANSWER: short_answer_count}
        short_answer_questions = self._generate_questions_by_type(topic, short_answer_distribution)
        for question in short_answer_questions:
            short_answer_section.add_question(question)
        
        assessment.sections.extend([objective_section, short_answer_section])
    
    def _create_exam_sections(self, assessment: Assessment, topic: Topic, question_count: int):
        """Create sections for an examination-type assessment."""
        # More comprehensive structure for exams
        sections = [
            ("Part A: Multiple Choice", "Choose the best answer", 0.4),
            ("Part B: Short Answer", "Answer in complete sentences", 0.3),
            ("Part C: Essay Questions", "Write detailed responses", 0.3)
        ]
        
        for section_name, section_instructions, proportion in sections:
            section = AssessmentSection(name=section_name, instructions=section_instructions)
            section_question_count = int(question_count * proportion)
            
            # Determine question types for each section
            if "Multiple Choice" in section_name:
                distribution = {QuestionType.MULTIPLE_CHOICE: section_question_count}
            elif "Short Answer" in section_name:
                distribution = {QuestionType.SHORT_ANSWER: section_question_count}
            else:  # Essay
                distribution = {QuestionType.ESSAY: section_question_count}
            
            questions = self._generate_questions_by_type(topic, distribution)
            for question in questions:
                section.add_question(question)
            
            assessment.sections.append(section)
    
    def _create_default_sections(self, assessment: Assessment, topic: Topic, question_count: int):
        """Create default sections for other assessment types."""
        section = AssessmentSection(
            name="Assessment Questions",
            instructions="Answer all questions to demonstrate your understanding."
        )
        
        distribution = self._get_question_distribution(topic.grade_level, question_count, "mixed")
        questions = self._generate_questions_by_type(topic, distribution)
        
        for question in questions:
            section.add_question(question)
        
        assessment.sections.append(section)
    
    def _get_question_distribution(self, grade_level: int, total_questions: int, assessment_style: str) -> Dict[QuestionType, int]:
        """Get distribution of question types based on grade level and style."""
        if grade_level <= 3:  # Early primary
            return {
                QuestionType.MULTIPLE_CHOICE: int(total_questions * 0.4),
                QuestionType.TRUE_FALSE: int(total_questions * 0.3),
                QuestionType.FILL_IN_BLANK: int(total_questions * 0.2),
                QuestionType.PRACTICAL: total_questions - int(total_questions * 0.9)
            }
        elif grade_level <= 7:  # Upper primary
            return {
                QuestionType.MULTIPLE_CHOICE: int(total_questions * 0.35),
                QuestionType.TRUE_FALSE: int(total_questions * 0.2),
                QuestionType.SHORT_ANSWER: int(total_questions * 0.25),
                QuestionType.FILL_IN_BLANK: int(total_questions * 0.15),
                QuestionType.MATCHING: total_questions - int(total_questions * 0.95)
            }
        else:  # Secondary
            return {
                QuestionType.MULTIPLE_CHOICE: int(total_questions * 0.3),
                QuestionType.SHORT_ANSWER: int(total_questions * 0.3),
                QuestionType.ESSAY: int(total_questions * 0.2),
                QuestionType.FILL_IN_BLANK: int(total_questions * 0.1),
                QuestionType.MATCHING: total_questions - int(total_questions * 0.9)
            }
    
    def _generate_questions_by_type(self, topic: Topic, distribution: Dict[QuestionType, int]) -> List[Question]:
        """Generate questions according to specified distribution."""
        questions = []
        question_counter = 1
        
        for question_type, count in distribution.items():
            for i in range(count):
                question_id = f"q_{topic.id}_{question_counter:03d}"
                
                if question_type == QuestionType.MULTIPLE_CHOICE:
                    question = self._generate_mcq(question_id, topic)
                elif question_type == QuestionType.TRUE_FALSE:
                    question = self._generate_true_false(question_id, topic)
                elif question_type == QuestionType.SHORT_ANSWER:
                    question = self._generate_short_answer(question_id, topic)
                elif question_type == QuestionType.FILL_IN_BLANK:
                    question = self._generate_fill_blank(question_id, topic)
                elif question_type == QuestionType.MATCHING:
                    question = self._generate_matching(question_id, topic)
                elif question_type == QuestionType.ESSAY:
                    question = self._generate_essay(question_id, topic)
                else:  # PRACTICAL
                    question = self._generate_practical(question_id, topic)
                
                questions.append(question)
                question_counter += 1
        
        return questions
    
    def _generate_mcq(self, question_id: str, topic: Topic) -> Question:
        """Generate a multiple choice question."""
        templates = self._get_mcq_templates(topic.subject)
        template = random.choice(templates)
        
        question_text = template.format(topic_name=topic.name.lower())
        
        # Generate options with one correct answer and distractors
        correct_answer = self._generate_correct_answer(topic, "mcq")
        distractors = self._generate_distractors(topic, correct_answer, count=3)
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        correct_letter = chr(65 + options.index(correct_answer))  # A, B, C, D
        
        return Question(
            id=question_id,
            type=QuestionType.MULTIPLE_CHOICE,
            question_text=question_text,
            difficulty=topic.difficulty_progression[0] if topic.difficulty_progression else DifficultyLevel.BEGINNER,
            options=[f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)],
            correct_answer=correct_letter,
            answer_key=f"{correct_letter}) {correct_answer}",
            explanation=f"The correct answer is {correct_letter} because {self._generate_explanation(topic, correct_answer)}",
            estimated_time_minutes=2 if topic.grade_level <= 7 else 3,
            points=1
        )
    
    def _generate_true_false(self, question_id: str, topic: Topic) -> Question:
        """Generate a true/false question."""
        templates = self._get_tf_templates(topic.subject)
        template = random.choice(templates)
        
        is_true = random.choice([True, False])
        question_text = template.format(topic_name=topic.name.lower(), is_true=is_true)
        
        return Question(
            id=question_id,
            type=QuestionType.TRUE_FALSE,
            question_text=question_text,
            difficulty=DifficultyLevel.BEGINNER,
            correct_answer="True" if is_true else "False",
            answer_key="True" if is_true else "False",
            explanation=self._generate_tf_explanation(topic, is_true),
            estimated_time_minutes=1,
            points=1
        )
    
    def _generate_short_answer(self, question_id: str, topic: Topic) -> Question:
        """Generate a short answer question."""
        templates = self._get_short_answer_templates(topic.subject)
        template = random.choice(templates)
        
        question_text = template.format(topic_name=topic.name.lower())
        answer_key = self._generate_short_answer_key(topic)
        
        return Question(
            id=question_id,
            type=QuestionType.SHORT_ANSWER,
            question_text=question_text,
            difficulty=DifficultyLevel.INTERMEDIATE,
            answer_key=answer_key,
            rubric=[
                "Full credit: Complete and accurate answer",
                "Partial credit: Mostly correct with minor errors", 
                "No credit: Incorrect or missing answer"
            ],
            estimated_time_minutes=3 if topic.grade_level <= 7 else 5,
            points=2
        )
    
    def _generate_fill_blank(self, question_id: str, topic: Topic) -> Question:
        """Generate a fill-in-the-blank question."""
        sentence = f"The key concept in {topic.name.lower()} is _____ and it involves _____."
        blanks = self._generate_fill_blank_answers(topic)
        
        return Question(
            id=question_id,
            type=QuestionType.FILL_IN_BLANK,
            question_text=sentence,
            difficulty=DifficultyLevel.BEGINNER,
            blanks=blanks,
            answer_key=", ".join(blanks),
            estimated_time_minutes=2,
            points=len(blanks)
        )
    
    def _generate_matching(self, question_id: str, topic: Topic) -> Question:
        """Generate a matching question."""
        left_items, right_items, matches = self._generate_matching_pairs(topic)
        
        return Question(
            id=question_id,
            type=QuestionType.MATCHING,
            question_text=f"Match the following items related to {topic.name.lower()}:",
            difficulty=DifficultyLevel.INTERMEDIATE,
            left_items=left_items,
            right_items=right_items,
            correct_matches=matches,
            answer_key=str(matches),
            estimated_time_minutes=4,
            points=len(matches)
        )
    
    def _generate_essay(self, question_id: str, topic: Topic) -> Question:
        """Generate an essay question."""
        prompts = [
            f"Explain the importance of {topic.name.lower()} and provide examples.",
            f"Discuss how {topic.name.lower()} relates to everyday life.",
            f"Compare and contrast different aspects of {topic.name.lower()}."
        ]
        
        question_text = random.choice(prompts)
        
        return Question(
            id=question_id,
            type=QuestionType.ESSAY,
            question_text=question_text,
            difficulty=DifficultyLevel.ADVANCED,
            rubric=[
                "Excellent (4): Clear thesis, well-developed arguments, good examples",
                "Good (3): Clear main points, adequate development",
                "Satisfactory (2): Basic understanding shown, some development",
                "Needs Improvement (1): Limited understanding, minimal development"
            ],
            estimated_time_minutes=15 if topic.grade_level <= 7 else 20,
            points=4
        )
    
    def _generate_practical(self, question_id: str, topic: Topic) -> Question:
        """Generate a practical/hands-on question."""
        return Question(
            id=question_id,
            type=QuestionType.PRACTICAL,
            question_text=f"Demonstrate your understanding of {topic.name.lower()} through a practical activity.",
            difficulty=DifficultyLevel.INTERMEDIATE,
            answer_key="Practical demonstration and explanation",
            rubric=["Shows understanding through practical application"],
            estimated_time_minutes=10,
            points=3
        )
    
    def _add_accessibility_features(self, assessment: Assessment):
        """Add accessibility adaptations to the assessment."""
        assessment.accessibility_adaptations = {
            "visual_impairment": "Large print version available, audio recording of questions",
            "hearing_impairment": "Written instructions provided, visual cues used",
            "learning_differences": "Extended time available, simplified language option",
            "physical_limitations": "Alternative response methods available"
        }
    
    def _get_grading_scale(self, grade_level: int) -> Dict[str, Tuple[int, int]]:
        """Get appropriate grading scale for the grade level."""
        if grade_level <= 7:
            return {
                "Excellent": (90, 100),
                "Very Good": (80, 89),
                "Good": (70, 79),
                "Satisfactory": (60, 69),
                "Needs Improvement": (0, 59)
            }
        else:
            return {
                "A": (80, 100),
                "B": (70, 79),
                "C": (60, 69),
                "D": (50, 59),
                "F": (0, 49)
            }
    
    # Template and content generation helper methods
    def _initialize_question_templates(self) -> Dict:
        """Initialize question templates for different subjects."""
        return {}
    
    def _initialize_distractor_generators(self) -> Dict:
        """Initialize distractor generation functions."""
        return {}
    
    def _initialize_grading_scales(self) -> Dict:
        """Initialize grading scales for different contexts."""
        return {}
    
    def _initialize_assessment_criteria(self) -> Dict:
        """Initialize assessment criteria and rubrics."""
        return {}
    
    def _get_mcq_templates(self, subject: Subject) -> List[str]:
        """Get MCQ templates for the subject."""
        return [f"Which of the following best describes {{topic_name}}?"]
    
    def _get_tf_templates(self, subject: Subject) -> List[str]:
        """Get true/false templates."""
        return [f"{{topic_name}} is always the same in all situations."]
    
    def _get_short_answer_templates(self, subject: Subject) -> List[str]:
        """Get short answer templates."""
        return [f"Explain what {{topic_name}} means and why it is important."]
    
    def _generate_correct_answer(self, topic: Topic, question_type: str) -> str:
        """Generate correct answer for a question."""
        return f"The correct understanding of {topic.name.lower()}"
    
    def _generate_distractors(self, topic: Topic, correct_answer: str, count: int) -> List[str]:
        """Generate plausible but incorrect answer options."""
        distractors = []
        for i in range(count):
            distractors.append(f"Alternative explanation {i+1} for {topic.name.lower()}")
        return distractors
    
    def _generate_explanation(self, topic: Topic, answer: str) -> str:
        """Generate explanation for why an answer is correct."""
        return f"it accurately represents the key concepts in {topic.name.lower()}"
    
    def _generate_tf_explanation(self, topic: Topic, is_true: bool) -> str:
        """Generate explanation for true/false answer."""
        return f"This statement about {topic.name.lower()} is {'true' if is_true else 'false'} because..."
    
    def _generate_short_answer_key(self, topic: Topic) -> str:
        """Generate answer key for short answer questions."""
        return f"Key points about {topic.name.lower()}: definition, importance, examples"
    
    def _generate_fill_blank_answers(self, topic: Topic) -> List[str]:
        """Generate answers for fill-in-the-blank questions."""
        return ["concept", "application"]
    
    def _generate_matching_pairs(self, topic: Topic) -> Tuple[List[str], List[str], Dict[str, str]]:
        """Generate matching pairs for matching questions."""
        left = ["Term 1", "Term 2"]
        right = ["Definition A", "Definition B"]
        matches = {"Term 1": "Definition A", "Term 2": "Definition B"}
        return left, right, matches