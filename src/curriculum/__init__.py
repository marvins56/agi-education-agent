"""
EduAGI Curriculum Management System

A comprehensive curriculum alignment system for East African education standards,
supporting Uganda (Primary 1-7, Senior 1-6) and Kenya (Form 1-4) grade levels
across multiple subjects.

Core Components:
- CurriculumEngine: Subject and grade level management with topic trees
- LessonGenerator: Structured lesson creation with difficulty variants
- AssessmentGenerator: Question generation with multiple formats
- ProgressTracker: Learning progress and prerequisite management
"""

from .engine import CurriculumEngine
from .lesson_generator import LessonGenerator
from .assessment_generator import AssessmentGenerator
from .progress_tracker import ProgressTracker

__version__ = "1.0.0"
__all__ = [
    "CurriculumEngine",
    "LessonGenerator", 
    "AssessmentGenerator",
    "ProgressTracker"
]