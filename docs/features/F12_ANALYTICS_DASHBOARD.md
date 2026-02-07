# Feature 12: Progress Analytics Dashboard

## Overview

A visual analytics dashboard that transforms raw learning data into actionable insights for students, teachers, administrators, and parents. Every tutoring interaction, quiz attempt, study session, and milestone generates data. This feature turns that data into meaningful visualizations that help students understand their own progress, help teachers identify struggling students early, and help administrators measure platform effectiveness.

**Priority:** High (P1)
**Status:** Design Phase
**Dependencies:** Student Memory System (F5), Assessment Engine (F8), Tutoring System (F1), Learning Path (F14)
**Stakeholders:** Students, Teachers, Parents, School Administrators, Platform Administrators

---

## Student Perspective

Marcus opens his EduAGI dashboard on Monday morning. He immediately sees:
- His weekly streak counter shows 12 days (his longest yet)
- A radar chart shows Biology and Chemistry are strong, but Physics "Kinematics" is a notable weak area
- A line chart shows his quiz scores trending upward over the last month in all subjects
- A heat map reveals he studies most effectively between 7-9 PM (his scores from that time window are highest)
- A notification says: "Based on your progress, you are on track to meet your AP Biology goal by March 15"
- A "What to study today" card recommends focusing on Kinematics, with an estimated 45 minutes to bring it up one mastery level
- He taps "Compare to last month" and sees concrete improvement in 6 out of 8 topics

This is not just data display. It is a motivational system that makes learning progress visible and actionable.

---

## Dashboard Views

### View Architecture

```
DASHBOARD VIEW HIERARCHY
==========================

  +------------------------------------------------------------------+
  |                    ANALYTICS DASHBOARD                            |
  +------------------------------------------------------------------+
  |                                                                    |
  |  +-----------------+                                              |
  |  |  ROLE SELECTOR  |  (automatically set by logged-in user role)  |
  |  +-----------------+                                              |
  |         |                                                         |
  |         +------+----------+-----------+----------+               |
  |         |      |          |           |          |               |
  |         v      v          v           v          v               |
  |     +------+ +-------+ +-------+ +-------+ +--------+          |
  |     |STUDENT| |TEACHER| |PARENT | |SCHOOL | |PLATFORM|          |
  |     | VIEW  | | VIEW  | | VIEW  | | ADMIN | | ADMIN  |          |
  |     +------+ +-------+ +-------+ +-------+ +--------+          |
  |                                                                    |
  +------------------------------------------------------------------+
```

---

## Student Dashboard View

### Layout

```
STUDENT DASHBOARD LAYOUT
==========================

+------------------------------------------------------------------+
|  Welcome back, Marcus!              Streak: 12 days [flame icon]  |
+------------------------------------------------------------------+
|                           |                                        |
|  TODAY'S RECOMMENDATION   |   WEEKLY SUMMARY                      |
|                           |                                        |
|  Focus: Kinematics        |   Sessions: 8                         |
|  Est. time: 45 min        |   Questions answered: 47              |
|  Why: Lowest mastery in   |   Accuracy: 78% (+5% from last week) |
|  your current subjects    |   Time studied: 6h 23m               |
|  [Start Studying -->]     |   Topics improved: 6                  |
|                           |                                        |
+---------------------------+----------------------------------------+
|                                                                    |
|  MASTERY BY TOPIC (Radar Chart)                                   |
|                                                                    |
|              Cell Biology                                          |
|                  *                                                  |
|                 / \                                                 |
|    Genetics   /   \   Ecology                                     |
|        *-----*     *-----*                                        |
|         \   / \   / \   /                                         |
|          \ /   \ /   \ /                                          |
|           *     *     *                                            |
|      Evolution    Kinematics                                      |
|                                                                    |
|  [View Details]  [Compare to Last Month]                          |
|                                                                    |
+------------------------------------------------------------------+
|                           |                                        |
|  QUIZ SCORES OVER TIME   |   STUDY PATTERN HEAT MAP              |
|  (Line Chart)            |                                        |
|                           |   Mon [##  ####  ]                    |
|  100|      . *            |   Tue [     #### ]                    |
|   90|   * .   *           |   Wed [##  ####  ]                    |
|   80| *                   |   Thu [     #### ]                    |
|   70|                     |   Fri [##       ]                     |
|   60|                     |   Sat [   ####   ]                    |
|     +------------>        |   Sun [####      ]                    |
|     W1  W2  W3  W4       |       6am    12pm    6pm    12am      |
|                           |                                        |
+---------------------------+----------------------------------------+
|                                                                    |
|  GOALS & MILESTONES                                               |
|                                                                    |
|  AP Biology Exam (May 15)                                         |
|  [====================>          ] 68% on track                   |
|  Estimated ready: April 28 (17 days ahead of schedule)            |
|                                                                    |
|  Chemistry Final (June 3)                                         |
|  [============>                  ] 41% on track                   |
|  Estimated ready: May 29 (5 days ahead of schedule)               |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  ACHIEVEMENTS & STREAKS                                           |
|                                                                    |
|  [10-day streak]  [Biology Master]  [100 Questions]  [Night Owl] |
|                                                                    |
+------------------------------------------------------------------+
```

### Student Metrics

| Metric | Calculation | Update Frequency |
|--------|------------|-----------------|
| Topic Mastery | Weighted average of quiz scores, AI assessment, and spaced repetition performance per topic | After each session |
| Learning Velocity | Rate of mastery change over time (mastery points gained per week) | Daily |
| Engagement Rate | (Active study days / Total days in period) x 100 | Daily |
| Quiz Score Trend | Rolling average of quiz scores with trend direction | After each quiz |
| Time Studied | Sum of active session durations (idle time excluded) | Real-time |
| Streak Days | Consecutive days with at least one study session | Daily |
| Accuracy Rate | Correct answers / Total answers, weighted by question difficulty | After each session |
| Goal Progress | Mastery across goal-relevant topics / Total required mastery | Daily |
| Best Study Time | Time-of-day window with highest average accuracy | Weekly |
| Improvement Delta | Current mastery minus mastery N days ago, per topic | Daily |

---

## Teacher Dashboard View

### Layout

```
TEACHER DASHBOARD LAYOUT
==========================

+------------------------------------------------------------------+
|  Ms. Rodriguez's Dashboard            AP Biology - Period 3       |
|                                        [Switch Class v]           |
+------------------------------------------------------------------+
|                                                                    |
|  CLASS OVERVIEW                                                   |
|                                                                    |
|  Students: 32        Avg Mastery: 74%       At-Risk: 3           |
|  Active Today: 28    Avg Engagement: 82%    Top Performer: Sarah |
|                                                                    |
+------------------------------------------------------------------+
|                           |                                        |
|  CLASS MASTERY HEATMAP   |   AT-RISK ALERTS                      |
|                           |                                        |
|  Topic        Mastery    |   [!] Marcus Chen                     |
|  Cell Bio     [========] |   Mastery dropped 15% this week       |
|  Genetics     [=======]  |   Last active: 3 days ago             |
|  Ecology      [======]   |   Suggestion: Assign review quiz      |
|  Evolution    [=====]    |   [Contact Student] [Assign Work]     |
|  Kinematics   [===]      |                                        |
|               ^problem   |   [!] Jordan Williams                  |
|                           |   0 sessions in last 7 days           |
|                           |   Suggestion: Check in with student   |
|                           |   [Contact Student] [View History]    |
|                           |                                        |
+---------------------------+----------------------------------------+
|                                                                    |
|  STUDENT PERFORMANCE TABLE                                        |
|                                                                    |
|  Name            Mastery  Engagement  Trend   Alerts   Actions   |
|  Sarah Kim       92%      95%         UP      --       [View]    |
|  Alex Torres     85%      88%         UP      --       [View]    |
|  Maria Garcia    78%      75%         FLAT    --       [View]    |
|  ...                                                              |
|  Marcus Chen     61%      45%         DOWN    [!]      [View]    |
|  Jordan Williams 58%      12%         DOWN    [!]      [View]    |
|                                                                    |
|  [Export CSV]  [Print Report]  [Bulk Message]                     |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  CLASS-WIDE WEAK TOPICS              RECENT ASSESSMENTS           |
|                                                                    |
|  These topics have <60% avg mastery: Quiz 7: Mitosis              |
|  - Kinematics (avg: 47%)             Avg: 76%  Completed: 30/32  |
|  - Thermodynamics (avg: 52%)         [View Results]               |
|  - Wave Mechanics (avg: 58%)                                      |
|                                       Quiz 6: Cell Division       |
|  Suggestion: Consider a review        Avg: 82%  Completed: 32/32 |
|  session on Kinematics               [View Results]               |
|  [Generate Review Material]                                        |
|                                                                    |
+------------------------------------------------------------------+
```

### Individual Student Drill-Down

When a teacher clicks "View" on a student:

```
INDIVIDUAL STUDENT VIEW (Teacher Perspective)
===============================================

+------------------------------------------------------------------+
|  Marcus Chen - AP Biology            [Back to Class Overview]     |
+------------------------------------------------------------------+
|                                                                    |
|  Overall Mastery: 61%   Engagement: 45%   Risk Level: HIGH       |
|  Last Active: 3 days ago   Total Sessions: 23   Avg Duration: 18m|
|                                                                    |
+------------------------------------------------------------------+
|                           |                                        |
|  MASTERY BY TOPIC         |   ENGAGEMENT TIMELINE                 |
|  (Same radar chart as     |   (Calendar heatmap showing           |
|   student sees, but       |    daily activity intensity)          |
|   teacher can see         |                                        |
|   class average overlay)  |   Jan: [## ## ###  ## # #    ##  ]   |
|                           |   Feb: [#   #          ]              |
|                           |        ^--- engagement dropped        |
|                           |                                        |
+---------------------------+----------------------------------------+
|                                                                    |
|  AI INSIGHTS                                                      |
|                                                                    |
|  "Marcus was progressing well through January but engagement      |
|   dropped significantly in February. His accuracy on Kinematics   |
|   questions dropped from 72% to 45% over the last two weeks.     |
|   His study sessions have shortened from 35 min avg to 12 min    |
|   avg. Consider: (1) reaching out to check on external factors,  |
|   (2) assigning shorter, more engaging practice sets,             |
|   (3) adjusting difficulty down temporarily to rebuild            |
|   confidence."                                                    |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  TEACHER ACTIONS                                                  |
|                                                                    |
|  [Send Message]  [Assign Custom Work]  [Adjust AI Difficulty]    |
|  [Schedule Meeting]  [Add Note]  [View Full Session History]     |
|                                                                    |
+------------------------------------------------------------------+
```

### Teacher Metrics

| Metric | Description | Granularity |
|--------|------------|-------------|
| Class Average Mastery | Mean mastery score across all students for a class | Per topic, per class |
| At-Risk Student Count | Students whose mastery or engagement dropped significantly | Daily |
| Engagement Distribution | Histogram of engagement rates across the class | Weekly |
| Topic Difficulty Index | Topics where the class struggles most (lowest avg mastery) | Per assessment cycle |
| Assessment Completion Rate | % of students who completed each assigned assessment | Per assessment |
| AI Intervention Effectiveness | Did students improve after AI-suggested interventions? | Monthly |
| Content Coverage | % of uploaded curriculum content actually used in student sessions | Monthly |
| Response Rate | Avg time for teacher to respond to at-risk alerts | Rolling 30 days |

---

## Admin Dashboard View

### School Administrator

```
SCHOOL ADMIN DASHBOARD
========================

+------------------------------------------------------------------+
|  Washington High School - EduAGI Overview       Feb 2026         |
+------------------------------------------------------------------+
|                                                                    |
|  PLATFORM USAGE                                                   |
|                                                                    |
|  Active Students: 847/920 (92%)    Active Teachers: 41/45 (91%) |
|  Total Sessions (Month): 12,340    Avg Session Duration: 24 min  |
|  Documents Uploaded: 1,847         Storage Used: 34.2 GB / 500GB |
|                                                                    |
+------------------------------------------------------------------+
|                           |                                        |
|  MASTERY BY DEPARTMENT    |   TEACHER ADOPTION                    |
|  (Grouped bar chart)     |                                        |
|                           |   Science: 12/12 active               |
|  Science    [========]   |   Math:     9/10 active                |
|  Math       [=======]    |   English:  8/9  active                |
|  English    [======]     |   History:  7/8  active                |
|  History    [=====]      |   Art:      3/4  active                |
|  Art        [====]       |   PE:       2/2  active                |
|                           |                                        |
+---------------------------+----------------------------------------+
|                                                                    |
|  SYSTEM-WIDE ALERTS                                               |
|                                                                    |
|  [!] 23 students flagged at-risk across all classes               |
|  [!] Physics department has 40% avg mastery (lowest)              |
|  [i] 3 teachers have not uploaded content in 30+ days             |
|  [i] Storage approaching 50% capacity                             |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  DEPARTMENT DRILL-DOWN    [Select Department v]                   |
|                                                                    |
|  CLASS COMPARISON         [Compare Classes v]                     |
|                                                                    |
|  EXPORT OPTIONS           [PDF Report] [CSV Data] [Schedule       |
|                            Weekly Email]                           |
|                                                                    |
+------------------------------------------------------------------+
```

### Platform Administrator (System-Wide)

| Metric | Description |
|--------|------------|
| Total active users | Across all schools on the platform |
| System uptime | Availability percentage and incident log |
| API response times | p50, p95, p99 latencies for key endpoints |
| Processing queue depth | Document processing backlog |
| AI model usage | Token consumption, model distribution, cost tracking |
| Error rates | Failed sessions, processing errors, API errors |
| Storage utilization | Total across all schools, growth trend |
| Cost per student | Total infrastructure cost / active students |

---

## Parent Dashboard View

```
PARENT VIEW
=============

+------------------------------------------------------------------+
|  Marcus Chen's Progress            Parent View                    |
+------------------------------------------------------------------+
|                                                                    |
|  WEEKLY SUMMARY                                                   |
|                                                                    |
|  Marcus studied 4 out of 7 days this week.                       |
|  He completed 3 quizzes with an average score of 76%.            |
|  Strongest area: Cell Biology (92% mastery)                       |
|  Area needing attention: Kinematics (47% mastery)                |
|                                                                    |
|  Compared to last week:                                           |
|  - Study time: DOWN 2 hours                                       |
|  - Quiz scores: UP 3%                                             |
|  - Topics improved: 2                                             |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  PROGRESS OVER TIME (simplified line chart)                       |
|                                                                    |
|  Shows monthly mastery trend, not daily noise.                    |
|  Clear "improving" / "steady" / "declining" labels.               |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  TEACHER NOTES                                                    |
|                                                                    |
|  Ms. Rodriguez (Feb 3): "Marcus did well on the mitosis quiz.   |
|  I recommend he spend extra time on kinematics problems."         |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  [Email Preferences]  [Contact Teacher]                           |
|                                                                    |
+------------------------------------------------------------------+
```

- Simplified view: no jargon, no raw numbers where a plain-English summary works better
- Privacy-conscious: parent sees progress and teacher comments, but not chat transcripts with the AI tutor
- Configurable: student (if over 16) can control what parents see
- Weekly email digest option

---

## Metrics Calculation Details

### Mastery Score Per Topic

```
MASTERY CALCULATION
====================

For each topic T and student S:

  mastery(S, T) = weighted_average(
    quiz_performance(S, T)    * 0.35,
    ai_assessment(S, T)       * 0.25,
    spaced_repetition(S, T)   * 0.20,
    recency_factor(S, T)      * 0.10,
    consistency_factor(S, T)  * 0.10
  )

  Where:
  - quiz_performance    = avg score on quizzes tagged with topic T
  - ai_assessment       = AI's evaluation of understanding during tutoring sessions
  - spaced_repetition   = performance on spaced repetition reviews (retention)
  - recency_factor      = higher if recently studied (exponential decay, half-life 14 days)
  - consistency_factor  = stability of performance (low variance = higher)

  Mastery scale: 0-100
  - 0-20:   Not Started
  - 21-40:  Beginner
  - 41-60:  Developing
  - 61-80:  Proficient
  - 81-100: Mastered
```

### Learning Velocity

```
LEARNING VELOCITY
==================

  velocity(S, T) = (mastery(S, T, now) - mastery(S, T, now - 7 days)) / 7

  Interpretation:
  - Positive: Student is improving in topic T
  - Zero: Student is plateaued
  - Negative: Student is regressing (mastery decaying due to inactivity or poor recent performance)

  Velocity is smoothed with a 3-week rolling average to reduce noise.
```

### Engagement Rate

```
ENGAGEMENT RATE
================

  engagement(S, period) = (active_days_in_period / total_days_in_period) * 100

  An "active day" = at least one study session of >= 5 minutes.

  Sub-metrics:
  - session_frequency:  sessions per week
  - session_duration:   avg minutes per session
  - session_depth:      avg questions answered per session
  - voluntary_sessions: sessions not triggered by assignments (self-motivated study)
```

### Predictive At-Risk Detection

```
AT-RISK DETECTION ALGORITHM
=============================

  risk_score(S) = weighted_sum(
    engagement_drop(S)        * 0.30,   // engagement rate dropped >20% vs 2-week avg
    mastery_decline(S)        * 0.25,   // mastery in any topic dropped >10 points
    inactivity_days(S)        * 0.20,   // consecutive days without a session
    session_shortening(S)     * 0.15,   // avg session duration declining
    negative_sentiment(S)     * 0.10    // AI detected frustration in recent sessions
  )

  Thresholds:
  - risk_score > 0.7:  HIGH risk -> immediate teacher alert
  - risk_score > 0.5:  MEDIUM risk -> included in weekly summary
  - risk_score > 0.3:  LOW risk -> visible in dashboard, no alert

  Alert message generated by LLM:
  "Marcus may fall behind in Biology. His engagement dropped 35% this week,
   and his last 3 quiz scores in Kinematics were below 50%. Consider
   reaching out to check on him."
```

---

## Visualization Types

### Progress Bars

- Used for: Goal progress, topic mastery, course completion percentage
- Style: Rounded, color-coded (red < 40%, yellow 40-70%, green > 70%)
- Animation: Smooth fill on load, celebratory pulse when milestone reached

### Line Charts

- Used for: Quiz scores over time, mastery trends, engagement trends
- Features: Hover for exact values, zoom into date ranges, overlay class average
- Multiple series: Compare subjects or compare current vs. previous period
- Trend line: Optional linear regression overlay to show trajectory

### Radar Charts (Strength Map)

- Used for: Multi-topic mastery comparison at a glance
- Axes: One per topic (6-12 topics ideal; group into categories if more)
- Overlays: Student vs. class average, current vs. previous period
- Interaction: Click an axis to drill into that topic's detail view

### Heat Maps

#### Study Pattern Heat Map

- Grid: 7 rows (days of week) x 24 columns (hours of day)
- Color intensity: Amount of study activity in that time slot
- Insight extraction: Automatically identify "peak study times" and "most effective study times" (highest accuracy periods)

#### Calendar Activity Heat Map

- GitHub-style contribution calendar showing daily activity intensity
- Months as columns, days as rows
- Hover for details: "Feb 3: 2 sessions, 45 min, 12 questions"

#### Class Mastery Heat Map (Teacher)

- Grid: students (rows) x topics (columns)
- Color: mastery level (red to green)
- Sort by: student name, overall mastery, specific topic mastery
- Quickly identify: which topics are problematic class-wide (full red column) and which students are struggling broadly (full red row)

### Leaderboards (Opt-In)

- Students must explicitly opt in to appear on leaderboards
- Metrics: streak length, questions answered, mastery improvement (not raw mastery -- to avoid discouraging lower performers)
- Anonymization option: show rank without names
- Teacher can disable leaderboards for a class
- Gamification elements: badges, titles, seasonal challenges

---

## Sub-Features

### Weekly Email Reports

```
WEEKLY EMAIL REPORT FLOW
==========================

  +----------------+     +------------------+     +----------------+
  | Sunday 8 PM    |---->| Report Generator |---->| Email Service  |
  | (Cron trigger) |     |                  |     | (SendGrid /    |
  +----------------+     | For each student:|     |  SES / SMTP)   |
                         | - Compute weekly |     +--------+-------+
                         |   metrics        |              |
                         | - Generate       |              v
                         |   summary text   |     +----------------+
                         | - Render email   |     | Student inbox  |
                         |   template       |     | Teacher inbox  |
                         +------------------+     | Parent inbox   |
                                                  +----------------+
```

**Student email contains:**
- This week: days studied, questions answered, quizzes completed, time spent
- Mastery changes: topics improved, topics that declined
- Streak status and encouragement
- "What to focus on next week" recommendation
- Link to full dashboard

**Teacher email contains:**
- Class summary: engagement rate, avg mastery change, assessment completion
- At-risk student list with brief explanations
- Class-wide weak topics
- Suggested actions

**Parent email contains:**
- Student's week summary in plain language
- Teacher notes (if any)
- Encouragement and tips for supporting learning at home

### Goal Tracking Visualization

- Students set goals: "Pass AP Biology exam by May 15" or "Master all Algebra II topics by semester end"
- System decomposes goal into sub-milestones based on topic dependency graph (from Learning Path, F14)
- Progress bar shows overall goal progress
- Timeline view shows projected completion date based on current velocity
- Milestone celebrations: confetti animation, achievement badge when a sub-milestone is reached
- "On track" / "Behind schedule" / "Ahead of schedule" indicator with days

### Predictive Alerts

- Proactive notifications to teachers when a student's at-risk score crosses the threshold
- Delivered via: in-app notification, email, and optionally SMS/push notification
- Each alert includes: what happened (data), why it matters (context), and what to do (actionable suggestion)
- Alert fatigue management: group related alerts, suppress duplicate alerts within 48 hours, allow teachers to snooze alerts for specific students
- Weekly digest alternative: all alerts collected into a single weekly email for teachers who prefer batch updates

### Exportable Reports (PDF)

- Student progress report: suitable for parent-teacher conferences
- Class summary report: suitable for department meetings
- Individual student report: detailed analytics for intervention planning
- PDF generated server-side using a report template engine
- Customizable: teacher selects date range, metrics to include, sections to include
- Branding: school logo and name on reports

### Shareable Progress Cards

- Students can generate a "progress card" -- a visual summary image they can share
- Contains: mastery radar chart, streak count, recent achievement badges
- No sensitive data (no quiz scores, no comparison to class average)
- Shareable via link (not social media directly, for student safety)
- Teacher can generate class-level progress cards for school newsletters

### Study Pattern Analysis

```
STUDY PATTERN ANALYSIS
========================

Inputs:
- Session timestamps and durations
- Quiz/assessment scores with timestamps
- Topic of study per session

Analysis:
1. Time-of-day effectiveness:
   - Bin sessions by hour-of-day
   - Calculate avg accuracy per time bin
   - Result: "You perform best between 7-9 PM (83% accuracy vs 71% overall)"

2. Session duration sweet spot:
   - Correlate session duration with accuracy
   - Result: "Your accuracy peaks in 25-35 minute sessions. After 45 minutes, it drops."

3. Day-of-week patterns:
   - Result: "You study most on Wednesdays and Sundays"

4. Spacing analysis:
   - Correlate days between study sessions on same topic with retention
   - Result: "Reviewing Biology every 3 days works best for you"

5. Fatigue detection:
   - Accuracy decline within a single session
   - Result: "After 40 minutes, your accuracy drops. Consider taking a break."

Output: Personalized study schedule recommendation.
```

### Comparison Mode

- Compare two time periods: "This month vs last month" or "This semester vs last semester"
- Side-by-side visualization for all metrics
- Delta indicators: arrows and percentages showing change
- Narrative summary: "Compared to last month, your mastery in Biology improved by 12 points, but engagement decreased by 15%. Your total study time was similar (24h vs 26h)."

---

## Data Flow

```
DATA FLOW: FROM LEARNING TO DASHBOARD
=======================================

  +------------------+
  | STUDENT ACTIVITY |
  | - Tutoring session (F1)
  | - Quiz attempt (F8)
  | - Study session
  | - Document read
  +--------+---------+
           |
           v
  +------------------+
  | EVENT STREAM     |
  | (Real-time       |
  |  events emitted  |
  |  as student      |
  |  interacts)      |
  +--------+---------+
           |
           +---------------------------+
           |                           |
           v                           v
  +------------------+       +------------------+
  | STUDENT MEMORY   |       | ANALYTICS        |
  | SYSTEM (F5)      |       | AGGREGATION      |
  | (Raw events,     |       | SERVICE           |
  |  detailed        |       |                  |
  |  per-interaction |       | Computes:        |
  |  records)        |       | - Mastery scores |
  +--------+---------+       | - Engagement     |
           |                 | - Velocity       |
           |                 | - Risk scores    |
           |                 | - Trends         |
           |                 +--------+---------+
           |                          |
           v                          v
  +------------------+       +------------------+
  | LONG-TERM        |       | ANALYTICS        |
  | STUDENT PROFILE  |       | DATABASE         |
  | (F5)             |       | (Pre-computed    |
  |                  |       |  metrics, time   |
  |                  |       |  series data)    |
  +------------------+       +--------+---------+
                                      |
                                      v
                             +------------------+
                             | DASHBOARD API    |
                             |                  |
                             | REST endpoints   |
                             | for each view &  |
                             | metric           |
                             +--------+---------+
                                      |
                       +--------------+--------------+
                       |              |              |
                       v              v              v
                 +-----------+ +-----------+ +-----------+
                 | Student   | | Teacher   | | Admin     |
                 | Dashboard | | Dashboard | | Dashboard |
                 | (React)   | | (React)   | | (React)   |
                 +-----------+ +-----------+ +-----------+
```

### Real-Time Update Flow

```
REAL-TIME UPDATE MECHANISM
============================

  Student completes a quiz
        |
        v
  +------------------+
  | Quiz Event       |
  | published to     |
  | event bus        |
  +--------+---------+
           |
           +---> Analytics aggregation service recomputes affected metrics
           |
           +---> WebSocket server receives updated metrics
           |
           +---> Connected dashboards receive push update
                      |
                      v
              Dashboard re-renders affected widgets
              (e.g., quiz score chart adds new point,
               mastery score updates)
```

---

## Service Comparison: Frontend Charting

### Chart.js

| Aspect | Details |
|--------|---------|
| **Pros** | Simple API, lightweight (~60KB), good documentation, responsive by default, large community |
| **Cons** | Limited chart types, less customizable than D3, canvas-based (no DOM access to elements) |
| **Best For** | Standard charts (line, bar, pie, radar, doughnut) with minimal customization needs |
| **Bundle Size** | ~60KB gzipped |
| **React Integration** | react-chartjs-2 wrapper |

### Recharts

| Aspect | Details |
|--------|---------|
| **Pros** | Built for React, declarative API, SVG-based (accessible, styleable), composable components |
| **Cons** | Larger bundle, limited animation, fewer chart types than D3, performance degrades with large datasets |
| **Best For** | React applications needing clean, composable charts with good defaults |
| **Bundle Size** | ~100KB gzipped |
| **React Integration** | Native React library |

### D3.js

| Aspect | Details |
|--------|---------|
| **Pros** | Unlimited customization, any visualization imaginable, SVG + Canvas, huge community, industry standard |
| **Cons** | Steep learning curve, verbose, not React-native (needs wrapper), DIY for common patterns |
| **Best For** | Custom/complex visualizations like the mastery radar chart, heat maps, interactive learning path maps |
| **Bundle Size** | ~80KB gzipped (full), tree-shakeable |
| **React Integration** | visx (Airbnb), react-d3-library, or custom hooks |

### Apache ECharts

| Aspect | Details |
|--------|---------|
| **Pros** | Extremely rich chart types, excellent performance, built-in animations, good for dashboards, great heat maps |
| **Cons** | Large bundle, opinionated styling, less React-idiomatic, documentation quality varies |
| **Best For** | Feature-rich dashboards with many chart types, especially heat maps and complex interactions |
| **Bundle Size** | ~300KB gzipped (full), tree-shakeable |
| **React Integration** | echarts-for-react wrapper |

### Recommendation

Use **Recharts** as the primary charting library for standard charts (line, bar, progress, radar) because it integrates cleanly with React and covers 80% of needs with minimal effort. Use **D3.js** (via visx) for the custom visualizations that Recharts cannot handle (the calendar heat map, the interactive learning path visualization, the class mastery heat map). This hybrid approach balances development speed with customization power.

---

## Service Comparison: Analytics Backend

### Custom Aggregations (Application-Level)

| Aspect | Details |
|--------|---------|
| **Approach** | Write aggregation queries directly against the application database (PostgreSQL) |
| **Pros** | No additional infrastructure, full control, no new technology to learn |
| **Cons** | Must build caching, incremental computation, and query optimization manually |
| **Best For** | Early stages, simple metrics, small scale |
| **Scaling** | Pre-compute and cache metrics in a materialized view or summary table, updated on schedule |

### Cube.js (Cube)

| Aspect | Details |
|--------|---------|
| **Approach** | Headless BI / analytics API layer that sits between your database and frontend |
| **Pros** | Pre-aggregation engine (fast queries on large data), semantic layer (define metrics once), caching, multi-database support, REST and GraphQL APIs |
| **Cons** | Additional service to deploy and maintain, learning curve for data modeling, overkill for simple metrics |
| **Best For** | Mid-to-large scale where analytics queries are becoming slow and metrics definitions need to be centralized |
| **Cost** | Open-source (self-hosted) or Cube Cloud (managed, starts free) |

### Apache Superset

| Aspect | Details |
|--------|---------|
| **Approach** | Full BI platform with query engine, visualization, and dashboards |
| **Pros** | Complete BI solution, SQL-based, rich visualizations, role-based access, open-source |
| **Cons** | Heavy infrastructure, separate UI (not embedded in app natively), complex deployment, more suited for internal analytics than student-facing dashboards |
| **Best For** | Admin-level analytics, internal platform monitoring, ad-hoc exploration |
| **Cost** | Free (open-source), significant ops cost |

### Recommendation

Start with **custom aggregations** backed by PostgreSQL materialized views and a background job that recomputes metrics periodically (every 5 minutes for real-time dashboards, hourly for daily summaries). As scale grows, introduce **Cube.js** as the analytics API layer to handle pre-aggregation, caching, and the semantic metric layer. Use **Apache Superset** only for internal platform admin analytics (not student/teacher-facing).

---

## Service Comparison: Real-Time Updates

### WebSocket (Socket.io / native WS)

| Aspect | Details |
|--------|---------|
| **Pros** | True bidirectional real-time, low latency, single persistent connection, wide library support |
| **Cons** | Connection management complexity, scalability requires sticky sessions or Redis pub/sub, more server resources |
| **Best For** | Dashboards that update frequently (every few seconds) during active sessions |
| **Recommendation** | Use for the student dashboard during active study sessions (live mastery updates, streak counter) |

### Server-Sent Events (SSE)

| Aspect | Details |
|--------|---------|
| **Pros** | Simple, HTTP-based, auto-reconnect built in, works through proxies, no special server setup |
| **Cons** | Unidirectional (server to client only), limited concurrent connections in some browsers, no binary data |
| **Best For** | One-way data push: progress updates, alert notifications, processing status |
| **Recommendation** | Use for document processing status updates (F11) and alert notifications |

### Polling (Short/Long)

| Aspect | Details |
|--------|---------|
| **Pros** | Simplest to implement, stateless, works everywhere, no special infrastructure |
| **Cons** | Higher latency, unnecessary network traffic, server load from empty responses |
| **Best For** | Infrequent updates (teacher dashboard refreshes, weekly reports) |
| **Recommendation** | Use for admin dashboards and teacher views that do not require second-by-second updates |

### Recommendation

**Hybrid approach:**
- **WebSocket** for student dashboard during active sessions (real-time mastery, streak, quiz score updates)
- **SSE** for notifications and document processing progress
- **Polling (60-second interval)** for teacher and admin dashboards that aggregate data and do not need instant updates

---

## MCP Servers

| MCP Server | Purpose | How It Helps |
|------------|---------|-------------|
| **SQLite / PostgreSQL MCP** | Database access | Allow AI to query analytics data directly for generating natural-language insights |
| **Memory MCP** | Student memory access | Retrieve student learning history for computing metrics and generating personalized insights |
| **Fetch MCP** | External data | Pull curriculum standard benchmarks, national average data for comparison |
| **Filesystem MCP** | Report generation | Write generated PDF reports to filesystem for download |
| **Brave Search MCP** | Research | Look up context for educational benchmarks, study technique recommendations |

---

## Data Model

### Aggregated Metrics Table

```
StudentMetrics {
  id:                   UUID
  student_id:           UUID (FK -> User)
  class_id:             UUID (FK -> Class)
  topic_id:             UUID (FK -> Topic)
  date:                 Date (one row per day per topic per class)

  // Mastery
  mastery_score:        Float (0-100)
  mastery_delta_7d:     Float (change from 7 days ago)
  mastery_components:   JSON { quiz, ai_assessment, spaced_rep, recency, consistency }

  // Engagement
  sessions_count:       Integer
  total_minutes:        Integer
  questions_answered:   Integer
  questions_correct:    Integer

  // Velocity
  learning_velocity:    Float (mastery points per day)

  // Risk
  risk_score:           Float (0-1)
  risk_factors:         JSON { engagement_drop, mastery_decline, inactivity, shortening, sentiment }

  computed_at:          Timestamp
}
```

### Dashboard Widget Configuration

```
DashboardWidget {
  id:                 UUID
  user_id:            UUID (FK -> User)
  dashboard_type:     Enum (student, teacher, admin, parent)
  widget_type:        String (e.g., "mastery_radar", "quiz_trend", "study_heatmap")
  position:           JSON { row, col, width, height }
  config:             JSON (widget-specific settings: date range, topics, comparison mode)
  is_visible:         Boolean
  created_at:         Timestamp
  updated_at:         Timestamp
}
```

---

## Privacy & Access Control

```
ACCESS CONTROL MATRIX
=======================

Data Point              Student  Teacher  Parent  School Admin  Platform Admin
----------------------  -------  -------  ------  -----------  --------------
Own mastery scores      YES      YES      YES     YES          Aggregated only
Own quiz answers        YES      YES      NO      NO           NO
Chat transcripts        YES      NO       NO      NO           NO
Study time patterns     YES      YES      YES     Aggregated   Aggregated
Class rankings          Opt-in   YES      NO      YES          Aggregated
Other students' data    NO       Own class NO     Own school    All (aggregated)
At-risk alerts          NO       Own class NO     Own school    All
AI insights text        YES      YES      NO      NO           NO
Raw event data          NO       NO       NO      NO           YES
```

- FERPA compliance: student data accessible only to the student, their teachers, and authorized school officials
- COPPA compliance: parental consent required for students under 13; parent view available
- Data minimization: dashboards show aggregated metrics, not raw event logs
- Right to export: student can download all their data as JSON/CSV
- Right to delete: deleting an account removes all analytics data within 30 days

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Dashboard initial load | < 2 seconds |
| Widget data refresh | < 500ms |
| Real-time update latency | < 3 seconds from event to dashboard display |
| Metric recomputation | < 5 minutes from event to updated aggregate |
| PDF report generation | < 10 seconds |
| Weekly email generation (all users) | < 30 minutes |
| Concurrent dashboard users | 5,000+ |
| Historical data retention | 3 years of aggregated metrics, 1 year of raw events |

---

## Open Questions

1. Should students be able to fully customize their dashboard layout (drag widgets, add/remove), or should we provide a fixed layout optimized for learning motivation?
2. How granular should the parent view be? Some parents want detailed control; some students (especially older ones) want privacy. What is the right default?
3. Should leaderboards be global (school-wide) or class-only? Global creates more competition but also more pressure.
4. Should we display "predicted exam score" as a metric? This could be highly motivating or anxiety-inducing.
5. How do we handle the cold start problem -- what does the dashboard show for a new student with no data yet?
6. Should teachers be able to see which students viewed their dashboard this week (engagement with the analytics itself)?
