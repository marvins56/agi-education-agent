# F03 + F01: Enhanced Student Memory & Adaptive Tutoring

## Overview
Enhance the Student Memory system (F03) with mastery tracking, memory consolidation,
and enriched student context. Upgrade the Adaptive Tutoring agent (F01) with
teaching strategy selection based on student mastery and learning style.

## Architecture

### Three-Tier Memory Enhancement

**Tier 1 -- Working Memory (Redis):**
- Current conversation (50 messages)
- Active session state (subject, topic, mood indicator)
- Scratchpad (student's working notes for current problem)
- Confusion tracker (detect repeated questions on same topic)

**Tier 2 -- Episodic Memory (PostgreSQL):**
- Session summaries (auto-generated at session end via consolidation)
- Quiz attempt history with per-question analysis
- Struggle points (topics where student repeatedly fails)
- Mastery change log (track score changes over time)
- Study streaks and engagement metrics

**Tier 3 -- Semantic Memory (ChromaDB):**
- Effective explanations per student (what worked for them)
- Student-specific knowledge gaps (embedded as searchable context)
- Conceptual connections the student has made

### New Components

#### 1. MasteryCalculator (`src/memory/mastery.py`)
Pure computation class for mastery scoring:
- Weighted average: quiz (0.4) + AI assessment (0.3) + interaction quality (0.2) + recency (0.1)
- Mastery levels: Novice (0-20), Beginner (21-40), Intermediate (41-60), Advanced (61-80), Expert (81-100)
- Decay function: `max(0, current - decay_rate * days_since_review)`

#### 2. MemoryConsolidator (`src/memory/consolidation.py`)
Async class that consolidates short-term Redis memory into long-term PostgreSQL storage:
- `consolidate_session(session_id)` -- summarize and archive a session
- `archive_expired_sessions(max_age_hours=24)` -- batch consolidation

#### 3. StudentContextBuilder (`src/memory/student_context.py`)
Assembles enriched context from all 3 memory tiers for the tutoring agent:
- Tier 1: current session state + recent conversation
- Tier 2: last 5 session summaries, mastery scores, struggle points
- Tier 3: student-specific knowledge gaps (optional, graceful fallback)

#### 4. Teaching Strategies (`src/agents/strategies.py`)
Strategy enum and selector:
- Strategies: socratic, direct_explanation, analogy, worked_example, scaffolded
- Selection rules based on mastery level, attempt count, learning style
- Multi-strategy fallback: if student doesn't understand after 2 attempts, switch strategy
- Strategy-specific prompt templates

#### 5. TopicMastery Model (`src/models/mastery.py`)
SQLAlchemy model tracking per-topic mastery with decay:
- Unique constraint: (student_id, subject, topic)
- Fields: mastery_score, confidence, attempts, last_assessed, last_reviewed, decay_rate

#### 6. Profile API (`src/api/routers/profile.py`)
Authenticated endpoints for student profile and mastery data:
- GET /profile -- get current user profile with preferences
- PUT /profile -- update learning preferences (learning_style, pace, grade_level)
- GET /profile/mastery -- mastery scores grouped by subject
- GET /profile/mastery/{subject} -- topic-level mastery for a subject
- GET /profile/history -- learning history summary
- GET /profile/streaks -- engagement data (total sessions, last active)

### Enhanced Existing Components

#### MemoryManager (`src/memory/manager.py`) additions:
- `get_student_mastery()` -- query TopicMastery records
- `update_mastery()` -- upsert mastery score
- `get_struggle_points()` -- topics below threshold
- `track_confusion()` -- Redis confusion counter
- `set_scratchpad()` / `get_scratchpad()` -- working notes for current problem
- `set_session_mood()` / `get_session_mood()` -- session mood indicator

#### TutorAgent (`src/agents/tutor.py`) enhancements:
- Strategy selection integrated into prompt generation
- Enriched context from StudentContextBuilder
- Confusion tracking: if student asks same concept 3+ times, switch to scaffolded
- Encouragement calibration via enriched context
- Strategy metadata in response -- fully backward compatible

#### MasterOrchestrator (`src/agents/orchestrator.py`) enhancements:
- Creates StudentContextBuilder and passes it to TutorAgent
- Enriches student profile with struggle points before routing

#### StudentProfile (`src/models/user.py`) additions:
- `total_study_minutes` -- engagement tracking
- `streak_days` -- consecutive study days
- `last_study_date` -- for streak calculation

### Migration
- `004_mastery_tables.py` -- creates `topic_mastery` table (down_revision="003")

### Security Considerations
- Students can only access their own profile/mastery data (auth required on all endpoints)
- Mastery scores are computed server-side (not client-submittable)
- PII data (learning difficulties, weaknesses) should be encrypted at rest in production

## Testing
Three test files with 40+ tests:
- `tests/test_memory_enhanced.py` -- mastery calculation, decay, levels, strategy selection, context builder, profile endpoint
- `tests/test_mastery.py` -- detailed mastery formula, decay boundaries, consolidation flow
- `tests/test_tutor_enhanced.py` -- strategy selection rules, prompts, TutorAgent process integration, confusion tracking
All mocked -- no external dependencies required.
