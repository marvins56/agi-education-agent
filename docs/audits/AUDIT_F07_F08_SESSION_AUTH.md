# Security Audit Report: F07/F08 Session Management + Auth Hardening

**Audit Date**: 2026-02-07
**Auditor**: Security Auditor Agent (DevSecOps)
**Severity Scale**: CRITICAL / HIGH / MEDIUM / LOW / INFO

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Execution Flow Analysis](#3-execution-flow-analysis)
4. [Integration Points](#4-integration-points)
5. [Security Deep-Dive](#5-security-deep-dive)
6. [Data Models](#6-data-models)
7. [Code Quality Issues](#7-code-quality-issues)
8. [Test Coverage Analysis](#8-test-coverage-analysis)
9. [Findings Summary Table](#9-findings-summary-table)
10. [Recommendations](#10-recommendations)

---

## 1. Executive Summary

The F07/F08 feature implements session management and auth hardening for the EduAGI platform. The implementation includes JWT-based authentication, RBAC, guest sessions, account lockout, rate limiting, and session CRUD. While the foundational pieces exist, this audit identified **7 CRITICAL**, **8 HIGH**, and several MEDIUM/LOW issues. The most severe problems are:

- Account lockout logic exists but is **never invoked** in the login endpoint.
- Refresh tokens are modeled in the database but **never persisted or validated** against DB records.
- Rate limiting middleware is defined but **never registered** in the application.
- The logout endpoint performs **no server-side token invalidation**.
- Access tokens and refresh tokens use the **same signing key** with no audience/issuer claims.
- The `get_current_user` dependency does **not check token type**, allowing refresh tokens to be used as access tokens.
- Default JWT secret is a hardcoded string `"change-me-jwt"`.

---

## 2. Architecture Overview

### 2.1 Auth Flow

```
Client --> POST /api/v1/auth/register  --> Create User + StudentProfile
Client --> POST /api/v1/auth/login     --> Verify password, return JWT access + refresh
Client --> POST /api/v1/auth/refresh   --> Verify refresh JWT, issue new token pair
Client --> POST /api/v1/auth/guest     --> Issue short-lived guest JWT (1hr, role=guest)
Client --> POST /api/v1/auth/logout    --> No-op (client discards token)
Client --> POST /api/v1/auth/change-password --> Verify old password, hash new
Client --> GET  /api/v1/auth/me        --> Return current user details
```

### 2.2 RBAC Hierarchy

Defined in `src/auth/rbac.py:18-23`:

```
admin  --> can access: {admin, teacher, parent, student}
teacher -> can access: {teacher}
parent  -> can access: {parent}
student -> can access: {student}
```

The `guest` role is NOT part of the RBAC `Role` enum. Guest tokens carry `role=guest` in the JWT but this role is not recognized by `require_role()`.

### 2.3 Session Lifecycle

```
Session created (externally, e.g. by chat router)
  --> GET /sessions (list user's sessions)
  --> GET /sessions/{id} (get specific session)
  --> POST /sessions/{id}/end (set ended_at, generate summary, archive)
  --> POST /sessions/{id}/resume (clear ended_at, unarchive)
```

### 2.4 Rate Limiting

- Sliding window algorithm using Redis sorted sets (`ZADD` + `ZRANGEBYSCORE`)
- Configurable limit and window (default: 60 requests / 60 seconds)
- Key based on user ID (if available from `request.state.user_id`) or client IP

### 2.5 Files Audited

| File | Lines | Purpose |
|------|-------|---------|
| `src/auth/security.py` | 91 | Password hashing, JWT creation/verification, lockout, guest tokens |
| `src/auth/schemas.py` | 55 | Pydantic v2 request/response schemas |
| `src/auth/rbac.py` | 42 | Role enum, hierarchy, `require_role` dependency |
| `src/auth/guest.py` | 54 | GuestSession dataclass with message limits |
| `src/models/user.py` | 48 | User + StudentProfile SQLAlchemy models |
| `src/models/refresh_token.py` | 22 | RefreshToken SQLAlchemy model |
| `src/models/session.py` | 25 | Session SQLAlchemy model |
| `src/api/routers/auth.py` | 149 | Auth endpoints |
| `src/api/routers/sessions.py` | 208 | Session CRUD endpoints |
| `src/api/middleware/rate_limit.py` | 102 | RateLimiter + RateLimitMiddleware |
| `src/api/middleware/request_id.py` | 20 | Request ID middleware |
| `src/api/dependencies.py` | 75 | `get_current_user`, `get_db` |
| `src/api/main.py` | 80 | App factory, middleware + router registration |
| `src/config.py` | 38 | Application settings |
| `migrations/versions/005_session_auth_tables.py` | 59 | Migration for new tables/columns |
| `tests/test_session_auth.py` | 303 | Unit tests |
| `tests/test_rbac.py` | 92 | RBAC tests |
| `tests/test_rate_limit.py` | 103 | Rate limit tests |
| `tests/test_session_enhanced.py` | 199 | Enhanced session tests |

---

## 3. Execution Flow Analysis

### 3.1 Registration Flow

**Path**: `POST /api/v1/auth/register` -> `src/api/routers/auth.py:32-59`

1. Pydantic validates `RegisterRequest` (email: `EmailStr`, password: `min_length=8`, name: str)
2. Query checks for duplicate email (`SELECT ... WHERE email = :email`)
3. Password hashed via `bcrypt.hashpw()` with generated salt
4. `User` record created with default `role="student"`, `is_active=True`
5. `StudentProfile` record created linked to user
6. `db.flush()` called (not `commit` -- commit happens in `get_db` dependency on success)
7. Returns `UserResponse` (id, email, name, role, created_at)

**Issues identified**:
- [F-01] No email verification required; `is_verified` defaults to `False` but is never checked
- [F-02] No password complexity validation beyond 8-char minimum
- [F-03] Role is hardcoded to `"student"` -- no admin registration path, which is fine for security but undocumented

### 3.2 Login Flow

**Path**: `POST /api/v1/auth/login` -> `src/api/routers/auth.py:62-77`

1. Pydantic validates `LoginRequest` (email: `EmailStr`, password: str)
2. Query for user by email
3. If user not found OR password mismatch, return 401
4. Create access token (60 min default) and refresh token (7 days)
5. JWT payload: `{"sub": user_id, "email": email, "role": role, "exp": ..., "type": "access"|"refresh"}`
6. Return `TokenResponse` with both tokens

**CRITICAL issues identified**:
- [F-04] Account lockout functions (`check_account_lockout`, `record_failed_login`, `clear_failed_logins`) are defined in `src/auth/security.py:64-90` but **NEVER CALLED** from the login endpoint. The login endpoint at `src/api/routers/auth.py:62-77` has no lockout checks whatsoever. An attacker can brute-force passwords without any rate limit or lockout.
- [F-05] `last_login` and `login_count` fields exist on the User model (`src/models/user.py:22-23`) but are **never updated** on login. These tracking fields are dead code.
- [F-06] No check for `user.is_active` during login. A disabled account can still authenticate.

### 3.3 Authenticated Request Flow

**Path**: Any endpoint with `Depends(get_current_user)` -> `src/api/dependencies.py:46-74`

1. `OAuth2PasswordBearer` extracts Bearer token from `Authorization` header
2. `verify_token()` decodes JWT using `settings.JWT_SECRET` with `HS256`
3. Extract `sub` (user_id) from payload
4. Query `User` by `id`
5. Check `user.is_active` -- return 403 if disabled
6. Return user object

**CRITICAL issues identified**:
- [F-07] **Token type not validated**: `get_current_user` at `src/api/dependencies.py:46-74` calls `verify_token()` but never checks `payload["type"]`. A refresh token (type="refresh") can be used as an access token. This defeats the purpose of short-lived access tokens -- an attacker with a stolen refresh token gets 7 days of access instead of 60 minutes.
- [F-08] **No token revocation check**: Even though `RefreshToken` model has `is_revoked` field, `get_current_user` performs no revocation check. Tokens cannot be invalidated server-side.

### 3.4 Refresh Token Flow

**Path**: `POST /api/v1/auth/refresh` -> `src/api/routers/auth.py:80-98`

1. `verify_token()` decodes the refresh token JWT
2. Check `payload["type"] == "refresh"` (the ONLY place token type is checked)
3. Extract `sub`, `email`, `role` from payload
4. Issue new access token + refresh token pair

**CRITICAL issues identified**:
- [F-09] **No database validation**: The refresh endpoint at `src/api/routers/auth.py:80-98` never queries the `refresh_tokens` table. It does not check if the token hash exists, is revoked, or has been used before. The `RefreshToken` model (`src/models/refresh_token.py`) is completely unused.
- [F-10] **No refresh token rotation**: Old refresh tokens remain valid after a new pair is issued. If a refresh token is stolen, the attacker can continue generating new tokens indefinitely, even after the legitimate user refreshes.
- [F-11] **Role escalation via stale JWT claims**: The refresh endpoint reads `role` from the old JWT payload (`src/api/routers/auth.py:93`) rather than from the database. If a user's role is downgraded (e.g., admin removes teacher privileges), the old refresh token retains the elevated role and continues issuing tokens with it.

### 3.5 Guest Session Flow

**Path**: `POST /api/v1/auth/guest` -> `src/api/routers/auth.py:101-108`

1. `create_guest_token()` generates a JWT with `sub=guest-{uuid}`, `role=guest`, `exp=1hr`
2. Returns token to client

**Issues identified**:
- [F-12] The `GuestSession` class (`src/auth/guest.py`) with its 5-message limit is **never used** by the guest endpoint. The endpoint at `src/api/routers/auth.py:101-108` calls `create_guest_token()` directly, bypassing the `GuestSession` class entirely. Message limits are not enforced.
- [F-13] Guest tokens have `role=guest` but the RBAC `Role` enum at `src/auth/rbac.py:11-15` does not include `guest`. If a guest token is presented to `get_current_user`, the DB query `User.id == "guest-{uuid}"` will fail (no such user), resulting in a 401. This means guest tokens cannot actually be used with any authenticated endpoint.
- [F-14] No rate limiting on guest token creation -- an attacker can generate unlimited guest tokens.

### 3.6 Logout Flow

**Path**: `POST /api/v1/auth/logout` -> `src/api/routers/auth.py:111-116`

1. Requires authenticated user via `get_current_user`
2. Returns `204 No Content`
3. Comment says "token revocation handled client-side or via Redis blacklist"

**CRITICAL issue**:
- [F-15] **Logout is a no-op**: The endpoint at `src/api/routers/auth.py:111-116` does nothing server-side. The access token remains valid until expiry (60 min). The refresh token remains valid for 7 days. There is no Redis blacklist implementation despite the comment suggesting one. A compromised token cannot be invalidated.

### 3.7 Password Change Flow

**Path**: `POST /api/v1/auth/change-password` -> `src/api/routers/auth.py:119-134`

1. Requires authenticated user
2. Verifies old password
3. Hashes and sets new password
4. Returns success message

**Issues identified**:
- [F-16] After password change, all existing tokens (access + refresh) remain valid. There is no mechanism to invalidate prior sessions.
- [F-17] No notification to the user (e.g., email) that their password was changed. If an attacker changes the password using a stolen token, the legitimate user has no way to know.

---

## 4. Integration Points

### 4.1 Auth Dependencies Used Across Routers

`get_current_user` (from `src/api/dependencies.py`) is the central auth dependency used by every protected router:

| Router | File | Protected Endpoints |
|--------|------|-------------------|
| auth | `src/api/routers/auth.py` | logout, change-password, me |
| sessions | `src/api/routers/sessions.py` | list, get, end, resume |
| chat | `src/api/routers/chat.py` | send message, get history, clear |
| content | `src/api/routers/content.py` | upload, search, list, get, delete |
| profile | `src/api/routers/profile.py` | get, update, stats, strengths, preferences, streak |
| assessments | `src/api/routers/assessments.py` | generate, get, submit, list, stats, grade, create, bulk |
| analytics | `src/api/routers/analytics.py` | student stats, learning trends, engagement, study time, class overview, student list, alerts |
| learning_path | `src/api/routers/learning_path.py` | paths, progress, recommendations, overdue, complete |

### 4.2 RBAC Usage

Only `src/api/routers/analytics.py` uses `require_role`:
- `GET /class-overview` -> `require_role(Role.teacher, Role.admin)` (line 74)
- `GET /students` -> `require_role(Role.teacher, Role.admin)` (line 85)
- `GET /alerts` -> `require_role(Role.teacher, Role.admin)` (line 96)

**Issue**: [F-18] All other routers (assessments, content, learning_path, chat, profile, sessions) rely solely on `get_current_user` with no role checks. Any authenticated user (student, teacher, parent, admin) can access all endpoints equally. For example, a student can access assessment generation/grading endpoints that may be teacher-only operations.

### 4.3 Session Ownership

Session endpoints at `src/api/routers/sessions.py` properly filter by `Session.student_id == current_user.id`, enforcing that users can only see/manage their own sessions. This is correctly implemented.

---

## 5. Security Deep-Dive

### 5.1 JWT Implementation

**File**: `src/auth/security.py:22-47`, `src/config.py:27-29`

| Aspect | Implementation | Assessment |
|--------|---------------|------------|
| Algorithm | HS256 | MEDIUM RISK - Symmetric key; consider RS256 for multi-service |
| Secret | `"change-me-jwt"` default | **CRITICAL** [F-19] - Hardcoded default secret. If `.env` is missing, tokens are signed with a predictable key |
| Access TTL | 60 minutes | Acceptable but on the long side for a security-sensitive app |
| Refresh TTL | 7 days (hardcoded) | Not configurable via settings |
| Claims | sub, email, role, exp, type | Missing: `iss`, `aud`, `iat`, `jti` |
| Key rotation | None | No mechanism for key rotation |

**Specific findings**:

- [F-19] **CRITICAL - Default JWT secret**: `src/config.py:27` sets `JWT_SECRET: str = "change-me-jwt"`. If the `.env` file is absent or does not override this value, all JWTs are signed with a publicly known key, allowing any attacker to forge valid tokens.
- [F-20] **HIGH - Same key for access and refresh**: Both `create_access_token` (line 22) and `create_refresh_token` (line 31) in `src/auth/security.py` use `settings.JWT_SECRET`. There is no key separation. Combined with [F-07] (no type checking in `get_current_user`), this allows refresh tokens to work as access tokens.
- [F-21] **MEDIUM - No `jti` (JWT ID) claim**: Without a unique token identifier, individual tokens cannot be blacklisted or tracked for revocation.
- [F-22] **MEDIUM - No `iss`/`aud` claims**: No issuer or audience validation. In a multi-service environment, tokens from one service could be accepted by another.
- [F-23] **LOW - Refresh TTL not configurable**: The 7-day refresh TTL at `src/auth/security.py:33` is hardcoded, unlike the access token TTL which uses `settings.ACCESS_TOKEN_EXPIRE_MINUTES`.

### 5.2 Password Hashing

**File**: `src/auth/security.py:14-19`

```python
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
```

- Uses `bcrypt` directly (good -- avoids passlib compatibility issues)
- Default salt rounds (12) is acceptable
- `bcrypt.checkpw` is constant-time internally, mitigating timing attacks on password comparison

**Issue**:
- [F-24] **MEDIUM - No password complexity enforcement**: `RegisterRequest` at `src/auth/schemas.py:10` only enforces `min_length=8`. No requirements for uppercase, lowercase, digits, or special characters. Common passwords like `password` or `12345678` are accepted.

### 5.3 Token Storage

**File**: `src/models/refresh_token.py`, `src/auth/security.py:50-52`

- `hash_token()` uses SHA-256 to hash refresh tokens for storage
- `RefreshToken` model stores: `token_hash`, `user_id`, `device_info`, `is_revoked`, `expires_at`
- Database has indexes on `token_hash` and `user_id`

**CRITICAL issue**:
- [F-25] **The entire RefreshToken model is dead code**. No endpoint creates, queries, or revokes RefreshToken records. The `hash_token()` function is never called outside tests. Refresh tokens are validated purely by JWT signature, with no database persistence or revocation capability.

### 5.4 Account Lockout

**File**: `src/auth/security.py:64-90`

- `check_account_lockout()`: Checks Redis for `lockout:{email}` flag
- `record_failed_login()`: Increments `login_fails:{email}` counter, sets lockout flag after 5 failures
- `clear_failed_logins()`: Deletes both counter and lockout flag
- Lockout TTL: 15 minutes

**CRITICAL issue**:
- [F-04] (repeated) **None of these functions are called from the login endpoint**. The lockout system is fully implemented but completely disconnected from the authentication flow. Brute-force attacks are unrestricted.

### 5.5 Rate Limiting

**File**: `src/api/middleware/rate_limit.py`

The `RateLimiter` and `RateLimitMiddleware` classes are well-implemented:
- Sliding window using Redis sorted sets (ZADD/ZRANGEBYSCORE)
- Proper pipeline usage for atomicity
- Graceful degradation (allows requests if Redis is down)
- Standard rate limit headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`)

**CRITICAL issue**:
- [F-26] **Rate limit middleware is never registered**. `src/api/main.py` registers `RequestIDMiddleware` (line 70) but does NOT register `RateLimitMiddleware`. The rate limiter is dead code. All endpoints are unprotected against abuse.

**Additional concerns**:
- [F-27] **HIGH - Fail-open on Redis failure**: `src/api/middleware/rate_limit.py:84-86` catches all exceptions from Redis and allows the request through. An attacker who can crash or disconnect Redis can bypass rate limiting entirely. While fail-open is sometimes acceptable for availability, this should be configurable and logged.
- [F-28] **MEDIUM - Request state user_id never set**: `src/api/middleware/rate_limit.py:78-79` checks `request.state.user_id` for per-user rate limiting, but no middleware or dependency sets this attribute. Rate limiting would always fall back to IP-based keying, which can be evaded via proxies and is unfair to users behind NAT.

### 5.6 RBAC Enforcement

**File**: `src/auth/rbac.py`

**Issues**:
- [F-29] **HIGH - ROLE_HIERARCHY defined but unused**: The `ROLE_HIERARCHY` dict at `src/auth/rbac.py:18-23` defines role inheritance but `require_role()` at lines 26-41 does not use it. Instead, it hardcodes admin bypass (`if user_role == Role.admin: return`) and then checks `user_role not in allowed_roles`. The hierarchy dict is dead code.
- [F-30] **HIGH - No guest role in enum**: `Role` enum has student/teacher/parent/admin but no `guest`. Guest tokens carry `role=guest` in the JWT. If `require_role()` is called with a guest user, `Role(current_user.role)` at line 30 raises `ValueError` (unhandled), resulting in a 500 Internal Server Error instead of a proper 403.
- [F-18] (repeated) **RBAC is only used in analytics router**. All other routers are unprotected by role checks.

### 5.7 CORS Configuration

**File**: `src/api/main.py:58-64`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [F-31] **MEDIUM - Wildcard methods and headers**: `allow_methods=["*"]` and `allow_headers=["*"]` are overly permissive. Should be restricted to actual methods (GET, POST, PUT, DELETE) and needed headers.
- The default origin `http://localhost:3000` is appropriate for development but must be updated for production.

---

## 6. Data Models

### 6.1 User Model

**File**: `src/models/user.py:11-27`

| Column | Type | Constraints | Status |
|--------|------|-------------|--------|
| id | UUID | PK, gen_random_uuid() | OK |
| email | String(255) | UNIQUE, NOT NULL | OK |
| password_hash | String(255) | NOT NULL | OK |
| name | String(255) | NOT NULL | OK |
| role | String(50) | DEFAULT "student" | No FK constraint, no enum check |
| is_active | Boolean | DEFAULT True | Checked in `get_current_user` |
| created_at | DateTime | server_default now() | OK |
| updated_at | DateTime | server_default now(), onupdate | OK |
| last_login | DateTime | nullable | **NEVER UPDATED** [F-05] |
| login_count | Integer | DEFAULT 0 | **NEVER UPDATED** [F-05] |
| is_verified | Boolean | DEFAULT False | **NEVER CHECKED** [F-01] |

### 6.2 RefreshToken Model

**File**: `src/models/refresh_token.py:10-22`

| Column | Type | Constraints | Status |
|--------|------|-------------|--------|
| id | UUID | PK | OK |
| user_id | UUID | FK users.id CASCADE | OK |
| token_hash | String(255) | NOT NULL | **NEVER POPULATED** [F-25] |
| device_info | String(255) | nullable | Never used |
| is_revoked | Boolean | DEFAULT False | **NEVER CHECKED** [F-25] |
| expires_at | DateTime | NOT NULL | Never used |
| created_at | DateTime | server_default now() | Never used |

**Entire model is dead code.**

### 6.3 Session Model

**File**: `src/models/session.py:10-25`

| Column | Type | Constraints | Status |
|--------|------|-------------|--------|
| id | UUID | PK | OK |
| student_id | UUID | FK users.id CASCADE | Properly filtered in queries |
| mode | String(50) | DEFAULT "tutoring" | OK |
| subject | String(100) | nullable | OK |
| topic | String(255) | nullable | OK |
| started_at | DateTime | server_default now() | OK |
| ended_at | DateTime | nullable | Set on end |
| metadata_ | JSONB | DEFAULT '{}' | OK - aliased to avoid Python keyword |
| summary | Text | nullable | Generated on end |
| is_archived | Boolean | DEFAULT False | Set on end |
| message_count | Integer | DEFAULT 0 | OK |
| device_info | String(255) | nullable | OK |

**Issues**:
- [F-32] **LOW - No pagination on session list**: `src/api/routers/sessions.py:39-69` returns ALL sessions for a user with no limit/offset. For power users with hundreds of sessions, this could be a performance issue or used for resource exhaustion.
- [F-33] **LOW - session_id is a string parameter**: `src/api/routers/sessions.py:73` accepts `session_id: str` with no UUID validation. Invalid UUID strings will cause a database-level error rather than a clean 400/422 response.

---

## 7. Code Quality Issues

### 7.1 Defensive `hasattr` Checks

**File**: `src/api/routers/sessions.py:61-64, 99-102, 160-161, 203-206`

Multiple lines like:
```python
summary=session.summary if hasattr(session, "summary") else None,
is_archived=session.is_archived if hasattr(session, "is_archived") else False,
```

These `hasattr` checks are unnecessary because the `Session` model always has these attributes (they are defined as columns). This suggests the columns were added incrementally and the code was not cleaned up. While not a security issue, it indicates potential lack of code review.

### 7.2 Duplicate `get_db` Definitions

**Files**: `src/api/dependencies.py:20-28` and `src/models/database.py:29-37`

Two identical `get_db` functions exist. `src/api/dependencies.py` imports `async_session` from `database.py` and defines its own `get_db`. The routers import `get_db` from different locations:
- `src/api/routers/auth.py:26` imports from `src.models.database`
- `src/api/routers/sessions.py:10` imports from `src.api.dependencies`

This inconsistency means some routes use one session factory and others use the other. While both are currently identical, this is fragile.

### 7.3 Missing `__init__.py` Audit

`src/auth/__init__.py` exists but was not checked for re-exports. No issues found via glob.

### 7.4 Error Information Leakage

- [F-34] **LOW**: `src/auth/rbac.py:38` includes the user's role in the 403 error message: `f"Role '{current_user.role}' not authorized"`. This reveals the user's role to potential attackers, which could aid in privilege escalation reconnaissance.

---

## 8. Test Coverage Analysis

### 8.1 What Is Tested

| Area | Test File | Tests | Quality |
|------|-----------|-------|---------|
| RBAC role checks | `tests/test_rbac.py` | 7 tests | Good - covers allow/deny for each role, multi-role, invalid role |
| RBAC basics | `tests/test_session_auth.py::TestRBAC` | 4 tests | Redundant with `test_rbac.py` |
| Guest token creation | `tests/test_session_auth.py::TestGuestToken` | 3 tests | Covers creation, payload, schema |
| Guest session class | `tests/test_session_enhanced.py::TestGuestSession` | 5 tests | Good - covers creation, limit, topics, serialization |
| Hash token | Both test files | 3 tests each | Good - consistency, uniqueness, format |
| Rate limiter | `tests/test_rate_limit.py` | 6 tests | Good - allowed, exceeded, custom limit, negative, close |
| Account lockout | Both test files | 4 tests each | Good - lockout trigger, check locked/unlocked, clear |
| Password schema | Both test files | 2 tests each | Good - valid and too-short |
| Session end/archive | Both test files | 1-2 tests each | Basic - mock-based, no endpoint testing |
| UserDetailResponse | Both test files | 1 test each | Basic schema validation |

### 8.2 What Is NOT Tested (Gaps)

**CRITICAL test gaps**:

1. **No endpoint-level (integration) tests**: No tests use `TestClient` or `httpx.AsyncClient` to test actual HTTP endpoints. All tests are unit tests with mocks. This means:
   - The register endpoint is untested
   - The login endpoint is untested
   - The refresh endpoint is untested
   - The logout endpoint is untested
   - The change-password endpoint is untested
   - The /me endpoint is untested
   - Session CRUD endpoints are untested at the HTTP level

2. **No `get_current_user` dependency tests**: The central auth dependency is never tested. No tests verify:
   - That expired tokens are rejected
   - That invalid tokens are rejected
   - That disabled users are blocked
   - That the correct user is returned
   - That token type is (not) validated

3. **No refresh token rotation/revocation tests**: Since the RefreshToken model is unused, there are no tests for it.

4. **No lockout integration test**: The lockout functions are tested in isolation but there is no test proving they are called from the login flow (they are not).

5. **No rate limit middleware integration test**: The `RateLimitMiddleware` class is never tested. Only `RateLimiter` (the core logic) is tested.

6. **No CORS test**: No validation that CORS is correctly configured.

7. **No password change with invalid old password test at endpoint level**: Only schema validation is tested.

8. **No session ownership test**: No test verifies that user A cannot access user B's sessions.

9. **No guest token usage test**: No test verifies what happens when a guest token is used to access protected endpoints.

10. **Significant test duplication**: `test_session_auth.py` and `test_session_enhanced.py` contain nearly identical test classes (TestGuestToken, TestHashToken, TestAccountLockout, etc.).

---

## 9. Findings Summary Table

| ID | Severity | Category | Description | File:Line |
|----|----------|----------|-------------|-----------|
| F-01 | MEDIUM | Auth | `is_verified` never checked; unverified accounts can login | `user.py:24`, `auth.py:62-77` |
| F-02 | MEDIUM | Auth | No password complexity beyond 8-char minimum | `schemas.py:10` |
| F-03 | INFO | Auth | Admin registration path undocumented | `auth.py:41-45` |
| F-04 | **CRITICAL** | Auth | Account lockout functions never called from login | `security.py:70-90`, `auth.py:62-77` |
| F-05 | LOW | Auth | `last_login`, `login_count` never updated | `auth.py:62-77`, `user.py:22-23` |
| F-06 | HIGH | Auth | `is_active` not checked during login | `auth.py:62-77` |
| F-07 | **CRITICAL** | JWT | `get_current_user` does not validate token type | `dependencies.py:46-74` |
| F-08 | HIGH | JWT | No token revocation check in auth dependency | `dependencies.py:46-74` |
| F-09 | **CRITICAL** | JWT | Refresh endpoint does no database validation | `auth.py:80-98` |
| F-10 | HIGH | JWT | No refresh token rotation; old tokens remain valid | `auth.py:80-98` |
| F-11 | HIGH | JWT | Role read from JWT not DB during refresh (stale roles) | `auth.py:90-94` |
| F-12 | MEDIUM | Guest | GuestSession class never used; message limits unenforced | `guest.py`, `auth.py:101-108` |
| F-13 | MEDIUM | Guest | Guest role not in RBAC enum; guest tokens unusable with protected endpoints | `rbac.py:11-15` |
| F-14 | MEDIUM | Guest | No rate limit on guest token creation | `auth.py:101-108` |
| F-15 | **CRITICAL** | Auth | Logout is a no-op; no server-side token invalidation | `auth.py:111-116` |
| F-16 | HIGH | Auth | Password change does not invalidate existing tokens | `auth.py:119-134` |
| F-17 | LOW | Auth | No notification on password change | `auth.py:119-134` |
| F-18 | HIGH | RBAC | RBAC only used in analytics router; all others unprotected | Multiple routers |
| F-19 | **CRITICAL** | Config | Default JWT secret is hardcoded `"change-me-jwt"` | `config.py:27` |
| F-20 | HIGH | JWT | Same signing key for access and refresh tokens | `security.py:22-35` |
| F-21 | MEDIUM | JWT | No `jti` claim for token identification/blacklisting | `security.py:22-35` |
| F-22 | MEDIUM | JWT | No `iss`/`aud` claims for multi-service validation | `security.py:22-35` |
| F-23 | LOW | JWT | Refresh TTL hardcoded to 7 days | `security.py:33` |
| F-24 | MEDIUM | Auth | Weak password policy | `schemas.py:10` |
| F-25 | **CRITICAL** | Data | RefreshToken model is dead code; never persisted or queried | `refresh_token.py`, `auth.py` |
| F-26 | **CRITICAL** | Middleware | Rate limit middleware never registered in app | `main.py` |
| F-27 | HIGH | Middleware | Rate limiter fail-open on Redis failure without logging | `rate_limit.py:84-86` |
| F-28 | MEDIUM | Middleware | `request.state.user_id` never set; always falls back to IP | `rate_limit.py:78-79` |
| F-29 | LOW | RBAC | ROLE_HIERARCHY dict defined but unused | `rbac.py:18-23` |
| F-30 | MEDIUM | RBAC | Guest role causes ValueError (500) in require_role | `rbac.py:30` |
| F-31 | MEDIUM | CORS | Wildcard methods and headers | `main.py:62-63` |
| F-32 | LOW | Sessions | No pagination on session list | `sessions.py:39-69` |
| F-33 | LOW | Sessions | No UUID validation on session_id parameter | `sessions.py:73` |
| F-34 | LOW | Info leak | User role leaked in 403 error message | `rbac.py:38` |

---

## 10. Recommendations

### 10.1 CRITICAL Priority (Must Fix Before Production)

**R-01: Wire up account lockout in login endpoint** [Fixes F-04]
Integrate `check_account_lockout()` and `record_failed_login()` into the login handler at `src/api/routers/auth.py:62-77`. Call `clear_failed_logins()` on successful login. This requires passing a Redis instance to the login endpoint.

**R-02: Validate token type in `get_current_user`** [Fixes F-07]
Add `if payload.get("type") != "access": raise HTTPException(401)` in `src/api/dependencies.py:51` after `verify_token()`. This prevents refresh tokens from being used as access tokens.

**R-03: Implement server-side refresh token storage** [Fixes F-09, F-25]
- On login: create RefreshToken record with `hash_token(refresh_jwt)`, store in DB
- On refresh: look up `token_hash`, verify not revoked, verify not expired
- On refresh: revoke old token, issue new pair (rotation) [Fixes F-10]
- On logout: revoke all user's refresh tokens

**R-04: Implement token blacklisting for logout** [Fixes F-15]
Use Redis with token `jti` and remaining TTL as expiry key. Check blacklist in `get_current_user`. Add `jti` claim to JWTs [also fixes F-21].

**R-05: Register rate limit middleware** [Fixes F-26]
Add to `src/api/main.py`:
```python
from src.api.middleware.rate_limit import RateLimiter, RateLimitMiddleware
rate_limiter = RateLimiter(redis_url=settings.REDIS_URL)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
```

**R-06: Enforce strong JWT secret** [Fixes F-19]
Require `JWT_SECRET` to be set via environment variable with no fallback default. Validate minimum length (32+ characters) at startup. Consider using `secrets.token_urlsafe(32)` to generate.

**R-07: Read role from database during refresh** [Fixes F-11]
In the refresh endpoint, query the User table to get current role rather than trusting the JWT payload.

### 10.2 HIGH Priority

**R-08: Check `is_active` during login** [Fixes F-06]
Add `if not user.is_active: raise HTTPException(403, "Account disabled")` after password verification in the login endpoint.

**R-09: Invalidate tokens on password change** [Fixes F-16]
After password change, revoke all refresh tokens for the user and add current access token to blacklist.

**R-10: Apply RBAC to all routers** [Fixes F-18]
Review each router and apply appropriate `require_role()` dependencies. For example:
- Assessment generation/grading: `require_role(Role.teacher, Role.admin)`
- Student profile: owner-only or `require_role(Role.student)`
- Content upload: `require_role(Role.teacher, Role.admin)`

**R-11: Use separate keys for access/refresh tokens** [Fixes F-20]
Add `JWT_REFRESH_SECRET` setting. Use it for refresh token signing/verification.

**R-12: Add logging for rate limit failures** [Fixes F-27]
Log at WARNING level when Redis is unavailable, including the request path and client IP.

### 10.3 MEDIUM Priority

**R-13: Add password complexity rules** [Fixes F-24, F-02]
Add a Pydantic validator requiring at least one uppercase, one lowercase, one digit, and one special character.

**R-14: Implement email verification flow** [Fixes F-01]
Use `is_verified` field. Send verification email on registration. Block login for unverified accounts (or limit capabilities).

**R-15: Fix guest token architecture** [Fixes F-12, F-13]
Either:
- (a) Add `guest` to the Role enum and handle it in RBAC, enforcing message limits via middleware/dependency using Redis-backed GuestSession, OR
- (b) Remove guest from auth and implement it as a separate, stateless, limited endpoint that does not use `get_current_user`.

**R-16: Handle invalid roles gracefully** [Fixes F-30]
Wrap `Role(current_user.role)` in try/except in `require_role()` to return 403 instead of 500 for unknown roles.

**R-17: Add `iss` and `aud` claims** [Fixes F-22]
Set `iss=settings.APP_NAME` and `aud="eduagi-api"` in token creation. Validate both in `verify_token()`.

**R-18: Restrict CORS** [Fixes F-31]
Change to explicit method and header lists:
```python
allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
allow_headers=["Authorization", "Content-Type"],
```

### 10.4 LOW Priority

**R-19: Update `last_login` and `login_count`** [Fixes F-05]
Set `user.last_login = datetime.now(timezone.utc)` and `user.login_count += 1` in the login endpoint.

**R-20: Add pagination to session list** [Fixes F-32]
Add `skip: int = 0, limit: int = 50` query parameters to `GET /sessions`.

**R-21: Validate UUID format for session_id** [Fixes F-33]
Change parameter type to `session_id: uuid.UUID` or add validation.

**R-22: Remove role from error messages** [Fixes F-34]
Change error detail to generic: `"Not authorized for this action"`.

**R-23: Clean up dead ROLE_HIERARCHY** [Fixes F-29]
Either use the hierarchy in `require_role()` or remove the dict.

**R-24: Remove test duplication**
Consolidate `test_session_auth.py` and `test_session_enhanced.py` to eliminate duplicate test classes.

**R-25: Add integration tests**
Write TestClient-based tests covering actual HTTP flows: register -> login -> access protected endpoint -> refresh -> logout.

**R-26: Make refresh TTL configurable** [Fixes F-23]
Add `REFRESH_TOKEN_EXPIRE_DAYS: int = 7` to Settings.

---

## Appendix: Dead Code Summary

The following components are implemented but never used in production code paths:

| Component | File | Reason |
|-----------|------|--------|
| `check_account_lockout()` | `security.py:70-73` | Never called from login |
| `record_failed_login()` | `security.py:76-84` | Never called from login |
| `clear_failed_logins()` | `security.py:87-90` | Never called from login |
| `hash_token()` | `security.py:50-52` | Only tested, never used in endpoints |
| `RefreshToken` model | `refresh_token.py` | Never queried or written to |
| `GuestSession` class | `guest.py` | Never instantiated from endpoints |
| `RateLimitMiddleware` | `rate_limit.py:68-101` | Never registered in app |
| `ROLE_HIERARCHY` dict | `rbac.py:18-23` | Defined but unused |
| `User.last_login` | `user.py:22` | Never updated |
| `User.login_count` | `user.py:23` | Never updated |
| `User.is_verified` | `user.py:24` | Never checked |

---

**End of Audit Report**

*Audited by: Security Auditor Agent*
*Date: 2026-02-07*
*Classification: Internal -- Contains security vulnerability details*
