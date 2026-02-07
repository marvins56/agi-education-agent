# F04 & F05: Assessment Generation + Auto-Grading
# EduAGI Feature Design Document

**Priority:** P0 (Critical)
**Tier:** 1 - Core MVP
**Dependencies:** F01 (Tutoring), F02 (RAG), F03 (Student Memory)

---

## 1. Feature Overview

### What It Does
The assessment system creates quizzes, exams, and assignments tailored to each
student's level — then grades them automatically with detailed, constructive feedback.
It's not just "right or wrong" — it tells students WHY and HOW to improve.

### The Student Experience

```
  Sarah just finished learning about quadratic equations.
  The AI says: "Nice work! Want to test yourself?"

  She clicks [Quiz Me] →

  ┌─────────────────────────────────────────────┐
  │  QUIZ: Quadratic Equations                  │
  │  5 questions · ~10 min · Adaptive           │
  │                                             │
  │  Q1 (Medium) ✓  Q2 (Medium) ✓              │
  │  Q3 (Hard) ✗    Q4 (Medium) ✓              │
  │  Q5 (Hard) ✓                                │
  │                                             │
  │  Score: 80% (4/5)                           │
  │                                             │
  │  "Great job! You nailed the basics.         │
  │   On Q3, you mixed up the signs when        │
  │   factoring. Here's what happened:          │
  │   You wrote (x+2)(x+3) but the middle      │
  │   term is negative, so it should be         │
  │   (x-2)(x-3). Want to try a similar one?"  │
  │                                             │
  │  [Try Similar] [Review All] [Continue]      │
  └─────────────────────────────────────────────┘
```

### Why It Matters
- Students learn by testing themselves (active recall > passive reading)
- Instant feedback beats waiting days for a teacher to grade
- Teachers save 5+ hours/week on grading
- Adaptive difficulty keeps students in their "learning zone"

---

## 2. Detailed Workflows

### 2.1 Who Can Trigger an Assessment?

```
  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  │   STUDENT    │   │   TEACHER    │   │    SYSTEM    │
  │              │   │              │   │   (auto)     │
  │ "Quiz me    │   │ "Assign a   │   │ After 5      │
  │  on Ch.5"   │   │  midterm"   │   │ lessons,     │
  │              │   │              │   │ suggest quiz │
  │ Casual,     │   │ Formal,     │   │ Checkpoint,  │
  │ practice    │   │ graded      │   │ low-stakes   │
  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
         │                  │                   │
         └──────────────────┴───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  ASSESSMENT ENGINE    │
                │                       │
                │  Configure:           │
                │  • Subject + topics   │
                │  • Question types     │
                │  • Difficulty         │
                │  • # of questions     │
                │  • Time limit         │
                │  • Practice or graded │
                └───────────┬───────────┘
                            │
                            ▼
                    Generate Questions
```

### 2.2 Question Generation Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│  QUESTION GENERATION FLOW                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Input: topic + difficulty + student_level + question_type  │
│       │                                                     │
│       ▼                                                     │
│  ┌────────────────┐                                         │
│  │ 1. RAG PULL    │  Retrieve relevant curriculum content   │
│  │    from KB     │  for this topic + grade level           │
│  └───────┬────────┘                                         │
│          │                                                  │
│          ▼                                                  │
│  ┌────────────────┐                                         │
│  │ 2. GENERATE    │  Claude creates question + answer key   │
│  │    via LLM     │  using retrieved content as ground      │
│  │                │  truth                                  │
│  └───────┬────────┘                                         │
│          │                                                  │
│          ▼                                                  │
│  ┌────────────────┐                                         │
│  │ 3. VALIDATE    │  Check for:                             │
│  │                │  • Ambiguity (only 1 correct answer)    │
│  │                │  • Clarity (understandable language)     │
│  │                │  • Difficulty match (easy/med/hard)      │
│  │                │  • No duplicate of recent questions      │
│  └───────┬────────┘                                         │
│          │                                                  │
│          ▼                                                  │
│  ┌────────────────┐                                         │
│  │ 4. STORE       │  Save to question bank with metadata    │
│  │                │  (topic, difficulty, bloom_level, etc.)  │
│  └────────────────┘                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Question Types - Detailed Design

#### MCQ (Multiple Choice)

```
  Generation:
  ┌──────────────────────────────────────────────┐
  │  1. Generate correct answer from RAG content │
  │  2. Generate 3 distractors that:            │
  │     • Target common misconceptions          │
  │     • Are plausible but clearly wrong        │
  │     • Are similar length to correct answer   │
  │  3. Randomize option order                   │
  │  4. Validate: exactly 1 unambiguous answer   │
  └──────────────────────────────────────────────┘

  Grading: Exact match → instant (0 or full points)

  Example:
  ┌──────────────────────────────────────────────┐
  │  What is the discriminant of x² + 5x + 6?   │
  │                                              │
  │  A) 1     ← correct (b²-4ac = 25-24 = 1)   │
  │  B) -1    ← common sign error               │
  │  C) 49    ← forgot to subtract 4ac          │
  │  D) 11    ← added instead of subtracted     │
  └──────────────────────────────────────────────┘
```

#### Essay Questions

```
  Generation:
  ┌──────────────────────────────────────────────┐
  │  1. Create open-ended prompt from topic      │
  │  2. Auto-generate rubric with criteria:      │
  │     • Content accuracy (40%)                 │
  │     • Argument structure (25%)               │
  │     • Evidence/examples (20%)                │
  │     • Clarity/grammar (15%)                  │
  │  3. Set word count range                     │
  │  4. Generate model answer for reference      │
  └──────────────────────────────────────────────┘

  Grading:
  ┌──────────────────────────────────────────────┐
  │  Claude evaluates against rubric             │
  │       │                                      │
  │       ▼                                      │
  │  Per-criteria score + specific feedback      │
  │       │                                      │
  │       ▼                                      │
  │  "Your explanation of osmosis was strong     │
  │   (8/10 content). However, your argument     │
  │   jumped between topics without transitions  │
  │   (5/10 structure). Try using 'furthermore'  │
  │   and 'in contrast' to connect ideas."       │
  └──────────────────────────────────────────────┘
```

#### Code Challenges

```
  Generation:
  ┌──────────────────────────────────────────────┐
  │  1. Create problem statement                 │
  │  2. Generate 5-10 test cases:                │
  │     • 2 basic cases (visible to student)     │
  │     • 3 edge cases (hidden)                  │
  │     • 2 performance cases (hidden)           │
  │  3. Generate starter code (optional)         │
  │  4. Set language + time limit                │
  └──────────────────────────────────────────────┘

  Grading:
  ┌──────────────────────────────────────────────┐
  │  Student submits code                        │
  │       │                                      │
  │       ▼                                      │
  │  Run in Docker sandbox (10s timeout)         │
  │       │                                      │
  │       ▼                                      │
  │  Execute test cases                          │
  │  Score = passed / total × points             │
  │       │                                      │
  │       ▼                                      │
  │  Claude reviews code quality:                │
  │  • Variable naming                           │
  │  • Efficiency                                │
  │  • Edge case handling                        │
  │       │                                      │
  │       ▼                                      │
  │  "3/5 tests passed. Test 4 failed:           │
  │   Input [0,0,0] → expected 0, got error.     │
  │   Your code doesn't handle empty arrays.     │
  │   Tip: Add a check at line 3."              │
  └──────────────────────────────────────────────┘
```

#### Math Problems

```
  Generation:
  ┌──────────────────────────────────────────────┐
  │  1. Generate problem with known solution     │
  │  2. Generate step-by-step solution key       │
  │  3. Identify common mistake points           │
  └──────────────────────────────────────────────┘

  Grading:
  ┌──────────────────────────────────────────────┐
  │  1. Check final answer (exact or ±tolerance) │
  │       │                                      │
  │   CORRECT → full points                      │
  │       │                                      │
  │   WRONG → check student's work steps         │
  │       │                                      │
  │       ▼                                      │
  │  2. Claude analyzes work for partial credit  │
  │     • Correct setup? (+25%)                  │
  │     • Correct method? (+25%)                 │
  │     • Arithmetic error only? (+50%)          │
  │       │                                      │
  │       ▼                                      │
  │  3. Pinpoint where the mistake happened      │
  │     "Your approach was correct! But in       │
  │      step 3, you wrote 5×3=18 instead of     │
  │      15. The rest of your work follows        │
  │      correctly from that error."             │
  └──────────────────────────────────────────────┘
```

#### Additional Types

```
  TRUE/FALSE + JUSTIFICATION:
  • Student picks T/F AND writes 1-2 sentence explanation
  • Grading: T/F check (50%) + justification quality (50%)

  FILL-IN-THE-BLANK:
  • Accepts exact match OR semantic equivalents
  • "The process by which plants make food is called ____"
  • Accepts: "photosynthesis", "photo-synthesis", "Photosynthesis"

  MATCHING:
  • Pair items from two columns
  • Grading: each correct pair = points / total_pairs

  DIAGRAM LABELING:
  • Present image, student labels parts
  • Grading: fuzzy text match on labels + position proximity
```

### 2.4 Adaptive Difficulty Engine

```
┌─────────────────────────────────────────────────────────────┐
│  ADAPTIVE DIFFICULTY FLOW                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Start: MEDIUM difficulty                                   │
│            │                                                │
│     ┌──────┴──────┐                                         │
│     │  Correct?   │                                         │
│     └──┬──────┬───┘                                         │
│     YES│      │NO                                           │
│        │      │                                             │
│        ▼      ▼                                             │
│     HARDER   EASIER                                         │
│        │      │                                             │
│     ┌──┴──────┴──┐                                          │
│     │  Correct?  │                                          │
│     └──┬──────┬──┘                                          │
│     YES│      │NO                                           │
│        ▼      ▼                                             │
│     HARDEST  SAME (+ hint)                                  │
│                                                             │
│  DIFFICULTY LEVELS:                                         │
│  1 = Remember (recall facts)                                │
│  2 = Understand (explain concepts)                          │
│  3 = Apply (use in new situations)                          │
│  4 = Analyze (break down, compare)                          │
│  5 = Evaluate (judge, critique)                             │
│  6 = Create (design, build)                                 │
│                                                             │
│  Maps to Bloom's Taxonomy for educational rigor.            │
│                                                             │
│  ZONE OF PROXIMAL DEVELOPMENT:                              │
│  Target: student gets ~70% correct                          │
│  Too easy (>90%) → increase level                           │
│  Too hard (<50%) → decrease level                           │
│  Sweet spot (60-80%) → stay here                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 Grading Pipeline

```
  Student submits answers
          │
          ▼
  ┌─────────────────────────────────────────────┐
  │  GRADING ROUTER                             │
  │                                             │
  │  For each question:                         │
  │                                             │
  │  MCQ / T-F / Fill-in ──▶ EXACT MATCH       │
  │  (instant, no LLM needed)    │              │
  │                              │              │
  │  Code ──────────────────▶ SANDBOX RUN       │
  │  (run tests, then LLM       │  + LLM       │
  │   reviews code quality)      │              │
  │                              │              │
  │  Math ──────────────────▶ SYMBOLIC CHECK    │
  │  (SymPy checks answer,      │  + LLM       │
  │   LLM checks work steps)    │              │
  │                              │              │
  │  Essay / Short Answer ──▶ LLM GRADING      │
  │  (Claude grades against      │              │
  │   rubric with specific       │              │
  │   feedback)                  │              │
  │                              │              │
  │  Matching ──────────────▶ PAIR MATCH        │
  │  (exact matching logic)      │              │
  │                              │              │
  └──────────────────────────────┼──────────────┘
                                 │
                                 ▼
  ┌─────────────────────────────────────────────┐
  │  FEEDBACK GENERATOR                         │
  │                                             │
  │  For each wrong answer:                     │
  │  1. What was wrong (specific)               │
  │  2. What the correct approach is            │
  │  3. Common mistake pattern identified       │
  │  4. Resource link for review                │
  │  5. "Try similar question" option           │
  │                                             │
  │  For correct answers:                       │
  │  1. Confirm understanding                   │
  │  2. Note if there's a faster/better method  │
  │                                             │
  │  Overall:                                   │
  │  1. Score + percentage                      │
  │  2. Strengths identified                    │
  │  3. Gaps identified                         │
  │  4. Recommended next steps                  │
  └─────────────────────────────────────────────┘
```

### 2.6 Grade Appeal Flow

```
  Student disagrees with grade
          │
          ▼
  ┌──────────────────────────┐
  │  Student writes appeal:  │
  │  "I think my answer to   │
  │   Q3 deserves more       │
  │   credit because..."     │
  └──────────┬───────────────┘
             │
             ▼
  ┌──────────────────────────┐
  │  AI RE-EVALUATES         │
  │                          │
  │  Second Claude call with │
  │  different prompt:       │
  │  "Review this grading    │
  │   considering student's  │
  │   appeal argument"       │
  │                          │
  │  Possible outcomes:      │
  │  • Grade increased       │
  │  • Grade confirmed       │
  │  • Explanation improved  │
  └──────────┬───────────────┘
             │
             ▼
  ┌──────────────────────────┐
  │  If still disputed →     │
  │  Flag for teacher review │
  │  (human in the loop)     │
  └──────────────────────────┘
```

---

## 3. Sub-features & Small Touches

### Practice Mode vs Graded Mode
```
  PRACTICE MODE:                    GRADED MODE:
  • Unlimited attempts              • One attempt
  • Hints available                 • No hints
  • Instant feedback per Q          • Feedback after submit
  • No time pressure                • Optional timer
  • Doesn't affect grades           • Affects grade record
  • "Safe to fail" environment      • Stakes matter
```

### Hint System
```
  Student stuck on Q3 →

  [Use Hint? This will cost 2 points]

  Hint Level 1: "Think about what happens when b²-4ac < 0"
  Hint Level 2: "The discriminant tells you the number of real roots"
  Hint Level 3: "Calculate: b² = 25, 4ac = 28. What's 25-28?"

  Each hint costs more points. Max 3 hints per question.
  Even with all hints used, student can still earn 40% credit.
```

### Other Small Touches
- **Timer** with gentle warnings at 75%, 50%, 25%, 5 min, 1 min remaining
- **Progress bar** showing questions answered / total
- **Save & continue later** for long assessments (state saved in Redis)
- **Review mode** after submission (see all Q&A with feedback, color-coded)
- **"Try similar question"** generates a new question on the same concept
- **Difficulty labels** visible to student: Easy ● Medium ●● Hard ●●●
- **Partial credit** shown transparently ("6/10 - here's why")
- **Code editor** with syntax highlighting, line numbers, auto-indent
- **Math input** with LaTeX preview (type LaTeX, see rendered math)
- **Question bank** - teachers can save, reuse, remix questions
- **Bloom's taxonomy tags** on each question (for curriculum alignment)
- **Flashcard generation** from missed questions ("Review these later")
- **Peer review** option for essays (students grade each other, AI moderates)
- **Plagiarism check** via embedding similarity against known submissions

---

## 4. Technical Requirements

### Code Execution Sandbox
```
  Student Code → Docker Container (isolated)

  Container specs:
  • Language-specific image (Python, JS, Java, C++)
  • No network access
  • 256MB memory limit
  • 10-second execution timeout
  • Read-only filesystem (except /tmp)
  • Killed after execution

  Security:
  • No system calls
  • No file access outside sandbox
  • No fork bombs (process limit)
  • Resource quotas enforced
```

### LLM Grading Consistency
```
  Problem: LLM grading can vary between calls

  Solution:
  • Temperature = 0.1 (near-deterministic)
  • Structured output format (JSON with scores + feedback)
  • Rubric included in every grading prompt
  • Sample graded answers in prompt (few-shot examples)
  • Grade calibration: run 3 parallel grading calls,
    take median score if spread > 15%
```

### Database Schema (Key Tables)
```
  assessments: id, title, subject, type, config, created_by, due_at
  questions: id, assessment_id, type, content, options, correct_answer,
             rubric, points, difficulty, bloom_level, topic
  submissions: id, assessment_id, student_id, answers, submitted_at,
               total_score, max_score, graded_at
  question_grades: id, submission_id, question_id, score, feedback
  question_bank: id, question_data, tags, usage_count, avg_score
```

### Math Expression Handling
```
  Input: Student types LaTeX or uses visual equation editor

  Rendering: KaTeX (client-side, fast)

  Evaluation: SymPy (server-side)
  • Parse student's expression
  • Symbolic comparison with answer key
  • Check algebraic equivalence (not just string match)
  • Example: "2(x+1)" = "2x+2" → both correct
```

---

## 5. Services & Alternatives

### Code Execution

| Service | Type | Pricing | Pros | Cons |
|---------|------|---------|------|------|
| **Docker Sandbox (Primary)** | Self-hosted | Infrastructure cost only | Full control, no limits | Must manage security |
| Judge0 | API | Free tier + $10/mo | Easy setup, 60+ languages | Rate limits on free |
| Piston API | Open-source | Free (self-host) | Lightweight, fast | Fewer languages |
| HackerRank API | API | Enterprise pricing | Battle-tested | Expensive, overkill |

**Recommendation:** Docker sandbox (self-hosted) for control + Judge0 as fallback.

### Math Evaluation

| Service | Type | Pricing | Pros | Cons |
|---------|------|---------|------|------|
| **SymPy (Primary)** | Library | Free | Full symbolic math, Python-native | Complex setup |
| Wolfram Alpha API | API | $5/mo (2K calls) | Most powerful | Expensive at scale |
| Mathjs | Library | Free | JavaScript, lightweight | Less powerful than SymPy |

### Plagiarism Detection

| Service | Type | Pricing | Pros | Cons |
|---------|------|---------|------|------|
| **Embedding similarity (Primary)** | Custom | LLM cost only | Works for all content | Novel approach |
| Turnitin API | API | Per-submission | Industry standard | Very expensive |
| Copyscape | API | $0.05/search | Cheap | Web-focused, not student work |

### LLM for Grading

| Model | Best For | Consistency | Cost |
|-------|----------|-------------|------|
| **Claude Opus** | Essays, complex grading | High | $15/M input |
| Claude Sonnet | Short answers, rubric grading | Good | $3/M input |
| Claude Haiku | MCQ validation, simple checks | Good | $0.25/M input |
| GPT-4o | Fallback grading | Good | $5/M input |

**Strategy:** Use Haiku for validation, Sonnet for standard grading, Opus for essay/appeal review.

---

## 6. Connections & Dependencies

```
  ┌──────────────┐        ┌──────────────┐
  │ F02 RAG      │───────▶│ F04/F05      │
  │ Knowledge    │ content│ Assessment   │
  │              │ for Qs │              │
  └──────────────┘        └──────┬───────┘
                                 │
  ┌──────────────┐               │ results
  │ F03 Student  │◀──────────────┘
  │ Memory       │ update mastery,
  │              │ strengths, gaps
  └──────────────┘
         │
         │ profile informs
         ▼
  ┌──────────────┐
  │ F14 Learning │ uses grades to
  │ Path         │ recommend next
  └──────────────┘

  ┌──────────────┐
  │ F13 Teacher  │ creates assessments,
  │ Dashboard    │ reviews grades,
  │              │ overrides scores
  └──────────────┘
```

---

*End of F04/F05 Assessment & Grading Design*
