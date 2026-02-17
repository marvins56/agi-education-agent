# Adaptive Learning Engine Implementation

**Document:** 03_ADAPTIVE_LEARNING_ENGINE.md  
**Version:** 1.0  
**Date:** February 17, 2026  
**Dependencies:** PyTorch, scikit-learn, PostgreSQL, Redis, ChromaDB  

---

## Overview

This document details the implementation of the Adaptive Learning Engine that uses Deep Knowledge Tracing (DKT) neural networks combined with Free-Spaced Repetition Scheduler (FSRS) algorithms to create personalized learning experiences for History education.

## Current State Analysis

### Existing Mastery Tracking (src/models/mastery.py)
```python
class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject = Column(String(100), nullable=False)
    topic = Column(String(255), nullable=False)
    mastery_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    attempts = Column(Integer, nullable=False, default=0)
    last_assessed = Column(DateTime, nullable=True)
    last_reviewed = Column(DateTime, nullable=True)
    decay_rate = Column(Float, nullable=True)
```

### Problems with Current System
1. **Static Scoring**: Simple mastery scores don't capture learning dynamics
2. **No Knowledge Dependencies**: Doesn't model how concepts build on each other
3. **No Temporal Modeling**: Ignores forgetting curves and learning patterns
4. **Limited Adaptation**: Cannot predict optimal learning sequences
5. **No Spaced Repetition**: Basic decay rate without sophisticated scheduling

### What We Keep
- Basic mastery storage infrastructure
- PostgreSQL storage for persistence
- Student-topic association model
- Assessment attempt tracking

### What We Replace
- Static mastery scoring with dynamic DKT modeling
- Simple decay rates with FSRS scheduling
- Independent topic tracking with knowledge graph dependencies

---

## Architecture Design

### Adaptive Learning Engine Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 ADAPTIVE LEARNING ENGINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ INPUT: Student interaction sequence                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ [Q: WWI causes] → [Correct: Alliance system] →             │ │
│ │ [Q: Economic factors] → [Incorrect: Missed imperialism] →   │ │
│ │ [Hint given] → [Q: Follow-up] → [Correct] → ...            │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │              SEQUENCE ENCODER                               │ │
│ │ • One-hot concept encoding                                  │ │
│ │ • Correctness binary encoding                               │ │
│ │ • Context features (time, difficulty, hints)               │ │
│ │ • Attention to previous interactions                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                 DKT NEURAL NETWORK                          │ │
│ │  Input Layer (concepts + context)                          │ │
│ │       │                                                     │ │
│ │       ▼                                                     │ │
│ │  ┌─────────┐   ┌─────────┐   ┌─────────┐                  │ │
│ │  │ LSTM    │→  │ LSTM    │→  │ LSTM    │                  │ │
│ │  │ Layer 1 │   │ Layer 2 │   │ Layer 3 │                  │ │
│ │  │ h=512   │   │ h=256   │   │ h=128   │                  │ │
│ │  └─────────┘   └─────────┘   └─────────┘                  │ │
│ │       │                                                     │ │
│ │       ▼                                                     │ │
│ │  ┌─────────────────────────────────────────┐               │ │
│ │  │ Attention Layer (concept relationships) │               │ │
│ │  └─────────────────────────────────────────┘               │ │
│ │       │                                                     │ │
│ │       ▼                                                     │ │
│ │  ┌─────────────────────────────────────────┐               │ │
│ │  │ Dense Layer → Dropout → Output         │               │ │
│ │  │ (512 History concepts)                  │               │ │
│ │  └─────────────────────────────────────────┘               │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │              KNOWLEDGE STATE VECTOR                         │ │
│ │ WWI_political_causes: 0.85    Economic_imperialism: 0.32   │ │
│ │ Alliance_system: 0.91         Nationalism: 0.67            │ │
│ │ Trench_warfare: 0.78         Treaty_of_Versailles: 0.45    │ │
│ │ ... (512 History concepts)                                  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │                   FSRS SCHEDULER                            │ │
│ │ For each concept:                                           │ │
│ │ • Calculate memory stability                                │ │
│ │ • Determine retrievability                                  │ │
│ │ • Schedule optimal review time                              │ │
│ │ • Adjust difficulty based on performance                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                           │                                     │
│                           ▼                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │              ADAPTIVE RECOMMENDATIONS                       │ │
│ │ • Next concept to study: "Economic causes of WWI"          │ │
│ │ • Review concepts: "Alliance system" (in 2 days)           │ │
│ │ • Difficulty adjustment: Increase scaffolding for economics│ │
│ │ • Learning path: Politics → Economics → Military → Social  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure and Implementation

### New Directory Structure
```
src/adaptive/
├── __init__.py
├── dkt/
│   ├── __init__.py
│   ├── model.py              # DKT neural network architecture
│   ├── trainer.py            # Model training pipeline
│   ├── predictor.py          # Real-time predictions
│   └── data_preparation.py   # Training data preparation
├── fsrs/
│   ├── __init__.py
│   ├── scheduler.py          # FSRS implementation
│   ├── memory_model.py       # Memory strength calculations
│   └── review_optimizer.py   # Review scheduling optimization
├── knowledge_graph/
│   ├── __init__.py
│   ├── history_graph.py      # History concept dependencies
│   ├── graph_builder.py      # Dynamic graph construction
│   └── prerequisite_tracker.py # Prerequisite relationship tracking
├── difficulty/
│   ├── __init__.py
│   ├── calibrator.py         # Dynamic difficulty calibration
│   ├── bloom_taxonomy.py     # Bloom's taxonomy integration
│   └── cognitive_load.py     # Cognitive load assessment
├── personalization/
│   ├── __init__.py
│   ├── learning_style_detector.py # Learning style detection
│   ├── pace_controller.py    # Adaptive pacing
│   └── strategy_selector.py  # Teaching strategy selection
├── engine.py                 # Main adaptive learning engine
└── schemas.py                # Data schemas and models
```

---

## Core Implementation

### 1. `src/adaptive/schemas.py` - Data Models
```python
"""Adaptive learning data schemas and models."""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field
import torch
from dataclasses import dataclass
import numpy as np


class LearningObjective(str, Enum):
    """Learning objectives aligned with Bloom's taxonomy."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class HistoryThinkingSkill(str, Enum):
    """Historical thinking skills taxonomy."""
    CHRONOLOGICAL_REASONING = "chronological_reasoning"
    CRAFTING_ARGUMENTS = "crafting_arguments"
    ANALYZING_SOURCES = "analyzing_sources"
    CONTEXTUALIZATION = "contextualization"
    SYNTHESIS = "synthesis"


class CognitiveLoadType(str, Enum):
    """Types of cognitive load."""
    INTRINSIC = "intrinsic"      # Inherent difficulty of material
    EXTRANEOUS = "extraneous"    # Poor instructional design
    GERMANE = "germane"          # Processing that builds schemas


@dataclass
class StudentInteraction:
    """Single student learning interaction."""
    student_id: str
    session_id: str
    concept_id: int               # Index in concept vocabulary
    concept_name: str
    question_type: str           # "multiple_choice", "essay", "timeline", etc.
    correctness: float           # 0.0-1.0 for partial credit
    response_time_seconds: float
    hint_count: int
    difficulty_level: float      # 0.0-1.0
    context_features: Dict[str, float]  # Additional context
    timestamp: datetime


@dataclass
class ConceptEmbedding:
    """Concept representation with relationships."""
    concept_id: int
    concept_name: str
    subject: str
    prerequisites: List[int]     # Concept IDs this depends on
    enables: List[int]           # Concept IDs this unlocks
    difficulty: float           # Inherent difficulty 0.0-1.0
    importance: float           # Curriculum importance 0.0-1.0
    embedding_vector: np.ndarray  # Dense representation


class KnowledgeState(BaseModel):
    """Student's knowledge state at a point in time."""
    student_id: str
    concept_probabilities: Dict[str, float]  # concept_name -> mastery probability
    confidence_intervals: Dict[str, Tuple[float, float]]  # confidence bounds
    knowledge_growth_rate: float
    forgetting_rate: float
    learning_efficiency: float
    last_updated: datetime
    interaction_count: int


class FSRSCard(BaseModel):
    """FSRS card state for spaced repetition."""
    concept_id: int
    concept_name: str
    student_id: str
    
    # FSRS parameters
    stability: float = Field(ge=0.0)      # Memory stability in days
    difficulty: float = Field(ge=0.0, le=10.0)  # Learning difficulty
    retrievability: float = Field(ge=0.0, le=1.0)  # Current recall probability
    
    # Scheduling
    due_date: datetime
    last_review: Optional[datetime] = None
    review_count: int = 0
    
    # Performance tracking
    average_response_time: float = 0.0
    success_rate: float = 0.0
    consecutive_successes: int = 0


class AdaptiveRecommendation(BaseModel):
    """Recommendation from adaptive learning engine."""
    student_id: str
    
    # Next learning actions
    next_concept: Optional[str] = None
    next_difficulty: float = Field(ge=0.0, le=1.0)
    teaching_strategy: str
    
    # Review recommendations  
    concepts_to_review: List[Tuple[str, datetime]]  # (concept, due_date)
    
    # Difficulty adjustments
    difficulty_adjustments: Dict[str, float]  # concept -> new difficulty
    
    # Learning path
    recommended_sequence: List[str]  # Concept names in order
    
    # Confidence metrics
    recommendation_confidence: float = Field(ge=0.0, le=1.0)
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    reasoning: str = ""


class DKTInput(BaseModel):
    """Input format for DKT model."""
    student_id: str
    interaction_sequence: List[StudentInteraction]
    concept_embeddings: Dict[int, ConceptEmbedding]
    max_sequence_length: int = 100
    
    def to_tensor(self, device: torch.device = None) -> Dict[str, torch.Tensor]:
        """Convert to PyTorch tensors for model input."""
        # Implement tensor conversion logic
        pass


class HistoryKnowledgeGraph(BaseModel):
    """Knowledge graph structure for History concepts."""
    concepts: Dict[int, ConceptEmbedding]
    prerequisite_matrix: np.ndarray  # [num_concepts, num_concepts]
    difficulty_matrix: np.ndarray    # [num_concepts, num_concepts] - difficulty relationships
    
    # History-specific structures
    chronological_ordering: Dict[str, List[int]]  # time_period -> concept_ids
    thematic_clusters: Dict[str, List[int]]       # theme -> concept_ids
    thinking_skill_mapping: Dict[HistoryThinkingSkill, List[int]]
    
    @classmethod
    def build_history_graph(cls) -> 'HistoryKnowledgeGraph':
        """Build comprehensive History knowledge graph."""
        # Implementation would load from curriculum data
        pass
```

### 2. `src/adaptive/dkt/model.py` - DKT Neural Network
```python
"""Deep Knowledge Tracing neural network implementation."""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any
import math


class MultiHeadAttention(nn.Module):
    """Multi-head attention for concept relationships."""
    
    def __init__(self, d_model: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.W_q = nn.Linear(d_model, d_model, bias=False)
        self.W_k = nn.Linear(d_model, d_model, bias=False) 
        self.W_v = nn.Linear(d_model, d_model, bias=False)
        self.W_o = nn.Linear(d_model, d_model)
        
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        batch_size = query.size(0)
        
        # Linear transformations and reshape for multi-head
        Q = self.W_q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
            
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        context = torch.matmul(attention_weights, V)
        
        # Concatenate heads and apply output projection
        context = context.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )
        
        return self.W_o(context)


class HistoryDKTModel(nn.Module):
    """Deep Knowledge Tracing model optimized for History education."""
    
    def __init__(
        self,
        num_concepts: int,
        num_questions: int = 1000,
        embedding_dim: int = 128,
        hidden_size: int = 256,
        num_layers: int = 2,
        num_attention_heads: int = 8,
        dropout: float = 0.2,
        max_sequence_length: int = 100
    ):
        super().__init__()
        
        self.num_concepts = num_concepts
        self.num_questions = num_questions
        self.embedding_dim = embedding_dim
        self.hidden_size = hidden_size
        self.max_sequence_length = max_sequence_length
        
        # Input embeddings
        self.concept_embedding = nn.Embedding(num_concepts, embedding_dim)
        self.question_embedding = nn.Embedding(num_questions, embedding_dim)
        
        # Context feature projection
        self.context_projection = nn.Linear(10, embedding_dim)  # 10 context features
        
        # Input combination layer
        input_size = embedding_dim * 3 + 1  # concept + question + context + correctness
        self.input_projection = nn.Linear(input_size, hidden_size)
        
        # LSTM layers for sequence modeling
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True,
            bidirectional=False
        )
        
        # Multi-head attention for concept relationships
        self.attention = MultiHeadAttention(hidden_size, num_attention_heads, dropout)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(hidden_size)
        
        # Output layers
        self.dropout = nn.Dropout(dropout)
        self.output_projection = nn.Linear(hidden_size, hidden_size // 2)
        self.concept_prediction = nn.Linear(hidden_size // 2, num_concepts)
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize model weights."""
        for name, param in self.named_parameters():
            if 'weight' in name and param.dim() > 1:
                nn.init.xavier_uniform_(param)
            elif 'bias' in name:
                nn.init.constant_(param, 0.0)
    
    def forward(
        self,
        concept_ids: torch.Tensor,        # [batch_size, seq_len]
        question_ids: torch.Tensor,       # [batch_size, seq_len]  
        correctness: torch.Tensor,        # [batch_size, seq_len]
        context_features: torch.Tensor,   # [batch_size, seq_len, num_features]
        mask: Optional[torch.Tensor] = None  # [batch_size, seq_len]
    ) -> torch.Tensor:
        """
        Forward pass of DKT model.
        
        Returns:
            concept_probabilities: [batch_size, seq_len, num_concepts]
        """
        batch_size, seq_len = concept_ids.shape
        
        # Embed inputs
        concept_emb = self.concept_embedding(concept_ids)      # [B, T, E]
        question_emb = self.question_embedding(question_ids)   # [B, T, E]
        context_emb = self.context_projection(context_features)  # [B, T, E]
        
        # Combine all inputs
        correctness_expanded = correctness.unsqueeze(-1)       # [B, T, 1]
        combined_input = torch.cat([
            concept_emb, question_emb, context_emb, correctness_expanded
        ], dim=-1)  # [B, T, 3E+1]
        
        # Project to hidden dimension
        hidden_input = self.input_projection(combined_input)   # [B, T, H]
        
        # LSTM processing
        lstm_output, _ = self.lstm(hidden_input)               # [B, T, H]
        
        # Apply attention for concept relationships
        attended_output = self.attention(lstm_output, lstm_output, lstm_output, mask)
        
        # Residual connection and layer norm
        lstm_output = self.layer_norm(lstm_output + attended_output)
        
        # Output projection
        output = self.dropout(lstm_output)
        output = F.relu(self.output_projection(output))
        concept_logits = self.concept_prediction(output)       # [B, T, num_concepts]
        
        # Apply sigmoid to get probabilities
        concept_probabilities = torch.sigmoid(concept_logits)
        
        return concept_probabilities
    
    def predict_next_concept_mastery(
        self,
        concept_ids: torch.Tensor,
        question_ids: torch.Tensor,
        correctness: torch.Tensor,
        context_features: torch.Tensor,
        target_concepts: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Predict mastery probability for specific concepts."""
        
        with torch.no_grad():
            concept_probs = self.forward(
                concept_ids, question_ids, correctness, context_features
            )
            
            # Take the last time step prediction
            last_step_probs = concept_probs[:, -1, :]  # [batch_size, num_concepts]
            
            if target_concepts is not None:
                # Return probabilities for specific concepts
                return torch.gather(last_step_probs, 1, target_concepts)
            
            return last_step_probs
    
    def get_concept_relationships(self) -> torch.Tensor:
        """Extract learned concept relationships from attention weights."""
        # This would extract attention patterns to understand concept dependencies
        pass


class DKTLoss(nn.Module):
    """Custom loss function for DKT training."""
    
    def __init__(self, concept_weights: Optional[torch.Tensor] = None):
        super().__init__()
        self.concept_weights = concept_weights
        self.bce_loss = nn.BCELoss(reduction='none')
    
    def forward(
        self,
        predictions: torch.Tensor,    # [batch_size, seq_len, num_concepts]
        targets: torch.Tensor,        # [batch_size, seq_len, num_concepts]
        mask: torch.Tensor            # [batch_size, seq_len]
    ) -> torch.Tensor:
        """
        Compute DKT loss with masking and optional concept weighting.
        """
        # Compute BCE loss
        loss = self.bce_loss(predictions, targets)  # [B, T, C]
        
        # Apply concept weights if provided
        if self.concept_weights is not None:
            loss = loss * self.concept_weights.unsqueeze(0).unsqueeze(0)
        
        # Apply sequence mask
        mask_expanded = mask.unsqueeze(-1).expand_as(loss)
        masked_loss = loss * mask_expanded
        
        # Average over valid positions
        total_loss = masked_loss.sum()
        total_valid = mask_expanded.sum()
        
        return total_loss / (total_valid + 1e-8)


# Model configuration for History domain
HISTORY_DKT_CONFIG = {
    "num_concepts": 512,           # Number of History concepts
    "num_questions": 2000,         # Number of unique question types
    "embedding_dim": 128,
    "hidden_size": 256,
    "num_layers": 3,
    "num_attention_heads": 8,
    "dropout": 0.2,
    "max_sequence_length": 100,
    
    # History-specific parameters
    "chronological_weight": 1.5,   # Extra weight for chronological reasoning
    "source_analysis_weight": 1.3, # Extra weight for source analysis skills
    "causation_weight": 1.4,       # Extra weight for cause-effect understanding
}
```

### 3. `src/adaptive/fsrs/scheduler.py` - FSRS Implementation
```python
"""Free-Spaced Repetition Scheduler (FSRS) implementation."""
import math
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import numpy as np

from src.adaptive.schemas import FSRSCard


@dataclass
class FSRSParameters:
    """FSRS algorithm parameters optimized for educational content."""
    # Request retention rate (target recall probability)
    request_retention: float = 0.9
    
    # Maximum interval in days
    maximum_interval: float = 36500.0  # ~100 years
    
    # FSRS-4.5 parameters (optimized for spaced repetition)
    w: List[float] = None
    
    def __post_init__(self):
        if self.w is None:
            # Default parameters optimized for educational content
            self.w = [
                0.4072,   # initial_stability_good
                1.1829,   # initial_stability_easy  
                3.1262,   # initial_stability_hard
                15.4722,  # initial_stability_again
                7.2102,   # initial_difficulty
                0.5316,   # difficulty_decay_factor
                1.0651,   # stability_decay_factor
                0.0234,   # increasing_factor
                1.616,    # hard_penalty
                0.1544,   # easy_bonus
            ]


class FSRSScheduler:
    """Free-Spaced Repetition Scheduler for optimal review timing."""
    
    def __init__(self, parameters: FSRSParameters = None):
        self.params = parameters or FSRSParameters()
        self.history_concept_weights = self._get_history_concept_weights()
    
    def _get_history_concept_weights(self) -> Dict[str, float]:
        """Get importance weights for different History concept types."""
        return {
            "political_causes": 1.3,      # High importance
            "economic_factors": 1.2,      
            "social_movements": 1.1,
            "military_strategy": 1.0,     # Base importance
            "cultural_aspects": 0.9,
            "biographical": 0.8,          # Lower priority for memorization
            "dates_specific": 0.7,        # Dates less critical than concepts
        }
    
    def schedule_review(
        self,
        card: FSRSCard,
        rating: int,        # 1=Again, 2=Hard, 3=Good, 4=Easy
        now: datetime = None
    ) -> FSRSCard:
        """Schedule next review for a concept card."""
        if now is None:
            now = datetime.now()
        
        # Update card state based on performance
        updated_card = self._update_card_state(card, rating, now)
        
        # Calculate new interval
        interval_days = self._calculate_interval(updated_card, rating)
        
        # Apply History-specific adjustments
        interval_days = self._apply_history_adjustments(
            updated_card, interval_days, rating
        )
        
        # Set due date
        updated_card.due_date = now + timedelta(days=interval_days)
        updated_card.last_review = now
        updated_card.review_count += 1
        
        # Update performance tracking
        updated_card = self._update_performance_metrics(updated_card, rating)
        
        return updated_card
    
    def _update_card_state(self, card: FSRSCard, rating: int, now: datetime) -> FSRSCard:
        """Update card's memory parameters based on performance."""
        new_card = FSRSCard(**card.dict())
        
        # Calculate elapsed days since last review
        if card.last_review:
            elapsed_days = (now - card.last_review).total_seconds() / 86400
            # Update retrievability based on elapsed time
            new_card.retrievability = self._calculate_retrievability(
                card.stability, elapsed_days
            )
        else:
            elapsed_days = 0
            new_card.retrievability = 1.0
        
        # Update difficulty based on performance
        if card.review_count > 0:  # Not first review
            new_card.difficulty = self._update_difficulty(card.difficulty, rating)
        
        return new_card
    
    def _calculate_retrievability(self, stability: float, elapsed_days: float) -> float:
        """Calculate current retrievability based on forgetting curve."""
        if elapsed_days <= 0:
            return 1.0
        
        # Exponential forgetting curve
        retrievability = math.pow(1 + elapsed_days / (9 * stability), -1)
        return max(0.01, min(1.0, retrievability))
    
    def _calculate_interval(self, card: FSRSCard, rating: int) -> float:
        """Calculate the next review interval."""
        if card.review_count == 0:
            # First review - use initial stability
            return self._get_initial_stability(rating)
        
        # Calculate new stability based on current state and performance
        current_retrievability = card.retrievability
        new_stability = self._calculate_new_stability(
            card.stability, card.difficulty, rating, current_retrievability
        )
        
        # Calculate interval to reach target retention
        interval = new_stability * (
            math.pow(self.params.request_retention, 1/9) - 1
        ) * 9
        
        # Apply bounds
        interval = max(1.0, min(self.params.maximum_interval, interval))
        
        return interval
    
    def _get_initial_stability(self, rating: int) -> float:
        """Get initial stability for first review."""
        stability_map = {
            1: self.params.w[3],  # again - very short interval
            2: self.params.w[2],  # hard - short interval
            3: self.params.w[0],  # good - medium interval
            4: self.params.w[1],  # easy - longer interval
        }
        return stability_map.get(rating, self.params.w[0])
    
    def _calculate_new_stability(
        self,
        old_stability: float,
        difficulty: float,
        rating: int,
        retrievability: float
    ) -> float:
        """Calculate new memory stability after review."""
        # Base stability calculation from FSRS algorithm
        if rating == 1:  # Again
            new_stability = old_stability * math.pow(
                self.params.w[6], math.pow(difficulty - 1, self.params.w[5])
            )
        else:  # Hard, Good, Easy
            success_rate = 1.0  # Successful recall
            if rating == 2:  # Hard
                success_rate *= self.params.w[8]  # Apply hard penalty
            elif rating == 4:  # Easy
                success_rate *= self.params.w[9]  # Apply easy bonus
            
            new_stability = old_stability * (
                1 + (math.exp(self.params.w[7]) - 1) * 
                success_rate * math.pow(retrievability, self.params.w[4])
            )
        
        return max(0.1, new_stability)  # Minimum stability
    
    def _update_difficulty(self, old_difficulty: float, rating: int) -> float:
        """Update concept difficulty based on performance."""
        # FSRS difficulty update formula
        difficulty_change = {
            1: 0.2,   # Again - increase difficulty
            2: 0.1,   # Hard - slight increase
            3: -0.05, # Good - slight decrease
            4: -0.15, # Easy - decrease difficulty
        }
        
        change = difficulty_change.get(rating, 0)
        new_difficulty = old_difficulty + change
        
        # Clamp difficulty between 1 and 10
        return max(1.0, min(10.0, new_difficulty))
    
    def _apply_history_adjustments(
        self,
        card: FSRSCard,
        base_interval: float,
        rating: int
    ) -> float:
        """Apply History-specific scheduling adjustments."""
        
        # Determine concept type from name
        concept_type = self._classify_history_concept(card.concept_name)
        weight = self.history_concept_weights.get(concept_type, 1.0)
        
        # High-importance concepts reviewed more frequently
        if weight > 1.1:
            base_interval *= 0.8  # 20% shorter intervals
        elif weight < 0.9:
            base_interval *= 1.3  # 30% longer intervals
        
        # Adjust based on concept complexity patterns
        if "cause" in card.concept_name.lower() or "effect" in card.concept_name.lower():
            # Causal relationships need more frequent review
            base_interval *= 0.9
        
        if "timeline" in card.concept_name.lower() or "chronol" in card.concept_name.lower():
            # Chronological concepts benefit from regular practice
            base_interval *= 0.85
        
        # Performance-based adjustments
        if card.success_rate < 0.6 and card.review_count > 2:
            # Struggling concepts need more frequent review
            base_interval *= 0.7
        elif card.success_rate > 0.9 and card.consecutive_successes > 3:
            # Well-mastered concepts can wait longer
            base_interval *= 1.2
        
        return base_interval
    
    def _classify_history_concept(self, concept_name: str) -> str:
        """Classify History concept type for scheduling adjustments."""
        name_lower = concept_name.lower()
        
        political_keywords = ["government", "politics", "power", "ruler", "revolution"]
        economic_keywords = ["economy", "trade", "money", "wealth", "commerce"]
        social_keywords = ["society", "culture", "people", "movement", "rights"]
        military_keywords = ["war", "battle", "military", "army", "weapon"]
        
        if any(keyword in name_lower for keyword in political_keywords):
            return "political_causes"
        elif any(keyword in name_lower for keyword in economic_keywords):
            return "economic_factors"
        elif any(keyword in name_lower for keyword in social_keywords):
            return "social_movements"
        elif any(keyword in name_lower for keyword in military_keywords):
            return "military_strategy"
        elif any(char.isdigit() for char in concept_name):
            return "dates_specific"
        else:
            return "cultural_aspects"
    
    def _update_performance_metrics(self, card: FSRSCard, rating: int) -> FSRSCard:
        """Update performance tracking metrics."""
        # Update success rate (exponential moving average)
        success = 1.0 if rating >= 3 else 0.0  # Good or Easy = success
        alpha = 0.1  # Learning rate for moving average
        card.success_rate = (1 - alpha) * card.success_rate + alpha * success
        
        # Update consecutive successes
        if rating >= 3:
            card.consecutive_successes += 1
        else:
            card.consecutive_successes = 0
        
        return card
    
    def get_due_cards(
        self,
        cards: List[FSRSCard],
        now: datetime = None
    ) -> List[FSRSCard]:
        """Get all cards due for review."""
        if now is None:
            now = datetime.now()
        
        due_cards = [card for card in cards if card.due_date <= now]
        
        # Sort by priority (overdue first, then by importance)
        due_cards.sort(key=lambda card: (
            (now - card.due_date).total_seconds(),  # How overdue
            -self.history_concept_weights.get(
                self._classify_history_concept(card.concept_name), 1.0
            )  # Importance (negative for descending sort)
        ))
        
        return due_cards
    
    def optimize_study_session(
        self,
        available_cards: List[FSRSCard],
        session_duration_minutes: int = 30,
        now: datetime = None
    ) -> List[FSRSCard]:
        """Select optimal cards for a study session."""
        if now is None:
            now = datetime.now()
        
        # Get due cards
        due_cards = self.get_due_cards(available_cards, now)
        
        # Estimate time per card (average 2-3 minutes)
        avg_time_per_card = 2.5
        max_cards = int(session_duration_minutes / avg_time_per_card)
        
        # Select high-priority cards that fit in time budget
        selected_cards = due_cards[:max_cards]
        
        # Fill remaining time with preview cards (new concepts)
        remaining_time = session_duration_minutes - len(selected_cards) * avg_time_per_card
        if remaining_time >= avg_time_per_card:
            new_cards = [card for card in available_cards if card.review_count == 0]
            additional_cards = min(
                int(remaining_time / avg_time_per_card),
                len(new_cards)
            )
            selected_cards.extend(new_cards[:additional_cards])
        
        return selected_cards
```

### 4. `src/adaptive/engine.py` - Main Adaptive Learning Engine
```python
"""Main adaptive learning engine orchestrating DKT and FSRS."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import torch
import numpy as np

from src.adaptive.schemas import (
    StudentInteraction, KnowledgeState, AdaptiveRecommendation,
    FSRSCard, ConceptEmbedding
)
from src.adaptive.dkt.model import HistoryDKTModel, HISTORY_DKT_CONFIG
from src.adaptive.dkt.predictor import DKTPredictor
from src.adaptive.fsrs.scheduler import FSRSScheduler, FSRSParameters
from src.adaptive.knowledge_graph.history_graph import HistoryKnowledgeGraph
from src.adaptive.difficulty.calibrator import DifficultyCalibrator
from src.adaptive.personalization.learning_style_detector import LearningStyleDetector
from src.memory.manager import MemoryManager

logger = logging.getLogger(__name__)


class AdaptiveLearningEngine:
    """Main engine for personalized adaptive learning."""
    
    def __init__(
        self,
        memory_manager: MemoryManager,
        model_path: Optional[str] = None,
        device: torch.device = None
    ):
        self.memory = memory_manager
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Initialize DKT model
        self.dkt_model = HistoryDKTModel(**HISTORY_DKT_CONFIG)
        if model_path:
            self.dkt_model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.dkt_model.to(self.device)
        self.dkt_model.eval()
        
        # Initialize FSRS scheduler
        self.fsrs_scheduler = FSRSScheduler(FSRSParameters())
        
        # Initialize knowledge graph
        self.knowledge_graph = HistoryKnowledgeGraph.build_history_graph()
        
        # Initialize other components
        self.difficulty_calibrator = DifficultyCalibrator(self.knowledge_graph)
        self.learning_style_detector = LearningStyleDetector()
        
        # Initialize DKT predictor
        self.dkt_predictor = DKTPredictor(self.dkt_model, self.device)
        
        # Cache for student knowledge states
        self._knowledge_state_cache: Dict[str, KnowledgeState] = {}
        self._cache_ttl_minutes = 15
    
    async def update_student_knowledge(
        self,
        student_id: str,
        interaction: StudentInteraction
    ) -> KnowledgeState:
        """Update student's knowledge state after a learning interaction."""
        
        # Get interaction history
        interaction_history = await self._get_interaction_history(student_id, limit=50)
        interaction_history.append(interaction)
        
        # Predict updated knowledge state using DKT
        knowledge_state = await self._predict_knowledge_state(
            student_id, interaction_history
        )
        
        # Update FSRS cards based on interaction
        if interaction.correctness is not None:
            await self._update_fsrs_card(student_id, interaction)
        
        # Cache the updated knowledge state
        self._knowledge_state_cache[student_id] = knowledge_state
        
        # Store in long-term memory
        await self._store_knowledge_state(knowledge_state)
        
        # Update mastery records in database
        await self._update_mastery_records(student_id, knowledge_state)
        
        return knowledge_state
    
    async def get_adaptive_recommendations(
        self,
        student_id: str,
        current_topic: Optional[str] = None,
        session_time_budget_minutes: int = 30
    ) -> AdaptiveRecommendation:
        """Generate personalized learning recommendations."""
        
        # Get current knowledge state
        knowledge_state = await self._get_knowledge_state(student_id)
        
        # Get FSRS cards for spaced repetition
        fsrs_cards = await self._get_student_fsrs_cards(student_id)
        
        # Detect learning style and preferences
        learning_style = await self.learning_style_detector.detect_style(student_id)
        
        # Generate recommendations
        recommendation = AdaptiveRecommendation(student_id=student_id)
        
        # 1. Determine next concept to learn
        next_concept = await self._recommend_next_concept(
            knowledge_state, current_topic
        )
        
        if next_concept:
            recommendation.next_concept = next_concept
            recommendation.next_difficulty = await self._calibrate_difficulty(
                student_id, next_concept, knowledge_state
            )
            recommendation.teaching_strategy = await self._select_teaching_strategy(
                student_id, next_concept, learning_style
            )
        
        # 2. Schedule reviews using FSRS
        review_cards = self.fsrs_scheduler.optimize_study_session(
            fsrs_cards, session_time_budget_minutes // 2  # Half time for reviews
        )
        recommendation.concepts_to_review = [
            (card.concept_name, card.due_date) for card in review_cards
        ]
        
        # 3. Generate learning path
        recommendation.recommended_sequence = await self._generate_learning_path(
            student_id, knowledge_state, target_concepts=5
        )
        
        # 4. Calculate recommendation confidence
        recommendation.recommendation_confidence = self._calculate_recommendation_confidence(
            knowledge_state, len(interaction_history)
        )
        
        # 5. Add reasoning
        recommendation.reasoning = self._generate_recommendation_reasoning(
            knowledge_state, next_concept, len(review_cards)
        )
        
        return recommendation
    
    async def _predict_knowledge_state(
        self,
        student_id: str,
        interaction_history: List[StudentInteraction]
    ) -> KnowledgeState:
        """Predict current knowledge state using DKT model."""
        
        if not interaction_history:
            # Return default knowledge state for new students
            return KnowledgeState(
                student_id=student_id,
                concept_probabilities={},
                confidence_intervals={},
                knowledge_growth_rate=0.5,
                forgetting_rate=0.1,
                learning_efficiency=0.5,
                last_updated=datetime.now(),
                interaction_count=0
            )
        
        # Prepare input for DKT model
        dkt_input = await self._prepare_dkt_input(student_id, interaction_history)
        
        # Get predictions from DKT model
        concept_probabilities = await self.dkt_predictor.predict_mastery(dkt_input)
        
        # Calculate confidence intervals
        confidence_intervals = await self._calculate_confidence_intervals(
            concept_probabilities, len(interaction_history)
        )
        
        # Calculate learning metrics
        growth_rate = self._calculate_knowledge_growth_rate(interaction_history)
        forgetting_rate = self._calculate_forgetting_rate(interaction_history)
        efficiency = self._calculate_learning_efficiency(interaction_history)
        
        return KnowledgeState(
            student_id=student_id,
            concept_probabilities=concept_probabilities,
            confidence_intervals=confidence_intervals,
            knowledge_growth_rate=growth_rate,
            forgetting_rate=forgetting_rate,
            learning_efficiency=efficiency,
            last_updated=datetime.now(),
            interaction_count=len(interaction_history)
        )
    
    async def _recommend_next_concept(
        self,
        knowledge_state: KnowledgeState,
        current_topic: Optional[str] = None
    ) -> Optional[str]:
        """Recommend the next concept to learn based on knowledge state."""
        
        # Get concepts with low mastery but prerequisites met
        low_mastery_concepts = []
        
        for concept_name, mastery in knowledge_state.concept_probabilities.items():
            if mastery < 0.7:  # Below mastery threshold
                # Check if prerequisites are met
                concept_id = self._get_concept_id(concept_name)
                if concept_id is not None:
                    prerequisites_met = self._check_prerequisites_met(
                        concept_id, knowledge_state.concept_probabilities
                    )
                    if prerequisites_met:
                        low_mastery_concepts.append((concept_name, mastery))
        
        if not low_mastery_concepts:
            # If all concepts are mastered, suggest advanced concepts
            return self._suggest_advanced_concept(current_topic)
        
        # Sort by mastery level (lowest first) and return best candidate
        low_mastery_concepts.sort(key=lambda x: x[1])
        
        # Consider topic context if provided
        if current_topic:
            topic_concepts = [
                (concept, mastery) for concept, mastery in low_mastery_concepts
                if current_topic.lower() in concept.lower()
            ]
            if topic_concepts:
                return topic_concepts[0][0]
        
        return low_mastery_concepts[0][0]
    
    async def _calibrate_difficulty(
        self,
        student_id: str,
        concept_name: str,
        knowledge_state: KnowledgeState
    ) -> float:
        """Calibrate difficulty level for a specific concept."""
        return await self.difficulty_calibrator.calibrate_difficulty(
            concept_name=concept_name,
            student_knowledge_state=knowledge_state,
            student_id=student_id
        )
    
    async def _select_teaching_strategy(
        self,
        student_id: str,
        concept_name: str,
        learning_style: Dict[str, float]
    ) -> str:
        """Select optimal teaching strategy based on student profile."""
        
        # Get concept characteristics
        concept_id = self._get_concept_id(concept_name)
        if concept_id is None:
            return "explanation"
        
        concept_embedding = self.knowledge_graph.concepts.get(concept_id)
        if concept_embedding is None:
            return "explanation"
        
        # Strategy selection logic based on learning style and concept type
        visual_preference = learning_style.get("visual", 0.5)
        auditory_preference = learning_style.get("auditory", 0.5)
        kinesthetic_preference = learning_style.get("kinesthetic", 0.5)
        
        # Concept-specific strategy adjustments
        if concept_embedding.difficulty > 0.7:  # Complex concept
            if visual_preference > 0.6:
                return "timeline_visualization"
            elif kinesthetic_preference > 0.6:
                return "interactive_exploration"
            else:
                return "scaffolded_explanation"
        else:  # Simple concept
            if auditory_preference > 0.6:
                return "socratic_dialogue"
            else:
                return "direct_explanation"
    
    async def _generate_learning_path(
        self,
        student_id: str,
        knowledge_state: KnowledgeState,
        target_concepts: int = 5
    ) -> List[str]:
        """Generate optimal learning sequence using knowledge graph."""
        
        # Get concepts ready to learn (prerequisites met, not yet mastered)
        ready_concepts = []
        
        for concept_id, embedding in self.knowledge_graph.concepts.items():
            mastery = knowledge_state.concept_probabilities.get(embedding.concept_name, 0.0)
            
            if mastery < 0.7:  # Not yet mastered
                prerequisites_met = self._check_prerequisites_met(
                    concept_id, knowledge_state.concept_probabilities
                )
                if prerequisites_met:
                    ready_concepts.append((embedding.concept_name, embedding.importance, mastery))
        
        # Sort by importance and current mastery level
        ready_concepts.sort(key=lambda x: (-x[1], x[2]))  # High importance, low mastery first
        
        return [concept[0] for concept in ready_concepts[:target_concepts]]
    
    def _calculate_recommendation_confidence(
        self,
        knowledge_state: KnowledgeState,
        interaction_count: int
    ) -> float:
        """Calculate confidence in recommendations based on data quality."""
        
        # Base confidence on number of interactions
        base_confidence = min(0.9, interaction_count / 50.0)  # Max confidence at 50 interactions
        
        # Adjust for knowledge state uncertainty
        avg_confidence_width = np.mean([
            interval[1] - interval[0]
            for interval in knowledge_state.confidence_intervals.values()
        ]) if knowledge_state.confidence_intervals else 0.5
        
        uncertainty_penalty = avg_confidence_width * 0.5
        
        return max(0.1, base_confidence - uncertainty_penalty)
    
    def _generate_recommendation_reasoning(
        self,
        knowledge_state: KnowledgeState,
        next_concept: Optional[str],
        review_count: int
    ) -> str:
        """Generate human-readable reasoning for recommendations."""
        
        reasoning_parts = []
        
        if next_concept:
            mastery = knowledge_state.concept_probabilities.get(next_concept, 0.0)
            reasoning_parts.append(
                f"Recommended '{next_concept}' (current mastery: {mastery:.1%}) "
                f"as it builds on your existing knowledge and has high curriculum importance."
            )
        
        if review_count > 0:
            reasoning_parts.append(
                f"Scheduled {review_count} concepts for review based on spaced repetition "
                f"to maintain long-term retention."
            )
        
        efficiency = knowledge_state.learning_efficiency
        if efficiency < 0.4:
            reasoning_parts.append(
                "Focusing on foundational concepts to improve learning efficiency."
            )
        elif efficiency > 0.8:
            reasoning_parts.append(
                "You're learning efficiently! Ready for more challenging material."
            )
        
        return " ".join(reasoning_parts)
    
    # Helper methods
    
    async def _get_interaction_history(
        self,
        student_id: str,
        limit: int = 100
    ) -> List[StudentInteraction]:
        """Get student's learning interaction history."""
        # This would query the database for learning events
        # and convert them to StudentInteraction objects
        learning_events = await self.memory.get_student_history(
            student_id, limit=limit
        )
        
        interactions = []
        for event in learning_events:
            # Convert learning event to StudentInteraction
            interaction = StudentInteraction(
                student_id=student_id,
                session_id=event.get("session_id", ""),
                concept_id=hash(event.get("topic", "")) % 1000,  # Simple hash for demo
                concept_name=event.get("topic", ""),
                question_type=event.get("event_type", "unknown"),
                correctness=self._extract_correctness(event),
                response_time_seconds=event.get("response_time", 60.0),
                hint_count=event.get("hint_count", 0),
                difficulty_level=event.get("difficulty", 0.5),
                context_features=event.get("context_features", {}),
                timestamp=datetime.fromisoformat(event.get("created_at"))
            )
            interactions.append(interaction)
        
        return interactions
    
    def _extract_correctness(self, learning_event: Dict[str, Any]) -> float:
        """Extract correctness score from learning event."""
        outcome = learning_event.get("outcome", "unknown")
        if outcome == "correct":
            return 1.0
        elif outcome == "incorrect":
            return 0.0
        elif outcome == "partial":
            return 0.5
        else:
            return 0.5  # Default for unknown outcomes
    
    def _get_concept_id(self, concept_name: str) -> Optional[int]:
        """Get concept ID from name."""
        for concept_id, embedding in self.knowledge_graph.concepts.items():
            if embedding.concept_name == concept_name:
                return concept_id
        return None
    
    def _check_prerequisites_met(
        self,
        concept_id: int,
        concept_probabilities: Dict[str, float],
        threshold: float = 0.7
    ) -> bool:
        """Check if concept prerequisites are met."""
        concept = self.knowledge_graph.concepts.get(concept_id)
        if not concept:
            return True
        
        for prereq_id in concept.prerequisites:
            prereq_concept = self.knowledge_graph.concepts.get(prereq_id)
            if prereq_concept:
                mastery = concept_probabilities.get(prereq_concept.concept_name, 0.0)
                if mastery < threshold:
                    return False
        
        return True
    
    async def _get_knowledge_state(self, student_id: str) -> KnowledgeState:
        """Get cached or compute knowledge state."""
        # Check cache first
        if student_id in self._knowledge_state_cache:
            cached_state = self._knowledge_state_cache[student_id]
            cache_age = datetime.now() - cached_state.last_updated
            if cache_age.total_seconds() < self._cache_ttl_minutes * 60:
                return cached_state
        
        # Compute fresh knowledge state
        interaction_history = await self._get_interaction_history(student_id)
        knowledge_state = await self._predict_knowledge_state(student_id, interaction_history)
        
        # Cache result
        self._knowledge_state_cache[student_id] = knowledge_state
        
        return knowledge_state
```

---

## Database Schema Extensions

### New Tables for Adaptive Learning

#### Migration: `migrations/versions/009_adaptive_learning.py`
```sql
"""Add adaptive learning tables.

Revision ID: 009
Revises: 008
Create Date: 2026-02-17
"""

-- DKT Training Data
CREATE TABLE dkt_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    concept_id INTEGER NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    question_type VARCHAR(100) NOT NULL,
    correctness FLOAT NOT NULL CHECK (correctness >= 0.0 AND correctness <= 1.0),
    response_time_seconds FLOAT NOT NULL,
    hint_count INTEGER DEFAULT 0,
    difficulty_level FLOAT NOT NULL CHECK (difficulty_level >= 0.0 AND difficulty_level <= 1.0),
    context_features JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- FSRS Cards for Spaced Repetition
CREATE TABLE fsrs_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_id INTEGER NOT NULL,
    concept_name VARCHAR(255) NOT NULL,
    stability FLOAT NOT NULL CHECK (stability >= 0.0),
    difficulty FLOAT NOT NULL CHECK (difficulty >= 0.0 AND difficulty <= 10.0),
    retrievability FLOAT NOT NULL CHECK (retrievability >= 0.0 AND retrievability <= 1.0),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    last_review TIMESTAMP WITH TIME ZONE,
    review_count INTEGER DEFAULT 0,
    average_response_time FLOAT DEFAULT 0.0,
    success_rate FLOAT DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    consecutive_successes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge State Snapshots
CREATE TABLE knowledge_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    concept_probabilities JSONB NOT NULL,
    confidence_intervals JSONB DEFAULT '{}',
    knowledge_growth_rate FLOAT DEFAULT 0.5,
    forgetting_rate FLOAT DEFAULT 0.1,
    learning_efficiency FLOAT DEFAULT 0.5,
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Adaptive Recommendations Log
CREATE TABLE adaptive_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    next_concept VARCHAR(255),
    next_difficulty FLOAT,
    teaching_strategy VARCHAR(100),
    concepts_to_review JSONB DEFAULT '[]',
    recommended_sequence JSONB DEFAULT '[]',
    recommendation_confidence FLOAT CHECK (recommendation_confidence >= 0.0 AND recommendation_confidence <= 1.0),
    reasoning TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for Performance
CREATE INDEX idx_dkt_interactions_student_concept ON dkt_interactions(student_id, concept_id);
CREATE INDEX idx_dkt_interactions_created_at ON dkt_interactions(created_at);
CREATE INDEX idx_fsrs_cards_student_due ON fsrs_cards(student_id, due_date);
CREATE INDEX idx_knowledge_states_student_created ON knowledge_states(student_id, created_at);
```

---

## Integration with Existing System

### Update `src/memory/manager.py`
```python
# Add to MemoryManager class

async def save_student_interaction(
    self,
    interaction: StudentInteraction
) -> str:
    """Save DKT training interaction."""
    if not self.db_session_factory:
        return None
        
    from src.models.adaptive import DKTInteraction
    
    async with self.db_session_factory() as session:
        db_interaction = DKTInteraction(
            student_id=interaction.student_id,
            session_id=interaction.session_id,
            concept_id=interaction.concept_id,
            concept_name=interaction.concept_name,
            question_type=interaction.question_type,
            correctness=interaction.correctness,
            response_time_seconds=interaction.response_time_seconds,
            hint_count=interaction.hint_count,
            difficulty_level=interaction.difficulty_level,
            context_features=interaction.context_features,
            created_at=interaction.timestamp
        )
        session.add(db_interaction)
        await session.commit()
        await session.refresh(db_interaction)
        return str(db_interaction.id)

async def get_fsrs_cards(self, student_id: str) -> List[FSRSCard]:
    """Get all FSRS cards for a student."""
    if not self.db_session_factory:
        return []
        
    from src.models.adaptive import FSRSCardDB
    from sqlalchemy import select
    
    async with self.db_session_factory() as session:
        stmt = select(FSRSCardDB).where(FSRSCardDB.student_id == student_id)
        result = await session.execute(stmt)
        db_cards = result.scalars().all()
        
        return [
            FSRSCard(
                concept_id=card.concept_id,
                concept_name=card.concept_name,
                student_id=card.student_id,
                stability=card.stability,
                difficulty=card.difficulty,
                retrievability=card.retrievability,
                due_date=card.due_date,
                last_review=card.last_review,
                review_count=card.review_count,
                average_response_time=card.average_response_time,
                success_rate=card.success_rate,
                consecutive_successes=card.consecutive_successes
            )
            for card in db_cards
        ]
```

### Update API Endpoints
```python
# Add to src/api/routers/chat.py

@router.get("/adaptive/recommendations/{student_id}")
async def get_adaptive_recommendations(
    student_id: str,
    current_topic: Optional[str] = None,
    session_duration: int = 30,
    current_user: User = Depends(get_current_user),
    adaptive_engine: AdaptiveLearningEngine = Depends(get_adaptive_engine),
):
    """Get personalized learning recommendations."""
    if str(current_user.id) != student_id and current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Access denied")
    
    recommendations = await adaptive_engine.get_adaptive_recommendations(
        student_id=student_id,
        current_topic=current_topic,
        session_time_budget_minutes=session_duration
    )
    
    return recommendations

@router.post("/adaptive/interaction")
async def record_learning_interaction(
    interaction_data: dict,
    current_user: User = Depends(get_current_user),
    adaptive_engine: AdaptiveLearningEngine = Depends(get_adaptive_engine),
):
    """Record a learning interaction for adaptive learning."""
    interaction = StudentInteraction(
        student_id=str(current_user.id),
        **interaction_data
    )
    
    updated_knowledge = await adaptive_engine.update_student_knowledge(
        str(current_user.id), interaction
    )
    
    return {
        "knowledge_updated": True,
        "new_mastery_levels": updated_knowledge.concept_probabilities,
        "learning_efficiency": updated_knowledge.learning_efficiency
    }
```

---

This adaptive learning engine provides sophisticated personalization using state-of-the-art algorithms specifically optimized for History education, enabling EduAGI to provide truly adaptive learning experiences that rival the best commercial educational AI systems.