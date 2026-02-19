"""
EduAGI Collaboration Package

Teacher-student collaboration tools for educational AI agents.
Provides classroom management, assignments, discussions, and peer learning.
"""

from .classroom import Classroom
from .assignments import AssignmentManager
from .discussion import DiscussionBoard
from .peer_learning import PeerLearningManager

__all__ = [
    'Classroom',
    'AssignmentManager', 
    'DiscussionBoard',
    'PeerLearningManager'
]

__version__ = "1.0.0"