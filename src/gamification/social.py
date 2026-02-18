"""
Social gamification features: StudyGroup, Leaderboard, PeerTutoring, ActivityFeed
"""

import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import random
from collections import defaultdict


class StudyGroupRole(Enum):
    """Roles within a study group"""
    OWNER = "owner"
    MODERATOR = "moderator" 
    MEMBER = "member"


class ActivityType(Enum):
    """Types of activities in the feed"""
    LEVEL_UP = "level_up"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    STREAK_MILESTONE = "streak_milestone"
    STUDY_SESSION = "study_session"
    HELPED_PEER = "helped_peer"
    JOINED_GROUP = "joined_group"
    COMPLETED_CHALLENGE = "completed_challenge"


@dataclass
class StudyGroupMember:
    """Member of a study group"""
    user_id: str
    username: str
    role: StudyGroupRole
    join_date: datetime.datetime
    contribution_score: int = 0  # Based on helping others, participation
    last_active: datetime.datetime = field(default_factory=datetime.datetime.now)


@dataclass
class StudyGroup:
    """Study group for collaborative learning"""
    id: str
    name: str
    description: str
    subject: str
    owner_id: str
    created_date: datetime.datetime
    members: Dict[str, StudyGroupMember] = field(default_factory=dict)
    max_members: int = 20
    is_public: bool = True
    tags: List[str] = field(default_factory=list)
    group_xp: int = 0  # Collective XP earned by group
    
    def add_member(self, user_id: str, username: str, role: StudyGroupRole = StudyGroupRole.MEMBER) -> bool:
        """Add a member to the study group"""
        if len(self.members) >= self.max_members:
            return False
            
        if user_id in self.members:
            return False  # Already a member
            
        member = StudyGroupMember(
            user_id=user_id,
            username=username,
            role=role,
            join_date=datetime.datetime.now()
        )
        self.members[user_id] = member
        return True
        
    def remove_member(self, user_id: str) -> bool:
        """Remove a member from the study group"""
        if user_id in self.members:
            del self.members[user_id]
            return True
        return False
        
    def update_member_activity(self, user_id: str):
        """Update member's last active timestamp"""
        if user_id in self.members:
            self.members[user_id].last_active = datetime.datetime.now()
            
    def add_contribution_score(self, user_id: str, points: int):
        """Add to member's contribution score"""
        if user_id in self.members:
            self.members[user_id].contribution_score += points
            
    def get_member_rankings(self) -> List[StudyGroupMember]:
        """Get members ranked by contribution score"""
        return sorted(self.members.values(), 
                     key=lambda m: m.contribution_score, reverse=True)


@dataclass
class LeaderboardEntry:
    """Entry in a leaderboard"""
    user_id: str
    username: str
    score: int
    rank: int
    level: int
    title: str
    streak: int = 0
    last_active: datetime.datetime = field(default_factory=datetime.datetime.now)


class LeaderboardScope(Enum):
    """Scope of leaderboard"""
    GLOBAL = "global"
    CLASS = "class"
    SCHOOL = "school"
    STUDY_GROUP = "study_group"


@dataclass
class PeerTutoringRequest:
    """Request for peer tutoring help"""
    id: str
    requester_id: str
    requester_username: str
    subject: str
    topic: str
    description: str
    difficulty_level: str  # "beginner", "intermediate", "advanced"
    created_date: datetime.datetime
    resolved: bool = False
    tutor_id: Optional[str] = None
    tutor_username: Optional[str] = None
    resolved_date: Optional[datetime.datetime] = None
    rating: Optional[int] = None  # 1-5 stars


@dataclass
class ActivityFeedItem:
    """Item in the activity feed"""
    id: str
    user_id: str
    username: str
    activity_type: ActivityType
    title: str
    description: str
    timestamp: datetime.datetime
    metadata: Dict = field(default_factory=dict)
    likes: Set[str] = field(default_factory=set)  # Set of user_ids who liked
    
    def add_like(self, user_id: str) -> bool:
        """Add a like from a user"""
        if user_id not in self.likes:
            self.likes.add(user_id)
            return True
        return False
        
    def remove_like(self, user_id: str) -> bool:
        """Remove a like from a user"""
        if user_id in self.likes:
            self.likes.remove(user_id)
            return True
        return False


class StudyGroupManager:
    """Manages study groups"""
    
    def __init__(self):
        self.groups: Dict[str, StudyGroup] = {}
        self.user_groups: Dict[str, Set[str]] = defaultdict(set)  # user_id -> group_ids
        
    def create_group(self, name: str, description: str, subject: str, 
                    owner_id: str, owner_username: str, is_public: bool = True) -> StudyGroup:
        """Create a new study group"""
        group_id = f"group_{datetime.datetime.now().timestamp()}_{owner_id}"
        
        group = StudyGroup(
            id=group_id,
            name=name,
            description=description,
            subject=subject,
            owner_id=owner_id,
            created_date=datetime.datetime.now(),
            is_public=is_public
        )
        
        # Add owner as first member
        group.add_member(owner_id, owner_username, StudyGroupRole.OWNER)
        
        self.groups[group_id] = group
        self.user_groups[owner_id].add(group_id)
        
        return group
        
    def join_group(self, group_id: str, user_id: str, username: str) -> bool:
        """Join a study group"""
        if group_id not in self.groups:
            return False
            
        group = self.groups[group_id]
        if group.add_member(user_id, username):
            self.user_groups[user_id].add(group_id)
            return True
        return False
        
    def leave_group(self, group_id: str, user_id: str) -> bool:
        """Leave a study group"""
        if group_id not in self.groups:
            return False
            
        group = self.groups[group_id]
        if group.remove_member(user_id):
            self.user_groups[user_id].discard(group_id)
            
            # If owner left and there are other members, transfer ownership
            if group.owner_id == user_id and group.members:
                # Transfer to member with highest contribution score
                new_owner = max(group.members.values(), 
                              key=lambda m: m.contribution_score)
                new_owner.role = StudyGroupRole.OWNER
                group.owner_id = new_owner.user_id
                
            return True
        return False
        
    def get_user_groups(self, user_id: str) -> List[StudyGroup]:
        """Get all groups a user belongs to"""
        user_group_ids = self.user_groups.get(user_id, set())
        return [self.groups[gid] for gid in user_group_ids if gid in self.groups]
        
    def search_groups(self, query: str = None, subject: str = None, 
                     max_results: int = 20) -> List[StudyGroup]:
        """Search for public study groups"""
        results = []
        
        for group in self.groups.values():
            if not group.is_public:
                continue
                
            if subject and group.subject.lower() != subject.lower():
                continue
                
            if query:
                query_lower = query.lower()
                if not (query_lower in group.name.lower() or 
                       query_lower in group.description.lower() or
                       any(query_lower in tag.lower() for tag in group.tags)):
                    continue
                    
            results.append(group)
            
            if len(results) >= max_results:
                break
                
        return results
        
    def record_group_activity(self, group_id: str, user_id: str, activity_type: str, xp_earned: int = 0):
        """Record member activity in a group"""
        if group_id not in self.groups:
            return
            
        group = self.groups[group_id]
        group.update_member_activity(user_id)
        group.group_xp += xp_earned
        
        # Award contribution points based on activity
        contribution_points = {
            'lesson_completed': 5,
            'helped_peer': 10,
            'challenge_completed': 7,
            'achievement_unlocked': 3
        }.get(activity_type, 1)
        
        group.add_contribution_score(user_id, contribution_points)


class Leaderboard:
    """Manages leaderboards for different scopes"""
    
    def __init__(self):
        self.leaderboards: Dict[Tuple[LeaderboardScope, str], List[LeaderboardEntry]] = {}
        
    def update_leaderboard(self, scope: LeaderboardScope, scope_id: str, 
                          entries: List[LeaderboardEntry]):
        """Update a leaderboard with new entries"""
        # Sort by score (descending) and assign ranks
        sorted_entries = sorted(entries, key=lambda e: e.score, reverse=True)
        
        for i, entry in enumerate(sorted_entries):
            entry.rank = i + 1
            
        self.leaderboards[(scope, scope_id)] = sorted_entries
        
    def get_leaderboard(self, scope: LeaderboardScope, scope_id: str = "global",
                       limit: int = 50) -> List[LeaderboardEntry]:
        """Get leaderboard entries"""
        key = (scope, scope_id)
        if key not in self.leaderboards:
            return []
            
        return self.leaderboards[key][:limit]
        
    def get_user_rank(self, scope: LeaderboardScope, scope_id: str, user_id: str) -> Optional[int]:
        """Get a specific user's rank in leaderboard"""
        entries = self.get_leaderboard(scope, scope_id)
        
        for entry in entries:
            if entry.user_id == user_id:
                return entry.rank
                
        return None
        
    def get_top_performers(self, scope: LeaderboardScope, scope_id: str, top_n: int = 3) -> List[LeaderboardEntry]:
        """Get top N performers"""
        return self.get_leaderboard(scope, scope_id, top_n)


class PeerTutoringMatcher:
    """Matches students for peer tutoring"""
    
    def __init__(self):
        self.requests: Dict[str, PeerTutoringRequest] = {}
        self.tutor_ratings: Dict[str, List[int]] = defaultdict(list)  # user_id -> [ratings]
        
    def create_request(self, requester_id: str, requester_username: str, 
                      subject: str, topic: str, description: str, 
                      difficulty_level: str) -> PeerTutoringRequest:
        """Create a new tutoring request"""
        request_id = f"req_{datetime.datetime.now().timestamp()}_{requester_id}"
        
        request = PeerTutoringRequest(
            id=request_id,
            requester_id=requester_id,
            requester_username=requester_username,
            subject=subject,
            topic=topic,
            description=description,
            difficulty_level=difficulty_level,
            created_date=datetime.datetime.now()
        )
        
        self.requests[request_id] = request
        return request
        
    def find_potential_tutors(self, request_id: str, user_levels: Dict[str, int],
                             user_subjects: Dict[str, List[str]]) -> List[Dict]:
        """Find potential tutors for a request"""
        if request_id not in self.requests:
            return []
            
        request = self.requests[request_id]
        potential_tutors = []
        
        # Define minimum level requirements based on difficulty
        min_level_requirements = {
            'beginner': 15,
            'intermediate': 30,
            'advanced': 50
        }
        
        min_level = min_level_requirements.get(request.difficulty_level, 15)
        
        for user_id, level in user_levels.items():
            if user_id == request.requester_id:
                continue  # Can't tutor yourself
                
            if level < min_level:
                continue
                
            # Check if tutor has knowledge in the subject
            user_subject_list = user_subjects.get(user_id, [])
            if request.subject not in user_subject_list:
                continue
                
            # Calculate tutor score based on level and ratings
            avg_rating = sum(self.tutor_ratings[user_id]) / len(self.tutor_ratings[user_id]) if self.tutor_ratings[user_id] else 3.0
            
            tutor_score = level * 0.7 + avg_rating * 0.3
            
            potential_tutors.append({
                'user_id': user_id,
                'level': level,
                'avg_rating': avg_rating,
                'score': tutor_score
            })
            
        # Sort by score (best matches first)
        potential_tutors.sort(key=lambda t: t['score'], reverse=True)
        return potential_tutors
        
    def assign_tutor(self, request_id: str, tutor_id: str, tutor_username: str) -> bool:
        """Assign a tutor to a request"""
        if request_id not in self.requests:
            return False
            
        request = self.requests[request_id]
        if request.resolved:
            return False
            
        request.tutor_id = tutor_id
        request.tutor_username = tutor_username
        return True
        
    def complete_session(self, request_id: str, rating: int) -> bool:
        """Mark tutoring session as complete with rating"""
        if request_id not in self.requests:
            return False
            
        request = self.requests[request_id]
        if not request.tutor_id:
            return False
            
        request.resolved = True
        request.resolved_date = datetime.datetime.now()
        request.rating = max(1, min(5, rating))  # Clamp to 1-5
        
        # Record tutor rating
        self.tutor_ratings[request.tutor_id].append(request.rating)
        
        return True
        
    def get_open_requests(self, subject: str = None, difficulty: str = None) -> List[PeerTutoringRequest]:
        """Get open tutoring requests"""
        open_requests = [req for req in self.requests.values() if not req.resolved]
        
        if subject:
            open_requests = [req for req in open_requests if req.subject == subject]
            
        if difficulty:
            open_requests = [req for req in open_requests if req.difficulty_level == difficulty]
            
        # Sort by creation date (oldest first)
        open_requests.sort(key=lambda req: req.created_date)
        return open_requests
        
    def get_tutor_stats(self, tutor_id: str) -> Dict:
        """Get statistics for a tutor"""
        completed_sessions = [req for req in self.requests.values() 
                            if req.tutor_id == tutor_id and req.resolved]
        
        ratings = self.tutor_ratings[tutor_id]
        
        return {
            'total_sessions': len(completed_sessions),
            'avg_rating': sum(ratings) / len(ratings) if ratings else 0,
            'rating_distribution': {
                str(i): ratings.count(i) for i in range(1, 6)
            },
            'subjects_tutored': list(set(req.subject for req in completed_sessions))
        }


class ActivityFeed:
    """Manages social activity feed"""
    
    def __init__(self):
        self.activities: List[ActivityFeedItem] = []
        self.max_items = 1000  # Keep last 1000 activities
        
    def add_activity(self, user_id: str, username: str, activity_type: ActivityType,
                    title: str, description: str, metadata: Dict = None) -> ActivityFeedItem:
        """Add a new activity to the feed"""
        activity_id = f"activity_{datetime.datetime.now().timestamp()}_{user_id}"
        
        activity = ActivityFeedItem(
            id=activity_id,
            user_id=user_id,
            username=username,
            activity_type=activity_type,
            title=title,
            description=description,
            timestamp=datetime.datetime.now(),
            metadata=metadata or {}
        )
        
        self.activities.insert(0, activity)  # Add to beginning (most recent first)
        
        # Trim old activities if necessary
        if len(self.activities) > self.max_items:
            self.activities = self.activities[:self.max_items]
            
        return activity
        
    def get_feed(self, user_id: str = None, activity_types: List[ActivityType] = None,
                limit: int = 50, offset: int = 0) -> List[ActivityFeedItem]:
        """Get activity feed items"""
        activities = self.activities
        
        # Filter by user if specified
        if user_id:
            activities = [a for a in activities if a.user_id == user_id]
            
        # Filter by activity types if specified
        if activity_types:
            activities = [a for a in activities if a.activity_type in activity_types]
            
        # Apply pagination
        start = offset
        end = offset + limit
        return activities[start:end]
        
    def get_user_feed(self, user_id: str, friend_ids: Set[str], limit: int = 50) -> List[ActivityFeedItem]:
        """Get personalized feed for a user (their activities + friends' activities)"""
        relevant_user_ids = {user_id} | friend_ids
        
        user_activities = [a for a in self.activities if a.user_id in relevant_user_ids]
        return user_activities[:limit]
        
    def like_activity(self, activity_id: str, user_id: str) -> bool:
        """Like an activity"""
        activity = self._find_activity(activity_id)
        if activity:
            return activity.add_like(user_id)
        return False
        
    def unlike_activity(self, activity_id: str, user_id: str) -> bool:
        """Unlike an activity"""
        activity = self._find_activity(activity_id)
        if activity:
            return activity.remove_like(user_id)
        return False
        
    def _find_activity(self, activity_id: str) -> Optional[ActivityFeedItem]:
        """Find an activity by ID"""
        for activity in self.activities:
            if activity.id == activity_id:
                return activity
        return None
        
    def get_trending_activities(self, hours: int = 24, limit: int = 10) -> List[ActivityFeedItem]:
        """Get trending activities based on likes in recent hours"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        recent_activities = [a for a in self.activities if a.timestamp >= cutoff_time]
        
        # Sort by number of likes (descending)
        trending = sorted(recent_activities, key=lambda a: len(a.likes), reverse=True)
        
        return trending[:limit]


class SocialGamificationManager:
    """Main manager for all social gamification features"""
    
    def __init__(self):
        self.study_group_manager = StudyGroupManager()
        self.leaderboard = Leaderboard()
        self.peer_tutoring = PeerTutoringMatcher()
        self.activity_feed = ActivityFeed()
        
    def handle_user_event(self, user_id: str, username: str, event_type: str, event_data: Dict):
        """Handle user events and update social features accordingly"""
        
        # Update activity feed
        if event_type == 'level_up':
            self.activity_feed.add_activity(
                user_id, username, ActivityType.LEVEL_UP,
                f"Level Up! 🎉",
                f"{username} reached level {event_data.get('new_level')}!",
                event_data
            )
            
        elif event_type == 'achievement_unlocked':
            self.activity_feed.add_activity(
                user_id, username, ActivityType.ACHIEVEMENT_UNLOCKED,
                f"Achievement Unlocked! 🏆",
                f"{username} earned the '{event_data.get('achievement_name')}' achievement!",
                event_data
            )
            
        elif event_type == 'streak_milestone':
            streak = event_data.get('streak', 0)
            if streak in [7, 30, 100, 365]:  # Notable milestones
                self.activity_feed.add_activity(
                    user_id, username, ActivityType.STREAK_MILESTONE,
                    f"Streak Milestone! 🔥",
                    f"{username} has studied for {streak} consecutive days!",
                    event_data
                )
                
        elif event_type == 'peer_help':
            self.activity_feed.add_activity(
                user_id, username, ActivityType.HELPED_PEER,
                f"Helping Hand 🤝",
                f"{username} helped a fellow student with {event_data.get('subject', 'studies')}!",
                event_data
            )
            
        # Update study group activities
        user_groups = self.study_group_manager.get_user_groups(user_id)
        for group in user_groups:
            self.study_group_manager.record_group_activity(
                group.id, user_id, event_type, event_data.get('xp_earned', 0)
            )
            
    def get_social_dashboard(self, user_id: str) -> Dict:
        """Get comprehensive social dashboard for a user"""
        user_groups = self.study_group_manager.get_user_groups(user_id)
        recent_activities = self.activity_feed.get_feed(user_id=user_id, limit=10)
        
        # Get user's ranks in different leaderboards
        global_rank = self.leaderboard.get_user_rank(LeaderboardScope.GLOBAL, "global", user_id)
        
        # Get tutoring stats
        tutor_stats = self.peer_tutoring.get_tutor_stats(user_id)
        
        return {
            'study_groups': {
                'joined': len(user_groups),
                'groups': [{'id': g.id, 'name': g.name, 'subject': g.subject, 
                          'members': len(g.members)} for g in user_groups]
            },
            'leaderboard': {
                'global_rank': global_rank,
                'trending_activities': self.activity_feed.get_trending_activities()
            },
            'peer_tutoring': tutor_stats,
            'recent_activities': recent_activities
        }