# EduAGI - Self-Learning Educational AI Agent

A comprehensive, self-learning artificial general intelligence (AGI) agent designed for educational purposes. EduAGI serves as both an intelligent tutor and sign language assistant, capable of teaching any subject to students of varying abilities.

## Vision

*"To create an accessible, personalized learning experience for every student, regardless of their learning style, language, or ability."*

## Key Features

- **Adaptive Tutoring**: AI-driven system that adapts content difficulty, pace, and teaching style
- **Multi-Subject Knowledge**: Comprehensive knowledge across all academic subjects via RAG
- **Voice Synthesis**: Natural voice output using ElevenLabs integration
- **Avatar Presentation**: Visual avatar for content explanation (DeepBrain/HeyGen)
- **Sign Language Support**: Full ASL/BSL translation for deaf/hard-of-hearing students
- **Automated Assessment**: Generate quizzes, grade assignments, provide detailed feedback
- **Memory System**: Long-term memory of student interactions and progress
- **Self-Learning**: Continuously improves teaching methods from outcomes

## Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](docs/PRD.md) | Product Requirements Document |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System Architecture Design |
| [TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md) | Technical Implementation Details |
| [IMPLEMENTATION_ROADMAP.md](docs/IMPLEMENTATION_ROADMAP.md) | 12-Month Implementation Plan |

## Project Structure

```
agi-education-agent/
├── docs/                    # Documentation
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── TECHNICAL_DESIGN.md
│   └── IMPLEMENTATION_ROADMAP.md
├── src/
│   ├── agents/              # AI Agent implementations
│   ├── memory/              # Memory system (working, episodic, semantic)
│   ├── tools/               # Agent tools and utilities
│   ├── avatars/             # Avatar generation
│   ├── voice/               # Voice synthesis (ElevenLabs)
│   ├── sign_language/       # Sign language translation
│   ├── assessment/          # Grading and quiz generation
│   └── core/                # Core utilities
├── tests/                   # Test suite
├── config/                  # Configuration files
└── data/                    # Data storage
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11+) |
| LLM | Claude (Anthropic) |
| Agent Framework | LangChain, LangGraph |
| Vector DB | ChromaDB |
| Database | PostgreSQL |
| Cache | Redis |
| Voice | ElevenLabs API |
| Avatar | DeepBrain AI / HeyGen |
| Sign Language | Sign-Speak API |

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/agi-education-agent.git
cd agi-education-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn src.api.main:app --reload
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-xxx      # Required: Claude API key
OPENAI_API_KEY=sk-xxx             # Required: For embeddings
ELEVENLABS_API_KEY=xxx            # Required: Voice synthesis
DATABASE_URL=postgresql://...      # Required: PostgreSQL connection
REDIS_URL=redis://localhost:6379   # Required: Redis connection
```

## Roadmap

- **Phase 1** (Months 1-2): Foundation - Core agents, memory system
- **Phase 2** (Months 2-3): Voice & Avatar integration
- **Phase 3** (Months 3-4): Sign language support
- **Phase 4** (Months 4-5): Assessment system
- **Phase 5** (Months 5-6): MVP Launch
- **Phase 6** (Months 7-12): Mobile apps, LMS integrations, scale

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

- Project Lead: TBD
- Email: TBD
