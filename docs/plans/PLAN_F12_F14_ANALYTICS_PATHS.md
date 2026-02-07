# F12 + F14: Analytics Dashboard Backend + Learning Path Engine

## Overview

Build the analytics dashboard backend (F12) and learning path recommendation engine (F14) for EduAGI. These features provide students with performance insights, study recommendations, and spaced repetition scheduling.

## Architecture

### F12 — Analytics Dashboard Backend

**Components:**
- `src/analytics/calculator.py` — Pure math: engagement rates, accuracy, streaks, velocity
- `src/analytics/aggregator.py` — Async DB queries that compose calculator functions
- `src/analytics/alerts.py` — At-risk student detection with configurable thresholds
- `src/models/analytics.py` — DailyMetric, WeeklyAggregate SQLAlchemy models
- `src/api/routers/analytics.py` — REST endpoints for dashboard data

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/analytics/summary | Student dashboard overview |
| GET | /api/v1/analytics/mastery | Mastery breakdown by subject |
| GET | /api/v1/analytics/activity | Activity heatmap (30 days) |
| GET | /api/v1/analytics/streaks | Streak data |

### F14 — Learning Path Recommendation Engine

**Components:**
- `src/learning_path/graph.py` — DAG of topic prerequisites with DFS/topological sort
- `src/learning_path/recommender.py` — Priority-based path recommendation
- `src/learning_path/spaced_repetition.py` — SM-2 algorithm implementation
- `src/models/learning_path.py` — TopicNode, TopicEdge, StudentGoal, ReviewSchedule
- `src/api/routers/learning_path.py` — REST endpoints for paths and reviews

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/learning-path/recommended | Personalized study recommendations |
| GET | /api/v1/learning-path/graph/{subject} | Prerequisite graph for a subject |
| POST | /api/v1/learning-path/goals | Create a learning goal |
| GET | /api/v1/learning-path/reviews-due | Topics due for spaced repetition |
| POST | /api/v1/learning-path/review-completed | Record review completion |

## Database Tables (Migration 006)

- `daily_metrics` — Per-student daily aggregated metrics
- `weekly_aggregates` — Per-student weekly roll-ups
- `topic_nodes` — Prerequisite graph vertices
- `topic_edges` — Prerequisite graph edges
- `student_goals` — Student learning goals
- `review_schedule` — SM-2 spaced repetition tracking

## Key Algorithms

1. **Learning Velocity**: Linear regression slope over mastery scores
2. **Prerequisite Gap Analysis**: DFS through prerequisite graph, filter by mastery threshold
3. **SM-2 Spaced Repetition**: Standard SuperMemo algorithm with easiness factor adjustment
4. **Recommendation Priority**: Weighted score of prerequisite depth, goal impact, time, deadline

## Testing Strategy

All tests are pure Python, no DB/Redis/ChromaDB required. Tests validate:
- Calculator math functions with known inputs/outputs
- Alert engine threshold detection
- Graph operations (add, DFS, topological sort, gap finding)
- SM-2 interval calculations
- Recommendation ordering
