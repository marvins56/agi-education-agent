# Audit Report: F12/F14 Analytics Dashboard Backend + Learning Path Engine

**Auditor**: Claude Opus 4.6 (automated code audit)
**Date**: 2026-02-07
**Scope**: Analytics pipeline (F12), DAG-based learning paths and SM-2 spaced repetition (F14)

---

## 1. Architecture Overview

### 1.1 Analytics Pipeline (F12)

The analytics subsystem follows a three-layer architecture:

1. **Calculator Layer** (`src/analytics/calculator.py`) -- Stateless, pure-function class `MetricsCalculator` with 9 static methods for computing engagement, accuracy, mastery, streaks, trends, study time, velocity, best study time, and daily aggregation. No side effects; all inputs are plain Python types.

2. **Aggregation Layer** (`src/analytics/aggregator.py`) -- `DataAggregator` bridges the database and calculator. It accepts an `async_sessionmaker`, issues SQLAlchemy queries against the `LearningEvent` table, and delegates math to `MetricsCalculator`. Provides student-level (`get_student_summary`, `get_student_activity_heatmap`, `get_student_mastery_by_subject`) and class-level methods (stubs).

3. **Alert Layer** (`src/analytics/alerts.py`) -- `AlertEngine.check_at_risk()` is a stateless, static method that evaluates four at-risk indicators and returns a list of alert dicts. It is not currently called by any API endpoint or aggregator method.

### 1.2 Learning Path Engine (F14)

The learning path subsystem comprises:

1. **Prerequisite Graph** (`src/learning_path/graph.py`) -- `PrerequisiteGraph` is an in-memory DAG with adjacency lists, supporting three relationship types (`requires`, `recommends`, `complements`). Provides topological sort (Kahn's algorithm), transitive prerequisite discovery (DFS), and gap analysis. Supports DB serialization via `load_from_db` / `save_to_db`.

2. **Path Recommender** (`src/learning_path/recommender.py`) -- `PathRecommender.recommend()` takes student mastery + goals, uses the graph to find gaps, then scores/ranks topics using a composite priority formula (depth, impact, time, deadline urgency).

3. **Spaced Repetition** (`src/learning_path/spaced_repetition.py`) -- `SpacedRepetitionScheduler` implements the SM-2 algorithm with quality-based EF adjustment, interval progression (1 -> 6 -> prev*EF), and a due-review filter.

### 1.3 Data Models

| Table | Model File | Purpose |
|-------|-----------|---------|
| `daily_metrics` | `src/models/analytics.py:10` | Per-student, per-day metric snapshots |
| `weekly_aggregates` | `src/models/analytics.py:26` | Weekly rollups (mastery, velocity, engagement, streak) |
| `topic_nodes` | `src/models/learning_path.py:20` | Topics in the prerequisite graph |
| `topic_edges` | `src/models/learning_path.py:32` | Directed edges (requires/recommends/complements) |
| `student_goals` | `src/models/learning_path.py:46` | Student learning goals with deadlines |
| `review_schedule` | `src/models/learning_path.py:62` | SM-2 state per student-topic pair |
| `learning_events` | `src/models/learning_event.py:10` | Raw student interaction events (used by aggregator) |

### 1.4 API Endpoints

**Analytics Router** (`src/api/routers/analytics.py`):
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/analytics/student/summary` | Any authenticated | Dashboard summary |
| GET | `/analytics/student/mastery` | Any authenticated | Per-subject mastery |
| GET | `/analytics/student/activity` | Any authenticated | Activity heatmap |
| GET | `/analytics/student/streaks` | Any authenticated | Current streak |
| GET | `/analytics/teacher/class/{class_id}/overview` | teacher/admin | Class overview (stub) |
| GET | `/analytics/teacher/class/{class_id}/students` | teacher/admin | Per-student metrics (stub) |
| GET | `/analytics/teacher/class/{class_id}/at-risk` | teacher/admin | At-risk students (stub) |

**Learning Path Router** (`src/api/routers/learning_path.py`):
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/learning-path/recommended` | Any authenticated | Personalized study path |
| GET | `/learning-path/graph/{subject}` | Any authenticated | Subject prerequisite graph |
| POST | `/learning-path/goals` | Any authenticated | Create learning goal |
| GET | `/learning-path/reviews-due` | Any authenticated | Spaced repetition reviews due |
| POST | `/learning-path/review-completed` | Any authenticated | Record review result |

---

## 2. Execution Flow Traces

### 2.1 Analytics: Student Activity -> Summary

```
Client GET /api/v1/analytics/student/summary
  -> analytics.py:23 get_student_summary()
    -> get_current_user (JWT verification)
    -> _get_aggregator() creates DataAggregator(async_session)
    -> aggregator.get_student_summary(student_id)
      -> SELECT learning_events WHERE student_id AND created_at >= 30d ago
      -> calculator.calculate_engagement_rate(active_dates, 30)
      -> calculator.calculate_streak(active_dates)
      -> calculator.calculate_accuracy_rate(correct, total_quiz_events)
      -> calculator.calculate_quiz_score_trend(quiz_scores)
      -> calculator.calculate_best_study_time(session_data)
      -> Returns consolidated dict
  -> Returns {success: true, data: {...}}
```

### 2.2 Learning Path: Recommendation Flow

```
Client GET /api/v1/learning-path/recommended
  -> learning_path.py:32 get_recommended_path()
    -> get_current_user (JWT verification)
    -> get_db() provides async session
    -> PrerequisiteGraph() created fresh
    -> graph.load_from_db(db) -- loads all TopicNode + TopicEdge
    -> SELECT student_goals WHERE student_id AND NOT completed
    -> PathRecommender(graph).recommend(mastery={}, goals)
      -> graph.find_gaps(mastery, targets, threshold=50)
      -> For each gap: compute impact, depth_score, time_score, deadline_score
      -> Sort by composite priority, return top 10
  -> Returns {success: true, data: [...]}
```

### 2.3 Spaced Repetition: Review Completion Flow

```
Client POST /api/v1/learning-path/review-completed {topic_id, quality}
  -> learning_path.py:186 record_review_completed()
    -> get_current_user (JWT verification)
    -> SELECT review_schedule WHERE student_id AND topic_id
    -> If exists:
        -> SM2.calculate_next_review(quality, count, ef, interval)
        -> Update schedule: next_review_date, interval_days, ef, count+1
    -> If not exists:
        -> SM2.calculate_next_review(quality, 0, 2.5, 1)
        -> INSERT new ReviewSchedule
    -> db.flush()
    -> Returns updated schedule
```

---

## 3. Integration Point Analysis

### 3.1 Analytics <-> LearningEvent

The `DataAggregator` (`aggregator.py:26-32`) queries the `learning_events` table directly. This is the **only** data source for analytics. The aggregator filters by `student_id` and `created_at >= 30 days ago`, which means:
- Historical data older than 30 days is invisible to the student summary endpoint
- No materialized views or pre-computed metrics are used; every request re-queries raw events

### 3.2 Analytics <-> Alert Engine

**Issue (MEDIUM)**: `AlertEngine` is imported in `aggregator.py:8` but never called. The `get_class_at_risk` endpoint (`aggregator.py:189-194`) returns an empty stub. The alert engine itself is fully implemented and tested but completely disconnected from the API and aggregation layers.

### 3.3 Learning Path <-> Student Mastery

**Issue (HIGH)**: In `learning_path.py:60`, the recommended path endpoint initializes `student_mastery` as an empty dict `{}`. The comment says "will be populated by other features" but this means **all topics always appear as gaps** (mastery 0.0 < threshold 50.0). The recommender's priority scoring still works, but the recommendations are not truly personalized -- they simply order all prerequisites of all goals by structural depth and impact, ignoring actual student progress.

### 3.4 Learning Path <-> Analytics

There is **no integration** between the learning path and analytics subsystems. Specifically:
- The `DailyMetric` and `WeeklyAggregate` models exist but are never written to by any code
- Learning velocity (`calculate_learning_velocity`) is computed by the calculator but the aggregator always returns `velocity: 0.0` (`aggregator.py:79`)
- The analytics aggregator does not use spaced repetition data
- The learning path does not consume analytics data to adjust recommendations

### 3.5 Router Registration

Both routers are properly registered in `src/api/main.py:67-79`:
- `analytics.router` at prefix `/api/v1` with tag "Analytics"
- `learning_path.router` at prefix `/api/v1` with tag "Learning Path"

---

## 4. Algorithm Correctness Audit

### 4.1 SM-2 Algorithm (`spaced_repetition.py`)

The implementation follows the standard SM-2 specification correctly:

**EF adjustment formula** (line 31):
```python
new_ef = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
```
This matches the original SM-2: `EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))`. Verified against test cases:
- quality=5: EF' = EF + 0.1 (correct)
- quality=4: EF' = EF + 0.0 (correct)
- quality=3: EF' = EF - 0.14 (correct)

**Interval progression** (lines 34-41):
- rep 0: interval = 1 day (correct)
- rep 1: interval = 6 days (correct)
- rep 2+: interval = round(prev * new_ef) (correct)
- quality < 3: reset to 1 day (correct)

**EF floor** (line 32): Clamped to minimum 1.3 (correct per SM-2 spec).

**Quality clamping** (line 28): Quality is clamped to [0, 5] range before computation (correct).

**Minor note**: The SM-2 algorithm uses `new_ef` (the **adjusted** EF) in the interval multiplication on line 41. The original SM-2 spec uses `new_ef` as well (EF is updated before interval calculation), so this is correct. However, some implementations apply the EF adjustment after the interval calculation; this is a valid variant.

### 4.2 Engagement Rate (`calculator.py:18-20`)

```python
return (active_days / max(total_days, 1)) * 100
```

Correct. Uses `max(total_days, 1)` to prevent division by zero. Returns percentage 0-100.

### 4.3 Accuracy Rate (`calculator.py:23-47`)

Simple mode: `(correct / total) * 100` with zero-total guard. Correct.

Weighted mode: Sums `correct * weight` and `total * weight` across difficulty buckets, then divides. This computes a weighted accuracy, which is mathematically valid.

**Edge case**: If `difficulty_weights` is provided but all buckets have `weighted_total == 0`, the function falls through to the simple `correct/total` path using the top-level `correct` and `total` arguments, which may both be 0. This is handled (returns 0.0 on line 44-45). However, passing `difficulty_weights` with a non-zero top-level `correct` and `total` but zero bucket totals would silently use the unweighted calculation, which could be confusing.

### 4.4 Topic Mastery (`calculator.py:50-69`)

Weighted sum of four components, clamped to [0, 100]. Correct.

### 4.5 Quiz Score Trend (`calculator.py:72-95`)

Splits the window into halves and compares averages with a 2.0-point threshold for determining direction. This is a reasonable heuristic, though the 2.0 threshold is quite sensitive for 0-100 scale scores.

**Edge case**: When `len(recent) == 2`, `first_half = recent[:1]` and `second_half = recent[1:]`. This works but the trend is determined by just 2 data points, which is volatile.

### 4.6 Streak Calculation (`calculator.py:117-138`)

Counts consecutive days backward from the most recent activity date. Streak is 0 if the most recent activity is more than 1 day before today. Correct.

### 4.7 Learning Velocity (`calculator.py:166-189`)

Implements simple linear regression (least squares) to compute the slope of mastery over time. The formula is the standard OLS slope formula. Mathematically correct.

### 4.8 Topological Sort (`graph.py:94-114`)

Standard Kahn's algorithm. Correct. However, does not detect cycles -- if a cycle exists, the returned order will be shorter than `len(self.nodes)`, which could silently produce incorrect results.

### 4.9 Gap Analysis (`graph.py:116-157`)

DFS-based gap finder that follows prerequisite edges. Filters by relationship type (hard-only by default). Depth tracking works correctly -- revisits a topic only if a deeper path is found.

**Potential issue**: No cycle detection. If the graph has a cycle (which would violate the DAG invariant), `find_depth` will recurse infinitely and cause a `RecursionError`. The `add_prerequisite` method does not validate that adding an edge preserves the DAG property.

### 4.10 Alert Thresholds (`alerts.py`)

| Alert | Threshold | Severity | Notes |
|-------|-----------|----------|-------|
| No activity | >= 7 days | warning (7-13d), critical (14+d) | Reasonable |
| Mastery declining | 3 consecutive decreases | warning | Only checks strict monotonic decrease |
| Engagement | < 30% | warning | Fixed threshold, not configurable |
| Quiz scores | avg < 40% | critical | Uses average of recent scores |

**Issue (LOW)**: The mastery declining check (`alerts.py:34`) requires strict monotonic decrease (`a > b > c`). Equal scores (e.g., `80, 80, 70`) or non-monotonic decline (e.g., `80, 60, 70`) would not trigger an alert even though the student may be struggling.

---

## 5. Data Model Audit

### 5.1 Missing Indexes

**Issue (HIGH -- Performance)**:

1. `daily_metrics` -- No index on `(student_id, date)`. This table will be queried by student and date range; a composite index is essential.

2. `weekly_aggregates` -- No index on `(student_id, week_start)`. Same concern.

3. `topic_edges` -- No index on `from_topic_id` or `to_topic_id`. Graph loading filters by these columns.

4. `student_goals` -- No index on `student_id`. Goal queries filter by student.

5. `review_schedule` -- No index on `(student_id, topic_id)`. The `record_review_completed` endpoint queries by this composite key.

6. `review_schedule` -- No index on `student_id`. The `get_reviews_due` endpoint filters by student.

Compare with `learning_events` which properly has indexes on `student_id`, `subject`, and `created_at`.

### 5.2 Missing Unique Constraints

1. `daily_metrics` -- Should have UNIQUE on `(student_id, date)` to prevent duplicate daily records.

2. `weekly_aggregates` -- Should have UNIQUE on `(student_id, week_start)`.

3. `review_schedule` -- Should have UNIQUE on `(student_id, topic_id)` since there should be exactly one schedule per student-topic pair.

4. `topic_edges` -- Should have UNIQUE on `(from_topic_id, to_topic_id)` to prevent duplicate edges.

### 5.3 Missing Relationships (ORM)

None of the models define SQLAlchemy `relationship()` attributes. While functional for the current query patterns, this prevents eager loading and makes joins harder. The `User` model is referenced by FK in all tables but cannot be navigated from the ORM.

### 5.4 Model vs Migration Consistency

The migration (`006_analytics_path_tables.py`) matches the model definitions. Column types, defaults, foreign keys, and nullable settings are consistent. The `updated_at` column on `review_schedule` uses `server_default` in the migration but relies on `onupdate=func.now()` in the model, which is an ORM-level trigger and works correctly.

### 5.5 DailyMetric/WeeklyAggregate Models Are Unused

**Issue (MEDIUM)**: The `DailyMetric` and `WeeklyAggregate` models are defined and migrated but never read from or written to. The aggregator computes metrics on-the-fly from `LearningEvent` data. These models suggest a planned materialization layer that was never implemented.

---

## 6. Code Quality Issues

### 6.1 Bugs

**BUG-1 (HIGH): `get_prerequisite_graph` fetches ALL edges** (`learning_path.py:85-96`)

```python
result = await db.execute(select(TopicEdge))  # Fetches ALL edges in entire system
all_edges = result.scalars().all()
```

Then filters in Python. With many subjects and edges, this loads the entire edge table into memory. Should filter by `from_topic_id IN node_ids OR to_topic_id IN node_ids` at the SQL level.

**BUG-2 (MEDIUM): `save_to_db` uses unreliable UUID detection** (`graph.py:190`)

```python
id=uuid.UUID(topic_id) if len(topic_id) == 36 else None,
```

This checks string length to determine if a topic_id is a UUID. A 36-character non-UUID string would cause `uuid.UUID()` to raise `ValueError`. Should use try/except instead.

**BUG-3 (MEDIUM): No `db.commit()` in `record_review_completed`** (`learning_path.py:232`)

The endpoint calls `db.flush()` but not `db.commit()`. However, reviewing `dependencies.py:20-28`, the `get_db()` dependency auto-commits on success. So this is actually correct -- the commit happens when the `get_db` context manager exits. Not a bug, but the use of `flush()` instead of relying on auto-flush is inconsistent with the `create_goal` endpoint which also uses `flush()`.

**BUG-4 (LOW): Graph rebuilt on every request** (`learning_path.py:37-38`)

```python
graph = PrerequisiteGraph()
await graph.load_from_db(db)
```

The prerequisite graph is rebuilt from scratch on every `/learning-path/recommended` and `/learning-path/graph/{subject}` request. For a production system with many topics, this is inefficient. The graph should be cached (e.g., in app state or Redis) with invalidation on topic/edge changes.

### 6.2 Performance Concerns

**PERF-1 (HIGH): N+1 query pattern in PathRecommender** (`recommender.py:65-68`)

```python
for gap in all_gaps:
    for goal_tid in goal_topic_ids:
        all_prereqs = self.graph.get_all_prerequisites(goal_tid)  # DFS per goal per gap
```

`get_all_prerequisites` performs a DFS traversal for every goal. With G goals and N gaps, this is O(G * N * depth). The prerequisite sets should be pre-computed once per goal.

**PERF-2 (HIGH): Duplicate DFS in priority scoring** (`recommender.py:84-86`)

```python
for goal_tid, deadline_days in deadline_map.items():
    all_prereqs = self.graph.get_all_prerequisites(goal_tid)  # Another DFS per goal per gap
```

This repeats the same DFS traversals done in the impact calculation. The prerequisite sets should be computed once and reused.

**PERF-3 (MEDIUM): `get_student_summary` loads all events into memory** (`aggregator.py:26-32`)

All learning events for the last 30 days are loaded into Python memory. For active students with thousands of events per month, this could be expensive. Consider using SQL aggregation (COUNT, SUM with GROUP BY).

**PERF-4 (MEDIUM): `get_student_mastery_by_subject` loads ALL events** (`aggregator.py:113-118`)

No date filter at all. Loads every event the student has ever created. This grows without bound.

### 6.3 Missing Error Handling

1. **No validation on `days` parameter** (`analytics.py:43-50`): The `days` query parameter for the activity heatmap has no bounds. A client could request `days=100000`, causing a massive query. Should be bounded (e.g., 1-365).

2. **No validation on `quality` in ReviewCompletedRequest** (`learning_path.py:28`): The quality field is `int` with no Pydantic validation. While the SM-2 algorithm clamps it (line 28 of `spaced_repetition.py`), the API should validate `0 <= quality <= 5` at the schema level using `Field(ge=0, le=5)`.

3. **No validation on `target_mastery` in GoalCreateRequest** (`learning_path.py:22`): Should be bounded to 0-100 using `Field(ge=0, le=100)`.

4. **`topic_id` string vs UUID mismatch** (`learning_path.py:123`): `GoalCreateRequest.topic_id` is `str`, but `TopicNode.id` is `UUID`. The comparison `TopicNode.id == body.topic_id` relies on SQLAlchemy/PostgreSQL to cast the string to UUID. An invalid UUID string would produce a database error rather than a clean 400 response.

### 6.4 Security Concerns

1. **Student analytics endpoints lack IDOR protection** (`analytics.py:22-66`): The student endpoints correctly use `current_user.id` rather than accepting a student_id parameter, preventing IDOR. This is good.

2. **Teacher endpoints use class_id without ownership verification** (`analytics.py:71-101`): Any teacher can query any class_id. There is no check that the teacher is assigned to that class. Currently mitigated by the stub returning empty data.

3. **No rate limiting on analytics endpoints**: Analytics queries hit the database directly and could be used for DoS if abused. However, the request-level rate limiter middleware may cover this at a higher level.

---

## 7. Test Coverage Analysis

### 7.1 What Is Tested

**Analytics Tests** (`tests/test_analytics.py` -- 298 lines, 24 test cases):
- `MetricsCalculator`: engagement rate (3 tests), accuracy rate (3 tests), streak (4 tests), learning velocity (3 tests), best study time (2 tests), daily metrics aggregation (1 test), topic mastery (3 tests), quiz score trend (5 tests), active study time (4 tests), weighted accuracy (1 test)
- `AlertEngine`: at-risk detection (6 tests covering all 4 alert types + healthy student + combined)

**Learning Path Tests** (`tests/test_learning_path.py` -- 269 lines, 16 test cases):
- `PrerequisiteGraph`: add topics (1), direct prerequisites (2), transitive prerequisites (1), topological sort (1), gap analysis (2), relationship types (3), complements (1)
- `PathRecommender`: foundations-first ordering (1), goal topic inclusion (1), empty goals (1)
- `SpacedRepetitionScheduler`: basic tests duplicated from dedicated file (2)

**SM-2 Tests** (`tests/test_spaced_repetition.py` -- 136 lines, 14 test cases):
- EF calculations for quality 0, 3, 4, 5 (4 tests)
- Quality clamping above 5 and below 0 (2 tests)
- Interval progression: first (1d), second (6d), third (EF*prev) (3 tests)
- Failed recall reset (1 test), interval minimum (1 test)
- Review date calculation (1 test)
- Reviews due filtering: overdue, today, future, null, default (5 tests)

### 7.2 What Is NOT Tested

**Critical gaps**:

1. **DataAggregator** -- Zero tests. The aggregator is the core business logic layer that translates raw events into dashboard data. None of `get_student_summary`, `get_student_activity_heatmap`, `get_student_mastery_by_subject` are tested. This is the highest-risk gap.

2. **API Endpoints** -- Zero integration tests for any analytics or learning path endpoint. No tests verify:
   - Correct HTTP status codes
   - Authentication/authorization enforcement
   - Request/response schema compliance
   - Error handling (invalid IDs, missing data)

3. **PrerequisiteGraph `load_from_db` / `save_to_db`** -- No tests for DB serialization. These methods contain UUID handling logic (BUG-2) and ORM operations.

4. **Graph cycle detection** -- No test verifying behavior when a cycle is introduced. The graph silently accepts cycles but will produce incorrect topological sorts and infinite recursion in gap analysis.

5. **PathRecommender deadline scoring** -- No test verifies that deadline proximity affects ordering.

6. **PathRecommender multi-goal impact** -- No test with multiple goals verifying that shared prerequisites are ranked higher.

7. **Edge cases in aggregator**:
   - Student with no events
   - Student with events but no quiz events
   - Events with missing `created_at`
   - Events with no `topic` field

8. **AlertEngine integration** -- The alert engine is tested in isolation but never tested as part of the aggregation flow (because it is not wired in).

### 7.3 Test Quality Assessment

The existing tests are well-structured:
- Good use of test classes for logical grouping
- Clear test names describing the scenario
- Assertions are specific and meaningful
- Edge cases covered for pure functions (empty inputs, zero denominators)
- SM-2 tests are particularly thorough, covering the mathematical properties

However, the complete absence of integration-level tests and aggregator tests means the system's correctness can only be verified through unit tests of pure functions, leaving the database interaction layer untested.

---

## 8. Summary of Issues

### Critical (3)

| ID | Location | Issue |
|----|----------|-------|
| C1 | `learning_path.py:60` | `student_mastery` is always empty; recommendations are not personalized |
| C2 | `aggregator.py:113-118` | `get_student_mastery_by_subject` loads ALL events without date filter |
| C3 | No tests | `DataAggregator` has zero test coverage |

### High (4)

| ID | Location | Issue |
|----|----------|-------|
| H1 | `learning_path.py:85` | `get_prerequisite_graph` fetches ALL edges then filters in Python |
| H2 | `recommender.py:65-68,84-86` | Duplicate DFS traversals in priority scoring (O(G*N*depth)) |
| H3 | Migration 006 | No indexes on any new table (daily_metrics, weekly_aggregates, topic_edges, student_goals, review_schedule) |
| H4 | Migration 006 | No unique constraints on (student_id, date), (student_id, topic_id), etc. |

### Medium (5)

| ID | Location | Issue |
|----|----------|-------|
| M1 | `alerts.py:8` | AlertEngine imported but never called by any endpoint/aggregator |
| M2 | `analytics.py`, `learning_path.py` | DailyMetric/WeeklyAggregate models defined but never used |
| M3 | `graph.py:190` | Unreliable UUID detection via string length |
| M4 | `aggregator.py:26-32` | All 30-day events loaded into memory per request |
| M5 | `learning_path.py:37-38` | Graph rebuilt from DB on every request |

### Low (4)

| ID | Location | Issue |
|----|----------|-------|
| L1 | `learning_path.py:28` | No Pydantic validation on `quality` (0-5 range) |
| L2 | `learning_path.py:22` | No Pydantic validation on `target_mastery` (0-100 range) |
| L3 | `analytics.py:43` | No bounds on `days` query parameter |
| L4 | `alerts.py:34` | Mastery decline check requires strict monotonic decrease |

---

## 9. Recommendations

### Immediate (before next release)

1. **Wire up student mastery data** (C1): The `/learning-path/recommended` endpoint should query actual mastery from analytics (either from `DataAggregator.get_student_mastery_by_subject()` or a dedicated mastery service) and pass real scores to the recommender.

2. **Add indexes** (H3): Add composite indexes on all frequently-queried columns:
   ```sql
   CREATE INDEX ix_daily_metrics_student_date ON daily_metrics(student_id, date);
   CREATE INDEX ix_weekly_agg_student_week ON weekly_aggregates(student_id, week_start);
   CREATE INDEX ix_topic_edges_from ON topic_edges(from_topic_id);
   CREATE INDEX ix_topic_edges_to ON topic_edges(to_topic_id);
   CREATE INDEX ix_student_goals_student ON student_goals(student_id);
   CREATE INDEX ix_review_schedule_student_topic ON review_schedule(student_id, topic_id);
   ```

3. **Add unique constraints** (H4): Prevent data corruption with UNIQUE constraints on natural keys.

4. **Add DataAggregator tests** (C3): Write async integration tests using an in-memory SQLite or test PostgreSQL database.

5. **Add date filter to mastery query** (C2): Add a reasonable date window to `get_student_mastery_by_subject()`.

### Short-term

6. **Filter edges at SQL level** (H1): Replace `select(TopicEdge)` with a filtered query using the node_ids set.

7. **Cache prerequisite set computations** (H2): Pre-compute `get_all_prerequisites()` once per goal and reuse across gap/impact/deadline scoring.

8. **Cache the prerequisite graph** (M5): Load the graph once at startup or with TTL caching, invalidate on topic/edge CRUD operations.

9. **Wire AlertEngine** (M1): Call `AlertEngine.check_at_risk()` from the aggregator or create a dedicated alerts endpoint.

10. **Add Pydantic validation** (L1, L2, L3): Use `Field(ge=0, le=5)` for quality, `Field(ge=0, le=100)` for target_mastery, and `Field(ge=1, le=365)` for days.

### Medium-term

11. **Implement DailyMetric/WeeklyAggregate materialization** (M2): Create a background task or cron job that populates these tables from LearningEvent data. Update the aggregator to read from pre-computed tables instead of re-querying raw events.

12. **Add cycle detection** to `add_prerequisite()`: Run a quick DFS/BFS to verify the edge doesn't create a cycle before accepting it.

13. **Add API integration tests**: Test all endpoints with mocked auth, verifying response schemas, error codes, and authorization enforcement.

14. **Implement class enrollment**: Replace the stub teacher endpoints with actual implementations once class/enrollment tables are available.

---

## 10. Files Audited

| File | Lines | Purpose |
|------|-------|---------|
| `src/analytics/calculator.py` | 229 | Stateless metrics calculations |
| `src/analytics/aggregator.py` | 195 | DB-to-calculator bridge |
| `src/analytics/alerts.py` | 72 | At-risk student detection |
| `src/learning_path/graph.py` | 209 | Prerequisite DAG |
| `src/learning_path/recommender.py` | 114 | Priority-based recommendations |
| `src/learning_path/spaced_repetition.py` | 68 | SM-2 algorithm |
| `src/models/analytics.py` | 39 | DailyMetric, WeeklyAggregate |
| `src/models/learning_path.py` | 79 | TopicNode, TopicEdge, StudentGoal, ReviewSchedule |
| `src/models/learning_event.py` | 26 | LearningEvent (source data) |
| `src/api/routers/analytics.py` | 102 | Analytics API endpoints |
| `src/api/routers/learning_path.py` | 244 | Learning path API endpoints |
| `migrations/versions/006_analytics_path_tables.py` | 106 | Migration for all 6 tables |
| `tests/test_analytics.py` | 298 | Analytics unit tests (24 cases) |
| `tests/test_learning_path.py` | 269 | Learning path + SM-2 tests (16 cases) |
| `tests/test_spaced_repetition.py` | 136 | Dedicated SM-2 tests (14 cases) |
| `src/api/main.py` | 80 | Router registration |
| `src/api/dependencies.py` | 75 | FastAPI dependencies |
| `src/auth/rbac.py` | 42 | RBAC enforcement |
| **Total** | **~2,383** | |
