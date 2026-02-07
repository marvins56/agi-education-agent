# Technical Design Document
# EduAGI - Self-Learning Educational AI Agent

**Version:** 1.0
**Date:** February 2026
**Status:** Draft

---

## 1. Introduction

This document provides detailed technical specifications for implementing the EduAGI system. It covers agent implementations, data flows, API contracts, and integration patterns.

---

## 2. Agent Implementations

### 2.1 Base Agent Interface

```python
# src/agents/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
from langchain.schema import AgentAction, AgentFinish

class AgentConfig(BaseModel):
    """Configuration for agent initialization"""
    name: str
    model: str = "claude-3-opus"
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: list[str] = []
    memory_enabled: bool = True

class AgentContext(BaseModel):
    """Shared context passed between agents"""
    session_id: str
    student_id: str
    student_profile: Dict[str, Any]
    conversation_history: list[Dict[str, str]]
    current_subject: Optional[str] = None
    current_topic: Optional[str] = None
    learning_objectives: list[str] = []

class AgentResponse(BaseModel):
    """Standardized agent response"""
    text: str
    metadata: Dict[str, Any] = {}
    suggested_actions: list[str] = []
    requires_voice: bool = False
    requires_avatar: bool = False
    requires_sign_language: bool = False

class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = self._initialize_llm()
        self.tools = self._load_tools()
        self.memory = self._initialize_memory() if config.memory_enabled else None

    @abstractmethod
    async def process(self, input: str, context: AgentContext) -> AgentResponse:
        """Process input and return response"""
        pass

    @abstractmethod
    def get_system_prompt(self, context: AgentContext) -> str:
        """Generate system prompt based on context"""
        pass

    def _initialize_llm(self):
        """Initialize the LLM with configuration"""
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

    def _load_tools(self) -> list:
        """Load tools specified in config"""
        from src.tools import tool_registry
        return [tool_registry.get(name) for name in self.config.tools]

    def _initialize_memory(self):
        """Initialize agent memory"""
        from langchain.memory import ConversationBufferWindowMemory
        return ConversationBufferWindowMemory(k=10)
```

### 2.2 Tutor Agent

```python
# src/agents/tutor_agent.py
from src.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResponse
from src.memory.student_memory import StudentMemoryManager
from src.rag.knowledge_retriever import KnowledgeRetriever

class TutorAgent(BaseAgent):
    """
    Primary tutoring agent that handles educational interactions.
    Implements Socratic dialogue, adaptive explanations, and personalized teaching.
    """

    def __init__(self, config: AgentConfig = None):
        super().__init__(config or AgentConfig(
            name="tutor",
            model="claude-3-opus",
            temperature=0.7,
            tools=["knowledge_search", "example_generator", "diagram_creator"]
        ))
        self.knowledge_retriever = KnowledgeRetriever()
        self.student_memory = StudentMemoryManager()

    def get_system_prompt(self, context: AgentContext) -> str:
        profile = context.student_profile
        return f"""You are EduAGI, a patient and adaptive AI tutor.

STUDENT PROFILE:
- Name: {profile.get('name', 'Student')}
- Learning Style: {profile.get('learning_style', 'balanced')}
- Pace: {profile.get('pace', 'moderate')}
- Grade Level: {profile.get('grade_level', 'general')}
- Strengths: {', '.join(profile.get('strengths', []))}
- Areas for Improvement: {', '.join(profile.get('weaknesses', []))}

TEACHING GUIDELINES:
1. Use Socratic questioning - guide discovery rather than giving direct answers
2. Adapt explanations to the student's learning style:
   - Visual: Use diagrams, charts, mental images
   - Auditory: Use verbal explanations, analogies, stories
   - Kinesthetic: Use examples, hands-on problems, simulations
   - Reading: Provide detailed written explanations, references
3. Break complex topics into smaller, digestible parts
4. Provide encouragement but avoid excessive praise
5. Check for understanding with follow-up questions
6. Use examples relevant to the student's interests when possible
7. If the student is struggling, try a different approach

CURRENT CONTEXT:
- Subject: {context.current_subject or 'General'}
- Topic: {context.current_topic or 'Open'}
- Learning Objectives: {', '.join(context.learning_objectives) or 'None specified'}

Remember: Your goal is to help the student truly understand, not just memorize."""

    async def process(self, input: str, context: AgentContext) -> AgentResponse:
        # Retrieve relevant knowledge
        knowledge_context = await self.knowledge_retriever.retrieve(
            query=input,
            subject=context.current_subject,
            filters={"grade_level": context.student_profile.get("grade_level")}
        )

        # Get student's previous interactions on this topic
        student_history = await self.student_memory.get_topic_history(
            student_id=context.student_id,
            topic=context.current_topic
        )

        # Build the prompt
        messages = [
            {"role": "system", "content": self.get_system_prompt(context)},
            {"role": "system", "content": f"KNOWLEDGE CONTEXT:\n{knowledge_context}"},
            {"role": "system", "content": f"STUDENT HISTORY ON TOPIC:\n{student_history}"}
        ]

        # Add conversation history
        for msg in context.conversation_history[-10:]:
            messages.append(msg)

        # Add current input
        messages.append({"role": "user", "content": input})

        # Generate response
        response = await self.llm.ainvoke(messages)

        # Analyze response for multi-modal needs
        needs_visual = self._needs_visual_aid(input, response.content)

        # Save interaction to memory
        await self.student_memory.save_interaction(
            student_id=context.student_id,
            topic=context.current_topic,
            input=input,
            response=response.content
        )

        return AgentResponse(
            text=response.content,
            metadata={
                "knowledge_sources": knowledge_context.get("sources", []),
                "confidence": self._calculate_confidence(response)
            },
            requires_voice=context.student_profile.get("voice_enabled", False),
            requires_avatar=context.student_profile.get("avatar_enabled", False),
            requires_sign_language=context.student_profile.get("sign_language") is not None
        )

    def _needs_visual_aid(self, input: str, response: str) -> bool:
        """Determine if response would benefit from visual aids"""
        visual_keywords = ["diagram", "graph", "chart", "visualize", "picture",
                          "draw", "show", "illustrate", "structure", "flow"]
        return any(kw in input.lower() or kw in response.lower() for kw in visual_keywords)

    def _calculate_confidence(self, response) -> float:
        """Calculate confidence score for the response"""
        # Implementation based on response characteristics
        return 0.85  # Placeholder
```

### 2.3 Assessment Agent

```python
# src/agents/assessment_agent.py
from src.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResponse
from src.assessment.question_generator import QuestionGenerator
from src.assessment.grader import AutoGrader
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class QuestionType(Enum):
    MCQ = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"
    CODE = "code"
    MATH = "math"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_in_blank"

class Question(BaseModel):
    id: str
    type: QuestionType
    content: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    rubric: Optional[str] = None
    points: int = 10
    difficulty: str = "medium"  # easy, medium, hard
    topic: str
    learning_objective: Optional[str] = None

class AssessmentConfig(BaseModel):
    subject: str
    topics: List[str]
    difficulty: str = "medium"
    question_count: int = 10
    question_types: List[QuestionType] = [QuestionType.MCQ, QuestionType.SHORT_ANSWER]
    time_limit_minutes: Optional[int] = None
    adaptive: bool = True  # Adjust difficulty based on performance

class GradeResult(BaseModel):
    question_id: str
    score: float
    max_score: float
    feedback: str
    correct: bool

class AssessmentAgent(BaseAgent):
    """
    Agent responsible for creating assessments, administering tests, and grading.
    """

    def __init__(self, config: AgentConfig = None):
        super().__init__(config or AgentConfig(
            name="assessment",
            model="claude-3-opus",
            temperature=0.3,  # Lower temperature for more consistent grading
            tools=["knowledge_search", "code_executor", "math_solver"]
        ))
        self.question_generator = QuestionGenerator()
        self.grader = AutoGrader()

    def get_system_prompt(self, context: AgentContext) -> str:
        return """You are an assessment specialist AI. Your responsibilities:

1. QUESTION GENERATION:
   - Create clear, unambiguous questions
   - Align questions with learning objectives
   - Ensure appropriate difficulty level
   - Include distractors (for MCQ) that test common misconceptions
   - Create comprehensive rubrics for open-ended questions

2. GRADING:
   - Apply rubrics consistently and fairly
   - Provide constructive, specific feedback
   - Identify areas of misunderstanding
   - Suggest resources for improvement
   - Be encouraging while being honest about errors

3. ACADEMIC INTEGRITY:
   - Generate unique questions to prevent cheating
   - Detect potential plagiarism patterns
   - Vary question order and options

4. ADAPTIVE ASSESSMENT:
   - Adjust difficulty based on student performance
   - Identify knowledge gaps
   - Recommend follow-up topics

Always be fair, consistent, and educational in your assessments."""

    async def generate_assessment(
        self,
        config: AssessmentConfig,
        context: AgentContext
    ) -> List[Question]:
        """Generate a complete assessment based on configuration"""

        questions = []
        student_level = context.student_profile.get("grade_level", "general")

        for topic in config.topics:
            # Retrieve relevant content for question generation
            knowledge = await self.knowledge_retriever.retrieve(
                query=topic,
                subject=config.subject,
                filters={"grade_level": student_level}
            )

            # Generate questions for this topic
            topic_questions = await self.question_generator.generate(
                topic=topic,
                knowledge_context=knowledge,
                question_types=config.question_types,
                difficulty=config.difficulty,
                count=config.question_count // len(config.topics)
            )
            questions.extend(topic_questions)

        return questions

    async def grade_submission(
        self,
        questions: List[Question],
        answers: dict,  # {question_id: answer}
        context: AgentContext
    ) -> List[GradeResult]:
        """Grade a student's submission"""

        results = []
        for question in questions:
            answer = answers.get(question.id)

            if question.type == QuestionType.MCQ:
                result = self._grade_mcq(question, answer)
            elif question.type == QuestionType.CODE:
                result = await self._grade_code(question, answer)
            elif question.type in [QuestionType.SHORT_ANSWER, QuestionType.ESSAY]:
                result = await self._grade_open_ended(question, answer, context)
            elif question.type == QuestionType.MATH:
                result = await self._grade_math(question, answer)
            else:
                result = self._grade_exact_match(question, answer)

            results.append(result)

        return results

    def _grade_mcq(self, question: Question, answer: str) -> GradeResult:
        """Grade multiple choice question"""
        correct = answer == question.correct_answer
        return GradeResult(
            question_id=question.id,
            score=question.points if correct else 0,
            max_score=question.points,
            feedback="Correct!" if correct else f"The correct answer was: {question.correct_answer}",
            correct=correct
        )

    async def _grade_open_ended(
        self,
        question: Question,
        answer: str,
        context: AgentContext
    ) -> GradeResult:
        """Grade essay or short answer using LLM"""

        grading_prompt = f"""Grade the following answer based on the rubric provided.

QUESTION: {question.content}

RUBRIC: {question.rubric}

STUDENT ANSWER: {answer}

MAX POINTS: {question.points}

Provide:
1. A score (0 to {question.points})
2. Specific feedback explaining the score
3. Suggestions for improvement

Format your response as JSON:
{{"score": <number>, "feedback": "<string>", "suggestions": "<string>"}}"""

        response = await self.llm.ainvoke([
            {"role": "system", "content": self.get_system_prompt(context)},
            {"role": "user", "content": grading_prompt}
        ])

        # Parse response (with error handling)
        import json
        try:
            result = json.loads(response.content)
            return GradeResult(
                question_id=question.id,
                score=result["score"],
                max_score=question.points,
                feedback=f"{result['feedback']}\n\nSuggestions: {result['suggestions']}",
                correct=result["score"] >= question.points * 0.7
            )
        except json.JSONDecodeError:
            # Fallback parsing
            return GradeResult(
                question_id=question.id,
                score=0,
                max_score=question.points,
                feedback="Unable to grade automatically. Please review manually.",
                correct=False
            )

    async def _grade_code(self, question: Question, answer: str) -> GradeResult:
        """Grade code submission by running tests"""
        from src.tools.code_executor import CodeExecutor

        executor = CodeExecutor()
        test_results = await executor.run_tests(
            code=answer,
            test_cases=question.metadata.get("test_cases", [])
        )

        passed = sum(1 for r in test_results if r["passed"])
        total = len(test_results)
        score = (passed / total) * question.points if total > 0 else 0

        feedback_parts = [f"Passed {passed}/{total} test cases."]
        for result in test_results:
            if not result["passed"]:
                feedback_parts.append(f"- Failed: {result['name']}: {result['error']}")

        return GradeResult(
            question_id=question.id,
            score=score,
            max_score=question.points,
            feedback="\n".join(feedback_parts),
            correct=passed == total
        )
```

### 2.4 Voice Agent (ElevenLabs Integration)

```python
# src/agents/voice_agent.py
import aiohttp
import asyncio
from typing import AsyncIterator, Optional
from src.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResponse
from pydantic import BaseModel

class VoiceConfig(BaseModel):
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Default ElevenLabs voice
    model_id: str = "eleven_turbo_v2"
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True

class VoiceAgent(BaseAgent):
    """
    Agent responsible for text-to-speech conversion using ElevenLabs.
    Supports streaming audio and multiple voice personas.
    """

    ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, config: AgentConfig = None):
        super().__init__(config or AgentConfig(
            name="voice",
            model="claude-3-haiku",  # Lightweight model for voice tasks
            temperature=0.3
        ))
        self.api_key = api_key
        self.voice_config = VoiceConfig()
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
        return self._session

    async def synthesize(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None
    ) -> bytes:
        """Convert text to speech, return audio bytes"""

        config = voice_config or self.voice_config
        session = await self._get_session()

        url = f"{self.ELEVENLABS_API_URL}/text-to-speech/{config.voice_id}"

        payload = {
            "text": text,
            "model_id": config.model_id,
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost,
                "style": config.style,
                "use_speaker_boost": config.use_speaker_boost
            }
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.read()
            else:
                error = await response.text()
                raise Exception(f"ElevenLabs API error: {error}")

    async def synthesize_stream(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None
    ) -> AsyncIterator[bytes]:
        """Stream audio chunks for real-time playback"""

        config = voice_config or self.voice_config
        session = await self._get_session()

        url = f"{self.ELEVENLABS_API_URL}/text-to-speech/{config.voice_id}/stream"

        payload = {
            "text": text,
            "model_id": config.model_id,
            "voice_settings": {
                "stability": config.stability,
                "similarity_boost": config.similarity_boost
            }
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                async for chunk in response.content.iter_chunked(1024):
                    yield chunk
            else:
                error = await response.text()
                raise Exception(f"ElevenLabs streaming error: {error}")

    async def get_available_voices(self) -> list:
        """Get list of available voices"""

        session = await self._get_session()
        url = f"{self.ELEVENLABS_API_URL}/voices"

        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("voices", [])
            else:
                return []

    async def clone_voice(self, name: str, audio_files: list[bytes]) -> str:
        """Clone a voice from audio samples (for personalization)"""

        session = await self._get_session()
        url = f"{self.ELEVENLABS_API_URL}/voices/add"

        # Prepare multipart form data
        data = aiohttp.FormData()
        data.add_field("name", name)
        for i, audio in enumerate(audio_files):
            data.add_field(
                f"files",
                audio,
                filename=f"sample_{i}.mp3",
                content_type="audio/mpeg"
            )

        async with session.post(url, data=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("voice_id")
            else:
                error = await response.text()
                raise Exception(f"Voice cloning error: {error}")

    def get_system_prompt(self, context: AgentContext) -> str:
        return "Voice synthesis agent - converts text to natural speech."

    async def process(self, input: str, context: AgentContext) -> AgentResponse:
        """Process text and return voice synthesis"""

        # Select appropriate voice based on context
        voice_id = context.student_profile.get(
            "preferred_voice_id",
            self.voice_config.voice_id
        )

        audio = await self.synthesize(
            text=input,
            voice_config=VoiceConfig(voice_id=voice_id)
        )

        return AgentResponse(
            text=input,
            metadata={
                "audio_data": audio,
                "voice_id": voice_id,
                "duration_estimate": len(input) / 15  # Rough estimate
            }
        )

    async def close(self):
        """Clean up resources"""
        if self._session and not self._session.closed:
            await self._session.close()
```

### 2.5 Sign Language Agent

```python
# src/agents/sign_language_agent.py
from src.agents.base import BaseAgent, AgentConfig, AgentContext, AgentResponse
from typing import Optional
from enum import Enum
import aiohttp

class SignLanguageType(Enum):
    ASL = "american_sign_language"
    BSL = "british_sign_language"
    ISL = "international_sign_language"

class SignLanguageAgent(BaseAgent):
    """
    Agent responsible for translating text to sign language avatar videos.
    Integrates with Sign-Speak API or similar services.
    """

    def __init__(self, api_key: str, config: AgentConfig = None):
        super().__init__(config or AgentConfig(
            name="sign_language",
            model="claude-3-haiku",
            temperature=0.3
        ))
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def translate_to_sign(
        self,
        text: str,
        sign_language: SignLanguageType = SignLanguageType.ASL,
        avatar_style: str = "realistic"
    ) -> dict:
        """
        Translate text to sign language video.

        Returns:
            dict with video_url, duration, and glosses (sign notation)
        """

        # Preprocess text for sign language
        processed_text = await self._preprocess_for_sign(text, sign_language)

        # Call sign language API
        session = await self._get_session()

        # Example API call (adjust for actual service)
        url = "https://api.sign-speak.com/v1/translate"
        payload = {
            "text": processed_text,
            "language": sign_language.value,
            "avatar_style": avatar_style,
            "output_format": "video/mp4"
        }

        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "video_url": result.get("video_url"),
                    "duration": result.get("duration"),
                    "glosses": result.get("glosses"),  # Sign notation
                    "status": "completed"
                }
            elif response.status == 202:
                # Async job - return job ID for polling
                result = await response.json()
                return {
                    "job_id": result.get("job_id"),
                    "status": "processing"
                }
            else:
                error = await response.text()
                raise Exception(f"Sign language API error: {error}")

    async def _preprocess_for_sign(
        self,
        text: str,
        sign_language: SignLanguageType
    ) -> str:
        """
        Preprocess text for better sign language translation.
        Sign languages have different grammar than spoken languages.
        """

        prompt = f"""Convert the following text to be more suitable for {sign_language.value} translation.
Sign language grammar is different from English:
- Topic-comment structure (topic comes first)
- Time indicators at the beginning
- Yes/no questions use facial expressions
- Simplified sentence structure

Original: {text}

Provide the rewritten text optimized for sign language translation:"""

        response = await self.llm.ainvoke([
            {"role": "user", "content": prompt}
        ])

        return response.content.strip()

    async def recognize_sign(self, video_data: bytes) -> str:
        """
        Recognize sign language from video input.
        Converts user's sign language to text.
        """

        session = await self._get_session()
        url = "https://api.sign-speak.com/v1/recognize"

        data = aiohttp.FormData()
        data.add_field(
            "video",
            video_data,
            filename="input.webm",
            content_type="video/webm"
        )

        async with session.post(url, data=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("transcription", "")
            else:
                error = await response.text()
                raise Exception(f"Sign recognition error: {error}")

    async def get_sign_dictionary(
        self,
        word: str,
        sign_language: SignLanguageType = SignLanguageType.ASL
    ) -> dict:
        """Get sign language video for a specific word/phrase"""

        session = await self._get_session()
        url = f"https://api.sign-speak.com/v1/dictionary"
        params = {
            "word": word,
            "language": sign_language.value
        }

        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": "Word not found in dictionary"}

    def get_system_prompt(self, context: AgentContext) -> str:
        return """Sign language translation agent. Converts text to sign language
        video representations for deaf and hard-of-hearing users."""

    async def process(self, input: str, context: AgentContext) -> AgentResponse:
        """Process text and return sign language video"""

        sign_lang = SignLanguageType(
            context.student_profile.get("sign_language", "american_sign_language")
        )

        result = await self.translate_to_sign(input, sign_lang)

        return AgentResponse(
            text=input,
            metadata={
                "sign_video_url": result.get("video_url"),
                "sign_glosses": result.get("glosses"),
                "duration": result.get("duration"),
                "sign_language": sign_lang.value
            },
            requires_sign_language=True
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self._session
```

---

## 3. Memory System Implementation

### 3.1 Memory Manager

```python
# src/memory/memory_manager.py
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from redis import asyncio as aioredis
from chromadb import AsyncClient as ChromaClient
import asyncpg

class MemoryManager:
    """
    Unified memory management system combining:
    - Working Memory (Redis): Current session context
    - Episodic Memory (PostgreSQL): Learning history
    - Semantic Memory (ChromaDB): Knowledge embeddings
    """

    def __init__(
        self,
        redis_url: str,
        postgres_url: str,
        chroma_host: str
    ):
        self.redis_url = redis_url
        self.postgres_url = postgres_url
        self.chroma_host = chroma_host

        self._redis: Optional[aioredis.Redis] = None
        self._pg_pool: Optional[asyncpg.Pool] = None
        self._chroma: Optional[ChromaClient] = None

    async def initialize(self):
        """Initialize all memory backends"""
        self._redis = aioredis.from_url(self.redis_url)
        self._pg_pool = await asyncpg.create_pool(self.postgres_url)
        self._chroma = ChromaClient(host=self.chroma_host)

    # ===== Working Memory (Redis) =====

    async def set_session_context(
        self,
        session_id: str,
        context: Dict[str, Any],
        ttl: int = 3600  # 1 hour default
    ):
        """Store current session context"""
        key = f"session:{session_id}:context"
        await self._redis.setex(key, ttl, json.dumps(context))

    async def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve current session context"""
        key = f"session:{session_id}:context"
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def add_to_conversation(
        self,
        session_id: str,
        role: str,
        content: str
    ):
        """Add message to conversation history"""
        key = f"session:{session_id}:messages"
        message = json.dumps({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self._redis.rpush(key, message)
        # Keep only last 50 messages in working memory
        await self._redis.ltrim(key, -50, -1)

    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get recent conversation history"""
        key = f"session:{session_id}:messages"
        messages = await self._redis.lrange(key, -limit, -1)
        return [json.loads(m) for m in messages]

    # ===== Episodic Memory (PostgreSQL) =====

    async def save_learning_event(
        self,
        student_id: str,
        event_type: str,  # "lesson", "quiz", "interaction"
        subject: str,
        topic: str,
        data: Dict[str, Any],
        outcome: Optional[str] = None
    ):
        """Save a learning event to long-term storage"""
        query = """
            INSERT INTO learning_events
            (student_id, event_type, subject, topic, data, outcome, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
            RETURNING id
        """
        async with self._pg_pool.acquire() as conn:
            return await conn.fetchval(
                query,
                student_id,
                event_type,
                subject,
                topic,
                json.dumps(data),
                outcome
            )

    async def get_student_history(
        self,
        student_id: str,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve student's learning history"""
        query = """
            SELECT * FROM learning_events
            WHERE student_id = $1
            AND ($2::text IS NULL OR subject = $2)
            AND ($3::text IS NULL OR topic = $3)
            ORDER BY created_at DESC
            LIMIT $4
        """
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(query, student_id, subject, topic, limit)
            return [dict(row) for row in rows]

    async def get_student_performance(
        self,
        student_id: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get aggregated performance metrics"""
        query = """
            SELECT
                subject,
                COUNT(*) as total_events,
                AVG(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_rate,
                COUNT(DISTINCT topic) as topics_covered
            FROM learning_events
            WHERE student_id = $1
            AND ($2::text IS NULL OR subject = $2)
            GROUP BY subject
        """
        async with self._pg_pool.acquire() as conn:
            rows = await conn.fetch(query, student_id, subject)
            return {row['subject']: dict(row) for row in rows}

    # ===== Semantic Memory (ChromaDB) =====

    async def store_knowledge(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        collection_name: str = "knowledge_base"
    ):
        """Store documents in vector database"""
        collection = await self._chroma.get_or_create_collection(collection_name)

        # Generate IDs
        ids = [f"doc_{i}_{datetime.utcnow().timestamp()}" for i in range(len(documents))]

        await collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    async def search_knowledge(
        self,
        query: str,
        collection_name: str = "knowledge_base",
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant knowledge"""
        collection = await self._chroma.get_collection(collection_name)

        results = await collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filters
        )

        return [
            {
                "content": doc,
                "metadata": meta,
                "distance": dist
            }
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]

    async def close(self):
        """Clean up connections"""
        if self._redis:
            await self._redis.close()
        if self._pg_pool:
            await self._pg_pool.close()
```

---

## 4. RAG Implementation

### 4.1 Knowledge Retriever

```python
# src/rag/knowledge_retriever.py
from typing import Any, Dict, List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredPowerPointLoader
)
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import os

class KnowledgeRetriever:
    """
    RAG-based knowledge retrieval system for educational content.
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma",
        embedding_model: str = "text-embedding-ada-002"
    ):
        self.persist_directory = persist_directory
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self._vectorstore = None

    def _get_vectorstore(self, collection_name: str = "educational_content") -> Chroma:
        """Get or create vectorstore"""
        if self._vectorstore is None:
            self._vectorstore = Chroma(
                collection_name=collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_directory
            )
        return self._vectorstore

    async def ingest_document(
        self,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Ingest a document into the knowledge base.

        Returns: Number of chunks created
        """
        # Select appropriate loader
        ext = os.path.splitext(file_path)[1].lower()
        loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': TextLoader,
            '.pptx': UnstructuredPowerPointLoader
        }

        loader_class = loaders.get(ext)
        if not loader_class:
            raise ValueError(f"Unsupported file type: {ext}")

        # Load document
        loader = loader_class(file_path)
        documents = loader.load()

        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Add metadata to each chunk
        for chunk in chunks:
            chunk.metadata.update(metadata)

        # Add to vectorstore
        vectorstore = self._get_vectorstore()
        vectorstore.add_documents(chunks)

        return len(chunks)

    async def retrieve(
        self,
        query: str,
        subject: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Retrieve relevant knowledge for a query.

        Returns:
            Dict with 'context' (combined text) and 'sources' (metadata)
        """
        vectorstore = self._get_vectorstore()

        # Build filter
        where_filter = {}
        if subject:
            where_filter["subject"] = subject
        if filters:
            where_filter.update(filters)

        # Perform similarity search
        if where_filter:
            docs = vectorstore.similarity_search(
                query,
                k=k,
                filter=where_filter
            )
        else:
            docs = vectorstore.similarity_search(query, k=k)

        # Combine results
        context_parts = []
        sources = []

        for doc in docs:
            context_parts.append(doc.page_content)
            sources.append({
                "content_preview": doc.page_content[:200] + "...",
                "metadata": doc.metadata
            })

        return {
            "context": "\n\n---\n\n".join(context_parts),
            "sources": sources,
            "num_results": len(docs)
        }

    async def hybrid_search(
        self,
        query: str,
        subject: Optional[str] = None,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining semantic and keyword search.
        """
        vectorstore = self._get_vectorstore()

        # Semantic search
        semantic_docs = vectorstore.similarity_search_with_score(query, k=k)

        # Keyword search (using BM25 or similar)
        # This would require additional setup with a keyword index

        # For now, just return semantic results
        # In production, you'd combine and re-rank results

        context_parts = []
        sources = []

        for doc, score in semantic_docs:
            context_parts.append(doc.page_content)
            sources.append({
                "content_preview": doc.page_content[:200] + "...",
                "metadata": doc.metadata,
                "relevance_score": float(score)
            })

        return {
            "context": "\n\n---\n\n".join(context_parts),
            "sources": sources,
            "num_results": len(semantic_docs)
        }

    async def delete_by_source(self, source_id: str):
        """Delete all chunks from a specific source"""
        vectorstore = self._get_vectorstore()
        # Implementation depends on ChromaDB version
        # vectorstore.delete(where={"source_id": source_id})
```

---

## 5. API Implementation

### 5.1 FastAPI Application

```python
# src/api/main.py
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager
from typing import Optional
import uvicorn

from src.api.routers import chat, assessments, content, voice, analytics
from src.api.dependencies import get_current_user, get_memory_manager
from src.orchestrator import MasterOrchestrator
from src.memory.memory_manager import MemoryManager
from src.config import settings

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.memory_manager = MemoryManager(
        redis_url=settings.REDIS_URL,
        postgres_url=settings.DATABASE_URL,
        chroma_host=settings.CHROMA_HOST
    )
    await app.state.memory_manager.initialize()

    app.state.orchestrator = MasterOrchestrator(
        memory_manager=app.state.memory_manager
    )
    await app.state.orchestrator.initialize()

    yield

    # Shutdown
    await app.state.memory_manager.close()
    await app.state.orchestrator.close()

# Create FastAPI app
app = FastAPI(
    title="EduAGI API",
    description="Self-Learning Educational AI Agent API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(assessments.router, prefix="/api/v1/assessments", tags=["Assessments"])
app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

# WebSocket endpoint for real-time chat
@app.websocket("/api/v1/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    await websocket.accept()

    orchestrator: MasterOrchestrator = app.state.orchestrator
    memory: MemoryManager = app.state.memory_manager

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Get session context
            context = await memory.get_session_context(session_id)
            if not context:
                await websocket.send_json({"error": "Invalid session"})
                continue

            # Process message
            message_type = data.get("type", "text")
            content = data.get("content", "")

            if message_type == "text":
                # Stream response
                await websocket.send_json({"type": "response_start"})

                async for chunk in orchestrator.process_stream(content, context):
                    await websocket.send_json({
                        "type": "response_chunk",
                        "content": chunk
                    })

                await websocket.send_json({"type": "response_end"})

            elif message_type == "voice_start":
                # Handle voice input start
                pass

            elif message_type == "voice_chunk":
                # Handle voice input chunk
                pass

    except WebSocketDisconnect:
        # Clean up session
        pass

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

### 5.2 Chat Router

```python
# src/api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from src.api.dependencies import get_current_user, get_orchestrator, get_memory
from src.orchestrator import MasterOrchestrator
from src.memory.memory_manager import MemoryManager

router = APIRouter()

class MessageRequest(BaseModel):
    content: str
    session_id: str
    include_voice: bool = False
    include_avatar: bool = False
    include_sign_language: bool = False

class MessageResponse(BaseModel):
    text: str
    audio_url: Optional[str] = None
    avatar_video_url: Optional[str] = None
    sign_language_video_url: Optional[str] = None
    sources: List[dict] = []
    suggested_actions: List[str] = []

class SessionCreateRequest(BaseModel):
    subject: Optional[str] = None
    topic: Optional[str] = None
    mode: str = "tutoring"  # tutoring, assessment, review

class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    mode: str

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: dict = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory)
):
    """Create a new tutoring session"""
    import uuid

    session_id = str(uuid.uuid4())

    # Initialize session context
    context = {
        "student_id": current_user["id"],
        "student_profile": current_user.get("profile", {}),
        "current_subject": request.subject,
        "current_topic": request.topic,
        "mode": request.mode,
        "conversation_history": [],
        "learning_objectives": []
    }

    await memory.set_session_context(session_id, context)

    return SessionResponse(
        session_id=session_id,
        created_at=datetime.utcnow(),
        mode=request.mode
    )

@router.post("/message", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(get_current_user),
    orchestrator: MasterOrchestrator = Depends(get_orchestrator),
    memory: MemoryManager = Depends(get_memory)
):
    """Send a message to the AI tutor"""

    # Get session context
    context = await memory.get_session_context(request.session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify session belongs to user
    if context["student_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update context with multi-modal preferences
    context["student_profile"]["voice_enabled"] = request.include_voice
    context["student_profile"]["avatar_enabled"] = request.include_avatar

    # Process message through orchestrator
    response = await orchestrator.process(request.content, context)

    # Save to conversation history
    await memory.add_to_conversation(request.session_id, "user", request.content)
    await memory.add_to_conversation(request.session_id, "assistant", response.text)

    # Build response
    result = MessageResponse(
        text=response.text,
        sources=response.metadata.get("knowledge_sources", []),
        suggested_actions=response.suggested_actions
    )

    # Add multi-modal content if requested
    if request.include_voice and response.metadata.get("audio_url"):
        result.audio_url = response.metadata["audio_url"]

    if request.include_avatar and response.metadata.get("avatar_video_url"):
        result.avatar_video_url = response.metadata["avatar_video_url"]

    if request.include_sign_language and response.metadata.get("sign_video_url"):
        result.sign_language_video_url = response.metadata["sign_video_url"]

    return result

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    memory: MemoryManager = Depends(get_memory)
):
    """Get conversation history for a session"""

    context = await memory.get_session_context(session_id)
    if not context or context["student_id"] != current_user["id"]:
        raise HTTPException(status_code=404, detail="Session not found")

    history = await memory.get_conversation_history(session_id, limit)

    return {"messages": history}
```

---

## 6. Configuration

### 6.1 Settings Management

```python
# src/config.py
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    APP_NAME: str = "EduAGI"
    DEBUG: bool = False
    SECRET_KEY: str

    # Database
    DATABASE_URL: str
    REDIS_URL: str
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # AI/LLM
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str  # For embeddings
    DEFAULT_MODEL: str = "claude-3-opus-20240229"

    # External Services
    ELEVENLABS_API_KEY: str
    DEEPBRAIN_API_KEY: str = ""
    SIGN_SPEAK_API_KEY: str = ""

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Storage
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    LLM_CALLS_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### 6.2 Environment Variables

```bash
# .env.example

# Application
APP_NAME=EduAGI
DEBUG=false
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/eduagi
REDIS_URL=redis://localhost:6379/0
CHROMA_HOST=localhost
CHROMA_PORT=8000

# AI/LLM APIs
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Voice & Avatar
ELEVENLABS_API_KEY=xxx
DEEPBRAIN_API_KEY=xxx
SIGN_SPEAK_API_KEY=xxx

# Security
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]

# Storage (optional)
S3_BUCKET=eduagi-assets
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

---

## 7. Database Schema

### 7.1 PostgreSQL Schema

```sql
-- migrations/001_initial_schema.sql

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'student',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Student profiles
CREATE TABLE student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    learning_style VARCHAR(50) DEFAULT 'balanced',
    pace VARCHAR(50) DEFAULT 'moderate',
    grade_level VARCHAR(50),
    strengths TEXT[],
    weaknesses TEXT[],
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Learning events (episodic memory)
CREATE TABLE learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    subject VARCHAR(100),
    topic VARCHAR(255),
    data JSONB,
    outcome VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learning_events_student ON learning_events(student_id);
CREATE INDEX idx_learning_events_subject ON learning_events(subject);
CREATE INDEX idx_learning_events_created ON learning_events(created_at);

-- Sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    mode VARCHAR(50) DEFAULT 'tutoring',
    subject VARCHAR(100),
    topic VARCHAR(255),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Assessments
CREATE TABLE assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    due_at TIMESTAMP
);

-- Questions
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    options JSONB,
    correct_answer TEXT,
    rubric TEXT,
    points INTEGER DEFAULT 10,
    difficulty VARCHAR(20) DEFAULT 'medium',
    order_num INTEGER
);

-- Submissions
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES assessments(id) ON DELETE CASCADE,
    student_id UUID REFERENCES users(id) ON DELETE CASCADE,
    answers JSONB NOT NULL,
    submitted_at TIMESTAMP DEFAULT NOW(),
    graded_at TIMESTAMP,
    total_score DECIMAL(10,2),
    max_score DECIMAL(10,2),
    feedback TEXT
);

-- Question grades
CREATE TABLE question_grades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    score DECIMAL(10,2),
    feedback TEXT,
    graded_by VARCHAR(50) DEFAULT 'ai'
);

-- Content/Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100),
    grade_level VARCHAR(50),
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 8. Testing Strategy

### 8.1 Test Structure

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from src.api.main import app
from src.memory.memory_manager import MemoryManager

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def mock_memory_manager():
    # Create mock memory manager for testing
    from unittest.mock import AsyncMock, MagicMock

    mock = MagicMock(spec=MemoryManager)
    mock.get_session_context = AsyncMock(return_value={
        "student_id": "test-user",
        "student_profile": {"learning_style": "visual"},
        "conversation_history": []
    })
    mock.add_to_conversation = AsyncMock()
    mock.get_conversation_history = AsyncMock(return_value=[])

    return mock

# tests/test_tutor_agent.py
import pytest
from src.agents.tutor_agent import TutorAgent
from src.agents.base import AgentContext

class TestTutorAgent:
    @pytest.fixture
    def tutor_agent(self):
        return TutorAgent()

    @pytest.fixture
    def sample_context(self):
        return AgentContext(
            session_id="test-session",
            student_id="test-student",
            student_profile={
                "name": "Test Student",
                "learning_style": "visual",
                "pace": "moderate",
                "grade_level": "high_school"
            },
            conversation_history=[],
            current_subject="Mathematics",
            current_topic="Algebra"
        )

    @pytest.mark.asyncio
    async def test_process_simple_question(self, tutor_agent, sample_context):
        response = await tutor_agent.process(
            "What is a quadratic equation?",
            sample_context
        )

        assert response.text is not None
        assert len(response.text) > 0
        assert "quadratic" in response.text.lower()

    @pytest.mark.asyncio
    async def test_socratic_response(self, tutor_agent, sample_context):
        response = await tutor_agent.process(
            "Just tell me the answer to x^2 + 5x + 6 = 0",
            sample_context
        )

        # Should guide rather than give direct answer
        assert "?" in response.text  # Contains guiding question
```

---

*Document Version History*
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Feb 2026 | AGI Team | Initial technical design |
