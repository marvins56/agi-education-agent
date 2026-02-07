# Architecture Design Document
# EduAGI - Self-Learning Educational AI Agent

**Version:** 1.0
**Date:** February 2026
**Status:** Draft

---

## 1. Architecture Overview

EduAGI follows a **multi-agent, event-driven microservices architecture** designed for scalability, modularity, and extensibility. The system leverages a hierarchical agent structure where specialized agents handle different aspects of the educational experience.

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │   Web    │  │  Mobile  │  │   API    │  │   LMS    │  │  Voice   │      │
│  │  Client  │  │   Apps   │  │ Clients  │  │ Plugins  │  │ Devices  │      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼────────────┘
        │             │             │             │             │
        └─────────────┴─────────────┴──────┬──────┴─────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────┐
│                            API GATEWAY LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Load Balancer  │  │  Auth Service   │  │  Rate Limiter   │              │
│  │    (Nginx)      │  │   (OAuth 2.0)   │  │                 │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
└───────────┴────────────────────┴────────────────────┴───────────────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────┐
│                         ORCHESTRATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                    ┌─────────────────────────────┐                           │
│                    │     MASTER ORCHESTRATOR     │                           │
│                    │    (LangGraph Controller)   │                           │
│                    └──────────────┬──────────────┘                           │
│                                   │                                          │
│    ┌──────────────────────────────┼──────────────────────────────┐          │
│    │                              │                              │          │
│    ▼                              ▼                              ▼          │
│ ┌──────────────┐           ┌──────────────┐           ┌──────────────┐      │
│ │   Session    │           │    Router    │           │   Workflow   │      │
│ │   Manager    │           │    Agent     │           │   Engine     │      │
│ └──────────────┘           └──────────────┘           └──────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────┐
│                         SPECIALIZED AGENTS LAYER                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │  TUTOR AGENT   │  │ ASSESSMENT     │  │   CONTENT      │                 │
│  │                │  │    AGENT       │  │    AGENT       │                 │
│  │ - Socratic     │  │ - Quiz Gen     │  │ - Lesson Plan  │                 │
│  │ - Explanation  │  │ - Grading      │  │ - Materials    │                 │
│  │ - Q&A          │  │ - Feedback     │  │ - Summarize    │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │   VOICE        │  │    AVATAR      │  │ SIGN LANGUAGE  │                 │
│  │   AGENT        │  │    AGENT       │  │    AGENT       │                 │
│  │                │  │                │  │                │                 │
│  │ - ElevenLabs   │  │ - DeepBrain    │  │ - ASL/BSL      │                 │
│  │ - TTS/STT      │  │ - HeyGen       │  │ - Avatar Gen   │                 │
│  │ - Voice Clone  │  │ - Lip Sync     │  │ - Recognition  │                 │
│  └────────────────┘  └────────────────┘  └────────────────┘                 │
│                                                                              │
│  ┌────────────────┐  ┌────────────────┐                                     │
│  │   MEMORY       │  │  ANALYTICS     │                                     │
│  │   AGENT        │  │    AGENT       │                                     │
│  │                │  │                │                                     │
│  │ - Long-term    │  │ - Progress     │                                     │
│  │ - Short-term   │  │ - Performance  │                                     │
│  │ - Context      │  │ - Predictions  │                                     │
│  └────────────────┘  └────────────────┘                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────┐
│                            DATA LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Vector DB  │  │  Relational  │  │    Cache     │  │   Object     │    │
│  │  (ChromaDB)  │  │  (PostgreSQL)│  │   (Redis)    │  │   Storage    │    │
│  │              │  │              │  │              │  │   (S3/MinIO) │    │
│  │ - Embeddings │  │ - Users      │  │ - Sessions   │  │ - Files      │    │
│  │ - Knowledge  │  │ - Progress   │  │ - Contexts   │  │ - Media      │    │
│  │ - RAG Index  │  │ - Grades     │  │ - Hot Data   │  │ - Avatars    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────┐
│                         EXTERNAL SERVICES LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│
│  │  Claude/   │ │ ElevenLabs │ │ DeepBrain  │ │ Sign-Speak │ │   LMS      ││
│  │  OpenAI    │ │   Voice    │ │   Avatar   │ │    ASL     │ │   APIs     ││
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Master Orchestrator

The central coordination component that manages all agent interactions and workflows.

```
┌─────────────────────────────────────────────────────────────────┐
│                     MASTER ORCHESTRATOR                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    LangGraph Controller                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │   │
│  │  │ State   │  │  Graph  │  │  Node   │  │ Memory  │     │   │
│  │  │ Machine │  │ Builder │  │ Router  │  │ Manager │     │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────┐  ┌────────────────────┐                 │
│  │   Intent Classifier │  │   Context Manager  │                 │
│  │                     │  │                    │                 │
│  │  - Tutor request    │  │  - User profile    │                 │
│  │  - Assessment       │  │  - Session state   │                 │
│  │  - Content gen      │  │  - Learning path   │                 │
│  │  - Voice/Avatar     │  │  - Preferences     │                 │
│  └────────────────────┘  └────────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- Route requests to appropriate specialized agents
- Maintain conversation state and context
- Coordinate multi-agent workflows
- Handle error recovery and fallbacks
- Manage agent lifecycle

### 2.2 Memory Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MEMORY SYSTEM                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   MEMORY LAYERS                          │    │
│  │                                                          │    │
│  │  ┌─────────────────┐                                    │    │
│  │  │  WORKING MEMORY │  ← Current conversation context    │    │
│  │  │  (Redis Cache)  │    Session state, recent turns     │    │
│  │  └────────┬────────┘                                    │    │
│  │           │                                              │    │
│  │  ┌────────▼────────┐                                    │    │
│  │  │ EPISODIC MEMORY │  ← Learning session history        │    │
│  │  │  (PostgreSQL)   │    Interactions, outcomes          │    │
│  │  └────────┬────────┘                                    │    │
│  │           │                                              │    │
│  │  ┌────────▼────────┐                                    │    │
│  │  │ SEMANTIC MEMORY │  ← Knowledge base, embeddings      │    │
│  │  │  (ChromaDB)     │    Course content, facts           │    │
│  │  └────────┬────────┘                                    │    │
│  │           │                                              │    │
│  │  ┌────────▼────────┐                                    │    │
│  │  │PROCEDURAL MEMORY│  ← Teaching strategies, methods    │    │
│  │  │  (Config/Code)  │    Best practices, workflows       │    │
│  │  └─────────────────┘                                    │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   STUDENT PROFILE                        │    │
│  │                                                          │    │
│  │  {                                                       │    │
│  │    "student_id": "uuid",                                │    │
│  │    "learning_style": "visual",                          │    │
│  │    "pace": "moderate",                                  │    │
│  │    "strengths": ["math", "logic"],                      │    │
│  │    "weaknesses": ["writing", "history"],                │    │
│  │    "preferences": {                                     │    │
│  │      "voice_enabled": true,                             │    │
│  │      "avatar_enabled": true,                            │    │
│  │      "sign_language": "ASL"                             │    │
│  │    },                                                   │    │
│  │    "progress": {...},                                   │    │
│  │    "interactions": [...]                                │    │
│  │  }                                                      │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 RAG (Retrieval-Augmented Generation) Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG PIPELINE                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   INGESTION PIPELINE                                            │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │
│   │ Document│  │  Text   │  │ Chunk   │  │ Embed   │           │
│   │ Loader  │──▶ Extract │──▶ Splitter│──▶ Model   │           │
│   │         │  │         │  │         │  │         │           │
│   │ PDF,DOCX│  │ Clean   │  │ 512 tok │  │ OpenAI  │           │
│   │ PPTX,TXT│  │ Parse   │  │ overlap │  │ ada-002 │           │
│   └─────────┘  └─────────┘  └─────────┘  └────┬────┘           │
│                                                │                 │
│                                    ┌───────────▼──────────┐     │
│                                    │     VECTOR STORE     │     │
│                                    │      (ChromaDB)      │     │
│                                    │                      │     │
│                                    │  - Subject Index     │     │
│                                    │  - Curriculum Index  │     │
│                                    │  - Q&A Index         │     │
│                                    └───────────┬──────────┘     │
│                                                │                 │
│   RETRIEVAL PIPELINE                          │                 │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───▼─────┐           │
│   │  Query  │  │  Query  │  │ Semantic│  │ Context │           │
│   │  Input  │──▶ Rewrite │──▶ Search  │──▶ Ranking │           │
│   │         │  │         │  │         │  │         │           │
│   └─────────┘  └─────────┘  └─────────┘  └────┬────┘           │
│                                                │                 │
│   GENERATION PIPELINE                         │                 │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───▼─────┐           │
│   │ Response│◀─│  LLM    │◀─│ Prompt  │◀─│Retrieved│           │
│   │ Output  │  │ Claude  │  │ Builder │  │ Context │           │
│   │         │  │         │  │         │  │         │           │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.4 Multi-Modal Output Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                  MULTI-MODAL OUTPUT PIPELINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    ┌──────────────────┐                         │
│                    │   LLM Response   │                         │
│                    │      (Text)      │                         │
│                    └────────┬─────────┘                         │
│                             │                                    │
│           ┌─────────────────┼─────────────────┐                 │
│           │                 │                 │                 │
│           ▼                 ▼                 ▼                 │
│   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐        │
│   │  TEXT OUTPUT  │ │ VOICE OUTPUT  │ │ VISUAL OUTPUT │        │
│   │               │ │               │ │               │        │
│   │  - Markdown   │ │  - ElevenLabs │ │  - Avatar     │        │
│   │  - Formatted  │ │  - Voice ID   │ │  - Sign Lang  │        │
│   │  - Code       │ │  - Streaming  │ │  - Diagrams   │        │
│   └───────────────┘ └───────────────┘ └───────────────┘        │
│           │                 │                 │                 │
│           │                 │                 │                 │
│           │         ┌───────▼───────┐        │                 │
│           │         │   AUDIO SYNC  │        │                 │
│           │         │               │        │                 │
│           │         │  - Timestamps │        │                 │
│           │         │  - Phonemes   │        │                 │
│           │         └───────┬───────┘        │                 │
│           │                 │                 │                 │
│           │         ┌───────▼───────┐        │                 │
│           │         │   AVATAR GEN  │◀───────┘                 │
│           │         │               │                          │
│           │         │  - Lip Sync   │                          │
│           │         │  - Gestures   │                          │
│           │         │  - Sign Lang  │                          │
│           │         └───────┬───────┘                          │
│           │                 │                                   │
│           └────────┬────────┘                                   │
│                    │                                            │
│           ┌────────▼────────┐                                   │
│           │  UNIFIED OUTPUT │                                   │
│           │                 │                                   │
│           │  {              │                                   │
│           │    text: "...", │                                   │
│           │    audio_url,   │                                   │
│           │    video_url,   │                                   │
│           │    sign_video   │                                   │
│           │  }              │                                   │
│           └─────────────────┘                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Agent Design Patterns

### 3.1 Agent Communication Protocol

```python
# Message Protocol
class AgentMessage:
    message_id: str
    sender: str           # Agent ID
    receiver: str         # Agent ID or "orchestrator"
    message_type: str     # "request", "response", "event"
    payload: dict
    context: dict         # Shared context
    timestamp: datetime
    priority: int         # 1-10

# Example Flow
"""
User: "Explain photosynthesis"
    │
    ▼
[Orchestrator]
    │
    ├──▶ [Memory Agent] → Retrieve student context
    │         │
    │         ▼
    │    Student prefers visual learning, knows basic biology
    │
    ├──▶ [Tutor Agent] → Generate explanation
    │         │
    │         ▼
    │    Tailored explanation with diagrams
    │
    ├──▶ [Voice Agent] → Generate audio
    │         │
    │         ▼
    │    ElevenLabs audio stream
    │
    └──▶ [Avatar Agent] → Generate video
              │
              ▼
         Avatar with lip-sync + sign language
"""
```

### 3.2 Agent State Machine

```
                    ┌─────────────────┐
                    │      IDLE       │
                    └────────┬────────┘
                             │ receive_task
                             ▼
                    ┌─────────────────┐
          ┌────────│   PROCESSING    │────────┐
          │        └────────┬────────┘        │
          │                 │                  │
          │ need_info       │ complete        │ error
          ▼                 ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  WAITING_INPUT  │ │   RESPONDING    │ │     ERROR       │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                    │
         │ input_received    │ sent               │ recovered
         │                   │                    │
         └───────────────────┴────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │      IDLE       │
                    └─────────────────┘
```

---

## 4. Data Models

### 4.1 Core Entities

```python
# Student Model
class Student:
    id: UUID
    email: str
    name: str
    created_at: datetime
    preferences: StudentPreferences
    learning_profile: LearningProfile

class StudentPreferences:
    voice_enabled: bool = True
    avatar_enabled: bool = True
    sign_language: Optional[str] = None  # "ASL", "BSL", None
    preferred_voice_id: Optional[str] = None
    theme: str = "light"
    language: str = "en"

class LearningProfile:
    learning_style: str  # "visual", "auditory", "kinesthetic", "reading"
    pace: str  # "slow", "moderate", "fast"
    strengths: List[str]
    weaknesses: List[str]
    grade_level: str
    subjects: List[str]

# Session Model
class Session:
    id: UUID
    student_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    messages: List[Message]
    context: dict
    mode: str  # "tutoring", "assessment", "review"

# Assessment Model
class Assessment:
    id: UUID
    student_id: UUID
    subject: str
    type: str  # "quiz", "assignment", "exam"
    questions: List[Question]
    submissions: List[Submission]
    grade: Optional[Grade]
    created_at: datetime
    due_at: Optional[datetime]

class Question:
    id: UUID
    type: str  # "mcq", "short_answer", "essay", "code"
    content: str
    options: Optional[List[str]]  # For MCQ
    correct_answer: Optional[str]
    rubric: Optional[str]
    points: int
    difficulty: str

class Grade:
    score: float
    max_score: float
    percentage: float
    feedback: str
    detailed_feedback: List[QuestionFeedback]
    graded_at: datetime
    graded_by: str  # "ai" or instructor_id
```

### 4.2 Knowledge Base Schema

```python
# Document for RAG
class KnowledgeDocument:
    id: UUID
    title: str
    content: str
    subject: str
    grade_level: str
    tags: List[str]
    source: str
    embedding: List[float]
    metadata: dict
    created_at: datetime
    updated_at: datetime

# Curriculum Structure
class Curriculum:
    id: UUID
    name: str
    subject: str
    grade_level: str
    modules: List[Module]

class Module:
    id: UUID
    name: str
    learning_objectives: List[str]
    lessons: List[Lesson]
    assessments: List[UUID]

class Lesson:
    id: UUID
    title: str
    content_ids: List[UUID]  # References to KnowledgeDocument
    duration_minutes: int
    prerequisites: List[UUID]
```

---

## 5. API Design

### 5.1 REST API Endpoints

```yaml
# Core API Endpoints
/api/v1:
  /auth:
    POST /login          # User authentication
    POST /register       # User registration
    POST /refresh        # Token refresh

  /sessions:
    POST /               # Start new tutoring session
    GET /{session_id}    # Get session details
    DELETE /{session_id} # End session

  /chat:
    POST /message        # Send message to tutor
    GET /history         # Get conversation history

  /assessments:
    POST /               # Create new assessment
    GET /                # List assessments
    GET /{id}            # Get assessment details
    POST /{id}/submit    # Submit answers
    GET /{id}/grade      # Get grade/feedback

  /content:
    POST /upload         # Upload educational content
    GET /search          # Search knowledge base
    GET /{id}            # Get content details

  /voice:
    POST /synthesize     # Generate speech from text
    GET /voices          # List available voices

  /avatar:
    POST /generate       # Generate avatar video
    GET /status/{job_id} # Check generation status

  /sign-language:
    POST /translate      # Translate text to sign language
    GET /status/{job_id} # Check translation status

  /analytics:
    GET /progress        # Get learning progress
    GET /performance     # Get performance metrics
    GET /recommendations # Get learning recommendations
```

### 5.2 WebSocket Events

```yaml
# Real-time Communication
ws://api/v1/stream:

  # Client → Server
  message.send:
    content: string
    attachments: array

  voice.start:
    # Start voice input

  voice.chunk:
    audio_data: base64

  voice.end:
    # End voice input

  # Server → Client
  response.start:
    session_id: string

  response.text.chunk:
    content: string

  response.audio.chunk:
    audio_data: base64

  response.avatar.ready:
    video_url: string

  response.sign_language.ready:
    video_url: string

  response.complete:
    full_response: object

  error:
    code: string
    message: string
```

---

## 6. Infrastructure Architecture

### 6.1 Cloud Deployment (AWS)

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS CLOUD                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    VPC (10.0.0.0/16)                     │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              Public Subnet (10.0.1.0/24)         │    │    │
│  │  │                                                  │    │    │
│  │  │  ┌──────────────┐    ┌──────────────┐           │    │    │
│  │  │  │     ALB      │    │  CloudFront  │           │    │    │
│  │  │  │ (API Gateway)│    │   (Static)   │           │    │    │
│  │  │  └──────┬───────┘    └──────────────┘           │    │    │
│  │  │         │                                        │    │    │
│  │  └─────────┼────────────────────────────────────────┘    │    │
│  │            │                                              │    │
│  │  ┌─────────▼────────────────────────────────────────┐    │    │
│  │  │              Private Subnet (10.0.2.0/24)        │    │    │
│  │  │                                                  │    │    │
│  │  │  ┌────────────────────────────────────────┐     │    │    │
│  │  │  │            ECS Cluster (Fargate)       │     │    │    │
│  │  │  │                                        │     │    │    │
│  │  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │     │    │    │
│  │  │  │  │   API   │ │  Agent  │ │  Worker │  │     │    │    │
│  │  │  │  │ Service │ │ Service │ │ Service │  │     │    │    │
│  │  │  │  │  (x3)   │ │  (x5)   │ │  (x3)   │  │     │    │    │
│  │  │  │  └─────────┘ └─────────┘ └─────────┘  │     │    │    │
│  │  │  │                                        │     │    │    │
│  │  │  └────────────────────────────────────────┘     │    │    │
│  │  │                                                  │    │    │
│  │  └──────────────────────────────────────────────────┘    │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐    │    │
│  │  │              Data Subnet (10.0.3.0/24)           │    │    │
│  │  │                                                  │    │    │
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐         │    │    │
│  │  │  │   RDS    │ │ ElastiC. │ │    S3    │         │    │    │
│  │  │  │ Postgres │ │  Redis   │ │  Bucket  │         │    │    │
│  │  │  └──────────┘ └──────────┘ └──────────┘         │    │    │
│  │  │                                                  │    │    │
│  │  └──────────────────────────────────────────────────┘    │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  External Services:                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ ChromaDB │ │ Anthropic│ │ElevenLabs│ │DeepBrain │           │
│  │  Cloud   │ │   API    │ │   API    │ │   API    │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Container Architecture

```yaml
# Docker Compose (Development)
services:
  api:
    image: eduagi-api:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://cache:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - db
      - cache
      - chromadb

  agent-worker:
    image: eduagi-agent:latest
    environment:
      - REDIS_URL=redis://cache:6379
      - CHROMADB_URL=http://chromadb:8000
    deploy:
      replicas: 3

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chroma_data:/chroma/chroma
```

---

## 7. Security Architecture

### 7.1 Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  AUTHENTICATION LAYER                    │    │
│  │                                                          │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │    │
│  │  │   OAuth    │  │    SAML    │  │    JWT     │         │    │
│  │  │   2.0      │  │    SSO     │  │   Tokens   │         │    │
│  │  │            │  │            │  │            │         │    │
│  │  │ - Google   │  │ - Okta     │  │ - Access   │         │    │
│  │  │ - Microsoft│  │ - Azure AD │  │ - Refresh  │         │    │
│  │  │ - LMS      │  │ - Custom   │  │ - API Keys │         │    │
│  │  └────────────┘  └────────────┘  └────────────┘         │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  AUTHORIZATION (RBAC)                    │    │
│  │                                                          │    │
│  │  Roles:                                                  │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │    │
│  │  │ Student  │ │ Teacher  │ │  Admin   │ │  Parent  │    │    │
│  │  │          │ │          │ │          │ │          │    │    │
│  │  │-Learn    │ │-Teach    │ │-Manage   │ │-View     │    │    │
│  │  │-Submit   │ │-Grade    │ │-Configure│ │-Monitor  │    │    │
│  │  │-View own │ │-Create   │ │-All      │ │-Child    │    │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   DATA PROTECTION                        │    │
│  │                                                          │    │
│  │  - TLS 1.3 in transit                                   │    │
│  │  - AES-256 at rest                                      │    │
│  │  - PII encryption (student data)                        │    │
│  │  - FERPA/COPPA compliance                               │    │
│  │  - Audit logging                                        │    │
│  │  - Data retention policies                              │    │
│  │                                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Scalability Considerations

### 8.1 Horizontal Scaling Strategy

| Component | Scaling Trigger | Max Instances |
|-----------|-----------------|---------------|
| API Service | CPU > 70% | 10 |
| Agent Workers | Queue depth > 100 | 20 |
| WebSocket Handlers | Connections > 1000 | 10 |
| Voice Workers | Audio queue > 50 | 5 |

### 8.2 Caching Strategy

```
Layer 1: Browser Cache (static assets)
    ↓
Layer 2: CDN Cache (CloudFront)
    ↓
Layer 3: API Response Cache (Redis)
    ↓
Layer 4: LLM Response Cache (Redis)
    ↓
Layer 5: RAG Results Cache (Redis)
    ↓
Layer 6: Database Query Cache (PostgreSQL)
```

### 8.3 Rate Limiting

| Tier | Requests/min | LLM Calls/min | Voice Minutes/day |
|------|--------------|---------------|-------------------|
| Free | 60 | 20 | 30 |
| Pro | 300 | 100 | 180 |
| Enterprise | Unlimited | 500 | Unlimited |

---

## 9. Monitoring & Observability

### 9.1 Metrics & Alerts

```yaml
# Key Metrics
metrics:
  - name: response_latency_p99
    threshold: 5000ms
    alert: critical

  - name: llm_error_rate
    threshold: 5%
    alert: warning

  - name: voice_generation_time
    threshold: 10000ms
    alert: warning

  - name: concurrent_sessions
    threshold: 10000
    alert: info

  - name: rag_retrieval_accuracy
    threshold: 85%
    alert: warning
```

### 9.2 Logging Architecture

```
Application Logs → FluentD → CloudWatch Logs
                              ↓
                     CloudWatch Insights
                              ↓
                     Grafana Dashboard
```

---

## 10. Technology Stack Summary

| Layer | Technology |
|-------|------------|
| **Frontend** | React, TypeScript, TailwindCSS |
| **Backend API** | FastAPI (Python 3.11+) |
| **Agent Framework** | LangChain, LangGraph |
| **LLM** | Claude (Anthropic), GPT-4 (fallback) |
| **Vector DB** | ChromaDB |
| **Relational DB** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **Object Storage** | AWS S3 / MinIO |
| **Voice** | ElevenLabs API |
| **Avatar** | DeepBrain AI / HeyGen |
| **Sign Language** | Sign-Speak API |
| **Container** | Docker, ECS Fargate |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus, Grafana, CloudWatch |

---

*Document Version History*
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | AGI Team | Initial architecture |
