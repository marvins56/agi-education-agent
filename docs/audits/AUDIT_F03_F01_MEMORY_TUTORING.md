# Audit Report: F03/F01 Enhanced Student Memory + Adaptive Tutoring

**Auditor**: Code Audit Agent
**Date**: 2026-02-07
**Scope**: All files in the memory subsystem and adaptive tutoring pipeline
**Verdict**: Solid foundation with several medium-severity issues requiring attention

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [File Inventory](#2-file-inventory)
3. [Execution Flow Trace](#3-execution-flow-trace)
4. [Data Models](#4-data-models)
5. [Strategy Selection Logic Audit](#5-strategy-selection-logic-audit)
6. [Code Quality Issues](#6-code-quality-issues)
7. [Integration Points](#7-integration-points)
8. [Test Coverage Analysis](#8-test-coverage-analysis)
9. [Recommendations](#9-recommendations)

---

## 1. Architecture Overview

The memory system implements a classic **three-tier memory architecture**:

| Tier | Storage | Purpose | TTL |
|------|---------|---------|-----|
| **Working Memory** | Redis | Session context, conversation history, scratchpad, mood, confusion counters | 1-2 hours |
| **Episodic Memory** | PostgreSQL | Learning events, session summaries, mastery records | Permanent |
| **Semantic Memory** | ChromaDB | Knowledge base search, student knowledge gaps | Permanent |

The adaptive tutoring pipeline layers on top of this with:

- **StrategySelector**: Rule-based teaching strategy selection (5 strategies)
- **TutorAgent**: LLM-backed tutoring with dynamic system prompts
- **StudentContextBuilder**: Merges all 3 tiers into a rich context dict
- **MemoryConsolidator**: Promotes Redis working memory into PostgreSQL episodic memory
- **MasterOrchestrator**: Routes messages to the TutorAgent (currently the only registered agent)

---

## 2. File Inventory

### Core Memory Layer
| File | Lines | Primary Class |
|------|-------|---------------|
| `src/memory/manager.py` | 327 | `MemoryManager` |
| `src/memory/mastery.py` | 62 | `MasteryCalculator` |
| `src/memory/consolidation.py` | 125 | `MemoryConsolidator` |
| `src/memory/student_context.py` | 75 | `StudentContextBuilder` |

### Agent Layer
| File | Lines | Primary Class |
|------|-------|---------------|
| `src/agents/base.py` | 69 | `BaseAgent`, `AgentContext`, `AgentResponse` |
| `src/agents/tutor.py` | 247 | `TutorAgent` |
| `src/agents/strategies.py` | 107 | `StrategySelector`, `TeachingStrategy` |
| `src/agents/orchestrator.py` | 65 | `MasterOrchestrator` |

### Data Models
| File | Lines | Primary Class |
|------|-------|---------------|
| `src/models/mastery.py` | 34 | `TopicMastery` |
| `src/models/learning_event.py` | 26 | `LearningEvent` |
| `src/models/user.py` | 48 | `User`, `StudentProfile` |
| `src/models/session.py` | 25 | `Session` |

### API Layer
| File | Lines | Primary Class |
|------|-------|---------------|
| `src/api/routers/chat.py` | 168 | Chat/session endpoints |
| `src/api/routers/profile.py` | 291 | Profile/mastery endpoints |
| `src/api/dependencies.py` | 75 | DI functions |
| `src/api/main.py` | 80 | App lifespan |

### Tests
| File | Lines | Test Classes |
|------|-------|--------------|
| `tests/test_memory_enhanced.py` | 305 | 6 classes |
| `tests/test_mastery.py` | 175 | 4 classes |
| `tests/test_tutor_enhanced.py` | 297 | 4 classes |

---

## 3. Execution Flow Trace

### Flow: Student sends a chat message

```
POST /api/v1/chat/message
    |
    v
chat.py:send_message (line 79)
    |
    +-- memory.get_session_context()          # Redis lookup
    +-- Verify session ownership              # Security check
    +-- memory.get_conversation_history()      # Redis LRANGE
    +-- Build AgentContext (Pydantic model)
    |
    v
orchestrator.process(message, agent_context) (orchestrator.py:42)
    |
    +-- memory_manager.get_struggle_points()   # PG query, mastery < 30
    +-- Inject struggle_points into student_profile
    |
    v
tutor_agent.process(input_text, context) (tutor.py:127)
    |
    +-- context_builder.build_context()        # Merges all 3 tiers
    |     +-- Redis: session context + conversation
    |     +-- PG: session summaries, mastery scores, struggle points
    |     +-- ChromaDB: knowledge gaps
    |
    +-- strategy_selector.select_strategy()    # Rule-based selection
    |     +-- Examines: learning_style, topic_mastery, attempt_count, previous_strategy
    |     +-- Returns: one of 5 TeachingStrategy enum values
    |
    +-- memory.track_confusion()               # Redis INCR counter
    |     +-- If count >= 3: override strategy to "scaffolded"
    |
    +-- retriever.retrieve(query)              # RAG knowledge lookup
    |
    +-- Build LLM messages:
    |     +-- SystemMessage(system_prompt with strategy + enriched context)
    |     +-- SystemMessage(RAG knowledge context) [optional]
    |     +-- Last 10 conversation turns
    |     +-- HumanMessage(current input)
    |
    +-- llm.ainvoke(messages)                  # Claude API call
    |
    +-- Return AgentResponse with metadata:
          teaching_strategy, needs_visual_aid, knowledge_sources
    |
    v
chat.py:send_message (continued)
    |
    +-- memory.add_to_conversation("user", ...)      # Redis RPUSH + LTRIM
    +-- memory.add_to_conversation("assistant", ...)  # Redis RPUSH + LTRIM
    +-- memory.save_learning_event(...)               # PG INSERT
    |
    v
Return MessageResponse to client
```

### Flow: Memory Consolidation

```
MemoryConsolidator.consolidate_session(session_id)
    |
    +-- memory.get_conversation_history()       # Redis
    +-- memory.get_session_context()            # Redis
    +-- Count questions (heuristic: any user message increments)
    +-- Extract topics from context
    +-- Build summary dict
    +-- memory.save_learning_event("session_summary")  # PG
    |
    v
Return summary dict
```

### Flow: Archive Expired Sessions

```
MemoryConsolidator.archive_expired_sessions(max_age_hours)
    |
    +-- redis.scan("session:*:context")         # SCAN pattern
    +-- For each key:
    |     +-- Parse JSON context
    |     +-- Check created_at age
    |     +-- If expired:
    |           +-- consolidate_session()
    |           +-- redis.delete(context key)
    |           +-- redis.delete(messages key)
    |
    v
Return count of archived sessions
```

---

## 4. Data Models

### TopicMastery (`src/models/mastery.py`)

```
topic_mastery
  id             UUID PK (gen_random_uuid)
  student_id     UUID FK -> users.id CASCADE
  subject        VARCHAR(100) NOT NULL
  topic          VARCHAR(255) NOT NULL
  mastery_score  FLOAT DEFAULT 0.0
  confidence     FLOAT DEFAULT 0.0
  attempts       INTEGER DEFAULT 0
  last_assessed  DATETIME nullable
  last_reviewed  DATETIME nullable
  decay_rate     FLOAT DEFAULT 0.02
  created_at     DATETIME (server_default now)
  updated_at     DATETIME (server_default now, onupdate now)

UNIQUE(student_id, subject, topic)
INDEX(student_id)
INDEX(subject)
```

**Migration**: `migrations/versions/004_mastery_tables.py` matches the model exactly.

### LearningEvent (`src/models/learning_event.py`)

```
learning_events
  id          UUID PK
  student_id  UUID FK -> users.id CASCADE
  event_type  VARCHAR(50) NOT NULL
  subject     VARCHAR(100) nullable
  topic       VARCHAR(255) nullable
  data        JSONB nullable
  outcome     VARCHAR(50) nullable
  created_at  DATETIME (server_default now)
```

### Relationships

- `TopicMastery.student_id -> users.id` (CASCADE) -- good
- `LearningEvent.student_id -> users.id` (CASCADE) -- good
- No ORM relationship defined on TopicMastery (queries via raw SQLAlchemy `select()`)
- No relationship from User to TopicMastery (only from User to StudentProfile)

---

## 5. Strategy Selection Logic Audit

### `StrategySelector.select_strategy()` (`src/agents/strategies.py:52-91`)

**Rules (priority order):**

1. **mastery < 20** -> `direct_explanation`
   - Exception: if `attempt_count > 2` AND `previous_strategy == "direct_explanation"`, rotate to next
2. **attempt_count > 2 AND previous_strategy is truthy** -> rotate away from previous
3. **learning_style == "visual"** -> `analogy`
4. **learning_style == "kinesthetic"** -> `worked_example`
5. **Default** -> `socratic`

**Rotation Logic** (`_next_strategy`, line 99-106):
- Steps through `_STRATEGY_ROTATION` starting from current index
- Skips any candidate matching `previous` strategy
- Fallback: next in list if all match previous (impossible with 5 strategies)

### Issues Found

**ISSUE S-1 (Medium): Mastery boundary at exactly 20.0 is ambiguous**

At `strategies.py:68`, the condition is `if topic_mastery < 20`, meaning a student with exactly 20.0 mastery skips Rule 1. Combined with the mastery level mapping in `mastery.py:8` where `(20, "Novice")` means 20.0 is still "Novice", a student can be classified as "Novice" but NOT receive the `direct_explanation` strategy intended for struggling students.

**ISSUE S-2 (Low): `attempt_count` semantics are overloaded**

In `tutor.py:154`, `attempt_count` comes from `TopicMastery.attempts` -- the total lifetime attempts on a topic. But the strategy rotation logic at `strategies.py:76` treats it as "consecutive attempts on the same topic in this session". A student who studied algebra 5 times over 3 months would always trigger strategy rotation, even on their first interaction in a new session.

**ISSUE S-3 (Low): No "reading/writing" learning style handling**

The system prompt mentions four learning styles (visual, auditory, kinesthetic, reading/writing) at `tutor.py:83-88`, but the strategy selector only handles "visual" and "kinesthetic". Auditory and reading/writing learners always get the default `socratic`.

**ISSUE S-4 (Low): `previous_strategy` validation**

At `strategies.py:78-80`, when `previous_strategy` is not a valid enum member, it falls back to `TeachingStrategy.socratic`. This silently swallows invalid values stored in Redis. If session state is corrupted, the user gets an unexpected strategy switch with no logging.

### Confusion Override Logic (`tutor.py:169-178`)

The confusion tracking via Redis INCR is clean. When `confusion_count >= 3`, the strategy is overridden to `scaffolded`. This correctly takes priority over the strategy selector since it runs after selection.

**ISSUE S-5 (Medium): Confusion counter never resets within a session**

The confusion counter key (`session:{session_id}:confusion:{topic}`) uses a 2-hour TTL but never resets on success. If a student asks about "Algebra" 3 times, gets confused, then successfully understands it, the counter remains >= 3 for the rest of the session. Every subsequent algebra question will be forced into `scaffolded` mode even after the student demonstrates understanding.

---

## 6. Code Quality Issues

### BUG-1 (Medium): Race condition in `update_mastery` upsert

**File**: `src/memory/manager.py:254-279`

The upsert in `update_mastery()` uses a SELECT-then-INSERT/UPDATE pattern without any locking:

```python
stmt = select(TopicMastery).where(...)
result = await session.execute(stmt)
record = result.scalars().first()
if record:
    record.mastery_score = new_score  # UPDATE
else:
    record = TopicMastery(...)        # INSERT
    session.add(record)
await session.commit()
```

If two concurrent requests try to create mastery for the same (student, subject, topic) triple, both will see `record = None`, both will INSERT, and one will hit the UNIQUE constraint `uq_student_subject_topic`. The exception is unhandled and will propagate as a 500 error.

**Fix**: Use `INSERT ... ON CONFLICT DO UPDATE` (PostgreSQL upsert) or wrap in a retry with conflict handling.

### BUG-2 (Medium): `MemoryManager` null guard inconsistency

**File**: `src/memory/manager.py`

Some methods guard against `self._redis is None` (e.g., `set_scratchpad` at line 181, `get_scratchpad` at line 187), but the core methods `set_session_context` (line 38), `get_session_context` (line 42), `add_to_conversation` (line 47), and `get_conversation_history` (line 57) do NOT check for `None`. If `initialize()` was never called or Redis is down, these will raise `AttributeError: 'NoneType' object has no attribute 'setex'`.

**Affected flow**: Every chat message goes through `get_session_context` and `add_to_conversation`.

### BUG-3 (Low): `store_knowledge` and `search_knowledge` are not truly async

**File**: `src/memory/manager.py:122-175`

ChromaDB's `HttpClient` is synchronous. The methods are declared `async` but call blocking I/O (`collection.add()`, `collection.query()`) directly. Under load, these block the event loop.

**Fix**: Use `asyncio.to_thread()` or switch to ChromaDB's async client if available.

### BUG-4 (Low): `created_at` timezone mismatch in consolidation archiver

**File**: `src/memory/consolidation.py:106-107`

```python
created_dt = datetime.fromisoformat(created)
age_hours = (now - created_dt).total_seconds() / 3600
```

`now` is `datetime.now(timezone.utc)` (timezone-aware), but `created_dt` is parsed from ISO format which may be naive or have a different timezone. If the stored `created_at` is naive (no `+00:00` suffix), this subtraction raises `TypeError: can't subtract offset-naive and offset-aware datetimes`.

### BUG-5 (Low): Conversation history saved AFTER LLM response

**File**: `src/api/routers/chat.py:126-127`

```python
# Process message through orchestrator
response = await orchestrator.process(body.content, agent_context)

# Save messages to conversation history
await memory.add_to_conversation(body.session_id, "user", body.content)
await memory.add_to_conversation(body.session_id, "assistant", response.text)
```

The user's message is saved to Redis AFTER the LLM call. But the TutorAgent at `tutor.py:209` reads `context.conversation_history` which was loaded BEFORE the current message was stored. This means the LLM sees the previous conversation but NOT the current user message in the conversation history -- it only sees it in the final `HumanMessage(content=input_text)` at line 217. This is functionally correct but means the conversation history in Redis is always 1 message behind during processing.

However, if the LLM call fails (timeout, API error), the user and assistant messages are never stored. This creates a gap in the conversation history -- the user sent a message that disappears.

### BUG-6 (Medium): `update_profile` does not commit

**File**: `src/api/routers/profile.py:134`

```python
await db.flush()
```

The `update_profile` endpoint uses `db.flush()` instead of `db.commit()`. This works only because the `get_db` dependency (`dependencies.py:23-28`) auto-commits on success:

```python
yield session
await session.commit()
```

This is technically correct but fragile -- if someone changes the dependency to not auto-commit, profile updates silently disappear.

### ISSUE-7 (Low): `get_system_prompt` signature breaks `BaseAgent` interface

**File**: `src/agents/tutor.py:42` vs `src/agents/base.py:55`

`BaseAgent` declares:
```python
@abstractmethod
def get_system_prompt(self, context: AgentContext) -> str:
```

But `TutorAgent` overrides with extra parameters:
```python
def get_system_prompt(self, context, strategy=None, enriched_context=None) -> str:
```

Python allows this (extra params have defaults), but it violates the Liskov Substitution Principle. Code calling `agent.get_system_prompt(context)` won't crash, but the type signature is misleading for anyone implementing a new agent.

### ISSUE-8 (Low): `sources` field type mismatch in `MessageResponse`

**File**: `src/schemas/chat.py:19`

```python
sources: list[dict] = []
```

But in `chat.py:142`:
```python
sources=response.metadata.get("knowledge_sources", []),
```

`knowledge_sources` is `list[str]` (see `tutor.py:228-229`), not `list[dict]`. This means `sources` will contain `["source1", "source2"]` which technically matches `list[dict]` in Pydantic v2's lenient mode, but the schema name implies structured dicts.

### ISSUE-9 (Low): Scratchpad and mood features are write-only

**File**: `src/memory/manager.py:179-205`

The `set_scratchpad`, `get_scratchpad`, `set_session_mood`, and `get_session_mood` methods exist but are never called anywhere in the codebase (no references in agents, API, or tests). They are dead code from the F03 specification that was never integrated.

---

## 7. Integration Points

### Memory Manager Lifecycle

```
main.py:lifespan (line 16)
  +-- MemoryManager(redis_url, db_session_factory)
  +-- memory.initialize()                     # connects Redis + ChromaDB
  +-- app.state.memory_manager = memory
  +-- MasterOrchestrator(memory_manager=memory)
  +-- orchestrator.initialize()
  |     +-- StudentContextBuilder(memory_manager=memory)
  |     +-- TutorAgent(memory=memory, context_builder=...)
  |
  v [on shutdown]
  +-- orchestrator.close()                    # no-op
  +-- memory.close()                          # closes Redis
```

### Dependency Injection

- `get_memory(request)` -> `request.app.state.memory_manager` (sync, returns singleton)
- `get_orchestrator(request)` -> `request.app.state.orchestrator` (sync, returns singleton)
- `get_db()` -> yields fresh `AsyncSession` per request

### Router Registration

`src/api/main.py:76`:
```python
app.include_router(profile.router, prefix="/api/v1", tags=["Profile"])
```

Profile routes are mounted at `/api/v1/profile`, `/api/v1/profile/mastery`, etc.

Chat routes at `/api/v1/chat/sessions`, `/api/v1/chat/message`, `/api/v1/chat/history/{session_id}`.

### Key Data Flow Connections

| Source | Target | Via |
|--------|--------|-----|
| `chat.py:send_message` | `orchestrator.process()` | Direct call |
| `orchestrator.process()` | `tutor_agent.process()` | Direct call |
| `tutor_agent.process()` | `context_builder.build_context()` | Direct call |
| `context_builder.build_context()` | `memory_manager.*` | 5 async calls |
| `tutor_agent.process()` | `strategy_selector.select_strategy()` | Static call |
| `tutor_agent.process()` | `memory_manager.track_confusion()` | Direct call |
| `chat.py:send_message` | `memory_manager.add_to_conversation()` | Direct call (post-response) |
| `chat.py:send_message` | `memory_manager.save_learning_event()` | Direct call (post-response) |

### Unused Integration Points

- `MemoryConsolidator` is never instantiated by any API or background task. It's test-only code.
- `MemoryConsolidator.archive_expired_sessions()` scans Redis but is never scheduled.
- Scratchpad and mood Redis methods have no callers.

---

## 8. Test Coverage Analysis

### What IS Tested

| Area | Test File | Count | Quality |
|------|-----------|-------|---------|
| MasteryCalculator.calculate_mastery | test_memory_enhanced.py, test_mastery.py | 9 tests | Excellent -- covers empty, decay, boundaries |
| MasteryCalculator.apply_decay | test_memory_enhanced.py, test_mastery.py | 7 tests | Good -- covers zero, large, custom rate |
| MasteryCalculator.get_mastery_level | test_memory_enhanced.py, test_mastery.py | 10 tests | Excellent -- every boundary |
| StrategySelector.select_strategy | test_memory_enhanced.py, test_tutor_enhanced.py | 12 tests | Good -- covers main rules |
| StrategySelector.get_strategy_prompt | test_memory_enhanced.py, test_tutor_enhanced.py | 5 tests | Good |
| StudentContextBuilder.build_context | test_memory_enhanced.py | 1 test | Minimal -- only happy path |
| MemoryConsolidator.consolidate_session | test_mastery.py | 3 tests | Good -- empty, basic, with DB |
| TutorAgent.get_system_prompt | test_memory_enhanced.py, test_tutor_enhanced.py | 5 tests | Good -- with/without strategy |
| TutorAgent.process | test_tutor_enhanced.py | 4 tests | Good -- strategy metadata, confusion |
| Profile GET endpoint | test_memory_enhanced.py | 1 test | Basic |

### What is NOT Tested (Gaps)

**Critical gaps:**

1. **`MemoryManager.update_mastery()`** -- zero tests for the upsert logic. The race condition in BUG-1 is completely untested.

2. **`MemoryManager.get_student_mastery()`** -- no tests. The method that feeds mastery data into the entire context pipeline.

3. **`MemoryManager.get_struggle_points()`** -- no tests. The threshold-based query driving struggle detection.

4. **`MemoryManager.track_confusion()`** -- tested only indirectly via TutorAgent mock. No test verifies the Redis INCR + EXPIRE behavior directly.

5. **`MasterOrchestrator.process()`** -- no direct tests. The struggle-point enrichment logic at `orchestrator.py:48-56` is untested.

6. **`MemoryConsolidator.archive_expired_sessions()`** -- no tests. The Redis SCAN + delete logic is completely uncovered.

7. **Profile PUT endpoint** -- no test for `update_profile`.

8. **Profile mastery endpoints** -- no tests for `GET /profile/mastery` or `GET /profile/mastery/{subject}`.

9. **Profile history/streaks endpoints** -- no tests for `GET /profile/history` or `GET /profile/streaks`.

10. **Chat `send_message` end-to-end** -- no integration test that traces the full flow from HTTP request through orchestrator to memory storage.

11. **Error paths** -- no tests for:
    - Redis connection failure during `get_session_context`
    - ChromaDB failure during `search_knowledge`
    - LLM timeout/error during `tutor.process()`
    - Invalid `previous_strategy` value in strategy selector

**Test infrastructure note**: Several test classes use `async def` test methods (e.g., `TestStudentContextBuilder`, `TestProfileEndpoint`, `TestMemoryConsolidation`, `TestTutorProcessIntegration`). These require `pytest-asyncio` with `mode="auto"` configured, which is present in `pyproject.toml`. If this config is missing, these tests silently pass without executing.

---

## 9. Recommendations

### High Priority

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| R-1 | BUG-1: Race condition in `update_mastery` | Medium | Use PostgreSQL `INSERT ... ON CONFLICT DO UPDATE` via SQLAlchemy's `insert().on_conflict_do_update()` |
| R-2 | BUG-2: Null Redis guard missing on core methods | Medium | Add `if not self._redis: return None/[]` guards to `set_session_context`, `get_session_context`, `add_to_conversation`, `get_conversation_history` |
| R-3 | S-5: Confusion counter never resets | Medium | Add a `reset_confusion(session_id, topic)` method and call it when the student demonstrates understanding (e.g., after a correct assessment) |
| R-4 | Test gaps: Add tests for `update_mastery`, `get_student_mastery`, `get_struggle_points` | Medium | These are core data paths feeding the entire adaptive pipeline |

### Medium Priority

| # | Issue | Severity | Fix |
|---|-------|----------|-----|
| R-5 | S-2: `attempt_count` semantics | Low | Track per-session attempt count separately in Redis instead of using lifetime `TopicMastery.attempts` |
| R-6 | BUG-3: ChromaDB blocking calls | Low | Wrap in `asyncio.to_thread()` |
| R-7 | BUG-4: Timezone mismatch in archiver | Low | Ensure `created_at` is always stored with UTC timezone suffix, or use `datetime.fromisoformat(created).replace(tzinfo=timezone.utc)` |
| R-8 | Schedule `archive_expired_sessions` | Low | Add a background task (e.g., FastAPI `BackgroundTasks` or APScheduler) to periodically run consolidation |
| R-9 | Wire up scratchpad/mood or remove dead code | Low | Either integrate into tutor flow or delete to reduce maintenance surface |

### Low Priority

| # | Issue | Fix |
|---|-------|-----|
| R-10 | S-1: Mastery boundary at 20.0 | Change to `topic_mastery <= 20` |
| R-11 | S-3: Add reading/writing learning style | Add a branch for reading/writing -> `direct_explanation` |
| R-12 | ISSUE-7: LSP violation in `get_system_prompt` | Refactor base class to accept `**kwargs` or use a protocol |
| R-13 | ISSUE-8: `sources` type mismatch | Change to `list[str]` or standardize knowledge sources as dicts |
| R-14 | BUG-5: Save user message before LLM call | Move `add_to_conversation("user", ...)` before `orchestrator.process()` |

---

## Appendix A: Strategy Selection Decision Tree

```
                    topic_mastery < 20?
                    /                \
                  YES                 NO
                  |                    |
          direct_explanation      attempt_count > 2
          (unless stuck ->          AND previous?
           rotate)                 /            \
                                 YES             NO
                                 |                |
                           rotate away      learning_style?
                           from previous    /    |     \
                                        visual kineth  other
                                          |      |       |
                                       analogy worked  socratic
                                              example

    [Post-selection override]
    confusion_count >= 3?  -->  scaffolded
```

## Appendix B: Redis Key Schema

| Pattern | Type | TTL | Used By |
|---------|------|-----|---------|
| `session:{id}:context` | STRING (JSON) | 3600s | set/get_session_context |
| `session:{id}:messages` | LIST (JSON elements) | None* | add_to/get_conversation |
| `session:{id}:scratchpad` | STRING | 7200s | set/get_scratchpad (unused) |
| `session:{id}:mood` | STRING | 3600s | set/get_session_mood (unused) |
| `session:{id}:confusion:{topic}` | STRING (counter) | 7200s | track_confusion |

*Note: `session:{id}:messages` has no TTL set. The list is trimmed to last 50 entries via `LTRIM`, but the key itself never expires. This is a minor memory leak -- if sessions are abandoned without consolidation, these keys persist indefinitely.

## Appendix C: File Cross-Reference Matrix

```
                manager  mastery  consolidation  student_ctx  tutor  strategies  orchestrator  base  chat  profile
manager            -        -          R             R          R        -            R          -     R      -
mastery            -        -          -             -          -        -            -          -     -      -
consolidation      W        -          -             -          -        -            -          -     -      -
student_ctx        R        -          -             -          -        -            -          -     -      -
tutor              R        -          -             R          -        R            -          W     -      -
strategies         -        -          -             -          R        -            -          -     -      -
orchestrator       R        -          -             W          R        -            -          R     -      -
base               -        -          -             -          W        -            W          -     -      -
chat               R        -          -             -          -        -            R          R     -      -
profile            -        -          -             -          -        -            -          -     -      -

R = reads from, W = writes to / extends
```

---

**End of Audit Report**
