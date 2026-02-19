"""
EduAGI Analytics Package

Comprehensive learning analytics system providing insights into student performance,
class dynamics, and educational effectiveness.

Main Components:
- StudentAnalytics: Individual student performance metrics and insights
- ClassAnalytics: Class-wide performance and teacher effectiveness metrics  
- ReportGenerator: Automated report generation for various stakeholders
- InsightsEngine: AI-powered learning insights and recommendations
"""

from .student_analytics import StudentAnalytics
from .class_analytics import ClassAnalytics
from .reporting import ReportGenerator
from .insights import InsightsEngine

__version__ = "1.0.0"
__author__ = "Thor - EduAGI Analytics Team"

__all__ = [
    "StudentAnalytics",
    "ClassAnalytics", 
    "ReportGenerator",
    "InsightsEngine"
]