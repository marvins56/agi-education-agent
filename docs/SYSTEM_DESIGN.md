# EduAGI - System Design Document
# Complete Architecture, Flows & Feature Design

**Version:** 2.0
**Date:** February 2026
**Status:** Design Phase

---

## Table of Contents

1. [System Vision & Principles](#1-system-vision--principles)
2. [High-Level Architecture](#2-high-level-architecture)
3. [User Journeys & Flows](#3-user-journeys--flows)
4. [Feature Overview (High-Level)](#4-feature-overview)
5. [Detailed Feature Design](#5-detailed-feature-design)
6. [Data Flow Architecture](#6-data-flow-architecture)
7. [Integration Architecture](#7-integration-architecture)
8. [Screen & Interface Flows](#8-screen--interface-flows)

---

## 1. System Vision & Principles

### What EduAGI Actually Is

EduAGI is a **multi-agent AI tutoring platform** that adapts to each student's
learning style, pace, and abilities. It delivers lessons through text, voice,
and visual avatars — with sign language support for deaf/hard-of-hearing students.

### Core Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                     DESIGN PRINCIPLES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. STUDENT-FIRST                                               │
│     Every design decision optimizes for the learner.            │
│     Not the teacher. Not the admin. The student.                │
│                                                                 │
│  2. PROGRESSIVE ENHANCEMENT                                     │
│     Core = text tutoring. Voice, avatar, sign language           │
│     are layers on top. System works without them.               │
│                                                                 │
│  3. MEMORY IS EVERYTHING                                        │
│     The system remembers what you struggle with,                │
│     what works for you, and where you left off.                 │
│     It gets better the more you use it.                         │
│                                                                 │
│  4. GUIDE, DON'T TELL                                           │
│     Socratic method by default. Lead students to                │
│     discover answers, don't hand them out.                      │
│                                                                 │
│  5. ACCESSIBLE BY DEFAULT                                       │
│     Not an afterthought. Sign language, screen readers,         │
│     and multiple modalities are core features.                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### System Boundaries - What EduAGI Is & Isn't

```
  ┌─────────────────────────────┐    ┌─────────────────────────────┐
  │       EduAGI IS             │    │      EduAGI IS NOT          │
  ├─────────────────────────────┤    ├─────────────────────────────┤
  │                             │    │                             │
  │ ✓ Adaptive AI tutor        │    │ ✗ Replacement for teachers  │
  │ ✓ Assessment generator     │    │ ✗ General-purpose AGI       │
  │ ✓ Auto-grader with feedback│    │ ✗ Content creation platform │
  │ ✓ Multi-modal delivery     │    │ ✗ Learning management system│
  │ ✓ Accessibility-first      │    │ ✗ Video conferencing tool   │
  │ ✓ Student progress tracker │    │ ✗ Social learning network   │
  │ ✓ Teaching assistant tool  │    │ ✗ Certification body        │
  │                             │    │                             │
  └─────────────────────────────┘    └─────────────────────────────┘
```

---

## 2. High-Level Architecture

### 2.1 The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                         ┌──────────────┐                                │
│                         │   STUDENTS   │                                │
│                         │  & TEACHERS  │                                │
│                         └──────┬───────┘                                │
│                                │                                        │
│                    ┌───────────┼───────────┐                            │
│                    │           │           │                            │
│               ┌────▼───┐ ┌────▼───┐ ┌────▼───┐                        │
│               │  Web   │ │ Mobile │ │  API   │                        │
│               │  App   │ │  App   │ │ Client │                        │
│               └────┬───┘ └────┬───┘ └────┬───┘                        │
│                    │          │          │                              │
│  ══════════════════╪══════════╪══════════╪══════════════════════════    │
│  PRESENTATION      │          │          │                              │
│  ══════════════════╪══════════╪══════════╪══════════════════════════    │
│                    └──────────┼──────────┘                              │
│                               │                                        │
│                    ┌──────────▼──────────┐                              │
│                    │    API GATEWAY      │                              │
│                    │  Auth + Rate Limit  │                              │
│                    └──────────┬──────────┘                              │
│                               │                                        │
│  ══════════════════════════════╪════════════════════════════════════    │
│  ORCHESTRATION                │                                        │
│  ══════════════════════════════╪════════════════════════════════════    │
│                               │                                        │
│                    ┌──────────▼──────────┐                              │
│                    │  MASTER ORCHESTRATOR │                              │
│                    │                      │                              │
│                    │  "The Brain"         │                              │
│                    │  Routes requests to  │                              │
│                    │  the right agent     │                              │
│                    └──────────┬──────────┘                              │
│                               │                                        │
│  ══════════════════════════════╪════════════════════════════════════    │
│  AGENT LAYER                  │                                        │
│  ══════════════════════════════╪════════════════════════════════════    │
│                               │                                        │
│       ┌───────────┬───────────┼───────────┬───────────┐                │
│       │           │           │           │           │                │
│  ┌────▼────┐ ┌────▼────┐ ┌───▼────┐ ┌────▼────┐ ┌───▼─────┐          │
│  │ TUTOR   │ │ ASSESS  │ │ VOICE  │ │ AVATAR  │ │  SIGN   │          │
│  │ AGENT   │ │ AGENT   │ │ AGENT  │ │ AGENT   │ │ LANGUAGE│          │
│  │         │ │         │ │        │ │         │ │  AGENT  │          │
│  └────┬────┘ └────┬────┘ └───┬────┘ └────┬────┘ └───┬─────┘          │
│       │           │          │           │          │                  │
│  ══════╪═══════════╪══════════╪═══════════╪══════════╪══════════════   │
│  DATA  │           │          │           │          │                  │
│  ══════╪═══════════╪══════════╪═══════════╪══════════╪══════════════   │
│       │           │          │           │          │                  │
│  ┌────▼───────────▼──────────▼───────────▼──────────▼─────┐           │
│  │                    MEMORY SYSTEM                        │           │
│  │  ┌─────────┐   ┌──────────┐   ┌───────────┐            │           │
│  │  │ Working │   │ Episodic │   │ Semantic  │            │           │
│  │  │ (Redis) │   │(Postgres)│   │ (ChromaDB)│            │           │
│  │  └─────────┘   └──────────┘   └───────────┘            │           │
│  └────────────────────────────────────────────────────────┘           │
│                                                                         │
│  ══════════════════════════════════════════════════════════════════     │
│  EXTERNAL SERVICES                                                      │
│  ══════════════════════════════════════════════════════════════════     │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌───────────┐                │
│  │  Claude  │ │ ElevenLabs│ │ DeepBrain│ │Sign-Speak │                │
│  │  (LLM)   │ │  (Voice)  │ │ (Avatar) │ │  (Sign)   │                │
│  └──────────┘ └───────────┘ └──────────┘ └───────────┘                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 How the Orchestrator Routes Requests

```
                        User sends message
                              │
                              ▼
                    ┌─────────────────┐
                    │    ORCHESTRATOR  │
                    │                 │
                    │  1. Classify    │
                    │     intent      │
                    │                 │
                    │  2. Load student│
                    │     context     │
                    │                 │
                    │  3. Route to    │
                    │     agent(s)    │
                    └────────┬────────┘
                             │
              What does the student need?
                             │
         ┌───────────┬───────┴───────┬───────────┐
         │           │               │           │
    "Explain X"  "Quiz me"    "Grade this"  "Show in
                                             sign language"
         │           │               │           │
         ▼           ▼               ▼           ▼
    ┌─────────┐ ┌─────────┐   ┌─────────┐ ┌─────────┐
    │  TUTOR  │ │ ASSESS  │   │ ASSESS  │ │  SIGN   │
    │  AGENT  │ │ AGENT   │   │ AGENT   │ │ LANGUAGE│
    │         │ │ (generate│   │ (grade) │ │  AGENT  │
    └────┬────┘ └────┬────┘   └────┬────┘ └────┬────┘
         │           │              │           │
         │     ┌─────┘              │           │
         │     │                    │           │
         ▼     ▼                    ▼           ▼
    ┌──────────────────────────────────────────────┐
    │          RESPONSE ASSEMBLER                   │
    │                                               │
    │  Combines: text + voice + avatar + sign lang  │
    │  Based on student's delivery preferences      │
    └──────────────────┬───────────────────────────┘
                       │
                       ▼
                 Back to student
```

### 2.3 The Three-Tier Memory Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TIER 1: WORKING MEMORY (Redis)                         │    │
│  │  ─────────────────────────────                          │    │
│  │  What: Current conversation, active session state       │    │
│  │  TTL:  1 hour (per session)                             │    │
│  │  Speed: <1ms reads                                      │    │
│  │                                                         │    │
│  │  Contains:                                              │    │
│  │  • Last 50 messages in current conversation             │    │
│  │  • Current subject/topic being discussed                │    │
│  │  • Active learning objectives                           │    │
│  │  • Temporary notes ("student confused about X")         │    │
│  │                                                         │    │
│  │  Think of it as: SHORT-TERM MEMORY                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                  session ends → persists to ▼                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TIER 2: EPISODIC MEMORY (PostgreSQL)                   │    │
│  │  ────────────────────────────────                       │    │
│  │  What: All past learning events, grades, interactions   │    │
│  │  TTL:  Permanent                                        │    │
│  │  Speed: <50ms reads                                     │    │
│  │                                                         │    │
│  │  Contains:                                              │    │
│  │  • Every tutoring session summary                       │    │
│  │  • All quiz results and grades                          │    │
│  │  • What topics the student covered and when             │    │
│  │  • What teaching approaches worked/failed               │    │
│  │  • Student's learning trajectory over time              │    │
│  │                                                         │    │
│  │  Think of it as: LIFE EXPERIENCE MEMORY                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                          │                                      │
│                  feeds into ▼                                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TIER 3: SEMANTIC MEMORY (ChromaDB)                     │    │
│  │  ──────────────────────────────                         │    │
│  │  What: Knowledge base, curriculum content, embeddings   │    │
│  │  TTL:  Permanent (updated when content changes)         │    │
│  │  Speed: <100ms reads                                    │    │
│  │                                                         │    │
│  │  Contains:                                              │    │
│  │  • Textbook content (chunked & embedded)                │    │
│  │  • Curriculum-aligned knowledge                         │    │
│  │  • Previously generated good explanations               │    │
│  │  • Fact-checked reference material                      │    │
│  │                                                         │    │
│  │  Think of it as: TEXTBOOK KNOWLEDGE                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. User Journeys & Flows

### 3.1 First-Time Student Onboarding

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  SIGN UP │────▶│ PROFILE  │────▶│ LEARNING │────▶│  FIRST   │
│          │     │  SETUP   │     │  STYLE   │     │  LESSON  │
│ email +  │     │          │     │ DETECTION│     │          │
│ password │     │ name,    │     │          │     │ guided   │
│          │     │ grade,   │     │ short    │     │ tutorial │
│          │     │ subjects │     │ adaptive │     │ with the │
│          │     │          │     │ quiz     │     │ AI tutor │
└──────────┘     └──────────┘     └──────────┘     └──────────┘

LEARNING STYLE DETECTION FLOW (Detail):

    Student answers 10-15 adaptive questions
                    │
                    ▼
    ┌───────────────────────────────┐
    │  System analyzes:             │
    │  • Response patterns          │
    │  • Time spent per question    │
    │  • Types of help requested    │
    │  • Preferred answer formats   │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  Assigns learning profile:    │
    │                               │
    │  Style:  visual / auditory /  │
    │          kinesthetic / reading │
    │                               │
    │  Pace:   slow / moderate /    │
    │          fast                  │
    │                               │
    │  Level:  based on quiz score  │
    └───────────────┬───────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  Configures delivery prefs:   │
    │                               │
    │  □ Enable voice explanations  │
    │  □ Enable avatar presenter    │
    │  □ Enable sign language       │
    │  □ Preferred language         │
    └───────────────────────────────┘
```

### 3.2 Core Tutoring Session Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 TUTORING SESSION LIFECYCLE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  START SESSION                                                  │
│  ─────────────                                                  │
│  Student picks subject + topic (or continues where they left)   │
│       │                                                         │
│       ▼                                                         │
│  ┌────────────────────────────────────────────┐                 │
│  │  CONTEXT LOADING                            │                 │
│  │                                             │                 │
│  │  System loads:                              │                 │
│  │  1. Student profile (style, pace, level)    │                 │
│  │  2. Past sessions on this topic             │                 │
│  │  3. Known strengths & weaknesses            │                 │
│  │  4. Where they left off last time           │                 │
│  │  5. Relevant curriculum content (RAG)       │                 │
│  └────────────────────┬───────────────────────┘                 │
│                       │                                         │
│                       ▼                                         │
│  ┌─────────────────────────────────────────────────────┐        │
│  │                                                     │        │
│  │   ┌──────────────────────────────────────────┐      │        │
│  │   │         CONVERSATION LOOP                │      │        │
│  │   │                                          │      │        │
│  │   │  Student asks / responds                 │      │        │
│  │   │         │                                │      │        │
│  │   │         ▼                                │      │        │
│  │   │  ┌─────────────────────┐                 │      │        │
│  │   │  │ INTENT DETECTION    │                 │      │        │
│  │   │  │                     │                 │      │        │
│  │   │  │ "explain" → teach   │                 │      │        │
│  │   │  │ "quiz me" → assess  │                 │      │        │
│  │   │  │ "I don't get" → re  │                 │      │        │
│  │   │  │   -explain simpler  │                 │      │        │
│  │   │  │ "next" → advance    │                 │      │        │
│  │   │  │ "help" → hint       │                 │      │        │
│  │   │  └─────────┬───────────┘                 │      │        │
│  │   │            │                             │      │        │
│  │   │            ▼                             │      │        │
│  │   │  ┌─────────────────────┐                 │      │        │
│  │   │  │ ADAPTIVE RESPONSE   │                 │      │        │
│  │   │  │                     │                 │      │        │
│  │   │  │ • Retrieve relevant │                 │      │        │
│  │   │  │   knowledge (RAG)   │                 │      │        │
│  │   │  │ • Adapt to student  │                 │      │        │
│  │   │  │   learning style    │                 │      │        │
│  │   │  │ • Use Socratic      │                 │      │        │
│  │   │  │   questioning       │                 │      │        │
│  │   │  │ • Check difficulty  │                 │      │        │
│  │   │  │   calibration       │                 │      │        │
│  │   │  └─────────┬───────────┘                 │      │        │
│  │   │            │                             │      │        │
│  │   │            ▼                             │      │        │
│  │   │  ┌─────────────────────┐                 │      │        │
│  │   │  │ MULTI-MODAL OUTPUT  │                 │      │        │
│  │   │  │                     │                 │      │        │
│  │   │  │ Text ──always──▶ ✓  │                 │      │        │
│  │   │  │ Voice ─if pref──▶ ✓ │                 │      │        │
│  │   │  │ Avatar if pref──▶ ✓ │                 │      │        │
│  │   │  │ Sign ──if pref──▶ ✓ │                 │      │        │
│  │   │  └─────────┬───────────┘                 │      │        │
│  │   │            │                             │      │        │
│  │   │            ▼                             │      │        │
│  │   │  ┌─────────────────────┐                 │      │        │
│  │   │  │ COMPREHENSION CHECK │                 │      │        │
│  │   │  │                     │                 │      │        │
│  │   │  │ Every 3-5 exchanges:│                 │      │        │
│  │   │  │ "Can you explain    │                 │      │        │
│  │   │  │  back to me..."     │                 │      │        │
│  │   │  │                     │                 │      │        │
│  │   │  │ If confused → retry │                 │      │        │
│  │   │  │   with simpler      │                 │      │        │
│  │   │  │   approach          │                 │      │        │
│  │   │  │                     │                 │      │        │
│  │   │  │ If got it → advance │                 │      │        │
│  │   │  │   to next concept   │                 │      │        │
│  │   │  └─────────┬───────────┘                 │      │        │
│  │   │            │                             │      │        │
│  │   │            └──── loops back ─────────┘   │      │        │
│  │   │                                          │      │        │
│  │   └──────────────────────────────────────────┘      │        │
│  │                                                     │        │
│  └─────────────────────────────────────────────────────┘        │
│                       │                                         │
│                       ▼                                         │
│  END SESSION                                                    │
│  ───────────                                                    │
│  ┌─────────────────────────────────────────┐                    │
│  │  System saves:                          │                    │
│  │  • Session summary                      │                    │
│  │  • Topics covered + mastery level       │                    │
│  │  • What teaching approach worked        │                    │
│  │  • Updated student profile              │                    │
│  │  • Recommended next topics              │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Assessment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    ASSESSMENT LIFECYCLE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  WHO CAN TRIGGER AN ASSESSMENT?                                 │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ Student  │  │ Teacher  │  │  System  │                      │
│  │ "Quiz me │  │ "Assign  │  │ (auto    │                      │
│  │  on Ch5" │  │  midterm"│  │  after   │                      │
│  └────┬─────┘  └────┬─────┘  │  5 lessons│                     │
│       │              │        └────┬─────┘                      │
│       └──────────────┴─────────────┘                            │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │  STEP 1: ASSESSMENT CONFIGURATION             │              │
│  │                                                │              │
│  │  Assessment Agent determines:                  │              │
│  │  • Subject & topics to cover                   │              │
│  │  • Question types (MCQ, essay, code, math)     │              │
│  │  • Difficulty level (based on student history)  │              │
│  │  • Number of questions                          │              │
│  │  • Time limit (if any)                          │              │
│  │  • Whether adaptive (gets harder/easier)        │              │
│  └───────────────────┬───────────────────────────┘              │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │  STEP 2: QUESTION GENERATION                  │              │
│  │                                                │              │
│  │  For each question:                            │              │
│  │  1. Pull relevant content from knowledge base  │              │
│  │  2. Generate question via Claude               │              │
│  │  3. Generate answer key + rubric               │              │
│  │  4. Validate question quality                  │              │
│  │  5. Calibrate difficulty                       │              │
│  │                                                │              │
│  │  Question Types:                               │              │
│  │  ┌─────────────────────────────────────────┐   │              │
│  │  │ MCQ      → 4 options, 1 correct         │   │              │
│  │  │ Essay    → rubric-based, open-ended     │   │              │
│  │  │ Code     → test cases, auto-run         │   │              │
│  │  │ Math     → step-by-step solution key    │   │              │
│  │  │ T/F      → with explanation required    │   │              │
│  │  │ Fill-in  → exact or semantic match      │   │              │
│  │  └─────────────────────────────────────────┘   │              │
│  └───────────────────┬───────────────────────────┘              │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │  STEP 3: STUDENT TAKES ASSESSMENT             │              │
│  │                                                │              │
│  │  ┌─────────────────────────────────────────┐   │              │
│  │  │  ADAPTIVE MODE (if enabled):            │   │              │
│  │  │                                         │   │              │
│  │  │  Q1 (medium) ──▶ correct                │   │              │
│  │  │       │                                 │   │              │
│  │  │  Q2 (harder) ──▶ correct                │   │              │
│  │  │       │                                 │   │              │
│  │  │  Q3 (hardest) ─▶ wrong                  │   │              │
│  │  │       │                                 │   │              │
│  │  │  Q4 (medium) ──▶ correct                │   │              │
│  │  │       │                                 │   │              │
│  │  │  ...adjusts in real-time                │   │              │
│  │  └─────────────────────────────────────────┘   │              │
│  └───────────────────┬───────────────────────────┘              │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │  STEP 4: AUTO-GRADING                         │              │
│  │                                                │              │
│  │  MCQ/T-F/Fill-in → instant exact match         │              │
│  │  Code → run in sandbox against test cases      │              │
│  │  Math → symbolic solver + step validation      │              │
│  │  Essay → Claude grades against rubric          │              │
│  │                                                │              │
│  │  Each answer gets:                             │              │
│  │  • Score (points earned / points possible)     │              │
│  │  • Specific feedback                           │              │
│  │  • What to review if wrong                     │              │
│  └───────────────────┬───────────────────────────┘              │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────┐              │
│  │  STEP 5: RESULTS & FOLLOW-UP                  │              │
│  │                                                │              │
│  │  Student sees:                                 │              │
│  │  • Overall score + grade                       │              │
│  │  • Per-question feedback                       │              │
│  │  • Strengths identified                        │              │
│  │  • Gaps identified                             │              │
│  │  • "Want to review [weak topic]?" prompt       │              │
│  │                                                │              │
│  │  System updates:                               │              │
│  │  • Student mastery levels per topic            │              │
│  │  • Learning path recommendations              │              │
│  │  • Teacher dashboard (if applicable)           │              │
│  └───────────────────────────────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Multi-Modal Output Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│            HOW A RESPONSE GETS DELIVERED                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Tutor Agent generates text response                            │
│                │                                                │
│                ▼                                                │
│  ┌─────────────────────────┐                                    │
│  │  Check student prefs    │                                    │
│  │                         │                                    │
│  │  voice_enabled?  ──┐    │                                    │
│  │  avatar_enabled? ──┤    │                                    │
│  │  sign_language?  ──┤    │                                    │
│  └─────────────────────┘   │                                    │
│                            │                                    │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                 │
│    voice=true         avatar=true        sign=true             │
│         │                  │                  │                 │
│         ▼                  ▼                  ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │ ElevenLabs  │   │  DeepBrain  │   │ Sign-Speak  │           │
│  │             │   │             │   │             │           │
│  │ text ──▶    │   │ text+audio  │   │ text ──▶    │           │
│  │   audio     │   │ ──▶ video   │   │  sign video │           │
│  │   stream    │   │ with lip-   │   │             │           │
│  │             │   │ sync        │   │             │           │
│  │ ~2-3 sec    │   │ ~15-30 sec  │   │ ~10-20 sec  │           │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘           │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────────────────────────────────────┐               │
│  │            RESPONSE PACKAGE                   │               │
│  │                                               │               │
│  │  {                                            │               │
│  │    text: "Photosynthesis is...",              │               │
│  │    audio_url: "/audio/abc123.mp3",            │               │
│  │    avatar_video_url: "/video/abc123.mp4",     │               │
│  │    sign_language_url: "/sign/abc123.mp4",     │               │
│  │    sources: [...],                            │               │
│  │    suggested_next: "Want to try a quiz?"      │               │
│  │  }                                            │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
│  DELIVERY STRATEGY:                                             │
│  ─────────────────                                              │
│  Text    → sent immediately (streaming)                         │
│  Audio   → sent as stream (plays while generating)              │
│  Avatar  → generated async, notification when ready             │
│  Sign    → generated async, notification when ready             │
│                                                                 │
│  The student sees text FIRST, then audio plays,                 │
│  then avatar/sign video appears when ready.                     │
│  NEVER block text waiting for slower modalities.                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.5 Teacher/Educator Flow

```
  Teacher logs in
       │
       ▼
  ┌─────────────────────────────────┐
  │         TEACHER DASHBOARD       │
  │                                 │
  │  ┌───────────┐ ┌───────────┐   │
  │  │ My Classes│ │ Create    │   │
  │  │           │ │ Assessment│   │
  │  └─────┬─────┘ └─────┬─────┘   │
  │        │              │         │
  │  ┌─────▼─────┐ ┌─────▼─────┐   │
  │  │ Student   │ │ Upload    │   │
  │  │ Progress  │ │ Content   │   │
  │  └─────┬─────┘ └─────┬─────┘   │
  │        │              │         │
  │  ┌─────▼─────┐ ┌─────▼─────┐   │
  │  │ Grade     │ │ Analytics │   │
  │  │ Override  │ │ & Reports │   │
  │  └───────────┘ └───────────┘   │
  └─────────────────────────────────┘

  CONTENT UPLOAD FLOW:
  ────────────────────
  Teacher uploads PDF/DOCX/PPTX
           │
           ▼
  ┌─────────────────┐
  │ Document Parser  │ ← extracts text, images, structure
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Chunk & Embed   │ ← splits into ~1000 token chunks
  └────────┬────────┘   creates vector embeddings
           │
           ▼
  ┌─────────────────┐
  │ Tag & Index     │ ← subject, grade level, topic
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Available in    │ ← RAG can now retrieve this content
  │ Knowledge Base  │   when students ask questions
  └─────────────────┘
```

---

## 4. Feature Overview (High-Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE MAP                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TIER 1 - CORE (MVP)                        Priority   │    │
│  │  ─────────────────────                                  │    │
│  │                                                         │    │
│  │  F1.  Adaptive Text Tutoring                    P0      │    │
│  │  F2.  RAG Knowledge Retrieval                   P0      │    │
│  │  F3.  Student Memory & Profiles                 P0      │    │
│  │  F4.  Assessment Generation                     P0      │    │
│  │  F5.  Auto-Grading with Feedback                P0      │    │
│  │  F6.  Voice Output (ElevenLabs)                 P1      │    │
│  │  F7.  Session Management                        P0      │    │
│  │  F8.  User Auth & Roles                         P0      │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TIER 2 - ENHANCED                          Priority   │    │
│  │  ─────────────────────                                  │    │
│  │                                                         │    │
│  │  F9.  Avatar Presentation                       P1      │    │
│  │  F10. Sign Language Translation                 P1      │    │
│  │  F11. Document Upload & Processing              P1      │    │
│  │  F12. Progress Analytics Dashboard              P1      │    │
│  │  F13. Teacher Dashboard                         P1      │    │
│  │  F14. Learning Path Recommendations             P1      │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  TIER 3 - SCALE                             Priority   │    │
│  │  ─────────────────────                                  │    │
│  │                                                         │    │
│  │  F15. Sign Language Recognition (webcam input)  P2      │    │
│  │  F16. LMS Integration (Canvas, Moodle)          P2      │    │
│  │  F17. Mobile Applications                       P2      │    │
│  │  F18. Collaborative Learning (group sessions)   P2      │    │
│  │  F19. Self-Improving Teaching Strategies         P2      │    │
│  │  F20. Multi-Language Support                    P2      │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Detailed Feature Design

### F1. Adaptive Text Tutoring

**What it does:** The core AI tutor that converses with students, explains concepts,
answers questions, and guides learning using Socratic methods — adapting in real-time
to the student's level and learning style.

**How it works:**

```
┌─────────────────────────────────────────────────────────────────┐
│  F1: ADAPTIVE TUTORING ENGINE                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUTS:                                                        │
│  • Student message                                              │
│  • Student profile (style, pace, level)                         │
│  • Conversation history (last 20 turns)                         │
│  • RAG-retrieved knowledge                                      │
│  • Past session data on this topic                              │
│                                                                 │
│  ADAPTATION DIMENSIONS:                                         │
│                                                                 │
│  1. DIFFICULTY LEVEL                                            │
│     ┌─────────────────────────────────────────┐                 │
│     │  Student keeps getting it right          │                 │
│     │         → increase complexity            │                 │
│     │  Student struggling (2+ wrong)           │                 │
│     │         → simplify, break down           │                 │
│     │  Student asking "what does X mean?"      │                 │
│     │         → too advanced, step back         │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
│  2. TEACHING STYLE (based on learning profile)                  │
│     ┌─────────────────────────────────────────┐                 │
│     │  VISUAL learner:                        │                 │
│     │    → use diagrams, charts, tables       │                 │
│     │    → "imagine it like a tree where..."  │                 │
│     │    → provide visual analogies           │                 │
│     │                                         │                 │
│     │  AUDITORY learner:                      │                 │
│     │    → detailed verbal explanations       │                 │
│     │    → use stories and analogies          │                 │
│     │    → auto-enable voice output           │                 │
│     │                                         │                 │
│     │  KINESTHETIC learner:                   │                 │
│     │    → hands-on examples first            │                 │
│     │    → "try this problem, then we'll..."  │                 │
│     │    → interactive exercises              │                 │
│     │                                         │                 │
│     │  READING/WRITING learner:               │                 │
│     │    → detailed written explanations      │                 │
│     │    → provide references & further reads │                 │
│     │    → structured outlines                │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
│  3. PACING                                                      │
│     ┌─────────────────────────────────────────┐                 │
│     │  SLOW pace:                             │                 │
│     │    → one concept at a time              │                 │
│     │    → lots of check-in questions         │                 │
│     │    → repeat with different wording      │                 │
│     │                                         │                 │
│     │  MODERATE pace:                         │                 │
│     │    → standard progression               │                 │
│     │    → periodic checks                    │                 │
│     │                                         │                 │
│     │  FAST pace:                             │                 │
│     │    → cover multiple concepts            │                 │
│     │    → skip basics if mastered            │                 │
│     │    → challenge with edge cases          │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
│  4. SOCRATIC METHOD                                             │
│     ┌─────────────────────────────────────────┐                 │
│     │  Student: "What is gravity?"            │                 │
│     │                                         │                 │
│     │  BAD (just telling):                    │                 │
│     │  "Gravity is the force that attracts    │                 │
│     │   two bodies toward each other."        │                 │
│     │                                         │                 │
│     │  GOOD (Socratic):                       │                 │
│     │  "When you throw a ball in the air,     │                 │
│     │   what happens to it? Why do you think  │                 │
│     │   it comes back down instead of         │                 │
│     │   floating away?"                       │                 │
│     │                                         │                 │
│     │  Rules:                                 │                 │
│     │  • Ask before telling                   │                 │
│     │  • Build on what student already knows  │                 │
│     │  • Give direct answer only after 3      │                 │
│     │    attempts or if student asks directly  │                 │
│     └─────────────────────────────────────────┘                 │
│                                                                 │
│  OUTPUT:                                                        │
│  • Adaptive text response                                       │
│  • Confidence score (how sure the AI is about its answer)       │
│  • Suggested follow-up actions                                  │
│  • Flags for multi-modal delivery (voice, avatar, sign)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F2. RAG Knowledge Retrieval

**What it does:** Grounds the AI tutor's responses in actual curriculum content,
textbooks, and verified educational material — preventing hallucination.

**How it works:**

```
┌─────────────────────────────────────────────────────────────────┐
│  F2: RAG PIPELINE                                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INGESTION (when content is uploaded):                          │
│                                                                 │
│  PDF/DOCX/PPTX                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Parse   │───▶│  Clean   │───▶│  Chunk   │───▶│  Embed   │  │
│  │          │    │          │    │          │    │          │  │
│  │ extract  │    │ remove   │    │ split to │    │ OpenAI   │  │
│  │ text +   │    │ headers, │    │ ~1000    │    │ ada-002  │  │
│  │ structure│    │ clean    │    │ tokens   │    │ vectors  │  │
│  │          │    │ encoding │    │ with 200 │    │          │  │
│  │          │    │          │    │ overlap  │    │          │  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘  │
│                                                       │        │
│                                              ┌────────▼──────┐ │
│                                              │   ChromaDB    │ │
│                                              │   (indexed    │ │
│                                              │    by subject,│ │
│                                              │    grade,     │ │
│                                              │    topic)     │ │
│                                              └───────────────┘ │
│                                                                 │
│  RETRIEVAL (when student asks a question):                      │
│                                                                 │
│  "How does photosynthesis work?"                                │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Query   │───▶│ Semantic │───▶│  Re-rank │───▶│  Build   │  │
│  │ Rewrite  │    │  Search  │    │  Results │    │  Context │  │
│  │          │    │          │    │          │    │          │  │
│  │ expand   │    │ find top │    │ filter   │    │ combine  │  │
│  │ query    │    │ 10 most  │    │ by grade │    │ top 5    │  │
│  │ with     │    │ similar  │    │ level &  │    │ chunks   │  │
│  │ context  │    │ chunks   │    │ relevance│    │ into     │  │
│  │          │    │          │    │          │    │ prompt   │  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘  │
│                                                       │        │
│                                                       ▼        │
│                                           Goes into the LLM    │
│                                           prompt as grounding   │
│                                           context              │
│                                                                 │
│  ANTI-HALLUCINATION RULES:                                      │
│  • If RAG returns no relevant content → say "I'm not sure,     │
│    let me check" instead of making things up                    │
│  • Always cite which source the answer comes from               │
│  • Confidence score drops if RAG match is weak                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F3. Student Memory & Profiles

**What it does:** Remembers everything about each student — what they've learned,
how they learn best, what they struggle with — and uses it to personalize every
interaction.

```
┌─────────────────────────────────────────────────────────────────┐
│  F3: STUDENT MEMORY SYSTEM                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STUDENT PROFILE (created at onboarding, evolves over time):    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  {                                                      │    │
│  │    id: "student-123",                                   │    │
│  │    name: "Marcus",                                      │    │
│  │    grade_level: "10th grade",                           │    │
│  │                                                         │    │
│  │    learning_style: "visual",       ← detected + adapts  │    │
│  │    pace: "moderate",               ← adjusts over time  │    │
│  │                                                         │    │
│  │    strengths: ["algebra", "logic"],                     │    │
│  │    weaknesses: ["essay writing", "history dates"],      │    │
│  │                                                         │    │
│  │    subjects: {                                          │    │
│  │      "math": {                                          │    │
│  │        mastery: 0.78,              ← 0 to 1 scale      │    │
│  │        topics_completed: 23,                            │    │
│  │        last_session: "2026-02-05",                      │    │
│  │        weak_topics: ["quadratic formula"]               │    │
│  │      },                                                 │    │
│  │      "biology": {                                       │    │
│  │        mastery: 0.45,                                   │    │
│  │        topics_completed: 8,                             │    │
│  │        last_session: "2026-02-03",                      │    │
│  │        weak_topics: ["cell division", "DNA"]            │    │
│  │      }                                                  │    │
│  │    },                                                   │    │
│  │                                                         │    │
│  │    preferences: {                                       │    │
│  │      voice_enabled: true,                               │    │
│  │      avatar_enabled: false,                             │    │
│  │      sign_language: "ASL",                              │    │
│  │      preferred_voice: "friendly_female"                 │    │
│  │    },                                                   │    │
│  │                                                         │    │
│  │    teaching_notes: [                ← what works for    │    │
│  │      "Responds well to analogies",    this student      │    │
│  │      "Needs extra time on word problems",               │    │
│  │      "Gets frustrated with long text - use bullet pts"  │    │
│  │    ]                                                    │    │
│  │  }                                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  HOW THE PROFILE UPDATES:                                       │
│                                                                 │
│  After every session:                                           │
│  ┌────────────────────────────────────────────────┐             │
│  │  Session ends                                  │             │
│  │       │                                        │             │
│  │       ▼                                        │             │
│  │  Analyze session outcomes                      │             │
│  │  • Did student understand the topic?           │             │
│  │  • Which explanations worked?                  │             │
│  │  • Where did they get stuck?                   │             │
│  │  • How long did each concept take?             │             │
│  │       │                                        │             │
│  │       ▼                                        │             │
│  │  Update profile                                │             │
│  │  • Adjust mastery scores                       │             │
│  │  • Update strengths/weaknesses                 │             │
│  │  • Add teaching notes                          │             │
│  │  • Refine learning style if needed             │             │
│  │       │                                        │             │
│  │       ▼                                        │             │
│  │  Next session uses updated profile             │             │
│  └────────────────────────────────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F4 & F5. Assessment Generation + Auto-Grading

**What it does:** Creates quizzes and exams tailored to a student's level,
grades them automatically, and provides detailed constructive feedback.

```
┌─────────────────────────────────────────────────────────────────┐
│  F4/F5: ASSESSMENT & GRADING                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  QUESTION GENERATION BY TYPE:                                   │
│                                                                 │
│  ┌─── MCQ ─────────────────────────────────────────────────┐    │
│  │  Input: topic + difficulty + student level               │    │
│  │  Process:                                                │    │
│  │    1. RAG retrieves relevant content                     │    │
│  │    2. Claude generates question + 4 options              │    │
│  │    3. Distractors target common misconceptions           │    │
│  │    4. Validate: exactly 1 correct, no ambiguity          │    │
│  │  Output: question, options[], correct_answer, explanation│    │
│  │  Grading: exact match → instant                          │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── ESSAY ───────────────────────────────────────────────┐    │
│  │  Input: topic + prompt + rubric criteria                 │    │
│  │  Process:                                                │    │
│  │    1. Generate open-ended prompt                         │    │
│  │    2. Auto-generate rubric (content, structure, clarity) │    │
│  │    3. Set point distribution per criteria                │    │
│  │  Grading:                                                │    │
│  │    Claude evaluates against rubric                       │    │
│  │    → per-criteria score                                  │    │
│  │    → specific feedback ("Your argument about X was       │    │
│  │       strong, but you missed the connection to Y")       │    │
│  │    → improvement suggestions                             │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── CODE ────────────────────────────────────────────────┐    │
│  │  Input: programming task + language + difficulty         │    │
│  │  Process:                                                │    │
│  │    1. Generate problem statement                         │    │
│  │    2. Generate hidden test cases (5-10)                  │    │
│  │    3. Generate starter code (optional)                   │    │
│  │  Grading:                                                │    │
│  │    1. Run student code in Docker sandbox                 │    │
│  │    2. Execute test cases                                 │    │
│  │    3. Score = passed_tests / total_tests                 │    │
│  │    4. Claude reviews code quality + style                │    │
│  │    5. Feedback includes: which tests failed + why        │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─── MATH ────────────────────────────────────────────────┐    │
│  │  Input: math topic + difficulty                          │    │
│  │  Process:                                                │    │
│  │    1. Generate problem with known solution               │    │
│  │    2. Generate step-by-step solution key                 │    │
│  │  Grading:                                                │    │
│  │    1. Check final answer (exact or within tolerance)     │    │
│  │    2. If wrong → Claude checks student's work steps      │    │
│  │    3. Partial credit for correct methodology             │    │
│  │    4. Pinpoint where the mistake happened                │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ADAPTIVE DIFFICULTY FLOW:                                      │
│                                                                 │
│  ┌──────────────────────────────────────────────┐               │
│  │                                              │               │
│  │  Start: MEDIUM difficulty                    │               │
│  │           │                                  │               │
│  │    ┌──────┴──────┐                           │               │
│  │    │  Correct?   │                           │               │
│  │    └──────┬──────┘                           │               │
│  │      YES  │  NO                              │               │
│  │      │    │                                  │               │
│  │      ▼    ▼                                  │               │
│  │   HARDER  EASIER                             │               │
│  │      │    │                                  │               │
│  │      ▼    ▼                                  │               │
│  │    ┌──────┴──────┐                           │               │
│  │    │  Correct?   │                           │               │
│  │    └──────┬──────┘                           │               │
│  │      YES  │  NO                              │               │
│  │      │    │                                  │               │
│  │      ▼    ▼                                  │               │
│  │   HARDER  SAME LEVEL                         │               │
│  │   (max    (give hint,                        │               │
│  │   reached) try again)                        │               │
│  │                                              │               │
│  │  Goal: Find the student's "zone of           │               │
│  │  proximal development" - hard enough to       │               │
│  │  learn, not so hard they give up.             │               │
│  │                                              │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F6. Voice Output (ElevenLabs)

**What it does:** Converts the tutor's text responses into natural-sounding
speech, streamed to the student in real-time.

```
┌─────────────────────────────────────────────────────────────────┐
│  F6: VOICE SYNTHESIS                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FLOW:                                                          │
│                                                                 │
│  Tutor text response ready                                      │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────┐                               │
│  │  TEXT PREPROCESSOR           │                               │
│  │                              │                               │
│  │  • Break into paragraphs     │                               │
│  │  • Handle code blocks        │                               │
│  │    (skip or read as "code    │                               │
│  │     example shows...")       │                               │
│  │  • Handle math notation      │                               │
│  │    (x² → "x squared")       │                               │
│  │  • Handle special chars      │                               │
│  └──────────┬───────────────────┘                               │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────────────┐                               │
│  │  VOICE SELECTION             │                               │
│  │                              │                               │
│  │  Based on:                   │                               │
│  │  • Student preference        │                               │
│  │  • Tone of response:         │                               │
│  │    encouraging → warm voice  │                               │
│  │    explaining → clear voice  │                               │
│  │    quizzing → neutral voice  │                               │
│  └──────────┬───────────────────┘                               │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────────────┐                               │
│  │  ELEVENLABS STREAMING API    │                               │
│  │                              │                               │
│  │  Send text paragraph by      │                               │
│  │  paragraph → receive audio   │                               │
│  │  chunks → stream to client   │                               │
│  │                              │                               │
│  │  Latency: ~1-2 sec for       │                               │
│  │  first chunk                 │                               │
│  └──────────┬───────────────────┘                               │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────────────┐                               │
│  │  CACHING                     │                               │
│  │                              │                               │
│  │  Cache generated audio by:   │                               │
│  │  hash(text + voice_id)       │                               │
│  │                              │                               │
│  │  Common explanations get     │                               │
│  │  cached → instant playback   │                               │
│  │  for popular topics          │                               │
│  └──────────────────────────────┘                               │
│                                                                 │
│  COST MANAGEMENT:                                               │
│  • ~$0.30 per 1000 characters                                   │
│  • Cache aggressively (same explanation = same audio)           │
│  • Offer text-only mode for budget-conscious usage              │
│  • Rate limit: max 30 voice-minutes per free-tier student/day   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F9. Avatar Presentation

**What it does:** A visual AI presenter that explains concepts with lip-synced
speech, gestures, and visual aids — like a virtual teacher on screen.

```
┌─────────────────────────────────────────────────────────────────┐
│  F9: AVATAR SYSTEM                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TWO MODES:                                                     │
│                                                                 │
│  MODE A: PRE-GENERATED (Recommended for MVP)                    │
│  ──────────────────────────────────────                         │
│  ┌──────────────────────────────────────────────┐               │
│  │                                              │               │
│  │  Tutor generates explanation text            │               │
│  │       │                                      │               │
│  │       ▼                                      │               │
│  │  Text + audio sent to DeepBrain/HeyGen       │               │
│  │       │                                      │               │
│  │       ▼                                      │               │
│  │  Avatar video generated (15-60 sec wait)     │               │
│  │       │                                      │               │
│  │       ▼                                      │               │
│  │  Student gets notification:                  │               │
│  │  "Video explanation ready! [Play]"           │               │
│  │                                              │               │
│  │  Good for: Complex explanations that         │               │
│  │  benefit from visual presentation.           │               │
│  │  NOT for: real-time conversation.            │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
│  MODE B: REAL-TIME AVATAR (Future / Tier 3)                     │
│  ──────────────────────────────────────                         │
│  ┌──────────────────────────────────────────────┐               │
│  │                                              │               │
│  │  Lightweight animated avatar on screen       │               │
│  │  (think: animated character, not deepfake)   │               │
│  │       │                                      │               │
│  │       ▼                                      │               │
│  │  Lip-syncs to audio stream from ElevenLabs   │               │
│  │  Basic gestures (nod, point, wave)           │               │
│  │  Rendered client-side (browser canvas/WebGL) │               │
│  │                                              │               │
│  │  This avoids the 30-sec API generation       │               │
│  │  delay. Trade-off: less realistic.           │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
│  WHEN TO USE AVATAR (auto-detection):                           │
│  • Student has avatar_enabled = true                            │
│  • Response is a complex explanation (>200 words)               │
│  • Topic benefits from visual presentation                      │
│  • NOT for simple Q&A or short answers                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F10. Sign Language Translation

**What it does:** Translates the tutor's responses into ASL/BSL sign language,
delivered through an animated avatar.

```
┌─────────────────────────────────────────────────────────────────┐
│  F10: SIGN LANGUAGE SYSTEM                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  THE CHALLENGE:                                                 │
│  Sign language ≠ word-for-word English translation.             │
│  ASL has its own grammar: topic-comment structure,              │
│  time markers first, different word order.                      │
│                                                                 │
│  TRANSLATION PIPELINE:                                          │
│                                                                 │
│  English text from tutor                                        │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────────────────────────┐                               │
│  │  STEP 1: SIMPLIFY TEXT      │                               │
│  │                              │                               │
│  │  Claude rewrites text for    │                               │
│  │  sign language compatibility:│                               │
│  │  • Shorter sentences         │                               │
│  │  • Active voice              │                               │
│  │  • Concrete nouns/verbs      │                               │
│  │  • Remove idioms             │                               │
│  └──────────┬───────────────────┘                               │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────────────┐                               │
│  │  STEP 2: GENERATE GLOSSES   │                               │
│  │                              │                               │
│  │  Convert to sign language    │                               │
│  │  notation (glosses):         │                               │
│  │                              │                               │
│  │  English: "The cat sat on    │                               │
│  │           the mat"           │                               │
│  │  ASL:     CAT MAT SIT       │                               │
│  │                              │                               │
│  │  Display glosses as text     │                               │
│  │  subtitle alongside video    │                               │
│  └──────────┬───────────────────┘                               │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────────────┐                               │
│  │  STEP 3: GENERATE VIDEO     │                               │
│  │                              │                               │
│  │  OPTION A: API-based         │                               │
│  │  → Send glosses to           │                               │
│  │    Sign-Speak API            │                               │
│  │  → Receive avatar video      │                               │
│  │                              │                               │
│  │  OPTION B: Dictionary-based  │                               │
│  │  → Look up each sign in      │                               │
│  │    pre-recorded dictionary   │                               │
│  │  → Stitch videos together    │                               │
│  │  (more reliable, less fluid) │                               │
│  │                              │                               │
│  │  OPTION C: Hybrid            │                               │
│  │  → Common phrases = pre-     │                               │
│  │    recorded (fast)           │                               │
│  │  → Uncommon = API-generated  │                               │
│  │    (slower but complete)     │                               │
│  └──────────┬───────────────────┘                               │
│             │                                                   │
│             ▼                                                   │
│  ┌──────────────────────────────┐                               │
│  │  DELIVERY                    │                               │
│  │                              │                               │
│  │  Student sees:               │                               │
│  │  ┌─────────────────────────┐ │                               │
│  │  │ ┌──────┐  Text response │ │                               │
│  │  │ │ Sign │  here alongside│ │                               │
│  │  │ │avatar│  the signing   │ │                               │
│  │  │ │      │  avatar        │ │                               │
│  │  │ └──────┘                │ │                               │
│  │  │ [ASL Glosses: CAT MAT] │ │                               │
│  │  └─────────────────────────┘ │                               │
│  └──────────────────────────────┘                               │
│                                                                 │
│  REALISTIC SCOPE FOR MVP:                                       │
│  • Start with pre-recorded sign dictionary (500+ common signs)  │
│  • Use API for full sentences (accept 10-20 sec delay)          │
│  • Always show text + glosses as fallback                       │
│  • Full ASL first, BSL as fast-follow                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F12. Progress Analytics Dashboard

**What it does:** Visual dashboard showing student progress over time —
mastery levels, strengths, weaknesses, and learning trajectory.

```
┌─────────────────────────────────────────────────────────────────┐
│  F12: ANALYTICS DASHBOARD                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STUDENT VIEW:                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ┌─ Overall Progress ─────────────────────────────┐      │   │
│  │  │                                                │      │   │
│  │  │  Math:     ████████████████░░░░  78%           │      │   │
│  │  │  Biology:  █████████░░░░░░░░░░░  45%           │      │   │
│  │  │  English:  ██████████████░░░░░░  67%           │      │   │
│  │  │  History:  ███████░░░░░░░░░░░░░  35%           │      │   │
│  │  │                                                │      │   │
│  │  └────────────────────────────────────────────────┘      │   │
│  │                                                          │   │
│  │  ┌─ This Week ────────────────────────────────────┐      │   │
│  │  │                                                │      │   │
│  │  │  Sessions: 7    Time: 4.5 hrs    Quizzes: 3   │      │   │
│  │  │                                                │      │   │
│  │  │  Topics Covered:                               │      │   │
│  │  │  ✓ Quadratic equations (mastered)              │      │   │
│  │  │  ⟳ Cell division (in progress)                 │      │   │
│  │  │  ✗ Essay structure (needs work)                │      │   │
│  │  │                                                │      │   │
│  │  └────────────────────────────────────────────────┘      │   │
│  │                                                          │   │
│  │  ┌─ Strengths & Gaps ─────────────────────────────┐      │   │
│  │  │                                                │      │   │
│  │  │  STRONG:           NEEDS WORK:                 │      │   │
│  │  │  ✓ Algebra         ✗ Essay writing             │      │   │
│  │  │  ✓ Logic           ✗ History dates             │      │   │
│  │  │  ✓ Programming     ✗ Lab reports               │      │   │
│  │  │                                                │      │   │
│  │  └────────────────────────────────────────────────┘      │   │
│  │                                                          │   │
│  │  ┌─ Recommended Next ─────────────────────────────┐      │   │
│  │  │                                                │      │   │
│  │  │  1. Review "Cell Division" - you're close!     │      │   │
│  │  │  2. Practice essay writing with guided prompts │      │   │
│  │  │  3. Try the Biology Chapter 5 quiz             │      │   │
│  │  │                                                │      │   │
│  │  └────────────────────────────────────────────────┘      │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  TEACHER VIEW:                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ┌─ Class Overview ───────────────────────────────┐      │   │
│  │  │                                                │      │   │
│  │  │  30 students enrolled                          │      │   │
│  │  │  Average mastery: 62%                          │      │   │
│  │  │  Most struggled topic: "Quadratic Formula"     │      │   │
│  │  │  Top performer: Sarah (91%)                    │      │   │
│  │  │  Needs attention: 5 students below 40%         │      │   │
│  │  │                                                │      │   │
│  │  └────────────────────────────────────────────────┘      │   │
│  │                                                          │   │
│  │  ┌─ Individual Student Drill-Down ────────────────┐      │   │
│  │  │                                                │      │   │
│  │  │  [Select Student ▼]                            │      │   │
│  │  │                                                │      │   │
│  │  │  Full learning history                         │      │   │
│  │  │  Session transcripts (summarized)              │      │   │
│  │  │  Assessment results over time                  │      │   │
│  │  │  AI teaching notes & recommendations           │      │   │
│  │  │                                                │      │   │
│  │  └────────────────────────────────────────────────┘      │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  DATA SOURCES:                                                  │
│  • Episodic memory (PostgreSQL) → session history               │
│  • Assessment grades → trend analysis                           │
│  • Student profiles → mastery scores                            │
│  • Calculated in real-time with materialized views              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### F14. Learning Path Recommendations

**What it does:** Based on student's progress, gaps, and goals — automatically
suggests what to study next and in what order.

```
┌─────────────────────────────────────────────────────────────────┐
│  F14: LEARNING PATH ENGINE                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  HOW IT DECIDES WHAT'S NEXT:                                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                                                      │       │
│  │  INPUT:                                              │       │
│  │  • Student's current mastery per topic               │       │
│  │  • Curriculum dependency graph                       │       │
│  │  • Known weak areas                                  │       │
│  │  • Student's stated goals                            │       │
│  │  • Time until next exam (if known)                   │       │
│  │                                                      │       │
│  │  ALGORITHM:                                          │       │
│  │                                                      │       │
│  │  1. Check prerequisite graph:                        │       │
│  │     "Can't do calculus until algebra is mastered"    │       │
│  │                                                      │       │
│  │  2. Priority scoring:                                │       │
│  │     score = (importance × gap_size) - mastery_level  │       │
│  │                                                      │       │
│  │  3. Rank topics by score                             │       │
│  │                                                      │       │
│  │  4. Filter out topics already mastered (>0.85)       │       │
│  │                                                      │       │
│  │  5. Present top 3-5 recommendations                  │       │
│  │                                                      │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  EXAMPLE PATH:                                                  │
│                                                                 │
│  Current state: Math mastery = 0.65                             │
│                                                                 │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐     │
│  │Linear│───▶│Quadra│───▶│Factor│───▶│Graph-│───▶│Intro │     │
│  │Equat.│    │tics  │    │izing │    │  ing │    │Calc. │     │
│  │      │    │      │    │      │    │      │    │      │     │
│  │ ✓ 92%│    │⟳ 55% │    │○ 20% │    │○ 0%  │    │○ 0%  │     │
│  │      │    │      │    │      │    │      │    │      │     │
│  │DONE  │    │ YOU  │    │ NEXT │    │LATER │    │LATER │     │
│  │      │    │ ARE  │    │      │    │      │    │      │     │
│  │      │    │ HERE │    │      │    │      │    │      │     │
│  └──────┘    └──────┘    └──────┘    └──────┘    └──────┘     │
│                                                                 │
│  Recommendation: "You're almost done with Quadratics.           │
│  Let's nail that down before moving to Factorizing."            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Data Flow Architecture

### 6.1 Request Lifecycle (End-to-End)

```
┌─────────────────────────────────────────────────────────────────┐
│  COMPLETE REQUEST LIFECYCLE                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Student types: "Explain photosynthesis"                        │
│                                                                 │
│  ① CLIENT                                                       │
│  │  Browser sends POST /api/v1/chat/message                     │
│  │  { content: "Explain photosynthesis", session_id: "abc" }    │
│  │                                                              │
│  ② API GATEWAY                                                  │
│  │  ├─ Verify JWT token                                         │
│  │  ├─ Check rate limit                                         │
│  │  └─ Route to API service                                     │
│  │                                                              │
│  ③ API SERVICE                                                  │
│  │  ├─ Load session context from Redis                          │
│  │  ├─ Verify session belongs to this user                      │
│  │  └─ Pass to Orchestrator                                     │
│  │                                                              │
│  ④ ORCHESTRATOR                                                 │
│  │  ├─ Classify intent → "explanation_request"                  │
│  │  ├─ Load student profile from PostgreSQL                     │
│  │  ├─ Determine which agents needed:                           │
│  │  │   → Tutor Agent (always)                                  │
│  │  │   → Voice Agent (if voice_enabled)                        │
│  │  │   → Sign Language Agent (if sign_language set)            │
│  │  └─ Execute agent pipeline                                   │
│  │                                                              │
│  ⑤ TUTOR AGENT                                                  │
│  │  ├─ Query RAG: search "photosynthesis" in ChromaDB           │
│  │  │   → Returns 5 relevant chunks from biology textbook       │
│  │  ├─ Load student history on "biology/photosynthesis"         │
│  │  │   → "Student is visual learner, 10th grade, first time"   │
│  │  ├─ Build prompt with all context                            │
│  │  ├─ Send to Claude API                                       │
│  │  │   → Gets adaptive explanation with diagrams               │
│  │  └─ Return AgentResponse                                     │
│  │                                                              │
│  ⑥ VOICE AGENT (parallel if enabled)                            │
│  │  ├─ Receive text from Tutor Agent                            │
│  │  ├─ Preprocess text for speech                               │
│  │  ├─ Send to ElevenLabs streaming API                         │
│  │  └─ Return audio stream URL                                  │
│  │                                                              │
│  ⑦ SIGN LANGUAGE AGENT (parallel if enabled)                    │
│  │  ├─ Receive text from Tutor Agent                            │
│  │  ├─ Simplify text for sign language                          │
│  │  ├─ Generate glosses                                         │
│  │  ├─ Send to Sign-Speak API (async job)                       │
│  │  └─ Return job_id (client polls for result)                  │
│  │                                                              │
│  ⑧ RESPONSE ASSEMBLY                                            │
│  │  ├─ Combine all agent outputs                                │
│  │  ├─ Save interaction to episodic memory                      │
│  │  ├─ Update session context in Redis                          │
│  │  └─ Return unified response                                  │
│  │                                                              │
│  ⑨ BACK TO CLIENT                                               │
│     {                                                           │
│       text: "Great question! Let me ask you...",                │
│       audio_url: "/audio/xyz.mp3",                              │
│       sign_language_job_id: "job-456",                          │
│       sources: ["Biology Ch.4 p.112"],                          │
│       suggested_next: "Want to see a diagram?"                  │
│     }                                                           │
│                                                                 │
│  TOTAL LATENCY BUDGET:                                          │
│  ┌──────────────────────────────────────────────┐               │
│  │  Auth + routing:     ~50ms                   │               │
│  │  Context loading:    ~100ms                  │               │
│  │  RAG retrieval:      ~200ms                  │               │
│  │  Claude generation:  ~1-3 sec (streaming)    │               │
│  │  Voice generation:   ~2-3 sec (parallel)     │               │
│  │  Sign language:      ~15-30 sec (async)      │               │
│  │                                              │               │
│  │  Text appears:  ~1.5 sec (first token)       │               │
│  │  Audio starts:  ~3 sec                       │               │
│  │  Sign video:    notification when ready      │               │
│  └──────────────────────────────────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICE INTEGRATION MAP                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Each external service is wrapped in an abstraction layer       │
│  so we can swap providers without changing business logic.      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  LLM PROVIDER                                           │    │
│  │                                                         │    │
│  │  Interface: LLMProvider                                  │    │
│  │  Primary:   Claude (Anthropic)                          │    │
│  │  Fallback:  GPT-4 (OpenAI)                              │    │
│  │                                                         │    │
│  │  Strategy:                                              │    │
│  │  • Complex reasoning → Claude Opus                      │    │
│  │  • Simple tasks → Claude Haiku (cheaper)                │    │
│  │  • If Claude down → failover to GPT-4                   │    │
│  │  • All calls go through abstraction layer               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  VOICE PROVIDER                                         │    │
│  │                                                         │    │
│  │  Interface: VoiceProvider                                │    │
│  │  Primary:   ElevenLabs                                  │    │
│  │  Fallback:  Google Cloud TTS                            │    │
│  │                                                         │    │
│  │  Strategy:                                              │    │
│  │  • Use ElevenLabs for quality voices                    │    │
│  │  • Cache all generated audio (24hr TTL)                 │    │
│  │  • Fallback to Google TTS if ElevenLabs is down/over    │    │
│  │    rate limit                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  AVATAR PROVIDER                                        │    │
│  │                                                         │    │
│  │  Interface: AvatarProvider                               │    │
│  │  Primary:   DeepBrain AI                                │    │
│  │  Alt:       HeyGen, D-ID                                │    │
│  │                                                         │    │
│  │  Strategy:                                              │    │
│  │  • Async generation only (not real-time)                │    │
│  │  • Job queue with status polling                        │    │
│  │  • Cache popular explanation videos                     │    │
│  │  • Budget cap per student per day                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  SIGN LANGUAGE PROVIDER                                 │    │
│  │                                                         │    │
│  │  Interface: SignLanguageProvider                          │    │
│  │  Primary:   Sign-Speak API (or similar)                 │    │
│  │  Fallback:  Pre-recorded dictionary lookup              │    │
│  │                                                         │    │
│  │  Strategy:                                              │    │
│  │  • Dictionary-first for common words/phrases            │    │
│  │  • API for full sentences                               │    │
│  │  • Graceful degradation: if API fails, show glosses     │    │
│  │    (text notation) as fallback                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  CIRCUIT BREAKER PATTERN:                                       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │                                                      │       │
│  │  Every external call has:                            │       │
│  │  • Timeout (5s for LLM, 3s for voice, 30s avatar)   │       │
│  │  • Retry with exponential backoff (max 3 retries)    │       │
│  │  • Circuit breaker (if 5 failures in 1 min → skip)   │       │
│  │  • Fallback behavior (graceful degradation)          │       │
│  │                                                      │       │
│  │  If voice fails → text still works                   │       │
│  │  If avatar fails → voice still works                 │       │
│  │  If sign lang fails → glosses still shown            │       │
│  │  If LLM fails → show cached response or error        │       │
│  │                                                      │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Screen & Interface Flows

### 8.1 Main Student Interface Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  STUDENT MAIN SCREEN                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ┌────────┐                                    ┌────────┐ │   │
│  │ │EduAGI  │  Math > Algebra > Quadratics       │Settings│ │   │
│  │ └────────┘                                    └────────┘ │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │                                                  │    │   │
│  │  │  ┌─────────────────────────────────────────┐     │    │   │
│  │  │  │ AI: "Let's explore quadratic equations. │     │    │   │
│  │  │  │ First, what do you already know about   │     │    │   │
│  │  │  │ equations with x²?"                     │     │    │   │
│  │  │  │                          [🔊] [👤] [🤟] │     │    │   │
│  │  │  └─────────────────────────────────────────┘     │    │   │
│  │  │                                                  │    │   │
│  │  │  ┌─────────────────────────────────────────┐     │    │   │
│  │  │  │ You: "I know they make a U-shape on     │     │    │   │
│  │  │  │ a graph?"                               │     │    │   │
│  │  │  └─────────────────────────────────────────┘     │    │   │
│  │  │                                                  │    │   │
│  │  │  ┌─────────────────────────────────────────┐     │    │   │
│  │  │  │ AI: "Exactly! That U-shape is called    │     │    │   │
│  │  │  │ a parabola. Now, can you think of why   │     │    │   │
│  │  │  │ it curves instead of being straight?"   │     │    │   │
│  │  │  │                          [🔊] [👤] [🤟] │     │    │   │
│  │  │  │                                         │     │    │   │
│  │  │  │  📎 Source: Algebra Textbook Ch.7       │     │    │   │
│  │  │  └─────────────────────────────────────────┘     │    │   │
│  │  │                                                  │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │ Type your answer...                     [Send ▶] │    │   │
│  │  │                                         [🎤 Mic] │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                          │   │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌───────────┐     │   │
│  │  │Quiz Me  │ │ My      │ │ Switch   │ │ End       │     │   │
│  │  │         │ │Progress │ │ Subject  │ │ Session   │     │   │
│  │  └─────────┘ └─────────┘ └──────────┘ └───────────┘     │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ICON LEGEND:                                                   │
│  [🔊] = Play voice version of this message                     │
│  [👤] = Generate avatar video for this explanation             │
│  [🤟] = Show sign language translation                         │
│  [🎤] = Voice input (speech-to-text)                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Navigation Flow

```
┌──────────────────────────────────────────────────────────┐
│                   APP NAVIGATION MAP                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│                    ┌──────────┐                           │
│                    │  LOGIN   │                           │
│                    └────┬─────┘                           │
│                         │                                │
│              ┌──────────┴──────────┐                     │
│              │                     │                     │
│         Student               Teacher                   │
│              │                     │                     │
│              ▼                     ▼                     │
│    ┌─────────────────┐   ┌─────────────────┐            │
│    │ STUDENT HOME    │   │ TEACHER HOME    │            │
│    │                 │   │                 │            │
│    │ • Continue      │   │ • My Classes    │            │
│    │   learning      │   │ • Create Quiz   │            │
│    │ • Start new     │   │ • Upload Content│            │
│    │   session       │   │ • View Grades   │            │
│    │ • View progress │   │ • Analytics     │            │
│    │ • Take quiz     │   │                 │            │
│    └───┬──┬──┬──┬────┘   └───┬──┬──┬──┬────┘            │
│        │  │  │  │            │  │  │  │                  │
│        ▼  │  │  │            │  │  │  │                  │
│  ┌──────────┐│  │      ┌──────────┐│  │                  │
│  │ TUTORING ││  │      │  CLASS   ││  │                  │
│  │ SESSION  ││  │      │ MANAGER  ││  │                  │
│  │          ││  │      │          ││  │                  │
│  │ chat +   ││  │      │ students ││  │                  │
│  │ voice +  ││  │      │ list +   ││  │                  │
│  │ avatar + ││  │      │ progress ││  │                  │
│  │ sign     ││  │      │          ││  │                  │
│  └──────────┘│  │      └──────────┘│  │                  │
│              ▼  │                   ▼  │                  │
│        ┌──────────┐         ┌──────────┐                 │
│        │ASSESSMENT│         │ CONTENT  │                 │
│        │          │         │ UPLOAD   │                 │
│        │ take     │         │          │                 │
│        │ quiz +   │         │ PDF,DOCX │                 │
│        │ see      │         │ → RAG    │                 │
│        │ results  │         │ indexed  │                 │
│        └──────────┘         └──────────┘                 │
│                    ▼                    ▼                 │
│              ┌──────────┐        ┌──────────┐            │
│              │ PROGRESS │        │ANALYTICS │            │
│              │DASHBOARD │        │DASHBOARD │            │
│              │          │        │          │            │
│              │ student  │        │ class-   │            │
│              │ view     │        │ wide     │            │
│              └──────────┘        └──────────┘            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Summary: What Makes This Design Work

```
┌─────────────────────────────────────────────────────────────────┐
│  KEY DESIGN DECISIONS                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TEXT FIRST, ALWAYS                                          │
│     Text response is never blocked by voice/avatar/sign.        │
│     Multi-modal is progressive enhancement, not a gate.         │
│                                                                 │
│  2. ASYNC HEAVY MEDIA                                           │
│     Avatar videos and sign language are generated async.        │
│     Students don't wait — they get a notification when ready.   │
│                                                                 │
│  3. MEMORY DRIVES PERSONALIZATION                               │
│     Every interaction updates the student profile.              │
│     Next interaction is smarter because of the last one.        │
│                                                                 │
│  4. PROVIDER ABSTRACTION                                        │
│     Every external API (LLM, voice, avatar, sign) is behind    │
│     an interface. We can swap ElevenLabs for Google TTS         │
│     without touching business logic.                            │
│                                                                 │
│  5. GRACEFUL DEGRADATION                                        │
│     If any service fails, the system still works.               │
│     Voice down? Text works. Avatar down? Voice works.           │
│     LLM down? Show cached responses.                           │
│                                                                 │
│  6. COST-AWARE ROUTING                                          │
│     Simple tasks → cheap model (Haiku)                          │
│     Complex reasoning → expensive model (Opus)                  │
│     Repeated explanations → cached (free)                       │
│                                                                 │
│  7. SOCRATIC BY DEFAULT                                         │
│     The AI asks questions first. It guides discovery.           │
│     Direct answers only when the student explicitly asks        │
│     or after 3 guided attempts.                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

*End of System Design Document*
*Next step: Implementation starts with Tier 1 (MVP) features.*
