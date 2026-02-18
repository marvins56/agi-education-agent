"""
LessonGenerator: Comprehensive lesson creation system for EduAGI.

Generates structured, adaptive lessons with multiple difficulty variants,
voice-friendly formatting, and accessibility considerations for East African
education contexts.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random

from .engine import Topic, Subject, DifficultyLevel, LearningObjective


class LessonFormat(Enum):
    STANDARD = "standard"
    VOICE_FRIENDLY = "voice_friendly"
    VISUAL = "visual"
    INTERACTIVE = "interactive"
    ACCESSIBILITY = "accessibility"


class ActivityType(Enum):
    EXPLANATION = "explanation"
    DEMONSTRATION = "demonstration"  
    PRACTICE = "practice"
    DISCUSSION = "discussion"
    EXPERIMENT = "experiment"
    GROUP_WORK = "group_work"
    INDIVIDUAL_WORK = "individual_work"
    REFLECTION = "reflection"


@dataclass
class LessonActivity:
    """Individual activity within a lesson."""
    type: ActivityType
    title: str
    content: str
    duration_minutes: int
    materials_needed: List[str] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    assessment_notes: str = ""
    accessibility_notes: str = ""


@dataclass
class LessonSection:
    """Major section of a lesson (intro, main content, etc.)"""
    name: str
    description: str
    activities: List[LessonActivity] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    duration_minutes: int = 0
    
    def add_activity(self, activity: LessonActivity):
        """Add an activity to this section."""
        self.activities.append(activity)
        self.duration_minutes += activity.duration_minutes


@dataclass
class Lesson:
    """Complete lesson structure with all components."""
    id: str
    title: str
    topic_id: str
    subject: Subject
    grade_level: int
    difficulty: DifficultyLevel
    format: LessonFormat
    
    # Core lesson sections
    introduction: LessonSection
    explanation: LessonSection
    examples: LessonSection
    practice: LessonSection
    summary: LessonSection
    
    # Lesson metadata
    duration_minutes: int = 0
    materials_needed: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    assessment_criteria: List[str] = field(default_factory=list)
    
    # Variants and accessibility
    difficulty_variants: Dict[DifficultyLevel, str] = field(default_factory=dict)
    accessibility_adaptations: Dict[str, str] = field(default_factory=dict)
    
    # Voice and interaction
    voice_prompts: List[str] = field(default_factory=list)
    interaction_cues: List[str] = field(default_factory=list)
    
    def calculate_total_duration(self):
        """Calculate total lesson duration from all sections."""
        total = 0
        for section in [self.introduction, self.explanation, self.examples, self.practice, self.summary]:
            total += section.duration_minutes
        self.duration_minutes = total
        return total
    
    def get_all_materials(self) -> List[str]:
        """Get all unique materials needed for the lesson."""
        materials = set(self.materials_needed)
        for section in [self.introduction, self.explanation, self.examples, self.practice, self.summary]:
            for activity in section.activities:
                materials.update(activity.materials_needed)
        return sorted(list(materials))


class LessonGenerator:
    """
    Advanced lesson generation system with multi-format support.
    
    Generates structured lessons optimized for different delivery methods
    including voice-based learning, visual presentations, and accessibility.
    """
    
    def __init__(self):
        self.lesson_templates = self._initialize_templates()
        self.activity_pools = self._initialize_activity_pools()
        self.voice_patterns = self._initialize_voice_patterns()
        self.accessibility_guidelines = self._initialize_accessibility_guidelines()
    
    def generate_lesson(self, topic: Topic, difficulty: DifficultyLevel = None,
                       format: LessonFormat = LessonFormat.STANDARD,
                       duration_target: int = 45) -> Lesson:
        """
        Generate a complete lesson for the given topic.
        
        Args:
            topic: The curriculum topic to create a lesson for
            difficulty: Override difficulty level (uses topic default if None)
            format: Lesson format type
            duration_target: Target lesson duration in minutes
            
        Returns:
            Complete Lesson object with all sections and activities
        """
        if difficulty is None:
            difficulty = topic.difficulty_progression[0] if topic.difficulty_progression else DifficultyLevel.BEGINNER
        
        lesson_id = f"lesson_{topic.id}_{difficulty.value}_{format.value}"
        
        # Create base lesson structure
        lesson = Lesson(
            id=lesson_id,
            title=self._generate_lesson_title(topic, difficulty),
            topic_id=topic.id,
            subject=topic.subject,
            grade_level=topic.grade_level,
            difficulty=difficulty,
            format=format,
            introduction=LessonSection("Introduction", "Lesson opening and motivation"),
            explanation=LessonSection("Explanation", "Core content delivery"),
            examples=LessonSection("Examples", "Worked examples and demonstrations"),
            practice=LessonSection("Practice", "Student practice activities"),
            summary=LessonSection("Summary", "Lesson wrap-up and assessment"),
            learning_objectives=[obj.description for obj in topic.learning_objectives],
            prerequisites=[f"Understanding of {prereq}" for prereq in topic.prerequisites]
        )
        
        # Generate content for each section
        self._generate_introduction(lesson, topic)
        self._generate_explanation(lesson, topic)
        self._generate_examples(lesson, topic)
        self._generate_practice(lesson, topic)
        self._generate_summary(lesson, topic)
        
        # Apply format-specific adaptations
        self._apply_format_adaptations(lesson)
        
        # Generate difficulty variants
        self._generate_difficulty_variants(lesson, topic)
        
        # Add accessibility adaptations
        self._add_accessibility_features(lesson)
        
        # Calculate timing and materials
        lesson.calculate_total_duration()
        lesson.materials_needed = lesson.get_all_materials()
        
        # Adjust to target duration
        self._adjust_lesson_duration(lesson, duration_target)
        
        return lesson
    
    def _generate_lesson_title(self, topic: Topic, difficulty: DifficultyLevel) -> str:
        """Generate an engaging lesson title."""
        difficulty_prefix = {
            DifficultyLevel.BEGINNER: "Introduction to",
            DifficultyLevel.INTERMEDIATE: "Exploring", 
            DifficultyLevel.ADVANCED: "Mastering",
            DifficultyLevel.EXPERT: "Advanced"
        }
        
        prefix = difficulty_prefix.get(difficulty, "Learning about")
        return f"{prefix} {topic.name}"
    
    def _generate_introduction(self, lesson: Lesson, topic: Topic):
        """Generate introduction section with hook and objectives."""
        # Welcome activity
        welcome = LessonActivity(
            type=ActivityType.DISCUSSION,
            title="Welcome and Review",
            content=f"Welcome, students! Today we're going to learn about {topic.name}. "
                   f"Let's start by thinking about what you already know about this topic.",
            duration_minutes=3,
            instructions=[
                "Greet students warmly",
                "Ask students to share what they know about the topic",
                "Connect to previous learning"
            ]
        )
        
        # Learning objectives introduction
        objectives = LessonActivity(
            type=ActivityType.EXPLANATION,
            title="Learning Goals",
            content=f"By the end of this lesson, you will be able to: "
                   + "; ".join([obj.description for obj in topic.learning_objectives[:3]]),
            duration_minutes=2,
            instructions=[
                "Present learning objectives clearly",
                "Use simple language appropriate for grade level",
                "Check for understanding"
            ]
        )
        
        # Motivation/hook activity
        hook_content = self._generate_hook_content(topic)
        hook = LessonActivity(
            type=ActivityType.DEMONSTRATION,
            title="Why This Matters",
            content=hook_content,
            duration_minutes=5,
            materials_needed=self._get_hook_materials(topic),
            instructions=[
                "Use engaging real-world examples",
                "Encourage student participation",
                "Build excitement for learning"
            ]
        )
        
        lesson.introduction.add_activity(welcome)
        lesson.introduction.add_activity(objectives)
        lesson.introduction.add_activity(hook)
    
    def _generate_explanation(self, lesson: Lesson, topic: Topic):
        """Generate core explanation section."""
        # Main concept explanation
        concept_explanation = LessonActivity(
            type=ActivityType.EXPLANATION,
            title=f"Understanding {topic.name}",
            content=self._generate_concept_explanation(topic),
            duration_minutes=15,
            materials_needed=self._get_explanation_materials(topic),
            instructions=[
                "Present content step by step",
                "Use visual aids where appropriate",
                "Check for understanding frequently",
                "Encourage questions"
            ]
        )
        
        # Interactive demonstration
        demonstration = LessonActivity(
            type=ActivityType.DEMONSTRATION,
            title="Let's See It in Action",
            content=self._generate_demonstration_content(topic),
            duration_minutes=8,
            materials_needed=["demonstration materials", "visual aids"],
            instructions=[
                "Show concrete examples",
                "Involve students in demonstration",
                "Make connections to real life"
            ]
        )
        
        lesson.explanation.add_activity(concept_explanation)
        lesson.explanation.add_activity(demonstration)
    
    def _generate_examples(self, lesson: Lesson, topic: Topic):
        """Generate worked examples section."""
        # Guided examples
        guided_examples = LessonActivity(
            type=ActivityType.EXPLANATION,
            title="Worked Examples",
            content=self._generate_worked_examples(topic),
            duration_minutes=10,
            materials_needed=["examples worksheet", "board/projector"],
            instructions=[
                "Work through examples step-by-step",
                "Think aloud to model problem-solving",
                "Invite student participation",
                "Address common misconceptions"
            ]
        )
        
        lesson.examples.add_activity(guided_examples)
    
    def _generate_practice(self, lesson: Lesson, topic: Topic):
        """Generate practice activities section."""
        # Individual practice
        individual_practice = LessonActivity(
            type=ActivityType.INDIVIDUAL_WORK,
            title="Try It Yourself",
            content=self._generate_practice_problems(topic),
            duration_minutes=12,
            materials_needed=["practice worksheets", "pencils"],
            instructions=[
                "Provide clear instructions",
                "Monitor student progress",
                "Offer support as needed",
                "Encourage peer helping"
            ]
        )
        
        # Group activity
        group_activity = LessonActivity(
            type=ActivityType.GROUP_WORK,
            title="Work Together",
            content=self._generate_group_activity(topic),
            duration_minutes=8,
            materials_needed=["group materials", "chart paper"],
            instructions=[
                "Form balanced groups",
                "Assign clear roles",
                "Facilitate collaboration",
                "Ensure all students participate"
            ]
        )
        
        lesson.practice.add_activity(individual_practice)
        lesson.practice.add_activity(group_activity)
    
    def _generate_summary(self, lesson: Lesson, topic: Topic):
        """Generate summary and assessment section."""
        # Review key points
        review = LessonActivity(
            type=ActivityType.DISCUSSION,
            title="What Did We Learn?",
            content=f"Let's review the key points about {topic.name}. "
                   + self._generate_summary_content(topic),
            duration_minutes=5,
            instructions=[
                "Ask students to summarize key learning",
                "Correct any misunderstandings",
                "Celebrate progress made"
            ]
        )
        
        # Quick assessment
        assessment = LessonActivity(
            type=ActivityType.INDIVIDUAL_WORK,
            title="Show What You Know",
            content=self._generate_quick_assessment(topic),
            duration_minutes=5,
            materials_needed=["exit tickets", "pencils"],
            instructions=[
                "Give clear assessment instructions",
                "Circulate to observe understanding",
                "Collect responses for feedback"
            ]
        )
        
        lesson.summary.add_activity(review)
        lesson.summary.add_activity(assessment)
    
    def _apply_format_adaptations(self, lesson: Lesson):
        """Apply format-specific adaptations to the lesson."""
        if lesson.format == LessonFormat.VOICE_FRIENDLY:
            self._make_voice_friendly(lesson)
        elif lesson.format == LessonFormat.VISUAL:
            self._enhance_visual_elements(lesson)
        elif lesson.format == LessonFormat.INTERACTIVE:
            self._add_interactive_elements(lesson)
        elif lesson.format == LessonFormat.ACCESSIBILITY:
            self._enhance_accessibility(lesson)
    
    def _make_voice_friendly(self, lesson: Lesson):
        """Adapt lesson for voice-based delivery."""
        lesson.voice_prompts = [
            "Welcome to today's lesson! Are you ready to learn?",
            "Let me explain this concept step by step.",
            "Now let's try an example together.",
            "It's your turn to practice!",
            "Great work! Let's summarize what we learned."
        ]
        
        lesson.interaction_cues = [
            "Say 'yes' if you understand, or 'repeat' if you'd like me to explain again.",
            "When you're ready for the next part, say 'continue'.",
            "If you have a question, say 'question' and I'll help.",
            "Say 'finished' when you complete each activity."
        ]
        
        # Add voice-specific instructions to activities
        for section in [lesson.introduction, lesson.explanation, lesson.examples, lesson.practice, lesson.summary]:
            for activity in section.activities:
                activity.accessibility_notes += " Voice delivery: Speak clearly with appropriate pauses. "
    
    def _enhance_visual_elements(self, lesson: Lesson):
        """Enhance lesson with visual elements."""
        visual_materials = [
            "colorful diagrams", "infographics", "visual aids",
            "interactive charts", "multimedia presentations"
        ]
        lesson.materials_needed.extend(visual_materials)
    
    def _add_interactive_elements(self, lesson: Lesson):
        """Add interactive components to the lesson."""
        lesson.interaction_cues.extend([
            "Students will participate in hands-on activities",
            "Use movement and gestures to reinforce learning",
            "Include games and collaborative exercises"
        ])
    
    def _enhance_accessibility(self, lesson: Lesson):
        """Add comprehensive accessibility features."""
        lesson.accessibility_adaptations = {
            "visual_impairment": "Provide audio descriptions, tactile materials, high contrast visuals",
            "hearing_impairment": "Use visual cues, written instructions, sign language support",
            "learning_differences": "Multiple presentation modes, extended time, simplified instructions",
            "physical_limitations": "Adaptive materials, flexible seating, modified activities",
            "language_barriers": "Visual supports, simplified vocabulary, translation assistance"
        }
    
    def _generate_difficulty_variants(self, lesson: Lesson, topic: Topic):
        """Generate content variants for different difficulty levels."""
        for difficulty in DifficultyLevel:
            if difficulty == DifficultyLevel.BEGINNER:
                lesson.difficulty_variants[difficulty] = "Simplified examples, more guidance, basic vocabulary"
            elif difficulty == DifficultyLevel.INTERMEDIATE:
                lesson.difficulty_variants[difficulty] = "Standard examples, moderate support, grade-level vocabulary"
            elif difficulty == DifficultyLevel.ADVANCED:
                lesson.difficulty_variants[difficulty] = "Complex examples, less guidance, advanced terminology"
            else:  # EXPERT
                lesson.difficulty_variants[difficulty] = "Challenging problems, independent work, specialized vocabulary"
    
    def _add_accessibility_features(self, lesson: Lesson):
        """Add comprehensive accessibility features."""
        lesson.assessment_criteria = [
            "Student demonstrates understanding through multiple modalities",
            "Learning objectives are met at appropriate level",
            "Student can apply knowledge in new contexts",
            "Participation shows engagement with content"
        ]
    
    def _adjust_lesson_duration(self, lesson: Lesson, target_minutes: int):
        """Adjust lesson timing to meet target duration."""
        current_duration = lesson.duration_minutes
        if current_duration > target_minutes:
            # Reduce activity durations proportionally
            reduction_factor = target_minutes / current_duration
            for section in [lesson.introduction, lesson.explanation, lesson.examples, lesson.practice, lesson.summary]:
                for activity in section.activities:
                    activity.duration_minutes = max(1, int(activity.duration_minutes * reduction_factor))
                section.duration_minutes = sum(activity.duration_minutes for activity in section.activities)
        
        lesson.calculate_total_duration()
    
    # Content generation helper methods
    def _generate_hook_content(self, topic: Topic) -> str:
        """Generate engaging hook content for the topic."""
        hooks = {
            Subject.MATHEMATICS: f"Did you know that {topic.name.lower()} is used everywhere around us? Let's discover how!",
            Subject.SCIENCE: f"Amazing! Let's explore the fascinating world of {topic.name.lower()} together!",
            Subject.ENGLISH: f"Words have power! Today we'll unlock the secrets of {topic.name.lower()}.",
            Subject.HISTORY: f"Travel back in time with me to discover {topic.name.lower()}!",
            Subject.GEOGRAPHY: f"Let's journey around the world to explore {topic.name.lower()}!",
            Subject.ICT: f"Ready to become a technology expert? Let's learn about {topic.name.lower()}!"
        }
        return hooks.get(topic.subject, f"Let's dive into the exciting world of {topic.name.lower()}!")
    
    def _get_hook_materials(self, topic: Topic) -> List[str]:
        """Get materials needed for the lesson hook."""
        return ["real-world examples", "visual props", "interactive elements"]
    
    def _generate_concept_explanation(self, topic: Topic) -> str:
        """Generate core concept explanation."""
        return f"Let me explain {topic.name} in a way that's easy to understand. {topic.description}"
    
    def _get_explanation_materials(self, topic: Topic) -> List[str]:
        """Get materials for explanation section."""
        materials = ["whiteboard/blackboard", "markers/chalk", "handouts"]
        if topic.subject == Subject.SCIENCE:
            materials.extend(["science equipment", "safety materials"])
        elif topic.subject == Subject.MATHEMATICS:
            materials.extend(["calculators", "manipulatives", "measuring tools"])
        return materials
    
    def _generate_demonstration_content(self, topic: Topic) -> str:
        """Generate demonstration content."""
        return f"Now let me show you how {topic.name.lower()} works in practice."
    
    def _generate_worked_examples(self, topic: Topic) -> str:
        """Generate worked examples content."""
        return f"Here are some examples of {topic.name.lower()} that we'll work through together."
    
    def _generate_practice_problems(self, topic: Topic) -> str:
        """Generate practice problems."""
        return f"Now it's your turn to practice {topic.name.lower()}. Try these problems:"
    
    def _generate_group_activity(self, topic: Topic) -> str:
        """Generate group activity content."""
        return f"Work with your team to explore {topic.name.lower()} through this collaborative activity."
    
    def _generate_summary_content(self, topic: Topic) -> str:
        """Generate summary content."""
        return f"Today we learned about {topic.name.lower()}. The most important things to remember are..."
    
    def _generate_quick_assessment(self, topic: Topic) -> str:
        """Generate quick assessment questions."""
        return f"Show me what you learned about {topic.name.lower()} by answering these questions."
    
    # Initialize helper methods
    def _initialize_templates(self) -> Dict:
        """Initialize lesson templates."""
        return {}
    
    def _initialize_activity_pools(self) -> Dict:
        """Initialize activity pools for different subjects."""
        return {}
    
    def _initialize_voice_patterns(self) -> Dict:
        """Initialize voice interaction patterns."""
        return {}
    
    def _initialize_accessibility_guidelines(self) -> Dict:
        """Initialize accessibility guidelines."""
        return {}
    
    def get_lesson_variants(self, topic: Topic) -> List[Lesson]:
        """Generate multiple lesson variants for a topic."""
        variants = []
        for difficulty in topic.difficulty_progression:
            for format in [LessonFormat.STANDARD, LessonFormat.VOICE_FRIENDLY, LessonFormat.VISUAL]:
                lesson = self.generate_lesson(topic, difficulty, format)
                variants.append(lesson)
        return variants