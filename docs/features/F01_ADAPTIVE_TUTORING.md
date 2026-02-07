# Feature F01: Adaptive Text Tutoring
# EduAGI - Core AI Tutor Conversation Engine

**Feature ID:** F01
**Version:** 1.0
**Date:** February 2026
**Status:** Design Phase
**Priority:** P0 (Critical Path)
**Owner:** AI Engineering Team

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [The Student Experience](#2-the-student-experience)
3. [Detailed Workflow & Flow Diagrams](#3-detailed-workflow--flow-diagrams)
4. [Sub-Features & Small Touches](#4-sub-features--small-touches)
5. [Technical Requirements](#5-technical-requirements)
6. [Services & Alternatives](#6-services--alternatives)
7. [Connections & Dependencies](#7-connections--dependencies)
8. [Appendix](#8-appendix)

---

## 1. Feature Overview

### 1.1 What It Does

Adaptive Text Tutoring is the **beating heart of EduAGI**. It is the primary
interface through which a student learns. At its core, it is a conversational
AI tutor that:

- **Talks to the student** the way a great human tutor would -- patient,
  encouraging, and perceptive.
- **Adapts in real time** to what the student knows, what confuses them, and
  how they prefer to learn.
- **Remembers everything** -- not just what was said five minutes ago, but what
  the student struggled with three weeks ago.
- **Guides rather than tells** -- using the Socratic method by default, nudging
  the student toward understanding rather than handing them answers.
- **Knows when to change tactics** -- if an explanation is not landing, it does
  not repeat the same words louder. It tries a different angle entirely.

### 1.2 Why It Matters

Every other feature in EduAGI (voice, avatars, sign language, assessments)
is a *delivery mechanism* for the intelligence that lives here. If the tutoring
engine is mediocre, a beautiful avatar is just a mediocre tutor with a face.

This feature is the difference between:
- "An AI that answers my questions" (ChatGPT)
- "An AI that actually teaches me" (EduAGI)

### 1.3 The Student Experience -- A Real Scenario

```
Sarah, 20, studying Computer Science. It is 11pm. She has a data structures
exam in two days and she does not understand AVL tree rotations.

She opens EduAGI.

EDUAGI:  "Hey Sarah. Last time we were working through binary search trees
          and you had them down solid. Ready to keep going, or is there
          something else on your mind tonight?"

SARAH:   "I need help with AVL trees. I don't get the rotations."

EDUAGI:  "Got it. Let's build on what you already know about BSTs.
          Quick question first -- do you remember what makes a BST
          'unbalanced'? What goes wrong?"

SARAH:   "Um, like when all the nodes go to one side?"

EDUAGI:  "Exactly. And when that happens, what does it do to your
          search time?"

SARAH:   "It becomes O(n) instead of O(log n)?"

EDUAGI:  "Nailed it. So AVL trees exist to prevent exactly that problem.
          They keep the tree balanced after every insert and delete.
          The rule is simple: for every node, the heights of its left
          and right subtrees can differ by at most 1.

          Now -- what do you think happens when an insertion violates
          that rule?"

SARAH:   "You have to... rotate something?"

EDUAGI:  "Right. That's where rotations come in. There are four cases,
          but honestly they boil down to two ideas. Let me show you
          the simplest one first.

          Imagine this tree:

              30
             /
           20
           /
         10

          The balance factor at node 30 is 2 (left heavy).
          What if we could make 20 the new root?

          Think about what the tree would look like if 20 were on top,
          with 10 on its left and 30 on its right."

SARAH:   "Oh -- it would be balanced. 10, 20, 30."

EDUAGI:  "That's a right rotation. You just did it in your head.
          Want to try the left-right case next, or should we do a
          few more right rotations until they feel automatic?"

                    [More right rotations]  [Left-right case]
                    [Quiz me on this]        [Explain differently]
```

**What just happened:**
- The tutor remembered Sarah's previous session (BSTs)
- It connected new material to what she already knew
- It used Socratic questioning to make *her* articulate the answer
- It used a concrete visual example (ASCII tree)
- It offered her control over the pacing
- It presented quick-action buttons so she does not have to type everything

---

## 2. The Student Experience

### 2.1 What Students Actually Want

Based on educational research and user studies, students want a tutor that:

| Student Need | How F01 Addresses It |
|---|---|
| "Don't make me feel stupid" | Encouraging tone, no judgment on wrong answers |
| "Remember what I already know" | Session memory + long-term student profile |
| "Let me go at my own pace" | Adaptive pacing, no pressure to move on |
| "Show me, don't just tell me" | Code examples, ASCII diagrams, LaTeX math |
| "Let me try different approaches" | "Teach me differently" button, multiple explanation styles |
| "Know when I'm lost" | Real-time confusion detection, proactive check-ins |
| "Don't waste my time" | Skip what they know, focus on gaps |
| "Let me be in control" | Quick action buttons, topic switching, bookmarking |
| "Help me study for exams" | Integrated quizzing, spaced repetition hooks |
| "Work at 2am" | Always available, no scheduling required |

### 2.2 Session Lifecycle from the Student's Perspective

```
    Student opens EduAGI
           |
           v
  +------------------+
  |  Welcome Screen   |
  |                   |
  |  "Continue where  |    <-- Returning student
  |   you left off?"  |
  |                   |
  |  [Continue]       |
  |  [New topic]      |
  |  [Just quiz me]   |
  +--------+----------+
           |
           v
  +------------------+
  |  Active Session   |
  |                   |
  |  Student types    |
  |  or clicks a      |
  |  quick action     |
  |  button           |
  +--------+----------+
           |
           v
  +------------------+
  |  AI Responds      |
  |                   |
  |  - Streaming text |
  |  - With code/math |
  |  - With suggested |
  |    next actions   |
  +--------+----------+
           |
           v
  +------------------+
  |  Comprehension    |    <-- Periodic, not every turn
  |  Check            |
  |                   |
  |  "Can you explain |
  |   back to me      |
  |   what a right    |
  |   rotation does?" |
  +--------+----------+
           |
    +------+------+
    |             |
  Solid       Struggling
    |             |
    v             v
  Move on     Try again
  to next     with a new
  concept     approach
           |
           v
  +------------------+
  |  Session Wrap-Up  |
  |                   |
  |  - Summary of     |
  |    what we covered|
  |  - What to review |
  |  - Next session   |
  |    suggestion     |
  |  - Confidence     |
  |    self-rating    |
  +------------------+
```

---

## 3. Detailed Workflow & Flow Diagrams

### 3.1 How a Tutoring Conversation Starts

Every session begins with context loading. The system must understand *who*
this student is before the first word is generated.

```
  Student hits "Start Session"
         |
         v
  +----------------------------------+
  |  SESSION INITIALIZATION          |
  |                                  |
  |  1. Authenticate student         |
  |  2. Load student profile         |
  |     from PostgreSQL              |
  |  3. Load learning history        |
  |     (recent sessions, grades,    |
  |      known weaknesses)           |
  |  4. Load previous session        |
  |     context from Redis           |
  |     (if resuming)                |
  |  5. Determine session type:      |
  |     - Continuation               |
  |     - New topic                  |
  |     - Free exploration           |
  |  6. Select appropriate system    |
  |     prompt template              |
  |  7. Create WebSocket connection  |
  +----------------+-----------------+
                   |
                   v
  +----------------------------------+
  |  OPENING MESSAGE GENERATION      |
  |                                  |
  |  IF returning student:           |
  |    "Welcome back, [name].        |
  |     Last time we covered [X].    |
  |     Want to continue, or         |
  |     something new?"              |
  |                                  |
  |  IF new student:                 |
  |    "Hi! I'm your AI tutor.      |
  |     What are you studying?       |
  |     Tell me a bit about          |
  |     where you are."              |
  |                                  |
  |  IF specific topic requested:    |
  |    "Let's work on [topic].       |
  |     Before we start, what do     |
  |     you already know about it?"  |
  +----------------------------------+
```

**What gets loaded into the system prompt:**

```
  +--------------------------------------------------------------+
  |  SYSTEM PROMPT ASSEMBLY                                      |
  |                                                              |
  |  [Base Tutor Persona]                                        |
  |  +                                                           |
  |  [Student Profile Block]                                     |
  |    - Name, grade level, learning style                       |
  |    - Strengths and weaknesses                                |
  |    - Preferred explanation style                             |
  |    - Pace preference (slow/moderate/fast)                    |
  |  +                                                           |
  |  [Session Context Block]                                     |
  |    - Current subject and topic                               |
  |    - Learning objectives for this session                    |
  |    - What was covered in the last session                    |
  |    - Known misconceptions to watch for                       |
  |  +                                                           |
  |  [RAG Context Block]                                         |
  |    - Relevant curriculum content                             |
  |    - Textbook excerpts if available                          |
  |    - Pre-fetched based on anticipated topic                  |
  |  +                                                           |
  |  [Teaching Strategy Block]                                   |
  |    - Socratic mode ON/OFF                                    |
  |    - Current difficulty level                                |
  |    - Retry count for current concept                         |
  |    - Which approaches have already been tried                |
  +--------------------------------------------------------------+
```

### 3.2 Intent Classification -- What Does the Student Want?

Every student message must be classified before the AI generates a response.
This classification drives the entire response strategy.

```
  Student sends a message
         |
         v
  +----------------------------------+
  |  INTENT CLASSIFIER               |
  |  (Runs as part of the LLM call   |
  |   via structured system prompt)   |
  +----------------+-----------------+
                   |
     +------+------+------+------+------+------+------+
     |      |      |      |      |      |      |      |
     v      v      v      v      v      v      v      v

  EXPLAIN  QUIZ   HELP   CONFUSED SOCIAL NAVIGATE META  OFF-TOPIC
     |      |      |      |        |      |       |      |
     v      v      v      v        v      v       v      v

  "What    "Test  "I'm   "I      "How   "Go     "How   "What's
  is X?"   me"    stuck  don't    are   back     am I   the
                   on     get     you?" to X"    doing?" weather?"
                   this"  it"
```

**Intent Definitions and Response Strategies:**

| Intent | Signal Words/Patterns | Response Strategy |
|---|---|---|
| **EXPLAIN** | "What is", "How does", "Explain", "Tell me about" | Teach with Socratic method, use examples, check understanding |
| **QUIZ** | "Quiz me", "Test me", "Give me problems" | Switch to assessment mode, generate targeted questions |
| **HELP** | "I'm stuck", "Help me with", "Can you solve" | Ask where exactly they are stuck before helping |
| **CONFUSED** | "I don't get it", "huh?", "what?", "confused", short frustrated replies | Detect which part is confusing, try a completely different approach |
| **SOCIAL** | "How are you", "thanks", greetings | Brief, warm response, then redirect to learning |
| **NAVIGATE** | "Go back to", "Skip", "Next topic", "Let's move on" | Adjust session state, confirm the transition |
| **META** | "How am I doing", "What should I study", "What's my progress" | Pull analytics, give honest assessment with encouragement |
| **OFF-TOPIC** | Unrelated questions, non-academic requests | Gentle redirect: "I'm best at helping you learn -- want to get back to [topic]?" |

**Classification Implementation Approach:**

The intent is not classified by a separate model. Instead, it is embedded
into the system prompt as structured instructions:

```
  +--------------------------------------------------------------+
  |  SYSTEM PROMPT -- INTENT HANDLING INSTRUCTIONS               |
  |                                                              |
  |  "Before responding, internally classify the student's       |
  |   message into one of these categories:                      |
  |                                                              |
  |   - EXPLAIN: They want to learn a concept                    |
  |   - QUIZ: They want to be tested                             |
  |   - HELP: They are stuck on a specific problem               |
  |   - CONFUSED: They did not understand your last response     |
  |   - SOCIAL: They are making conversation                     |
  |   - NAVIGATE: They want to change topics or direction        |
  |   - META: They want progress info or study advice            |
  |   - OFF-TOPIC: Unrelated to learning                         |
  |                                                              |
  |   Then respond according to the strategy for that intent.    |
  |   Include your classification in the response metadata."     |
  +--------------------------------------------------------------+
```

Why not a separate classifier? Because:
1. Adding a separate LLM call doubles latency.
2. The tutor LLM already has full conversation context.
3. The classification only needs to be "good enough" to guide tone, not exact.
4. The metadata tag lets us log and improve classification over time.

### 3.3 Real-Time Adaptation -- Difficulty, Style, and Pacing

The tutor adapts along three axes simultaneously. These are not set once;
they shift within a single session as the student's needs change.

```
  ADAPTATION AXES
  ===============

  DIFFICULTY          STYLE               PACING
  (how hard)          (how it's taught)   (how fast)

  [1] Foundational    [V] Visual          [1] Very slow
  [2] Beginner        [A] Auditory*       [2] Slow
  [3] Intermediate    [R] Reading/Writing [3] Moderate
  [4] Advanced        [K] Kinesthetic**   [4] Fast
  [5] Expert          [S] Socratic        [5] Sprint

  * Auditory = more analogies, storytelling, verbal-style explanations
  ** Kinesthetic = more examples to work through, "try this" exercises

  Starting values come from the student profile.
  They shift based on signals during the conversation.
```

**Adaptation Signal Detection:**

```
  +--------------------------------------------------------------+
  |  SIGNALS THAT THE STUDENT IS DOING WELL                      |
  |                                                              |
  |  - Correct answers to comprehension checks                  |
  |  - Building on the tutor's explanation with their own words |
  |  - Asking deeper "why" or "what if" questions               |
  |  - Requesting harder material ("this is easy")              |
  |  - Quick, confident replies                                 |
  |                                                              |
  |  ACTION: Increase difficulty, increase pacing, introduce     |
  |          more Socratic questioning (they can handle it)      |
  +--------------------------------------------------------------+

  +--------------------------------------------------------------+
  |  SIGNALS THAT THE STUDENT IS STRUGGLING                      |
  |                                                              |
  |  - Wrong answers to checks                                  |
  |  - "I don't understand" or equivalent                       |
  |  - Very short replies ("ok", "sure", "idk")                 |
  |  - Long pauses between messages (> 2 minutes)               |
  |  - Repeating the same question in different words           |
  |  - Asking to "just tell me the answer"                      |
  |                                                              |
  |  ACTION: Decrease difficulty, slow pacing, switch from       |
  |          Socratic to direct explanation, try a new analogy,  |
  |          offer to break the concept into smaller pieces      |
  +--------------------------------------------------------------+

  +--------------------------------------------------------------+
  |  SIGNALS THAT THE STUDENT IS FRUSTRATED                      |
  |                                                              |
  |  - Negative language ("this is stupid", "I hate this")      |
  |  - Rapid short messages ("idk" "idk" "whatever")            |
  |  - Asking to skip or quit                                   |
  |  - Sarcasm or dismissiveness                                |
  |                                                              |
  |  ACTION: Acknowledge the frustration. Do NOT be overly      |
  |          cheerful. Say something real: "This is genuinely    |
  |          a hard topic. Most people struggle with it."        |
  |          Offer a break. Offer to approach it differently.    |
  |          Drop Socratic method entirely -- just explain it    |
  |          clearly and let them absorb it.                     |
  +--------------------------------------------------------------+
```

**Adaptation State Machine:**

```
                    +------------------+
                    |   ASSESS STATE   |
                    | (every 3-5 turns)|
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
        +----------+   +----------+   +----------+
        |  DOING   |   |  STEADY  |   | STRUGGLE |
        |  WELL    |   |  STATE   |   |   ING    |
        +----+-----+   +----+-----+   +----+-----+
             |              |              |
             v              v              v
        Increase       No change      Decrease
        difficulty     in level       difficulty
             |              |              |
             v              v              v
        Try more       Continue       Switch
        Socratic       current        explanation
        questioning    approach       style
             |              |              |
             v              v              v
        Offer to       Periodic       Offer help,
        go deeper      check-in       break, or
        or quiz        question       new approach
             |              |              |
             +------+-------+------+------+
                    |              |
                    v              v
              +----------+   +----------+
              | Continue |   |  LOG     |
              | session  |   |  ADAPT.  |
              +----------+   |  EVENT   |
                             +----------+
```

### 3.4 The Socratic Method Implementation

The Socratic method is central to EduAGI's teaching philosophy. But it must
be used intelligently -- there are times to ask and times to tell.

```
  WHEN TO USE SOCRATIC METHOD          WHEN TO JUST EXPLAIN
  ================================     ================================

  - Student is learning a new           - Student is already frustrated
    concept they have prereqs for       - Student explicitly asks
  - Student gave a partially             "just tell me"
    correct answer                      - The concept is purely
  - Student is trying to solve            factual (dates, definitions)
    a problem                           - Student has failed the same
  - Student seems engaged and             question 3+ times
    willing to think                    - Time pressure (exam tomorrow)
  - Building on known material          - First exposure to a topic
                                          where they have no foundation
```

**Socratic Flow:**

```
  Student asks "What is recursion?"
         |
         v
  +----------------------------------+
  |  EVALUATE: Can I use Socratic?   |
  |                                  |
  |  Does the student know enough    |
  |  to be guided to the answer?     |
  +----------+----------+------------+
             |          |
            YES         NO
             |          |
             v          v
  +----------------+  +----------------+
  |  Ask a leading |  |  Give a brief  |
  |  question      |  |  foundation    |
  |                |  |  explanation   |
  |  "Have you     |  |  first, THEN  |
  |  ever seen a   |  |  switch to    |
  |  function call |  |  Socratic     |
  |  itself?"      |  |               |
  +-------+--------+  +-------+--------+
          |                    |
          v                    v
  +----------------------------------+
  |  Student responds                |
  +----------+----------+------------+
             |          |
          Correct/    Wrong/
          Partial     No idea
             |          |
             v          v
  +----------------+  +----------------+
  |  Build on it   |  |  Give a hint,  |
  |                |  |  not the       |
  |  "Right! Now   |  |  answer        |
  |  what do you   |  |                |
  |  think happens |  |  "Think about  |
  |  if that       |  |  what happens  |
  |  function      |  |  when you      |
  |  never stops   |  |  put two       |
  |  calling       |  |  mirrors       |
  |  itself?"      |  |  facing each   |
  |                |  |  other..."     |
  +-------+--------+  +-------+--------+
          |                    |
          v                    v
  +----------------------------------+
  |  Continue until:                 |
  |                                  |
  |  A) Student articulates the      |
  |     concept in their own words   |
  |     --> Confirm & reinforce      |
  |                                  |
  |  B) Student is stuck after 3     |
  |     guided attempts              |
  |     --> Switch to direct explain |
  |                                  |
  |  C) Student asks to just be told |
  |     --> Respect the request      |
  +----------------------------------+
```

**Socratic Depth Levels:**

```
  Level 1: SURFACE
    "What do you think X means?"
    Used for: Initial exploration, checking existing knowledge

  Level 2: REASONING
    "Why do you think that happens?"
    Used for: Deepening understanding, building causal chains

  Level 3: IMPLICATION
    "What would happen if we changed Y?"
    Used for: Testing flexibility of understanding, edge cases

  Level 4: SYNTHESIS
    "How does this connect to Z that we learned before?"
    Used for: Building knowledge networks, connecting concepts

  Level 5: EVALUATION
    "When would you choose approach A over approach B?"
    Used for: Developing judgment, expert-level thinking
```

### 3.5 Handling "I Don't Understand" -- Retry Strategies

When a student says they do not understand, the worst thing the tutor can
do is repeat the same explanation with minor rewording. EduAGI uses a
structured retry ladder.

```
  Student says: "I don't understand"
         |
         v
  +----------------------------------+
  |  RETRY STRATEGY SELECTOR         |
  |                                  |
  |  Check: Which retry attempt      |
  |  is this for this concept?       |
  +--------+--------+--------+------+
           |        |        |
        1st try  2nd try  3rd try   4th+ try
           |        |        |         |
           v        v        v         v

  +-----------+ +-----------+ +-----------+ +-----------+
  | SIMPLIFY  | | ANALOGY   | | CONCRETE  | | RESET     |
  |           | |           | | EXAMPLE   | |           |
  | Break it  | | Use a     | | Walk      | | "Let's   |
  | into      | | real-world| | through a | | take a   |
  | smaller   | | comparison| | specific  | | step     |
  | pieces.   | | the       | | worked    | | back.    |
  | Remove    | | student   | | example   | | What's   |
  | jargon.   | | can       | | step by   | | the last |
  | One idea  | | relate to | | step      | | thing    |
  | at a time | |           | |           | | that     |
  |           | |           | |           | | DID make |
  |           | |           | |           | | sense?"  |
  +-----------+ +-----------+ +-----------+ +-----------+
```

**Retry Strategy Details:**

```
  RETRY 1: SIMPLIFY
  ==================
  - Identify which specific part is confusing (ask if unclear)
  - Re-explain using simpler vocabulary
  - Break multi-step concept into individual steps
  - Remove all assumed knowledge
  - Example: Instead of "AVL trees maintain O(log n) by enforcing
    a balance invariant," say "AVL trees have one simple rule:
    the left and right sides of any node can't differ in height
    by more than 1."

  RETRY 2: ANALOGY
  ==================
  - Map the concept to something from daily life
  - Connect to the student's known interests (from profile)
  - Make it visual or physical
  - Example: "Think of a balanced tree like a mobile hanging
    from a ceiling. If one side gets too heavy, the whole thing
    tilts. A rotation is like moving a piece from the heavy
    side to the light side to rebalance it."

  RETRY 3: CONCRETE EXAMPLE
  ==========================
  - Stop explaining the theory entirely
  - Walk through a specific, small example
  - Show every step with numbers or code
  - Let the student see the pattern
  - Example: "Let's insert the numbers 3, 2, 1 into an AVL tree.
    Step 1: Insert 3. Tree is just [3]. Step 2: Insert 2.
    Tree is [3] with [2] on the left. Step 3: Insert 1..."

  RETRY 4: RESET
  ==================
  - Acknowledge this is hard
  - Find the last point of solid understanding
  - Rebuild from there using a completely different path
  - Consider if prerequisite knowledge is missing
  - Example: "No worries. Let's find where the confusion starts.
    You're solid on regular binary search trees, right?
    OK. What does 'balanced' mean to you?"

  RETRY 5+: ESCALATION
  ==================
  - Suggest a break ("Sometimes stepping away for 10 minutes helps")
  - Offer to create a focused practice exercise
  - Suggest supplementary resources (videos, textbook sections)
  - Save a flag in the student profile: "struggles with [concept]"
  - Note: Never make the student feel bad for not getting it
```

### 3.6 Comprehension Checks

Comprehension checks happen periodically -- not after every exchange, but
at natural breakpoints when a concept unit has been taught.

```
  COMPREHENSION CHECK TRIGGERS
  ============================

  +--------------------------------------------------------------+
  |  Trigger                               | Check Type           |
  +----------------------------------------+----------------------+
  |  Finished explaining a concept         | Recall check         |
  |  Student said "I get it" or "makes     | Verification check   |
  |  sense" (trust but verify)             |                      |
  |  About to build on concept A to teach  | Prerequisite check   |
  |  concept B                             |                      |
  |  Student has been quiet for a while    | Engagement check     |
  |  End of a session                      | Summary check        |
  |  Every 10-15 minutes of active study   | Periodic check       |
  +----------------------------------------+----------------------+
```

**Check Formats:**

```
  TYPE 1: TEACH-BACK
  "Can you explain [concept] back to me in your own words?"

  TYPE 2: PREDICT
  "Given what you now know, what do you think would happen if [scenario]?"

  TYPE 3: APPLY
  "Try this quick problem: [short exercise]"

  TYPE 4: COMPARE
  "What's the difference between [concept A] and [concept B]?"

  TYPE 5: SPOT THE ERROR
  "I'm going to make a deliberate mistake. Can you find it?
   [Intentionally flawed explanation or code]"
```

**Comprehension Check Flow:**

```
  Trigger fires
       |
       v
  +-------------------------+
  |  Select check type      |
  |  based on context       |
  +------------+------------+
               |
               v
  +-------------------------+
  |  Ask the check question |
  +------------+------------+
               |
               v
  +-------------------------+
  |  Student responds       |
  +------+----------+------+
         |          |
    DEMONSTRATES    DOES NOT
    UNDERSTANDING   DEMONSTRATE
         |          |
         v          v
  +-------------+  +-------------+
  |  Confirm    |  |  Identify   |
  |  and praise |  |  the gap    |
  |  (briefly)  |  |             |
  |             |  |  "Almost!   |
  |  "Exactly   |  |  You've got |
  |  right."    |  |  the first  |
  |             |  |  part. The  |
  |  Log:       |  |  piece      |
  |  concept    |  |  you're     |
  |  UNDERSTOOD |  |  missing    |
  |             |  |  is..."     |
  +------+------+  +------+------+
         |                |
         v                v
  +-------------+  +-------------+
  |  Move on to |  |  Re-teach   |
  |  next       |  |  the gap    |
  |  concept    |  |  (use retry |
  |             |  |  strategies)|
  +-------------+  +-------------+
```

### 3.7 Session Wrap-Up and What Gets Saved

A session does not just end. It wraps up in a way that reinforces learning
and sets up the next session.

```
  SESSION WRAP-UP TRIGGERS
  ========================

  - Student clicks "End Session"
  - Student has been idle > 15 minutes
  - Student says "goodbye" / "I'm done" / "thanks, that's enough"
  - Session duration exceeds 2 hours (suggest a break)
  - Student has run through their allocated session time (free tier)
```

**Wrap-Up Flow:**

```
  Wrap-up triggered
       |
       v
  +----------------------------------+
  |  GENERATE SESSION SUMMARY        |
  |                                  |
  |  1. What topics were covered     |
  |  2. Key concepts explained       |
  |  3. What the student got right   |
  |  4. What still needs work        |
  |  5. Recommended next steps       |
  +----------------+-----------------+
                   |
                   v
  +----------------------------------+
  |  PRESENT TO STUDENT              |
  |                                  |
  |  "Great session! Here's what     |
  |  we covered:                     |
  |                                  |
  |  - AVL tree basics              |
  |  - Right rotations (solid)      |
  |  - Left rotations (solid)       |
  |  - Double rotations (needs      |
  |    more practice)                |
  |                                  |
  |  Next time, I'd suggest we      |
  |  do some practice problems on   |
  |  double rotations.              |
  |                                  |
  |  How confident do you feel?     |
  |  [1] [2] [3] [4] [5]"          |
  +----------------+-----------------+
                   |
                   v
  +----------------------------------+
  |  SAVE SESSION DATA               |
  +----------------------------------+
```

**What Gets Saved After Every Session:**

```
  TO POSTGRESQL (Episodic Memory):
  +--------------------------------------------------------------+
  |  session_record = {                                          |
  |    session_id:        UUID,                                  |
  |    student_id:        UUID,                                  |
  |    started_at:        timestamp,                             |
  |    ended_at:          timestamp,                             |
  |    duration_minutes:  int,                                   |
  |    subject:           "Computer Science",                    |
  |    topics_covered:    ["AVL trees", "rotations"],            |
  |    concepts_mastered: ["right rotation", "left rotation"],   |
  |    concepts_struggling: ["double rotation"],                 |
  |    difficulty_level:  3 (intermediate),                      |
  |    total_messages:    42,                                    |
  |    comprehension_checks: {                                   |
  |      attempted: 4,                                           |
  |      passed: 3,                                              |
  |      failed: 1                                               |
  |    },                                                        |
  |    retry_count:       2,                                     |
  |    student_confidence_rating: 4,                             |
  |    teaching_strategies_used: [                                |
  |      "socratic", "analogy", "worked_example"                 |
  |    ],                                                        |
  |    bookmarked_explanations: [msg_id_17, msg_id_32],          |
  |    token_usage: {                                            |
  |      input_tokens:  12400,                                   |
  |      output_tokens: 8200,                                    |
  |      model:         "claude-sonnet-4-20250514"                |
  |    }                                                         |
  |  }                                                           |
  +--------------------------------------------------------------+

  TO REDIS (Working Memory -- expires after 24h):
  +--------------------------------------------------------------+
  |  - Full conversation history (for quick resume)              |
  |  - Last session context (topic, difficulty, state)           |
  |  - Pending comprehension checks                              |
  |  - Active retry state (which concept, which retry attempt)   |
  +--------------------------------------------------------------+

  TO CHROMADB (Semantic Memory):
  +--------------------------------------------------------------+
  |  - Embeddings of student questions (for pattern analysis)    |
  |  - Embeddings of effective explanations (for reuse)          |
  |  - Updated concept mastery vectors                           |
  +--------------------------------------------------------------+

  TO STUDENT PROFILE (PostgreSQL):
  +--------------------------------------------------------------+
  |  - Updated strengths/weaknesses list                         |
  |  - Updated learning style signals                            |
  |  - Session count incremented                                 |
  |  - Total study time updated                                  |
  |  - Last active timestamp                                     |
  +--------------------------------------------------------------+
```

---

## 4. Sub-Features & Small Touches

These are the details that separate a functional tutoring tool from one
that students actually *want* to use.

### 4.1 Encouragement System

**Philosophy:** Encouragement should feel *earned*, not automated. "Great job!"
after every answer becomes noise. A well-timed "You really nailed that" after
a hard problem feels genuine.

```
  ENCOURAGEMENT RULES
  ====================

  DO:
  +--------------------------------------------------------------+
  |  - Praise after a genuinely difficult question is answered    |
  |    correctly ("That was a hard one -- well done.")            |
  |  - Acknowledge persistence after multiple retries             |
  |    ("You stuck with it and it paid off.")                     |
  |  - Celebrate milestones ("That's 10 concepts mastered in      |
  |    data structures. Solid progress.")                         |
  |  - Normalize difficulty ("This trips up most people. The      |
  |    fact that you're asking about it means you're on the       |
  |    right track.")                                             |
  +--------------------------------------------------------------+

  DO NOT:
  +--------------------------------------------------------------+
  |  - Say "Great job!" after trivial answers                     |
  |  - Use excessive exclamation marks or emojis when the         |
  |    student is frustrated                                      |
  |  - Praise wrong answers ("Good try!" feels condescending)     |
  |    Instead: "Not quite, but your reasoning about X was on     |
  |    the right track."                                          |
  |  - Use the same encouragement phrase twice in a row           |
  |  - Be artificially upbeat when the student is struggling      |
  +--------------------------------------------------------------+

  EMOJI USAGE:
  +--------------------------------------------------------------+
  |  Context                    | Emoji Appropriate?              |
  |-----------------------------+---------------------------------|
  |  Student gets hard Q right  | Subtle OK (checkmark, star)     |
  |  Milestone reached          | Brief celebration               |
  |  Student is frustrated      | NO -- feels dismissive          |
  |  Normal explanation flow    | NO -- distracting               |
  |  Casual greeting/closing    | Light, optional                 |
  |  Student uses emojis first  | Mirror their level              |
  +--------------------------------------------------------------+
```

### 4.2 Code Formatting in Responses

When the tutor includes code in explanations, it must be properly formatted
with language tags for syntax highlighting on the frontend.

```
  CODE FORMATTING RULES
  =====================

  1. Always wrap code in triple-backtick fences with language tag:
     ```python
     def factorial(n):
         if n <= 1:
             return 1
         return n * factorial(n - 1)
     ```

  2. For inline code references, use single backticks:
     "The `factorial` function calls itself with `n - 1`."

  3. For pseudocode (not a specific language), use:
     ```
     FUNCTION factorial(n):
       IF n <= 1: RETURN 1
       RETURN n * factorial(n - 1)
     ```

  4. For terminal/shell commands:
     ```bash
     python3 factorial.py
     ```

  5. When explaining code, use line-by-line annotations:
     ```python
     def factorial(n):        # Base case check
         if n <= 1:           # If n is 0 or 1
             return 1         # Return 1 (base case)
         return n * factorial(n - 1)  # Recursive call
     ```

  6. Maximum code block length: 30 lines. If longer, break into
     sections with explanations between them.
```

**Frontend rendering note:** The frontend must support syntax highlighting
for at least: Python, JavaScript, Java, C/C++, HTML/CSS, SQL, Bash, and
plain pseudocode. Recommended library: Prism.js or highlight.js.

### 4.3 Math Rendering (LaTeX / KaTeX)

Mathematical expressions must be rendered properly, not displayed as
raw ASCII or plaintext.

```
  MATH RENDERING RULES
  ====================

  1. INLINE MATH: Wrap in single dollar signs
     "The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$"

  2. DISPLAY MATH: Wrap in double dollar signs (centered, block)
     $$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$$

  3. The LLM system prompt instructs the tutor to always use LaTeX
     notation for mathematical expressions.

  4. The frontend renders LaTeX using KaTeX (preferred for speed)
     or MathJax (fallback for complex expressions).

  5. When explaining step-by-step math:
     - Show each step as a separate display math block
     - Add text between steps explaining the transformation
     - Example:

       "Starting with:"
       $$x^2 + 5x + 6 = 0$$

       "We need two numbers that multiply to 6 and add to 5:"
       $$(x + 2)(x + 3) = 0$$

       "Setting each factor to zero:"
       $$x = -2 \quad \text{or} \quad x = -3$$

  6. For students who have trouble with LaTeX rendering (accessibility),
     always include a plain-text fallback description in the response
     metadata.
```

### 4.4 Diagram Suggestions

The tutor should detect when a visual diagram would help and either
generate an ASCII diagram inline or suggest that the student view a
visual aid.

```
  WHEN TO SUGGEST DIAGRAMS
  ========================

  +--------------------------------------------------------------+
  |  Topic Type            | Diagram Type                        |
  +------------------------+-------------------------------------|
  |  Data structures       | ASCII tree/graph/stack/queue        |
  |  Algorithms            | Step-by-step state diagrams         |
  |  System architecture   | Box-and-arrow diagrams              |
  |  Math functions        | Coordinate plane / graph sketches   |
  |  Chemistry             | Molecular structure descriptions    |
  |  Biology               | Process flow (photosynthesis, etc.) |
  |  Physics               | Force diagrams, circuit diagrams    |
  |  Flowcharts            | Decision/process flows              |
  +--------------------------------------------------------------+

  IMPLEMENTATION:
  - For text mode: ASCII art diagrams inline
  - Future: Mermaid.js diagram generation via tool call
  - Future: Integration with diagramming API for rich visuals
  - Always describe the diagram in text as well (accessibility)
```

### 4.5 "Explain Like I'm 5" Mode (ELI5)

A special mode the student can activate at any time that drastically
simplifies the current explanation.

```
  ELI5 MODE
  =========

  Triggered by:
  - Student clicks "Explain like I'm 5" button
  - Student types "explain it simpler" or "ELI5" or "dumb it down"

  What changes:
  +--------------------------------------------------------------+
  |  Normal Mode                    | ELI5 Mode                  |
  +---------------------------------+----------------------------|
  |  Technical vocabulary           | Everyday words             |
  |  Abstract concepts              | Physical analogies         |
  |  Formal definitions             | "It's like when..."        |
  |  Assumed prerequisite knowledge | Zero assumptions           |
  |  Multi-step explanations        | One idea at a time         |
  |  Code examples                  | Real-world examples only   |
  |  Mathematical notation          | Numbers and counting       |
  +---------------------------------+----------------------------+

  Example:
    Normal: "A hash table provides O(1) average-case lookup by
            computing a hash function on the key to determine the
            storage index."

    ELI5:   "Imagine you have a huge wall of mailboxes, numbered
            1 to 1000. You have a magic formula that turns any
            name into a mailbox number. When you want to store
            something for 'Alice', the formula says 'mailbox 42'.
            When you want to find Alice's stuff later, you run
            the same formula, get 42 again, and go straight there.
            No searching. That's a hash table."

  The mode persists for the current concept only. When the student
  moves to a new topic, the tutor returns to the difficulty level
  in their profile.
```

### 4.6 Study Timer / Pomodoro Integration

Students study better with structured time. The tutor can optionally
manage a study timer.

```
  POMODORO INTEGRATION
  ====================

  Default Pomodoro: 25 min study / 5 min break
  Configurable:     15-50 min study / 5-15 min break

  +--------------------------------------------------------------+
  |  Timer starts when session begins (if enabled in prefs)      |
  |                                                              |
  |  At 5 min remaining:                                         |
  |    "Heads up -- 5 minutes left in this study block.          |
  |     Let's wrap up the current concept."                      |
  |                                                              |
  |  At timer end:                                               |
  |    "Time for a break! You covered [X, Y, Z] in this block.  |
  |     Stand up, stretch, grab water.                           |
  |     I'll be here when you're ready."                         |
  |                                                              |
  |  After break:                                                |
  |    "Welcome back. Quick recap of where we were:              |
  |     [brief summary]. Ready to continue?"                     |
  +--------------------------------------------------------------+

  Implementation:
  - Timer runs on the frontend (JavaScript)
  - The backend is notified of timer events via WebSocket
  - The tutor adjusts its pacing to align with remaining time
  - Timer state is persisted so it survives page refreshes
```

### 4.7 Bookmark / Save Important Explanations

Students should be able to flag specific explanations as worth saving
for later review.

```
  BOOKMARK FEATURE
  ================

  Student action:
  - Click bookmark icon on any tutor message
  - Or type "save that" / "bookmark this"

  What gets saved:
  +--------------------------------------------------------------+
  |  bookmark = {                                                |
  |    id:                UUID,                                  |
  |    student_id:        UUID,                                  |
  |    session_id:        UUID,                                  |
  |    message_id:        UUID,                                  |
  |    message_content:   "Full text of the explanation...",     |
  |    topic:             "AVL tree rotations",                  |
  |    subject:           "Computer Science",                    |
  |    created_at:        timestamp,                             |
  |    tags:              ["data-structures", "trees"],          |
  |    student_note:      "This analogy really helped" (optional)|
  |  }                                                           |
  +--------------------------------------------------------------+

  Access:
  - Bookmarks page in the UI (searchable, filterable by subject)
  - "Show my bookmarks on [topic]" in chat
  - Exported as study notes (Markdown / PDF)

  Storage: PostgreSQL table `bookmarks`
```

### 4.8 "Teach Me Differently" Button

A one-click way to say "your current approach isn't working for me"
without having to articulate what is wrong.

```
  "TEACH ME DIFFERENTLY" FLOW
  ============================

  Student clicks [Teach Me Differently]
         |
         v
  +----------------------------------+
  |  STRATEGY ROTATION               |
  |                                  |
  |  1. Check which strategies have  |
  |     already been used for this   |
  |     concept in this session      |
  |                                  |
  |  2. Select the NEXT strategy     |
  |     from the rotation that has   |
  |     NOT been tried yet:          |
  |                                  |
  |     a) Analogy/metaphor          |
  |     b) Concrete worked example   |
  |     c) Step-by-step breakdown    |
  |     d) Visual/diagram            |
  |     e) Compare/contrast with     |
  |        known concept             |
  |     f) Interactive exercise      |
  |        ("try this yourself")     |
  |     g) Real-world application    |
  |     h) Historical context        |
  |        ("why was this invented?") |
  |                                  |
  |  3. If ALL strategies exhausted: |
  |     "I've tried several ways.    |
  |      Would it help to:           |
  |      - Take a break              |
  |      - Try a practice problem    |
  |      - Look at a video resource  |
  |      - Come back to this later"  |
  +----------------------------------+
```

### 4.9 Quick Action Buttons

Persistent buttons below the chat input that let the student take
common actions without typing.

```
  QUICK ACTION BUTTONS
  ====================

  +------------------------------------------------------------------+
  |                                                                    |
  |  [ Give me an example ]  [ Simplify ]  [ Go deeper ]  [ Quiz me ]|
  |                                                                    |
  +------------------------------------------------------------------+

  Button Behaviors:

  [Give me an example]
    - Sends: "Can you give me a concrete example of what you
      just explained?"
    - Tutor generates a specific, worked example related to
      the current concept.

  [Simplify]
    - Sends: "Can you explain that more simply?"
    - Triggers retry strategy level 1 (simplify) for the
      most recent concept.

  [Go deeper]
    - Sends: "I understand the basics. Can you go deeper into
      how this works under the hood?"
    - Increases difficulty level for the current concept.
    - Introduces edge cases, implementation details, or theory.

  [Quiz me]
    - Sends: "Quiz me on what we've covered so far."
    - Triggers the Assessment Agent to generate 3-5 quick
      questions on the current session's topics.
    - Returns to tutoring mode after the quiz.

  CONTEXTUAL BUTTONS (appear based on situation):

  [Teach me differently]
    - Appears after a retry or when confusion is detected.

  [Explain like I'm 5]
    - Appears when difficulty seems too high.

  [Show me the code]
    - Appears when discussing programming concepts.

  [Take a break]
    - Appears after 25+ minutes of continuous study.

  [What should I study next?]
    - Appears at session end or when a topic is mastered.
```

### 4.10 Conversation Branching (Tangent & Return)

Students naturally go on tangents. The tutor must support this without
losing the original thread.

```
  BRANCHING FLOW
  ==============

  Main topic: AVL Trees
       |
       |  Student: "Wait, what's a pointer again?"
       |
       +----> BRANCH: Pointers (tangent)
       |          |
       |          |  Tutor explains pointers
       |          |
       |          |  Student: "Ok got it, back to AVL"
       |          |
       +<---------+  RETURN to AVL Trees
       |
       |  Continues where it left off
       v

  IMPLEMENTATION:
  +--------------------------------------------------------------+
  |  The system maintains a TOPIC STACK:                         |
  |                                                              |
  |  topic_stack = [                                             |
  |    {                                                         |
  |      topic: "AVL Trees",                                     |
  |      last_message_index: 23,                                 |
  |      state: "paused",                                        |
  |      context_summary: "Explained right rotation, was about   |
  |                        to start left-right rotation"          |
  |    },                                                         |
  |    {                                                         |
  |      topic: "Pointers",                                      |
  |      last_message_index: 27,                                 |
  |      state: "active",                                        |
  |      context_summary: "Explaining memory addresses"          |
  |    }                                                         |
  |  ]                                                           |
  |                                                              |
  |  When student returns:                                       |
  |  - Pop the tangent topic                                     |
  |  - Restore the previous topic's context                      |
  |  - Tutor says: "Great, back to AVL trees. We were about      |
  |    to look at the left-right rotation case..."               |
  |                                                              |
  |  Maximum stack depth: 3 (to prevent infinite tangents)       |
  |  If depth exceeded: "We've gone pretty far from the          |
  |  original topic. Want to wrap up [current tangent] and       |
  |  get back to [original topic]?"                              |
  +--------------------------------------------------------------+
```

### 4.11 Mood Detection and Adaptive Tone

The tutor monitors emotional signals in the student's messages and
adjusts its tone accordingly.

```
  MOOD DETECTION
  ==============

  +--------------------------------------------------------------+
  |  Detected Mood     | Signals                | Tutor Response |
  +--------------------+------------------------+----------------|
  |  Engaged/Curious   | "Interesting!", long   | Match energy,  |
  |                    | thoughtful questions,  | encourage      |
  |                    | "Tell me more"         | exploration    |
  |                    |                        |                |
  |  Confident         | Correct answers,       | Challenge them |
  |                    | "That's easy",         | more, increase |
  |                    | quick responses        | difficulty     |
  |                    |                        |                |
  |  Neutral/Working   | Normal responses,      | Stay the       |
  |                    | on-topic, moderate     | course, steady |
  |                    | engagement             | pacing         |
  |                    |                        |                |
  |  Confused          | "Huh?", "What?",       | Slow down,     |
  |                    | wrong answers, silence | simplify,      |
  |                    | after explanation       | check in       |
  |                    |                        |                |
  |  Frustrated        | "I give up", negative  | Acknowledge,   |
  |                    | language, short angry  | empathize,     |
  |                    | replies                | offer break    |
  |                    |                        |                |
  |  Bored             | "Ok", "sure", very     | Make it more   |
  |                    | short replies, slow    | interactive,   |
  |                    | response times         | try a quiz or  |
  |                    |                        | real-world tie |
  |                    |                        |                |
  |  Anxious/Stressed  | "I have an exam",      | Be reassuring  |
  |                    | "I'll never get this", | but practical, |
  |                    | self-deprecating       | focus on what  |
  |                    |                        | they CAN do    |
  +--------------------+------------------------+----------------+

  IMPLEMENTATION:
  - Mood detection is part of the system prompt instructions
  - The LLM classifies mood alongside intent in its internal
    reasoning before generating a response
  - Mood is logged with each message for analytics
  - No separate sentiment analysis model needed -- the main LLM
    is already reading the full conversation context
```

---

## 5. Technical Requirements

### 5.1 API Requirements

#### 5.1.1 Primary LLM -- Anthropic Claude API

```
  CLAUDE API USAGE
  ================

  Model Selection Strategy:
  +--------------------------------------------------------------+
  |  Task                        | Model                | Why     |
  +------------------------------+------------------------+-------|
  |  Main tutoring conversation  | claude-sonnet-4-20250514  | Best    |
  |                              |                        | balance |
  |                              |                        | of cost |
  |                              |                        | speed & |
  |                              |                        | quality |
  |                              |                        |         |
  |  Complex reasoning tasks     | claude-opus-4-0-20250115  | Deep    |
  |  (proof verification, essay  |                        | reason  |
  |   grading, advanced math)    |                        | ing     |
  |                              |                        |         |
  |  Simple tasks (intent        | claude-haiku-3-5       | Fast &  |
  |  classification backup,      |                        | cheap   |
  |  formatting, summarization)  |                        |         |
  +--------------------------------------------------------------+

  API Configuration:
  +--------------------------------------------------------------+
  |  Endpoint:     https://api.anthropic.com/v1/messages         |
  |  Auth:         x-api-key header with ANTHROPIC_API_KEY       |
  |  Streaming:    YES (required for real-time chat experience)  |
  |  Max tokens:   4096 for responses, 200K context window       |
  |  Temperature:  0.7 for tutoring, 0.3 for assessment/grading |
  |  System:       Dynamic system prompt (see Section 3.1)       |
  +--------------------------------------------------------------+

  Streaming Response Format:
  +--------------------------------------------------------------+
  |  The API streams Server-Sent Events (SSE). Each event:       |
  |                                                              |
  |  event: content_block_delta                                  |
  |  data: {"type":"content_block_delta",                        |
  |         "delta":{"type":"text_delta","text":"chunk..."}}     |
  |                                                              |
  |  The backend receives these and forwards them over WebSocket |
  |  to the frontend for real-time text rendering.               |
  +--------------------------------------------------------------+
```

#### 5.1.2 Embedding Models

```
  EMBEDDING MODEL
  ===============

  Primary:   OpenAI text-embedding-3-small
  Fallback:  OpenAI text-embedding-ada-002

  Usage:
  - Embedding student questions for similarity search
  - Embedding curriculum content for RAG retrieval
  - Embedding effective explanations for reuse

  Dimensions: 1536 (ada-002) or 512/1536 configurable (3-small)
  Storage:    ChromaDB vector store
```

#### 5.1.3 MCP Servers

```
  MCP (Model Context Protocol) SERVERS
  =====================================

  MCP Server 1: Filesystem MCP
  +--------------------------------------------------------------+
  |  Purpose:  Allow the tutor to read uploaded student documents |
  |            (PDFs, notes, textbook chapters)                   |
  |  When:     Student uploads a file and says "help me with this"|
  |  How:      Claude accesses file content via MCP tool call     |
  |  Config:   Restricted to student's upload directory only      |
  +--------------------------------------------------------------+

  MCP Server 2: Database MCP (Future)
  +--------------------------------------------------------------+
  |  Purpose:  Allow the tutor to query student progress data     |
  |            directly during conversation                       |
  |  When:     Student asks "How am I doing in calculus?"         |
  |  How:      Claude runs a read-only SQL query via MCP          |
  |  Config:   Read-only access, student-scoped queries only      |
  +--------------------------------------------------------------+

  MCP Server 3: Web Search MCP (Future)
  +--------------------------------------------------------------+
  |  Purpose:  Allow the tutor to look up current information     |
  |            not in the knowledge base                          |
  |  When:     Question about recent events, new frameworks, etc. |
  |  How:      Claude searches the web via MCP tool call          |
  |  Config:   Rate-limited, educational content preferred        |
  +--------------------------------------------------------------+
```

### 5.2 Database Connections

```
  DATA FLOW MAP
  =============

  +-------------------+    +------------------+    +-------------------+
  |                   |    |                  |    |                   |
  |    POSTGRESQL     |    |      REDIS       |    |     CHROMADB      |
  |                   |    |                  |    |                   |
  | - Student profile |    | - Session state  |    | - Knowledge base  |
  | - Session records |    | - Conversation   |    |   embeddings      |
  | - Learning events |    |   history (live) |    | - Question bank   |
  | - Bookmarks       |    | - Current topic  |    |   embeddings      |
  | - Assessment data |    |   stack          |    | - Student question|
  | - Concept mastery |    | - Timer state    |    |   embeddings      |
  |   records         |    | - Rate limit     |    | - Effective       |
  |                   |    |   counters       |    |   explanation     |
  |                   |    | - Active user    |    |   embeddings      |
  |                   |    |   sessions       |    |                   |
  +-------------------+    +------------------+    +-------------------+
         |                        |                        |
         |      +-----------------+----------------+       |
         |      |                                  |       |
         +------+    TUTORING SERVICE (FastAPI)    +-------+
                |                                  |
                +----------+----------+------------+
                           |          |
                    WebSocket    REST API
                    (streaming   (session mgmt,
                     chat)       bookmarks, etc.)
                           |          |
                           +----+-----+
                                |
                           FRONTEND
                           (React)
```

### 5.3 WebSocket vs REST -- When to Use Which

```
  COMMUNICATION PROTOCOL DECISIONS
  =================================

  +--------------------------------------------------------------+
  |  Operation                      | Protocol | Why              |
  +---------------------------------+----------+------------------|
  |  Sending a message to tutor     | WebSocket| Real-time,       |
  |                                 |          | streaming resp.  |
  |                                 |          |                  |
  |  Receiving streamed response    | WebSocket| Token-by-token   |
  |                                 |          | delivery needed  |
  |                                 |          |                  |
  |  Creating a session             | REST POST| One-time action, |
  |                                 |          | needs response   |
  |                                 |          | confirmation     |
  |                                 |          |                  |
  |  Loading session history        | REST GET | Paginated data,  |
  |                                 |          | cacheable        |
  |                                 |          |                  |
  |  Saving a bookmark              | REST POST| Fire-and-forget  |
  |                                 |          | action           |
  |                                 |          |                  |
  |  Fetching student profile       | REST GET | Static data,     |
  |                                 |          | cacheable        |
  |                                 |          |                  |
  |  Timer events                   | WebSocket| Bidirectional,   |
  |                                 |          | real-time sync   |
  |                                 |          |                  |
  |  Typing indicator               | WebSocket| Low-latency      |
  |                                 |          | ephemeral events |
  +--------------------------------------------------------------+
```

### 5.4 Streaming Response Handling

```
  STREAMING ARCHITECTURE
  ======================

  Claude API          Backend            WebSocket         Frontend
  (SSE stream)        (FastAPI)          Connection        (React)
       |                  |                  |                |
       |  content_delta   |                  |                |
       |----------------->|                  |                |
       |                  |  ws: text_chunk  |                |
       |                  |----------------->|                |
       |                  |                  |  append text   |
       |                  |                  |--------------->|
       |  content_delta   |                  |                |
       |----------------->|                  |                |
       |                  |  ws: text_chunk  |                |
       |                  |----------------->|                |
       |                  |                  |  append text   |
       |                  |                  |--------------->|
       |                  |                  |                |
       |   ...continues...|                  |                |
       |                  |                  |                |
       |  message_stop    |                  |                |
       |----------------->|                  |                |
       |                  | Save complete    |                |
       |                  | message to DB    |                |
       |                  |                  |                |
       |                  |  ws: msg_complete|                |
       |                  |----------------->|                |
       |                  |                  | Show action    |
       |                  |                  | buttons        |
       |                  |                  |--------------->|
       |                  |                  |                |

  IMPORTANT DETAILS:
  +--------------------------------------------------------------+
  |  1. The backend buffers chunks and performs basic processing: |
  |     - Detects code blocks (``` markers) to send them as      |
  |       complete units when possible                           |
  |     - Detects LaTeX blocks ($ markers) to send complete      |
  |       expressions                                            |
  |     - Detects sentence boundaries for smoother rendering     |
  |                                                              |
  |  2. The frontend renders incrementally:                      |
  |     - Plain text: append character by character              |
  |     - Code blocks: render when block is complete             |
  |     - Math: render when expression is complete               |
  |     - Markdown: re-render paragraph on each chunk            |
  |                                                              |
  |  3. Error handling:                                          |
  |     - If stream drops, attempt reconnect within 3 seconds    |
  |     - If reconnect fails, fall back to REST polling          |
  |     - Partial messages are saved and marked as incomplete    |
  +--------------------------------------------------------------+
```

### 5.5 Rate Limiting Per Student

```
  RATE LIMITING STRATEGY
  ======================

  Layer 1: API Gateway (Nginx / CloudFront)
  +--------------------------------------------------------------+
  |  Global rate limit: 1000 requests/minute per IP              |
  |  Protects against DDoS, applies to all endpoints             |
  +--------------------------------------------------------------+

  Layer 2: Application Rate Limiter (Redis-based)
  +--------------------------------------------------------------+
  |  Per-student limits (sliding window):                        |
  |                                                              |
  |  Tier     | Messages/min | LLM calls/min | Sessions/day     |
  |-----------|--------------|---------------|------------------|
  |  Free     | 10           | 10            | 5                |
  |  Student  | 30           | 30            | 20               |
  |  Pro      | 60           | 60            | Unlimited        |
  |  School   | 60           | 60            | Unlimited        |
  |                                                              |
  |  Implementation: Redis INCR with TTL                         |
  |  Key pattern: rate:{student_id}:{endpoint}:{window}          |
  +--------------------------------------------------------------+

  Layer 3: Token Budget (Cost Control)
  +--------------------------------------------------------------+
  |  Per-student daily token budget:                             |
  |                                                              |
  |  Tier     | Input tokens/day | Output tokens/day             |
  |-----------|------------------|-------------------------------|
  |  Free     | 50,000           | 25,000                        |
  |  Student  | 200,000          | 100,000                       |
  |  Pro      | 1,000,000        | 500,000                       |
  |  School   | 500,000          | 250,000                       |
  |                                                              |
  |  Tracked in Redis, reset at midnight UTC                     |
  |  When 80% consumed: warn student                             |
  |  When 100% consumed: graceful denial with explanation        |
  +--------------------------------------------------------------+

  User-facing message when rate limited:
  "You've been studying hard today! You've used your daily
   message allowance. Your limit resets at midnight, or you
   can upgrade for more study time. In the meantime, try
   reviewing your bookmarked explanations."
```

### 5.6 Token Usage Optimization

```
  TOKEN OPTIMIZATION STRATEGIES
  ==============================

  1. SYSTEM PROMPT COMPRESSION
  +--------------------------------------------------------------+
  |  Problem: System prompts can be 2000-4000 tokens             |
  |  Solution:                                                   |
  |  - Use structured, concise formatting (no prose in prompts)  |
  |  - Only include relevant student profile fields              |
  |  - Only include recent session context (not full history)    |
  |  - Compress RAG context to top-3 most relevant chunks        |
  |  Target: System prompt under 2000 tokens                     |
  +--------------------------------------------------------------+

  2. CONVERSATION HISTORY WINDOWING
  +--------------------------------------------------------------+
  |  Problem: Full conversation can be 50,000+ tokens            |
  |  Solution:                                                   |
  |  - Keep last 10 message pairs in full                        |
  |  - Summarize older messages into a "session so far" block    |
  |  - Summary generated by Haiku (cheap, fast)                  |
  |  - Summary refresh: every 20 messages                        |
  |  Target: Conversation context under 8000 tokens              |
  +--------------------------------------------------------------+

  3. RAG CONTEXT OPTIMIZATION
  +--------------------------------------------------------------+
  |  Problem: Retrieved documents can be very long               |
  |  Solution:                                                   |
  |  - Retrieve 5 chunks, re-rank, keep top 3                   |
  |  - Truncate each chunk to 500 tokens max                    |
  |  - Deduplicate overlapping content                           |
  |  Target: RAG context under 1500 tokens                       |
  +--------------------------------------------------------------+

  4. RESPONSE LENGTH GUIDANCE
  +--------------------------------------------------------------+
  |  Problem: LLM may generate unnecessarily long responses      |
  |  Solution:                                                   |
  |  - System prompt instructs: "Be concise. One concept per     |
  |    response. If the student wants more, they'll ask."        |
  |  - Hard cap: max_tokens=1500 for tutoring responses          |
  |  - Exception: worked examples and code may be longer         |
  |  Target: Average response under 800 tokens                   |
  +--------------------------------------------------------------+

  5. CACHING
  +--------------------------------------------------------------+
  |  Cache Layer         | What                | TTL              |
  |----------------------|---------------------|------------------|
  |  Redis               | Common Q&A pairs    | 24 hours         |
  |  Redis               | RAG query results   | 1 hour           |
  |  Redis               | Session summaries   | Session duration |
  |  Application memory  | System prompt       | Session duration |
  |                      | templates           |                  |
  +--------------------------------------------------------------+

  ESTIMATED TOKEN USAGE PER SESSION (30 minutes):
  +--------------------------------------------------------------+
  |  Component           | Input tokens | Output tokens           |
  |----------------------|--------------|-------------------------|
  |  System prompt       | 2,000        | --                      |
  |  Conversation (20    | 6,000        | 12,000                  |
  |  exchanges)          |              |                         |
  |  RAG context         | 1,500        | --                      |
  |  Summary generation  | 2,000        | 500                     |
  |  Comprehension check | 500          | 300                     |
  |  TOTAL               | ~12,000      | ~12,800                 |
  +--------------------------------------------------------------+
  |  Estimated cost per session (Sonnet):                        |
  |  Input:  12,000 tokens x $3.00/MTok  = $0.036               |
  |  Output: 12,800 tokens x $15.00/MTok = $0.192               |
  |  TOTAL: ~$0.23 per 30-minute session                         |
  +--------------------------------------------------------------+
```

---

## 6. Services & Alternatives

### 6.1 Primary LLM: Claude (Anthropic)

```
  WHY CLAUDE IS THE PRIMARY CHOICE
  ==================================

  +--------------------------------------------------------------+
  |  Criteria              | Claude Rating | Notes                |
  |------------------------|---------------|----------------------|
  |  Educational tone      | Excellent     | Patient, clear,      |
  |                        |               | encouraging by       |
  |                        |               | default              |
  |                        |               |                      |
  |  Socratic capability   | Excellent     | Naturally asks        |
  |                        |               | guiding questions    |
  |                        |               |                      |
  |  Math/Science accuracy | Very Good     | Strong reasoning,    |
  |                        |               | good with proofs     |
  |                        |               |                      |
  |  Code generation       | Excellent     | Clear explanations   |
  |                        |               | with code            |
  |                        |               |                      |
  |  Safety/Guardrails     | Excellent     | Won't generate       |
  |                        |               | harmful content,     |
  |                        |               | critical for minors  |
  |                        |               |                      |
  |  Streaming support     | Yes           | SSE streaming        |
  |                        |               |                      |
  |  Context window        | 200K tokens   | Handles long         |
  |                        |               | sessions easily      |
  |                        |               |                      |
  |  API reliability       | High          | Stable, good uptime  |
  +--------------------------------------------------------------+

  MODEL PRICING (as of February 2026):
  +--------------------------------------------------------------+
  |  Model               | Input/MTok | Output/MTok | Context    |
  |----------------------|------------|-------------|------------|
  |  claude-opus-4-0-20250115  | $15.00     | $75.00      | 200K       |
  |  claude-sonnet-4-20250514  | $3.00      | $15.00      | 200K       |
  |  claude-haiku-3-5    | $0.80      | $4.00       | 200K       |
  +--------------------------------------------------------------+

  RECOMMENDED MIX:
  - 80% of calls: Sonnet (main tutoring)
  - 10% of calls: Haiku (summarization, simple classification)
  - 10% of calls: Opus (complex grading, advanced reasoning)
```

### 6.2 Alternative: GPT-4 (OpenAI)

```
  GPT-4 AS FALLBACK
  ==================

  When to use:
  +--------------------------------------------------------------+
  |  1. Claude API is down or rate-limited                       |
  |  2. Specific task where GPT-4 excels (function calling,      |
  |     structured JSON output)                                  |
  |  3. A/B testing teaching effectiveness                       |
  +--------------------------------------------------------------+

  Model options:
  +--------------------------------------------------------------+
  |  Model            | Input/MTok | Output/MTok | Context        |
  |--------------------|------------|-------------|---------------|
  |  gpt-4o           | $2.50      | $10.00      | 128K          |
  |  gpt-4o-mini      | $0.15      | $0.60       | 128K          |
  |  gpt-4-turbo      | $10.00     | $30.00      | 128K          |
  +--------------------------------------------------------------+

  Pros:
  - Strong function calling / tool use
  - Good at structured output (JSON mode)
  - Large ecosystem and community
  - GPT-4o-mini is extremely cheap for simple tasks

  Cons:
  - Less naturally "patient" as a tutor (needs more prompt work)
  - Smaller context window than Claude (128K vs 200K)
  - Safety guardrails less nuanced for educational context
  - Different system prompt format required (adds maintenance)
```

### 6.3 Alternative: Gemini (Google)

```
  GEMINI CONSIDERATION
  =====================

  Model options:
  +--------------------------------------------------------------+
  |  Model              | Input/MTok | Output/MTok | Context      |
  |---------------------|------------|-------------|-------------|
  |  gemini-2.0-flash   | $0.10      | $0.40       | 1M          |
  |  gemini-1.5-pro     | $1.25      | $5.00       | 2M          |
  +--------------------------------------------------------------+

  Pros:
  - Extremely large context window (up to 2M tokens)
  - Very cheap (especially Flash)
  - Good multimodal support (could read diagrams from uploads)
  - Google Workspace integration possibilities

  Cons:
  - Less consistent educational tone
  - Requires more prompt engineering for tutoring style
  - API stability historically less reliable than Claude/OpenAI
  - Gemini Pro needed for quality comparable to Sonnet

  Best use case for EduAGI:
  - Processing very long documents (textbooks, papers) where
    the 2M context window is valuable
  - Bulk document summarization tasks
  - Cost-sensitive operations where quality can be slightly lower
```

### 6.4 Alternative: Open-Source Models (Llama, Mistral)

```
  OPEN-SOURCE OPTIONS
  ====================

  Models:
  +--------------------------------------------------------------+
  |  Model              | Parameters | Quality  | Self-host Cost  |
  |---------------------|------------|----------|-----------------|
  |  Llama 3.1 70B      | 70B        | Good     | ~$2/hr (A100)   |
  |  Llama 3.1 405B     | 405B       | V. Good  | ~$8/hr (multi)  |
  |  Mistral Large      | ~100B+     | Good     | ~$3/hr (A100)   |
  |  Mixtral 8x22B      | 141B MoE   | Good     | ~$3/hr (A100)   |
  +--------------------------------------------------------------+

  Pros:
  - No per-token API cost after infrastructure setup
  - Full control over model behavior and fine-tuning
  - No vendor lock-in
  - Can be fine-tuned on educational data for better tutoring
  - Data stays on-premise (privacy benefit)

  Cons:
  - Quality gap vs Claude Sonnet/Opus for complex reasoning
  - Requires ML ops team to maintain infrastructure
  - GPU costs are significant for 70B+ models
  - No streaming-optimized API out of the box (need vLLM/TGI)
  - Fine-tuning requires labeled educational data

  Recommended approach:
  - Phase 1-5 (MVP): Use Claude/OpenAI APIs exclusively
  - Phase 6+: Evaluate fine-tuned Llama 3.1 70B for:
    * Simple Q&A (offload from Haiku)
    * Practice problem generation
    * Summarization tasks
  - Calculate: At what student volume does self-hosting
    become cheaper than API calls?
  - Estimated breakeven: ~10,000 daily active sessions
```

### 6.5 Embedding Model Options

```
  EMBEDDING MODELS COMPARISON
  ============================

  +--------------------------------------------------------------+
  |  Model                    | Dims  | Cost/MTok | Quality      |
  |---------------------------|-------|-----------|-------------|
  |  OpenAI text-embedding-   | 1536  | $0.02     | Excellent   |
  |  3-small                  |       |           |             |
  |  OpenAI text-embedding-   | 3072  | $0.13     | Best        |
  |  3-large                  |       |           |             |
  |  Cohere embed-english-v3  | 1024  | $0.10     | Very Good   |
  |  Voyage-3                 | 1024  | $0.06     | Very Good   |
  |  BGE-large-en-v1.5        | 1024  | Free*     | Good        |
  |  (self-hosted)            |       |           |             |
  +--------------------------------------------------------------+
  * Free = self-hosted, but requires GPU infrastructure

  RECOMMENDATION:
  - Primary: OpenAI text-embedding-3-small ($0.02/MTok, excellent
    quality, low cost)
  - Evaluate: Voyage-3 if Anthropic partnership pricing available
  - Future: Self-hosted BGE model if embedding volume exceeds
    $500/month in API costs
```

### 6.6 Prompt Management & Observability

```
  PROMPT MANAGEMENT TOOLS
  ========================

  +--------------------------------------------------------------+
  |  Tool          | Purpose              | When to Use           |
  |----------------|----------------------|-----------------------|
  |  LangSmith     | Prompt tracing,      | Development &         |
  |  (LangChain)   | debugging, A/B       | production monitoring |
  |                | testing prompts      |                       |
  |                |                      |                       |
  |  Anthropic     | Prompt testing,      | Prompt development,   |
  |  Workbench     | model comparison     | iteration             |
  |                |                      |                       |
  |  Custom prompt | Version control for  | Managing 10+ prompt   |
  |  registry      | system prompts,      | templates across      |
  |  (PostgreSQL)  | A/B test configs     | agents                |
  |                |                      |                       |
  |  Helicone      | LLM cost tracking,   | Cost monitoring,      |
  |                | latency monitoring   | usage analytics       |
  +--------------------------------------------------------------+

  PROMPT VERSIONING STRATEGY:
  - All system prompts stored in a prompt_templates table
  - Each template has a version number and active/inactive flag
  - A/B testing: assign students to prompt versions randomly
  - Track effectiveness metrics per prompt version:
    * Comprehension check pass rate
    * Retry frequency
    * Student satisfaction rating
    * Session duration
```

---

## 7. Connections & Dependencies

### 7.1 What F01 Depends On

```
  UPSTREAM DEPENDENCIES
  =====================

  +--------------------------------------------------------------+
  |  Dependency              | Why F01 Needs It     | Critical?  |
  |--------------------------|----------------------|------------|
  |  Authentication Service  | Must know who the    | YES        |
  |  (Auth)                  | student is           |            |
  |                          |                      |            |
  |  Student Profile Service | Learning style, pace,| YES        |
  |  (User Management)       | history, preferences |            |
  |                          |                      |            |
  |  Memory System           | Session context,     | YES        |
  |  (Redis + PostgreSQL)    | conversation history |            |
  |                          |                      |            |
  |  RAG / Knowledge Base    | Curriculum content   | YES        |
  |  (ChromaDB)              | for grounded answers | (degrades  |
  |                          |                      |  gracefully|
  |                          |                      |  without)  |
  |                          |                      |            |
  |  WebSocket Service       | Real-time streaming  | YES        |
  |  (FastAPI)               | chat                 |            |
  |                          |                      |            |
  |  Claude API              | The LLM itself       | YES        |
  |  (Anthropic)             |                      |            |
  +--------------------------------------------------------------+
```

### 7.2 What Depends on F01

```
  DOWNSTREAM DEPENDENTS
  =====================

  +--------------------------------------------------------------+
  |  Feature                     | How It Uses F01               |
  |------------------------------|-------------------------------|
  |  F02: Voice Synthesis        | Takes F01 text output and     |
  |  (ElevenLabs)                | converts to speech            |
  |                              |                               |
  |  F03: Avatar Presentation    | Takes F01 text + F02 audio    |
  |  (DeepBrain/HeyGen)         | and generates avatar video    |
  |                              |                               |
  |  F04: Sign Language          | Takes F01 text output and     |
  |  (Sign-Speak)               | translates to sign language   |
  |                              |                               |
  |  F05: Assessment System      | F01 triggers quiz generation  |
  |  (Quiz, Grading)             | when student asks to be tested|
  |                              |                               |
  |  F06: Analytics Dashboard    | F01 session data feeds all    |
  |  (Progress Tracking)         | progress and analytics views  |
  |                              |                               |
  |  F07: Self-Learning          | F01 interaction logs are the  |
  |  (Teaching Improvement)      | training signal for improving |
  |                              | teaching strategies           |
  |                              |                               |
  |  F08: Content Generation     | F01 may request lesson plans  |
  |  (Lesson Plans, Notes)       | or study guides mid-session   |
  +--------------------------------------------------------------+
```

### 7.3 Full Data Flow Diagram

```
  +=====================================================================+
  |                    F01 ADAPTIVE TUTORING - DATA FLOW                 |
  +=====================================================================+
  |                                                                     |
  |                         +------------------+                        |
  |                         |     STUDENT      |                        |
  |                         |  (Web/Mobile)    |                        |
  |                         +--------+---------+                        |
  |                                  |                                  |
  |                         Login + Message                             |
  |                                  |                                  |
  |                         +--------v---------+                        |
  |                         |  API GATEWAY     |                        |
  |                         |  (Auth + Rate    |                        |
  |                         |   Limiting)      |                        |
  |                         +--------+---------+                        |
  |                                  |                                  |
  |                    +-------------+-------------+                    |
  |                    |                           |                    |
  |             REST Endpoints              WebSocket                   |
  |             (session mgmt,             (real-time                   |
  |              bookmarks,                 chat)                       |
  |              profile)                      |                        |
  |                    |                       |                        |
  |                    +----------+------------+                        |
  |                               |                                    |
  |                    +----------v------------+                        |
  |                    |                       |                        |
  |                    |  MASTER ORCHESTRATOR   |                        |
  |                    |                       |                        |
  |                    |  1. Load context      |                        |
  |                    |  2. Classify intent   |                        |
  |                    |  3. Route to agent    |                        |
  |                    |  4. Assemble response |                        |
  |                    |                       |                        |
  |                    +---+--------+------+---+                        |
  |                        |        |      |                            |
  |              +---------+   +----+   +--+----------+                 |
  |              |             |        |              |                 |
  |              v             v        v              v                 |
  |     +--------+---+ +------+--+ +---+------+ +-----+-------+        |
  |     |            | |         | |          | |             |        |
  |     | TUTOR      | | MEMORY  | | RAG      | | ASSESSMENT  |        |
  |     | AGENT      | | SYSTEM  | | ENGINE   | | AGENT       |        |
  |     |            | |         | |          | | (on demand) |        |
  |     | - System   | | - Redis | | - ChromaDB| |             |        |
  |     |   prompt   | | - PG    | | - Embeddings| - Quiz gen |        |
  |     | - Claude   | | - Chroma| |          | | - Grading  |        |
  |     |   API call | |         | |          | |             |        |
  |     +------+-----+ +----+----+ +-----+----+ +------+------+        |
  |            |             |           |              |               |
  |            |   +---------+-----------+              |               |
  |            |   |                                    |               |
  |            v   v                                    v               |
  |     +------+---+-----+                 +-----------+------+        |
  |     |                |                 |                  |        |
  |     | RESPONSE       |                 | SESSION DATA     |        |
  |     | (streamed text)|                 | (saved to DB)    |        |
  |     |                |                 |                  |        |
  |     +--------+-------+                 +------------------+        |
  |              |                                                     |
  |     +--------v----------+                                          |
  |     |                   |                                          |
  |     | OUTPUT ROUTER     |                                          |
  |     |                   |                                          |
  |     | Based on student  |                                          |
  |     | preferences:      |                                          |
  |     |                   |                                          |
  |     +--+-----+-----+---+                                          |
  |        |     |     |                                               |
  |        v     v     v                                               |
  |     Text  Voice  Sign                                              |
  |     only  (F02)  Lang                                              |
  |        |  (F03)  (F04)                                             |
  |        |     |     |                                               |
  |        +--+--+--+--+                                               |
  |           |     |                                                  |
  |           v     v                                                  |
  |     +-----------+--------+                                         |
  |     |                    |                                         |
  |     | STUDENT'S SCREEN   |                                         |
  |     |                    |                                         |
  |     | - Streaming text   |                                         |
  |     | - Code highlighting|                                         |
  |     | - Math rendering   |                                         |
  |     | - Quick actions    |                                         |
  |     | - Bookmark button  |                                         |
  |     |                    |                                         |
  |     +--------------------+                                         |
  |                                                                     |
  +=====================================================================+
```

### 7.4 Feature Interaction Matrix

```
  FEATURE INTERACTION MATRIX
  ===========================

  How F01 interacts with every other planned feature:

            F01   F02    F03    F04    F05    F06    F07    F08
          Tutor  Voice  Avatar  Sign  Assess Analytics Self  Content
          ------+------+------+------+------+------+------+------
  F01     --     OUT    OUT    OUT    BIDIR  OUT    OUT    BIDIR
  Tutor          (text  (text  (text  (quiz  (logs  (logs  (may
                 feed)  feed)  feed)  req.)  data)  data)  request)

  Legend:
    OUT   = F01 sends data to this feature
    IN    = F01 receives data from this feature
    BIDIR = Data flows both directions
    --    = Self (not applicable)

  Details:
  - F01 --> F02: Every tutor response text is sent to Voice for TTS
  - F01 --> F03: Tutor response + audio sent to Avatar for video
  - F01 --> F04: Tutor response text sent for sign language translation
  - F01 <-> F05: Student says "quiz me" --> F05 generates questions
                  F05 results feed back into F01 conversation
  - F01 --> F06: Session data, comprehension checks, mastery data
  - F01 --> F07: Teaching strategy effectiveness data
  - F01 <-> F08: Student asks for study guide --> F08 generates it
                  F08 content can be used as RAG context for F01
```

---

## 8. Appendix

### 8.1 System Prompt Template (Full)

The following is the complete system prompt template that gets assembled
for every tutoring call. Variables in `{braces}` are filled dynamically.

```
  You are EduAGI, a patient, knowledgeable, and adaptive AI tutor.

  == STUDENT PROFILE ==
  Name: {student_name}
  Grade Level: {grade_level}
  Learning Style: {learning_style}
  Pace Preference: {pace}
  Known Strengths: {strengths_list}
  Areas for Growth: {weaknesses_list}
  Preferred Explanation Style: {explanation_style}

  == CURRENT SESSION ==
  Subject: {current_subject}
  Topic: {current_topic}
  Session Duration So Far: {duration_minutes} minutes
  Difficulty Level: {difficulty_level} (1-5 scale)
  Socratic Mode: {socratic_enabled}
  Retry Count for Current Concept: {retry_count}

  == PREVIOUS SESSION SUMMARY ==
  {previous_session_summary}

  == KNOWLEDGE CONTEXT ==
  {rag_context}

  == TEACHING GUIDELINES ==
  1. Classify the student's intent before responding. Possible
     intents: EXPLAIN, QUIZ, HELP, CONFUSED, SOCIAL, NAVIGATE,
     META, OFF-TOPIC.

  2. If Socratic mode is ON and the student has sufficient
     foundation, guide them to the answer with questions rather
     than stating it directly. If they struggle after 3 guided
     attempts, switch to direct explanation.

  3. Adapt your language complexity to the student's grade level.
     A high school student and a PhD candidate should receive
     very different explanations of the same concept.

  4. If the student seems confused (short replies, "I don't get it",
     wrong answers), do NOT repeat the same explanation. Use this
     retry ladder:
     - Attempt 1: Simplify. Remove jargon. One idea at a time.
     - Attempt 2: Use an analogy from everyday life.
     - Attempt 3: Walk through a specific, concrete example.
     - Attempt 4: Reset. Find the last point they understood.

  5. Check comprehension at natural breakpoints. Do not check
     after every response -- that feels like an interrogation.
     Good check formats: teach-back, prediction, application.

  6. Encouragement rules:
     - Praise only when earned (hard question answered correctly,
       persistence through difficulty).
     - Never say "Great job!" after trivial answers.
     - When correcting, acknowledge what WAS right before
       addressing what was wrong.
     - If the student is frustrated, acknowledge it honestly.
       Do not be artificially cheerful.

  7. Format your responses:
     - Use Markdown formatting for structure.
     - Wrap code in triple-backtick fences with language tags.
     - Use LaTeX notation ($..$ inline, $$...$$ display) for math.
     - Keep responses concise. One concept per response unless
       the student asks for more.
     - Suggest quick actions when appropriate: [Give me an example],
       [Simplify], [Go deeper], [Quiz me].

  8. If the student goes off-topic, gently redirect:
     "I'm best at helping you learn -- want to get back to {topic}?"

  9. At the end of your internal reasoning, tag your response
     metadata with:
     - intent_classified: the intent you detected
     - mood_detected: the student's apparent mood
     - difficulty_appropriate: whether current difficulty is right
     - comprehension_check_due: whether it's time for a check
```

### 8.2 Error Handling & Fallback Strategy

```
  ERROR SCENARIOS AND RESPONSES
  ==============================

  +--------------------------------------------------------------+
  |  Error                     | Student Sees          | Backend |
  +----------------------------+-----------------------+---------|
  |  Claude API timeout (30s)  | "Give me a moment,   | Retry   |
  |                            |  thinking about       | once    |
  |                            |  this..."             | with    |
  |                            |                       | backoff |
  |                            |                       |         |
  |  Claude API 500 error      | "I hit a snag. Let   | Switch  |
  |                            |  me try again."       | to GPT-4|
  |                            |                       | fallback|
  |                            |                       |         |
  |  Claude API 429 (rate      | "I'm thinking about  | Queue   |
  |  limited)                  |  a lot of questions   | and     |
  |                            |  right now. Yours is  | retry   |
  |                            |  next."               | in 5s   |
  |                            |                       |         |
  |  WebSocket disconnection   | "Connection lost.     | Auto    |
  |                            |  Reconnecting..."     | reconn. |
  |                            |                       | 3 tries |
  |                            |                       |         |
  |  Redis unavailable         | No visible impact     | Degrade |
  |                            | (session context lost  | to      |
  |                            |  but tutor still works)| stateless|
  |                            |                       |         |
  |  ChromaDB unavailable      | Tutor still works but | Skip RAG|
  |                            | may be less accurate  | context |
  |                            | on factual questions  |         |
  |                            |                       |         |
  |  All LLMs unavailable      | "I'm having technical | Show    |
  |                            |  difficulties. Your   | offline |
  |                            |  session is saved."   | page    |
  +--------------------------------------------------------------+
```

### 8.3 Metrics to Track for F01

```
  KEY PERFORMANCE INDICATORS
  ===========================

  Quality Metrics:
  +--------------------------------------------------------------+
  |  Metric                         | Target    | Measurement     |
  +---------------------------------+-----------+-----------------|
  |  Comprehension check pass rate  | > 75%     | Automated       |
  |  Average retries per concept    | < 2.0     | Logged data     |
  |  Student satisfaction (per      | > 4.2/5   | Post-session    |
  |  session rating)                |           | survey          |
  |  Session completion rate        | > 80%     | Analytics       |
  |  (student finishes vs abandons) |           |                 |
  |  Concept mastery rate           | > 70%     | Assessment      |
  |  (tested 1 week later)          |           | follow-up       |
  +--------------------------------------------------------------+

  Performance Metrics:
  +--------------------------------------------------------------+
  |  Metric                         | Target    | Measurement     |
  +---------------------------------+-----------+-----------------|
  |  Time to first token (TTFT)     | < 800ms   | APM monitoring  |
  |  Full response latency (p95)    | < 5s      | APM monitoring  |
  |  WebSocket connection success   | > 99.5%   | Server logs     |
  |  Stream interruption rate       | < 1%      | Client telemetry|
  +--------------------------------------------------------------+

  Cost Metrics:
  +--------------------------------------------------------------+
  |  Metric                         | Target    | Measurement     |
  +---------------------------------+-----------+-----------------|
  |  Average cost per session       | < $0.30   | Token tracking  |
  |  Average tokens per exchange    | < 2000    | API logs        |
  |  Cache hit rate (RAG)           | > 30%     | Redis metrics   |
  |  Fallback to GPT-4 rate        | < 5%      | Service logs    |
  +--------------------------------------------------------------+
```

### 8.4 Glossary of Terms

| Term | Definition |
|---|---|
| **Comprehension Check** | A question asked by the tutor to verify the student understood a concept |
| **ELI5** | "Explain Like I'm 5" -- extreme simplification mode |
| **Intent Classification** | Determining what type of action the student's message requires |
| **MCP** | Model Context Protocol -- a standard for connecting LLMs to external tools |
| **Pomodoro** | A time management technique: 25 min work, 5 min break |
| **RAG** | Retrieval-Augmented Generation -- grounding LLM responses with retrieved documents |
| **Retry Ladder** | The escalating sequence of different explanation strategies when a student is confused |
| **Socratic Method** | Teaching by asking guiding questions rather than giving direct answers |
| **SSE** | Server-Sent Events -- the streaming protocol used by the Claude API |
| **TTFT** | Time To First Token -- how quickly the student sees the first character of a response |
| **Topic Stack** | The data structure tracking conversation branches and tangents |
| **Token Budget** | The daily limit on LLM tokens a student can consume |

---

*Document Version History*

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | AGI Education Team | Initial feature design |

---

*This document is part of the EduAGI Feature Design Series. See also:*
- *F02: Voice Synthesis (ElevenLabs Integration)*
- *F03: Avatar Presentation (DeepBrain/HeyGen)*
- *F04: Sign Language Support*
- *F05: Assessment & Grading System*
- *F06: Analytics & Progress Dashboard*
- *F07: Self-Learning Engine*
- *F08: Content Generation*
