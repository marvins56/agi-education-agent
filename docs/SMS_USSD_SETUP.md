# SMS & USSD Channel Setup Guide

EduAGI supports learning via SMS and USSD, enabling access on **any phone** — including basic feature phones without internet. This is critical for rural students across East Africa.

## Architecture

```
Student's Phone
    │
    ├── USSD (*384*123#) ──► Africa's Talking ──► POST /api/v1/channels/ussd/callback
    │                                              (returns CON/END plain text)
    │
    └── SMS  ──────────────► Africa's Talking ──► POST /api/v1/channels/sms/callback
                                                   (optionally sends reply SMS)
```

### Components

| File | Purpose |
|------|---------|
| `src/channels/ussd_handler.py` | USSD session management & menu navigation |
| `src/channels/sms_gateway.py` | SMS send/receive with AT + Twilio failover |
| `src/channels/sms_lessons.py` | Lesson formatting & delivery scheduling |
| `src/channels/channel_router.py` | Intelligent routing between channels |
| `src/api/routers/sms_ussd.py` | FastAPI webhook endpoints |

---

## Quick Start (Sandbox)

### 1. Create Africa's Talking Sandbox Account

1. Go to [sandbox.africastalking.com](https://sandbox.africastalking.com)
2. Sign up / log in
3. Go to **Settings → API Key** and generate a key

### 2. Configure Environment

Add to your `.env`:

```env
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=atsk_your_sandbox_api_key_here
AFRICASTALKING_SHORTCODE=
AFRICASTALKING_ENVIRONMENT=sandbox
```

### 3. Start the Server

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 4. Expose with ngrok (for sandbox callbacks)

```bash
ngrok http 8000
```

### 5. Configure Callbacks in AT Dashboard

In the Africa's Talking sandbox dashboard:

- **USSD → Callback URL:** `https://your-ngrok-url/api/v1/channels/ussd/callback`
- **SMS → Callback URL:** `https://your-ngrok-url/api/v1/channels/sms/callback`
- **SMS → Delivery Report URL:** `https://your-ngrok-url/api/v1/channels/sms/delivery`

### 6. Test with AT Simulator

Use the sandbox simulator at `sandbox.africastalking.com` to send USSD requests and SMS messages.

---

## USSD Menu Flow

```
🎓 EduAGI Learning
├── 1. 📚 Start Learning
│   ├── 1. Mathematics
│   │   ├── 1. Basic Numbers
│   │   │   ├── 1. Counting 1-10  →  Lesson  →  Quiz  →  Score
│   │   │   ├── 2. Addition Basics
│   │   │   └── 3. Subtraction Basics
│   │   ├── 2. Shapes
│   │   └── 3. Time
│   ├── 2. English
│   └── 3. Science
├── 2. 📊 My Progress
├── 3. 👤 My Profile
└── 4. ❓ Help

Navigation:
  0 = Go back
  # = Main menu
  * = Help
```

## SMS Commands

| Command | Action |
|---------|--------|
| `START` | Begin learning / welcome message |
| `LESSON` | Get today's lesson |
| `QUIZ` | Take a quiz |
| `PROGRESS` | View learning stats |
| `HELP` | Show available commands |
| `NEXT` | Continue to next section |
| `REVIEW` | Re-read current lesson |
| `A/B/C/D` | Answer quiz question |
| `STOP` | Unsubscribe |

---

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/channels/ussd/callback` | USSD session handler (AT webhook) |
| POST | `/api/v1/channels/sms/callback` | Incoming SMS handler (AT webhook) |
| POST | `/api/v1/channels/sms/delivery` | SMS delivery reports (AT webhook) |
| GET | `/api/v1/channels/health` | Channel health check |

---

## Running Tests

```bash
python -m pytest tests/test_sms_ussd.py -v
```

Tests use in-memory session storage — no database or external services required.

---

## Production Deployment

1. Set `AFRICASTALKING_ENVIRONMENT=production` in `.env`
2. Use your production AT credentials
3. Register a USSD shortcode with your carrier
4. Set up a dedicated SMS shortcode
5. Ensure your server has a stable public URL (no ngrok)
6. Enable database storage by switching from in-memory handlers to DB-backed ones

### Cost Estimates (East Africa)

| Channel | Cost per interaction |
|---------|---------------------|
| USSD session | ~KES 1-2 (~$0.01) |
| SMS (outbound) | ~KES 0.5-1 (~$0.005) |
| SMS (inbound) | Free |

Built-in rate limiting: 10 SMS/day, 50/week, 200/month per student.
