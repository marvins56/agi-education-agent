"""Sliding context window management."""
import json
import logging
from typing import List, Optional
from src.context.schemas import ContextWindow, AnnotatedMessage
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class SlidingContextWindow:
    """Manages the sliding window of active conversation messages."""
    
    def __init__(self, config: Optional[ContextWindow] = None):
        self.config = config or ContextWindow()
    
    async def update_window(self, session_id: str, memory_manager: MemoryManager) -> None:
        """Update the sliding window based on token/message limits."""
        key = f"session:{session_id}:annotated_messages"
        
        # Get current messages
        raw_messages = await memory_manager._redis.lrange(key, 0, -1)
        
        if not raw_messages:
            return
        
        # Parse messages
        messages = []
        for raw_msg in raw_messages:
            try:
                msg_data = json.loads(raw_msg)
                messages.append(AnnotatedMessage(**msg_data))
            except Exception as e:
                logger.warning(f"Failed to parse message in window: {e}")
                continue
        
        # Apply sliding window logic
        windowed_messages = await self._apply_window_logic(messages)
        
        # Store back the windowed messages
        if windowed_messages:
            await memory_manager._redis.delete(key)
            for msg in windowed_messages:
                await memory_manager._redis.rpush(key, msg.model_dump_json())
        
        logger.debug(f"Window updated for {session_id}: {len(windowed_messages)} messages")
    
    async def _apply_window_logic(self, messages: List[AnnotatedMessage]) -> List[AnnotatedMessage]:
        """Apply intelligent window management logic."""
        
        if len(messages) <= self.config.max_messages:
            total_tokens = sum(msg.token_count for msg in messages)
            if total_tokens <= self.config.max_tokens:
                return messages  # Within limits, keep all
        
        # Need to apply windowing
        if self.config.adaptive_sizing:
            return await self._adaptive_window(messages)
        else:
            return await self._fixed_window(messages)
    
    async def _adaptive_window(self, messages: List[AnnotatedMessage]) -> List[AnnotatedMessage]:
        """Adaptive windowing that prioritizes educational importance."""
        
        # Always keep minimum recent messages
        recent_messages = messages[-self.config.min_messages:]
        remaining_messages = messages[:-self.config.min_messages]
        
        # Calculate available budget
        recent_tokens = sum(msg.token_count for msg in recent_messages)
        remaining_budget = max(0, self.config.max_tokens - recent_tokens)
        
        # Score and select from remaining messages
        selected_messages = await self._select_by_educational_importance(
            remaining_messages, 
            token_budget=remaining_budget,
            message_budget=self.config.max_messages - len(recent_messages)
        )
        
        # Combine and maintain chronological order
        all_selected = selected_messages + recent_messages
        all_selected.sort(key=lambda msg: msg.timestamp)
        
        return all_selected
    
    async def _fixed_window(self, messages: List[AnnotatedMessage]) -> List[AnnotatedMessage]:
        """Simple sliding window keeping most recent messages."""
        
        # Start with recent messages and work backwards
        selected = []
        total_tokens = 0
        
        for msg in reversed(messages):
            if (len(selected) >= self.config.max_messages or 
                total_tokens + msg.token_count > self.config.max_tokens):
                break
                
            selected.append(msg)
            total_tokens += msg.token_count
        
        # Ensure minimum messages if possible
        while (len(selected) < self.config.min_messages and 
               len(selected) < len(messages)):
            idx = len(messages) - len(selected) - 1
            if idx >= 0:
                selected.append(messages[idx])
        
        selected.reverse()  # Restore chronological order
        return selected
    
    async def _select_by_educational_importance(
        self, 
        messages: List[AnnotatedMessage], 
        token_budget: int,
        message_budget: int
    ) -> List[AnnotatedMessage]:
        """Select messages based on educational importance scores."""
        
        # Score messages by educational importance
        scored_messages = []
        for msg in messages:
            score = await self._calculate_educational_importance(msg)
            scored_messages.append((score, msg))
        
        # Sort by importance (highest first)
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        
        # Select within budget constraints
        selected = []
        total_tokens = 0
        
        for score, msg in scored_messages:
            if (len(selected) >= message_budget or 
                total_tokens + msg.token_count > token_budget):
                break
                
            selected.append(msg)
            total_tokens += msg.token_count
        
        return selected
    
    async def _calculate_educational_importance(self, message: AnnotatedMessage) -> float:
        """Calculate educational importance score for a message."""
        
        base_score = 1.0
        
        # Boost for educational annotations
        for annotation in message.annotations:
            if annotation.type in ["breakthrough", "misconception", "mastery"]:
                base_score += annotation.confidence * 2.0
            elif annotation.type in ["confusion", "question"]:
                base_score += annotation.confidence * 1.5
            elif annotation.type == "insight":
                base_score += annotation.confidence * 1.8
        
        # Boost for longer, more substantive messages
        content_boost = min(len(message.content) / 200, 1.0) * 0.5
        base_score += content_boost
        
        # Boost for tutor messages with explanations
        if message.role == "assistant" and len(message.content) > 100:
            base_score += 0.3
        
        # Boost for student questions
        if message.role == "user" and "?" in message.content:
            base_score += 0.4
        
        return base_score
    
    async def force_summarization_trigger(
        self, 
        session_id: str, 
        memory_manager: MemoryManager
    ) -> bool:
        """Check if we should force summarization due to window pressure."""
        
        key = f"session:{session_id}:annotated_messages"
        message_count = await memory_manager._redis.llen(key)
        
        # Force summarization if we're significantly over limits
        if message_count > self.config.max_messages * 1.5:
            return True
        
        # Check token pressure
        raw_messages = await memory_manager._redis.lrange(key, 0, -1)
        total_tokens = 0
        
        for raw_msg in raw_messages:
            try:
                msg_data = json.loads(raw_msg)
                total_tokens += msg_data.get("token_count", 50)  # Estimate fallback
            except Exception:
                total_tokens += 50  # Rough estimate
        
        if total_tokens > self.config.max_tokens * 1.5:
            return True
        
        return False