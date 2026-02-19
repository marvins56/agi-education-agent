"""
Virtual Classroom Management System

Provides comprehensive classroom creation, management, and collaboration features
for teachers and students in the EduAGI platform.
"""

import uuid
import random
import string
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum


class UserRole(Enum):
    """User roles within a classroom."""
    OWNER = "owner"
    CO_TEACHER = "co_teacher" 
    STUDENT = "student"


class GradeLevel(Enum):
    """Educational grade levels."""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    COLLEGE = "college"
    ADULT_LEARNING = "adult_learning"


@dataclass
class ClassroomSettings:
    """Configuration settings for a classroom."""
    curriculum: str = "general"
    grade_level: GradeLevel = GradeLevel.MIDDLE_SCHOOL
    language: str = "en"
    max_students: int = 30
    allow_peer_grading: bool = False
    auto_archive_days: int = 90
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "assignments": True,
        "discussions": True,
        "announcements": True,
        "grades": True
    })


@dataclass
class ClassroomMember:
    """Represents a member of the classroom."""
    user_id: str
    username: str
    display_name: str
    role: UserRole
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_active: Optional[datetime] = None
    email: Optional[str] = None
    
    
@dataclass
class Announcement:
    """Classroom announcement."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    author_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: str = "normal"  # low, normal, high, urgent
    expires_at: Optional[datetime] = None
    target_roles: Set[UserRole] = field(default_factory=lambda: {UserRole.STUDENT})
    read_by: Set[str] = field(default_factory=set)
    pinned: bool = False


class Classroom:
    """
    Virtual classroom management system.
    
    Handles classroom creation, member management, settings, announcements,
    and basic collaboration features.
    """
    
    def __init__(self, name: str, owner_id: str, owner_username: str, 
                 description: str = "", settings: Optional[ClassroomSettings] = None):
        """Initialize a new classroom."""
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.settings = settings or ClassroomSettings()
        self.invite_code = self._generate_invite_code()
        self.created_at = datetime.now(timezone.utc)
        self.archived = False
        
        # Members management
        self.members: Dict[str, ClassroomMember] = {}
        self.add_member(owner_id, owner_username, owner_username, UserRole.OWNER)
        
        # Announcements
        self.announcements: List[Announcement] = []
        
        # Statistics
        self.stats = {
            "total_assignments": 0,
            "active_discussions": 0,
            "total_messages": 0,
            "last_activity": datetime.now(timezone.utc)
        }

    def _generate_invite_code(self, length: int = 8) -> str:
        """Generate a unique classroom invite code."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    def regenerate_invite_code(self, requester_id: str) -> str:
        """Regenerate the invite code (teachers only)."""
        if not self.is_teacher(requester_id):
            raise PermissionError("Only teachers can regenerate invite codes")
        
        self.invite_code = self._generate_invite_code()
        return self.invite_code

    def add_member(self, user_id: str, username: str, display_name: str, 
                   role: UserRole, email: Optional[str] = None) -> ClassroomMember:
        """Add a new member to the classroom."""
        if len(self.members) >= self.settings.max_students + 10:  # +10 for teachers
            raise ValueError("Classroom is at maximum capacity")
            
        if user_id in self.members:
            raise ValueError(f"User {username} is already a member")
            
        member = ClassroomMember(
            user_id=user_id,
            username=username,
            display_name=display_name,
            role=role,
            email=email
        )
        
        self.members[user_id] = member
        self.stats["last_activity"] = datetime.now(timezone.utc)
        return member

    def join_with_invite(self, invite_code: str, user_id: str, 
                        username: str, display_name: str, 
                        email: Optional[str] = None) -> ClassroomMember:
        """Join classroom using an invite code."""
        if self.archived:
            raise ValueError("Cannot join archived classroom")
            
        if invite_code != self.invite_code:
            raise ValueError("Invalid invite code")
            
        return self.add_member(user_id, username, display_name, 
                             UserRole.STUDENT, email)

    def remove_member(self, user_id: str, requester_id: str) -> bool:
        """Remove a member from the classroom."""
        if user_id not in self.members:
            return False
            
        requester = self.members.get(requester_id)
        target_member = self.members[user_id]
        
        # Only owners can remove co-teachers, teachers can remove students
        if target_member.role == UserRole.OWNER:
            raise PermissionError("Cannot remove classroom owner")
        elif target_member.role == UserRole.CO_TEACHER and requester.role != UserRole.OWNER:
            raise PermissionError("Only owners can remove co-teachers")
        elif not self.is_teacher(requester_id):
            raise PermissionError("Only teachers can remove members")
            
        del self.members[user_id]
        self.stats["last_activity"] = datetime.now(timezone.utc)
        return True

    def promote_to_co_teacher(self, user_id: str, requester_id: str) -> bool:
        """Promote a student to co-teacher (owner only)."""
        if not self.is_owner(requester_id):
            raise PermissionError("Only classroom owner can promote co-teachers")
            
        if user_id not in self.members:
            raise ValueError("User not found in classroom")
            
        member = self.members[user_id]
        if member.role != UserRole.STUDENT:
            raise ValueError("Can only promote students")
            
        member.role = UserRole.CO_TEACHER
        return True

    def is_member(self, user_id: str) -> bool:
        """Check if user is a classroom member."""
        return user_id in self.members

    def is_teacher(self, user_id: str) -> bool:
        """Check if user is a teacher (owner or co-teacher)."""
        member = self.members.get(user_id)
        return member and member.role in [UserRole.OWNER, UserRole.CO_TEACHER]

    def is_owner(self, user_id: str) -> bool:
        """Check if user is the classroom owner."""
        member = self.members.get(user_id)
        return member and member.role == UserRole.OWNER

    def get_students(self) -> List[ClassroomMember]:
        """Get all student members."""
        return [m for m in self.members.values() if m.role == UserRole.STUDENT]

    def get_teachers(self) -> List[ClassroomMember]:
        """Get all teacher members (owner + co-teachers)."""
        return [m for m in self.members.values() 
                if m.role in [UserRole.OWNER, UserRole.CO_TEACHER]]

    def create_announcement(self, title: str, content: str, author_id: str,
                          priority: str = "normal", expires_at: Optional[datetime] = None,
                          target_roles: Optional[Set[UserRole]] = None,
                          pinned: bool = False) -> Announcement:
        """Create a new classroom announcement."""
        if not self.is_teacher(author_id):
            raise PermissionError("Only teachers can create announcements")
            
        announcement = Announcement(
            title=title,
            content=content,
            author_id=author_id,
            priority=priority,
            expires_at=expires_at,
            target_roles=target_roles or {UserRole.STUDENT},
            pinned=pinned
        )
        
        self.announcements.append(announcement)
        self.stats["last_activity"] = datetime.now(timezone.utc)
        return announcement

    def get_announcements(self, user_id: str, include_expired: bool = False) -> List[Announcement]:
        """Get announcements visible to the user."""
        if not self.is_member(user_id):
            return []
            
        user_role = self.members[user_id].role
        now = datetime.now(timezone.utc)
        
        announcements = []
        for announcement in self.announcements:
            # Check role targeting
            if user_role not in announcement.target_roles:
                continue
                
            # Check expiration
            if not include_expired and announcement.expires_at and announcement.expires_at < now:
                continue
                
            announcements.append(announcement)
            
        # Sort by priority and creation time (pinned first)
        priority_order = {"urgent": 4, "high": 3, "normal": 2, "low": 1}
        return sorted(announcements, 
                     key=lambda a: (a.pinned, priority_order.get(a.priority, 2), a.created_at),
                     reverse=True)

    def mark_announcement_read(self, announcement_id: str, user_id: str) -> bool:
        """Mark an announcement as read by a user."""
        for announcement in self.announcements:
            if announcement.id == announcement_id:
                announcement.read_by.add(user_id)
                return True
        return False

    def delete_announcement(self, announcement_id: str, requester_id: str) -> bool:
        """Delete an announcement."""
        if not self.is_teacher(requester_id):
            raise PermissionError("Only teachers can delete announcements")
            
        for i, announcement in enumerate(self.announcements):
            if announcement.id == announcement_id:
                # Only original author or owner can delete
                if announcement.author_id != requester_id and not self.is_owner(requester_id):
                    raise PermissionError("Can only delete your own announcements")
                    
                del self.announcements[i]
                return True
        return False

    def update_settings(self, requester_id: str, **kwargs) -> ClassroomSettings:
        """Update classroom settings (teachers only)."""
        if not self.is_teacher(requester_id):
            raise PermissionError("Only teachers can update settings")
            
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                
        self.stats["last_activity"] = datetime.now(timezone.utc)
        return self.settings

    def archive(self, requester_id: str) -> bool:
        """Archive the classroom (owner only)."""
        if not self.is_owner(requester_id):
            raise PermissionError("Only classroom owner can archive")
            
        self.archived = True
        return True

    def get_activity_summary(self) -> Dict[str, Any]:
        """Get classroom activity summary."""
        active_members = len([m for m in self.members.values() 
                            if m.last_active and 
                            (datetime.now(timezone.utc) - m.last_active).days <= 7])
        
        unread_announcements = sum(1 for a in self.announcements 
                                 if len(a.read_by) < len(self.get_students()))
        
        return {
            "total_members": len(self.members),
            "active_members_week": active_members,
            "total_students": len(self.get_students()),
            "total_teachers": len(self.get_teachers()),
            "unread_announcements": unread_announcements,
            "last_activity": self.stats["last_activity"],
            "created_at": self.created_at,
            "archived": self.archived,
            **self.stats
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize classroom to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "invite_code": self.invite_code,
            "created_at": self.created_at.isoformat(),
            "archived": self.archived,
            "settings": {
                "curriculum": self.settings.curriculum,
                "grade_level": self.settings.grade_level.value,
                "language": self.settings.language,
                "max_students": self.settings.max_students,
                "allow_peer_grading": self.settings.allow_peer_grading,
                "auto_archive_days": self.settings.auto_archive_days,
                "notification_preferences": self.settings.notification_preferences
            },
            "members": {uid: {
                "username": m.username,
                "display_name": m.display_name,
                "role": m.role.value,
                "joined_at": m.joined_at.isoformat(),
                "last_active": m.last_active.isoformat() if m.last_active else None,
                "email": m.email
            } for uid, m in self.members.items()},
            "stats": {
                **self.stats,
                "last_activity": self.stats["last_activity"].isoformat()
            }
        }