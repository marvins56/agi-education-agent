"""
Peer Learning Management System

Study buddy matching, collaborative problem solving, peer review,
teaching rewards, and group project management for EduAGI.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random


class MatchingCriteria(Enum):
    """Criteria for matching study partners."""
    SUBJECT = "subject"
    SKILL_LEVEL = "skill_level"
    AVAILABILITY = "availability"
    LEARNING_STYLE = "learning_style"
    TIMEZONE = "timezone"
    LANGUAGE = "language"


class SessionType(Enum):
    """Types of collaborative learning sessions."""
    STUDY_SESSION = "study_session"
    PROBLEM_SOLVING = "problem_solving"
    PEER_REVIEW = "peer_review"
    TUTORING = "tutoring"
    GROUP_PROJECT = "group_project"
    DISCUSSION = "discussion"


class SessionStatus(Enum):
    """Status of learning sessions."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ProjectRole(Enum):
    """Roles in group projects."""
    LEADER = "leader"
    RESEARCHER = "researcher"
    WRITER = "writer"
    PRESENTER = "presenter"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


@dataclass
class LearnerProfile:
    """Profile of a learner for matching purposes."""
    user_id: str
    subjects: List[str] = field(default_factory=list)
    skill_levels: Dict[str, int] = field(default_factory=dict)  # subject -> level (1-5)
    learning_style: str = "visual"  # visual, auditory, kinesthetic, reading
    availability_hours: List[int] = field(default_factory=list)  # Hours of day available
    timezone: str = "UTC"
    preferred_languages: List[str] = field(default_factory=lambda: ["en"])
    
    # Performance metrics
    help_given_count: int = 0
    help_received_count: int = 0
    teaching_rating: float = 0.0
    collaboration_rating: float = 0.0
    
    # Preferences
    max_group_size: int = 4
    preferred_session_duration: int = 60  # minutes
    can_tutor_subjects: List[str] = field(default_factory=list)
    seeking_help_subjects: List[str] = field(default_factory=list)


@dataclass
class StudyBuddy:
    """Study buddy pairing information."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user1_id: str = ""
    user2_id: str = ""
    subjects: List[str] = field(default_factory=list)
    matched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    compatibility_score: float = 0.0
    
    # Activity tracking
    sessions_completed: int = 0
    total_study_time: int = 0  # minutes
    last_session: Optional[datetime] = None
    
    # Feedback
    user1_rating: Optional[float] = None
    user2_rating: Optional[float] = None
    active: bool = True


@dataclass
class LearningSession:
    """Collaborative learning session."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_type: SessionType = SessionType.STUDY_SESSION
    title: str = ""
    description: str = ""
    
    # Participants
    organizer_id: str = ""
    participants: List[str] = field(default_factory=list)
    max_participants: int = 4
    
    # Scheduling
    scheduled_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_duration: int = 60  # minutes
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: SessionStatus = SessionStatus.SCHEDULED
    
    # Content
    subject: str = ""
    topics: List[str] = field(default_factory=list)
    materials: List[Dict[str, str]] = field(default_factory=list)  # {name, url, type}
    
    # Notes and outcomes
    session_notes: str = ""
    outcomes: List[str] = field(default_factory=list)
    participant_feedback: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # XP rewards
    xp_awarded: Dict[str, int] = field(default_factory=dict)  # user_id -> xp


@dataclass
class PeerReview:
    """Peer review assignment and feedback."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    assignment_id: str = ""
    reviewer_id: str = ""
    reviewee_id: str = ""
    
    # Review criteria
    criteria: List[str] = field(default_factory=list)
    rubric: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Review content
    scores: Dict[str, float] = field(default_factory=dict)  # criterion -> score
    feedback: str = ""
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    
    # Metadata
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    helpful_votes: int = 0
    quality_rating: Optional[float] = None  # Rated by reviewee


@dataclass
class GroupProject:
    """Group project management."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    assignment_id: Optional[str] = None
    
    # Team composition
    members: Dict[str, ProjectRole] = field(default_factory=dict)  # user_id -> role
    max_members: int = 4
    
    # Timeline
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None
    
    # Project components
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    
    # Collaboration
    shared_documents: List[Dict[str, str]] = field(default_factory=list)
    meetings: List[LearningSession] = field(default_factory=list)
    
    # Progress tracking
    completion_percentage: float = 0.0
    individual_contributions: Dict[str, float] = field(default_factory=dict)  # user_id -> %


class PeerLearningManager:
    """
    Comprehensive peer learning management system.
    
    Handles study buddy matching, collaborative sessions, peer review,
    teaching rewards, and group project coordination.
    """
    
    def __init__(self, classroom_id: str):
        """Initialize peer learning manager for a classroom."""
        self.classroom_id = classroom_id
        
        # Core data structures
        self.learner_profiles: Dict[str, LearnerProfile] = {}
        self.study_buddies: Dict[str, StudyBuddy] = {}
        self.learning_sessions: Dict[str, LearningSession] = {}
        self.peer_reviews: Dict[str, PeerReview] = {}
        self.group_projects: Dict[str, GroupProject] = {}
        
        # Configuration
        self.matching_enabled = True
        self.xp_rewards = {
            "help_given": 10,
            "session_attended": 5,
            "quality_review": 15,
            "project_contribution": 20,
            "teach_concept": 25
        }
        
        # Matching algorithm weights
        self.matching_weights = {
            MatchingCriteria.SUBJECT: 0.3,
            MatchingCriteria.SKILL_LEVEL: 0.25,
            MatchingCriteria.AVAILABILITY: 0.2,
            MatchingCriteria.LEARNING_STYLE: 0.1,
            MatchingCriteria.TIMEZONE: 0.1,
            MatchingCriteria.LANGUAGE: 0.05
        }

    def create_learner_profile(self, user_id: str, **profile_data) -> LearnerProfile:
        """Create or update learner profile."""
        existing_profile = self.learner_profiles.get(user_id)
        
        if existing_profile:
            # Update existing profile
            for key, value in profile_data.items():
                if hasattr(existing_profile, key):
                    setattr(existing_profile, key, value)
            return existing_profile
        else:
            # Create new profile
            profile = LearnerProfile(user_id=user_id, **profile_data)
            self.learner_profiles[user_id] = profile
            return profile

    def find_study_buddies(self, user_id: str, subject: str, 
                          max_matches: int = 5) -> List[Dict[str, Any]]:
        """Find compatible study buddies for a user."""
        if not self.matching_enabled or user_id not in self.learner_profiles:
            return []
            
        user_profile = self.learner_profiles[user_id]
        matches = []
        
        for other_id, other_profile in self.learner_profiles.items():
            if other_id == user_id:
                continue
                
            # Skip if already study buddies
            if self._are_study_buddies(user_id, other_id):
                continue
                
            # Calculate compatibility score
            compatibility = self._calculate_compatibility(user_profile, other_profile, subject)
            
            if compatibility > 0.3:  # Minimum threshold
                matches.append({
                    "user_id": other_id,
                    "profile": other_profile,
                    "compatibility_score": compatibility,
                    "common_subjects": list(set(user_profile.subjects) & set(other_profile.subjects)),
                    "complementary_skills": self._find_complementary_skills(user_profile, other_profile)
                })
        
        # Sort by compatibility and return top matches
        return sorted(matches, key=lambda x: x["compatibility_score"], reverse=True)[:max_matches]

    def _calculate_compatibility(self, profile1: LearnerProfile, profile2: LearnerProfile, 
                               subject: str) -> float:
        """Calculate compatibility score between two learners."""
        total_score = 0.0
        
        # Subject overlap
        common_subjects = set(profile1.subjects) & set(profile2.subjects)
        subject_score = len(common_subjects) / max(len(profile1.subjects), len(profile2.subjects), 1)
        total_score += subject_score * self.matching_weights[MatchingCriteria.SUBJECT]
        
        # Skill level compatibility (not too far apart)
        if subject in profile1.skill_levels and subject in profile2.skill_levels:
            skill_diff = abs(profile1.skill_levels[subject] - profile2.skill_levels[subject])
            skill_score = max(0, 1.0 - skill_diff / 4.0)  # 4 is max skill difference
            total_score += skill_score * self.matching_weights[MatchingCriteria.SKILL_LEVEL]
        
        # Availability overlap
        common_hours = set(profile1.availability_hours) & set(profile2.availability_hours)
        availability_score = len(common_hours) / 24.0  # Normalize to 24 hours
        total_score += availability_score * self.matching_weights[MatchingCriteria.AVAILABILITY]
        
        # Learning style compatibility
        style_score = 1.0 if profile1.learning_style == profile2.learning_style else 0.5
        total_score += style_score * self.matching_weights[MatchingCriteria.LEARNING_STYLE]
        
        # Timezone compatibility
        timezone_score = 1.0 if profile1.timezone == profile2.timezone else 0.3
        total_score += timezone_score * self.matching_weights[MatchingCriteria.TIMEZONE]
        
        # Language compatibility
        common_languages = set(profile1.preferred_languages) & set(profile2.preferred_languages)
        language_score = 1.0 if common_languages else 0.0
        total_score += language_score * self.matching_weights[MatchingCriteria.LANGUAGE]
        
        return min(total_score, 1.0)

    def _find_complementary_skills(self, profile1: LearnerProfile, 
                                 profile2: LearnerProfile) -> List[str]:
        """Find subjects where profiles have complementary skill levels."""
        complementary = []
        
        for subject in set(profile1.subjects) & set(profile2.subjects):
            if (subject in profile1.skill_levels and subject in profile2.skill_levels):
                level1 = profile1.skill_levels[subject]
                level2 = profile2.skill_levels[subject]
                
                # One can help the other if skill difference is 1-2 levels
                if 1 <= abs(level1 - level2) <= 2:
                    complementary.append(subject)
                    
        return complementary

    def create_study_buddy_pair(self, user1_id: str, user2_id: str, 
                               subjects: List[str]) -> StudyBuddy:
        """Create a study buddy pairing."""
        if user1_id not in self.learner_profiles or user2_id not in self.learner_profiles:
            raise ValueError("Both users must have learner profiles")
            
        if self._are_study_buddies(user1_id, user2_id):
            raise ValueError("Users are already study buddies")
            
        # Calculate compatibility
        compatibility = self._calculate_compatibility(
            self.learner_profiles[user1_id],
            self.learner_profiles[user2_id],
            subjects[0] if subjects else ""
        )
        
        buddy_pair = StudyBuddy(
            user1_id=user1_id,
            user2_id=user2_id,
            subjects=subjects,
            compatibility_score=compatibility
        )
        
        self.study_buddies[buddy_pair.id] = buddy_pair
        return buddy_pair

    def _are_study_buddies(self, user1_id: str, user2_id: str) -> bool:
        """Check if two users are already study buddies."""
        return any(
            (sb.user1_id == user1_id and sb.user2_id == user2_id) or
            (sb.user1_id == user2_id and sb.user2_id == user1_id)
            for sb in self.study_buddies.values()
            if sb.active
        )

    def schedule_learning_session(self, organizer_id: str, title: str, 
                                session_type: SessionType, subject: str,
                                scheduled_start: datetime, duration_minutes: int = 60,
                                max_participants: int = 4, description: str = "") -> LearningSession:
        """Schedule a collaborative learning session."""
        session = LearningSession(
            session_type=session_type,
            title=title,
            description=description,
            organizer_id=organizer_id,
            subject=subject,
            scheduled_start=scheduled_start,
            scheduled_duration=duration_minutes,
            max_participants=max_participants
        )
        
        self.learning_sessions[session.id] = session
        return session

    def join_learning_session(self, session_id: str, user_id: str) -> bool:
        """Join a learning session."""
        session = self.learning_sessions.get(session_id)
        if not session:
            return False
            
        if (len(session.participants) >= session.max_participants or
            user_id in session.participants or
            session.status != SessionStatus.SCHEDULED):
            return False
            
        session.participants.append(user_id)
        return True

    def start_learning_session(self, session_id: str, organizer_id: str) -> bool:
        """Start a learning session."""
        session = self.learning_sessions.get(session_id)
        if (not session or session.organizer_id != organizer_id or 
            session.status != SessionStatus.SCHEDULED):
            return False
            
        session.actual_start = datetime.now(timezone.utc)
        session.status = SessionStatus.IN_PROGRESS
        return True

    def complete_learning_session(self, session_id: str, organizer_id: str, 
                                outcomes: List[str] = None, 
                                session_notes: str = "") -> bool:
        """Complete a learning session and award XP."""
        session = self.learning_sessions.get(session_id)
        if (not session or session.organizer_id != organizer_id or 
            session.status != SessionStatus.IN_PROGRESS):
            return False
            
        session.actual_end = datetime.now(timezone.utc)
        session.status = SessionStatus.COMPLETED
        session.outcomes = outcomes or []
        session.session_notes = session_notes
        
        # Award XP to participants
        xp_per_participant = self.xp_rewards["session_attended"]
        organizer_bonus = 5  # Extra XP for organizing
        
        for participant_id in session.participants:
            xp_amount = xp_per_participant + (organizer_bonus if participant_id == organizer_id else 0)
            session.xp_awarded[participant_id] = xp_amount
            self._award_xp(participant_id, xp_amount, "session_completed")
            
        # Update study buddy relationship if applicable
        if len(session.participants) == 2:
            buddy_pair = self._find_study_buddy_pair(session.participants[0], session.participants[1])
            if buddy_pair:
                buddy_pair.sessions_completed += 1
                buddy_pair.total_study_time += session.scheduled_duration
                buddy_pair.last_session = session.actual_end
                
        return True

    def create_peer_review(self, assignment_id: str, reviewer_id: str, 
                          reviewee_id: str, criteria: List[str]) -> PeerReview:
        """Create a peer review assignment."""
        review = PeerReview(
            assignment_id=assignment_id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            criteria=criteria
        )
        
        self.peer_reviews[review.id] = review
        return review

    def submit_peer_review(self, review_id: str, scores: Dict[str, float], 
                          feedback: str, suggestions: List[str] = None,
                          strengths: List[str] = None) -> bool:
        """Submit a completed peer review."""
        review = self.peer_reviews.get(review_id)
        if not review:
            return False
            
        review.scores = scores
        review.feedback = feedback
        review.suggestions = suggestions or []
        review.strengths = strengths or []
        review.submitted_at = datetime.now(timezone.utc)
        
        # Award XP for completing review
        self._award_xp(review.reviewer_id, self.xp_rewards["quality_review"], "peer_review")
        
        return True

    def create_group_project(self, title: str, description: str, creator_id: str,
                           due_date: Optional[datetime] = None, 
                           max_members: int = 4) -> GroupProject:
        """Create a group project."""
        project = GroupProject(
            title=title,
            description=description,
            max_members=max_members,
            due_date=due_date
        )
        
        # Add creator as leader
        project.members[creator_id] = ProjectRole.LEADER
        project.individual_contributions[creator_id] = 0.0
        
        self.group_projects[project.id] = project
        return project

    def join_group_project(self, project_id: str, user_id: str, 
                          preferred_role: Optional[ProjectRole] = None) -> bool:
        """Join a group project."""
        project = self.group_projects.get(project_id)
        if (not project or len(project.members) >= project.max_members or
            user_id in project.members):
            return False
            
        # Assign role (prefer requested role if available)
        assigned_role = self._assign_project_role(project, preferred_role)
        project.members[user_id] = assigned_role
        project.individual_contributions[user_id] = 0.0
        
        return True

    def _assign_project_role(self, project: GroupProject, 
                           preferred_role: Optional[ProjectRole]) -> ProjectRole:
        """Assign a role in a group project."""
        current_roles = set(project.members.values())
        
        # If preferred role is available, assign it
        if preferred_role and preferred_role not in current_roles:
            return preferred_role
            
        # Otherwise, assign first available role
        available_roles = [role for role in ProjectRole if role not in current_roles]
        return available_roles[0] if available_roles else ProjectRole.COORDINATOR

    def update_project_contribution(self, project_id: str, user_id: str, 
                                  contribution_percentage: float) -> bool:
        """Update individual contribution to a group project."""
        project = self.group_projects.get(project_id)
        if not project or user_id not in project.members:
            return False
            
        project.individual_contributions[user_id] = min(contribution_percentage, 100.0)
        
        # Recalculate overall completion
        total_contributions = sum(project.individual_contributions.values())
        project.completion_percentage = min(total_contributions / len(project.members), 100.0)
        
        return True

    def _award_xp(self, user_id: str, amount: int, reason: str) -> bool:
        """Award XP to a user and update their teaching metrics."""
        profile = self.learner_profiles.get(user_id)
        if not profile:
            return False
            
        # Update relevant metrics based on reason
        if reason == "peer_review":
            profile.help_given_count += 1
        elif reason == "session_completed":
            profile.help_given_count += 1
        elif reason == "tutoring":
            profile.help_given_count += 1
            
        # Update teaching rating based on recent activity
        self._update_teaching_rating(profile)
        
        return True

    def _update_teaching_rating(self, profile: LearnerProfile) -> None:
        """Update teaching rating based on help given and feedback."""
        # Simple rating calculation (would be more sophisticated in practice)
        help_ratio = profile.help_given_count / max(profile.help_received_count + profile.help_given_count, 1)
        base_rating = min(help_ratio * 5.0, 5.0)  # Cap at 5.0
        
        # Incorporate collaboration rating
        profile.teaching_rating = (base_rating + profile.collaboration_rating) / 2.0

    def get_learning_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning analytics for a user."""
        profile = self.learner_profiles.get(user_id)
        if not profile:
            return {}
            
        # Session participation
        sessions_attended = sum(1 for session in self.learning_sessions.values()
                              if user_id in session.participants and 
                              session.status == SessionStatus.COMPLETED)
        
        sessions_organized = sum(1 for session in self.learning_sessions.values()
                               if session.organizer_id == user_id and
                               session.status == SessionStatus.COMPLETED)
        
        # Peer review activity
        reviews_given = sum(1 for review in self.peer_reviews.values()
                          if review.reviewer_id == user_id)
        
        reviews_received = sum(1 for review in self.peer_reviews.values()
                             if review.reviewee_id == user_id)
        
        # Study buddy relationships
        active_buddies = sum(1 for buddy in self.study_buddies.values()
                           if (buddy.user1_id == user_id or buddy.user2_id == user_id)
                           and buddy.active)
        
        # Group project participation
        projects_active = sum(1 for project in self.group_projects.values()
                            if user_id in project.members)
        
        return {
            "profile": profile,
            "session_analytics": {
                "sessions_attended": sessions_attended,
                "sessions_organized": sessions_organized,
                "total_study_time": sum(session.scheduled_duration 
                                      for session in self.learning_sessions.values()
                                      if user_id in session.participants),
                "favorite_subjects": self._get_favorite_subjects(user_id)
            },
            "peer_review_analytics": {
                "reviews_given": reviews_given,
                "reviews_received": reviews_received,
                "average_review_rating": self._calculate_average_review_rating(user_id)
            },
            "collaboration_analytics": {
                "active_study_buddies": active_buddies,
                "active_projects": projects_active,
                "teaching_rating": profile.teaching_rating,
                "collaboration_rating": profile.collaboration_rating
            },
            "achievements": self._get_user_achievements(user_id)
        }

    def _get_favorite_subjects(self, user_id: str) -> List[str]:
        """Get user's favorite subjects based on session participation."""
        subject_counts = {}
        
        for session in self.learning_sessions.values():
            if (user_id in session.participants and 
                session.status == SessionStatus.COMPLETED):
                subject = session.subject
                subject_counts[subject] = subject_counts.get(subject, 0) + 1
                
        return sorted(subject_counts.keys(), key=subject_counts.get, reverse=True)[:5]

    def _calculate_average_review_rating(self, user_id: str) -> float:
        """Calculate average rating for peer reviews given by user."""
        user_reviews = [review for review in self.peer_reviews.values()
                       if review.reviewer_id == user_id and review.quality_rating is not None]
        
        if not user_reviews:
            return 0.0
            
        return sum(review.quality_rating for review in user_reviews) / len(user_reviews)

    def _get_user_achievements(self, user_id: str) -> List[Dict[str, Any]]:
        """Get achievements/badges earned by user."""
        profile = self.learner_profiles.get(user_id)
        if not profile:
            return []
            
        achievements = []
        
        # Help achievements
        if profile.help_given_count >= 10:
            achievements.append({"name": "Helpful Helper", "description": "Helped 10+ peers"})
        if profile.help_given_count >= 50:
            achievements.append({"name": "Teaching Star", "description": "Helped 50+ peers"})
            
        # Session achievements
        session_count = sum(1 for session in self.learning_sessions.values()
                          if user_id in session.participants)
        if session_count >= 5:
            achievements.append({"name": "Study Group Regular", "description": "Attended 5+ sessions"})
        if session_count >= 20:
            achievements.append({"name": "Collaboration Expert", "description": "Attended 20+ sessions"})
            
        # Teaching rating achievements
        if profile.teaching_rating >= 4.0:
            achievements.append({"name": "Excellent Tutor", "description": "4.0+ teaching rating"})
        if profile.teaching_rating >= 4.8:
            achievements.append({"name": "Master Teacher", "description": "4.8+ teaching rating"})
            
        return achievements

    def _find_study_buddy_pair(self, user1_id: str, user2_id: str) -> Optional[StudyBuddy]:
        """Find study buddy pair between two users."""
        for buddy in self.study_buddies.values():
            if ((buddy.user1_id == user1_id and buddy.user2_id == user2_id) or
                (buddy.user1_id == user2_id and buddy.user2_id == user1_id)) and buddy.active:
                return buddy
        return None

    def get_collaboration_recommendations(self, user_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get personalized collaboration recommendations."""
        if user_id not in self.learner_profiles:
            return {}
            
        profile = self.learner_profiles[user_id]
        
        return {
            "study_buddies": self.find_study_buddies(user_id, profile.subjects[0] if profile.subjects else ""),
            "open_sessions": self._find_relevant_sessions(user_id),
            "peer_review_opportunities": self._find_review_opportunities(user_id),
            "group_projects": self._find_joinable_projects(user_id),
            "tutoring_opportunities": self._find_tutoring_opportunities(user_id)
        }

    def _find_relevant_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Find relevant upcoming learning sessions."""
        profile = self.learner_profiles[user_id]
        relevant_sessions = []
        
        for session in self.learning_sessions.values():
            if (session.status == SessionStatus.SCHEDULED and
                user_id not in session.participants and
                len(session.participants) < session.max_participants and
                session.subject in profile.subjects):
                
                relevant_sessions.append({
                    "session": session,
                    "relevance_score": self._calculate_session_relevance(profile, session)
                })
                
        return sorted(relevant_sessions, key=lambda x: x["relevance_score"], reverse=True)[:5]

    def _calculate_session_relevance(self, profile: LearnerProfile, session: LearningSession) -> float:
        """Calculate how relevant a session is to a user."""
        score = 0.0
        
        # Subject match
        if session.subject in profile.subjects:
            score += 0.5
            
        # Skill level appropriateness
        if session.subject in profile.skill_levels:
            skill_level = profile.skill_levels[session.subject]
            # Prefer sessions slightly above current level
            if session.session_type == SessionType.TUTORING:
                score += 0.3 if skill_level <= 3 else 0.1
            else:
                score += 0.3
                
        # Time compatibility (simplified)
        session_hour = session.scheduled_start.hour
        if session_hour in profile.availability_hours:
            score += 0.2
            
        return score

    def _find_review_opportunities(self, user_id: str) -> List[Dict[str, Any]]:
        """Find peer review opportunities."""
        # This would integrate with assignment system
        # For now, return empty list
        return []

    def _find_joinable_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Find group projects the user can join."""
        profile = self.learner_profiles[user_id]
        joinable_projects = []
        
        for project in self.group_projects.values():
            if (user_id not in project.members and
                len(project.members) < project.max_members):
                
                # Check if project aligns with user's interests
                # (This would need more context about project subjects)
                joinable_projects.append({
                    "project": project,
                    "available_roles": [role for role in ProjectRole 
                                      if role not in project.members.values()]
                })
                
        return joinable_projects[:5]

    def _find_tutoring_opportunities(self, user_id: str) -> List[Dict[str, Any]]:
        """Find tutoring opportunities where user can help others."""
        profile = self.learner_profiles[user_id]
        if not profile.can_tutor_subjects:
            return []
            
        opportunities = []
        
        # Find users seeking help in subjects this user can tutor
        for other_id, other_profile in self.learner_profiles.items():
            if other_id == user_id:
                continue
                
            common_subjects = set(profile.can_tutor_subjects) & set(other_profile.seeking_help_subjects)
            if common_subjects:
                opportunities.append({
                    "student_id": other_id,
                    "subjects": list(common_subjects),
                    "skill_gap": self._calculate_skill_gap(profile, other_profile, list(common_subjects)[0])
                })
                
        return sorted(opportunities, key=lambda x: x["skill_gap"], reverse=True)[:5]

    def _calculate_skill_gap(self, tutor_profile: LearnerProfile, 
                           student_profile: LearnerProfile, subject: str) -> float:
        """Calculate skill gap between potential tutor and student."""
        if (subject not in tutor_profile.skill_levels or 
            subject not in student_profile.skill_levels):
            return 0.0
            
        return tutor_profile.skill_levels[subject] - student_profile.skill_levels[subject]