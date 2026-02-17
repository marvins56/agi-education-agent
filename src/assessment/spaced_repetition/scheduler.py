"""Spaced repetition scheduler for optimizing learning retention."""
import asyncio
import logging
import math
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import uuid

from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class SpacedRepetitionScheduler:
    """Implements spaced repetition algorithm for optimal learning retention."""
    
    def __init__(
        self,
        memory_manager: MemoryManager
    ):
        self.memory = memory_manager
        
        # Default algorithm parameters (based on SuperMemo SM-2)
        self.default_params = {
            "initial_interval": 1,  # First review after 1 day
            "second_interval": 6,   # Second review after 6 days
            "ease_factor_default": 2.5,
            "ease_factor_min": 1.3,
            "ease_factor_max": 3.0,
            "interval_multiplier": 1.1
        }
        
        # Performance thresholds for adjusting intervals
        self.performance_thresholds = {
            "excellent": 0.9,   # 90%+ correct
            "good": 0.8,        # 80%+ correct  
            "fair": 0.6,        # 60%+ correct
            "poor": 0.4,        # 40%+ correct
            "fail": 0.0         # Below 40%
        }
        
        # Subject-specific adjustments
        self.subject_adjustments = {
            "history": {
                "fact_retention_factor": 0.9,  # Facts fade faster
                "concept_retention_factor": 1.1,  # Concepts last longer
                "date_retention_factor": 0.8   # Dates fade fastest
            }
        }
        
        # Active cards tracking
        self.student_cards = {}
    
    async def create_spaced_repetition_card(
        self,
        student_id: str,
        content_id: str,
        content_type: str,
        concept: str,
        subject: str = "history",
        difficulty: float = 0.5,
        importance: float = 1.0
    ) -> Dict[str, Any]:
        """Create a new spaced repetition card for a learning item."""
        
        logger.info(f"Creating SR card for student {student_id}, concept: {concept}")
        
        card = {
            "card_id": str(uuid.uuid4()),
            "student_id": student_id,
            "content_id": content_id,
            "content_type": content_type,  # "fact", "concept", "date", "cause_effect", etc.
            "concept": concept,
            "subject": subject,
            
            # Spaced repetition parameters
            "ease_factor": self.default_params["ease_factor_default"],
            "interval": self.default_params["initial_interval"],
            "repetition": 0,
            
            # Performance tracking
            "correct_streak": 0,
            "total_reviews": 0,
            "success_rate": 0.0,
            "last_performance": 0.0,
            
            # Scheduling
            "next_review_date": datetime.now() + timedelta(days=self.default_params["initial_interval"]),
            "last_reviewed": None,
            "created_at": datetime.now(),
            
            # Metadata
            "difficulty_rating": difficulty,
            "importance_weight": importance,
            "learning_state": "new",  # new, learning, review, mastered
            "review_history": []
        }
        
        # Store card
        await self._store_card(card)
        
        # Add to active tracking
        if student_id not in self.student_cards:
            self.student_cards[student_id] = {}
        self.student_cards[student_id][card["card_id"]] = card
        
        return card
    
    async def process_review_result(
        self,
        card_id: str,
        student_id: str,
        performance_score: float,
        response_time_seconds: Optional[float] = None,
        difficulty_rating: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process the result of a spaced repetition review."""
        
        logger.info(f"Processing review result for card {card_id}, score: {performance_score}")
        
        # Retrieve card
        card = await self._get_card(student_id, card_id)
        if not card:
            return {"error": "Card not found"}
        
        # Update performance tracking
        card["total_reviews"] += 1
        card["last_performance"] = performance_score
        card["last_reviewed"] = datetime.now()
        
        # Update success rate
        total_score = (card["success_rate"] * (card["total_reviews"] - 1)) + performance_score
        card["success_rate"] = total_score / card["total_reviews"]
        
        # Update correct streak
        if performance_score >= self.performance_thresholds["fair"]:
            card["correct_streak"] += 1
        else:
            card["correct_streak"] = 0
        
        # Determine performance category
        performance_category = self._categorize_performance(performance_score)
        
        # Calculate new interval and ease factor
        new_interval, new_ease_factor = self._calculate_next_interval(
            card, performance_score, performance_category, response_time_seconds
        )
        
        # Update card parameters
        card["interval"] = new_interval
        card["ease_factor"] = new_ease_factor
        card["repetition"] += 1
        
        # Calculate next review date
        card["next_review_date"] = datetime.now() + timedelta(days=new_interval)
        
        # Update learning state
        card["learning_state"] = self._determine_learning_state(card)
        
        # Add to review history
        review_record = {
            "review_date": datetime.now(),
            "performance_score": performance_score,
            "response_time": response_time_seconds,
            "interval": new_interval,
            "ease_factor": new_ease_factor,
            "performance_category": performance_category
        }
        card["review_history"].append(review_record)
        
        # Update difficulty rating if provided
        if difficulty_rating is not None:
            # Blend with existing rating
            card["difficulty_rating"] = (card["difficulty_rating"] * 0.7) + (difficulty_rating * 0.3)
        
        # Store updated card
        await self._store_card(card)
        
        return {
            "card_id": card_id,
            "next_review_date": card["next_review_date"],
            "interval_days": new_interval,
            "learning_state": card["learning_state"],
            "performance_category": performance_category,
            "success_rate": card["success_rate"],
            "correct_streak": card["correct_streak"]
        }
    
    def _categorize_performance(self, score: float) -> str:
        """Categorize performance score into qualitative levels."""
        
        if score >= self.performance_thresholds["excellent"]:
            return "excellent"
        elif score >= self.performance_thresholds["good"]:
            return "good"
        elif score >= self.performance_thresholds["fair"]:
            return "fair"
        elif score >= self.performance_thresholds["poor"]:
            return "poor"
        else:
            return "fail"
    
    def _calculate_next_interval(
        self,
        card: Dict[str, Any],
        performance_score: float,
        performance_category: str,
        response_time: Optional[float]
    ) -> Tuple[int, float]:
        """Calculate next review interval using modified SM-2 algorithm."""
        
        current_interval = card["interval"]
        current_ease_factor = card["ease_factor"]
        repetition = card["repetition"]
        
        # Adjust ease factor based on performance
        new_ease_factor = current_ease_factor
        
        if performance_category == "fail":
            # Reset interval, reduce ease factor
            new_interval = 1
            new_ease_factor = max(
                self.default_params["ease_factor_min"],
                current_ease_factor - 0.2
            )
        elif performance_category == "poor":
            # Reduce interval, slightly reduce ease factor
            new_interval = max(1, int(current_interval * 0.6))
            new_ease_factor = max(
                self.default_params["ease_factor_min"],
                current_ease_factor - 0.15
            )
        elif performance_category == "fair":
            # Keep current interval, maintain ease factor
            new_interval = current_interval
        elif performance_category == "good":
            # Increase interval based on ease factor
            if repetition == 0:
                new_interval = self.default_params["second_interval"]
            else:
                new_interval = int(current_interval * current_ease_factor)
            
            new_ease_factor = min(
                self.default_params["ease_factor_max"],
                current_ease_factor + 0.1
            )
        else:  # excellent
            # Increase interval significantly, increase ease factor
            if repetition == 0:
                new_interval = self.default_params["second_interval"]
            else:
                new_interval = int(current_interval * current_ease_factor * 1.3)
            
            new_ease_factor = min(
                self.default_params["ease_factor_max"],
                current_ease_factor + 0.15
            )
        
        # Apply subject-specific adjustments
        new_interval = self._apply_subject_adjustments(
            new_interval, card["subject"], card["content_type"]
        )
        
        # Apply difficulty adjustments
        difficulty_factor = 1.0 + (card["difficulty_rating"] - 0.5) * 0.5
        new_interval = max(1, int(new_interval * difficulty_factor))
        
        # Apply importance weighting (important items reviewed more frequently)
        importance_factor = 2.0 - card["importance_weight"]
        new_interval = max(1, int(new_interval * importance_factor))
        
        # Consider response time if available
        if response_time is not None:
            # If response was very quick, slightly increase interval
            # If response was slow, slightly decrease interval
            time_factor = self._calculate_time_factor(response_time, card["content_type"])
            new_interval = max(1, int(new_interval * time_factor))
        
        return new_interval, new_ease_factor
    
    def _apply_subject_adjustments(
        self,
        interval: int,
        subject: str,
        content_type: str
    ) -> int:
        """Apply subject-specific adjustments to intervals."""
        
        if subject not in self.subject_adjustments:
            return interval
        
        adjustments = self.subject_adjustments[subject]
        
        # Apply content-type specific adjustments
        if content_type == "fact" and "fact_retention_factor" in adjustments:
            interval = int(interval * adjustments["fact_retention_factor"])
        elif content_type == "concept" and "concept_retention_factor" in adjustments:
            interval = int(interval * adjustments["concept_retention_factor"])
        elif content_type == "date" and "date_retention_factor" in adjustments:
            interval = int(interval * adjustments["date_retention_factor"])
        
        return max(1, interval)
    
    def _calculate_time_factor(self, response_time: float, content_type: str) -> float:
        """Calculate adjustment factor based on response time."""
        
        # Expected response times by content type (in seconds)
        expected_times = {
            "fact": 5.0,
            "date": 3.0,
            "concept": 10.0,
            "cause_effect": 15.0
        }
        
        expected_time = expected_times.get(content_type, 8.0)
        
        # If response is much faster than expected, item might be well-learned
        if response_time < expected_time * 0.5:
            return 1.2  # Increase interval by 20%
        # If response is much slower, item might need more practice
        elif response_time > expected_time * 2.0:
            return 0.8  # Decrease interval by 20%
        else:
            return 1.0  # No adjustment
    
    def _determine_learning_state(self, card: Dict[str, Any]) -> str:
        """Determine the learning state of a card."""
        
        success_rate = card["success_rate"]
        total_reviews = card["total_reviews"]
        correct_streak = card["correct_streak"]
        interval = card["interval"]
        
        if total_reviews == 0:
            return "new"
        elif success_rate >= 0.9 and correct_streak >= 3 and interval >= 30:
            return "mastered"
        elif success_rate >= 0.7 and total_reviews >= 3:
            return "review"
        else:
            return "learning"
    
    async def get_due_reviews(
        self,
        student_id: str,
        subject: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get cards due for review for a student."""
        
        logger.info(f"Getting due reviews for student {student_id}")
        
        try:
            # Get all cards for student
            cards = await self._get_student_cards(student_id, subject)
            
            # Filter for due cards
            due_cards = []
            current_time = datetime.now()
            
            for card in cards:
                if card["next_review_date"] <= current_time:
                    # Calculate urgency score for prioritization
                    urgency_score = self._calculate_urgency_score(card, current_time)
                    card["urgency_score"] = urgency_score
                    due_cards.append(card)
            
            # Sort by urgency (most urgent first)
            due_cards.sort(key=lambda x: x["urgency_score"], reverse=True)
            
            return due_cards[:limit]
            
        except Exception as e:
            logger.error(f"Error getting due reviews: {e}")
            return []
    
    def _calculate_urgency_score(self, card: Dict[str, Any], current_time: datetime) -> float:
        """Calculate urgency score for prioritizing due reviews."""
        
        # Base urgency: how overdue is the card
        overdue_hours = (current_time - card["next_review_date"]).total_seconds() / 3600
        overdue_score = min(overdue_hours / 24, 5.0)  # Cap at 5 days overdue
        
        # Importance weighting
        importance_score = card["importance_weight"]
        
        # Difficulty weighting (harder items are more urgent)
        difficulty_score = card["difficulty_rating"]
        
        # Learning state urgency
        state_urgency = {
            "new": 1.5,
            "learning": 2.0,
            "review": 1.0,
            "mastered": 0.5
        }
        state_score = state_urgency.get(card["learning_state"], 1.0)
        
        # Low success rate items are more urgent
        success_penalty = 2.0 - card["success_rate"]
        
        total_urgency = (
            overdue_score * 0.3 +
            importance_score * 0.2 +
            difficulty_score * 0.2 +
            state_score * 0.2 +
            success_penalty * 0.1
        )
        
        return total_urgency
    
    async def create_review_session(
        self,
        student_id: str,
        subject: Optional[str] = None,
        max_cards: int = 10,
        session_duration_minutes: int = 15
    ) -> Dict[str, Any]:
        """Create an optimized review session for a student."""
        
        logger.info(f"Creating review session for student {student_id}")
        
        # Get due cards
        due_cards = await self.get_due_reviews(student_id, subject, max_cards * 2)
        
        if not due_cards:
            return {
                "session_id": str(uuid.uuid4()),
                "cards": [],
                "estimated_duration_minutes": 0,
                "message": "No cards due for review at this time!"
            }
        
        # Optimize card selection for session
        selected_cards = self._optimize_session_cards(
            due_cards, max_cards, session_duration_minutes
        )
        
        session = {
            "session_id": str(uuid.uuid4()),
            "student_id": student_id,
            "subject": subject,
            "cards": selected_cards,
            "estimated_duration_minutes": self._estimate_session_duration(selected_cards),
            "created_at": datetime.now(),
            "status": "active"
        }
        
        return session
    
    def _optimize_session_cards(
        self,
        due_cards: List[Dict[str, Any]],
        max_cards: int,
        target_duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """Optimize card selection for review session."""
        
        # Estimate time per card based on content type and difficulty
        for card in due_cards:
            card["estimated_time_seconds"] = self._estimate_card_time(card)
        
        # Select cards that fit within time budget
        selected_cards = []
        total_time_seconds = 0
        target_time_seconds = target_duration_minutes * 60
        
        # Sort by urgency score (already done in get_due_reviews)
        for card in due_cards:
            if len(selected_cards) >= max_cards:
                break
            
            card_time = card["estimated_time_seconds"]
            if total_time_seconds + card_time <= target_time_seconds:
                selected_cards.append(card)
                total_time_seconds += card_time
        
        # If we haven't filled the session, add more cards regardless of time
        while len(selected_cards) < max_cards and len(selected_cards) < len(due_cards):
            for card in due_cards:
                if card not in selected_cards:
                    selected_cards.append(card)
                    break
        
        return selected_cards
    
    def _estimate_card_time(self, card: Dict[str, Any]) -> int:
        """Estimate time needed to review a card (in seconds)."""
        
        base_times = {
            "fact": 5,
            "date": 4,
            "concept": 12,
            "cause_effect": 20,
            "timeline": 15,
            "source_analysis": 25
        }
        
        base_time = base_times.get(card["content_type"], 10)
        
        # Adjust for difficulty
        difficulty_factor = 0.5 + (card["difficulty_rating"] * 1.0)
        
        # Adjust for learning state
        state_factors = {
            "new": 1.5,
            "learning": 1.3,
            "review": 1.0,
            "mastered": 0.7
        }
        state_factor = state_factors.get(card["learning_state"], 1.0)
        
        return int(base_time * difficulty_factor * state_factor)
    
    def _estimate_session_duration(self, cards: List[Dict[str, Any]]) -> int:
        """Estimate total duration of review session."""
        
        total_seconds = sum(card.get("estimated_time_seconds", 10) for card in cards)
        return max(1, int(total_seconds / 60))  # Convert to minutes
    
    async def get_student_progress(
        self,
        student_id: str,
        subject: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive progress report for student's spaced repetition."""
        
        logger.info(f"Generating progress report for student {student_id}")
        
        try:
            cards = await self._get_student_cards(student_id, subject)
            
            if not cards:
                return {"message": "No spaced repetition data available"}
            
            # Calculate progress metrics
            progress = self._calculate_progress_metrics(cards, days_back)
            
            # Get upcoming reviews
            upcoming = await self._get_upcoming_reviews(student_id, subject, 7)  # Next 7 days
            
            return {
                "student_id": student_id,
                "subject": subject,
                "analysis_period_days": days_back,
                "total_cards": len(cards),
                "progress_metrics": progress,
                "upcoming_reviews": upcoming,
                "generated_at": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {"error": str(e)}
    
    def _calculate_progress_metrics(
        self,
        cards: List[Dict[str, Any]],
        days_back: int
    ) -> Dict[str, Any]:
        """Calculate detailed progress metrics."""
        
        if not cards:
            return {}
        
        # Learning state distribution
        state_counts = {"new": 0, "learning": 0, "review": 0, "mastered": 0}
        for card in cards:
            state = card.get("learning_state", "new")
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Success rate statistics
        success_rates = [card["success_rate"] for card in cards if card["total_reviews"] > 0]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0.0
        
        # Review activity
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_reviews = 0
        
        for card in cards:
            for review in card.get("review_history", []):
                if isinstance(review["review_date"], str):
                    review_date = datetime.fromisoformat(review["review_date"])
                else:
                    review_date = review["review_date"]
                
                if review_date >= cutoff_date:
                    recent_reviews += 1
        
        # Cards by difficulty
        difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
        for card in cards:
            difficulty = card["difficulty_rating"]
            if difficulty < 0.33:
                difficulty_distribution["easy"] += 1
            elif difficulty < 0.67:
                difficulty_distribution["medium"] += 1
            else:
                difficulty_distribution["hard"] += 1
        
        # Streak statistics
        streaks = [card["correct_streak"] for card in cards]
        avg_streak = sum(streaks) / len(streaks) if streaks else 0.0
        max_streak = max(streaks) if streaks else 0
        
        return {
            "learning_state_distribution": state_counts,
            "mastery_percentage": (state_counts["mastered"] / len(cards)) * 100,
            "average_success_rate": avg_success_rate,
            "recent_review_count": recent_reviews,
            "reviews_per_day": recent_reviews / days_back,
            "difficulty_distribution": difficulty_distribution,
            "average_correct_streak": avg_streak,
            "longest_correct_streak": max_streak,
            "total_review_sessions": sum(card["total_reviews"] for card in cards)
        }
    
    async def _get_upcoming_reviews(
        self,
        student_id: str,
        subject: Optional[str],
        days_ahead: int
    ) -> Dict[str, int]:
        """Get upcoming review counts by day."""
        
        cards = await self._get_student_cards(student_id, subject)
        
        upcoming = {}
        current_date = datetime.now().date()
        
        for i in range(days_ahead):
            date = current_date + timedelta(days=i)
            date_str = date.isoformat()
            
            count = 0
            for card in cards:
                review_date = card["next_review_date"].date()
                if review_date == date:
                    count += 1
            
            upcoming[date_str] = count
        
        return upcoming
    
    async def _store_card(self, card: Dict[str, Any]) -> None:
        """Store spaced repetition card in memory."""
        
        try:
            await self.memory.store_learning_data(
                student_id=card["student_id"],
                data_type="spaced_repetition_card",
                data=card,
                subject=card["subject"]
            )
        except Exception as e:
            logger.error(f"Error storing card: {e}")
    
    async def _get_card(self, student_id: str, card_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve spaced repetition card."""
        
        try:
            # Check active tracking first
            if student_id in self.student_cards and card_id in self.student_cards[student_id]:
                return self.student_cards[student_id][card_id]
            
            # Fallback to memory retrieval
            cards = await self._get_student_cards(student_id)
            for card in cards:
                if card["card_id"] == card_id:
                    return card
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving card: {e}")
            return None
    
    async def _get_student_cards(
        self,
        student_id: str,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all spaced repetition cards for a student."""
        
        try:
            # This would integrate with the actual memory system
            # For now, return from active tracking
            if student_id in self.student_cards:
                cards = list(self.student_cards[student_id].values())
                if subject:
                    cards = [card for card in cards if card["subject"] == subject]
                return cards
            
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving student cards: {e}")
            return []
    
    async def create_cards_from_content(
        self,
        student_id: str,
        content_items: List[Dict[str, Any]],
        subject: str = "history"
    ) -> List[Dict[str, Any]]:
        """Create spaced repetition cards from learning content."""
        
        logger.info(f"Creating {len(content_items)} SR cards from content for student {student_id}")
        
        created_cards = []
        
        for item in content_items:
            try:
                card = await self.create_spaced_repetition_card(
                    student_id=student_id,
                    content_id=item.get("content_id", str(uuid.uuid4())),
                    content_type=item.get("type", "concept"),
                    concept=item.get("concept", "Unknown concept"),
                    subject=subject,
                    difficulty=item.get("difficulty", 0.5),
                    importance=item.get("importance", 1.0)
                )
                created_cards.append(card)
                
            except Exception as e:
                logger.error(f"Error creating card for item {item}: {e}")
                continue
        
        return created_cards
    
    async def update_card_parameters(
        self,
        card_id: str,
        student_id: str,
        parameter_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update parameters of a spaced repetition card."""
        
        card = await self._get_card(student_id, card_id)
        if not card:
            return {"error": "Card not found"}
        
        # Update allowed parameters
        allowed_updates = [
            "difficulty_rating", "importance_weight", "ease_factor",
            "interval", "learning_state"
        ]
        
        for param, value in parameter_updates.items():
            if param in allowed_updates:
                card[param] = value
        
        # Recalculate next review date if interval changed
        if "interval" in parameter_updates:
            card["next_review_date"] = datetime.now() + timedelta(days=card["interval"])
        
        await self._store_card(card)
        
        return {
            "card_id": card_id,
            "updated_parameters": parameter_updates,
            "next_review_date": card["next_review_date"]
        }