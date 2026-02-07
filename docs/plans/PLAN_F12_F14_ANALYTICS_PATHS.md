# F12 + F14: Analytics Dashboard Backend + Learning Path Engine

## Overview

Build the analytics dashboard backend (F12) and learning path recommendation engine (F14) for EduAGI. These features provide students and teachers with performance insights, study recommendations, and spaced repetition scheduling.

## Architecture

### F12 -- Analytics Dashboard Backend

**Components:**
- `src/analytics/calculator.py` -- Pure math: engagement rates, weighted accuracy, streaks, velocity, topic mastery (weighted: quiz 40%, AI assessment 30%, interaction 20%, recency 10%), quiz score trends, active study time
- `src/analytics/aggregator.py` -- Async DB queries that compose calculator functions (student + class-level)
- `src/analytics/alerts.py` -- At-risk student detection with configurable thresholds
- `src/models/analytics.py` -- DailyMetric, WeeklyAggregate SQLAlchemy models
- `src/api/routers/analytics.py` -- REST endpoints for student and teacher dashboard data

**Student Metrics:**
- topic_mastery: weighted avg (quiz 40%, ai_assessment 30%, interaction 20%, recency 10%)
- learning_velocity: slope of mastery over time (linear regression)
- engagement_rate: active_days / total_days * 100
- quiz_score_trend: rolling 5-quiz average with direction indicator
- time_studied: sum of active session durations (excluding idle >5min)
- streak_days: consecutive days with >= 1 session
- accuracy_rate: correct / total answers (weighted by difficulty)
- best_study_time: hour-of-day with highest accuracy (last 30 days)

**Teacher Metrics (per class):**
- class_avg_mastery: avg student mastery per topic
- at_risk_count: students with mastery <30% or no activity in 7 days
- class_engagement: avg engagement rate
- topic_difficulty_ranking: topics ranked by class-wide struggle rate

**At-Risk Detection:**
- No activity for 7+ days (warning at 7, critical at 14)
- Mastery declining 3+ consecutive assessments
- Engagement rate below 30%
- Quiz scores consistently below 40%
- Each alert has: type, severity, message, suggestion

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/analytics/student/summary | Student dashboard overview |
| GET | /api/v1/analytics/student/mastery | Mastery by subject/topic |
| GET | /api/v1/analytics/student/activity | Activity heatmap (day x hour) |
| GET | /api/v1/analytics/student/streaks | Streak info |
| GET | /api/v1/analytics/teacher/class/{class_id}/overview | Class summary |
| GET | /api/v1/analytics/teacher/class/{class_id}/students | Student list with metrics |
| GET | /api/v1/analytics/teacher/class/{class_id}/at-risk | At-risk students with alerts |

### F14 -- Learning Path Recommendation Engine

**Components:**
- `src/learning_path/graph.py` -- DAG with three edge types (REQUIRES, RECOMMENDS, COMPLEMENTS), DFS/topological sort, gap detection
- `src/learning_path/recommender.py` -- Priority-based path recommendation
- `src/learning_path/spaced_repetition.py` -- SM-2 algorithm implementation
- `src/models/learning_path.py` -- TopicNode, TopicEdge, StudentGoal, ReviewSchedule
- `src/api/routers/learning_path.py` -- REST endpoints for paths and reviews

**Prerequisite Graph Edge Types:**
- REQUIRES: hard prerequisite (must master before advancing)
- RECOMMENDS: soft prerequisite (helpful but not required)
- COMPLEMENTS: related topic (broadens understanding)
- Gap analysis follows only REQUIRES by default (configurable with include_soft)

**Path Recommendation Algorithm:**
1. Load student's current mastery per topic
2. Identify target topics (curriculum goals + student goals)
3. Compute prerequisite gaps (unmastered prerequisites of targets)
4. Prioritize by: prerequisite_depth, impact_score, estimated_time, deadline proximity
5. Return ordered list with time estimates and reasons

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/learning-path/recommended | Personalized study recommendations |
| GET | /api/v1/learning-path/graph/{subject} | Prerequisite graph for a subject |
| POST | /api/v1/learning-path/goals | Create a learning goal |
| GET | /api/v1/learning-path/reviews-due | Topics due for spaced repetition |
| POST | /api/v1/learning-path/review-completed | Record review completion |

## Database Tables (Migration 006)

- `daily_metrics` -- Per-student daily aggregated metrics
- `weekly_aggregates` -- Per-student weekly roll-ups
- `topic_nodes` -- Prerequisite graph vertices
- `topic_edges` -- Prerequisite graph edges
- `student_goals` -- Student learning goals
- `review_schedule` -- SM-2 spaced repetition tracking

## Key Algorithms

1. **Topic Mastery**: Weighted average (quiz 40%, AI assessment 30%, interaction 20%, recency 10%)
2. **Learning Velocity**: Linear regression slope over mastery scores
3. **Quiz Score Trend**: Rolling window average with direction detection
4. **Prerequisite Gap Analysis**: DFS through prerequisite graph, filter by mastery threshold and edge type
5. **SM-2 Spaced Repetition**: SuperMemo algorithm with easiness factor adjustment
6. **Recommendation Priority**: Weighted score of prerequisite depth, goal impact, time, deadline

## Security

- Students only see their own analytics
- Teachers require teacher/admin role (RBAC enforced) for class endpoints
- Class enrollment stub ready for when enrollment tables are added

## Testing Strategy

All tests are pure Python, no DB/Redis/ChromaDB required:
- `tests/test_analytics.py` -- Calculator (engagement, accuracy, weighted accuracy, streaks, velocity, topic mastery, quiz trends, active study time), alert engine
- `tests/test_learning_path.py` -- Graph (add, DFS, topological sort, gap finding, edge types REQUIRES/RECOMMENDS/COMPLEMENTS), recommender
- `tests/test_spaced_repetition.py` -- SM-2 algorithm (EF adjustment, interval progression, quality clamping, review date, reviews-due filtering)
