# Feature 06: Voice System (TTS + STT)
# EduAGI - Self-Learning Educational AI Agent

**Version:** 1.0
**Date:** February 2026
**Author:** AGI Education Team
**Status:** Design Phase
**Priority:** P1 (High)
**Phase:** Phase 2 (Months 2-3)

---

## Table of Contents

1. [Feature Overview](#1-feature-overview)
2. [Detailed Workflows](#2-detailed-workflows)
3. [Sub-features and Small Touches](#3-sub-features-and-small-touches)
4. [Technical Requirements](#4-technical-requirements)
5. [Services and Alternatives](#5-services-and-alternatives)
6. [MCP Servers](#6-mcp-servers)
7. [Connections and Dependencies](#7-connections-and-dependencies)

---

## 1. Feature Overview

### 1.1 What This Feature Does

The Voice System gives EduAGI a voice -- literally. It covers two complementary
capabilities that transform a text chatbot into something that feels like
sitting across from a real tutor:

- **Text-to-Speech (TTS):** The AI tutor speaks its explanations aloud,
  reading back lesson content, answers, feedback, and encouragement in a
  natural human voice.

- **Speech-to-Text (STT):** The student speaks naturally into their
  microphone and the system transcribes their words in real time, so they
  can ask questions, answer quizzes, or have a full conversation without
  ever touching the keyboard.

Together, these two pipelines enable a **voice conversation mode** where
the student and tutor talk back and forth like a real tutoring session.

### 1.2 Why Voice Matters for Education

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WHY VOICE CHANGES EVERYTHING                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  FOR AUDITORY LEARNERS                                               │
│  Research shows ~30% of students learn best by listening.            │
│  Reading a wall of text is painful for them. Hearing an              │
│  explanation makes it click instantly.                                │
│                                                                      │
│  FOR STUDENTS WITH READING DIFFICULTIES                              │
│  Dyslexia affects ~15% of students. Voice output means they         │
│  can absorb the same content without struggling through text.        │
│  Voice input means they can participate fully without typing.        │
│                                                                      │
│  FOR YOUNGER STUDENTS (K-5)                                          │
│  Young children can speak far more fluently than they type.          │
│  Voice lets a 7-year-old interact with the AI tutor as               │
│  naturally as they talk to their classroom teacher.                   │
│                                                                      │
│  FOR THE "REAL TUTOR" EFFECT                                         │
│  A voice transforms the experience from "using a tool" to            │
│  "learning from someone." Students form stronger engagement          │
│  with a tutor that speaks to them. It is the difference              │
│  between reading a textbook and having a conversation.               │
│                                                                      │
│  FOR MULTITASKING STUDENTS                                           │
│  Students can listen to explanations while drawing diagrams,         │
│  following along in a textbook, or even commuting. Voice             │
│  makes EduAGI usable without eyes on the screen.                     │
│                                                                      │
│  FOR ACCESSIBILITY (WCAG 2.1 AA)                                     │
│  Voice output is not optional -- it is a core accessibility          │
│  requirement. Screen readers help, but natural TTS with              │
│  proper pacing and emphasis is a fundamentally better                 │
│  experience for visually impaired students.                          │
│                                                                      │
│  FOR LANGUAGE LEARNERS                                                │
│  Students learning a new language need to hear correct               │
│  pronunciation. They also need to practice speaking and              │
│  get feedback. Voice enables both sides of this loop.                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 The Student Experience

Imagine a 14-year-old student named Amir studying algebra at 9pm. He is tired.
Reading long explanations feels like a chore. He clicks the speaker icon, and
EduAGI starts reading the explanation aloud in a warm, patient voice. The words
on screen highlight as the tutor speaks, so he can follow along. He leans back,
listens, and it makes sense.

Then he has a question. Instead of typing, he holds the microphone button and
asks out loud: "Wait, why did we move the 3 to the other side?" The AI
transcribes his question instantly, thinks, and then speaks back: "Great
question, Amir. When we move a number across the equals sign, we flip its
operation. Since it was adding 3 on the left, it becomes subtracting 3 on the
right. Think of the equals sign as a balance..."

Amir nods. He says "Read that again." The AI re-reads the last explanation.
He gets it now. This is what the voice system enables.

### 1.4 High-Level Voice System Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                     VOICE SYSTEM - COMPLETE MAP                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                      ┌─────────────────┐                             │
│                      │     STUDENT     │                             │
│                      └───────┬─────────┘                             │
│                     speaks   │   listens                             │
│                   ┌──────────┼──────────┐                            │
│                   │                     │                             │
│                   ▼                     ▼                             │
│         ┌─────────────────┐   ┌─────────────────┐                   │
│         │  STT PIPELINE   │   │  TTS PIPELINE   │                   │
│         │                 │   │                 │                    │
│         │ Mic Capture     │   │ Text Preprocess │                   │
│         │ Audio Stream    │   │ Voice Selection │                   │
│         │ Transcription   │   │ Audio Generate  │                   │
│         │ Intent Parse    │   │ Audio Cache     │                   │
│         │ Command Handle  │   │ Audio Stream    │                   │
│         └────────┬────────┘   └────────┬────────┘                   │
│                  │                     │                              │
│                  ▼                     ▼                              │
│         ┌─────────────────────────────────────┐                     │
│         │          VOICE CONTROLLER            │                     │
│         │                                      │                     │
│         │  - Turn management (who is talking)  │                     │
│         │  - Conversation state machine        │                     │
│         │  - Pause/resume coordination         │                     │
│         │  - Text highlight synchronization    │                     │
│         └──────────────────┬──────────────────┘                     │
│                            │                                         │
│              ┌─────────────┼─────────────┐                          │
│              │             │             │                           │
│              ▼             ▼             ▼                           │
│     ┌──────────────┐ ┌──────────┐ ┌──────────────┐                 │
│     │ Tutor Agent  │ │  Avatar  │ │   Memory     │                 │
│     │ (processes   │ │  Agent   │ │   Agent      │                 │
│     │  question,   │ │ (lip     │ │ (logs voice  │                 │
│     │  generates   │ │  sync)   │ │  interaction)│                 │
│     │  answer)     │ │          │ │              │                 │
│     └──────────────┘ └──────────┘ └──────────────┘                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Workflows

### 2.1 Text-to-Speech (TTS) Pipeline

The TTS pipeline converts the tutor's text response into natural spoken audio.
This is not a simple API call -- it involves preprocessing the text for spoken
delivery, selecting the right voice, generating audio with streaming, caching
for performance, and synchronizing playback with on-screen text highlights.

#### 2.1.1 Complete TTS Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TTS PIPELINE - COMPLETE FLOW                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐                                                    │
│  │ Tutor Agent  │   "The quadratic formula is x = (-b +/- sqrt(     │
│  │ produces     │    b^2 - 4ac)) / 2a. Let me explain each part."   │
│  │ text answer  │                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 1: TEXT PREPROCESSING                                │       │
│  │                                                           │       │
│  │  Input:  "x = (-b +/- sqrt(b^2 - 4ac)) / 2a"           │       │
│  │                                                           │       │
│  │  (a) Detect content type (prose, math, code, mixed)      │       │
│  │  (b) Expand abbreviations: "sqrt" -> "square root"       │       │
│  │  (c) Expand symbols: "+/-" -> "plus or minus"            │       │
│  │  (d) Expand math: "b^2" -> "b squared"                   │       │
│  │  (e) Handle special chars: "/" -> "divided by"            │       │
│  │  (f) Add SSML pauses: <break> before key concepts        │       │
│  │  (g) Add SSML emphasis: <emphasis> on important words     │       │
│  │  (h) Split into speakable chunks (sentence boundaries)    │       │
│  │                                                           │       │
│  │  Output: "The quadratic formula is x equals open paren   │       │
│  │           negative b, plus or minus the square root of    │       │
│  │           b squared minus 4 a c, close paren, divided    │       │
│  │           by 2 a. <break/> Let me explain each part."    │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 2: CACHE LOOKUP                                      │       │
│  │                                                           │       │
│  │  Generate cache key:                                      │       │
│  │    hash = SHA256(preprocessed_text + voice_id + speed     │       │
│  │                   + pitch + language)                      │       │
│  │                                                           │       │
│  │  Check Redis: GET audio_cache:{hash}                      │       │
│  │                                                           │       │
│  │  ┌─── HIT ────────────────┐  ┌─── MISS ───────────────┐ │       │
│  │  │ Return cached audio    │  │ Continue to Step 3      │ │       │
│  │  │ URL from S3/CDN.       │  │ for generation.         │ │       │
│  │  │ Skip to Step 5.        │  │                         │ │       │
│  │  └────────────────────────┘  └─────────────────────────┘ │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │ (cache miss)                           │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 3: VOICE SELECTION                                   │       │
│  │                                                           │       │
│  │  Decision tree:                                           │       │
│  │                                                           │       │
│  │  1. Does student have a saved voice preference?           │       │
│  │     YES -> use that voice_id                              │       │
│  │     NO  -> continue                                       │       │
│  │                                                           │       │
│  │  2. What persona is active?                               │       │
│  │     "friendly_teacher" -> warm, moderate pace voice       │       │
│  │     "professional"     -> clear, authoritative voice      │       │
│  │     "study_buddy"      -> casual, upbeat voice            │       │
│  │                                                           │       │
│  │  3. What language is needed?                              │       │
│  │     Match voice to content language (en, es, fr, etc.)    │       │
│  │                                                           │       │
│  │  4. Apply student settings:                               │       │
│  │     speed: 0.5x to 2.0x  (default 1.0)                   │       │
│  │     pitch: -20% to +20%  (default 0%)                     │       │
│  │     stability: 0.3 to 0.8  (default 0.5)                 │       │
│  │     clarity: 0.5 to 1.0   (default 0.75)                 │       │
│  │                                                           │       │
│  │  Output: VoiceConfig object with all parameters           │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 4: STREAMING AUDIO GENERATION                        │       │
│  │                                                           │       │
│  │  (a) Open WebSocket to TTS provider (e.g. ElevenLabs)    │       │
│  │  (b) Send preprocessed text + voice config                │       │
│  │  (c) Receive audio chunks (each ~100-500ms of audio)     │       │
│  │  (d) Forward each chunk to client via WebSocket           │       │
│  │  (e) Simultaneously buffer chunks for caching             │       │
│  │  (f) On completion: assemble full audio, store in S3      │       │
│  │  (g) Write cache entry: SET audio_cache:{hash} = s3_url  │       │
│  │  (h) Set cache TTL (default: 7 days)                      │       │
│  │                                                           │       │
│  │  Timeline for a typical explanation (~200 words):         │       │
│  │  ┌────────────────────────────────────────────────┐       │       │
│  │  │ 0ms       500ms     1500ms                     │       │       │
│  │  │  |─────────|─────────|─────── ─ ─ ─ ─ ─       │       │       │
│  │  │  request   first     student hears              │       │       │
│  │  │  sent      audio     continuous speech          │       │       │
│  │  │            byte                                 │       │       │
│  │  │            arrives                              │       │       │
│  │  └────────────────────────────────────────────────┘       │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 5: PLAYBACK + TEXT HIGHLIGHT SYNC                    │       │
│  │                                                           │       │
│  │  Client-side (browser):                                   │       │
│  │                                                           │       │
│  │  (a) Web Audio API decodes incoming audio chunks          │       │
│  │  (b) AudioContext schedules seamless playback             │       │
│  │  (c) Word-level timestamps from TTS provider (if avail)  │       │
│  │      OR estimated from character count + speech rate      │       │
│  │  (d) As each word is spoken, its DOM element gets         │       │
│  │      a "speaking" CSS class (highlighted background)      │       │
│  │  (e) Scroll position follows the highlighted word         │       │
│  │                                                           │       │
│  │  Visual effect:                                           │       │
│  │  "The quadratic formula is x equals negative b..."       │       │
│  │   ^^^                                                     │       │
│  │   highlighted word moves forward as audio plays           │       │
│  │                                                           │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.1.2 Text Preprocessing Rules by Content Type

The preprocessor must handle different content types that appear in educational
material. This is critical because a TTS engine that reads "x^2 + 3x - 7 = 0"
literally will say "x caret two plus three x dash seven equals zero," which is
incomprehensible.

**Prose / Natural Language (default)**
- No special transformation needed
- Insert SSML `<break>` tags at paragraph boundaries (400ms pause)
- Insert shorter breaks at sentence boundaries (200ms pause)
- Detect emphasis words (bold, italic, CAPS) and wrap in SSML `<emphasis>`

**Mathematical Expressions**
- Detection: presence of operators (^, /, sqrt, integral, sigma), variables
  in formula context, LaTeX delimiters ($...$, \[...\])
- Transformations:
  - `x^2` becomes "x squared"
  - `x^3` becomes "x cubed"
  - `x^n` becomes "x to the power of n"
  - `sqrt(x)` becomes "the square root of x"
  - `a/b` becomes "a divided by b" or "a over b"
  - `>=` becomes "greater than or equal to"
  - `!=` becomes "not equal to"
  - `pi` becomes "pi" (already readable)
  - `theta` becomes "theta"
  - `sum_{i=1}^{n}` becomes "the sum from i equals 1 to n"
  - `integral` becomes "the integral"
  - Parentheses: "open parenthesis ... close parenthesis" for clarity
  - Fractions: "a over b" or "the fraction a over b"

**Code Blocks**
- Detection: fenced code blocks (```), inline code (`...`), or context from
  the tutor discussing programming
- Strategy: Code is NOT read character by character. Instead:
  - Short inline code (< 20 chars): spell it out with naming conventions
    - `myVariable` becomes "my variable" (split on camelCase)
    - `user_name` becomes "user name" (split on underscores)
    - `len()` becomes "len function"
  - Full code blocks: read a natural-language summary instead
    - "Here is a Python function called calculate area that takes width and
       height as parameters and returns their product."
    - The actual code remains on screen for the student to read visually
  - Line-by-line mode (on student request): read code line by line
    - `for i in range(10):` becomes "for i in range 10 colon"
    - Indentation: "indented" or "one level deeper"

**Lists and Bullet Points**
- Number each item: "First, ... Second, ... Third, ..."
- Insert 300ms pause between items
- For nested lists: "Under that, ..."

**URLs and File Paths**
- Abbreviated: "link to wikipedia dot org" (not the full URL)
- File paths: "the file main dot py in the src folder"

**Tables**
- Read as structured prose: "In the first row, the subject is Math and the
  score is 85. In the second row..."
- For large tables: summarize instead of reading every cell

#### 2.1.3 Audio Caching Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUDIO CACHING ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CACHE KEY GENERATION                                                │
│  ┌───────────────────────────────────────────────────┐              │
│  │                                                    │              │
│  │  key = SHA256(                                     │              │
│  │    preprocessed_text   // the spoken-form text     │              │
│  │    + voice_id          // which voice              │              │
│  │    + speed             // playback speed            │              │
│  │    + pitch             // pitch adjustment          │              │
│  │    + language          // target language           │              │
│  │    + model_id          // TTS model version         │              │
│  │  )                                                 │              │
│  │                                                    │              │
│  │  Example: audio_cache:a3f8b2c1d4e5...              │              │
│  └───────────────────────────────────────────────────┘              │
│                                                                      │
│  TWO-TIER CACHE                                                      │
│                                                                      │
│  ┌─────────────────┐     ┌─────────────────┐                       │
│  │   TIER 1: Redis │     │ TIER 2: S3/CDN  │                       │
│  │   (Hot Cache)   │     │ (Warm Storage)  │                       │
│  ├─────────────────┤     ├─────────────────┤                       │
│  │                 │     │                 │                        │
│  │ Stores: S3 URL  │     │ Stores: actual  │                       │
│  │ + metadata      │     │ audio files     │                       │
│  │                 │     │ (.mp3)          │                       │
│  │ TTL: 7 days     │     │                 │                       │
│  │                 │     │ TTL: 30 days    │                       │
│  │ Eviction: LRU   │     │                 │                       │
│  │                 │     │ Served via      │                       │
│  │ Max size:       │     │ CloudFront CDN  │                       │
│  │ 10,000 entries  │     │                 │                       │
│  │                 │     │ Max size:       │                       │
│  │ Lookup: <1ms    │     │ 50GB per tenant │                       │
│  │                 │     │                 │                       │
│  └─────────────────┘     └─────────────────┘                       │
│                                                                      │
│  CACHE HIT RATES (expected)                                          │
│                                                                      │
│  Common greetings, feedback phrases  -> ~90% hit rate               │
│  Standard lesson explanations        -> ~40% hit rate               │
│  Personalized / dynamic responses    -> ~5% hit rate                │
│  Overall weighted average            -> ~30-35% hit rate            │
│                                                                      │
│  CACHE INVALIDATION                                                  │
│                                                                      │
│  - Voice model upgrade by provider  -> flush all                    │
│  - Student changes voice preference -> no flush (new key)           │
│  - TTL expiry                       -> automatic                    │
│  - Manual purge via admin API       -> targeted flush               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Speech-to-Text (STT) Pipeline

The STT pipeline captures the student's spoken words through their browser
microphone, streams the audio to a transcription service, converts it to text
in real time, and then feeds that text into the tutor agent as if the student
had typed it.

#### 2.2.1 Complete STT Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STT PIPELINE - COMPLETE FLOW                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 1: MICROPHONE CAPTURE (Browser)                      │       │
│  │                                                           │       │
│  │  (a) Student clicks mic button OR uses push-to-talk      │       │
│  │      OR system detects wake word "Hey EduAGI"             │       │
│  │                                                           │       │
│  │  (b) Browser calls navigator.mediaDevices.getUserMedia()  │       │
│  │      Request: { audio: true, video: false }               │       │
│  │      Constraints: sampleRate 16000Hz, mono channel        │       │
│  │                                                           │       │
│  │  (c) Permission check:                                    │       │
│  │      GRANTED -> proceed to capture                        │       │
│  │      DENIED  -> show message, fall back to text input     │       │
│  │                                                           │       │
│  │  (d) Create MediaRecorder or ScriptProcessorNode          │       │
│  │      Format: audio/webm;codecs=opus (preferred)           │       │
│  │      Fallback: audio/wav (if opus unavailable)            │       │
│  │                                                           │       │
│  │  (e) Visual indicator: pulsing red dot + waveform         │       │
│  │      so student knows they are being heard                │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 2: AUDIO STREAMING TO SERVER                         │       │
│  │                                                           │       │
│  │  (a) Open WebSocket: ws://api/v1/voice/stream             │       │
│  │                                                           │       │
│  │  (b) Send audio in chunks every 100ms:                    │       │
│  │      { type: "audio_chunk",                               │       │
│  │        data: <base64 encoded audio>,                      │       │
│  │        sequence: 1,                                       │       │
│  │        timestamp: 1709234567890 }                         │       │
│  │                                                           │       │
│  │  (c) Client-side Voice Activity Detection (VAD):          │       │
│  │      - Monitor audio energy levels                        │       │
│  │      - Only send chunks when speech detected              │       │
│  │      - Save bandwidth by skipping silence                 │       │
│  │      - Detect end-of-speech (1.5s silence threshold)      │       │
│  │                                                           │       │
│  │  (d) End signal when student stops speaking:              │       │
│  │      { type: "audio_end" }                                │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 3: SERVER-SIDE PROCESSING                            │       │
│  │                                                           │       │
│  │  (a) Voice API gateway receives audio chunks              │       │
│  │                                                           │       │
│  │  (b) Forward to STT provider via their streaming API:     │       │
│  │      Deepgram WebSocket / Whisper / Google STT            │       │
│  │                                                           │       │
│  │  (c) Receive partial (interim) transcripts:               │       │
│  │      "What is..."                                         │       │
│  │      "What is the quadra..."                              │       │
│  │      "What is the quadratic..."                           │       │
│  │      "What is the quadratic formula"  (final)             │       │
│  │                                                           │       │
│  │  (d) Forward interim transcripts to client for display:   │       │
│  │      Student sees their words appearing in real time      │       │
│  │      in a text bubble, like live captioning               │       │
│  │                                                           │       │
│  │  (e) On "final" transcript:                               │       │
│  │      - Punctuation restoration                            │       │
│  │      - Capitalization normalization                        │       │
│  │      - Profanity filter (for safety with minors)          │       │
│  │      - Language detection confirmation                     │       │
│  └──────────────────────────┬───────────────────────────────┘       │
│                             │                                        │
│                             ▼                                        │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │ STEP 4: INTENT HANDLING                                   │       │
│  │                                                           │       │
│  │  Final transcript goes through intent classification:     │       │
│  │                                                           │       │
│  │  ┌─────────────────────────────────────────────────┐     │       │
│  │  │ VOICE COMMAND?          EDUCATIONAL QUERY?       │     │       │
│  │  │                                                  │     │       │
│  │  │ "Read that again"       "What is photosynthesis" │     │       │
│  │  │ "Slow down"             "Can you explain step 3" │     │       │
│  │  │ "Stop reading"          "I don't understand"     │     │       │
│  │  │ "Go back"               "Give me an example"     │     │       │
│  │  │ "Next section"          "Quiz me on this"        │     │       │
│  │  │ "Save this"             "What's my grade"        │     │       │
│  │  │ "Take a note"                                    │     │       │
│  │  │                                                  │     │       │
│  │  │     |                           |                │     │       │
│  │  │     v                           v                │     │       │
│  │  │ Execute command           Send to Tutor Agent    │     │       │
│  │  │ directly (no LLM)        for processing          │     │       │
│  │  └─────────────────────────────────────────────────┘     │       │
│  │                                                           │       │
│  └──────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.2.2 Wake Word Detection ("Hey EduAGI")

This is an optional, opt-in feature that lets the student activate voice input
without clicking any button -- a hands-free experience.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    WAKE WORD DETECTION FLOW                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  When wake word is enabled:                                          │
│                                                                      │
│  ┌────────────┐    ┌──────────────┐    ┌──────────────────┐         │
│  │ Microphone │    │  Local Wake  │    │  Full STT Mode   │         │
│  │ always     │───>│  Word Model  │───>│  activates for   │         │
│  │ listening  │    │  (browser,   │    │  the next spoken │         │
│  │ at low     │    │   <5MB,      │    │  utterance only  │         │
│  │ power      │    │   runs on    │    │                  │         │
│  │            │    │   device)    │    │  Auto-deactivates│         │
│  └────────────┘    └──────────────┘    │  after 10s of    │         │
│                                         │  silence          │         │
│  IMPORTANT PRIVACY NOTES:               └──────────────────┘         │
│                                                                      │
│  - Wake word detection runs ENTIRELY in the browser                 │
│  - No audio is sent to the server until wake word is detected       │
│  - Uses a small TensorFlow.js or ONNX model (~3-5MB)               │
│  - Student must explicitly opt in (off by default)                  │
│  - Visual indicator shows when listening is active                  │
│  - Can be turned off instantly via settings or voice: "Stop         │
│    listening"                                                        │
│                                                                      │
│  Implementation options:                                             │
│  (a) Porcupine by Picovoice - custom wake word, runs in browser    │
│  (b) Custom trained small keyword model via TensorFlow.js           │
│  (c) Browser SpeechRecognition API in continuous mode (limited)     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Voice Conversation Mode

When both TTS and STT are active simultaneously, the system enters "voice
conversation mode." This is the pinnacle experience: a real-time, spoken
dialogue between student and AI tutor.

#### 2.3.1 Conversation Turn Management

```
┌─────────────────────────────────────────────────────────────────────┐
│                VOICE CONVERSATION STATE MACHINE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                      ┌─────────────┐                                │
│                      │    IDLE     │                                 │
│                      │  (waiting   │                                 │
│                      │   for input)│                                 │
│                      └──────┬──────┘                                │
│                             │                                        │
│               student speaks or clicks mic                           │
│                             │                                        │
│                             ▼                                        │
│                      ┌─────────────┐                                │
│                      │  LISTENING  │ <-- visual: pulsing mic icon   │
│                      │  (STT on,   │     waveform animation         │
│                      │   TTS off)  │     "I'm listening..."         │
│                      └──────┬──────┘                                │
│                             │                                        │
│               silence detected (1.5s) or student clicks stop        │
│                             │                                        │
│                             ▼                                        │
│                      ┌─────────────┐                                │
│                      │  THINKING   │ <-- visual: typing indicator   │
│                      │  (STT off,  │     "Thinking..."              │
│                      │   LLM       │     ~1-3 seconds               │
│                      │   processing│                                │
│                      └──────┬──────┘                                │
│                             │                                        │
│               tutor response ready, TTS begins streaming            │
│                             │                                        │
│                             ▼                                        │
│                      ┌─────────────┐                                │
│                      │  SPEAKING   │ <-- visual: avatar lip-sync    │
│                      │  (TTS on,   │     text highlighting           │
│                      │   STT off)  │     speaker icon animating     │
│                      └──────┬──────┘                                │
│                             │                                        │
│          ┌──────────────────┼──────────────────┐                    │
│          │                  │                  │                     │
│    TTS finishes      student interrupts   student starts            │
│          │           (clicks mic or       typing                    │
│          │            speaks loudly)         │                      │
│          │                  │                  │                     │
│          ▼                  ▼                  ▼                     │
│    ┌──────────┐     ┌─────────────┐    ┌──────────┐                │
│    │  IDLE    │     │  LISTENING  │    │ TTS PAUSE │               │
│    │  (ready  │     │  (TTS stops │    │ (auto-    │               │
│    │   for    │     │   mid-      │    │  pauses   │               │
│    │   next)  │     │   sentence, │    │  voice,   │               │
│    └──────────┘     │   STT on)   │    │  student  │               │
│                     └─────────────┘    │  types)   │               │
│                                        └──────────┘                │
│                                                                      │
│  KEY RULES:                                                          │
│  - Student can ALWAYS interrupt. Their voice takes priority.        │
│  - TTS stops gracefully mid-word, not abruptly.                     │
│  - If student starts typing, TTS pauses automatically.              │
│  - STT and TTS never run simultaneously (echo/feedback issues).     │
│  - After speaking, there is a 500ms buffer before STT reactivates  │
│    to avoid the tutor's own voice being captured.                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.3.2 Interruption Handling

When a student interrupts the tutor mid-speech:

1. Audio playback stops within 100ms
2. Any buffered audio chunks are discarded
3. The STT pipeline activates immediately
4. The partial response that was spoken is logged in the conversation history
   (marked as "partial")
5. The student's interruption is captured and processed
6. The tutor's next response takes into account that the previous answer was
   cut short -- it may resume, rephrase, or answer the new question

### 2.4 Handling Different Content Types with Voice

Educational content is not uniform text. The voice system must handle each
content type appropriately so the student actually understands what they hear.

```
┌─────────────────────────────────────────────────────────────────────┐
│            CONTENT TYPE HANDLING STRATEGIES                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  CONTENT TYPE       VOICE STRATEGY                                   │
│  ─────────────      ────────────────────────────────────            │
│                                                                      │
│  Plain text         Read normally. Add pauses at paragraph          │
│                     breaks. Emphasize bold/italic words.            │
│                                                                      │
│  Math formulas      Convert to spoken math (see 2.1.2).             │
│                     "x squared plus 3x minus 7 equals zero"         │
│                     Pause before and after formula for clarity.     │
│                                                                      │
│  Code blocks        Do NOT read code verbatim by default.           │
│                     Instead, read a natural language summary:       │
│                     "Here is a for loop that iterates through       │
│                      each item in the list and prints it."          │
│                     Student can request line-by-line reading.       │
│                                                                      │
│  Inline code        Read as a word: "the variable user name"        │
│                     or "the function get data."                     │
│                                                                      │
│  Bullet lists       "First, ... Second, ... Third, ..."             │
│                     Pause 300ms between items.                      │
│                                                                      │
│  Numbered steps     "Step one: ... Step two: ..."                   │
│                     Pause 400ms between steps.                      │
│                                                                      │
│  Tables             Summarize: "The table shows three columns:      │
│                     name, score, and grade. Sarah scored 92,        │
│                     which is an A. Marcus scored 85, a B."          │
│                                                                      │
│  URLs               Abbreviate: "link to docs dot python dot org"   │
│                     Do NOT spell out full URLs.                     │
│                                                                      │
│  Headings           Announce: "Section: Photosynthesis Process"     │
│                     Pause 600ms before heading content.             │
│                                                                      │
│  Quotes             Change tone slightly (if provider supports      │
│                     SSML prosody). Prefix: "Quote..."              │
│                                                                      │
│  Diagrams/Images    "There is a diagram here showing the water      │
│                      cycle. I will describe it: ..."                │
│                     Use alt-text or generate description via LLM.   │
│                                                                      │
│  Chemical formulas  "H 2 O" becomes "H two O, or water"            │
│                     "NaCl" becomes "sodium chloride, N A C L"       │
│                                                                      │
│  Foreign words      Switch to appropriate language voice briefly    │
│                     for correct pronunciation, then switch back.   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Sub-features and Small Touches

These are the details that transform a basic voice feature into a polished,
student-friendly experience. Each one is small on its own, but together they
make the difference between "this is a feature" and "this feels natural."

### 3.1 Voice Speed Control Slider

**What:** A slider in the UI that lets students control how fast the tutor
speaks, from 0.5x (half speed) to 2.0x (double speed).

**Why:** Students reviewing material they already know want 1.5-2x speed.
Students hearing a difficult concept for the first time want 0.75x. ESL
students often need 0.7x. Let the student control their own pace.

**Implementation:**
- Slider with discrete stops: 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0
- Can be changed mid-playback (takes effect on next sentence)
- Saved to student profile (persists across sessions)
- Two approaches:
  - Provider-side: send speed parameter to TTS API (better quality)
  - Client-side: use Web Audio API playbackRate (lower quality but instant)
- Default: 1.0x for new students
- Keyboard shortcut: `[` to slow down, `]` to speed up

### 3.2 Multiple Voice Personas

**What:** The student can choose from distinct voice personalities that change
not just the voice but the speaking style.

**Personas:**

| Persona | Voice Character | Tone | Best For |
|---------|----------------|------|----------|
| Friendly Teacher | Warm, mid-range, moderate pace | Encouraging, patient | K-8, struggling students |
| Professional Lecturer | Clear, authoritative, measured | Structured, precise | High school, college |
| Study Buddy | Casual, upbeat, slightly faster | Conversational, relatable | Teens, review sessions |
| Calm Coach | Soft, slow, soothing | Reassuring, gentle | Test anxiety, late-night study |
| Energetic Motivator | Bright, dynamic, varied pitch | Enthusiastic, motivating | Engagement boost, low energy |

**Implementation:**
- Each persona maps to a specific ElevenLabs voice_id + voice_settings
- Persona selection in settings with audio preview samples
- Can be changed per session or set as default
- System can suggest persona based on time of day and student mood detection

### 3.3 Language-Specific Voices

**What:** When the tutor teaches in a non-English language (or the student
has chosen a different interface language), the TTS uses a native voice for
that language -- not an English voice attempting foreign words.

**Supported languages (launch):**
- English (US, UK, Australian accents)
- Spanish (Latin American, Castilian)
- French
- German
- Mandarin Chinese
- Japanese
- Portuguese (Brazilian)
- Arabic
- Hindi
- Korean

**Implementation:**
- Each language has at least 2 voice options (1 male, 1 female)
- Language detection runs on the text before TTS to auto-select voice
- Mixed-language content (e.g., English lesson with French vocabulary)
  switches voices mid-stream for correct pronunciation
- Provider selection may vary by language (ElevenLabs for English, Google
  Cloud TTS for broader language coverage)

### 3.4 Text Highlight Synchronization

**What:** As the tutor speaks, the corresponding words on screen are
highlighted in real time -- like a karaoke display. The student can read
along while listening.

```
┌─────────────────────────────────────────────────────────────────────┐
│                 TEXT HIGHLIGHT SYNC - HOW IT WORKS                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  APPROACH 1: Word-Level Timestamps from TTS Provider                │
│                                                                      │
│  Some providers (ElevenLabs, Google) return timestamps:             │
│  [                                                                   │
│    { "word": "The",        "start": 0.00, "end": 0.15 },           │
│    { "word": "quadratic",  "start": 0.16, "end": 0.62 },           │
│    { "word": "formula",    "start": 0.63, "end": 1.01 },           │
│    ...                                                               │
│  ]                                                                   │
│                                                                      │
│  Client matches timestamps to DOM word-span elements.               │
│  As currentTime crosses each boundary, highlight moves.             │
│                                                                      │
│  APPROACH 2: Estimated Timing (fallback)                            │
│                                                                      │
│  If no timestamps available:                                         │
│  - Average speech rate: ~150 words/minute at 1.0x speed             │
│  - Per-word duration estimate: char_count * ms_per_char             │
│  - Adjusted for punctuation pauses                                  │
│  - Less precise but functional                                      │
│                                                                      │
│  VISUAL DESIGN                                                       │
│                                                                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │                                                     │            │
│  │  The quadratic formula is used to find the roots    │            │
│  │  of a quadratic equation. It states that x equals   │            │
│  │  negative b, plus or minus the [square root] of     │            │
│  │  b squared minus four a c, all divided by two a.    │            │
│  │                    ^^^^^^^^^                         │            │
│  │                    highlighted (soft yellow bg,      │            │
│  │                    smooth transition 50ms)           │            │
│  │                                                     │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
│  - Highlight color: semi-transparent yellow (#FFF3B0)               │
│  - Transition: smooth 50ms ease                                      │
│  - Auto-scroll: viewport follows highlighted word                   │
│  - Can be toggled off by students who find it distracting           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.5 Auto-Pause When Student Starts Typing

**What:** If the tutor is speaking and the student starts typing in the
input box, the audio automatically pauses. When the student stops typing
(2 second idle) or submits their message, audio optionally resumes.

**Why:** The student clearly wants to respond or take action. Continuing
to talk over them is rude -- even for an AI.

**Implementation:**
- Listen for `keydown` events on the input element
- On first keypress: pause audio, show "paused" indicator
- On submit or 2s idle + student clicks "resume": resume audio
- TTS resumes from the exact word where it paused
- Also applies to: clicking a link, opening a menu, switching tabs

### 3.6 "Read That Again" Voice Command

**What:** The student says "Read that again" (or "Repeat that" or "Say that
again") and the tutor re-reads the last spoken response from the beginning.

**Implementation:**
- Recognized as a voice command (not sent to LLM)
- Last audio is already cached, so replay is instant
- Variant: "Read from [section/topic]" replays from a specific point
- Variant: "Read it slower" replays at 0.75x speed

### 3.7 Voice Notes from Student

**What:** Students can record short voice notes while studying -- quick
thoughts, reminders, or questions to come back to later. These are
transcribed and saved to their study notes.

```
┌─────────────────────────────────────────────────────────────────────┐
│                      VOICE NOTES FLOW                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Student clicks "Record Note" button (or says "Take a note")        │
│         │                                                            │
│         ▼                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │ Record audio │───>│  Transcribe  │───>│  Save to     │           │
│  │ (max 2 min)  │    │  via STT     │    │  student's   │           │
│  │              │    │              │    │  notes with  │           │
│  │ Show timer   │    │ Show text    │    │  timestamp   │           │
│  │ and waveform │    │ preview      │    │  and topic   │           │
│  └──────────────┘    └──────────────┘    │  context     │           │
│                                          └──────────────┘           │
│                                                                      │
│  Notes are stored as:                                                │
│  {                                                                   │
│    "type": "voice_note",                                             │
│    "transcript": "Remember to review chapter 3 examples...",        │
│    "audio_url": "s3://notes/student123/note_2026-02-06_1.mp3",     │
│    "session_id": "abc-123",                                         │
│    "topic": "Algebra - Quadratic Equations",                        │
│    "timestamp": "2026-02-06T21:15:00Z"                              │
│  }                                                                   │
│                                                                      │
│  Students can review notes later by:                                 │
│  - Reading the transcript                                            │
│  - Playing back the original audio                                   │
│  - Filtering by topic or date                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.8 Pronunciation Help (Language Learning)

**What:** For language learning courses, students can tap any word to hear
its correct pronunciation. They can also speak the word and get feedback
on their pronunciation accuracy.

**Implementation:**
- Tap-to-pronounce: TTS generates just the single word in the target language
- Speak-and-compare: STT captures student's attempt, system compares to
  reference pronunciation (phoneme-level comparison)
- Feedback: "Good! Your 'r' sound in 'rouge' is almost right. Try rolling
  the R slightly at the back of your throat."
- Uses language-specific voices for authentic pronunciation
- Supports IPA (International Phonetic Alphabet) display

### 3.9 Voice-Only Mode for Accessibility

**What:** A mode where the entire EduAGI interface is usable through voice
commands alone. Every action that can be done by clicking can be done by
speaking.

**Voice command categories:**
- Navigation: "Go to my dashboard" / "Open settings" / "Show my grades"
- Content: "Start a lesson on biology" / "Quiz me on chapter 5"
- Controls: "Pause" / "Resume" / "Slower" / "Faster" / "Louder"
- Input: Any educational question or answer
- System: "Help" / "What can I say?" / "Log out"

**Why:** Students with motor disabilities, temporary injuries (broken arm),
or vision impairments need a fully voice-navigable interface to have equal
access to the tutoring experience.

### 3.10 Background Audio Mode

**What:** The student can minimize the browser or switch to another app, and
the tutor's voice continues playing in the background -- like a podcast.

**Implementation:**
- Uses the Web Audio API which continues playing when tab is in background
- Shows a persistent browser notification with playback controls
- Media Session API integration for lock-screen controls on mobile
- Controls: play/pause, skip forward 15s, skip back 15s
- Audio continues even if screen is locked (mobile)
- Visual indicator when returning to the app: "You are at: [topic], [timestamp]"

### 3.11 Audio Download for Offline Listening

**What:** Students can download any lesson explanation as an MP3 file to
listen offline -- on the bus, on a plane, while exercising.

**Implementation:**
- "Download audio" button appears next to any TTS-generated content
- Generates a complete MP3 file (not chunked stream)
- File includes metadata: lesson title, topic, date
- For longer lessons: combines multiple responses into one audio file with
  section markers
- File naming: `EduAGI_[Subject]_[Topic]_[Date].mp3`
- File size estimate: ~1MB per minute of audio (128kbps MP3)
- Batch download: "Download all audio from this session"

### 3.12 Adjustable Pitch

**What:** A slider that lets students adjust the pitch (frequency) of the
tutor's voice higher or lower without changing the speed.

**Why:** Some students find higher-pitched voices clearer and more energizing.
Others find lower-pitched voices more calming and authoritative. Letting the
student choose their comfort zone improves engagement.

**Implementation:**
- Range: -20% to +20% from the voice's natural pitch
- Can be combined with speed control independently
- Provider-side (SSML `<prosody pitch="+10%">`) for best quality
- Client-side fallback: Web Audio API detune property
- Saved to student profile

---

## 4. Technical Requirements

### 4.1 WebSocket Protocol for Streaming Audio

All voice audio (both TTS output and STT input) flows through WebSocket
connections for low-latency, bidirectional streaming.

```
┌─────────────────────────────────────────────────────────────────────┐
│                   WEBSOCKET PROTOCOL DESIGN                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ENDPOINT: wss://api.eduagi.com/v1/voice/stream                     │
│                                                                      │
│  CONNECTION LIFECYCLE:                                                │
│  1. Client opens WebSocket with auth token in header                │
│  2. Server validates token, creates voice session                   │
│  3. Bidirectional audio/control messages flow                       │
│  4. Either side can close (student leaves, timeout, error)          │
│                                                                      │
│  CLIENT -> SERVER MESSAGES:                                          │
│                                                                      │
│  { "type": "stt_start",                                             │
│    "config": {                                                       │
│      "language": "en-US",                                            │
│      "interim_results": true,                                        │
│      "profanity_filter": true                                        │
│    }                                                                 │
│  }                                                                   │
│                                                                      │
│  { "type": "stt_audio",                                             │
│    "data": "<base64 encoded audio chunk>",                          │
│    "sequence": 42                                                    │
│  }                                                                   │
│                                                                      │
│  { "type": "stt_stop" }                                             │
│                                                                      │
│  { "type": "tts_request",                                           │
│    "text": "...",                                                    │
│    "voice_id": "abc123",                                             │
│    "speed": 1.0,                                                     │
│    "pitch": 0                                                        │
│  }                                                                   │
│                                                                      │
│  { "type": "tts_control",                                           │
│    "action": "pause" | "resume" | "stop" | "restart"                │
│  }                                                                   │
│                                                                      │
│  SERVER -> CLIENT MESSAGES:                                          │
│                                                                      │
│  { "type": "stt_transcript",                                        │
│    "text": "What is the quadratic",                                 │
│    "is_final": false,                                                │
│    "confidence": 0.92                                                │
│  }                                                                   │
│                                                                      │
│  { "type": "stt_transcript",                                        │
│    "text": "What is the quadratic formula?",                        │
│    "is_final": true,                                                 │
│    "confidence": 0.97                                                │
│  }                                                                   │
│                                                                      │
│  { "type": "tts_audio",                                             │
│    "data": "<base64 encoded audio chunk>",                          │
│    "sequence": 1,                                                    │
│    "word_timestamps": [                                              │
│      { "word": "The", "start": 0.0, "end": 0.15 },                 │
│      { "word": "quadratic", "start": 0.16, "end": 0.62 }           │
│    ]                                                                 │
│  }                                                                   │
│                                                                      │
│  { "type": "tts_complete",                                          │
│    "audio_url": "https://cdn.eduagi.com/audio/abc123.mp3",          │
│    "duration": 12.5                                                  │
│  }                                                                   │
│                                                                      │
│  { "type": "error",                                                 │
│    "code": "RATE_LIMIT",                                             │
│    "message": "Voice quota exceeded for this session"               │
│  }                                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Audio Format Handling

| Format | Use Case | Bitrate | Browser Support |
|--------|----------|---------|-----------------|
| Opus/WebM | STT upload (mic capture) | Variable | Chrome, Firefox, Edge |
| MP3 | TTS playback, downloads, cache | 128kbps | All browsers |
| WAV | STT fallback (Safari) | 768kbps | All browsers |
| OGG Vorbis | TTS playback fallback | 128kbps | Chrome, Firefox |
| AAC | Mobile-optimized playback | 128kbps | Safari, Chrome |

**Format selection logic:**
- STT input: prefer Opus (smallest size). Fall back to WAV for Safari.
- TTS output: prefer MP3 (universal). Use Opus for WebSocket streaming
  to save bandwidth, transcode to MP3 for caching and download.
- Server-side conversion: FFmpeg for any necessary transcoding.

### 4.3 Browser Audio APIs

```
┌─────────────────────────────────────────────────────────────────────┐
│                  BROWSER API USAGE MAP                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  getUserMedia API                                                    │
│  ├── Purpose: Access microphone                                     │
│  ├── Used by: STT pipeline                                          │
│  ├── Permissions: Requires user gesture + explicit permission       │
│  └── Fallback: Text input if denied                                 │
│                                                                      │
│  MediaRecorder API                                                   │
│  ├── Purpose: Encode microphone audio into chunks                   │
│  ├── Used by: STT pipeline                                          │
│  ├── Format: audio/webm;codecs=opus (preferred)                    │
│  └── Chunk interval: 100ms                                          │
│                                                                      │
│  Web Audio API (AudioContext)                                        │
│  ├── Purpose: Decode and play TTS audio chunks                      │
│  ├── Used by: TTS pipeline                                          │
│  ├── Features used:                                                  │
│  │   ├── AudioBufferSourceNode: schedule chunk playback             │
│  │   ├── GainNode: volume control                                   │
│  │   ├── playbackRate: client-side speed adjustment                 │
│  │   ├── detune: client-side pitch adjustment                       │
│  │   └── AnalyserNode: waveform visualization                      │
│  └── Handles: Gapless playback of sequential chunks                 │
│                                                                      │
│  MediaSession API                                                    │
│  ├── Purpose: Lock screen and notification controls                 │
│  ├── Used by: Background audio mode                                 │
│  ├── Actions: play, pause, seekforward, seekbackward                │
│  └── Metadata: lesson title, topic, tutor avatar image              │
│                                                                      │
│  SpeechRecognition API (Web Speech API)                              │
│  ├── Purpose: Browser-native STT (backup only)                     │
│  ├── Limitations: No streaming, limited languages, varies by        │
│  │   browser, inconsistent accuracy                                 │
│  └── Used only as: emergency fallback when server STT fails         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.4 Caching Layer Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLETE CACHING ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  REQUEST FLOW:                                                       │
│                                                                      │
│  TTS Request                                                         │
│      │                                                               │
│      ▼                                                               │
│  ┌──────────────────┐     ┌──────────────────┐                      │
│  │ Generate Cache   │────>│ Check Redis      │                      │
│  │ Key (SHA256)     │     │ (Hot Cache)      │                      │
│  └──────────────────┘     └────────┬─────────┘                      │
│                                    │                                 │
│                          ┌─── HIT ─┴── MISS ───┐                   │
│                          │                      │                    │
│                          ▼                      ▼                    │
│                   ┌──────────────┐    ┌──────────────────┐          │
│                   │ Return S3    │    │ Check S3 bucket  │          │
│                   │ CDN URL      │    │ (Warm Storage)   │          │
│                   │ immediately  │    └────────┬─────────┘          │
│                   └──────────────┘             │                     │
│                                      ┌─── EXISTS ── MISS ──┐       │
│                                      │                      │       │
│                                      ▼                      ▼       │
│                              ┌──────────────┐   ┌────────────────┐ │
│                              │ Restore to   │   │ Generate via   │ │
│                              │ Redis +      │   │ TTS provider.  │ │
│                              │ return URL   │   │ Store in S3.   │ │
│                              └──────────────┘   │ Store in Redis.│ │
│                                                 │ Return URL.    │ │
│                                                 └────────────────┘ │
│                                                                      │
│  CACHE ENTRY STRUCTURE (Redis):                                      │
│                                                                      │
│  Key:   audio_cache:{sha256_hash}                                   │
│  Value: {                                                            │
│    "s3_url": "s3://eduagi-audio/cache/abc123.mp3",                  │
│    "cdn_url": "https://cdn.eduagi.com/audio/abc123.mp3",            │
│    "duration_seconds": 12.5,                                         │
│    "format": "mp3",                                                  │
│    "size_bytes": 150000,                                             │
│    "voice_id": "voice_abc",                                          │
│    "created_at": "2026-02-06T21:00:00Z",                            │
│    "access_count": 47                                                │
│  }                                                                   │
│  TTL:   604800 (7 days)                                              │
│                                                                      │
│  STORAGE ESTIMATES:                                                  │
│                                                                      │
│  Average audio file: ~150KB (10 seconds of MP3 at 128kbps)          │
│  10,000 cached entries: ~1.5GB in S3                                │
│  Redis metadata: ~2KB per entry = ~20MB total                       │
│  Monthly S3 cost at 50GB: ~$1.15                                    │
│  Monthly Redis cost: negligible (fits in existing instance)         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.5 Bandwidth Considerations

| Scenario | Direction | Bandwidth | Notes |
|----------|-----------|-----------|-------|
| STT streaming (Opus) | Client to Server | ~32 kbps | Opus at 16kHz mono |
| STT streaming (WAV) | Client to Server | ~256 kbps | Uncompressed fallback |
| TTS streaming (MP3) | Server to Client | ~128 kbps | Standard quality |
| TTS streaming (Opus) | Server to Client | ~64 kbps | WebSocket streaming |
| Idle (no voice active) | Both | ~0.5 kbps | WebSocket heartbeat only |
| Voice conversation mode | Both | ~160 kbps | STT + TTS alternating |

**Minimum connection requirement:** 256 kbps (equivalent to a basic 3G connection)

**Bandwidth optimization strategies:**
- Voice Activity Detection (VAD) on client: only send audio when speaking
- Opus codec for streaming: 50% smaller than MP3 at comparable quality
- Adaptive bitrate: reduce quality on slow connections automatically
- Preload next expected audio during idle moments
- CDN delivery for cached audio (edge servers near student)

### 4.6 Latency Targets

```
┌─────────────────────────────────────────────────────────────────────┐
│                     LATENCY BUDGET                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TTS (Text-to-Speech) LATENCY                                       │
│                                                                      │
│  Target: First audio byte to client < 2000ms                        │
│                                                                      │
│  Breakdown:                                                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │ Text preprocessing         :    50ms                 │           │
│  │ Cache lookup (Redis)       :     5ms                 │           │
│  │ TTS API request to first   : 800-1500ms              │           │
│  │   audio byte (streaming)   :                         │           │
│  │ Server to client WebSocket :  50-150ms               │           │
│  │ Client audio decode        :    20ms                 │           │
│  │ ───────────────────────────────────────               │           │
│  │ TOTAL (cache miss)         : 925-1725ms              │           │
│  │ TOTAL (cache hit)          :  75-200ms               │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                      │
│  STT (Speech-to-Text) LATENCY                                       │
│                                                                      │
│  Target: Interim transcript visible < 500ms from spoken word        │
│                                                                      │
│  Breakdown:                                                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │ Mic capture + encode       :   100ms (chunk size)    │           │
│  │ Client to server WebSocket :  50-150ms               │           │
│  │ Server to STT provider     :  50-100ms               │           │
│  │ STT processing (interim)   : 100-200ms               │           │
│  │ Server to client WebSocket :  50-150ms               │           │
│  │ ───────────────────────────────────────               │           │
│  │ TOTAL (interim transcript) : 350-700ms               │           │
│  │ TOTAL (final transcript)   : 500-1500ms              │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                      │
│  FULL VOICE CONVERSATION ROUND-TRIP                                  │
│                                                                      │
│  Target: Student speaks -> hears tutor reply < 5 seconds            │
│                                                                      │
│  Breakdown:                                                          │
│  ┌──────────────────────────────────────────────────────┐           │
│  │ Student speaks (variable)  : student-dependent       │           │
│  │ Silence detection          :  1500ms                 │           │
│  │ Final STT transcript       :   500ms                 │           │
│  │ LLM processing (Claude)    : 1000-3000ms             │           │
│  │ TTS first audio byte       : 1000-1500ms             │           │
│  │ ───────────────────────────────────────               │           │
│  │ TOTAL (after student stops): 4000-6500ms             │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                      │
│  OPTIMIZATION: Start TTS as soon as first sentence of LLM           │
│  response is available (stream LLM -> stream TTS). This reduces     │
│  the combined LLM+TTS time from sequential to overlapping.          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.7 Concurrent Audio Generation Limits

| Tier | Concurrent TTS Sessions | Concurrent STT Sessions | Daily TTS Characters | Daily STT Minutes |
|------|------------------------|------------------------|---------------------|-------------------|
| Free | 1 | 1 | 10,000 | 30 |
| Pro (Student) | 2 | 1 | 100,000 | 180 |
| Pro (Teacher) | 5 | 3 | 500,000 | 600 |
| Enterprise | 50 | 25 | Unlimited | Unlimited |

**Rate limiting implementation:**
- Per-user limits enforced at the API gateway level
- Token bucket algorithm: refills over time, allows bursts
- When limit reached: graceful fallback to text-only mode with message
  "Voice quota reached for today. Continuing in text mode."
- Admin dashboard shows usage per user and aggregate

---

## 5. Services and Alternatives

### 5.1 TTS Services

#### 5.1.1 PRIMARY: ElevenLabs

**Why Primary:** Best-in-class voice quality. The most natural-sounding AI
voices available. Their "Turbo v2" model achieves near-human quality with
low latency streaming -- exactly what a tutor voice needs.

| Attribute | Details |
|-----------|---------|
| API | REST + WebSocket streaming |
| Models | Eleven Multilingual v2, Eleven Turbo v2, Eleven English v1 |
| Voice Library | 1000+ premade voices + custom voice cloning |
| Languages | 29 languages |
| Streaming | Yes (WebSocket, chunked HTTP) |
| Word Timestamps | Yes (with alignment API) |
| SSML Support | Partial (breaks, emphasis) |
| Latency (first byte) | ~500ms (Turbo v2) |
| Audio Formats | MP3, PCM, Opus, uLaw |

**Pricing (as of 2026):**

| Plan | Price | Characters/month | Cost per 1K chars |
|------|-------|-----------------|-------------------|
| Free | $0 | 10,000 | $0 |
| Starter | $5/mo | 30,000 | ~$0.17 |
| Creator | $22/mo | 100,000 | ~$0.22 |
| Pro | $99/mo | 500,000 | ~$0.20 |
| Scale | $330/mo | 2,000,000 | ~$0.165 |
| Business | Custom | Custom | ~$0.12-0.15 |

**Cost projection for EduAGI:**
- Average tutor response: ~200 characters
- Average student session: ~20 responses = ~4,000 characters
- 1,000 daily active users: ~4,000,000 characters/day
- Monthly: ~120,000,000 characters
- At Scale/Business rate: ~$18,000-$20,000/month
- With 30% cache hit rate: ~$12,600-$14,000/month

**Voice selection for personas:**

| Persona | Recommended Voice | Voice ID (example) | Character |
|---------|------------------|-------------------|-----------|
| Friendly Teacher | "Rachel" | 21m00Tcm4TlvDq8ikWAM | Warm, clear, mid-range |
| Professional Lecturer | "Antoni" | ErXwobaYiN019PkySvjV | Authoritative, measured |
| Study Buddy | "Josh" | TxGEqnHWrfWFTfGW9XjX | Casual, young, upbeat |
| Calm Coach | "Elli" | MF3mGyEYCl7XYWbV9V6O | Soft, gentle, soothing |
| Energetic Motivator | "Sam" | yoZ06aMxZJJ28mfd3POQ | Bright, dynamic |

**Integration approach:**
- WebSocket streaming for real-time playback
- REST API for batch generation (downloads, offline)
- Use "Turbo v2" model for conversation mode (lowest latency)
- Use "Multilingual v2" for non-English content (best quality)

#### 5.1.2 ALT 1: Google Cloud Text-to-Speech

| Attribute | Details |
|-----------|---------|
| API | REST (gRPC available) |
| Voice Types | Standard, WaveNet, Neural2, Studio |
| Languages | 50+ languages, 200+ voices |
| Streaming | Yes (via gRPC) |
| Word Timestamps | Yes (timepoints in response) |
| SSML Support | Full SSML 1.0 support |
| Latency (first byte) | ~800ms (Neural2) |
| Audio Formats | MP3, OGG Opus, WAV, MULAW |

**Pricing:**

| Voice Type | Price per 1M characters |
|------------|------------------------|
| Standard | $4.00 |
| WaveNet | $16.00 |
| Neural2 | $16.00 |
| Studio | $160.00 |

**Comparison to ElevenLabs:**
- Pros: Better language coverage (50+ vs 29), lower cost for standard voices,
  full SSML support, Google infrastructure reliability
- Cons: Voice quality slightly below ElevenLabs for English, fewer character
  options for personas, Studio voices are expensive
- Best for: Multilingual fallback, cost-sensitive deployments, full SSML needs

#### 5.1.3 ALT 2: Amazon Polly

| Attribute | Details |
|-----------|---------|
| API | REST (AWS SDK) |
| Voice Types | Standard, Neural, Long-form, Generative |
| Languages | 30+ languages |
| Streaming | Yes (HTTP chunked) |
| Word Timestamps | Yes (speech marks) |
| SSML Support | Full SSML support |
| Latency (first byte) | ~1000ms (Neural) |
| Audio Formats | MP3, OGG Vorbis, PCM |

**Pricing:**

| Voice Type | Price per 1M characters |
|------------|------------------------|
| Standard | $4.00 |
| Neural | $16.00 |
| Long-form | $100.00 |
| Generative | $30.00 |

**Comparison to ElevenLabs:**
- Pros: Deep AWS integration (already on AWS), predictable pricing, speech
  marks for text sync, neural voices are solid quality
- Cons: Voice quality below ElevenLabs and Google for naturalness, fewer
  voice customization options, no voice cloning
- Best for: AWS-native deployments, cost-predictable environments

#### 5.1.4 ALT 3: Azure Cognitive Services TTS

| Attribute | Details |
|-----------|---------|
| API | REST + WebSocket |
| Voice Types | Neural, Custom Neural Voice |
| Languages | 60+ languages, 400+ voices |
| Streaming | Yes (WebSocket) |
| Word Timestamps | Yes (word boundary events) |
| SSML Support | Full SSML support + Mstts extensions |
| Latency (first byte) | ~700ms (Neural) |
| Audio Formats | MP3, OGG, WAV, WebM, SILK |

**Pricing:**

| Feature | Price per 1M characters |
|---------|------------------------|
| Neural TTS | $16.00 |
| Custom Neural Voice | $24.00 |
| Personal Voice (preview) | $24.00 |

**Comparison to ElevenLabs:**
- Pros: Widest language coverage (60+), custom neural voice training,
  excellent SSML with Microsoft extensions, word boundary events are
  precise for text highlighting, strong enterprise support
- Cons: Voice character/personality slightly less natural than ElevenLabs,
  custom voice requires 300+ training utterances
- Best for: Enterprise deployments, maximum language coverage, custom voices

#### 5.1.5 ALT 4: OpenAI TTS

| Attribute | Details |
|-----------|---------|
| API | REST |
| Models | tts-1 (fast), tts-1-hd (quality) |
| Voices | 6 voices (Alloy, Echo, Fable, Onyx, Nova, Shimmer) |
| Languages | ~20 languages (auto-detected) |
| Streaming | Yes (chunked HTTP) |
| Word Timestamps | No |
| SSML Support | No |
| Latency (first byte) | ~600ms (tts-1), ~1200ms (tts-1-hd) |
| Audio Formats | MP3, Opus, AAC, FLAC |

**Pricing:**

| Model | Price per 1M characters |
|-------|------------------------|
| tts-1 | $15.00 |
| tts-1-hd | $30.00 |

**Comparison to ElevenLabs:**
- Pros: Simple API (already using OpenAI for embeddings), good quality for
  the price, low latency on tts-1, easy to integrate
- Cons: Only 6 voices (limited persona options), no SSML, no word timestamps
  (breaks text highlight sync), no voice cloning, no custom voices
- Best for: Quick MVP, simplicity, when text highlighting is not required

#### 5.1.6 ALT 5: Coqui / XTTS (Open Source, Self-Hosted)

| Attribute | Details |
|-----------|---------|
| Model | XTTS v2 (open source) |
| Hosting | Self-hosted (GPU required) |
| Languages | 17 languages |
| Streaming | Yes (with custom server) |
| Word Timestamps | Yes (with alignment model) |
| SSML Support | No (custom preprocessing needed) |
| Latency (first byte) | ~1500-3000ms (depending on GPU) |
| Audio Formats | WAV (transcode to MP3/Opus) |

**Cost (self-hosted on AWS):**

| GPU Instance | Cost/hour | Cost/month (on-demand) |
|-------------|-----------|----------------------|
| g5.xlarge (A10G) | $1.006 | ~$724 |
| g4dn.xlarge (T4) | $0.526 | ~$379 |
| p3.2xlarge (V100) | $3.06 | ~$2,203 |

**Comparison to ElevenLabs:**
- Pros: No per-character cost (unlimited generation), full control over
  model and data, no vendor lock-in, voice cloning with just 6 seconds
  of reference audio, can fine-tune for educational content
- Cons: Requires GPU infrastructure, higher latency, voice quality below
  ElevenLabs, requires ML ops expertise, maintenance burden
- Best for: Cost control at extreme scale (millions of characters/day),
  data sovereignty requirements, custom model fine-tuning

**Recommendation:** Start with ElevenLabs for quality. Add Coqui/XTTS as
a self-hosted fallback for cost optimization once daily volume exceeds
5 million characters.

### 5.2 STT Services

#### 5.2.1 PRIMARY: Deepgram

**Why Primary:** Best real-time streaming accuracy with the lowest latency.
Purpose-built for streaming speech recognition. Their Nova-2 model leads
benchmarks for English accuracy, and streaming interim results arrive
faster than any competitor.

| Attribute | Details |
|-----------|---------|
| API | REST + WebSocket streaming |
| Models | Nova-2 (latest), Nova, Enhanced, Base |
| Languages | 36 languages |
| Streaming | Yes (WebSocket, real-time) |
| Interim Results | Yes (partial transcripts) |
| Latency (interim) | ~200-300ms |
| Latency (final) | ~500-800ms |
| Accuracy (English) | ~95-97% (Nova-2) |
| Features | Punctuation, diarization, smart formatting, topic detection |

**Pricing:**

| Model | Price per minute |
|-------|-----------------|
| Nova-2 | $0.0043 (Pay-as-you-go) |
| Nova-2 (Growth) | $0.0036 |
| Enhanced | $0.0145 |
| Base | $0.0125 |

**Cost projection for EduAGI:**
- Average student speaking per session: ~5 minutes
- 1,000 daily active users: ~5,000 minutes/day
- Monthly: ~150,000 minutes
- At Nova-2 Growth rate: ~$540/month

**Integration approach:**
- WebSocket streaming for real-time conversation mode
- REST API for voice note transcription (non-real-time)
- Enable: punctuation, smart_format, utterances
- Set language based on student profile
- Use endpointing for end-of-speech detection

#### 5.2.2 ALT 1: OpenAI Whisper

**Option A: Whisper API (cloud)**

| Attribute | Details |
|-----------|---------|
| API | REST only (no streaming) |
| Model | whisper-1 |
| Languages | 57 languages |
| Streaming | No (batch only) |
| Latency | ~2-5 seconds (depends on audio length) |
| Accuracy | ~93-95% (English) |
| Price | $0.006 per minute |

**Option B: Whisper (self-hosted)**

| Attribute | Details |
|-----------|---------|
| Models | tiny, base, small, medium, large-v3 |
| Languages | 99 languages |
| Streaming | With custom implementation (faster-whisper) |
| GPU Required | Yes (for real-time, large-v3 needs A10G+) |
| Latency | ~1-3 seconds (large-v3 on A10G) |
| Accuracy | ~95-97% (large-v3, English) |

**Self-hosted cost:**
- g5.xlarge instance: ~$724/month
- Can share GPU with Coqui/XTTS for both TTS + STT

**Comparison to Deepgram:**
- Pros: Wider language support (99 languages), high accuracy, self-hosting
  eliminates per-minute cost, OpenAI ecosystem integration
- Cons: API has no streaming (deal-breaker for conversation mode), self-hosted
  streaming requires engineering effort (faster-whisper), higher latency
- Best for: Self-hosted cost optimization, widest language support, batch
  transcription (voice notes)

#### 5.2.3 ALT 2: Google Cloud Speech-to-Text

| Attribute | Details |
|-----------|---------|
| API | REST + gRPC streaming |
| Models | Default, Medical, Phone call, Latest (Chirp) |
| Languages | 125+ languages |
| Streaming | Yes (gRPC) |
| Interim Results | Yes |
| Latency (interim) | ~300-500ms |
| Accuracy (English) | ~93-96% |
| Price | $0.006-$0.009 per 15 seconds |

**Comparison to Deepgram:**
- Pros: Widest language support (125+), mature streaming API, strong medical
  vocabulary, Google infrastructure
- Cons: Higher cost, slightly higher latency, gRPC adds complexity
- Best for: Maximum language coverage, Google Cloud-native deployments

#### 5.2.4 ALT 3: AssemblyAI

| Attribute | Details |
|-----------|---------|
| API | REST + WebSocket streaming |
| Models | Best, Nano |
| Languages | 20+ languages |
| Streaming | Yes (WebSocket, real-time) |
| Interim Results | Yes |
| Latency (interim) | ~300-400ms |
| Accuracy (English) | ~95-97% |
| Features | Sentiment analysis, topic detection, entity recognition, summarization |
| Price | $0.006-0.0097 per minute |

**Comparison to Deepgram:**
- Pros: Built-in NLU features (sentiment, topics) useful for understanding
  student mood and engagement, clean API, good documentation
- Cons: Slightly higher latency, higher cost, fewer languages
- Best for: When you want speech analytics (student engagement detection)

#### 5.2.5 ALT 4: Azure Speech-to-Text

| Attribute | Details |
|-----------|---------|
| API | REST + WebSocket |
| Models | Default, Custom Speech |
| Languages | 100+ languages |
| Streaming | Yes (WebSocket, real-time) |
| Interim Results | Yes |
| Latency (interim) | ~300-500ms |
| Accuracy (English) | ~93-96% |
| Features | Custom models, pronunciation assessment, keyword recognition |
| Price | $1.00 per audio hour (standard) |

**Comparison to Deepgram:**
- Pros: Pronunciation assessment feature (gold for language learning),
  custom acoustic models, widest vendor support, Azure ecosystem
- Cons: Higher cost at scale, slightly lower accuracy than Deepgram Nova-2
- Best for: Language learning pronunciation features, Azure-native deployments,
  custom acoustic model training for educational vocabulary

---

## 6. MCP Servers

Model Context Protocol (MCP) servers can extend EduAGI's voice capabilities
by providing standardized tool interfaces for audio processing.

### 6.1 Applicable MCP Servers

```
┌─────────────────────────────────────────────────────────────────────┐
│                   MCP SERVERS FOR VOICE SYSTEM                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  MCP Server: Audio Processing                                        │
│  ─────────────────────────────                                       │
│  Purpose: Provide LLM agents with audio manipulation tools           │
│  Tools exposed:                                                      │
│    - audio.convert(input, output_format)                             │
│    - audio.trim(input, start, end)                                   │
│    - audio.normalize(input, target_lufs)                             │
│    - audio.concatenate(inputs[])                                     │
│    - audio.get_duration(input)                                       │
│    - audio.get_waveform(input) -> visualization data                │
│  Use case: When the tutor agent needs to manipulate audio            │
│  as part of a lesson (e.g., combining audio segments for a          │
│  study summary, trimming a voice note)                              │
│                                                                      │
│  MCP Server: ElevenLabs Voice                                        │
│  ────────────────────────────                                        │
│  Purpose: Give LLM agents direct access to voice generation          │
│  Tools exposed:                                                      │
│    - voice.synthesize(text, voice_id, settings)                     │
│    - voice.list_voices()                                             │
│    - voice.get_voice_settings(voice_id)                              │
│    - voice.clone(name, audio_samples[])                              │
│  Use case: The orchestrator agent can generate voice output          │
│  as part of its response pipeline without custom integration        │
│  code -- the MCP server handles the ElevenLabs API                  │
│                                                                      │
│  MCP Server: Transcription                                           │
│  ─────────────────────────                                           │
│  Purpose: Provide transcription tools to LLM agents                  │
│  Tools exposed:                                                      │
│    - transcribe.audio(audio_input, language)                        │
│    - transcribe.realtime_start(config)                               │
│    - transcribe.realtime_stop(session_id)                            │
│  Use case: When the tutor agent needs to process a student's        │
│  uploaded audio file (e.g., a recorded presentation for              │
│  feedback) or manage real-time transcription sessions                │
│                                                                      │
│  MCP Server: Pronunciation Assessment                                │
│  ────────────────────────────────────                                │
│  Purpose: Evaluate student pronunciation for language learning       │
│  Tools exposed:                                                      │
│    - pronunciation.assess(audio, reference_text, language)          │
│    - pronunciation.get_phonemes(word, language)                      │
│    - pronunciation.compare(student_audio, reference_audio)          │
│  Use case: Language learning module where the tutor needs            │
│  to assess how well a student pronounced a word or sentence         │
│                                                                      │
│  NOTE: As of February 2026, most of these would be custom-built     │
│  MCP servers wrapping the respective provider APIs. The MCP          │
│  ecosystem for audio is still emerging. Building these as MCP        │
│  servers (vs. direct integrations) future-proofs the architecture   │
│  and allows swapping providers without changing agent code.          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. Connections and Dependencies

### 7.1 How Voice Connects to the Tutor Agent

The voice system is not a standalone feature -- it is deeply integrated into
the tutor agent's response pipeline. The tutor agent produces text, and the
voice system adds an audio layer on top.

```
┌─────────────────────────────────────────────────────────────────────┐
│              VOICE <-> TUTOR AGENT INTEGRATION                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STUDENT INPUT (voice path):                                         │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ Student  │    │   STT    │    │  Intent  │    │  Tutor   │      │
│  │ speaks   │───>│ Pipeline │───>│ Classify │───>│  Agent   │      │
│  │ into mic │    │ (text)   │    │          │    │ (process)│      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│                                                                      │
│  The Tutor Agent receives the transcribed text exactly as if the    │
│  student had typed it. The AgentContext includes a flag:             │
│    context.input_mode = "voice"                                      │
│  This lets the tutor adjust its response style:                     │
│    - Shorter sentences (easier to follow when spoken)               │
│    - More conversational tone                                        │
│    - Fewer code blocks (hard to hear)                               │
│    - More analogies and verbal explanations                         │
│                                                                      │
│  ─────────────────────────────────────────────────────────────      │
│                                                                      │
│  TUTOR OUTPUT (voice path):                                          │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │  Tutor   │    │   Text   │    │   TTS    │    │ Student  │      │
│  │  Agent   │───>│ Preproc. │───>│ Pipeline │───>│  hears   │      │
│  │ (text)   │    │          │    │ (audio)  │    │  audio   │      │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘      │
│                                                                      │
│  STREAMING OPTIMIZATION (LLM -> TTS pipeline):                       │
│                                                                      │
│  The LLM streams its text response token by token. We buffer         │
│  until a sentence boundary is detected, then immediately send       │
│  that sentence to TTS for audio generation. This means TTS          │
│  starts generating audio for the first sentence while the LLM       │
│  is still generating the rest of the response.                      │
│                                                                      │
│  ┌─── LLM Stream ───────────────────────────────┐                  │
│  │ "The"  "quadratic"  "formula"  "is"  "used"  │                  │
│  │ "to"  "find"  "roots."  "It"  "states"  ...   │                  │
│  └─────────────────────┬─────────────────────────┘                  │
│                        │ (sentence boundary: ".")                    │
│                        ▼                                             │
│  ┌─── TTS Generation (parallel) ───────────────┐                   │
│  │ Sentence 1: "The quadratic formula is used   │                   │
│  │              to find roots."                   │                   │
│  │              -> audio chunks streaming to      │                   │
│  │                 student while sentence 2       │                   │
│  │                 is still being generated       │                   │
│  └───────────────────────────────────────────────┘                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.2 How Voice Feeds into Avatar Lip-Sync

The avatar system (Feature 07 in the roadmap) needs audio data from the voice
system to synchronize lip movements with speech.

```
┌─────────────────────────────────────────────────────────────────────┐
│              VOICE -> AVATAR LIP-SYNC DATA FLOW                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐                                                    │
│  │  TTS Engine  │                                                    │
│  │  (ElevenLabs)│                                                    │
│  └──────┬───────┘                                                    │
│         │                                                            │
│         │ produces                                                   │
│         │                                                            │
│    ┌────┴────────────────────────────────────┐                      │
│    │                                          │                      │
│    ▼                                          ▼                      │
│  ┌──────────────┐                    ┌──────────────────┐           │
│  │ Audio Stream │                    │ Phoneme/Viseme   │           │
│  │ (for student │                    │ Timeline         │           │
│  │  playback)   │                    │ (for avatar)     │           │
│  └──────────────┘                    └────────┬─────────┘           │
│                                               │                      │
│                                               ▼                      │
│                                      ┌──────────────────┐           │
│                                      │   Avatar Agent   │           │
│                                      │                  │           │
│                                      │  Maps phonemes   │           │
│                                      │  to mouth shapes:│           │
│                                      │                  │           │
│                                      │  /a/ -> open     │           │
│                                      │  /m/ -> closed   │           │
│                                      │  /o/ -> round    │           │
│                                      │  /s/ -> narrow   │           │
│                                      │  /th/ -> tongue  │           │
│                                      │  etc.            │           │
│                                      └────────┬─────────┘           │
│                                               │                      │
│                                               ▼                      │
│                                      ┌──────────────────┐           │
│                                      │ Avatar renders   │           │
│                                      │ lip-sync video   │           │
│                                      │ synchronized     │           │
│                                      │ with audio       │           │
│                                      │ playback         │           │
│                                      └──────────────────┘           │
│                                                                      │
│  DATA FORMAT (phoneme timeline):                                     │
│  [                                                                   │
│    { "phoneme": "DH", "viseme": "TH", "start": 0.00, "end": 0.08 },│
│    { "phoneme": "AH", "viseme": "aa", "start": 0.08, "end": 0.15 },│
│    { "phoneme": "K",  "viseme": "kk", "start": 0.16, "end": 0.22 },│
│    ...                                                               │
│  ]                                                                   │
│                                                                      │
│  TIMING: Avatar lip-sync must be within 50ms of audio playback     │
│  to avoid the "dubbed movie" effect that feels unnatural.           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Audio Storage and CDN Delivery

```
┌─────────────────────────────────────────────────────────────────────┐
│              AUDIO STORAGE AND DELIVERY ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STORAGE LAYOUT (S3):                                                │
│                                                                      │
│  s3://eduagi-audio/                                                  │
│  ├── cache/                    # TTS cache (auto-generated)         │
│  │   ├── ab/                   # First 2 chars of hash (sharding)   │
│  │   │   ├── abc123...def.mp3                                       │
│  │   │   └── abd456...ghi.mp3                                       │
│  │   └── cd/                                                        │
│  │       └── ...                                                    │
│  ├── voice-notes/              # Student voice notes                │
│  │   ├── student_{id}/                                              │
│  │   │   ├── 2026-02-06_note_1.mp3                                 │
│  │   │   └── 2026-02-06_note_2.mp3                                 │
│  │   └── ...                                                        │
│  ├── downloads/                # Downloadable lesson audio          │
│  │   ├── session_{id}/                                              │
│  │   │   └── lesson_complete.mp3                                    │
│  │   └── ...                                                        │
│  └── pronunciation/            # Reference pronunciation clips      │
│      ├── en/                                                        │
│      ├── es/                                                        │
│      └── fr/                                                        │
│                                                                      │
│  CDN DELIVERY:                                                       │
│                                                                      │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐            │
│  │    S3    │────>│  CloudFront  │────>│   Student    │            │
│  │  Bucket  │     │  CDN         │     │   Browser    │            │
│  │          │     │              │     │              │            │
│  │ Origin   │     │ Edge caching │     │ Plays from   │            │
│  │          │     │ Gzip/Brotli  │     │ nearest edge │            │
│  │          │     │ HTTPS only   │     │ server       │            │
│  └──────────┘     └──────────────┘     └──────────────┘            │
│                                                                      │
│  CDN Configuration:                                                  │
│  - Cache behavior: cache/ path -> TTL 30 days                       │
│  - Cache behavior: voice-notes/ -> TTL 0 (private, signed URLs)    │
│  - Cache behavior: downloads/ -> TTL 7 days                         │
│  - Signed URLs for private content (voice notes)                    │
│  - CORS: allow *.eduagi.com origins                                 │
│  - Compression: enabled for all audio formats                       │
│                                                                      │
│  LIFECYCLE POLICIES:                                                 │
│  - cache/: delete after 30 days of no access                        │
│  - voice-notes/: move to Glacier after 90 days                      │
│  - downloads/: delete after 7 days (regeneratable)                  │
│  - pronunciation/: permanent (reference data)                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.4 Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│              COMPLETE VOICE SYSTEM DATA FLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                        ┌──────────────┐                              │
│                        │   STUDENT    │                              │
│                        │   BROWSER    │                              │
│                        └───┬──────┬───┘                              │
│                  speaks    │      │   listens                        │
│                ┌───────────┘      └───────────┐                     │
│                │                              │                      │
│                ▼                              │                      │
│  ┌──────────────────────┐                    │                      │
│  │ MediaRecorder API    │                    │                      │
│  │ (Opus/WebM chunks)   │                    │                      │
│  └──────────┬───────────┘                    │                      │
│             │ WebSocket                      │                      │
│             ▼                                │                      │
│  ┌──────────────────────┐                    │                      │
│  │ API Gateway          │                    │                      │
│  │ (auth, rate limit)   │                    │                      │
│  └──────────┬───────────┘                    │                      │
│             │                                │                      │
│      ┌──────┴──────┐                        │                      │
│      │             │                        │                      │
│      ▼             ▼                        │                      │
│  ┌────────┐  ┌──────────┐                   │                      │
│  │  STT   │  │  Voice   │                   │                      │
│  │Provider│  │Controller│                   │                      │
│  │(Deep-  │  │(session  │                   │                      │
│  │ gram)  │  │ state)   │                   │                      │
│  └───┬────┘  └──────────┘                   │                      │
│      │                                      │                      │
│      │ transcript                            │                      │
│      ▼                                      │                      │
│  ┌──────────────────────┐                   │                      │
│  │ Intent Classifier    │                   │                      │
│  │ (command vs question)│                   │                      │
│  └──────────┬───────────┘                   │                      │
│             │                               │                      │
│      ┌──────┴──────┐                        │                      │
│      │             │                        │                      │
│      ▼             ▼                        │                      │
│  ┌────────┐  ┌──────────┐                   │                      │
│  │Command │  │  Master  │                   │                      │
│  │Execute │  │Orchestr- │                   │                      │
│  │(direct)│  │  ator    │                   │                      │
│  └────────┘  └────┬─────┘                   │                      │
│                   │                         │                      │
│            ┌──────┴──────┐                  │                      │
│            │             │                  │                      │
│            ▼             ▼                  │                      │
│      ┌──────────┐  ┌──────────┐            │                      │
│      │  Tutor   │  │  Memory  │            │                      │
│      │  Agent   │  │  Agent   │            │                      │
│      │(generate │  │(log the  │            │                      │
│      │ answer)  │  │ exchange)│            │                      │
│      └────┬─────┘  └──────────┘            │                      │
│           │                                │                      │
│           │ text response (streaming)      │                      │
│           ▼                                │                      │
│      ┌──────────────────┐                  │                      │
│      │Text Preprocessor │                  │                      │
│      │(math, code, etc.)│                  │                      │
│      └────┬─────────────┘                  │                      │
│           │                                │                      │
│           ▼                                │                      │
│      ┌──────────────────┐                  │                      │
│      │  Cache Lookup    │                  │                      │
│      │  (Redis)         │                  │                      │
│      └────┬──────┬──────┘                  │                      │
│      HIT  │      │ MISS                    │                      │
│           │      ▼                         │                      │
│           │ ┌──────────────┐               │                      │
│           │ │ TTS Provider │               │                      │
│           │ │ (ElevenLabs) │               │                      │
│           │ └──┬───────────┘               │                      │
│           │    │                            │                      │
│           │    │ audio chunks               │                      │
│           │    ▼                            │                      │
│           │ ┌──────────────┐               │                      │
│           │ │ Cache Store  │               │                      │
│           │ │ (Redis + S3) │               │                      │
│           │ └──┬───────────┘               │                      │
│           │    │                            │                      │
│           └────┤                            │                      │
│                │ audio (cached or fresh)    │                      │
│                ▼                            │                      │
│      ┌──────────────────┐                  │                      │
│      │ Avatar Agent     │                  │                      │
│      │ (phoneme data    │                  │                      │
│      │  for lip sync)   │                  │                      │
│      └────┬─────────────┘                  │                      │
│           │                                │                      │
│           │ audio + timestamps + phonemes  │                      │
│           │                                │                      │
│           ▼                                ▼                      │
│      ┌──────────────────────────────────────────┐                │
│      │           WebSocket (Server -> Client)    │                │
│      │                                           │                │
│      │  { type: "tts_audio",                     │                │
│      │    data: "<audio chunk>",                 │                │
│      │    word_timestamps: [...],                │                │
│      │    phonemes: [...] }                      │                │
│      └──────────────────────┬───────────────────┘                │
│                             │                                     │
│                             ▼                                     │
│                   ┌──────────────────┐                            │
│                   │ Web Audio API    │                            │
│                   │ (decode + play)  │                            │
│                   │ Text highlight   │                            │
│                   │ Avatar lip-sync  │                            │
│                   └──────────────────┘                            │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### 7.5 Dependencies Summary

| Dependency | What Voice Needs From It | What It Needs From Voice |
|------------|-------------------------|-------------------------|
| **Tutor Agent** | Text response to speak | Transcribed student speech as input |
| **Avatar Agent** | Nothing | Audio stream + phoneme timeline for lip-sync |
| **Memory Agent** | Student voice preferences | Voice interaction logs for learning analytics |
| **Master Orchestrator** | Routing decisions, session context | Voice session state updates |
| **Redis** | Fast cache storage | Cache entries for audio |
| **S3** | Persistent audio storage | Audio files (cache, notes, downloads) |
| **CloudFront CDN** | Edge delivery of audio | Cached audio files from S3 |
| **PostgreSQL** | Student profile (voice preferences) | Voice usage analytics data |
| **WebSocket Gateway** | Bidirectional streaming channel | Audio and control messages |
| **Auth Service** | User identity for rate limiting | Nothing |

### 7.6 Failure Modes and Graceful Degradation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GRACEFUL DEGRADATION STRATEGY                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  FAILURE                        FALLBACK                             │
│  ──────────────────             ─────────────────────────────────   │
│                                                                      │
│  TTS provider down              Fall back to browser native          │
│  (ElevenLabs outage)            SpeechSynthesis API (lower quality   │
│                                 but functional). Show banner:        │
│                                 "Voice quality reduced temporarily." │
│                                                                      │
│  TTS provider slow              Return text immediately. Queue       │
│  (latency > 5s)                 audio generation. Play when ready.   │
│                                 "Your answer is ready. Audio         │
│                                  loading..."                         │
│                                                                      │
│  STT provider down              Disable mic button. Show text        │
│  (Deepgram outage)              input as primary. Try browser        │
│                                 SpeechRecognition API as backup.     │
│                                                                      │
│  Microphone not available       Text-only mode. Hide mic button.    │
│  (no hardware or denied)        No degraded experience, just a      │
│                                 different modality.                  │
│                                                                      │
│  WebSocket disconnected         Reconnect with exponential backoff. │
│                                 Buffer audio locally. Resume on     │
│                                 reconnection. Show "Reconnecting..."│
│                                                                      │
│  Cache (Redis) down             Skip cache. Generate fresh audio    │
│                                 every time. Higher cost but works.  │
│                                                                      │
│  S3/CDN down                    Stream audio directly from TTS      │
│                                 provider (no caching). Higher       │
│                                 latency for repeat content.         │
│                                                                      │
│  Student quota exceeded         Switch to text-only mode. Show:     │
│                                 "Voice minutes used up for today.   │
│                                  Upgrade for more, or continue      │
│                                  in text mode."                     │
│                                                                      │
│  PRINCIPLE: Voice is an enhancement layer. The core tutoring        │
│  experience (text) must ALWAYS work, regardless of voice system     │
│  state. Progressive enhancement, graceful degradation.              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Voice System Configuration Schema

```
voice_system_config:
  tts:
    primary_provider: "elevenlabs"
    fallback_provider: "google_cloud_tts"
    emergency_fallback: "browser_native"
    default_model: "eleven_turbo_v2"
    default_voice_id: "21m00Tcm4TlvDq8ikWAM"
    default_speed: 1.0
    default_pitch: 0
    max_text_length: 5000  # characters per request
    streaming_enabled: true
    cache_enabled: true
    cache_ttl_seconds: 604800  # 7 days

  stt:
    primary_provider: "deepgram"
    fallback_provider: "whisper_api"
    emergency_fallback: "browser_speech_recognition"
    default_model: "nova-2"
    default_language: "en-US"
    interim_results: true
    profanity_filter: true
    smart_format: true
    endpointing_ms: 1500  # silence before end-of-speech

  conversation:
    turn_timeout_seconds: 30  # max time student can speak
    silence_threshold_ms: 1500  # silence before processing
    interruption_enabled: true
    auto_pause_on_typing: true
    wake_word_enabled: false  # opt-in only
    wake_word: "Hey EduAGI"

  personas:
    friendly_teacher:
      voice_id: "21m00Tcm4TlvDq8ikWAM"
      stability: 0.5
      similarity_boost: 0.75
      style: 0.3
    professional:
      voice_id: "ErXwobaYiN019PkySvjV"
      stability: 0.7
      similarity_boost: 0.8
      style: 0.1
    study_buddy:
      voice_id: "TxGEqnHWrfWFTfGW9XjX"
      stability: 0.4
      similarity_boost: 0.7
      style: 0.5

  rate_limits:
    free_tier:
      tts_chars_per_day: 10000
      stt_minutes_per_day: 30
      concurrent_sessions: 1
    pro_tier:
      tts_chars_per_day: 100000
      stt_minutes_per_day: 180
      concurrent_sessions: 2
```

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| TTS | Text-to-Speech -- converting written text into spoken audio |
| STT | Speech-to-Text -- converting spoken audio into written text |
| SSML | Speech Synthesis Markup Language -- XML tags to control TTS behavior |
| VAD | Voice Activity Detection -- determining when someone is speaking |
| Viseme | Visual representation of a phoneme (mouth shape for lip-sync) |
| Phoneme | Smallest unit of sound in speech |
| Opus | High-quality, low-latency audio codec |
| WebM | Media container format (commonly wraps Opus audio) |
| Wake Word | Trigger phrase that activates voice input (like "Hey Siri") |
| Interim Transcript | Partial, in-progress transcription (may change) |
| Final Transcript | Completed, confirmed transcription |
| LUFS | Loudness Units Full Scale -- standard for audio loudness measurement |
| CDN | Content Delivery Network -- edge servers for fast content delivery |

---

*Document Version History*

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | AGI Team | Initial voice system design |
