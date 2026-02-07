# F07/F08: Enhanced Session Management & Auth Hardening

## Overview
Implement enhanced session management (F07) and auth system hardening (F08) for the EduAGI platform.

## F07 — Enhanced Session Management

### New Files
- `src/api/routers/sessions.py` — Session CRUD endpoints (list, get, end, resume)

### Enhanced Files
- `src/models/session.py` — Add: summary, is_archived, message_count, device_info columns

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /sessions | List user sessions (active + archived) |
| GET | /sessions/{id} | Get session details |
| POST | /sessions/{id}/end | End session, generate summary, archive |
| POST | /sessions/{id}/resume | Resume archived session |

## F08 — Auth Hardening

### New Files
- `src/auth/rbac.py` — Role-based access control with Role enum + hierarchy
- `src/models/refresh_token.py` — RefreshToken SQLAlchemy model
- `src/api/middleware/__init__.py` — Package init
- `src/api/middleware/rate_limit.py` — Redis sliding-window rate limiter
- `src/api/middleware/request_id.py` — X-Request-ID middleware

### Enhanced Files
- `src/auth/security.py` — Add: hash_token, create_guest_token, check_account_lockout, record_failed_login, clear_failed_logins
- `src/auth/schemas.py` — Add: GuestTokenResponse, PasswordChangeRequest, UserDetailResponse
- `src/api/routers/auth.py` — Add: /guest, /logout, /change-password, /me endpoints + lockout logic in /login
- `src/models/user.py` — Add: last_login, login_count columns
- `src/api/main.py` — Register sessions router + request_id middleware

### Migration
- `migrations/versions/005_session_auth_tables.py` (revision=005, down=004)
  - Create refresh_tokens table
  - Add columns to sessions: summary, is_archived, message_count, device_info
  - Add columns to users: last_login, login_count

### Security Mechanisms
- **RBAC**: Role enum (student, teacher, parent, admin) with hierarchy; admin bypasses all
- **Refresh tokens**: SHA-256 hashed storage (not bcrypt)
- **Rate limiting**: Redis ZADD + ZRANGEBYSCORE sliding window
- **Account lockout**: 5 failed attempts -> 15-min lockout via Redis
- **Guest tokens**: 1-hour JWT, role=guest, no DB user
- **Request IDs**: UUID per request for tracing

## Tests (tests/test_session_auth.py)
10+ tests covering RBAC, guest tokens, hash_token, rate limiting, password schema, lockout, session archival.
All tests mock Redis/DB — no external dependencies needed.
