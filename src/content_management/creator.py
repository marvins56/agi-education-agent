"""
Content Creator - AI-assisted educational content generation

This module provides the ContentCreator class for generating various types of
educational content using AI assistance and templates.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from .library import ContentType, DifficultyLevel, ContentLibrary

logger = logging.getLogger(__name__)


class GenerationMode(Enum):
    """Content generation modes"""
    STRUCTURED = "structured"  # Follow strict curriculum alignment
    ADAPTIVE = "adaptive"      # Adapt to student needs
    CREATIVE = "creative"      # Creative and engaging approach
    ACCESSIBLE = "accessible"  # Optimized for accessibility


@dataclass
class CurriculumObjective:
    """Curriculum learning objective"""
    subject: str
    grade: Union[int, str]
    topic: str
    objective_text: str
    skills: List[str]
    assessment_criteria: List[str]


@dataclass
class ContentTemplate:
    """Template for content generation"""
    template_id: str
    name: str
    content_type: ContentType
    template_structure: Dict[str, Any]
    default_prompts: Dict[str, str]
    variables: List[str]  # Template variables that need to be filled
    
    def render(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Render template with provided variables"""
        rendered = self.template_structure.copy()
        
        def replace_variables(obj):
            if isinstance(obj, str):
                for var, value in variables.items():
                    obj = obj.replace(f"{{{var}}}", str(value))
                return obj
            elif isinstance(obj, dict):
                return {k: replace_variables(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_variables(item) for item in obj]
            return obj
        
        return replace_variables(rendered)


class ContentGenerationEngine(ABC):
    """Abstract base class for content generation engines"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text content"""
        pass
    
    @abstractmethod
    async def translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language"""
        pass


class MockGenerationEngine(ContentGenerationEngine):
    """Mock generation engine for testing"""
    
    async def generate_text(self, prompt: str, max_tokens: int = 1000) -> str:
        return f"Generated content for prompt: {prompt[:50]}..."
    
    async def translate_text(self, text: str, target_language: str) -> str:
        return f"[{target_language}] {text}"


class ContentCreator:
    """AI-assisted content creation system"""
    
    def __init__(self, 
                 generation_engine: Optional[ContentGenerationEngine] = None,
                 content_library: Optional[ContentLibrary] = None):
        """
        Initialize content creator
        
        Args:
            generation_engine: AI generation engine
            content_library: Content library for storing created content
        """
        self.generation_engine = generation_engine or MockGenerationEngine()
        self.content_library = content_library
        self.templates: Dict[str, ContentTemplate] = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default content templates"""
        
        # Lesson template
        lesson_template = ContentTemplate(
            template_id="lesson_basic",
            name="Basic Lesson Template",
            content_type=ContentType.LESSON,
            template_structure={
                "title": "{lesson_title}",
                "learning_objectives": "{objectives}",
                "introduction": "{introduction}",
                "main_content": "{main_content}",
                "examples": "{examples}",
                "practice_exercises": "{exercises}",
                "summary": "{summary}",
                "additional_resources": "{resources}"
            },
            default_prompts={
                "introduction": "Create an engaging introduction for a lesson on {topic} for grade {grade} students",
                "main_content": "Explain {topic} in detail appropriate for grade {grade} level",
                "examples": "Provide practical examples of {topic} that students can relate to",
                "exercises": "Create practice exercises for {topic} at {difficulty} level"
            },
            variables=["lesson_title", "topic", "grade", "difficulty", "objectives", 
                      "introduction", "main_content", "examples", "exercises", "summary", "resources"]
        )
        self.templates["lesson_basic"] = lesson_template
        
        # Quiz template
        quiz_template = ContentTemplate(
            template_id="quiz_multiple_choice",
            name="Multiple Choice Quiz Template", 
            content_type=ContentType.QUIZ,
            template_structure={
                "title": "{quiz_title}",
                "instructions": "Choose the best answer for each question",
                "questions": "{questions}",
                "answer_key": "{answers}",
                "explanations": "{explanations}"
            },
            default_prompts={
                "questions": "Generate multiple choice questions about {topic} for grade {grade}",
                "explanations": "Provide explanations for quiz answers on {topic}"
            },
            variables=["quiz_title", "topic", "grade", "questions", "answers", "explanations"]
        )
        self.templates["quiz_multiple_choice"] = quiz_template
        
        # Flashcard template
        flashcard_template = ContentTemplate(
            template_id="flashcard_basic",
            name="Basic Flashcard Template",
            content_type=ContentType.FLASHCARD,
            template_structure={
                "title": "{set_title}",
                "cards": "{cards}",
                "category": "{topic}",
                "spaced_repetition_config": {
                    "initial_interval": 1,
                    "max_interval": 30,
                    "ease_factor": 2.5
                }
            },
            default_prompts={
                "cards": "Create flashcards for {topic} suitable for grade {grade} students"
            },
            variables=["set_title", "topic", "grade", "cards"]
        )
        self.templates["flashcard_basic"] = flashcard_template
    
    async def generate_lesson(self,
                            topic: str,
                            curriculum_objectives: List[CurriculumObjective],
                            grade: Union[int, str],
                            subject: str,
                            difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                            language: str = "en",
                            mode: GenerationMode = GenerationMode.STRUCTURED,
                            duration: int = 45) -> Dict[str, Any]:
        """
        Generate a complete lesson
        
        Args:
            topic: Lesson topic
            curriculum_objectives: Learning objectives to align with
            grade: Grade level
            subject: Subject area
            difficulty: Difficulty level
            language: Content language
            mode: Generation mode
            duration: Lesson duration in minutes
            
        Returns:
            Generated lesson content
        """
        logger.info(f"Generating lesson: {topic} (Grade {grade}, {subject})")
        
        # Build context for generation
        objectives_text = "\n".join([obj.objective_text for obj in curriculum_objectives])
        skills_text = ", ".join(set().union(*[obj.skills for obj in curriculum_objectives]))
        
        # Generate lesson components
        lesson_title = f"{topic} - Grade {grade} {subject}"
        
        # Introduction
        intro_prompt = f"""
        Create an engaging introduction for a lesson on '{topic}' for grade {grade} {subject} students.
        Learning objectives: {objectives_text}
        Difficulty level: {difficulty.value}
        Duration: {duration} minutes
        Mode: {mode.value}
        """
        introduction = await self.generation_engine.generate_text(intro_prompt, 300)
        
        # Main content
        content_prompt = f"""
        Create detailed lesson content for '{topic}' appropriate for grade {grade} {subject}.
        Cover these skills: {skills_text}
        Difficulty: {difficulty.value}
        Include explanations, key concepts, and important points.
        """
        main_content = await self.generation_engine.generate_text(content_prompt, 800)
        
        # Examples
        examples_prompt = f"""
        Provide 3-5 practical examples of '{topic}' that grade {grade} students can understand and relate to.
        Make examples relevant to their daily life and appropriate for {difficulty.value} level.
        """
        examples = await self.generation_engine.generate_text(examples_prompt, 400)
        
        # Practice exercises
        exercises_prompt = f"""
        Create practice exercises for '{topic}' at {difficulty.value} level for grade {grade} students.
        Include 5-7 exercises that help students practice the skills: {skills_text}
        Vary the exercise types (problems, questions, activities).
        """
        exercises = await self.generation_engine.generate_text(exercises_prompt, 500)
        
        # Summary
        summary_prompt = f"""
        Create a concise summary for the lesson on '{topic}' that reinforces key concepts
        and helps grade {grade} students remember the main points.
        """
        summary = await self.generation_engine.generate_text(summary_prompt, 200)
        
        # Additional resources
        resources_prompt = f"""
        Suggest additional learning resources for '{topic}' suitable for grade {grade} {subject}.
        Include books, websites, videos, or activities for further learning.
        """
        resources = await self.generation_engine.generate_text(resources_prompt, 300)
        
        # Use template to structure content
        template = self.templates["lesson_basic"]
        lesson_content = template.render({
            "lesson_title": lesson_title,
            "topic": topic,
            "grade": grade,
            "difficulty": difficulty.value,
            "objectives": objectives_text,
            "introduction": introduction,
            "main_content": main_content,
            "examples": examples,
            "exercises": exercises,
            "summary": summary,
            "resources": resources
        })
        
        # Translate if needed
        if language != "en":
            lesson_content = await self._translate_content(lesson_content, language)
        
        return lesson_content
    
    async def generate_quiz(self,
                          topic: str,
                          grade: Union[int, str],
                          subject: str,
                          num_questions: int = 10,
                          difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                          language: str = "en",
                          question_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate a quiz with multiple question types
        
        Args:
            topic: Quiz topic
            grade: Grade level
            subject: Subject area
            num_questions: Number of questions to generate
            difficulty: Difficulty level
            language: Content language
            question_types: Types of questions (multiple_choice, true_false, short_answer)
            
        Returns:
            Generated quiz content
        """
        logger.info(f"Generating quiz: {topic} ({num_questions} questions)")
        
        if question_types is None:
            question_types = ["multiple_choice", "true_false", "short_answer"]
        
        quiz_title = f"{topic} Quiz - Grade {grade}"
        
        # Generate questions
        questions_prompt = f"""
        Generate {num_questions} quiz questions about '{topic}' for grade {grade} {subject}.
        Difficulty level: {difficulty.value}
        Include these question types: {', '.join(question_types)}
        
        Format each question as:
        Question: [question text]
        Type: [question type]
        Options: [for multiple choice, list A, B, C, D options]
        Answer: [correct answer]
        Explanation: [brief explanation]
        """
        questions_text = await self.generation_engine.generate_text(questions_prompt, 1200)
        
        # Parse and structure questions
        questions = self._parse_quiz_questions(questions_text)
        
        # Generate answer key
        answer_key = [q.get("answer", "") for q in questions]
        
        # Generate explanations
        explanations = [q.get("explanation", "") for q in questions]
        
        # Use template
        template = self.templates["quiz_multiple_choice"]
        quiz_content = template.render({
            "quiz_title": quiz_title,
            "topic": topic,
            "grade": grade,
            "questions": questions,
            "answers": answer_key,
            "explanations": explanations
        })
        
        # Translate if needed
        if language != "en":
            quiz_content = await self._translate_content(quiz_content, language)
        
        return quiz_content
    
    async def generate_flashcards(self,
                                topic: str,
                                grade: Union[int, str],
                                subject: str,
                                num_cards: int = 20,
                                difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
                                language: str = "en",
                                card_type: str = "definition") -> Dict[str, Any]:
        """
        Generate flashcard set for spaced repetition
        
        Args:
            topic: Topic for flashcards
            grade: Grade level
            subject: Subject area
            num_cards: Number of flashcards
            difficulty: Difficulty level
            language: Content language
            card_type: Type of flashcards (definition, question_answer, term_example)
            
        Returns:
            Generated flashcard set
        """
        logger.info(f"Generating {num_cards} flashcards for {topic}")
        
        set_title = f"{topic} Flashcards - Grade {grade}"
        
        # Generate flashcards
        cards_prompt = f"""
        Create {num_cards} flashcards for '{topic}' suitable for grade {grade} {subject} students.
        Difficulty level: {difficulty.value}
        Card type: {card_type}
        
        Format each card as:
        Front: [question/term/concept]
        Back: [answer/definition/explanation]
        Hint: [optional hint]
        """
        cards_text = await self.generation_engine.generate_text(cards_prompt, 800)
        
        # Parse cards
        cards = self._parse_flashcards(cards_text)
        
        # Use template
        template = self.templates["flashcard_basic"]
        flashcard_content = template.render({
            "set_title": set_title,
            "topic": topic,
            "grade": grade,
            "cards": cards
        })
        
        # Translate if needed
        if language != "en":
            flashcard_content = await self._translate_content(flashcard_content, language)
        
        return flashcard_content
    
    async def generate_audio_lesson_script(self,
                                         lesson_content: Dict[str, Any],
                                         voice_style: str = "friendly",
                                         include_pauses: bool = True) -> str:
        """
        Generate script optimized for audio delivery
        
        Args:
            lesson_content: Existing lesson content
            voice_style: Style of narration (friendly, professional, energetic)
            include_pauses: Whether to include pause markers
            
        Returns:
            Audio-optimized script
        """
        script_prompt = f"""
        Convert this lesson content into a script optimized for audio delivery:
        Title: {lesson_content.get('title', '')}
        Content: {json.dumps(lesson_content, indent=2)}
        
        Requirements:
        - Use {voice_style} narration style
        - Include natural speech patterns
        - Add transition phrases
        - Break content into digestible segments
        {"- Include [PAUSE] markers for natural breaks" if include_pauses else ""}
        - Make it engaging for audio-only learning
        """
        
        script = await self.generation_engine.generate_text(script_prompt, 1500)
        return script
    
    async def generate_simplified_version(self,
                                        content: Dict[str, Any],
                                        target_reading_level: int = 6,
                                        accessibility_features: List[str] = None) -> Dict[str, Any]:
        """
        Generate simplified version for accessibility
        
        Args:
            content: Original content
            target_reading_level: Target reading grade level
            accessibility_features: Features to include (simple_language, short_sentences, etc.)
            
        Returns:
            Simplified content
        """
        if accessibility_features is None:
            accessibility_features = ["simple_language", "short_sentences", "clear_structure"]
        
        simplify_prompt = f"""
        Simplify this educational content for better accessibility:
        Original content: {json.dumps(content, indent=2)}
        
        Requirements:
        - Target reading level: Grade {target_reading_level}
        - Features: {', '.join(accessibility_features)}
        - Maintain educational value
        - Use clear, simple language
        - Break down complex concepts
        - Include visual structure markers
        """
        
        simplified_text = await self.generation_engine.generate_text(simplify_prompt, 1000)
        
        # Structure the simplified content
        simplified_content = content.copy()
        simplified_content["accessibility"] = {
            "reading_level": target_reading_level,
            "features": accessibility_features,
            "simplified_content": simplified_text
        }
        
        return simplified_content
    
    async def translate_content(self,
                              content: Dict[str, Any],
                              target_languages: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Translate content to multiple languages
        
        Args:
            content: Content to translate
            target_languages: List of target language codes
            
        Returns:
            Dictionary mapping language codes to translated content
        """
        translations = {}
        
        for language in target_languages:
            logger.info(f"Translating content to {language}")
            translated_content = await self._translate_content(content, language)
            translations[language] = translated_content
        
        return translations
    
    def add_template(self, template: ContentTemplate):
        """Add a custom content template"""
        self.templates[template.template_id] = template
        logger.info(f"Added template: {template.name}")
    
    def get_template(self, template_id: str) -> Optional[ContentTemplate]:
        """Get a content template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self) -> List[ContentTemplate]:
        """List all available templates"""
        return list(self.templates.values())
    
    async def _translate_content(self, content: Dict[str, Any], target_language: str) -> Dict[str, Any]:
        """Translate content to target language"""
        translated_content = content.copy()
        
        # Translate text fields
        for key, value in content.items():
            if isinstance(value, str) and value.strip():
                translated_content[key] = await self.generation_engine.translate_text(value, target_language)
            elif isinstance(value, list):
                translated_items = []
                for item in value:
                    if isinstance(item, str):
                        translated_items.append(await self.generation_engine.translate_text(item, target_language))
                    else:
                        translated_items.append(item)
                translated_content[key] = translated_items
        
        return translated_content
    
    def _parse_quiz_questions(self, questions_text: str) -> List[Dict[str, Any]]:
        """Parse generated quiz questions from text"""
        # Simple parsing logic (could be enhanced with better NLP)
        questions = []
        lines = questions_text.strip().split('\n')
        
        current_question = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Question:"):
                if current_question:
                    questions.append(current_question)
                current_question = {"question": line[9:].strip()}
            elif line.startswith("Type:"):
                current_question["type"] = line[5:].strip()
            elif line.startswith("Options:"):
                current_question["options"] = line[8:].strip().split(", ")
            elif line.startswith("Answer:"):
                current_question["answer"] = line[7:].strip()
            elif line.startswith("Explanation:"):
                current_question["explanation"] = line[12:].strip()
        
        if current_question:
            questions.append(current_question)
        
        return questions
    
    def _parse_flashcards(self, cards_text: str) -> List[Dict[str, str]]:
        """Parse generated flashcards from text"""
        cards = []
        lines = cards_text.strip().split('\n')
        
        current_card = {}
        for line in lines:
            line = line.strip()
            if line.startswith("Front:"):
                if current_card:
                    cards.append(current_card)
                current_card = {"front": line[6:].strip()}
            elif line.startswith("Back:"):
                current_card["back"] = line[5:].strip()
            elif line.startswith("Hint:"):
                current_card["hint"] = line[5:].strip()
        
        if current_card:
            cards.append(current_card)
        
        return cards