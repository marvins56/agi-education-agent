# EduAGI Demo Guide

## Prerequisites

- **Docker services**: PostgreSQL (5433), Redis (6380), ChromaDB (8100)
- **Backend**: FastAPI on port 8000
- **Frontend**: Next.js on port 3000 (optional for API-only demo)
- **Ollama** with `qwen2.5:3b` model (required for chat/tutoring only)

## Quick Start

```bash
# 1. Start Docker services
docker compose up -d

# 2. Activate virtualenv and run migrations
cd ~/projects/agi-education-agent
source .venv/bin/activate
alembic upgrade head

# 3. Seed data
python scripts/seed_users.py      # Creates student/teacher/admin users
python scripts/seed_curriculum.py  # Seeds Mathematics curriculum (63 topics)

# 4. Start the backend
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 5. Run the demo flow
bash scripts/demo_flow.sh
```

## Seeded Users

| Email | Password | Role |
|-------|----------|------|
| student@eduagi.com | student123! | student |
| teacher@eduagi.com | teacher123! | teacher |
| admin@eduagi.com | admin123! | admin |

## API Endpoints

### Auth (`/api/v1/auth`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/auth/register` | Register new user | ✅ Working |
| POST | `/auth/login` | Login, get JWT | ✅ Working |
| GET | `/auth/me` | Current user info | ✅ Working |

### Profile (`/api/v1`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/profile` | Student profile | ✅ Working |

### Chat / Tutoring (`/api/v1/chat`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/chat/sessions` | Create tutoring session | ✅ Working |
| POST | `/chat/message` | Send message to AI tutor | ⚠️ Requires Ollama |
| GET | `/chat/history/{session_id}` | Get conversation history | ✅ Working |

### Sessions (`/api/v1`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/sessions` | List user sessions | ✅ Working |

### Assessments (`/api/v1/assessments`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/assessments` | Create assessment (teacher+) | ✅ Working |
| GET | `/assessments` | List own assessments | ✅ Working |
| GET | `/assessments/{id}` | Get assessment details | ✅ Working |

### Learning Path (`/api/v1`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/learning-path/graph/{subject}` | Prerequisite graph | ✅ Working (63 topics for Math) |
| GET | `/learning-path/recommended` | Personalized recommendations | ✅ Working |

### Adaptive Learning (`/api/v1/adaptive`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/adaptive/knowledge-state` | Student knowledge model | ✅ Working |
| GET | `/adaptive/learning-style` | Learning style profile | ✅ Working |
| GET | `/adaptive/spaced-repetition/due` | Due review items | ✅ Working |
| POST | `/adaptive/interactions` | Record learning interaction | ✅ Working |
| POST | `/adaptive/recommendations` | Get adaptive recommendations | ✅ Working |

### Analytics (`/api/v1/analytics`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/analytics/student/summary` | Dashboard summary | ✅ Working |
| GET | `/analytics/student/mastery` | Mastery by subject | ✅ Working |

### Content (`/api/v1/content`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| POST | `/content/upload` | Upload documents | ✅ Working (teacher+) |
| GET | `/content/documents` | List documents | ✅ Working |
| POST | `/content/search` | RAG search | ✅ Working |

### Models (`/api/v1`)
| Method | Path | Description | Status |
|--------|------|-------------|--------|
| GET | `/models` | Available LLM providers | ✅ Working |

## Bugs Fixed

1. **Analytics timezone mismatch** (`src/analytics/aggregator.py`): `datetime.now(timezone.utc)` produced timezone-aware datetime compared against naive DB column. Fixed by using `datetime.utcnow()`.

2. **Adaptive engine dependency injection** (`src/api/routers/adaptive.py`): `MemoryManager()` was called without required `redis_url` arg. Fixed to use `Depends(get_memory)`.

3. **Adaptive endpoints user type mismatch** (`src/api/routers/adaptive.py`): `current_student["id"]` treated User ORM object as dict. Fixed to `str(current_student.id)`.

## Known Limitations

- **Chat/tutoring requires Ollama**: The `/chat/message` endpoint needs a running Ollama instance with `qwen2.5:3b`. Without it, you get 500 errors.
- **No subject/topic browsing endpoint**: There's no dedicated `GET /subjects` or `GET /topics` endpoint. Curriculum data is accessed via the learning path graph (`/learning-path/graph/{subject}`).
- **Assessment listing is creator-scoped**: `GET /assessments` only returns assessments created by the authenticated user. Students need a separate endpoint to see assigned assessments.

## Demo Flow

Run the automated demo: `bash scripts/demo_flow.sh`

This walks through: health check → register → login → profile → curriculum graph → create session → chat → assessments → adaptive learning → analytics → models → learning path.
