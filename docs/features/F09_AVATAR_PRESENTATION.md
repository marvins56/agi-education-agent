# F09: Avatar Presentation
# EduAGI Feature Design Document

**Priority:** P1 (High)
**Tier:** 2 - Enhanced
**Dependencies:** F01 (Tutoring), F06 (Voice)

---

## 1. Feature Overview

### What It Does
A visual AI presenter that explains concepts with lip-synced speech, gestures,
and visual aids. Like having a friendly teacher on screen who talks to you,
points at things, and reacts to your answers.

### Why It Matters (Student Perspective)
```
  Reading text = 10% retention
  Listening + reading = 20% retention
  Watching a teacher explain = 50% retention
  Watching + interacting = 75% retention

  Students (especially younger ones) ENGAGE more with a face.
  It transforms "reading a chatbot" into "learning from a teacher."
```

### The Student Experience
```
  Student asks: "Can you explain how the heart pumps blood?"

  AI generates text explanation →

  ┌─────────────────────────────────────────────┐
  │  ┌──────────────────┐                       │
  │  │                  │  "The heart has four   │
  │  │   👩‍🏫 Avatar     │   chambers. Blood      │
  │  │   (speaking,     │   enters through the   │
  │  │    pointing to   │   right atrium..."     │
  │  │    diagram)      │                        │
  │  │                  │  [Diagram appears as   │
  │  └──────────────────┘   avatar points to it] │
  │                                             │
  │  [⏸ Pause] [🔄 Replay] [⏩ 1.5x] [📥 Save] │
  └─────────────────────────────────────────────┘
```

---

## 2. Detailed Workflows

### 2.1 When to Generate an Avatar Video

```
┌─────────────────────────────────────────────────────────────┐
│  AVATAR TRIGGER DECISION                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tutor generates response                                   │
│       │                                                     │
│       ▼                                                     │
│  ┌────────────────────────────┐                             │
│  │  Does student have         │                             │
│  │  avatar_enabled = true?    │                             │
│  └─────────┬──────────────────┘                             │
│         NO │    YES                                         │
│         │  │    │                                           │
│         │  │    ▼                                           │
│         │  │  ┌────────────────────────────┐                │
│         │  │  │  Is this response suitable │                │
│         │  │  │  for avatar?               │                │
│         │  │  │                            │                │
│         │  │  │  YES if:                   │                │
│         │  │  │  • Explanation > 100 words  │                │
│         │  │  │  • Complex concept          │                │
│         │  │  │  • Student requested it     │                │
│         │  │  │  • Visual topic (anatomy,   │                │
│         │  │  │    geometry, etc.)          │                │
│         │  │  │                            │                │
│         │  │  │  NO if:                    │                │
│         │  │  │  • Simple Q&A (<50 words)  │                │
│         │  │  │  • Code review             │                │
│         │  │  │  • Quiz question           │                │
│         │  │  └──────────┬─────────────────┘                │
│         │  │          YES│    NO                            │
│         │  │             │    │                             │
│         ▼  ▼             ▼    ▼                             │
│     Text only    Generate avatar   Text + voice only       │
│                  video (async)                              │
│                       │                                    │
│                       ▼                                    │
│              Student gets text immediately                  │
│              + notification when video ready                │
│              "📹 Video explanation ready! [Watch]"          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Mode A: Pre-Generated Avatar Video (MVP)

```
  Tutor text response ready
       │
       ▼
  ┌──────────────────────┐
  │ 1. PREPARE SCRIPT    │
  │                      │
  │ Clean text for speech:│
  │ • Remove markdown    │
  │ • Expand abbreviations│
  │ • Add pauses (...)   │
  │ • Split into segments│
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │ 2. GENERATE AUDIO    │
  │    (ElevenLabs)      │
  │                      │
  │ Text → audio file    │
  │ + timing data        │
  │ (word timestamps)    │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │ 3. SEND TO AVATAR API│
  │    (DeepBrain/HeyGen)│
  │                      │
  │ Audio + avatar config│
  │ → async job created  │
  │ → job_id returned    │
  │                      │
  │ Takes: 15-60 seconds │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │ 4. POLL FOR STATUS   │
  │                      │
  │ Every 5 sec check:   │
  │ "Is job done?"       │
  │                      │
  │ Done → get video URL │
  └──────────┬───────────┘
             │
             ▼
  ┌──────────────────────┐
  │ 5. CACHE + DELIVER   │
  │                      │
  │ Store video in S3/CDN│
  │ Notify student:      │
  │ "Video ready! [Play]"│
  └──────────────────────┘
```

### 2.3 Mode B: Real-Time Lightweight Avatar (Future)

```
  ┌─────────────────────────────────────────────────────────┐
  │  CLIENT-SIDE AVATAR (no API needed)                     │
  │                                                         │
  │  How it works:                                          │
  │                                                         │
  │  1. Pre-built 3D character model loaded in browser      │
  │     (Three.js / Babylon.js / Ready Player Me)           │
  │                                                         │
  │  2. Audio stream from ElevenLabs provides:              │
  │     • Audio data (for playback)                         │
  │     • Viseme data (mouth shapes per phoneme)            │
  │                                                         │
  │  3. Client-side renderer:                               │
  │     • Lip-syncs to viseme data                          │
  │     • Adds idle animations (blinking, breathing)        │
  │     • Gesture triggers from text analysis               │
  │       ("first" → holds up 1 finger)                     │
  │       ("think about" → tilts head)                      │
  │       ("great job!" → smiles, nods)                     │
  │                                                         │
  │  Latency: Near-zero (same as audio)                     │
  │  Cost: Zero API cost (all client-side)                  │
  │  Quality: Lower than deepfake, but responsive           │
  │                                                         │
  │  Good for: Real-time conversation, low-bandwidth        │
  │  Bad for: Marketing videos, highly realistic needs      │
  └─────────────────────────────────────────────────────────┘
```

### 2.4 Avatar Customization Flow

```
  First time setup (or Settings → Avatar):

  ┌─────────────────────────────────────────────────┐
  │  Choose Your AI Tutor                           │
  │                                                 │
  │  ┌────┐  ┌────┐  ┌────┐  ┌────┐  ┌────┐       │
  │  │ 👩 │  │ 👨 │  │ 👩‍🦱 │  │ 🧔 │  │ 🤖 │       │
  │  │Sara│  │Alex│  │Maya│  │Prof│  │Byte│       │
  │  │    │  │    │  │    │  │ K  │  │Bot │       │
  │  └────┘  └────┘  └────┘  └────┘  └────┘       │
  │  Friendly  Calm   Energetic Formal  Cartoon    │
  │  Teacher  Mentor  Study Buddy Expert Mascot    │
  │                                                 │
  │  Style: [Realistic ▼]  Voice: [Warm ▼]         │
  │                                                 │
  │  Preview: [▶ Watch sample explanation]          │
  │                                                 │
  │  [Save Choice]                                  │
  └─────────────────────────────────────────────────┘

  Diversity: Avatars represent different ages, ethnicities,
  genders. Students see themselves reflected.

  For younger students (K-5): Animated cartoon characters
  available (friendly robot, animal mascots, etc.)
```

---

## 3. Sub-features & Small Touches

### Whiteboard Mode
```
  Avatar + virtual whiteboard side by side.

  ┌──────────────────────────────────────────────┐
  │  ┌──────────┐  ┌──────────────────────────┐  │
  │  │          │  │                          │  │
  │  │  Avatar  │  │  WHITEBOARD              │  │
  │  │ (talking,│  │                          │  │
  │  │  pointing│  │  y = ax² + bx + c       │  │
  │  │  at board│  │      ↑                   │  │
  │  │    →)    │  │  [diagram being drawn    │  │
  │  │          │  │   as avatar explains]    │  │
  │  │          │  │                          │  │
  │  └──────────┘  └──────────────────────────┘  │
  └──────────────────────────────────────────────┘

  Whiteboard content synced with explanation timing.
  Uses Excalidraw or custom canvas for diagrams.
```

### Other Small Touches
- **Gesture matching** — avatar gestures match content naturally
  - Counting: holds up fingers
  - "Think about it": tilts head, looks up
  - "Great job!": smiles, thumbs up
  - "Let me explain": leans forward
  - Confused student detected: avatar makes empathetic face
- **Picture-in-picture** — small avatar in corner while student reads
- **Avatar reactions** — responds to student answers (smile, nod, encouraging expression)
- **Speed control** — 0.5x, 1x, 1.5x, 2x playback
- **Subtitles/captions** — always on by default, toggleable
- **Save favorites** — bookmark avatar explanations to rewatch
- **"Watch explanation"** button on difficult concepts
- **Auto-suggest** — "This is a complex topic. Want to watch a video explanation?"

---

## 4. Technical Requirements

### Video Generation
```
  Format: MP4 (H.264) or WebM (VP9)
  Resolution: 720p default, 1080p optional
  Frame rate: 30fps
  Max duration: 5 minutes per video
  Typical size: ~5MB per minute (720p)
```

### Storage & CDN
```
  Storage: S3 (or compatible)
  CDN: CloudFront for delivery
  Cache strategy:
  • Same explanation → same video (content-addressed hash)
  • Popular explanations pre-cached
  • Expire after 30 days if not accessed
  • Estimated storage: ~500GB for 100K cached videos
```

### Client-Side Rendering (Mode B)
```
  Libraries:
  • Three.js or Babylon.js for 3D rendering
  • Ready Player Me SDK for avatar models
  • Rhubarb Lip Sync or Oculus LipSync for visemes
  • GSAP for animation timing

  Browser requirements:
  • WebGL 2.0 support
  • ~100MB initial model download (cached)
  • 30fps on mid-range devices
  • Fallback: 2D animated avatar for low-end devices
```

---

## 5. Services & Alternatives

### Avatar Video Generation (API-based)

| Service | Pricing | Quality | Latency | Best For |
|---------|---------|---------|---------|----------|
| **DeepBrain AI (Primary)** | ~$0.50-1.50/min | High (realistic) | 30-60s | Polished explanations |
| HeyGen | ~$0.50-2.00/min | High | 30-60s | Multi-language |
| D-ID | ~$0.10-0.50/min | Medium-High | 15-30s | Cost-effective |
| Synthesia | Enterprise pricing | Very High | 60s+ | Enterprise clients |
| Colossyan | ~$0.50/min | High | 30s | Education-focused |

### Lightweight Client-Side Avatar

| Solution | Cost | Quality | Latency | Best For |
|----------|------|---------|---------|----------|
| **Ready Player Me + Three.js** | Free | Medium (3D cartoon) | Real-time | Interactive tutoring |
| Three.js custom | Dev time | Custom | Real-time | Full control |
| Lottie animations | Free | Medium (2D) | Real-time | Simple, mobile-friendly |
| Live2D | License fee | High (anime-style) | Real-time | Engaging for younger students |

### Whiteboard Integration

| Service | Type | Cost |
|---------|------|------|
| **Excalidraw** | Open-source | Free |
| tldraw | Open-source | Free |
| Miro API | API | Paid |
| Custom Canvas | Built-in | Dev time |

### Video CDN

| Service | Pricing | Pros | Cons |
|---------|---------|------|------|
| **CloudFront** | ~$0.085/GB | AWS ecosystem, reliable | Complex pricing |
| Cloudflare Stream | $1/1K min stored + $5/1K min delivered | Simple pricing | Less configurable |
| Mux | $0.007/min stored + $0.007/min streamed | Developer-friendly | Adds up at scale |
| Bunny.net | ~$0.01/GB | Cheapest | Smaller company |

**Recommendation:** DeepBrain for pre-generated (MVP), Ready Player Me + Three.js for real-time (v2), CloudFront for CDN.

---

## 6. Connections & Dependencies

```
  ┌──────────┐     text/script     ┌──────────────┐
  │ F01      │────────────────────▶│              │
  │ Tutor    │                     │  F09 Avatar  │
  │ Agent    │                     │              │
  └──────────┘                     └──────┬───────┘
                                          │
  ┌──────────┐     audio + timing  ┌──────┴───────┐
  │ F06      │────────────────────▶│  Avatar API  │
  │ Voice    │                     │  (DeepBrain) │
  │ Agent    │                     └──────┬───────┘
  └──────────┘                            │
                                          │ video
                                          ▼
                                   ┌──────────────┐
                                   │  S3 + CDN    │
                                   │  (storage +  │
                                   │   delivery)  │
                                   └──────┬───────┘
                                          │
                                          ▼
                                   Student's browser

  F09 DEPENDS ON:
  • F01 (Tutor) — provides the explanation text
  • F06 (Voice) — provides the audio for lip-sync
  • S3/CDN — stores and delivers video files

  F09 IS OPTIONAL FOR:
  • All features work without avatar
  • Progressive enhancement only
```

---

## 7. Cost Analysis

```
  Scenario: 1,000 daily active students, each watches ~3 avatar videos/day

  Pre-generated (DeepBrain):
  • 3,000 videos/day × avg 2 min = 6,000 minutes
  • With 60% cache hit rate → 2,400 new minutes/day
  • At $1/min = $2,400/day = $72,000/month  ← EXPENSIVE

  Cost reduction strategies:
  • Aggressive caching (popular explanations = generate once)
  • Limit to 5 avatar videos per student per day
  • Use lightweight mode for real-time, API for "premium"
  • Pre-generate top 500 common explanations in batch

  With caching + limits:
  • ~500 new unique videos/day × 2 min = 1,000 min
  • At $1/min = $1,000/day = $30,000/month

  Lightweight mode (Three.js):
  • Zero per-use cost
  • One-time dev cost: ~2-4 weeks of engineering
  • Ongoing: CDN for 3D model assets (~$50/month)

  RECOMMENDATION: Start with lightweight (Three.js) for MVP,
  add pre-generated for "premium" explanations.
```

---

*End of F09 Avatar Presentation Design*
