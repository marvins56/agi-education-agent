# F03: Student Memory & Profiles
# EduAGI - Feature Design Document

**Feature:** F03 - Student Memory & Profiles
**Version:** 1.0
**Date:** February 2026
**Author:** AGI Education Team
**Status:** Design Phase
**Priority:** P0 (Critical)

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Detailed Workflows](#2-detailed-workflows)
3. [Sub-features & Small Touches](#3-sub-features--small-touches)
4. [Technical Requirements](#4-technical-requirements)
5. [Services & Alternatives](#5-services--alternatives)
6. [Connections & Dependencies](#6-connections--dependencies)

---

## 1. Feature Overview

### 1.1 What This Feature Does

Student Memory & Profiles is the persistent intelligence layer that makes EduAGI
feel like a personal tutor who has known you for years, not a stateless chatbot
that forgets everything the moment you close the tab.

It tracks three dimensions of every student:

- **Who they are** -- learning style, preferences, grade level, goals, mood
- **What they know** -- mastery levels per topic, strengths, weaknesses, gaps
- **What happened** -- every session, every quiz, every struggle, every breakthrough

Every single interaction the student has with EduAGI reads from and writes to
this memory system. The tutor agent never generates a response without first
consulting the student's profile. The assessment agent never creates a quiz
without knowing what the student has already mastered. The voice agent picks
the right tone. The difficulty adjusts automatically. Everything flows from memory.

### 1.2 Why Memory Is the Killer Feature

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  THE FUNDAMENTAL PROBLEM WITH AI TUTORING TODAY                        │
│                                                                         │
│  ┌─────────────────────────┐     ┌──────────────────────────────────┐  │
│  │      ChatGPT / Generic  │     │          EduAGI                  │  │
│  │      AI Chatbots        │     │      (with Student Memory)       │  │
│  ├─────────────────────────┤     ├──────────────────────────────────┤  │
│  │                         │     │                                  │  │
│  │  Session 1:             │     │  Session 1:                      │  │
│  │  "Explain derivatives"  │     │  "Explain derivatives"           │  │
│  │  -> Generic explanation │     │  -> Learns you're visual,        │  │
│  │                         │     │     uses graphs, saves context   │  │
│  │  Session 2:             │     │                                  │  │
│  │  "Explain derivatives"  │     │  Session 2:                      │  │
│  │  -> SAME generic        │     │  "Welcome back! Last time we     │  │
│  │     explanation again   │     │   covered the limit definition   │  │
│  │                         │     │   of derivatives. You understood │  │
│  │  Session 3:             │     │   the concept but struggled with │  │
│  │  "I still don't get it" │     │   chain rule. Want to practice   │  │
│  │  -> Starts from zero.   │     │   chain rule with some visual    │  │
│  │     No idea what you    │     │   examples?"                     │  │
│  │     already tried.      │     │                                  │  │
│  │                         │     │  Session 15:                     │  │
│  │  Every session is       │     │  "You've mastered single-var     │  │
│  │  groundhog day.         │     │   calculus! 94% accuracy on      │  │
│  │                         │     │   the last 3 quizzes. Ready to   │  │
│  │                         │     │   start multivariable?"          │  │
│  └─────────────────────────┘     └──────────────────────────────────┘  │
│                                                                         │
│  Memory transforms a tool into a relationship.                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 How It Differentiates EduAGI

| Capability | ChatGPT | Khan Academy | EduAGI |
|---|---|---|---|
| Remembers past sessions | No (resets) | Progress bars only | Full episodic memory |
| Knows learning style | No | No | Detected + adaptive |
| Tracks per-topic mastery | No | Yes (exercise-based) | Yes (conversation + quiz) |
| Adjusts difficulty in real-time | No | Partially | Yes, per-exchange |
| Knows what explanations worked | No | No | Yes, stored in memory |
| Continues mid-topic across sessions | No | Partially | Yes, exact context restored |
| Tracks mood / energy | No | No | Yes, adjusts approach |
| Spaced repetition reminders | No | Partially | Yes, personalized schedule |
| Works across devices seamlessly | No | Yes | Yes, with full context |

### 1.4 The Three Memory Tiers

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THREE-TIER MEMORY ARCHITECTURE                       │
│                                                                         │
│  Think of it like the human brain:                                     │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                                                                  │   │
│  │   TIER 1: WORKING MEMORY (Redis)                                │   │
│  │   ─────────────────────────────                                 │   │
│  │   Like your short-term memory.                                  │   │
│  │   What you're thinking about RIGHT NOW.                         │   │
│  │                                                                  │   │
│  │   - Current conversation (last 50 messages)                     │   │
│  │   - Active session state (subject, topic, difficulty)           │   │
│  │   - Mood this session                                           │   │
│  │   - What the student just asked                                 │   │
│  │   - Temporary problem-solving scratchpad                        │   │
│  │                                                                  │   │
│  │   Speed: <1ms reads   |  TTL: 1-24 hours  |  Size: ~50KB/student│   │
│  │                                                                  │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                           Consolidates                                  │
│                             down to                                     │
│                                 │                                       │
│  ┌──────────────────────────────▼──────────────────────────────────┐   │
│  │                                                                  │   │
│  │   TIER 2: EPISODIC MEMORY (PostgreSQL)                          │   │
│  │   ────────────────────────────────────                          │   │
│  │   Like your autobiographical memory.                            │   │
│  │   What HAPPENED -- events, sessions, outcomes.                  │   │
│  │                                                                  │   │
│  │   - Every learning session (start, end, topic, outcome)         │   │
│  │   - Every quiz attempt (score, per-question results)            │   │
│  │   - Every struggle point (what confused them, how resolved)     │   │
│  │   - Mastery level changes over time                             │   │
│  │   - Streak data, study time logs                                │   │
│  │   - Goal progress events                                        │   │
│  │                                                                  │   │
│  │   Speed: 5-20ms reads  |  Retention: Forever  |  Structured     │   │
│  │                                                                  │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                            Feeds into                                   │
│                                 │                                       │
│  ┌──────────────────────────────▼──────────────────────────────────┐   │
│  │                                                                  │   │
│  │   TIER 3: SEMANTIC MEMORY (ChromaDB)                            │   │
│  │   ──────────────────────────────────                            │   │
│  │   Like your knowledge and understanding.                        │   │
│  │   What you KNOW -- concepts, relationships, context.            │   │
│  │                                                                  │   │
│  │   - Student-specific knowledge embeddings                       │   │
│  │   - Which explanations worked for THIS student                  │   │
│  │   - Conceptual connections the student has made                 │   │
│  │   - Analogies that resonated                                    │   │
│  │   - Student's own notes and summaries                           │   │
│  │                                                                  │   │
│  │   Speed: 20-50ms reads  |  Retention: Forever  |  Vector-based  │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.5 The Student Profile -- What We Track

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      STUDENT PROFILE STRUCTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  IDENTITY                          LEARNING STYLE                      │
│  ─────────                         ──────────────                      │
│  student_id: uuid                  primary_style: "visual"             │
│  name: "Sarah Chen"                secondary_style: "reading"          │
│  email: sarah@univ.edu             pace: "moderate"                    │
│  grade_level: "college_sophomore"  prefers_examples: true              │
│  age_group: "18-24"               prefers_socratic: true              │
│  sign_up_date: 2026-01-15         prefers_analogies: true             │
│                                    attention_span: "medium" (25 min)   │
│                                                                         │
│  ACADEMIC PROFILE                  PREFERENCES                         │
│  ────────────────                  ───────────                         │
│  subjects: [math, cs, physics]     voice_enabled: true                 │
│  current_courses:                  preferred_voice: "warm_female"      │
│    - Calculus II                   avatar_enabled: false               │
│    - Data Structures               sign_language: null                 │
│  strengths:                        theme: "dark"                       │
│    - algebra (92%)                 language: "en"                      │
│    - logic (88%)                   session_reminders: true             │
│  weaknesses:                       difficulty_preference: "challenge"  │
│    - word_problems (45%)                                               │
│    - proofs (52%)                  GOALS                               │
│                                    ─────                               │
│  MASTERY MAP                       - "Master Calc II by March"        │
│  ──────────                        - "Improve proof writing"          │
│  calculus:                         - "4.0 GPA this semester"           │
│    limits: 0.91                                                        │
│    derivatives: 0.85               ENGAGEMENT                          │
│    chain_rule: 0.62                ──────────                          │
│    integration: 0.34               current_streak: 7 days             │
│    u_substitution: 0.12            longest_streak: 14 days            │
│  data_structures:                  total_study_hours: 48.5            │
│    arrays: 0.95                    sessions_this_week: 4              │
│    linked_lists: 0.78              avg_session_length: 32 min         │
│    trees: 0.45                     badges: [first_quiz, week_warrior] │
│    graphs: 0.00 (not started)      last_active: 2026-02-05 19:32     │
│                                                                         │
│  MOOD / ENERGY HISTORY             PRIVACY                             │
│  ─────────────────────             ───────                             │
│  last_mood: "focused"              data_sharing: "minimal"            │
│  energy_pattern: higher_evenings   parent_view_enabled: false         │
│  frustration_triggers:             export_requested: false            │
│    - repeated wrong answers        deletion_requested: false          │
│    - long explanations                                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Workflows

### 2.1 Profile Creation During Onboarding

When a new student signs up, EduAGI runs a guided onboarding flow that builds
the initial profile. This takes about 5-8 minutes and feels like a conversation,
not a form.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     ONBOARDING FLOW                                     │
│                                                                         │
│   Student signs up                                                     │
│        │                                                                │
│        ▼                                                                │
│   ┌──────────────────────────────────────┐                             │
│   │  STEP 1: BASIC INFO                  │                             │
│   │                                       │                             │
│   │  "Hi! I'm EduAGI. What's your name?" │                             │
│   │  "What grade/year are you in?"        │                             │
│   │  "What subjects are you studying?"    │                             │
│   │                                       │                             │
│   │  Collected: name, grade_level,        │                             │
│   │            subjects[]                 │                             │
│   └──────────────┬───────────────────────┘                             │
│                  │                                                       │
│                  ▼                                                       │
│   ┌──────────────────────────────────────┐                             │
│   │  STEP 2: LEARNING STYLE ASSESSMENT   │                             │
│   │                                       │                             │
│   │  Short interactive assessment         │                             │
│   │  (see Section 2.2 for details)        │                             │
│   │                                       │                             │
│   │  Detected: learning_style,            │                             │
│   │           pace, attention_span        │                             │
│   └──────────────┬───────────────────────┘                             │
│                  │                                                       │
│                  ▼                                                       │
│   ┌──────────────────────────────────────┐                             │
│   │  STEP 3: PREFERENCES                 │                             │
│   │                                       │                             │
│   │  "Would you like me to speak my       │                             │
│   │   explanations out loud?"             │                             │
│   │  "Do you prefer to be challenged,     │                             │
│   │   or build confidence first?"         │                             │
│   │  "Do you need sign language support?" │                             │
│   │                                       │                             │
│   │  Collected: voice, avatar, sign_lang, │                             │
│   │            difficulty_preference      │                             │
│   └──────────────┬───────────────────────┘                             │
│                  │                                                       │
│                  ▼                                                       │
│   ┌──────────────────────────────────────┐                             │
│   │  STEP 4: GOAL SETTING               │                             │
│   │                                       │                             │
│   │  "What do you want to accomplish?"    │                             │
│   │  "Any deadlines I should know about?" │                             │
│   │  "How many hours per week can you     │                             │
│   │   dedicate to studying?"              │                             │
│   │                                       │                             │
│   │  Collected: goals[], deadlines,       │                             │
│   │            weekly_time_budget         │                             │
│   └──────────────┬───────────────────────┘                             │
│                  │                                                       │
│                  ▼                                                       │
│   ┌──────────────────────────────────────┐                             │
│   │  STEP 5: INITIAL DIAGNOSTIC          │                             │
│   │  (Optional -- student can skip)      │                             │
│   │                                       │                             │
│   │  Quick 5-question diagnostic per      │                             │
│   │  subject to establish baseline        │                             │
│   │  mastery levels.                      │                             │
│   │                                       │                             │
│   │  Generated: initial mastery_map       │                             │
│   └──────────────┬───────────────────────┘                             │
│                  │                                                       │
│                  ▼                                                       │
│   ┌──────────────────────────────────────┐                             │
│   │  PROFILE CREATED                     │                             │
│   │                                       │                             │
│   │  -> Saved to PostgreSQL              │                             │
│   │  -> Cached in Redis                  │                             │
│   │  -> Embeddings created in ChromaDB   │                             │
│   │                                       │                             │
│   │  "Great, Sarah! I know you're a      │                             │
│   │   visual learner studying Calc II.   │                             │
│   │   Let's get started!"                │                             │
│   └──────────────────────────────────────┘                             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**What happens behind the scenes at profile creation:**

1. A `student_profiles` row is inserted in PostgreSQL with all collected data
2. A Redis hash is created at `profile:{student_id}` with hot profile data
3. A ChromaDB collection `student_{student_id}_context` is initialized
4. Default mastery levels of 0.0 are set for all topics in selected subjects
5. A `learning_events` row is logged: `event_type = "onboarding_complete"`
6. If diagnostic was taken, mastery levels are updated from results

### 2.2 Learning Style Detection Flow

The learning style assessment is a 6-question interactive exercise that
classifies the student across four dimensions. It is NOT a boring multiple-choice
survey. It presents the same concept in different ways and observes which one
the student engages with most.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  LEARNING STYLE DETECTION FLOW                         │
│                                                                         │
│  QUESTION 1: Concept Presentation                                      │
│  ─────────────────────────────────                                     │
│  "I'm going to explain what a 'function' is in four different ways.    │
│   Tell me which one clicks best."                                      │
│                                                                         │
│   A) [DIAGRAM]  f(x) shown as a machine with input/output arrows      │
│   B) [TEXT]     "A function maps each input to exactly one output..."  │
│   C) [ANALOGY]  "Think of a vending machine. You put in a code..."    │
│   D) [EXAMPLE]  "Try it: if f(x) = 2x+1, what is f(3)?"             │
│                                                                         │
│                     │                                                   │
│       ┌─────────────┼─────────────┬─────────────┐                      │
│       │             │             │             │                      │
│     Picks A       Picks B      Picks C       Picks D                  │
│       │             │             │             │                      │
│   visual++      reading++    auditory++   kinesthetic++               │
│                                                                         │
│  QUESTION 2: Problem Approach                                          │
│  ────────────────────────────                                          │
│  "How would you prefer to learn to solve quadratic equations?"         │
│                                                                         │
│   A) "Show me a worked example step by step"                           │
│   B) "Let me try one and give me hints"                                │
│   C) "Explain the theory first, then I'll practice"                    │
│   D) "Show me a video walking through it"                              │
│                                                                         │
│  QUESTION 3: Recall Test                                               │
│  ────────────────────────                                              │
│  Shows a concept via all four modalities. After 60 seconds, asks      │
│  the student to recall. Measures which modality produced best recall.  │
│                                                                         │
│  QUESTION 4: Pacing Test                                               │
│  ────────────────────────                                              │
│  Presents 3 explanations of increasing complexity. Tracks:             │
│   - Time spent on each                                                 │
│   - Whether student asked "slow down" or "skip ahead"                  │
│   - Comprehension check answers                                        │
│                                                                         │
│  QUESTION 5: Engagement Pattern                                        │
│  ────────────────────────────                                          │
│  "When you get stuck on a problem, what do you usually do?"            │
│   A) "Look for a diagram or visual explanation"                        │
│   B) "Re-read the textbook section"                                    │
│   C) "Ask someone to explain it to me verbally"                        │
│   D) "Try different approaches until something works"                  │
│                                                                         │
│  QUESTION 6: Attention Span Estimation                                 │
│  ────────────────────────────────────                                  │
│  Tracks how long the student spent on questions 1-5 without           │
│  disengaging. Combined with self-report:                               │
│  "How long can you usually focus on studying before needing a break?" │
│   A) 10-15 minutes   B) 20-30 minutes                                 │
│   C) 30-45 minutes   D) 45+ minutes                                   │
│                                                                         │
│                     │                                                   │
│                     ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │               STYLE CLASSIFICATION ENGINE                     │      │
│  │                                                               │      │
│  │  Scoring Matrix:                                             │      │
│  │                                                               │      │
│  │  visual_score     = sum(visual indicators)    / max_possible │      │
│  │  auditory_score   = sum(auditory indicators)  / max_possible │      │
│  │  reading_score    = sum(reading indicators)   / max_possible │      │
│  │  kinesthetic_score= sum(kinesthetic indicators)/ max_possible│      │
│  │                                                               │      │
│  │  primary_style    = argmax(scores)                           │      │
│  │  secondary_style  = second_highest(scores)                   │      │
│  │                                                               │      │
│  │  pace = derived from Q4 timing data                          │      │
│  │  attention_span = derived from Q6 + observed behavior        │      │
│  │                                                               │      │
│  │  Confidence:                                                  │      │
│  │  If top two scores are within 10% -> "balanced" learner      │      │
│  │  If top score is >60% -> high confidence in classification   │      │
│  │  If all scores are similar -> "multimodal" learner           │      │
│  │                                                               │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  NOTE: This classification is NOT permanent. The system continuously   │
│  re-evaluates learning style based on which explanations actually      │
│  lead to better outcomes for this student. Initial detection is just   │
│  the starting point.                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Working Memory During a Session (Redis)

Working memory holds the live state of an active tutoring session. It is the
fastest memory tier and the one consulted on every single exchange.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  WORKING MEMORY (REDIS) -- IN-SESSION FLOW             │
│                                                                         │
│  When a student opens EduAGI and starts a session:                     │
│                                                                         │
│  1. LOAD PHASE                                                         │
│     ──────────                                                         │
│     ┌─────────────┐     ┌─────────────┐     ┌──────────────┐          │
│     │  Student    │     │  PostgreSQL  │     │    Redis     │          │
│     │  opens app  │────>│  Load full   │────>│  Cache hot   │          │
│     │             │     │  profile     │     │  profile     │          │
│     └─────────────┘     └─────────────┘     └──────────────┘          │
│                                                                         │
│     Redis keys created:                                                │
│     ┌──────────────────────────────────────────────────────────┐       │
│     │  session:{session_id}:context                            │       │
│     │    -> {student_id, subject, topic, mode, difficulty}     │       │
│     │                                                          │       │
│     │  session:{session_id}:messages                           │       │
│     │    -> [msg1, msg2, ...] (capped at 50)                  │       │
│     │                                                          │       │
│     │  profile:{student_id}                                    │       │
│     │    -> {learning_style, pace, mastery_map, preferences}  │       │
│     │                                                          │       │
│     │  session:{session_id}:scratchpad                         │       │
│     │    -> {current_problem, hints_given, attempts}          │       │
│     └──────────────────────────────────────────────────────────┘       │
│                                                                         │
│  2. EXCHANGE PHASE (every message)                                     │
│     ──────────────────────────────                                     │
│                                                                         │
│     Student sends message                                              │
│          │                                                              │
│          ▼                                                              │
│     ┌─────────────────┐                                                │
│     │ Read from Redis │                                                │
│     │                 │                                                │
│     │ - session ctx   │  <1ms per read                                 │
│     │ - last N msgs   │                                                │
│     │ - profile cache │                                                │
│     │ - scratchpad    │                                                │
│     └────────┬────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│     ┌─────────────────┐                                                │
│     │ Build system    │                                                │
│     │ prompt from     │  Profile data shapes the prompt                │
│     │ memory context  │  (see Section 2.7)                             │
│     └────────┬────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│     ┌─────────────────┐                                                │
│     │ LLM generates   │                                                │
│     │ response        │                                                │
│     └────────┬────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│     ┌─────────────────┐                                                │
│     │ Write to Redis  │                                                │
│     │                 │                                                │
│     │ - Append msg    │                                                │
│     │ - Update ctx    │                                                │
│     │ - Update        │                                                │
│     │   scratchpad    │                                                │
│     └────────┬────────┘                                                │
│              │                                                          │
│              ▼                                                          │
│     Response sent to student                                           │
│                                                                         │
│  3. CONSOLIDATION PHASE (session end or periodic flush)                │
│     ───────────────────────────────────────────────────                │
│     When session ends, working memory is consolidated to               │
│     episodic memory (PostgreSQL). See Section 2.6.                     │
│                                                                         │
│     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│     │    Redis     │     │  Summarize   │     │ PostgreSQL   │        │
│     │  session     │────>│  session     │────>│ Save event   │        │
│     │  data        │     │  via LLM     │     │ + update     │        │
│     └──────────────┘     └──────────────┘     │ profile      │        │
│                                                └──────────────┘        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.4 Episodic Memory -- Recording Learning Events (PostgreSQL)

Episodic memory is the structured log of everything that has happened in the
student's learning journey. It answers the question: "What did this student
experience, and what were the outcomes?"

```
┌─────────────────────────────────────────────────────────────────────────┐
│                EPISODIC MEMORY -- EVENT RECORDING FLOW                  │
│                                                                         │
│  Every significant learning moment becomes a learning_event row:       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    EVENT TRIGGERS                                │   │
│  │                                                                  │   │
│  │  SESSION EVENTS          ASSESSMENT EVENTS    MILESTONE EVENTS  │   │
│  │  ──────────────          ─────────────────    ────────────────  │   │
│  │  session_start           quiz_started         mastery_achieved  │   │
│  │  session_end             quiz_completed        topic_unlocked   │   │
│  │  topic_changed           question_answered     badge_earned     │   │
│  │  explanation_given       assignment_submitted  streak_milestone │   │
│  │  student_confused        grade_received        goal_completed   │   │
│  │  breakthrough_moment                                            │   │
│  │  hint_requested                                                 │   │
│  │  student_disengaged                                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  Example: What gets recorded during a single tutoring session          │
│  ─────────────────────────────────────────────────────────────         │
│                                                                         │
│  Timeline    Event                   Data Stored                       │
│  ─────────   ─────                   ───────────                       │
│  19:00:00    session_start           {subject: "calculus",             │
│                                       topic: "chain_rule",             │
│                                       mood: "focused"}                 │
│                                                                         │
│  19:03:22    explanation_given       {concept: "chain_rule",           │
│                                       approach: "visual_diagram",      │
│                                       student_understood: true}        │
│                                                                         │
│  19:08:45    hint_requested          {problem: "d/dx sin(x^2)",       │
│                                       hint_number: 1,                  │
│                                       hint_text: "What's the          │
│                                        outer function?"}               │
│                                                                         │
│  19:09:12    hint_requested          {problem: "d/dx sin(x^2)",       │
│                                       hint_number: 2}                  │
│                                                                         │
│  19:10:30    breakthrough_moment     {problem: "d/dx sin(x^2)",       │
│                                       student_got_it: true,            │
│                                       after_hints: 2}                  │
│                                                                         │
│  19:15:00    student_confused        {concept: "nested_chain_rule",   │
│                                       confusion_signal: "repeated      │
│                                        wrong answers",                 │
│                                       approach_tried: "algebraic"}     │
│                                                                         │
│  19:18:00    explanation_given       {concept: "nested_chain_rule",   │
│                                       approach: "analogy_layers",      │
│                                       switched_from: "algebraic",      │
│                                       student_understood: true}        │
│                                                                         │
│  19:32:00    session_end             {duration_minutes: 32,           │
│                                       topics_covered:                  │
│                                         ["chain_rule",                 │
│                                          "nested_chain_rule"],         │
│                                       mastery_change:                  │
│                                         {chain_rule: 0.62->0.71,      │
│                                          nested: 0.00->0.35},         │
│                                       session_summary: "Student       │
│                                         made progress on chain rule.  │
│                                         Struggled with nested but     │
│                                         responded well to analogy     │
│                                         approach."}                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key design decisions for episodic memory:**

- Events are append-only. We never update or delete learning events (except
  for GDPR deletion requests). This gives us a complete audit trail.
- The `data` column is JSONB, allowing flexible schemas per event type while
  keeping the core columns (student_id, event_type, subject, topic, outcome,
  created_at) queryable and indexed.
- Session summaries are generated by the LLM at session end and stored as a
  separate `session_summary` event. This gives us a compressed, searchable
  narrative of what happened.

### 2.5 Semantic Memory -- Student-Specific Knowledge Context (ChromaDB)

Semantic memory stores vector embeddings that capture qualitative knowledge
about the student's learning. While episodic memory tracks WHAT happened,
semantic memory tracks WHAT WORKED.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              SEMANTIC MEMORY (ChromaDB) -- KNOWLEDGE CONTEXT            │
│                                                                         │
│  Each student gets a dedicated ChromaDB collection:                    │
│  Collection name: "student_{student_id}_context"                       │
│                                                                         │
│  WHAT GETS EMBEDDED:                                                   │
│  ──────────────────                                                    │
│                                                                         │
│  1. Successful Explanations                                            │
│     "The analogy of peeling an onion worked for explaining             │
│      nested chain rule. Student had a breakthrough after this."        │
│     Metadata: {topic: "nested_chain_rule", approach: "analogy",        │
│                effectiveness: 0.95, timestamp: "2026-02-05"}           │
│                                                                         │
│  2. Student Misconceptions                                             │
│     "Student believes derivatives 'find the slope of a line'.          │
│      Needs correction: derivatives find instantaneous rate of          │
│      change, which is the slope of the tangent line."                  │
│     Metadata: {topic: "derivatives", type: "misconception",            │
│                corrected: true, timestamp: "2026-01-28"}               │
│                                                                         │
│  3. Student's Own Insights                                             │
│     "Student described integration as 'adding up tiny slices'          │
│      which shows good intuition for Riemann sums."                     │
│     Metadata: {topic: "integration", type: "student_insight",          │
│                quality: "strong"}                                       │
│                                                                         │
│  4. Failed Approaches                                                  │
│     "Pure algebraic explanation of chain rule did not work.            │
│      Student zoned out after 3 minutes. Switch to visual."            │
│     Metadata: {topic: "chain_rule", approach: "algebraic",             │
│                effectiveness: 0.15, avoid: true}                       │
│                                                                         │
│  5. Cross-Topic Connections                                            │
│     "Student connects derivatives to physics (velocity).               │
│      Use physics analogies when introducing new calc concepts."        │
│     Metadata: {topics: ["derivatives", "physics"], type: "connection"} │
│                                                                         │
│  HOW IT IS USED:                                                       │
│  ──────────────                                                        │
│                                                                         │
│  Student asks about integration by parts                               │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────┐                                       │
│  │ Similarity search:          │                                       │
│  │ "integration by parts        │                                       │
│  │  explanation approach"       │                                       │
│  │                              │                                       │
│  │ Results:                     │                                       │
│  │  - Visual approaches work    │                                       │
│  │  - Physics analogies help    │                                       │
│  │  - Pure algebra does NOT     │                                       │
│  │  - Student knows u-sub       │                                       │
│  │    (can build on that)       │                                       │
│  └──────────────┬──────────────┘                                       │
│                 │                                                        │
│                 ▼                                                        │
│  ┌─────────────────────────────┐                                       │
│  │ System prompt includes:     │                                       │
│  │                              │                                       │
│  │ "This student responds well  │                                       │
│  │  to visual explanations and  │                                       │
│  │  physics analogies. Avoid    │                                       │
│  │  pure algebraic approaches.  │                                       │
│  │  They already understand     │                                       │
│  │  u-substitution -- build on  │                                       │
│  │  that foundation."           │                                       │
│  └─────────────────────────────┘                                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.6 Profile Update Cycle

The student profile is a living document that updates after every meaningful
interaction. There are two update cadences: real-time micro-updates and
end-of-session macro-updates.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PROFILE UPDATE CYCLE                                │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │                  MICRO-UPDATES (real-time)                     │     │
│  │                  During every exchange                         │     │
│  │                                                                │     │
│  │  Trigger                    What Updates                      │     │
│  │  ───────                    ────────────                      │     │
│  │  Student answers correctly  scratchpad.attempts++             │     │
│  │                             scratchpad.correct++               │     │
│  │                                                                │     │
│  │  Student asks for hint      scratchpad.hints_given++          │     │
│  │                             confidence signal -= 0.05         │     │
│  │                                                                │     │
│  │  Student says "I don't      difficulty_this_session -= 1      │     │
│  │   understand"               confusion_flag = true             │     │
│  │                                                                │     │
│  │  Student says "too easy"    difficulty_this_session += 1      │     │
│  │                                                                │     │
│  │  Student goes quiet for     engagement_signal = "low"         │     │
│  │   >2 minutes                check_in_needed = true            │     │
│  │                                                                │     │
│  │  All micro-updates go to Redis only (fast writes)             │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                         │
│                            │                                            │
│                  Session ends or flush timer fires                      │
│                            │                                            │
│                            ▼                                            │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │                  MACRO-UPDATES (end of session)                │     │
│  │                                                                │     │
│  │  Step 1: Summarize session                                    │     │
│  │  ─────────────────────────                                    │     │
│  │  LLM reads full session transcript from Redis and generates:  │     │
│  │   - Session summary (2-3 sentences)                           │     │
│  │   - Topics covered with outcomes                              │     │
│  │   - Key struggle points                                       │     │
│  │   - Key breakthroughs                                         │     │
│  │   - Recommended next topics                                   │     │
│  │                                                                │     │
│  │  Step 2: Update mastery levels                                │     │
│  │  ─────────────────────────────                                │     │
│  │  For each topic discussed:                                    │     │
│  │   mastery_new = f(mastery_old, correct_answers,               │     │
│  │                   hints_needed, confusion_events,              │     │
│  │                   time_on_topic)                               │     │
│  │   (see Section 2.9 for algorithm)                             │     │
│  │                                                                │     │
│  │  Step 3: Update strengths/weaknesses                          │     │
│  │  ───────────────────────────────────                          │     │
│  │  Recalculate from updated mastery map                         │     │
│  │   strengths = topics where mastery > 0.80                     │     │
│  │   weaknesses = topics where mastery < 0.50                    │     │
│  │   (see Section 2.10 for algorithm)                            │     │
│  │                                                                │     │
│  │  Step 4: Update learning style signals                        │     │
│  │  ─────────────────────────────────────                        │     │
│  │  If a new explanation approach worked better than expected     │     │
│  │  for this student's classified style, adjust style weights:   │     │
│  │   visual_weight += delta if visual approach worked             │     │
│  │   (Style evolves over time based on actual outcomes)          │     │
│  │                                                                │     │
│  │  Step 5: Persist to PostgreSQL and ChromaDB                   │     │
│  │  ──────────────────────────────────────────                   │     │
│  │   -> learning_events rows for the session                     │     │
│  │   -> student_profiles row updated                             │     │
│  │   -> Effective explanations embedded in ChromaDB              │     │
│  │   -> Failed approaches embedded in ChromaDB (marked avoid)    │     │
│  │                                                                │     │
│  │  Step 6: Update engagement metrics                            │     │
│  │  ─────────────────────────────────                            │     │
│  │   -> study_time += session_duration                           │     │
│  │   -> streak updated (if new day)                              │     │
│  │   -> weekly_sessions++                                        │     │
│  │   -> Check for badge triggers                                 │     │
│  │                                                                │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────┐     │
│  │                  QUIZ-TRIGGERED UPDATES                        │     │
│  │                                                                │     │
│  │  After quiz grading completes:                                │     │
│  │                                                                │     │
│  │  For each question:                                           │     │
│  │   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐  │     │
│  │   │  Question   │     │  Grade +     │     │  Update      │  │     │
│  │   │  topic +    │────>│  correct/    │────>│  mastery     │  │     │
│  │   │  difficulty │     │  incorrect   │     │  for topic   │  │     │
│  │   └─────────────┘     └──────────────┘     └──────────────┘  │     │
│  │                                                                │     │
│  │  Quiz mastery impact is weighted MORE heavily than             │     │
│  │  conversation-based signals because it is a direct             │     │
│  │  measurement of understanding.                                │     │
│  │                                                                │     │
│  │  quiz_weight = 0.7  |  conversation_weight = 0.3              │     │
│  │                                                                │     │
│  │  If quiz score < 50% on a topic previously marked as          │     │
│  │  "mastered": trigger review recommendation and reduce         │     │
│  │  mastery level by decay factor.                               │     │
│  │                                                                │     │
│  └───────────────────────────────────────────────────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.7 How the Profile Feeds Into the Tutor's System Prompt

Every response from EduAGI is shaped by the student's profile. The system
prompt is dynamically constructed before each LLM call.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              SYSTEM PROMPT CONSTRUCTION PIPELINE                        │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │   Redis      │  │  PostgreSQL  │  │   ChromaDB   │                 │
│  │              │  │              │  │              │                 │
│  │  Session ctx │  │  Mastery map │  │  What works  │                 │
│  │  Last msgs   │  │  History     │  │  for student │                 │
│  │  Mood        │  │  Strengths   │  │  Past good   │                 │
│  │  Difficulty  │  │  Weaknesses  │  │  explanations│                 │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                  │                          │
│         └─────────────────┼──────────────────┘                         │
│                           │                                             │
│                           ▼                                             │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                  PROMPT BUILDER                                │      │
│  │                                                               │      │
│  │  SECTION 1: Role & Persona                                   │      │
│  │  "You are EduAGI, a patient, adaptive AI tutor..."           │      │
│  │                                                               │      │
│  │  SECTION 2: Student Profile                       [from PG]  │      │
│  │  "STUDENT: Sarah Chen, college sophomore                      │      │
│  │   LEARNING STYLE: Visual learner, moderate pace               │      │
│  │   STRENGTHS: algebra (92%), logic (88%)                       │      │
│  │   WEAKNESSES: word problems (45%), proofs (52%)               │      │
│  │   MASTERY ON CURRENT TOPIC: chain_rule = 0.71"               │      │
│  │                                                               │      │
│  │  SECTION 3: Session Context                      [from Redis] │      │
│  │  "CURRENT SESSION: Calculus, chain rule practice              │      │
│  │   DIFFICULTY: medium (student finding it manageable)           │      │
│  │   MOOD: focused                                               │      │
│  │   SESSION TIME: 18 minutes in"                                │      │
│  │                                                               │      │
│  │  SECTION 4: What Works for This Student         [from Chroma] │      │
│  │  "EFFECTIVE APPROACHES:                                       │      │
│  │   - Visual diagrams of function composition                   │      │
│  │   - Physics analogies (velocity, acceleration)                │      │
│  │   - Step-by-step worked examples                              │      │
│  │   AVOID: Pure algebraic derivations without visuals"          │      │
│  │                                                               │      │
│  │  SECTION 5: Continuity Context                   [from PG]   │      │
│  │  "LAST SESSION (2 days ago): Worked on basic chain rule.      │      │
│  │   Student mastered simple cases but struggled with nested     │      │
│  │   compositions. Onion-peeling analogy was a breakthrough."    │      │
│  │                                                               │      │
│  │  SECTION 6: Teaching Guidelines                               │      │
│  │  "1. Use Socratic questioning                                 │      │
│  │   2. Favor visual explanations for this student               │      │
│  │   3. Break into small steps (attention span: 25 min)          │      │
│  │   4. Reference the onion analogy if discussing nesting        │      │
│  │   5. If student shows frustration, simplify and encourage"    │      │
│  │                                                               │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  This prompt is rebuilt on EVERY exchange. It costs ~800-1200           │
│  tokens of system prompt but makes every response deeply                │
│  personalized. The overhead is worth it.                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.8 Cross-Session Continuity

When a student returns after hours, days, or weeks, EduAGI picks up where
they left off. The greeting and re-engagement flow depends on the time gap.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   CROSS-SESSION CONTINUITY FLOW                        │
│                                                                         │
│  Student logs in                                                       │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────┐                                   │
│  │ Load last session from PG       │                                   │
│  │  -> last_session_date           │                                   │
│  │  -> last_topic                  │                                   │
│  │  -> last_session_summary        │                                   │
│  │  -> unfinished_work             │                                   │
│  │  -> current_streak              │                                   │
│  └────────────┬────────────────────┘                                   │
│               │                                                         │
│               ▼                                                         │
│  ┌─────────────────────────────────┐                                   │
│  │ Calculate time gap              │                                   │
│  │  gap = now - last_session_date  │                                   │
│  └────────────┬────────────────────┘                                   │
│               │                                                         │
│       ┌───────┼───────┬───────────┬──────────────┐                     │
│       │       │       │           │              │                     │
│    < 4 hrs  4-24 hrs  1-7 days   1-4 weeks    > 4 weeks              │
│       │       │       │           │              │                     │
│       ▼       ▼       ▼           ▼              ▼                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  GAP < 4 HOURS (same study session, took a break)           │      │
│  │                                                              │      │
│  │  "Welcome back! We were working on [topic].                 │      │
│  │   Ready to continue?"                                        │      │
│  │                                                              │      │
│  │  Action: Restore full Redis session state.                  │      │
│  │  No re-assessment needed.                                   │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  GAP 4-24 HOURS (came back next day)                         │      │
│  │                                                              │      │
│  │  "Hey Sarah! Yesterday we covered [topic] and you were      │      │
│  │   getting the hang of [specific_concept]. Want to do a       │      │
│  │   quick warm-up problem before we continue?"                 │      │
│  │                                                              │      │
│  │  Action: Start fresh Redis session but pre-load context.    │      │
│  │  Offer 1 warm-up question on yesterday's topic.             │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  GAP 1-7 DAYS (regular return)                               │      │
│  │                                                              │      │
│  │  "Welcome back, Sarah! It's been [N] days. Last time we     │      │
│  │   worked on [topic]. You had mastered [X] and were working  │      │
│  │   on [Y]. I also noticed it's been a while since we         │      │
│  │   reviewed [old_topic] -- want to do a quick refresher      │      │
│  │   first?"                                                    │      │
│  │                                                              │      │
│  │  Action: Fresh session. Include spaced repetition check.    │      │
│  │  Offer choice: continue where left off OR review old topic. │      │
│  │  Apply memory decay to recent topic mastery (-5% per day).  │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  GAP 1-4 WEEKS (been away)                                   │      │
│  │                                                              │      │
│  │  "Sarah! Great to see you back. It's been [N] weeks.        │      │
│  │   Before we dive in, let me give you a quick 3-question     │      │
│  │   check-in on what we covered last time to see what stuck." │      │
│  │                                                              │      │
│  │  Action: Fresh session. Run mini-diagnostic on last 2-3     │      │
│  │  topics. Re-calibrate mastery levels from diagnostic         │      │
│  │  results. Apply significant decay (-15% to -30%) to         │      │
│  │  topics not recently practiced.                              │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │  GAP > 4 WEEKS (long absence)                                │      │
│  │                                                              │      │
│  │  "Hey Sarah, it's been a while! Welcome back. A lot can     │      │
│  │   change in [N] weeks, so let me do a quick assessment to   │      │
│  │   see where you are now. This will take about 5 minutes     │      │
│  │   and will help me give you the best experience."           │      │
│  │                                                              │      │
│  │  Action: Fresh session. Run full diagnostic on all active   │      │
│  │  subjects. Reset mastery levels to diagnostic results.       │      │
│  │  Preserve historical data but do not assume current          │      │
│  │  knowledge matches old levels.                               │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.9 Mastery Level Calculation Per Topic

Mastery is a decimal between 0.00 and 1.00, calculated per topic per student.
It represents how well the student understands and can apply a concept.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   MASTERY LEVEL CALCULATION                             │
│                                                                         │
│  MASTERY SIGNALS (inputs to the algorithm)                             │
│  ─────────────────────────────────────────                             │
│                                                                         │
│  Signal                    Weight    Source          Range              │
│  ────────────────────────  ──────    ──────          ─────              │
│  quiz_accuracy             0.35      Assessment      0.0 - 1.0         │
│  conversation_understanding 0.20     Tutor analysis  0.0 - 1.0         │
│  problem_solving_success   0.25      Exercise logs   0.0 - 1.0         │
│  hint_dependency           -0.10     Session data    0.0 - 1.0 (neg)  │
│  time_decay                -0.10     Time since last 0.0 - 0.3 (neg)  │
│  consistency               0.10      Variance check  0.0 - 1.0         │
│  self_assessment_alignment 0.10      Student input   0.0 - 1.0         │
│                                                                         │
│  CALCULATION                                                           │
│  ───────────                                                           │
│                                                                         │
│  mastery = (                                                           │
│    quiz_accuracy * 0.35                                                │
│    + conversation_understanding * 0.20                                 │
│    + problem_solving_success * 0.25                                    │
│    - hint_dependency * 0.10                                            │
│    - time_decay * 0.10                                                 │
│    + consistency * 0.10                                                │
│    + self_assessment_alignment * 0.10                                  │
│  )                                                                      │
│                                                                         │
│  mastery = clamp(mastery, 0.00, 1.00)                                  │
│                                                                         │
│                                                                         │
│  MASTERY LEVELS                                                        │
│  ──────────────                                                        │
│                                                                         │
│  0.00 - 0.19  |  NOT STARTED     |  No exposure to this topic         │
│  0.20 - 0.39  |  BEGINNER        |  Introduced but not understood     │
│  0.40 - 0.59  |  DEVELOPING      |  Partial understanding, needs help │
│  0.60 - 0.79  |  PROFICIENT      |  Solid understanding, some gaps    │
│  0.80 - 0.94  |  ADVANCED        |  Strong command, minor weaknesses  │
│  0.95 - 1.00  |  MASTERED        |  Can teach this to others          │
│                                                                         │
│                                                                         │
│  TIME DECAY FUNCTION                                                   │
│  ───────────────────                                                   │
│  Mastery decays if the student hasn't engaged with a topic.            │
│  Decay follows a modified Ebbinghaus forgetting curve:                 │
│                                                                         │
│  decay = 0.05 * ln(days_since_last_practice + 1)                      │
│                                                                         │
│  Capped at 0.30 (mastery never drops more than 30% from decay alone). │
│  Decay is PAUSED for topics with mastery >= 0.95 for the first        │
│  14 days (well-learned topics are more resistant to forgetting).       │
│                                                                         │
│                                                                         │
│  EXAMPLE MASTERY EVOLUTION                                             │
│  ────────────────────────                                              │
│                                                                         │
│  Topic: chain_rule                                                     │
│                                                                         │
│  Day 1:  Introduced in session          -> 0.20                       │
│  Day 1:  Practiced 3 problems (2/3)     -> 0.38                       │
│  Day 3:  Quiz: 60% on chain rule Qs     -> 0.52                       │
│  Day 3:  Session: worked examples       -> 0.61                       │
│  Day 5:  Quiz: 85% on chain rule Qs     -> 0.74                       │
│  Day 8:  (no practice, -0.08 decay)     -> 0.66                       │
│  Day 8:  Session: nailed all problems   -> 0.79                       │
│  Day 10: Quiz: 95% on chain rule Qs     -> 0.88                       │
│  Day 15: Review quiz: 90%               -> 0.91                       │
│  Day 30: (no practice, -0.12 decay)     -> 0.79                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.10 Strength/Weakness Tracking Algorithm

Strengths and weaknesses are derived from the mastery map but also factor in
trend direction (improving vs declining) and relative performance.

```
┌─────────────────────────────────────────────────────────────────────────┐
│              STRENGTH / WEAKNESS TRACKING ALGORITHM                     │
│                                                                         │
│  CLASSIFICATION RULES                                                  │
│  ────────────────────                                                  │
│                                                                         │
│  A topic is a STRENGTH if:                                             │
│    mastery >= 0.80                                                     │
│    AND (trend == "stable" OR trend == "improving")                     │
│    AND quiz_accuracy_last_3 >= 0.75                                    │
│                                                                         │
│  A topic is a WEAKNESS if:                                             │
│    mastery < 0.50                                                      │
│    OR (mastery < 0.65 AND trend == "declining")                        │
│    OR (quiz_accuracy_last_3 < 0.50 regardless of mastery)             │
│                                                                         │
│  A topic is an EMERGING STRENGTH if:                                   │
│    mastery between 0.60 and 0.79                                       │
│    AND trend == "improving" (mastery went up last 3 sessions)          │
│                                                                         │
│  A topic is an AT-RISK area if:                                        │
│    mastery was >= 0.80 (previously a strength)                         │
│    AND mastery has decayed to < 0.70 (due to time or quiz failure)     │
│                                                                         │
│                                                                         │
│  TREND CALCULATION                                                     │
│  ─────────────────                                                     │
│  Based on last 5 mastery snapshots for a topic:                        │
│                                                                         │
│  mastery_snapshots = [0.45, 0.52, 0.58, 0.61, 0.67]                   │
│                                                                         │
│  slope = linear_regression_slope(snapshots)                            │
│                                                                         │
│  if slope > 0.02:   trend = "improving"                                │
│  if slope < -0.02:  trend = "declining"                                │
│  else:              trend = "stable"                                    │
│                                                                         │
│                                                                         │
│  RELATIVE PERFORMANCE                                                  │
│  ────────────────────                                                  │
│  Strengths and weaknesses are also computed relative to the student's  │
│  own average. A student averaging 0.90 across topics with one topic    │
│  at 0.72 has a RELATIVE weakness even though 0.72 is objectively      │
│  decent.                                                                │
│                                                                         │
│  relative_weakness = topics where                                      │
│    mastery < (student_average_mastery - 0.15)                          │
│                                                                         │
│  relative_strength = topics where                                      │
│    mastery > (student_average_mastery + 0.10)                          │
│                                                                         │
│                                                                         │
│  HOW STRENGTHS/WEAKNESSES ARE USED                                     │
│  ─────────────────────────────────                                     │
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│  │  Weaknesses  │────>│ Tutor adjusts│────>│ More scaffolding,    │   │
│  │  detected    │     │ approach     │     │ extra examples, check│   │
│  └──────────────┘     └──────────────┘     │ for understanding    │   │
│                                             └──────────────────────┘   │
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│  │  Strengths   │────>│ Assessment   │────>│ Harder questions,    │   │
│  │  detected    │     │ adjusts      │     │ less hand-holding,   │   │
│  └──────────────┘     └──────────────┘     │ connect to new topics│   │
│                                             └──────────────────────┘   │
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐   │
│  │  At-risk     │────>│ Spaced rep   │────>│ "It's been a while  │   │
│  │  topics      │     │ system       │     │  since we reviewed   │   │
│  └──────────────┘     └──────────────┘     │  X. Quick refresher?"│   │
│                                             └──────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Sub-features & Small Touches

These are the details that transform a functional system into a delightful
experience. Students remember these small touches more than they remember the
architecture behind them.

### 3.1 "Welcome Back" Greeting

Every return visit generates a personalized greeting based on the continuity
flow described in Section 2.8. The greeting includes:

- Student's name
- Reference to last session's topic and what they accomplished
- Streak status if applicable ("Day 7 of your streak!")
- Spaced repetition suggestion if any topics are due for review
- Mood check-in if the student has opted in

The greeting is generated by the LLM with a specific mini-prompt that reads the
last session summary from episodic memory. It is cached for the session so it
only generates once per login.

### 3.2 Spaced Repetition Reminders

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   SPACED REPETITION SYSTEM                             │
│                                                                         │
│  Based on a simplified SM-2 algorithm adapted for topic mastery:       │
│                                                                         │
│  When a topic reaches mastery >= 0.60 ("proficient"), it enters the   │
│  spaced repetition queue with an initial review interval.              │
│                                                                         │
│  Review Schedule (days until next review):                             │
│                                                                         │
│  After 1st successful review:    1 day                                 │
│  After 2nd successful review:    3 days                                │
│  After 3rd successful review:    7 days                                │
│  After 4th successful review:    14 days                               │
│  After 5th successful review:    30 days                               │
│  After 6th+ successful review:   60 days                               │
│                                                                         │
│  "Successful review" = student scores >= 70% on a 3-question check    │
│  on the topic.                                                          │
│                                                                         │
│  If review is FAILED (< 70%), interval resets to 1 day and mastery    │
│  is reduced.                                                            │
│                                                                         │
│  NOTIFICATION FLOW                                                     │
│  ─────────────────                                                     │
│                                                                         │
│  Daily cron job at 06:00 UTC:                                          │
│    1. Query all students with topics due for review                    │
│    2. For each student, check notification preferences                 │
│    3. If session_reminders == true:                                    │
│       - Add to welcome greeting queue                                  │
│       - Optionally send push/email notification                        │
│                                                                         │
│  In-session prompt:                                                    │
│  "Hey Sarah, it's been 3 days since we reviewed integration by        │
│   parts. Want to do a quick 3-question refresher? It'll take less     │
│   than 2 minutes."                                                     │
│                                                                         │
│  The student can:                                                      │
│   - Accept (do the refresher now)                                      │
│   - Snooze ("Maybe later" -- moves to end of session)                 │
│   - Dismiss ("Skip it" -- extends interval by 1 day)                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Learning Streak Tracker

Streaks are calculated based on calendar days with at least one meaningful
learning session (>= 5 minutes of active engagement, not just logging in).

- **Current streak**: Consecutive days with a session
- **Longest streak**: All-time record
- **Streak freeze**: Students get 1 free "freeze" per week (miss a day without
  breaking the streak). Must be claimed in advance or auto-applied.

Streak milestones trigger celebrations:
- 3 days: "Nice! 3-day streak!"
- 7 days: "A full week! You're building a habit."
- 14 days: "Two weeks strong. Consistency is key."
- 30 days: "30 days! You're in the top 5% of learners."
- 100 days: "Triple digits! Legendary commitment."

Streaks are stored in the `student_profiles` table and updated as part of the
session-end macro-update.

### 3.4 Study Time Tracking with Weekly Summaries

Every session's duration is logged in `learning_events` with millisecond
precision (start to last activity, not start to session close -- idle time
over 3 minutes is subtracted).

Weekly summary generated every Sunday at 20:00 in the student's timezone:

```
  ┌──────────────────────────────────────────┐
  │  YOUR WEEK IN REVIEW                      │
  │  ─────────────────                        │
  │  Total study time: 4h 23m                 │
  │  Sessions: 6                              │
  │  Topics worked on: 4                      │
  │  Mastery improvements:                    │
  │    chain_rule:     0.52 -> 0.71  (+19%)  │
  │    integration:    0.34 -> 0.42  (+8%)   │
  │  Quiz scores: 78% avg (up from 65%)      │
  │  Current streak: 7 days                   │
  │                                            │
  │  Top achievement this week:               │
  │  Reached "Proficient" on chain rule!      │
  └──────────────────────────────────────────┘
```

The summary is stored as a `weekly_summary` learning event and also embedded
in ChromaDB for the LLM to reference when discussing progress.

### 3.5 Mood/Energy Tracking

At the start of each session, EduAGI optionally asks about the student's
current state. This is NOT a mandatory popup. It is a natural conversational
check-in.

**How it is asked:**
- First session of the day: "How are you feeling about studying today?"
- Return after a break: "Ready to jump back in, or want to start easy?"
- Before an assessment: "How confident are you feeling about [topic]?"

**Mood options** (internally mapped):
- "Great / Energized" -> difficulty can be pushed higher, move faster
- "Good / Normal" -> standard difficulty and pace
- "Tired / Low energy" -> reduce difficulty by 1 level, shorter problems
- "Stressed / Anxious" -> reduce difficulty, more encouragement, avoid
  timed exercises, offer breathing break suggestion
- "Frustrated" -> switch to confidence-building exercises on strengths
  before returning to the challenging topic

Mood data is stored in Redis for the session and in PostgreSQL as a
`mood_check_in` learning event. Over time, mood patterns are analyzed
(e.g., "this student is usually more productive in evenings" or "this
student gets frustrated after 30+ minutes on the same topic").

### 3.6 Goal Setting

Students can set learning goals with deadlines. Goals are stored in PostgreSQL
and tracked through a progress calculation.

**Goal types:**
- **Mastery goal**: "Master [topic] by [date]" -- tracked via mastery level
- **Time goal**: "Study [N] hours per week" -- tracked via session logs
- **Score goal**: "Achieve [N]% on [subject] quizzes" -- tracked via assessments
- **Completion goal**: "Finish all [course] topics" -- tracked via topic coverage

**Progress tracking:**
- Each session, the system calculates progress toward each active goal
- If a student is falling behind pace, the system proactively mentions it:
  "You wanted to master integration by March 15. At your current pace, you'll
  need about 2 more sessions per week to hit that. Want to adjust the goal
  or the schedule?"

### 3.7 Achievement Badges / Milestones

Badges are lightweight gamification elements that reward positive behaviors.
They are stored as JSONB arrays on the student profile.

**Badge categories:**

| Category | Badge | Trigger |
|---|---|---|
| Consistency | First Session | Complete first tutoring session |
| Consistency | Week Warrior | 7-day streak |
| Consistency | Month Master | 30-day streak |
| Mastery | First Mastery | Any topic reaches 0.95+ |
| Mastery | Subject Scholar | All topics in a subject reach 0.80+ |
| Assessment | Quiz Ace | Score 100% on any quiz |
| Assessment | Comeback Kid | Improve quiz score by 30%+ on retry |
| Engagement | Night Owl | 10 sessions after 10pm |
| Engagement | Early Bird | 10 sessions before 8am |
| Engagement | Centurion | 100 total sessions |
| Social | Help a Friend | (future: share explanation with peer) |
| Growth | Growth Mindset | Retried a failed topic 3+ times |

Badges appear as a brief celebration notification when earned and are
visible on the student's profile/dashboard.

### 3.8 "Forget This" -- Topic Reset

Students can ask EduAGI to reset their mastery on a specific topic. This is
useful when a student feels the system is overestimating their understanding
or when they want to relearn something from scratch.

**Flow:**
1. Student says "I want to start over on [topic]" or uses a settings toggle
2. System confirms: "This will reset your mastery on [topic] to zero and
   remove it from your strengths. Your learning history will be kept but
   won't influence future difficulty. Are you sure?"
3. If confirmed:
   - `mastery_map[topic]` set to 0.00
   - Topic removed from strengths/weaknesses lists (will be recalculated)
   - Spaced repetition queue entry removed for this topic
   - A `topic_reset` learning event is logged (history is preserved)
   - ChromaDB entries for this topic are NOT deleted (past approaches that
     worked are still useful when re-teaching)

### 3.9 Privacy Controls

Students have full visibility and control over their data.

**Available controls:**
- **View my data**: See everything EduAGI knows about them, presented in a
  friendly dashboard (not raw JSON)
- **Download my data**: Export all data as a structured JSON file (GDPR right
  of data portability). Also available as a PDF report (see 3.10).
- **Delete specific data**: Remove individual learning events, session logs,
  or quiz results. This triggers actual deletion from PostgreSQL and ChromaDB.
- **Delete all my data**: Nuclear option. Removes all profile data, learning
  events, session histories, and ChromaDB embeddings. Confirmation required
  with a 7-day grace period (can undo within 7 days).
- **Data sharing level**:
  - "Full" -- teacher/institution can see progress reports
  - "Summary only" -- teacher sees grades and mastery levels, not session logs
  - "Minimal" -- teacher sees only quiz grades
  - "None" -- no data shared (student is fully private)

All privacy actions are logged in an audit trail for compliance.

### 3.10 Export Learning History (PDF Report)

Students can generate a PDF report of their learning history. The report
includes:

- Profile summary (learning style, preferences)
- Mastery map visualization (all subjects and topics with levels)
- Progress over time chart (mastery trends per topic)
- Quiz score history
- Study time statistics
- Achievement badges earned
- Goal progress
- Strengths and areas for improvement
- Recommended next steps

The PDF is generated server-side using a templating library (WeasyPrint or
ReportLab) and returned as a downloadable file. Generation is asynchronous
for large histories (queued as a background job).

### 3.11 Parent/Guardian View

For students under 18, a parent/guardian account can be linked. The parent
view is a read-only dashboard that shows:

- Study time this week
- Current streak
- Mastery levels per subject (high-level, not per-topic)
- Recent quiz scores
- Goal progress
- Active topics being studied
- Session frequency

The parent view does NOT show:
- Individual conversation transcripts (privacy)
- Mood/energy data (student's personal information)
- Specific wrong answers or mistakes
- Anything the student has marked as private

**Linking flow:**
1. Student (or parent) initiates link from settings
2. An invitation code is generated (valid for 48 hours)
3. Parent creates account and enters code
4. Student must approve the link (for students age 13+)
5. Parent gets read-only access to the dashboard

### 3.12 Device Sync

All session state that matters for continuity is stored server-side (Redis +
PostgreSQL + ChromaDB), not in the browser or device. This means:

- Student starts studying on their laptop at home
- Closes the laptop mid-session
- Opens the phone app on the bus
- EduAGI restores the full session context: "Looks like you were working
  on [topic] on your other device. Want to pick up where you left off?"

**Technical approach:**
- Session state lives in Redis with a TTL of 24 hours
- When a new device connects, it checks for an active session in Redis
- If found, it offers to resume or start fresh
- If the student starts a new session on the new device, the old session
  is closed and consolidated to PostgreSQL
- Concurrent sessions on multiple devices are NOT supported (last device
  wins, with a graceful notification on the old device)

---

## 4. Technical Requirements

### 4.1 Redis Configuration

**Purpose:** Working memory -- active session state, profile cache, real-time
data.

**Key patterns:**

```
  KEY PATTERN                              TYPE       TTL
  ───────────────────────────────────────  ─────────  ────────
  session:{session_id}:context             Hash       24 hours
  session:{session_id}:messages            List       24 hours
  session:{session_id}:scratchpad          Hash       24 hours
  profile:{student_id}                     Hash       1 hour
  profile:{student_id}:mastery             Hash       1 hour
  streak:{student_id}                      String     48 hours
  mood:{student_id}:current                String     24 hours
  spaced_rep:{student_id}:due              SortedSet  7 days
  active_session:{student_id}              String     24 hours
  rate_limit:llm:{student_id}             String     60 sec
```

**Memory limits:**
- Max memory per student session: ~100KB (50 messages at ~2KB each)
- Max Redis instance memory: 2GB (supports ~20,000 concurrent sessions)
- Eviction policy: `allkeys-lru` (least recently used sessions evicted first)
- Persistence: RDB snapshots every 5 minutes (session loss on crash is
  acceptable -- sessions can be reconstructed from PostgreSQL)

**Configuration:**

```
  maxmemory 2gb
  maxmemory-policy allkeys-lru
  save 300 1
  tcp-keepalive 60
  timeout 300
```

### 4.2 PostgreSQL Schema for Episodic Memory

The core tables for student memory (extends the base schema from TECHNICAL_DESIGN):

```
  TABLE: student_profiles
  ──────────────────────────────────────────────────────────────
  Column                  Type            Notes
  ──────────────────────  ──────────────  ─────────────────────
  id                      UUID PK         gen_random_uuid()
  user_id                 UUID FK->users  ON DELETE CASCADE
  learning_style          VARCHAR(50)     visual/auditory/etc
  secondary_style         VARCHAR(50)     nullable
  pace                    VARCHAR(50)     slow/moderate/fast
  grade_level             VARCHAR(50)
  attention_span_minutes  INTEGER         default 25
  strengths               TEXT[]          topic names
  weaknesses              TEXT[]          topic names
  mastery_map             JSONB           {topic: decimal}
  goals                   JSONB           [{goal, deadline, progress}]
  preferences             JSONB           {voice, avatar, theme...}
  engagement              JSONB           {streak, badges, hours...}
  mood_patterns           JSONB           {avg_mood, best_time...}
  style_weights           JSONB           {visual:0.7, reading:0.2..}
  created_at              TIMESTAMP       default NOW()
  updated_at              TIMESTAMP       default NOW()

  INDEXES:
  - idx_profiles_user_id ON student_profiles(user_id)
  - idx_profiles_updated ON student_profiles(updated_at)


  TABLE: learning_events
  ──────────────────────────────────────────────────────────────
  Column                  Type            Notes
  ──────────────────────  ──────────────  ─────────────────────
  id                      UUID PK         gen_random_uuid()
  student_id              UUID FK->users  ON DELETE CASCADE
  session_id              UUID            nullable (FK->sessions)
  event_type              VARCHAR(50)     NOT NULL
  subject                 VARCHAR(100)    nullable
  topic                   VARCHAR(255)    nullable
  data                    JSONB           event-specific payload
  outcome                 VARCHAR(50)     success/failure/partial
  mastery_before          DECIMAL(4,3)    nullable
  mastery_after           DECIMAL(4,3)    nullable
  created_at              TIMESTAMP       default NOW()

  INDEXES:
  - idx_events_student ON learning_events(student_id)
  - idx_events_student_type ON learning_events(student_id, event_type)
  - idx_events_student_subject ON learning_events(student_id, subject)
  - idx_events_created ON learning_events(created_at)
  - idx_events_topic ON learning_events(topic)

  PARTITIONING:
  - Partitioned by created_at (monthly partitions)
  - Older partitions (>6 months) moved to cold storage


  TABLE: spaced_repetition_queue
  ──────────────────────────────────────────────────────────────
  Column                  Type            Notes
  ──────────────────────  ──────────────  ─────────────────────
  id                      UUID PK
  student_id              UUID FK->users
  topic                   VARCHAR(255)    NOT NULL
  subject                 VARCHAR(100)    NOT NULL
  next_review_date        DATE            NOT NULL
  interval_days           INTEGER         current interval
  review_count            INTEGER         number of reviews done
  last_score              DECIMAL(4,3)    last review score
  created_at              TIMESTAMP
  updated_at              TIMESTAMP

  INDEXES:
  - idx_sr_student_date ON spaced_repetition_queue(student_id, next_review_date)


  TABLE: student_goals
  ──────────────────────────────────────────────────────────────
  Column                  Type            Notes
  ──────────────────────  ──────────────  ─────────────────────
  id                      UUID PK
  student_id              UUID FK->users
  goal_type               VARCHAR(50)     mastery/time/score/completion
  description             TEXT            student's own words
  target_value            DECIMAL(10,2)   target number
  current_value           DECIMAL(10,2)   current progress
  subject                 VARCHAR(100)    nullable
  topic                   VARCHAR(255)    nullable
  deadline                DATE            nullable
  status                  VARCHAR(50)     active/completed/abandoned
  created_at              TIMESTAMP
  completed_at            TIMESTAMP       nullable


  TABLE: privacy_audit_log
  ──────────────────────────────────────────────────────────────
  Column                  Type            Notes
  ──────────────────────  ──────────────  ─────────────────────
  id                      UUID PK
  student_id              UUID FK->users
  action                  VARCHAR(100)    view/export/delete/share_change
  details                 JSONB           what was accessed/changed
  ip_address              VARCHAR(45)     for audit trail
  created_at              TIMESTAMP       NOT NULL
```

### 4.3 ChromaDB Collections for Student-Specific Knowledge

Each student gets a dedicated collection for personalized context. A global
collection is shared for curriculum knowledge.

```
  COLLECTION: student_{student_id}_context
  ──────────────────────────────────────────────────────────────
  Purpose: Store student-specific learning context embeddings

  Document types:
  - effective_explanation:   What explanation approaches worked
  - failed_explanation:      What approaches did NOT work
  - student_misconception:   Known misconceptions and corrections
  - student_insight:         Student's own understanding expressed
  - cross_topic_connection:  Links between topics the student has made
  - session_summary:         Compressed session narratives

  Metadata fields (on every document):
  - type:          string   (one of the above types)
  - topic:         string   (related topic)
  - subject:       string   (related subject)
  - effectiveness: float    (0.0-1.0, for explanation types)
  - timestamp:     string   (ISO 8601)
  - session_id:    string   (which session generated this)
  - avoid:         boolean  (true if this approach should be avoided)

  Embedding model: text-embedding-ada-002 (or comparable open-source)
  Distance metric: cosine similarity
  Expected size: 50-500 documents per student after 3 months of use


  COLLECTION: global_knowledge_base
  ──────────────────────────────────────────────────────────────
  Purpose: Shared curriculum content for RAG retrieval
  (Not student-specific -- see ARCHITECTURE.md for details)
```

### 4.4 Session State Management

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE                                    │
│                                                                         │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ CREATE  │──>│  ACTIVE  │──>│ CLOSING  │──>│ CLOSED   │            │
│  └─────────┘   └──────────┘   └──────────┘   └──────────┘            │
│       │             │              │              │                     │
│       │             │              │              │                     │
│  Profile loaded  Messages     Summarize via   Events saved             │
│  Redis populated exchanged    LLM. Flush to   to PostgreSQL.           │
│  Session row     Micro-updates PostgreSQL.     Redis keys              │
│  in PostgreSQL   to Redis     Update mastery.  expired or              │
│                               Update profile.  deleted.                │
│                                                                         │
│  SESSION TIMEOUT                                                       │
│  ───────────────                                                       │
│  If no activity for 30 minutes, session auto-closes:                   │
│  - Background worker checks session:{id}:last_activity timestamp      │
│  - If stale, triggers the CLOSING flow automatically                   │
│  - Student is notified on next visit that session was saved            │
│                                                                         │
│  CONCURRENT SESSION HANDLING                                           │
│  ──────────────────────────                                            │
│  Only one active session per student at a time.                        │
│  If student opens a new session while one is active:                   │
│  - Old session is force-closed and consolidated                        │
│  - New session is created with context from old session                │
│  - Tracked via active_session:{student_id} key in Redis               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.5 Data Encryption at Rest (FERPA Compliance)

EduAGI handles student educational records, which fall under FERPA (Family
Educational Rights and Privacy Act) and potentially COPPA (for students under
13).

**Encryption requirements:**

| Data Store | Encryption Method | Key Management |
|---|---|---|
| PostgreSQL | TDE (Transparent Data Encryption) via `pgcrypto` + disk-level AES-256 | AWS KMS or HashiCorp Vault |
| Redis | TLS in transit + encrypted EBS volumes at rest | AWS KMS |
| ChromaDB | Encrypted disk volumes (AES-256) | AWS KMS |
| S3/MinIO (exports) | SSE-S3 or SSE-KMS server-side encryption | AWS KMS |
| Backups | AES-256 encryption before upload to backup storage | Separate backup key in Vault |

**PII fields requiring column-level encryption in PostgreSQL:**
- `users.email`
- `users.name`
- `student_profiles.preferences` (may contain identifying data)
- `privacy_audit_log.ip_address`

Encrypted using `pgcrypto` extension with application-level key.

**Access controls:**
- Database credentials rotated every 90 days
- Application uses connection pooling with least-privilege roles
- All database queries go through parameterized prepared statements (no raw SQL)
- Admin access to production data requires 2-person approval

### 4.6 GDPR Data Export / Deletion Endpoints

**Data Export (Right of Portability):**
- Endpoint: `GET /api/v1/privacy/export`
- Returns: JSON file containing all student data, or initiates async PDF
  generation
- Response time: immediate for JSON (<5s), async for PDF (queued, notified
  when ready)
- Format follows a standardized schema so data could theoretically be imported
  into another system

**Data Deletion (Right to Erasure):**
- Endpoint: `DELETE /api/v1/privacy/data`
- Options: `scope=all` (full deletion) or `scope=selective&type=sessions` etc.
- Full deletion process:
  1. Mark account as `pending_deletion` (7-day grace period)
  2. Immediately stop collecting new data
  3. After 7 days, permanently delete from:
     - PostgreSQL: all rows in student_profiles, learning_events,
       spaced_repetition_queue, student_goals, privacy_audit_log, sessions,
       submissions, question_grades
     - Redis: all keys matching `*:{student_id}:*`
     - ChromaDB: delete collection `student_{student_id}_context`
     - S3: delete any exported files
  4. Retain a single anonymized record: `{deleted_user_id: hash, deleted_at: timestamp}`
     for audit compliance
- Selective deletion follows the same process but scoped to specific tables/types
- All deletions are logged in an immutable audit log (separate from
  privacy_audit_log, which gets deleted with the user)

### 4.7 Backup Strategy

| Component | Backup Method | Frequency | Retention | Recovery Time |
|---|---|---|---|---|
| PostgreSQL | pg_dump + WAL archiving | Continuous WAL, daily full | 30 days full, 7 days WAL | <15 min (point-in-time) |
| Redis | RDB snapshots + AOF | RDB every 5 min, AOF continuous | 7 days | <5 min |
| ChromaDB | Collection export + volume snapshots | Daily | 30 days | <30 min |
| S3/MinIO | Cross-region replication | Continuous | Indefinite | <5 min |

**Disaster recovery:**
- RPO (Recovery Point Objective): 5 minutes (worst case data loss)
- RTO (Recovery Time Objective): 30 minutes (time to full restoration)
- Tested quarterly with simulated failures

---

## 5. Services & Alternatives

For each component of the memory system, we evaluate the chosen technology
against alternatives.

### 5.1 Working Memory: Redis vs Memcached vs DragonflyDB

| Criterion | Redis | Memcached | DragonflyDB |
|---|---|---|---|
| **Data structures** | Rich (hash, list, sorted set, stream) | Key-value only | Redis-compatible |
| **Persistence** | RDB + AOF | None | Snapshots |
| **TTL support** | Per-key TTL | Per-key TTL | Per-key TTL |
| **Pub/Sub** | Yes (for session events) | No | Yes |
| **Memory efficiency** | Good | Better for simple KV | Excellent (25x less memory claimed) |
| **Clustering** | Redis Cluster / Sentinel | Consistent hashing | Built-in multi-threaded |
| **Maturity** | Very mature, massive ecosystem | Very mature | Newer (2022+), growing |
| **Managed options** | AWS ElastiCache, Redis Cloud | AWS ElastiCache | Self-hosted primarily |
| **Our use case fit** | Excellent -- we need lists, hashes, sorted sets, TTL, pub/sub | Poor -- too simple for our needs | Good -- but less ecosystem support |

**Decision: Redis**
Rationale: We need rich data structures (lists for message history, hashes for
session context, sorted sets for spaced repetition queues). Memcached is too
simple. DragonflyDB is promising but lacks the managed cloud options and
ecosystem maturity we need at launch. Redis is the industry standard for this
use case.

### 5.2 Episodic Memory: PostgreSQL vs MongoDB vs DynamoDB

| Criterion | PostgreSQL | MongoDB | DynamoDB |
|---|---|---|---|
| **Schema** | Structured with JSONB flexibility | Schema-less | Schema-less |
| **JSONB support** | Excellent native support | Native (BSON) | Native (JSON) |
| **Querying** | Full SQL + JSONB operators | MQL | Limited (key-value + GSI) |
| **Aggregations** | Excellent (window functions, CTEs) | Aggregation pipeline | Limited |
| **Partitioning** | Native table partitioning | Sharding | Automatic |
| **ACID compliance** | Full ACID | Document-level | Item-level |
| **Joins** | Full SQL joins | $lookup (limited) | None |
| **Ecosystem** | Massive (pgcrypto, PostGIS, etc.) | Large | AWS-only |
| **Cost at scale** | Predictable | Predictable | Can spike unpredictably |
| **Managed options** | AWS RDS, Supabase, Neon | MongoDB Atlas | AWS native |

**Decision: PostgreSQL**
Rationale: We need strong querying for analytics (mastery trends, progress
reports), ACID compliance for student records, table partitioning for scaling
learning_events over time, and JSONB for flexible event payloads. PostgreSQL
gives us the best of both structured and semi-structured worlds. MongoDB would
work but we lose powerful SQL analytics. DynamoDB's query limitations would
force us to add a separate analytics database.

### 5.3 Session Store: Redis vs PostgreSQL Sessions vs JWT-Only

| Criterion | Redis Sessions | PostgreSQL Sessions | JWT-Only |
|---|---|---|---|
| **Speed** | Sub-millisecond | 5-20ms | Zero (no lookup) |
| **Server state** | Stateful | Stateful | Stateless |
| **Session data size** | Unlimited (practical: MBs) | Unlimited | ~4KB (cookie limit) |
| **Revocation** | Instant (delete key) | Instant (delete row) | Difficult (need blocklist) |
| **Scalability** | Excellent | Good | Excellent |
| **Persistence** | Configurable | Full | N/A (client-side) |
| **Our needs** | Full session context for tutoring | Could work but slower | Cannot hold conversation state |

**Decision: Redis for session state, JWT for authentication**
Rationale: We use a hybrid approach. JWT tokens handle authentication (who is
this user?). Redis handles session state (what are they doing right now?). We
need to store conversation history, scratchpad, and real-time context in the
session -- far too much data for a JWT. But we do not want Redis to handle
auth because we need auth to work even if Redis is temporarily down.

### 5.4 Analytics: Custom vs Mixpanel vs Amplitude

| Criterion | Custom (PostgreSQL + Grafana) | Mixpanel | Amplitude |
|---|---|---|---|
| **Data ownership** | Full ownership | Third-party | Third-party |
| **FERPA compliance** | We control it | BAA available | BAA available |
| **Cost** | Infrastructure cost only | $25+/mo per 1K MTUs | $49+/mo |
| **Customization** | Unlimited | Limited to their model | Limited to their model |
| **Learning-specific metrics** | We build exactly what we need | Generic events | Generic events |
| **Integration with memory** | Native (same PostgreSQL) | API calls required | API calls required |
| **Setup effort** | Higher (build dashboards) | Lower (pre-built) | Lower (pre-built) |

**Decision: Custom analytics built on PostgreSQL + Grafana**
Rationale: Our analytics are deeply tied to learning events and mastery
calculations that already live in PostgreSQL. Using an external service would
require duplicating data, introducing FERPA compliance complexity with a
third party, and would not give us the learning-specific metrics we need
(mastery trends, spaced repetition effectiveness, learning style correlation).
We build our own dashboards with Grafana for internal monitoring and custom
React components for student-facing analytics.

### 5.5 Gamification: Custom vs Badgeville vs Open Badges

| Criterion | Custom | Badgeville (SAP) | Open Badges (Mozilla) |
|---|---|---|---|
| **Cost** | Development time only | Enterprise pricing | Free standard |
| **Flexibility** | Full control over rules | Configurable | Badge spec only |
| **Integration** | Native to our system | API integration | API integration |
| **Learning-specific** | We design for education | Generic gamification | Designed for credentials |
| **Portability** | Internal only | Proprietary | Portable (IMS standard) |
| **Complexity** | Simple (we need ~20 badges) | Overkill for our needs | Good for formal credentials |

**Decision: Custom gamification with Open Badges export capability**
Rationale: Our gamification needs are modest (streaks, badges, milestones) and
deeply integrated with our memory system (badge triggers come from mastery
changes, session counts, quiz scores). A third-party gamification engine would
be overkill and add unnecessary complexity. However, we plan to adopt the Open
Badges specification for exporting badges as verifiable credentials in Phase 2,
so students can share their achievements externally.

---

## 6. Connections & Dependencies

### 6.1 How Memory Feeds Every Other Feature

```
┌─────────────────────────────────────────────────────────────────────────┐
│            MEMORY AS THE FOUNDATION FOR ALL FEATURES                   │
│                                                                         │
│                    ┌──────────────────────┐                             │
│                    │   STUDENT MEMORY     │                             │
│                    │   & PROFILES         │                             │
│                    │                      │                             │
│                    │  Profile + Mastery   │                             │
│                    │  + History + Context │                             │
│                    └──────────┬───────────┘                             │
│                               │                                         │
│       ┌───────────┬───────────┼───────────┬───────────┐                │
│       │           │           │           │           │                │
│       ▼           ▼           ▼           ▼           ▼                │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ F01:    │ │ F02:    │ │ F04:    │ │ F05:    │ │ F06:    │        │
│  │ TUTOR   │ │ ASSESS  │ │ VOICE   │ │ AVATAR  │ │ SIGN    │        │
│  │ AGENT   │ │ AGENT   │ │ AGENT   │ │ AGENT   │ │ LANG    │        │
│  │         │ │         │ │         │ │         │ │ AGENT   │        │
│  │ Uses:   │ │ Uses:   │ │ Uses:   │ │ Uses:   │ │ Uses:   │        │
│  │-Learning│ │-Mastery │ │-Voice   │ │-Avatar  │ │-Sign    │        │
│  │ style   │ │ levels  │ │ pref   │ │ pref   │ │ lang    │        │
│  │-Mastery │ │-Weakness│ │-Tone   │ │-Student │ │ pref   │        │
│  │-What    │ │-History │ │ based  │ │ name   │ │-Content │        │
│  │ works   │ │-Goals   │ │ on mood│ │-Session │ │ adapted │        │
│  │-Pace    │ │-Pace    │ │        │ │ context│ │ to level│        │
│  │-Context │ │         │ │        │ │        │ │        │        │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
│                                                                         │
│  WITHOUT MEMORY, EVERY FEATURE DEGRADES:                               │
│                                                                         │
│  Tutor without memory  = Generic chatbot. No personalization.          │
│  Assessment without memory = Wrong difficulty. Redundant questions.    │
│  Voice without memory = Same robotic tone for everyone.                │
│  Avatar without memory = No continuity in presentation.                │
│  Sign lang without memory = No adaptation to student's level.         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Data Flow Between All 3 Memory Tiers

```
┌─────────────────────────────────────────────────────────────────────────┐
│              DATA FLOW BETWEEN MEMORY TIERS                            │
│                                                                         │
│                                                                         │
│                        ┌───────────────────┐                           │
│                        │   STUDENT ACTION  │                           │
│                        │   (message, quiz, │                           │
│                        │    login, etc.)   │                           │
│                        └────────┬──────────┘                           │
│                                 │                                       │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                    TIER 1: REDIS (Working Memory)             │      │
│  │                                                               │      │
│  │  READS from:                 WRITES to:                      │      │
│  │  - Own cache (fastest)       - Session state                 │      │
│  │  - Tier 2 on cache miss      - Message history               │      │
│  │  - Tier 3 for context        - Scratchpad                    │      │
│  │                               - Micro-update signals         │      │
│  │                                                               │      │
│  │  Data here is EPHEMERAL. If Redis dies, we rebuild from      │      │
│  │  Tier 2. Inconvenient but not catastrophic.                  │      │
│  └────────────────────┬─────────────────────────────────────────┘      │
│                       │                                                 │
│              On session end,                                            │
│              timeout, or                                                │
│              periodic flush                                             │
│              (every 5 min)                                              │
│                       │                                                 │
│                       ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                TIER 2: POSTGRESQL (Episodic Memory)           │      │
│  │                                                               │      │
│  │  READS from:                 WRITES to:                      │      │
│  │  - Own tables (on cache      - learning_events (append)      │      │
│  │    miss from Tier 1)         - student_profiles (update)     │      │
│  │  - Used by analytics         - spaced_repetition_queue       │      │
│  │    dashboards directly       - student_goals                 │      │
│  │                               - sessions                     │      │
│  │                                                               │      │
│  │  Data here is PERMANENT and STRUCTURED. Source of truth       │      │
│  │  for all historical data and profile state.                  │      │
│  └────────────────────┬─────────────────────────────────────────┘      │
│                       │                                                 │
│              After session                                              │
│              summary generated,                                         │
│              effective/failed                                            │
│              approaches identified                                      │
│                       │                                                 │
│                       ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                TIER 3: CHROMADB (Semantic Memory)             │      │
│  │                                                               │      │
│  │  READS from:                 WRITES to:                      │      │
│  │  - Queried by tutor agent    - Effective explanations        │      │
│  │    before every response     - Failed approaches             │      │
│  │  - "What works for this      - Misconceptions               │      │
│  │    student on this topic?"   - Student insights              │      │
│  │                               - Session summaries            │      │
│  │                                                               │      │
│  │  Data here is QUALITATIVE and SEARCHABLE by meaning.         │      │
│  │  It answers "what kind of teaching works for this student?"  │      │
│  └──────────────────────────────────────────────────────────────┘      │
│                                                                         │
│                                                                         │
│  FLOW DIRECTION SUMMARY:                                               │
│                                                                         │
│  Hot path (every exchange):                                            │
│    Redis READ -> Build prompt -> LLM -> Redis WRITE                    │
│                                                                         │
│  Warm path (session end):                                              │
│    Redis -> Summarize -> PostgreSQL WRITE + ChromaDB WRITE             │
│                                                                         │
│  Cold path (analytics, reports):                                       │
│    PostgreSQL READ -> Compute metrics -> Dashboard/PDF                 │
│                                                                         │
│  Context enrichment (per exchange, async):                             │
│    ChromaDB READ -> Add to system prompt                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.3 What Happens When a Student Returns After Days/Weeks

This section ties together Sections 2.8, 2.9, and 3.2 into a complete
end-to-end flow.

```
┌─────────────────────────────────────────────────────────────────────────┐
│          RETURNING STUDENT -- COMPLETE FLOW (EXAMPLE: 5 DAYS AWAY)    │
│                                                                         │
│  Day 0: Student's last session was 5 days ago.                         │
│         Topic: chain_rule. Mastery at session end: 0.71                │
│                                                                         │
│  Day 5: Student opens EduAGI.                                          │
│                                                                         │
│  STEP 1: Authentication                                                │
│  ───────────────────────                                               │
│  JWT verified. User ID extracted. No active Redis session found.       │
│                                                                         │
│  STEP 2: Load Profile from PostgreSQL                                  │
│  ────────────────────────────────────                                  │
│  Query student_profiles for full profile.                              │
│  Query learning_events for last session summary.                       │
│  Query spaced_repetition_queue for due topics.                         │
│  Cache all of this in Redis at profile:{student_id}.                   │
│                                                                         │
│  STEP 3: Apply Time Decay                                              │
│  ────────────────────────                                              │
│  chain_rule mastery: 0.71                                              │
│  Decay: 0.05 * ln(5 + 1) = 0.05 * 1.79 = 0.09                       │
│  Adjusted mastery: 0.71 - 0.09 = 0.62                                │
│  (Decay is provisional -- will be confirmed or overridden by          │
│   review quiz results)                                                 │
│                                                                         │
│  STEP 4: Check Spaced Repetition Queue                                 │
│  ─────────────────────────────────────                                 │
│  integration_by_parts: due 2 days ago (overdue)                        │
│  limits: due today                                                     │
│  chain_rule: not in queue yet (mastery was below 0.80 threshold)       │
│                                                                         │
│  STEP 5: Generate Welcome Greeting                                     │
│  ─────────────────────────────────                                     │
│  LLM receives:                                                         │
│  - Student name: Sarah                                                 │
│  - Days away: 5                                                        │
│  - Last topic: chain_rule                                              │
│  - Last session summary: "Made progress on chain rule..."             │
│  - Spaced rep due: integration_by_parts, limits                        │
│  - Streak status: broken (was 7, now 0)                                │
│                                                                         │
│  LLM generates:                                                        │
│  "Hey Sarah! It's been a few days -- welcome back! Last time we        │
│   were making good progress on chain rule. I also notice it's been     │
│   a while since we reviewed integration by parts and limits.           │
│   Want to start with a quick refresher on those, or dive back          │
│   into chain rule?"                                                    │
│                                                                         │
│  STEP 6: Create New Session                                            │
│  ──────────────────────────                                            │
│  New session row in PostgreSQL.                                        │
│  New Redis keys for session state.                                     │
│  Profile cached in Redis.                                              │
│  active_session:{student_id} set to new session_id.                    │
│                                                                         │
│  STEP 7: Student Chooses Path                                          │
│  ────────────────────────────                                          │
│  If student picks "refresher on integration by parts":                 │
│   -> 3-question mini-quiz on integration by parts                      │
│   -> Results update mastery and spaced rep interval                    │
│   -> Then transition to chain rule                                     │
│                                                                         │
│  If student picks "dive back into chain rule":                         │
│   -> Start with a warm-up problem to assess current level              │
│   -> If they still remember: mastery decay is partially reversed       │
│   -> If they forgot: mastery stays at decayed level, re-teach          │
│   -> Spaced rep items will be offered later in session or next visit   │
│                                                                         │
│  STEP 8: Session Proceeds Normally                                     │
│  ─────────────────────────────                                         │
│  Every exchange reads/writes Redis.                                    │
│  System prompt includes full profile context.                          │
│  ChromaDB queried for effective approaches.                            │
│  Session ends -> macro-update cycle (Section 2.6).                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Dependency Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEPENDENCY MAP                                     │
│                                                                         │
│  F03 (Student Memory) DEPENDS ON:                                      │
│  ─────────────────────────────────                                     │
│  - Redis infrastructure (working memory)                               │
│  - PostgreSQL infrastructure (episodic memory)                         │
│  - ChromaDB infrastructure (semantic memory)                           │
│  - Authentication system (user identity)                               │
│  - LLM API (for session summarization, style detection)                │
│  - Embedding model (for ChromaDB writes)                               │
│                                                                         │
│  FEATURES THAT DEPEND ON F03:                                          │
│  ─────────────────────────────                                         │
│  - F01 (Tutor Agent): Reads profile for every response                │
│  - F02 (Assessment Agent): Reads mastery for difficulty calibration    │
│  - F04 (Voice Agent): Reads voice preferences and mood                │
│  - F05 (Avatar Agent): Reads avatar preferences                       │
│  - F06 (Sign Language Agent): Reads sign language preference           │
│  - F07 (Analytics/Reporting): Reads all historical data                │
│  - F08 (Content Agent): Reads mastery to recommend next content        │
│  - Frontend dashboard: Reads profile, mastery, streaks, badges         │
│  - Parent view: Reads filtered profile data                            │
│                                                                         │
│  FAILURE MODES:                                                        │
│  ──────────────                                                        │
│  If Redis is down:                                                     │
│  -> Fall back to PostgreSQL for session state (slower but functional) │
│  -> Degrade gracefully: responses will be less contextual              │
│  -> Alert ops team, auto-recovery expected within minutes              │
│                                                                         │
│  If PostgreSQL is down:                                                │
│  -> Active sessions continue using Redis cache (read-only mode)       │
│  -> No new events can be persisted (queued in Redis until PG recovers)│
│  -> No new sessions can be created (no profile loading)               │
│  -> Critical alert to ops team                                         │
│                                                                         │
│  If ChromaDB is down:                                                  │
│  -> Tutoring continues but without personalized approach context       │
│  -> System falls back to learning_style from profile only              │
│  -> Degraded but functional                                            │
│  -> Warning alert to ops team                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| Working Memory | Short-term, fast-access memory (Redis) holding active session state |
| Episodic Memory | Long-term structured memory (PostgreSQL) of learning events |
| Semantic Memory | Vector-based memory (ChromaDB) of qualitative learning context |
| Mastery Level | Decimal 0.00-1.00 representing student understanding of a topic |
| Spaced Repetition | Algorithm-driven review scheduling based on forgetting curves |
| Macro-update | Profile update at end of session (mastery, strengths, weaknesses) |
| Micro-update | Real-time session state update during each exchange |
| Time Decay | Gradual mastery reduction when a topic is not practiced |
| Profile Hydration | Loading full student profile from PostgreSQL into Redis cache |

## Appendix B: Open Questions

1. **Profile versioning**: Should we keep snapshots of the profile over time,
   or is the learning_events log sufficient for historical reconstruction?
   Recommendation: Add monthly profile snapshots.

2. **Multi-student households**: If two students share a device, how do we
   handle fast switching? Recommendation: Require login per session.

3. **Teacher override**: Can a teacher manually adjust a student's mastery
   level? Recommendation: Yes, with an audit log entry.

4. **Data retention limits**: How long do we keep detailed learning_events?
   Recommendation: 2 years detailed, then aggregate and archive.

5. **Offline support**: Should sessions work offline with sync later?
   Recommendation: Defer to Phase 2. Requires significant client-side storage.

---

*Document Version History*
| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | Feb 2026 | AGI Team | Initial feature design |
