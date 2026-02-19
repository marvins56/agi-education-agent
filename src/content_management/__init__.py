"""
Content Management System for EduAGI

This package provides comprehensive content management capabilities for educational materials,
including content creation, review, import/export, and library management.
"""

from .library import ContentLibrary, ContentType, ContentMetadata
from .creator import ContentCreator, ContentTemplate
from .review import ContentReview, ReviewStatus, QualityScore
from .import_export import ContentImporter, ContentExporter

__version__ = "1.0.0"

__all__ = [
    "ContentLibrary",
    "ContentType", 
    "ContentMetadata",
    "ContentCreator",
    "ContentTemplate",
    "ContentReview",
    "ReviewStatus",
    "QualityScore",
    "ContentImporter",
    "ContentExporter",
]