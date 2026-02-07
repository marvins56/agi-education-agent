# F07 & F08: Session Management + User Auth & Roles
# EduAGI Feature Design Document

**Priority:** P0 (Critical)
**Tier:** 1 - Core MVP
**Dependencies:** None (foundation feature)

---

## 1. Feature Overview

### What It Does
Handles who can access EduAGI, how they log in, what they can see/do based on
their role, and how learning sessions persist across time and devices. The goal:
zero friction to start learning, pick up exactly where you left off.

### The Student Experience
```
  Marcus opens EduAGI on his phone during lunch.

  [Continue with Google] ← one tap

  "Welcome back, Marcus! Last time we were working on
   cell division in Biology. Want to continue?"

  [Continue]  [Start something new]

  He taps Continue → conversation picks up mid-topic,
  the AI remembers his last question was about mitosis.

  After school, he opens his laptop → same session,
  same place, seamlessly.
```

---

## 2. Detailed Workflows

### 2.1 Registration Flows

```
┌─────────────────────────────────────────────────────────────┐
│  REGISTRATION OPTIONS                                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PATH 1: Email/Password (Personal)                          │
│  ┌────────────────────────────────────────────┐             │
│  │  1. Student enters name, email, password   │             │
│  │  2. Verification email sent                │             │
│  │  3. Click verify link                      │             │
│  │  4. Complete onboarding (grade, subjects)  │             │
│  │  5. Learning style quiz                    │             │
│  │  6. Ready to learn                         │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  PATH 2: OAuth (Google / Microsoft / Apple)                 │
│  ┌────────────────────────────────────────────┐             │
│  │  1. Click "Continue with Google"           │             │
│  │  2. Google OAuth consent screen            │             │
│  │  3. Redirect back with token               │             │
│  │  4. Auto-create account from Google profile│             │
│  │  5. Complete onboarding                    │             │
│  │  6. Ready to learn                         │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  PATH 3: School SSO (Institution)                           │
│  ┌────────────────────────────────────────────┐             │
│  │  1. Student goes to school's EduAGI portal │             │
│  │  2. Redirected to school's identity provider│            │
│  │     (Okta, Azure AD, Google Workspace)     │             │
│  │  3. SAML/OIDC assertion sent to EduAGI     │             │
│  │  4. Account auto-provisioned with school   │             │
│  │     data (name, grade, class assignments)  │             │
│  │  5. Minimal onboarding (prefs only)        │             │
│  │  6. Ready to learn                         │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  PATH 4: LMS Launch (Canvas, Moodle)                        │
│  ┌────────────────────────────────────────────┐             │
│  │  1. Teacher adds EduAGI as LTI tool in LMS│             │
│  │  2. Student clicks EduAGI link in course   │             │
│  │  3. LTI 1.3 launch → JWT with user info   │             │
│  │  4. Account auto-created/linked            │             │
│  │  5. Context: knows which class + assignment│             │
│  │  6. Opens directly to relevant content     │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  PATH 5: Teacher Invite                                     │
│  ┌────────────────────────────────────────────┐             │
│  │  1. Teacher sends invite link/code         │             │
│  │  2. Student clicks link or enters code     │             │
│  │  3. Creates account (email or OAuth)       │             │
│  │  4. Auto-joined to teacher's class         │             │
│  │  5. Subjects/curriculum pre-configured     │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  PATH 6: Guest Mode (No Account)                            │
│  ┌────────────────────────────────────────────┐             │
│  │  1. Click "Try without account"            │             │
│  │  2. Temporary session (no memory saved)    │             │
│  │  3. Limited: 5 messages, no assessments    │             │
│  │  4. Prompt to create account to save work  │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Login & Token Management

```
┌─────────────────────────────────────────────────────────────┐
│  AUTH TOKEN FLOW                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Login successful                                           │
│       │                                                     │
│       ▼                                                     │
│  Server generates:                                          │
│  ┌─────────────────────────────────┐                        │
│  │  ACCESS TOKEN (JWT)             │                        │
│  │  • Short-lived: 15 minutes      │                        │
│  │  • Contains: user_id, role,     │                        │
│  │    permissions, session_id      │                        │
│  │  • Sent in Authorization header │                        │
│  │  • Stored in memory (not local  │                        │
│  │    storage — XSS protection)    │                        │
│  └─────────────────────────────────┘                        │
│  ┌─────────────────────────────────┐                        │
│  │  REFRESH TOKEN                  │                        │
│  │  • Long-lived: 7 days           │                        │
│  │  • HttpOnly secure cookie       │                        │
│  │  • Rotated on each use          │                        │
│  │  • Stored in DB (revocable)     │                        │
│  └─────────────────────────────────┘                        │
│                                                             │
│  TOKEN REFRESH FLOW:                                        │
│                                                             │
│  Access token expires → 401 response                        │
│       │                                                     │
│       ▼                                                     │
│  Client sends refresh token (cookie)                        │
│       │                                                     │
│       ▼                                                     │
│  Server validates refresh token                             │
│       │                                                     │
│       ├─── Valid → issue new access + refresh tokens        │
│       │                                                     │
│       └─── Invalid → redirect to login                      │
│                                                             │
│  MULTI-DEVICE:                                              │
│  • Each device gets its own refresh token                   │
│  • Max 5 active devices per account                         │
│  • "Manage devices" in settings to revoke                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Session Management

```
┌─────────────────────────────────────────────────────────────┐
│  TUTORING SESSION LIFECYCLE                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CREATE SESSION:                                            │
│  ┌────────────────────────────────────────────┐             │
│  │  Student starts learning                   │             │
│  │       │                                    │             │
│  │       ▼                                    │             │
│  │  Generate session_id (UUID)                │             │
│  │       │                                    │             │
│  │       ▼                                    │             │
│  │  Store in Redis:                           │             │
│  │  session:{id} = {                          │             │
│  │    student_id, subject, topic,             │             │
│  │    mode (tutor/assess/review),             │             │
│  │    started_at, last_active,                │             │
│  │    conversation_history (last 50),         │             │
│  │    context (learning objectives, etc.),    │             │
│  │    delivery_prefs (voice, avatar, sign)    │             │
│  │  }                                         │             │
│  │  TTL: 2 hours (refreshed on activity)      │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  SESSION RESUME (after disconnect):                         │
│  ┌────────────────────────────────────────────┐             │
│  │  Student returns                           │             │
│  │       │                                    │             │
│  │  Check Redis for active session            │             │
│  │       │                                    │             │
│  │  ├── Found → restore full context          │             │
│  │  │   "Welcome back! We were discussing..." │             │
│  │  │                                         │             │
│  │  └── Expired → check PostgreSQL for last   │             │
│  │      session summary → offer to continue   │             │
│  │      "Last time you were studying X.       │             │
│  │       Pick up where you left off?"         │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  SESSION END:                                               │
│  ┌────────────────────────────────────────────┐             │
│  │  Student ends session (or timeout)         │             │
│  │       │                                    │             │
│  │       ▼                                    │             │
│  │  1. Generate session summary (Claude)      │             │
│  │  2. Save summary to PostgreSQL             │             │
│  │  3. Update student profile                 │             │
│  │  4. Clear Redis session data               │             │
│  │  5. Record analytics (duration, topics,    │             │
│  │     messages exchanged, outcomes)          │             │
│  └────────────────────────────────────────────┘             │
│                                                             │
│  INACTIVITY HANDLING:                                       │
│  • 15 min idle → "Still there?" prompt                      │
│  • 30 min idle → session paused, context saved              │
│  • 2 hours idle → session ended, summary generated          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Role-Based Access Control (RBAC)

```
┌─────────────────────────────────────────────────────────────┐
│  ROLES & PERMISSIONS                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  STUDENT                                                    │
│  ├── Start/resume tutoring sessions                         │
│  ├── Take assessments                                       │
│  ├── View own progress/grades                               │
│  ├── Upload documents (for own study)                       │
│  ├── Manage own profile/preferences                         │
│  ├── Appeal grades                                          │
│  └── Cannot: see other students, create classes             │
│                                                             │
│  TEACHER                                                    │
│  ├── Everything a student can do, plus:                     │
│  ├── Create/manage classes                                  │
│  ├── Create/assign assessments                              │
│  ├── View all students in their classes                     │
│  ├── Override AI grades                                     │
│  ├── Upload curriculum content (goes to RAG)                │
│  ├── View class-wide analytics                              │
│  ├── Send messages to students                              │
│  └── Cannot: manage other teachers, system config           │
│                                                             │
│  PARENT                                                     │
│  ├── View linked child's progress (read-only)               │
│  ├── View assessment results                                │
│  ├── Receive progress reports                               │
│  └── Cannot: interact with AI tutor, modify anything        │
│                                                             │
│  ADMIN (Institution)                                        │
│  ├── Everything a teacher can do, plus:                     │
│  ├── Manage teachers and classes                            │
│  ├── Configure institution settings                         │
│  ├── View institution-wide analytics                        │
│  ├── Manage SSO configuration                               │
│  ├── Set content policies                                   │
│  └── Cannot: access system internals                        │
│                                                             │
│  SUPER ADMIN (Platform)                                     │
│  ├── Full system access                                     │
│  ├── Manage institutions                                    │
│  ├── System configuration                                   │
│  ├── Monitor health/usage                                   │
│  └── Emergency access controls                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Sub-features & Small Touches

- **"Continue where I left off"** — one-click on login, shows last session topic + preview
- **Session replay** — student can scroll through past sessions (read-only)
- **"Share with teacher"** — share a specific session/conversation for feedback
- **Guest mode** — try 5 free messages without account, prompt to sign up
- **Account linking** — connect personal Google account + school SSO to same profile
- **2FA** — TOTP-based for teachers/admins (optional for students)
- **Magic link login** — email a login link (no password needed)
- **Password reset** — email-based, expires in 1 hour
- **Email verification** — required before full access
- **Account deletion** — one-click, 30-day grace period, GDPR compliant
- **Session analytics** — "This session: 45 min, 3 topics, 12 questions answered"
- **Inactivity detector** — "Still there?" with gentle animation
- **Auto session summary email** — optional daily/weekly digest of learning activity
- **Device management** — see active devices, revoke access
- **Login history** — see when/where you logged in (security)
- **Parental consent flow** — for students under 13 (COPPA)

---

## 4. Technical Requirements

### JWT Structure
```
  Header: { alg: "RS256", typ: "JWT" }

  Payload: {
    sub: "user-uuid",
    role: "student",
    permissions: ["tutor", "assess", "view_own"],
    institution_id: "school-uuid" | null,
    session_id: "current-session-uuid",
    iat: 1709000000,
    exp: 1709000900  (15 min)
  }

  Signed with: RSA-256 private key (asymmetric)
  Verified with: public key (any service can verify)
```

### Compliance Requirements
```
  FERPA (Student Privacy):
  • No student data shared without consent
  • Parents can access child's records
  • Data minimization
  • Audit logging of all data access

  COPPA (Children Under 13):
  • Parental consent required
  • Limited data collection
  • No behavioral advertising
  • Easy data deletion

  GDPR (EU Students):
  • Explicit consent for data processing
  • Right to data export (JSON/CSV)
  • Right to deletion ("right to be forgotten")
  • Data processing agreements with all vendors
  • Data residency options (EU servers)
```

### Session Storage Schema (Redis)
```
  Key: session:{uuid}
  TTL: 7200 seconds (2 hours, refreshed on activity)

  Value: {
    student_id: "uuid",
    subject: "math",
    topic: "quadratic_equations",
    mode: "tutoring",
    started_at: "2026-02-06T10:00:00Z",
    last_active: "2026-02-06T10:45:00Z",
    message_count: 23,
    conversation_history: [ last 50 messages ],
    context: {
      learning_objectives: [...],
      current_difficulty: "medium",
      comprehension_score: 0.75
    },
    delivery_prefs: {
      voice: true,
      avatar: false,
      sign_language: "ASL"
    }
  }
```

---

## 5. Services & Alternatives

### Authentication

| Service | Type | Pricing | Pros | Cons |
|---------|------|---------|------|------|
| **Custom JWT + OAuth (Primary)** | Self-built | Dev time only | Full control, no limits | Must maintain |
| Auth0 | Managed | Free to 7.5K MAU, then $23/mo+ | Easy, feature-rich | Expensive at scale |
| Clerk | Managed | Free to 10K MAU, then $25/mo+ | Beautiful UI, modern | Newer, less enterprise |
| Supabase Auth | Open-source | Free (self-host) or hosted | PostgreSQL-native, simple | Less SSO support |
| Firebase Auth | Managed | Free tier generous | Google ecosystem, easy | Vendor lock-in |
| **Keycloak (Recommended for enterprise)** | Self-hosted | Free | Full SAML/OIDC, enterprise-grade | Complex setup |

**Recommendation:** Custom JWT for MVP, Keycloak when institutions need SSO.

### Session Store

| Service | Pros | Cons |
|---------|------|------|
| **Redis (Primary)** | Fast, TTL support, pub/sub | Volatile (needs backup strategy) |
| DragonflyDB | Redis-compatible, more efficient | Newer, less community |
| PostgreSQL sessions | Persistent, ACID | Slower for session reads |
| Encrypted cookies | No server storage | Size limits, no server-side revocation |

### SSO Providers (Institutional)

| Provider | Protocol | Common In |
|----------|----------|-----------|
| Okta | SAML 2.0, OIDC | US universities |
| Azure AD | SAML 2.0, OIDC | Schools using Microsoft |
| Google Workspace | OIDC | Schools using Google |
| Clever | OAuth 2.0 | K-12 (US) |
| ClassLink | SAML, OIDC | K-12 (US) |

---

## 6. Connections & Dependencies

```
  F07/F08 is the FOUNDATION — everything depends on it.

  ┌──────────────────────────────────────────┐
  │              F07/F08                      │
  │         Session + Auth                    │
  └────────────────┬─────────────────────────┘
                   │
       ┌───────────┼───────────┬──────────┐
       │           │           │          │
       ▼           ▼           ▼          ▼
  ┌─────────┐ ┌─────────┐ ┌────────┐ ┌────────┐
  │ F01     │ │ F03     │ │ F04/05 │ │ F12/13 │
  │ Tutor   │ │ Memory  │ │ Assess │ │ Dash-  │
  │ (needs  │ │ (needs  │ │ (needs │ │ boards │
  │ session)│ │ user_id)│ │ auth)  │ │ (RBAC) │
  └─────────┘ └─────────┘ └────────┘ └────────┘

  Every API call includes: Authorization: Bearer {jwt}
  Every feature checks: user role + permissions before acting
```

---

*End of F07/F08 Session & Auth Design*
