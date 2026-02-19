"""
Discussion Board System

Threaded discussions, Q&A format, teacher moderation tools,
and AI-assisted answer suggestions for EduAGI classrooms.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class PostType(Enum):
    """Types of discussion posts."""
    QUESTION = "question"
    ANSWER = "answer"
    COMMENT = "comment"
    ANNOUNCEMENT = "announcement"
    RESOURCE = "resource"


class PostStatus(Enum):
    """Status of discussion posts."""
    ACTIVE = "active"
    HIDDEN = "hidden"
    FLAGGED = "flagged"
    DELETED = "deleted"
    PINNED = "pinned"


class ModerationAction(Enum):
    """Moderation actions available to teachers."""
    APPROVE = "approve"
    HIDE = "hide"
    DELETE = "delete"
    PIN = "pin"
    UNPIN = "unpin"
    MARK_SOLUTION = "mark_solution"
    UNMARK_SOLUTION = "unmark_solution"


@dataclass
class Vote:
    """Vote on a discussion post."""
    user_id: str
    vote_type: str  # "up", "down", "helpful", "unhelpful"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Attachment:
    """File attachment for discussion posts."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    filename: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = ""
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DiscussionPost:
    """Individual discussion post with threading support."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str = ""
    parent_id: Optional[str] = None  # For replies/threading
    
    # Content
    title: str = ""
    content: str = ""
    post_type: PostType = PostType.QUESTION
    attachments: List[Attachment] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Author info
    author_id: str = ""
    author_role: str = "student"  # student, teacher, ai_assistant
    anonymous: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Status and moderation
    status: PostStatus = PostStatus.ACTIVE
    moderated_by: Optional[str] = None
    moderated_at: Optional[datetime] = None
    
    # Engagement
    votes: Dict[str, Vote] = field(default_factory=dict)  # user_id -> vote
    views: Set[str] = field(default_factory=set)  # user_ids who viewed
    
    # Q&A specific
    is_solution: bool = False
    solution_confirmed_by: Optional[str] = None
    
    # AI assistance
    ai_suggested: bool = False
    ai_confidence: Optional[float] = None


@dataclass
class DiscussionThread:
    """Discussion thread containing posts."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    classroom_id: str = ""
    
    # Metadata
    title: str = ""
    description: str = ""
    category: str = "general"  # general, homework, project, quiz, etc.
    
    # Configuration
    qa_mode: bool = False  # Q&A format vs free discussion
    allow_anonymous: bool = True
    require_moderation: bool = False
    locked: bool = False
    
    # Association
    assignment_id: Optional[str] = None
    topic_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Posts
    posts: Dict[str, DiscussionPost] = field(default_factory=dict)
    
    # Statistics
    total_posts: int = 0
    unique_participants: Set[str] = field(default_factory=set)
    
    # Pinned and featured
    pinned: bool = False
    featured: bool = False


class DiscussionBoard:
    """
    Comprehensive discussion board system.
    
    Supports threaded discussions, Q&A format, teacher moderation,
    AI-assisted suggestions, and engagement tracking.
    """
    
    def __init__(self, classroom_id: str):
        """Initialize discussion board for a classroom."""
        self.classroom_id = classroom_id
        self.threads: Dict[str, DiscussionThread] = {}
        
        # Configuration
        self.moderation_enabled = True
        self.ai_suggestions_enabled = True
        self.anonymous_posts_allowed = True
        
        # Categories
        self.categories = {
            "general": "General Discussion",
            "homework": "Homework Help", 
            "projects": "Project Collaboration",
            "quizzes": "Quiz Questions",
            "resources": "Learning Resources",
            "announcements": "Teacher Announcements"
        }
        
        # AI suggestion templates
        self.ai_templates = {
            "homework_help": "Here are some steps to approach this problem:",
            "concept_explanation": "Let me explain this concept:",
            "resource_suggestion": "You might find these resources helpful:",
        }

    def create_thread(self, title: str, description: str, creator_id: str,
                     category: str = "general", qa_mode: bool = False,
                     assignment_id: Optional[str] = None) -> DiscussionThread:
        """Create a new discussion thread."""
        thread = DiscussionThread(
            classroom_id=self.classroom_id,
            title=title,
            description=description,
            category=category,
            qa_mode=qa_mode,
            assignment_id=assignment_id
        )
        
        self.threads[thread.id] = thread
        
        # Create initial post if description is substantial
        if description and len(description) > 50:
            self.create_post(
                thread_id=thread.id,
                title=title,
                content=description,
                author_id=creator_id,
                post_type=PostType.ANNOUNCEMENT if category == "announcements" else PostType.QUESTION
            )
            
        return thread

    def create_post(self, thread_id: str, title: str, content: str, 
                   author_id: str, author_role: str = "student",
                   post_type: PostType = PostType.QUESTION,
                   parent_id: Optional[str] = None,
                   anonymous: bool = False,
                   attachments: List[Attachment] = None,
                   tags: List[str] = None) -> DiscussionPost:
        """Create a new discussion post."""
        thread = self.threads.get(thread_id)
        if not thread:
            raise ValueError("Thread not found")
            
        if thread.locked and author_role != "teacher":
            raise ValueError("Thread is locked")
            
        # Validate anonymous posting
        if anonymous and not (thread.allow_anonymous and self.anonymous_posts_allowed):
            raise ValueError("Anonymous posting not allowed")
            
        post = DiscussionPost(
            thread_id=thread_id,
            parent_id=parent_id,
            title=title,
            content=content,
            post_type=post_type,
            author_id=author_id,
            author_role=author_role,
            anonymous=anonymous,
            attachments=attachments or [],
            tags=tags or [],
            status=PostStatus.ACTIVE if not thread.require_moderation or author_role == "teacher" 
                   else PostStatus.HIDDEN
        )
        
        # Add to thread
        thread.posts[post.id] = post
        thread.total_posts += 1
        thread.unique_participants.add(author_id)
        thread.last_activity = datetime.now(timezone.utc)
        
        # Generate AI suggestion if appropriate
        if (self.ai_suggestions_enabled and post_type == PostType.QUESTION 
            and author_role == "student"):
            self._generate_ai_suggestion(thread_id, post.id)
            
        return post

    def reply_to_post(self, thread_id: str, parent_post_id: str, 
                     content: str, author_id: str, author_role: str = "student",
                     anonymous: bool = False) -> DiscussionPost:
        """Reply to an existing post."""
        thread = self.threads.get(thread_id)
        if not thread or parent_post_id not in thread.posts:
            raise ValueError("Thread or parent post not found")
            
        parent_post = thread.posts[parent_post_id]
        
        # Determine post type based on context
        post_type = PostType.ANSWER if parent_post.post_type == PostType.QUESTION else PostType.COMMENT
        
        return self.create_post(
            thread_id=thread_id,
            title=f"Re: {parent_post.title}",
            content=content,
            author_id=author_id,
            author_role=author_role,
            post_type=post_type,
            parent_id=parent_post_id,
            anonymous=anonymous
        )

    def vote_on_post(self, thread_id: str, post_id: str, user_id: str, 
                    vote_type: str = "up") -> bool:
        """Vote on a discussion post."""
        thread = self.threads.get(thread_id)
        if not thread or post_id not in thread.posts:
            return False
            
        post = thread.posts[post_id]
        
        # Remove existing vote if present
        if user_id in post.votes:
            del post.votes[user_id]
            
        # Add new vote
        if vote_type in ["up", "down", "helpful", "unhelpful"]:
            post.votes[user_id] = Vote(user_id=user_id, vote_type=vote_type)
            
        thread.last_activity = datetime.now(timezone.utc)
        return True

    def mark_as_solution(self, thread_id: str, post_id: str, 
                        confirmed_by: str) -> bool:
        """Mark a post as the solution to a question."""
        thread = self.threads.get(thread_id)
        if not thread or post_id not in thread.posts:
            return False
            
        post = thread.posts[post_id]
        
        # Only allow for answers in Q&A mode
        if not thread.qa_mode or post.post_type != PostType.ANSWER:
            return False
            
        # Unmark other solutions in the thread
        for other_post in thread.posts.values():
            if other_post.is_solution:
                other_post.is_solution = False
                other_post.solution_confirmed_by = None
                
        # Mark as solution
        post.is_solution = True
        post.solution_confirmed_by = confirmed_by
        
        return True

    def moderate_post(self, thread_id: str, post_id: str, action: ModerationAction,
                     moderator_id: str, reason: str = "") -> bool:
        """Apply moderation action to a post."""
        thread = self.threads.get(thread_id)
        if not thread or post_id not in thread.posts:
            return False
            
        post = thread.posts[post_id]
        
        # Apply moderation action
        if action == ModerationAction.APPROVE:
            post.status = PostStatus.ACTIVE
        elif action == ModerationAction.HIDE:
            post.status = PostStatus.HIDDEN
        elif action == ModerationAction.DELETE:
            post.status = PostStatus.DELETED
        elif action == ModerationAction.PIN:
            post.status = PostStatus.PINNED
        elif action == ModerationAction.UNPIN:
            post.status = PostStatus.ACTIVE
        elif action == ModerationAction.MARK_SOLUTION:
            return self.mark_as_solution(thread_id, post_id, moderator_id)
        elif action == ModerationAction.UNMARK_SOLUTION:
            post.is_solution = False
            post.solution_confirmed_by = None
            
        post.moderated_by = moderator_id
        post.moderated_at = datetime.now(timezone.utc)
        
        return True

    def search_discussions(self, query: str, category: Optional[str] = None,
                          post_type: Optional[PostType] = None,
                          author_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search through discussions."""
        results = []
        query_lower = query.lower()
        
        for thread in self.threads.values():
            # Filter by category
            if category and thread.category != category:
                continue
                
            thread_match = False
            
            # Check thread title/description
            if (query_lower in thread.title.lower() or 
                query_lower in thread.description.lower()):
                thread_match = True
                
            # Check posts in thread
            matching_posts = []
            for post in thread.posts.values():
                if post.status in [PostStatus.DELETED, PostStatus.HIDDEN]:
                    continue
                    
                # Filter by post type
                if post_type and post.post_type != post_type:
                    continue
                    
                # Filter by author
                if author_id and post.author_id != author_id:
                    continue
                    
                # Check content match
                if (query_lower in post.title.lower() or 
                    query_lower in post.content.lower() or
                    any(query_lower in tag.lower() for tag in post.tags)):
                    matching_posts.append(post)
                    thread_match = True
                    
            if thread_match:
                results.append({
                    "thread": thread,
                    "matching_posts": matching_posts,
                    "relevance_score": len(matching_posts)
                })
                
        # Sort by relevance
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    def get_thread_summary(self, thread_id: str, user_id: str) -> Dict[str, Any]:
        """Get comprehensive thread summary."""
        thread = self.threads.get(thread_id)
        if not thread:
            return {}
            
        # Mark thread as viewed
        for post in thread.posts.values():
            post.views.add(user_id)
            
        # Calculate engagement metrics
        total_votes = sum(len(post.votes) for post in thread.posts.values())
        total_views = len(set().union(*(post.views for post in thread.posts.values())))
        
        # Get post hierarchy for threading
        root_posts = [p for p in thread.posts.values() if not p.parent_id]
        
        def build_post_tree(post: DiscussionPost) -> Dict[str, Any]:
            children = [p for p in thread.posts.values() if p.parent_id == post.id]
            return {
                "post": post,
                "children": [build_post_tree(child) for child in 
                           sorted(children, key=lambda x: x.created_at)],
                "vote_score": self._calculate_vote_score(post),
                "is_solution": post.is_solution
            }
            
        post_tree = [build_post_tree(post) for post in 
                    sorted(root_posts, key=lambda x: (not x.is_solution, x.created_at))]
        
        return {
            "thread": thread,
            "post_tree": post_tree,
            "statistics": {
                "total_posts": thread.total_posts,
                "unique_participants": len(thread.unique_participants),
                "total_votes": total_votes,
                "total_views": total_views,
                "has_solution": any(p.is_solution for p in thread.posts.values()),
                "last_activity": thread.last_activity
            }
        }

    def _calculate_vote_score(self, post: DiscussionPost) -> int:
        """Calculate net vote score for a post."""
        score = 0
        for vote in post.votes.values():
            if vote.vote_type in ["up", "helpful"]:
                score += 1
            elif vote.vote_type in ["down", "unhelpful"]:
                score -= 1
        return score

    def _generate_ai_suggestion(self, thread_id: str, post_id: str) -> Optional[DiscussionPost]:
        """Generate AI-assisted answer suggestion."""
        thread = self.threads.get(thread_id)
        if not thread or post_id not in thread.posts:
            return None
            
        question_post = thread.posts[post_id]
        
        # Simple AI suggestion logic (would be enhanced with actual AI)
        suggestion_content = self._get_ai_suggestion_content(question_post)
        
        if suggestion_content:
            ai_post = self.create_post(
                thread_id=thread_id,
                title=f"AI Suggestion: {question_post.title}",
                content=suggestion_content,
                author_id="ai_assistant",
                author_role="ai_assistant",
                post_type=PostType.ANSWER,
                parent_id=post_id
            )
            
            ai_post.ai_suggested = True
            ai_post.ai_confidence = 0.7  # Mock confidence score
            
            return ai_post
            
        return None

    def _get_ai_suggestion_content(self, question_post: DiscussionPost) -> Optional[str]:
        """Generate AI suggestion content based on question."""
        content = question_post.content.lower()
        
        # Simple keyword-based suggestions (would use actual AI)
        if any(word in content for word in ["how", "what", "explain"]):
            return (
                "Here are some key points to consider:\n\n"
                "1. Break down the problem into smaller parts\n"
                "2. Review related course materials\n"
                "3. Consider similar examples from class\n\n"
                "Would you like to discuss any specific aspect in more detail?"
            )
        elif any(word in content for word in ["homework", "assignment"]):
            return (
                "For homework help:\n\n"
                "• Check the assignment requirements carefully\n"
                "• Review relevant lecture notes\n"
                "• Try working through similar practice problems\n"
                "• Don't hesitate to ask for clarification on specific steps\n\n"
                "What specific part are you having trouble with?"
            )
        elif any(word in content for word in ["error", "bug", "not working"]):
            return (
                "When troubleshooting:\n\n"
                "1. Check your input data and format\n"
                "2. Review error messages carefully\n"
                "3. Test with simpler examples first\n"
                "4. Compare with working examples\n\n"
                "Can you share the specific error message you're seeing?"
            )
            
        return None

    def get_popular_threads(self, limit: int = 10, 
                           time_period_days: int = 7) -> List[Dict[str, Any]]:
        """Get most popular threads by engagement."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_period_days)
        
        thread_scores = []
        for thread in self.threads.values():
            if thread.last_activity < cutoff_date:
                continue
                
            # Calculate popularity score
            recent_posts = sum(1 for p in thread.posts.values() 
                             if p.created_at > cutoff_date and p.status == PostStatus.ACTIVE)
            total_votes = sum(len(p.votes) for p in thread.posts.values())
            unique_participants = len(thread.unique_participants)
            
            score = recent_posts * 2 + total_votes + unique_participants * 3
            
            thread_scores.append({
                "thread": thread,
                "score": score,
                "recent_activity": recent_posts,
                "engagement": total_votes + unique_participants
            })
            
        return sorted(thread_scores, key=lambda x: x["score"], reverse=True)[:limit]

    def get_unanswered_questions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get questions that haven't been answered yet."""
        unanswered = []
        
        for thread in self.threads.values():
            if not thread.qa_mode:
                continue
                
            for post in thread.posts.values():
                if (post.post_type == PostType.QUESTION and 
                    post.status == PostStatus.ACTIVE and
                    not post.is_solution):
                    
                    # Check if there are any answers
                    has_answers = any(p.parent_id == post.id and p.post_type == PostType.ANSWER
                                    for p in thread.posts.values())
                    
                    if not has_answers:
                        age_hours = (datetime.now(timezone.utc) - post.created_at).total_seconds() / 3600
                        unanswered.append({
                            "post": post,
                            "thread": thread,
                            "age_hours": age_hours,
                            "votes": self._calculate_vote_score(post)
                        })
                        
        return sorted(unanswered, key=lambda x: (x["votes"], -x["age_hours"]), reverse=True)[:limit]

    def export_thread_data(self, thread_id: str) -> Dict[str, Any]:
        """Export thread data for analysis or backup."""
        thread = self.threads.get(thread_id)
        if not thread:
            return {}
            
        return {
            "thread_metadata": {
                "id": thread.id,
                "title": thread.title,
                "description": thread.description,
                "category": thread.category,
                "qa_mode": thread.qa_mode,
                "created_at": thread.created_at.isoformat(),
                "last_activity": thread.last_activity.isoformat()
            },
            "posts": [{
                "id": post.id,
                "parent_id": post.parent_id,
                "title": post.title,
                "content": post.content,
                "post_type": post.post_type.value,
                "author_id": post.author_id if not post.anonymous else "anonymous",
                "author_role": post.author_role,
                "created_at": post.created_at.isoformat(),
                "status": post.status.value,
                "is_solution": post.is_solution,
                "vote_score": self._calculate_vote_score(post),
                "view_count": len(post.views),
                "tags": post.tags
            } for post in thread.posts.values()],
            "statistics": {
                "total_posts": thread.total_posts,
                "unique_participants": len(thread.unique_participants),
                "total_votes": sum(len(p.votes) for p in thread.posts.values()),
                "solutions_count": sum(1 for p in thread.posts.values() if p.is_solution)
            }
        }