# Feature 14: Learning Path Recommendations

## Overview

The Learning Path engine is the brain behind EduAGI's personalized learning experience. It analyzes what a student knows, what they do not know, what they need to know next, and how much time they have -- then generates a prioritized, visual roadmap of what to study. This is not a static curriculum sequence. It is a dynamic, adaptive system that recalculates after every interaction, adjusting for the student's pace, knowledge gaps, goals, and available time.

**Priority:** High (P1)
**Status:** Design Phase
**Dependencies:** Student Memory (F5), Assessment Engine (F8), Document Processing (F11), Analytics Dashboard (F12)
**Stakeholders:** Students, Teachers, Curriculum Coordinators

---

## Student Perspective

Marcus opens EduAGI on a Wednesday evening. He has 90 minutes to study. The Learning Path shows him:

1. **"Your Path to AP Biology Exam (May 15)"** -- an interactive roadmap with nodes representing topics. He has completed 68% of the path. Completed nodes are green. Current focus nodes pulse gently. Future nodes are grayed out but visible.

2. **"What to study tonight"** -- a prioritized list:
   - **Kinematics (Priority: HIGH)** -- "You scored 45% on your last quiz. This is a prerequisite for Dynamics, which is coming up. Estimated time: 40 min to move from Developing to Proficient."
   - **Meiosis I stages (Priority: MEDIUM)** -- "You have a quiz on this Friday. Quick review recommended. Estimated time: 20 min."
   - **Ecology food webs (Priority: LOW)** -- "You are already Proficient here, but a spaced review would help retention. Estimated time: 15 min."

3. Marcus drags "Meiosis I stages" to the top of his list because the quiz is Friday. The system accepts the override and adjusts.

4. He clicks "Start" on Kinematics. The AI tutor begins a focused session on exactly the concepts he is weakest on, using content from his teacher's uploaded materials.

After the session, the learning path updates in real time. Kinematics moves from red to yellow. The estimated time to mastery drops from 3 hours to 1.5 hours.

---

## Prerequisite Graph

### Concept

Every subject is a network of topics with dependency relationships. You cannot understand Dynamics without understanding Kinematics. You cannot understand Meiosis without understanding Mitosis. The prerequisite graph encodes these relationships and is the foundation of all learning path recommendations.

```
PREREQUISITE GRAPH EXAMPLE (Biology)
======================================

                    +-------------------+
                    |  Cellular         |
                    |  Structure        |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
    +-------------------+         +-------------------+
    |  Cell Membrane    |         |  Organelles       |
    |  & Transport      |         |                   |
    +--------+----------+         +--------+----------+
             |                             |
             +-------------+---------------+
                           |
                           v
                 +-------------------+
                 |  Cell Division    |
                 |  (Overview)       |
                 +--------+----------+
                          |
              +-----------+------------+
              |                        |
              v                        v
    +-------------------+    +-------------------+
    |  Mitosis          |    |  Cell Cycle       |
    |                   |    |  Regulation       |
    +--------+----------+    +-------------------+
             |
             v
    +-------------------+
    |  Meiosis          |
    +--------+----------+
             |
             +--------------------+
             |                    |
             v                    v
    +-------------------+  +-------------------+
    |  Genetic          |  |  Heredity &       |
    |  Variation        |  |  Mendel's Laws    |
    +-------------------+  +--------+----------+
                                    |
                                    v
                           +-------------------+
                           |  Complex          |
                           |  Inheritance      |
                           |  Patterns         |
                           +-------------------+
```

### Graph Structure

Each node in the prerequisite graph represents a **topic** at a specific granularity level:

```
TOPIC HIERARCHY
================

Subject (e.g., Biology)
  |
  +-- Domain (e.g., Cell Biology)
  |     |
  |     +-- Topic (e.g., Cell Division)
  |     |     |
  |     |     +-- Sub-topic (e.g., Mitosis)
  |     |           |
  |     |           +-- Concept (e.g., Prophase)
  |     |
  |     +-- Topic (e.g., Cell Membrane & Transport)
  |           |
  |           +-- Sub-topic (e.g., Osmosis)
  |           +-- Sub-topic (e.g., Active Transport)
  |
  +-- Domain (e.g., Genetics)
        |
        +-- Topic (e.g., Heredity)
        ...
```

### Edge Types

| Edge Type | Meaning | Example |
|-----------|---------|---------|
| **REQUIRES** | Must understand A before B | Mitosis REQUIRES Cell Division Overview |
| **STRONGLY_RECOMMENDS** | Understanding A significantly helps with B | Cell Membrane Transport STRONGLY_RECOMMENDS Cellular Structure |
| **WEAKLY_RECOMMENDS** | Understanding A provides useful context for B | Ecology WEAKLY_RECOMMENDS Evolution |
| **COMPLEMENTS** | A and B are best learned together | Meiosis COMPLEMENTS Genetic Variation |

### Graph Construction

```
PREREQUISITE GRAPH CONSTRUCTION
=================================

  +-------------------+
  | SOURCE 1:         |
  | Curriculum        |
  | Standards         |  (Common Core, AP, IB standards encode
  | (structured)      |   topic sequences and prerequisites)
  +--------+----------+
           |
           +----+
                |
                v
  +-------------------+     +-------------------+
  | SOURCE 2:         |     | GRAPH BUILDER     |
  | Teacher Input     |---->|                   |
  | (manual edges)    |     | Merges all sources|
  +-------------------+     | Resolves conflicts|
                            | Validates (no     |
  +-------------------+     |  cycles, all nodes|
  | SOURCE 3:         |---->|  reachable)       |
  | AI Analysis       |     |                   |
  | (analyze uploaded  |     +--------+----------+
  |  content to infer |              |
  |  prerequisites)   |              v
  +-------------------+     +-------------------+
                            | VALIDATED         |
  +-------------------+     | PREREQUISITE      |
  | SOURCE 4:         |---->| GRAPH             |
  | Student Data      |     |                   |
  | (empirical: which |     | Stored in graph   |
  |  topic orderings  |     | database          |
  |  lead to better   |     +-------------------+
  |  outcomes)        |
  +-------------------+
```

**Source 1 - Curriculum Standards:** Parse structured curriculum frameworks (Common Core, AP course descriptions, IB syllabi) which already encode topic sequences. These form the backbone of the graph.

**Source 2 - Teacher Input:** Teachers can manually add, remove, or adjust prerequisite edges in the graph editor. Teachers know their students and curriculum better than any algorithm.

**Source 3 - AI Analysis:** Analyze uploaded curriculum content (from F11) to infer prerequisite relationships. When a chapter on Meiosis begins with "Recall from Chapter 5 that during mitosis...", the AI detects that Mitosis is a prerequisite for Meiosis.

**Source 4 - Empirical Student Data:** Over time, analyze which topic orderings lead to better learning outcomes across the student population. If students who study Topic A before Topic B perform 30% better on Topic B assessments, strengthen the A->B prerequisite edge. This is a feedback loop that improves the graph over time.

---

## Gap Analysis

### What the Student Doesn't Know That They Should

```
GAP ANALYSIS ALGORITHM
========================

  Input:
  - Student's current mastery scores per topic (from F5/F12)
  - Student's enrolled classes and their curriculum
  - Prerequisite graph
  - Student's goals (if set)

  Process:

  1. Identify TARGET TOPICS:
     - All topics in the student's enrolled curriculum
     - All topics required for the student's goals
     - All prerequisites of target topics (recursively)

  2. For each target topic T:
     gap(T) = max(0, required_mastery(T) - current_mastery(T))

     Where required_mastery(T) depends on context:
     - For a prerequisite of an upcoming topic: 70% (must be "Proficient")
     - For a goal topic: 80% (must be solidly "Proficient" or "Mastered")
     - For a current curriculum topic: 60% (must be "Developing" or above)

  3. Sort topics by gap size (descending)

  4. Filter: only include topics where gap > 10 points
     (smaller gaps are not actionable)

  Output:
  - Ordered list of knowledge gaps with gap size, current mastery, and required mastery
```

### Gap Visualization

```
GAP ANALYSIS VIEW
==================

+------------------------------------------------------------------+
|  Your Knowledge Gaps                     AP Biology Exam Goal     |
+------------------------------------------------------------------+
|                                                                    |
|  Topic              Current  Required  Gap    Status              |
|  ---------------------------------------------------------------- |
|  Kinematics         45%      70%       25     [=====     ] LARGE |
|  Meiosis I          52%      70%       18     [====      ] MEDIUM|
|  Thermodynamics     55%      70%       15     [===       ] MEDIUM|
|  Wave Mechanics     60%      70%       10     [==        ] SMALL |
|  Protein Synthesis  62%      70%       8      [=         ] MINOR |
|  ---------------------------------------------------------------- |
|                                                                    |
|  Gaps found: 5 topics need attention                              |
|  Estimated total study time to close all gaps: 8.5 hours         |
|                                                                    |
+------------------------------------------------------------------+
```

---

## Priority Scoring Algorithm

### Core Formula

```
PRIORITY SCORING
=================

For each topic T with a knowledge gap:

  priority(T) = (importance(T) * gap_size(T)) - mastery(T) + urgency(T) + prerequisite_boost(T)

  Where:

  importance(T) = weighted sum of:
    - curriculum_weight(T)     * 0.30   // How much of the curriculum does T represent?
    - exam_weight(T)           * 0.25   // How heavily is T tested on upcoming exams?
    - prerequisite_count(T)    * 0.20   // How many other topics depend on T?
    - teacher_emphasis(T)      * 0.15   // Has the teacher flagged T as important?
    - standard_alignment(T)    * 0.10   // How central is T to curriculum standards?

  gap_size(T) = required_mastery(T) - current_mastery(T)
    // Normalized to 0-1 scale

  mastery(T) = current_mastery(T)
    // Normalized to 0-1 scale (higher mastery = lower priority, the subtraction)

  urgency(T) =
    if T has an assessment due within 7 days: +0.3
    if T has an assessment due within 3 days: +0.5
    if T is a prerequisite for a topic being studied NOW: +0.4
    else: 0

  prerequisite_boost(T) =
    // Topics that are prerequisites for many other gap topics get a boost
    // because closing this gap unlocks progress on other gaps
    count(downstream_gap_topics(T)) * 0.1

  Final priority score normalized to 0-100 scale.
```

### Priority Levels

| Score Range | Label | Color | Recommendation |
|-------------|-------|-------|---------------|
| 80-100 | CRITICAL | Red | Study this immediately. Major gap blocking progress. |
| 60-79 | HIGH | Orange | Study this soon. Significant gap or upcoming deadline. |
| 40-59 | MEDIUM | Yellow | Study this within the week. Notable gap. |
| 20-39 | LOW | Blue | Review when time allows. Small gap or not urgent. |
| 0-19 | MAINTENANCE | Gray | Optional review for retention. Mastery is adequate. |

### Worked Example

```
WORKED EXAMPLE: Marcus's Priority Scores
==========================================

Topic: Kinematics
  importance   = (0.15 * 0.30) + (0.20 * 0.25) + (3 deps * 0.05 * 0.20) + (0 * 0.15) + (0.10 * 0.10)
               = 0.045 + 0.05 + 0.03 + 0 + 0.01 = 0.135 (normalized to ~0.68)
  gap_size     = (70% - 45%) / 100 = 0.25
  mastery      = 45% / 100 = 0.45
  urgency      = 0.4 (prerequisite for Dynamics, which is being studied)
  prereq_boost = 2 downstream gaps * 0.1 = 0.2

  priority = (0.68 * 0.25) - 0.45 + 0.4 + 0.2
           = 0.17 - 0.45 + 0.4 + 0.2
           = 0.32 (raw)
  Normalized: 82 -> CRITICAL

Topic: Ecology Food Webs
  importance   = 0.55 (moderately important)
  gap_size     = (70% - 68%) / 100 = 0.02
  mastery      = 68% / 100 = 0.68
  urgency      = 0 (no upcoming assessment)
  prereq_boost = 0 (no downstream gaps)

  priority = (0.55 * 0.02) - 0.68 + 0 + 0
           = 0.011 - 0.68
           = -0.669 (raw, clamped to 0)
  Normalized: 5 -> MAINTENANCE
```

---

## Goal-Based Path Generation

### Goal Types

| Goal Type | Example | Path Strategy |
|-----------|---------|--------------|
| **Exam Preparation** | "Pass AP Biology exam (May 15)" | Map all exam topics, identify gaps, create time-bound study plan |
| **Course Completion** | "Complete Algebra II by end of semester" | Follow curriculum sequence, prioritize lagging topics |
| **Topic Mastery** | "Master Calculus derivatives" | Deep-dive path with all prerequisites and practice |
| **Skill Building** | "Improve scientific writing" | Cross-topic path focusing on a skill applied across subjects |
| **Remediation** | "Catch up on missed material from last semester" | Gap-focused path targeting specific deficiencies |

### Goal-Based Path Generation Flow

```
GOAL-BASED PATH GENERATION
=============================

  +-------------------+
  | Student sets goal |
  | "Pass AP Bio exam |
  |  by May 15"       |
  +--------+----------+
           |
           v
  +-------------------+
  | GOAL DECOMPOSITION|
  |                   |
  | 1. Map goal to    |
  |    required topics|
  |    (from exam     |
  |    blueprint)     |
  |                   |
  | 2. Identify all   |
  |    prerequisites  |
  |    recursively    |
  |                   |
  | 3. Result:        |
  |    47 topics      |
  |    needed for     |
  |    this goal      |
  +--------+----------+
           |
           v
  +-------------------+
  | GAP ANALYSIS      |
  |                   |
  | 47 topics needed  |
  | 31 already mastered|
  | 16 need work      |
  | 5 are CRITICAL    |
  +--------+----------+
           |
           v
  +-------------------+
  | TIME BUDGET       |
  |                   |
  | Days until exam:  |
  |   98              |
  | Available study   |
  |   time/week: ~7hr |
  |   (estimated from |
  |   past behavior)  |
  | Total time budget:|
  |   ~98 hours       |
  +--------+----------+
           |
           v
  +-------------------+
  | PATH OPTIMIZATION |
  |                   |
  | Order topics by:  |
  | 1. Prerequisites  |
  |    first          |
  | 2. Then by        |
  |    priority score |
  | 3. Respect time   |
  |    constraints    |
  | 4. Include review |
  |    sessions       |
  +--------+----------+
           |
           v
  +-------------------+
  | GENERATED PATH    |
  |                   |
  | Week 1-2:         |
  |   Kinematics      |
  |   (prerequisite,  |
  |    largest gap)    |
  | Week 3-4:         |
  |   Meiosis +       |
  |   Genetics        |
  | Week 5-8:         |
  |   Remaining gaps  |
  | Week 9-14:        |
  |   Review cycle    |
  |   + practice exams|
  +-------------------+
```

### Time Budget Calculation

```
TIME BUDGET ALGORITHM
======================

Inputs:
- goal_deadline: Date
- student_avg_sessions_per_week: Float (from historical data)
- student_avg_session_duration: Float (from historical data)
- student_effective_study_ratio: Float (active learning time / total session time)

Calculation:
  days_remaining = goal_deadline - today
  weeks_remaining = days_remaining / 7
  total_study_hours = weeks_remaining * sessions_per_week * avg_duration * effective_ratio

  // Estimate time needed per topic:
  For each gap topic T:
    estimated_hours(T) = base_time(difficulty(T)) * (gap_size(T) / 25)
    // base_time: Easy=1h, Medium=2h, Hard=3h per 25 mastery points of gap

  total_needed_hours = sum(estimated_hours(T) for all gap topics)

  // Check feasibility:
  if total_needed_hours <= total_study_hours * 0.8:
    status = "ON TRACK" (20% buffer for review and unexpected)
  elif total_needed_hours <= total_study_hours:
    status = "TIGHT" (little buffer, recommend more study time)
  else:
    status = "AT RISK" (not enough time at current pace)
    // Suggest: increase study sessions, extend deadline, or narrow focus
```

---

## Time-Aware Recommendations

### Adapting to Available Time

When a student starts a study session, the system asks (or infers) how much time they have:

```
TIME-AWARE RECOMMENDATION ENGINE
===================================

  Student indicates: "I have 30 minutes"
        |
        v
  +-------------------+
  | Filter priority   |
  | list to topics    |
  | that fit within   |
  | 30 minutes        |
  +--------+----------+
           |
           v
  +-------------------+
  | OPTION A:         |     +-------------------+
  | Single topic      |     | OPTION B:         |
  | deep dive         |     | Multi-topic       |
  | (30 min on        |     | review            |
  |  Kinematics)      |     | (10 min each on   |
  |                   |     |  3 topics)         |
  | Best when: large  |     |                   |
  | gap, needs focus  |     | Best when: small  |
  +-------------------+     | gaps, spaced      |
                            | review needed     |
                            +-------------------+
           |                          |
           v                          v
  +-------------------------------------------+
  | Present both options to student.           |
  | Default to AI recommendation, but student |
  | can choose.                                |
  +-------------------------------------------+
```

### Session Duration Optimization

Based on the student's historical performance data:
- If accuracy drops after 35 minutes, recommend sessions of max 30 minutes with 5-minute breaks
- If the student is most effective between 7-9 PM, weight recommendations toward evening study
- If the student consistently skips long sessions, recommend shorter, more frequent sessions

### Weekly Schedule View

```
WEEKLY STUDY SCHEDULE (AI-Generated)
======================================

+------------------------------------------------------------------+
|  Your Study Plan This Week         Based on: AP Bio Exam Goal    |
+------------------------------------------------------------------+
|                                                                    |
|  Monday:     Kinematics - Force Diagrams (40 min)                |
|              Why: Critical gap, prerequisite for Thursday's topic |
|                                                                    |
|  Tuesday:    Meiosis I Review (20 min)                           |
|              Why: Quiz on Friday                                  |
|                                                                    |
|  Wednesday:  Kinematics - Newton's Laws (35 min)                 |
|              Why: Continues Monday's focus                        |
|                                                                    |
|  Thursday:   Dynamics Introduction (30 min)                      |
|              Why: New topic, unlocked by Kinematics progress     |
|                                                                    |
|  Friday:     Meiosis I Quiz + Light Review (25 min)              |
|              Why: Assessment day + retention boost                |
|                                                                    |
|  Saturday:   Rest day (optional: Ecology review, 15 min)         |
|                                                                    |
|  Sunday:     Weekly review session (30 min)                      |
|              Why: Spaced repetition for all topics studied        |
|                                                                    |
|  Total estimated time: 3 hours 15 minutes                        |
|  [Adjust Schedule]  [Sync to Calendar]  [Start Monday's Session] |
|                                                                    |
+------------------------------------------------------------------+
```

---

## Visual Learning Path

### Interactive Roadmap

```
VISUAL LEARNING PATH (Student View)
=====================================

The learning path is displayed as an interactive node-and-edge graph,
similar to a skill tree in a video game or a metro map.

+------------------------------------------------------------------+
|  AP Biology Exam Path                    Progress: 68%           |
|                                          Est. completion: Apr 28 |
+------------------------------------------------------------------+
|                                                                    |
|    [Cellular Structure]                                           |
|    (MASTERED - green)                                             |
|         |                                                         |
|    -----+-----                                                    |
|    |         |                                                    |
|    v         v                                                    |
|  [Cell      [Organelles]                                         |
|  Membrane]  (MASTERED)                                            |
|  (MASTERED)                                                       |
|    |         |                                                    |
|    +----+----+                                                    |
|         |                                                         |
|         v                                                         |
|    [Cell Division]                                                |
|    (PROFICIENT - green)                                           |
|         |                                                         |
|    -----+-----                                                    |
|    |         |                                                    |
|    v         v                                                    |
|  [Mitosis]  [Cell Cycle                                           |
|  (PROFIC.)   Regulation]                                          |
|    |        (PROFICIENT)                                          |
|    v                                                              |
|  [MEIOSIS]  <-- CURRENT FOCUS (pulsing, yellow)                  |
|  (DEVELOPING - 52%)                                               |
|    |                                                              |
|    +----+----+                                                    |
|    |         |                                                    |
|    v         v                                                    |
|  [Genetic   [Heredity]  <-- LOCKED (gray, prerequisites not met) |
|  Variation]  (NOT STARTED)                                        |
|  (NOT STARTED)                                                    |
|         |                                                         |
|         v                                                         |
|    [Complex Inheritance]                                          |
|    (LOCKED)                                                       |
|                                                                    |
|  [Legend: Green=Mastered, Yellow=In Progress, Gray=Locked]        |
|                                                                    |
+------------------------------------------------------------------+
```

### Node States

| State | Visual | Meaning |
|-------|--------|---------|
| LOCKED | Gray, semi-transparent | Prerequisites not yet met |
| NOT_STARTED | Gray, solid | Prerequisites met but not yet studied |
| DEVELOPING | Yellow | Mastery 21-60%, actively being learned |
| PROFICIENT | Light green | Mastery 61-80%, solid understanding |
| MASTERED | Dark green, checkmark | Mastery 81-100%, well understood |
| CURRENT_FOCUS | Pulsing outline | Recommended to study next |
| REVIEW_DUE | Orange dot | Mastered but spaced repetition review is due |

### Interaction

- **Click a node**: See topic details (current mastery, estimated time to next level, last studied, related content)
- **Click "Start"**: Begin an AI tutoring session focused on that topic
- **Zoom in/out**: See more or less detail (zoom in to see sub-topics within a topic)
- **Pan**: Navigate across the full graph (for large curricula)
- **Filter**: Show only topics for a specific domain, or only topics with gaps
- **Timeline view toggle**: Switch from graph view to chronological timeline view

---

## Sub-Features

### Drag-and-Drop Path Customization

- Students can reorder their priority list by dragging topics up or down
- System validates changes: warns if moving a topic ahead of its prerequisites
- Teacher can lock certain topics in position ("You must study Mitosis before Meiosis, no skipping")
- Customizations persist across sessions
- "Reset to AI recommended" button available

### Milestone Celebrations

```
MILESTONE CELEBRATION SYSTEM
==============================

  Student completes a topic (reaches MASTERED status)
        |
        v
  +-------------------+
  | Celebration       |
  | triggered         |
  +--------+----------+
           |
           +---> Visual celebration (confetti, glow effect on node)
           |
           +---> Achievement badge awarded
           |
           +---> Progress notification ("You mastered Mitosis!
           |     3 topics to go until your Genetics milestone.")
           |
           +---> Streak extended (if applicable)
           |
           +---> Unlock notification ("Meiosis is now available
                 to study!")
```

**Milestone Types:**
- Topic mastery (complete a single topic)
- Domain mastery (complete all topics in a domain, e.g., all of Cell Biology)
- Goal milestone (reach a checkpoint on the goal path, e.g., "50% ready for AP exam")
- Streak milestone (7 days, 14 days, 30 days, 100 days)
- Volume milestones (100 questions answered, 1000 questions answered)
- Time milestones (10 hours studied, 50 hours studied)

**Celebration principles:**
- Celebrate progress, not just perfection
- Never compare to other students in celebrations (avoid discouragement)
- Frequency: not too rare (loses motivation) and not too frequent (loses meaning)
- Customizable: students can reduce or disable celebration animations

### Skip-Ahead Testing

```
SKIP-AHEAD TESTING FLOW
=========================

  +-------------------+
  | Student clicks    |
  | "Test Out" on a   |
  | locked topic      |
  +--------+----------+
           |
           v
  +-------------------+
  | Challenge         |
  | Assessment        |
  |                   |
  | - 10-15 questions |
  | - Must score 80%+ |
  | - Covers all key  |
  |   concepts        |
  | - One attempt     |
  |   per 7 days      |
  +--------+----------+
           |
           +--------- PASS (>= 80%) --------+
           |                                 |
           v                                 v
  +-------------------+            +-------------------+
  | FAIL              |            | PASS              |
  |                   |            |                   |
  | "You scored 65%.  |            | "Congratulations! |
  | You need to       |            |  You tested out   |
  | strengthen these  |            |  of Mitosis.      |
  | areas:            |            |  Meiosis is now   |
  | - Prophase        |            |  unlocked."       |
  | - Spindle fibers" |            |                   |
  |                   |            | Topic set to      |
  | Try again in 7    |            | MASTERED (85%)    |
  | days, or study    |            |                   |
  | the topic first.  |            | Downstream topics |
  +-------------------+            | unlocked          |
                                   +-------------------+
```

- Available for any topic where the student believes they already know the material
- Prevents students from having to study topics they learned elsewhere (e.g., in another class, through self-study)
- Rate-limited: one attempt per topic per 7 days (prevents brute-force guessing)
- Teacher can disable skip-ahead for specific topics
- Assessment is dynamically generated and harder than normal quizzes (higher bar for skipping)

### Daily "What to Study" Notification

```
DAILY NOTIFICATION FLOW
=========================

  +-------------------+
  | Morning (or       |
  | student-configured|
  | time)             |
  +--------+----------+
           |
           v
  +-------------------+
  | Compute today's   |
  | recommendation    |
  | based on:         |
  | - Priority scores |
  | - Upcoming assess.|
  | - Spaced rep due  |
  | - Day of week     |
  |   (lighter on     |
  |    weekends?)     |
  +--------+----------+
           |
           v
  +-------------------+
  | Push notification |
  | / Email           |
  |                   |
  | "Good morning,    |
  | Marcus! Today's   |
  | focus: Kinematics |
  | (40 min). You     |
  | have a quiz on    |
  | Meiosis Friday -  |
  | a quick review    |
  | tonight would     |
  | help. Tap to      |
  | start."           |
  +-------------------+
```

- Channels: push notification (mobile), email, in-app banner
- Student configures: preferred notification time, frequency (daily, weekdays only, manual)
- Smart quiet hours: no notifications during school hours or sleeping hours
- Unsubscribe: students can turn off notifications at any time
- Engagement-aware: if a student ignores notifications for 7+ days, reduce frequency to avoid annoyance, then try a re-engagement message

### Smart Scheduling (Calendar Integration)

```
SMART SCHEDULING
=================

  +-------------------+     +-------------------+
  | Student's         |     | EduAGI Learning   |
  | Calendar          |<--->| Path Engine       |
  | (Google, Apple,   |     |                   |
  |  Outlook)         |     | Reads: busy times |
  +-------------------+     | Writes: study     |
                            |   session blocks  |
                            +-------------------+

  Example output:

  Student's actual calendar:
  - Mon 3-5pm: Basketball practice
  - Tue 4-6pm: Music lesson
  - Wed: Free after 3pm
  - Thu 3-5pm: Basketball practice
  - Fri: Free after 3pm

  AI-suggested study blocks:
  - Mon 7-7:40pm: Kinematics (after dinner, post-practice)
  - Tue 7-7:20pm: Meiosis review (short session on busy day)
  - Wed 3:30-4:15pm: Kinematics continued (free afternoon)
  - Thu 7-7:35pm: Dynamics intro (after practice)
  - Fri 3:30-3:55pm: Meiosis quiz prep (before the weekend)

  Total: 2h 50min across 5 days (within the 3h/week average)
```

- Read-only calendar access to find free time slots
- Suggest study blocks that fit the student's actual schedule
- Respect student preferences: "I do not study after 9 PM" or "I prefer morning study on weekends"
- Create calendar events for study sessions (optional, student must confirm)
- Adapt when schedule changes (cancelled practice = suggest extra study time, or rest)

### Difficulty Prediction for Upcoming Topics

For each topic the student has not yet started:
- Predict difficulty based on: the student's mastery of prerequisites, the topic's inherent difficulty rating, and how similar students performed
- Display: "This topic is likely MODERATE difficulty for you because your Mitosis mastery (78%) provides a good foundation, but Meiosis has additional complexity around crossing over."
- Use this to set expectations and allocate appropriate time

### Estimated Time to Mastery

```
TIME ESTIMATION MODEL
======================

For each topic T:

  estimated_hours_to_mastery(T) =
    base_time(difficulty(T), level_target) *
    student_learning_rate_factor(S) *
    prerequisite_readiness_factor(S, T)

  Where:
  - base_time: average hours needed by all students at this difficulty
    - Easy topic, to Proficient: 1.0 hours
    - Medium topic, to Proficient: 2.5 hours
    - Hard topic, to Proficient: 4.0 hours

  - student_learning_rate_factor: how fast this student learns relative
    to average (computed from historical data)
    - Fast learner: 0.7x
    - Average: 1.0x
    - Slower learner: 1.4x

  - prerequisite_readiness_factor: how well-prepared the student is
    - All prereqs mastered: 0.8x (well-prepared, faster)
    - All prereqs proficient: 1.0x (baseline)
    - Some prereqs developing: 1.3x (under-prepared, slower)

  Example:
  Meiosis (Medium difficulty) for Marcus:
  base_time = 2.5 hours
  Marcus is an average learner: * 1.0
  Mitosis is Proficient (78%): * 1.0
  = 2.5 hours estimated to reach Proficient in Meiosis
```

Display on the learning path node: "Estimated time: ~2.5 hours (5 sessions)"

### Alternative Learning Paths

Not every student needs to follow the same route through a subject. The system can identify multiple valid orderings:

```
ALTERNATIVE PATH EXAMPLE
==========================

Standard path to Genetics:
  Cellular Structure -> Cell Division -> Mitosis -> Meiosis -> Genetics

Alternative path (for a student strong in chemistry):
  Molecular Biology -> DNA Structure -> Gene Expression -> Genetics
  (Skip the cell biology route, come at Genetics from the molecular side)

Alternative path (for a visual learner):
  Same topics, but prioritize topics with strong visual content
  (diagrams, videos) in the teacher's uploaded materials
```

- The system identifies when multiple valid paths exist (multiple valid topological orderings of the prerequisite graph)
- Students can view alternatives and switch paths
- AI explains the trade-offs: "Path A is shorter but assumes you can learn Genetics without deep Meiosis knowledge. Path B is more thorough but takes 2 weeks longer."
- Teacher can restrict to a single path for their class if desired

### Peer Recommendations

- Anonymous, aggregated: "Students with similar profiles who focused on Kinematics early performed 23% better on the Physics final"
- Not identifying specific students (privacy)
- Based on collaborative filtering: find students with similar mastery profiles and see what study order worked best for them
- Confidence threshold: only show peer recommendations when the sample size is large enough to be meaningful (n > 50 similar students)
- Teacher can disable peer recommendations for their class

---

## Service Comparison: Graph Database

### Neo4j

| Aspect | Details |
|--------|---------|
| **Approach** | Native graph database with Cypher query language |
| **Pros** | Purpose-built for graphs, excellent traversal performance, rich query language (Cypher), mature ecosystem, built-in visualization tools, ACID compliant |
| **Cons** | Additional infrastructure to deploy and maintain, memory-intensive for large graphs, licensing costs for enterprise features, steep learning curve for Cypher |
| **Best For** | Large, complex prerequisite graphs with frequent traversal queries (find all prerequisites, find shortest path, detect cycles) |
| **Cost** | Community edition: free. Enterprise: ~$60k/year |
| **Scalability** | Single-machine performance is excellent (millions of nodes). Clustering available in enterprise. |

### Custom Graph in PostgreSQL

| Aspect | Details |
|--------|---------|
| **Approach** | Store nodes and edges in relational tables, use recursive CTEs or pg_graphql extension for traversal |
| **Pros** | No new infrastructure (reuse existing PostgreSQL), simpler ops, ACID, familiar SQL, joins with other data |
| **Cons** | Recursive CTEs become slow on deep graphs (>10 levels), no native graph algorithms (shortest path, centrality), less expressive for complex graph queries |
| **Best For** | Small-to-medium graphs (< 10,000 nodes), infrequent deep traversals, tight budget |
| **Cost** | Free (part of existing database) |
| **Scalability** | Good for thousands of nodes. Degrades on deep recursive queries. |

### In-Memory Graph Library (e.g., graphlib, networkx)

| Aspect | Details |
|--------|---------|
| **Approach** | Load the prerequisite graph into memory in the application layer, use a graph library for operations |
| **Pros** | Fastest traversal (in-memory), rich algorithms (topological sort, shortest path, cycle detection), no external DB |
| **Cons** | Not persistent (must load from DB on startup), memory limited, not shared across instances without synchronization |
| **Best For** | Computation-heavy operations (path optimization, alternative path generation) on moderately sized graphs |
| **Cost** | Free |
| **Scalability** | Limited by application memory. Fine for per-school graphs (thousands of nodes). |

### Recommendation

Use a **hybrid approach**:
1. **PostgreSQL** as the persistent store for the prerequisite graph (nodes table, edges table). This keeps ops simple and allows joins with the rest of the data model.
2. **In-memory graph library** (Python: NetworkX; Node.js: graphlib) loaded on application startup for computation-heavy operations like topological sorting, path finding, cycle detection, and alternative path generation. Refresh from PostgreSQL periodically or on change events.
3. **Neo4j** is reserved as a future upgrade path if the graph grows very large (multi-school, cross-curriculum) or if complex graph analytics become a core product feature.

---

## Service Comparison: Recommendation Engine

### Custom Algorithm (Priority Scoring + Prerequisite Ordering)

| Aspect | Details |
|--------|---------|
| **Approach** | Implement the priority scoring algorithm described above, combined with topological sorting of the prerequisite graph |
| **Pros** | Fully transparent, explainable, tunable, no black box, domain-specific (education-focused) |
| **Cons** | Requires manual feature engineering, may miss non-obvious patterns, significant development effort |
| **Best For** | Educational recommendations where explainability matters (students and teachers need to understand WHY a topic is recommended) |
| **Recommendation** | USE THIS as the primary recommendation engine. Education requires explainable AI. |

### Collaborative Filtering

| Aspect | Details |
|--------|---------|
| **Approach** | "Students who studied X in this order also studied Y" (like Netflix/Amazon recommendations) |
| **Pros** | Discovers non-obvious patterns, improves with more data, captures what works empirically |
| **Cons** | Cold start problem (needs large dataset), black box (hard to explain), can reinforce biases, requires significant data infrastructure |
| **Best For** | Supplementary recommendations ("students like you also found it helpful to..."), not primary path generation |
| **Recommendation** | USE THIS as a secondary signal. Feed collaborative filtering insights into the "peer recommendations" sub-feature, but do not let it override the primary algorithm. |

### Content-Based Filtering

| Aspect | Details |
|--------|---------|
| **Approach** | Recommend topics based on similarity to what the student has engaged with positively before |
| **Pros** | Works with limited user data, no cold start if content metadata is rich |
| **Cons** | Filter bubble (keeps recommending similar things), does not push students to study weak areas |
| **Best For** | NOT RECOMMENDED as primary. Education requires studying what you are BAD at, not what you like. However, useful for choosing between equally-prioritized topics (prefer the style the student engages with more). |

### Recommendation

**Custom algorithm as primary** (the priority scoring system described above). It is explainable, domain-appropriate, and puts educational outcomes first. **Collaborative filtering as secondary** for peer recommendations and tie-breaking. **Content-based filtering** only for presentation preferences (e.g., if two topics have equal priority, recommend the one with content in the student's preferred format).

---

## Notification Service

### Notification Types

| Type | Channel | Trigger | Example |
|------|---------|---------|---------|
| Daily study reminder | Push / Email | Scheduled (student-configured time) | "Good morning! Today's focus: Kinematics (40 min)" |
| Milestone celebration | Push / In-app | Topic mastered | "You mastered Mitosis! Meiosis is now unlocked." |
| Assessment reminder | Push / Email | 24h before due date | "Quiz on Meiosis I due tomorrow at 11:59 PM" |
| Path update | In-app | Priority recalculation | "Your learning path updated. New focus: Dynamics." |
| Goal progress | Email (weekly) | Scheduled (Sunday) | "You're 68% of the way to your AP Bio goal. On track!" |
| Re-engagement | Push / Email | 5+ days inactive | "We miss you! Quick 15-min review to keep your streak?" |
| Skip-ahead available | In-app | Cooldown expired | "You can retry the Mitosis skip-ahead test now." |

### Notification Preferences

- Per-channel toggle: push on/off, email on/off, in-app always on
- Quiet hours: no notifications during specified hours
- Frequency cap: maximum N notifications per day
- Per-type toggle: can disable specific notification types
- Digest mode: batch all notifications into a daily or weekly summary email

### Service Options

| Service | Pros | Cons |
|---------|------|------|
| **Firebase Cloud Messaging** | Free, cross-platform (iOS, Android, web), reliable | Google dependency, limited customization |
| **OneSignal** | Rich segmentation, A/B testing, analytics, generous free tier | External dependency, data leaves platform |
| **Custom (WebSocket + email service)** | Full control, no external dependency, privacy | Must build and maintain, scaling complexity |
| **Amazon SNS + SES** | Scalable, AWS ecosystem, multi-channel | AWS lock-in, complex setup, cost at scale |

**Recommendation:** **Firebase Cloud Messaging** for push notifications (free, reliable, cross-platform) combined with **Amazon SES** or **SendGrid** for email. In-app notifications via the existing WebSocket connection (shared with the analytics dashboard real-time updates).

---

## Connections to Other Features

```
FEATURE CONNECTIONS
====================

  +-------------------+
  | F8: Assessment    |<---- Assessment results feed mastery scores
  | Engine            |      and trigger path recalculation
  +-------------------+
           |
           v
  +-------------------+     +-------------------+
  | F5: Student       |---->| F14: Learning     |
  | Memory System     |     | Path              |
  |                   |     | (THIS FEATURE)    |
  | Provides:         |     |                   |
  | - Mastery scores  |     | Consumes all      |
  | - Session history |     | student data to   |
  | - Learning rate   |     | generate paths    |
  | - Preferences     |     +--------+----------+
  +-------------------+              |
                                     |
  +-------------------+              +---> Recommendations displayed in
  | F11: Document     |              |     Student Dashboard (F12)
  | Processing        |              |
  |                   |              +---> "What to study" feeds into
  | Provides:         |              |     AI Tutoring Session (F1)
  | - Topic inventory |              |
  | - Curriculum map  |              +---> Teacher Dashboard (F13) shows
  | - Content per     |              |     path progress per student
  |   topic           |              |
  +-------------------+              +---> Notifications sent via
                                           platform notification system
  +-------------------+
  | F12: Analytics    |<---- Learning path progress and velocity
  | Dashboard         |      data feeds into analytics
  +-------------------+
```

**Assessment Engine (F8):** Every quiz and assessment result triggers a mastery score update, which in turn triggers a learning path recalculation. The path engine also tells the assessment engine which topics to test next (adaptive assessment focus).

**Student Memory (F5):** The foundation. Mastery scores, learning velocity, session history, and student preferences all come from the memory system. The learning path is essentially a projection of the student's memory forward in time.

**Document Processing (F11):** Provides the topic inventory (what topics exist in the curriculum), content availability per topic (which topics have rich content vs. sparse), and curriculum standard mappings that feed into the prerequisite graph.

**Analytics Dashboard (F12):** Displays learning path progress, goal tracking, and velocity metrics. The visual learning path itself may be embedded in the student's analytics dashboard.

**Teacher Dashboard (F13):** Teachers see each student's learning path progress and can intervene (lock topics, adjust priorities, assign specific content).

**AI Tutoring System (F1):** When a student starts a session via "Start" on a learning path node, the tutoring system receives the topic context and focuses the session accordingly.

---

## Data Model

### Topic Node

```
Topic {
  id:                     UUID
  name:                   String
  description:            Text
  subject_id:             UUID (FK -> Subject)
  domain_id:              UUID (FK -> Domain)
  parent_topic_id:        UUID? (FK -> Topic, for sub-topics)

  // Classification
  difficulty_level:       Enum (easy, medium, hard)
  estimated_base_hours:   Float (average hours to mastery)
  bloom_taxonomy_level:   Enum (remember, understand, apply, analyze, evaluate, create)
  grade_level_range:      IntRange (e.g., 9-12)

  // Curriculum mapping
  curriculum_standard_ids: UUID[] (FK -> CurriculumStandard)

  // Content
  content_document_ids:   UUID[] (FK -> Document, from F11)
  content_richness_score: Float (0-5, how much quality content exists)

  created_at:             Timestamp
  updated_at:             Timestamp
}
```

### Prerequisite Edge

```
PrerequisiteEdge {
  id:                UUID
  source_topic_id:   UUID (FK -> Topic, the prerequisite)
  target_topic_id:   UUID (FK -> Topic, the dependent topic)
  edge_type:         Enum (requires, strongly_recommends, weakly_recommends, complements)
  strength:          Float (0-1, how important is this prerequisite)
  source_origin:     Enum (curriculum_standard, teacher_input, ai_inferred, empirical_data)
  confidence:        Float (0-1, how confident are we in this edge)
  created_by:        UUID? (FK -> User, if teacher-created)
  created_at:        Timestamp
}
```

### Student Learning Path

```
StudentLearningPath {
  id:                 UUID
  student_id:         UUID (FK -> User)
  goal_id:            UUID? (FK -> LearningGoal)
  class_id:           UUID? (FK -> Class)

  // Computed path
  ordered_topic_ids:  UUID[] (prioritized order of topics to study)
  last_computed_at:   Timestamp

  // Progress
  topics_mastered:    Integer
  topics_total:       Integer
  progress_percent:   Float

  // Time estimates
  estimated_hours_remaining: Float
  estimated_completion_date: Date
  pace_status:        Enum (ahead, on_track, behind, at_risk)

  // Customization
  student_overrides:  JSON (manually reordered topics)
  teacher_locks:      JSON (topics locked in position by teacher)

  created_at:         Timestamp
  updated_at:         Timestamp
}
```

### Learning Goal

```
LearningGoal {
  id:                 UUID
  student_id:         UUID (FK -> User)
  title:              String (e.g., "Pass AP Biology Exam")
  goal_type:          Enum (exam_prep, course_completion, topic_mastery, skill_building, remediation)
  target_date:        Date
  target_topics:      UUID[] (FK -> Topic)
  target_mastery:     Float (required mastery level, e.g., 80)

  // Progress
  current_progress:   Float (0-100)
  pace_status:        Enum (ahead, on_track, behind, at_risk)
  estimated_completion: Date

  // Status
  status:             Enum (active, paused, completed, abandoned)
  completed_at:       Timestamp?

  created_at:         Timestamp
  updated_at:         Timestamp
}
```

---

## MCP Servers

| MCP Server | Purpose | How It Helps |
|------------|---------|-------------|
| **Memory MCP** | Student data access | Retrieve student mastery scores, learning history, and preferences for path computation |
| **SQLite / PostgreSQL MCP** | Graph and path data | Query prerequisite graph, student paths, and goal data |
| **Google Calendar MCP** | Calendar integration | Read student's schedule for smart scheduling, write study session events |
| **Fetch MCP** | Curriculum standards | Fetch curriculum framework data from educational standards APIs |
| **Brave Search MCP** | Research | Look up topic difficulty benchmarks, prerequisite relationships from educational resources |
| **Filesystem MCP** | Export | Generate and save learning path visualizations or reports |

---

## Performance Requirements

| Metric | Target |
|--------|--------|
| Path recomputation (single student) | < 2 seconds |
| Daily batch recomputation (all students) | < 30 minutes for 10,000 students |
| Visual learning path render | < 1 second |
| Priority score calculation | < 500ms |
| "What to study" recommendation | < 1 second |
| Skip-ahead test generation | < 10 seconds |
| Calendar sync | < 5 seconds |
| Goal decomposition | < 3 seconds |
| Prerequisite graph traversal (full curriculum) | < 200ms |

---

## Edge Cases and Error Handling

| Scenario | Handling |
|----------|---------|
| Circular dependency in prerequisite graph | Detect during graph construction (topological sort fails). Alert teacher/admin. Refuse to add the edge. |
| Student has no data (new student) | Cold start: use curriculum standard sequence as default path. Administer a placement assessment to bootstrap mastery scores. |
| All topics are mastered | Congratulate student. Suggest advanced topics, enrichment activities, or peer tutoring opportunities. |
| Goal is not achievable in time | Alert student and teacher. Suggest: extend deadline, increase study time, or narrow focus to most critical topics. |
| Teacher removes content for a topic | Path still includes the topic but flags "limited content available." Suggest teacher upload more content. |
| Student is enrolled in conflicting curricula | Merge prerequisite graphs and de-duplicate topics. Show unified path with color-coding by class. |
| Student disputes AI recommendation | Allow override (drag-and-drop). Log the override. If many students override the same recommendation, flag for algorithm review. |

---

## Open Questions

1. Should students be able to see the prerequisite graph for the entire curriculum, or only the portion relevant to their current goals? Showing everything could be overwhelming; showing too little could prevent exploration.
2. How do we handle interdisciplinary prerequisites? (e.g., Chemistry requires certain Math skills.) Should the learning path span across subjects?
3. Should the path engine account for cognitive load -- e.g., not recommend two hard topics on the same day even if both are high priority?
4. How do we validate the prerequisite graph? Teacher consensus? Expert review? Purely empirical (data-driven)?
5. Should the skip-ahead test count as a formal assessment (appears in grade book) or be informal (pathway-only)?
6. How do we handle students who are significantly ahead of or behind their class? Should the path deviate from the teacher's curriculum sequence?
7. What happens when a student's mastery in a "mastered" topic decays over time? Should the path automatically insert review sessions, or only when triggered by a failed spaced-repetition check?
