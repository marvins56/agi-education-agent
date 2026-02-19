"""
FastAPI router for SMS and USSD webhook endpoints.

These endpoints receive callbacks from Africa's Talking (and other providers)
for incoming SMS messages and USSD session requests.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import PlainTextResponse

from src.channels.ussd_handler import USSDSessionHandler, USSDResponse
from src.channels.sms_gateway import SMSGateway
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/channels", tags=["SMS/USSD Channels"])


# ---------------------------------------------------------------------------
# USSD callback  – Africa's Talking sends POST with form-encoded fields
# ---------------------------------------------------------------------------

@router.post("/ussd/callback", response_class=PlainTextResponse)
async def ussd_callback(
    sessionId: str = Form(...),
    phoneNumber: str = Form(...),
    networkCode: Optional[str] = Form(None),
    serviceCode: str = Form(""),
    text: str = Form(""),
):
    """
    Africa's Talking USSD callback endpoint.

    The gateway POSTs form data with the user's input.  We must reply with
    plain text prefixed by either:
      - ``CON `` → session continues (user sees a new menu)
      - ``END `` → session ends

    See: https://developers.africastalking.com/docs/ussd/overview
    """
    try:
        # Build a lightweight in-memory handler (no real DB in sandbox mode)
        handler = _get_ussd_handler()
        response: USSDResponse = await handler.handle_ussd_request(
            session_id=sessionId,
            phone_number=phoneNumber,
            user_input=text,
        )

        prefix = "END " if response.end_session else "CON "
        return PlainTextResponse(content=prefix + response.text)

    except Exception as exc:
        logger.error(f"USSD callback error: {exc}", exc_info=True)
        return PlainTextResponse(content="END Sorry, an error occurred. Please try again.")


# ---------------------------------------------------------------------------
# SMS callback – Africa's Talking sends POST when an SMS is received
# ---------------------------------------------------------------------------

@router.post("/sms/callback")
async def sms_callback(
    request: Request,
    # Africa's Talking form fields
    date: Optional[str] = Form(None),
    from_: Optional[str] = Form(None, alias="from"),
    id: Optional[str] = Form(None),
    linkId: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    to: Optional[str] = Form(None),
    networkCode: Optional[str] = Form(None),
):
    """
    Africa's Talking incoming SMS callback endpoint.

    Receives an SMS, processes it via the SMS gateway, and optionally sends
    a reply SMS back to the student.
    """
    phone_number = from_ or ""
    content = text or ""

    logger.info(f"Incoming SMS from {phone_number}: {content[:50]}...")

    try:
        handler = _get_sms_handler()
        reply = await handler.handle_incoming_sms(
            from_number=phone_number,
            content=content,
            provider="africastalking",
        )

        # If we have a reply, send it back
        if reply and handler.providers:
            from src.channels.sms_gateway import SMSMessage

            msg = SMSMessage(
                phone_number=phone_number,
                content=reply,
                message_type="auto_reply",
            )
            await handler.send_sms(msg)

        return {"status": "ok"}

    except Exception as exc:
        logger.error(f"SMS callback error: {exc}", exc_info=True)
        return {"status": "error", "detail": str(exc)}


# ---------------------------------------------------------------------------
# SMS delivery report callback
# ---------------------------------------------------------------------------

@router.post("/sms/delivery")
async def sms_delivery_report(
    id: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    phoneNumber: Optional[str] = Form(None),
    networkCode: Optional[str] = Form(None),
    failureReason: Optional[str] = Form(None),
):
    """Receive SMS delivery status reports from Africa's Talking."""
    logger.info(f"SMS delivery report: id={id} status={status} phone={phoneNumber}")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Health check for channel endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
async def channels_health():
    """Health check for SMS/USSD channel endpoints."""
    return {
        "status": "ok",
        "channels": ["sms", "ussd"],
        "provider": "africastalking",
    }


# ---------------------------------------------------------------------------
# Helpers – lightweight handlers that work without a real DB session
# ---------------------------------------------------------------------------

class _InMemoryUSSDHandler(USSDSessionHandler):
    """USSD handler that uses in-memory session storage for sandbox testing."""

    def __init__(self):
        # Skip parent __init__ which requires a DB session
        from datetime import timedelta

        self.db = None
        self.session_timeout = timedelta(minutes=10)
        self.max_text_length = 182
        self._sessions: dict = {}

        # Copy educational content from parent class
        self.subjects = {
            "1": {"name": "Mathematics", "topics": {
                "1": {"name": "Basic Numbers", "lessons": ["Counting 1-10", "Addition Basics", "Subtraction Basics"]},
                "2": {"name": "Shapes", "lessons": ["Circles & Squares", "Triangles", "Rectangle"]},
                "3": {"name": "Time", "lessons": ["Reading Clock", "Days of Week", "Months"]},
            }},
            "2": {"name": "English", "topics": {
                "1": {"name": "Alphabet", "lessons": ["Letters A-M", "Letters N-Z", "Letter Sounds"]},
                "2": {"name": "Words", "lessons": ["Simple Words", "Action Words", "Animal Names"]},
                "3": {"name": "Sentences", "lessons": ["Making Sentences", "Questions", "Stories"]},
            }},
            "3": {"name": "Science", "topics": {
                "1": {"name": "Animals", "lessons": ["Farm Animals", "Wild Animals", "Animal Homes"]},
                "2": {"name": "Plants", "lessons": ["Parts of Plant", "How Plants Grow", "Trees & Flowers"]},
                "3": {"name": "Weather", "lessons": ["Sun & Rain", "Hot & Cold", "Seasons"]},
            }},
        }

        self.lesson_content = {
            "Counting 1-10": {
                "content": "Let's learn numbers!\n\n1-One  2-Two  3-Three\n4-Four  5-Five\n\nPractice counting objects around you!",
                "quiz": {
                    "question": "What number comes after 3?",
                    "options": ["2", "4", "5", "1"],
                    "correct": 1,
                    "explanation": "4 comes after 3: 1,2,3,4,5...",
                },
            },
            "Addition Basics": {
                "content": "Addition means putting together.\n\n1+1=2  2+1=3  2+2=4\n3+2=5  4+1=5\n\nTry adding fingers!",
                "quiz": {
                    "question": "What is 2 + 3?",
                    "options": ["4", "5", "6", "3"],
                    "correct": 1,
                    "explanation": "2+3=5. Count: 2...3,4,5!",
                },
            },
            "Subtraction Basics": {
                "content": "Subtraction means taking away.\n\n5-1=4  4-2=2  3-1=2\n\nIf you have 5 sweets and eat 2, you have 3 left!",
                "quiz": {
                    "question": "What is 5 - 2?",
                    "options": ["2", "4", "3", "1"],
                    "correct": 2,
                    "explanation": "5-2=3. Count back: 5,4,3!",
                },
            },
            "Letters A-M": {
                "content": "The alphabet starts with:\nA B C D E F G\nH I J K L M\n\nA=Apple B=Ball C=Cat\nD=Dog E=Egg F=Fish",
                "quiz": {
                    "question": "What letter comes after C?",
                    "options": ["B", "E", "D", "A"],
                    "correct": 2,
                    "explanation": "D comes after C: A,B,C,D,E...",
                },
            },
            "Farm Animals": {
                "content": "Farm animals live with people:\n\nCow-gives milk\nChicken-gives eggs\nGoat-gives milk & meat\nPig-gives meat\nDog-guards the farm",
                "quiz": {
                    "question": "Which animal gives us eggs?",
                    "options": ["Cow", "Goat", "Chicken", "Dog"],
                    "correct": 2,
                    "explanation": "Chickens lay eggs that we eat!",
                },
            },
        }

    async def _get_or_create_session(self, session_id: str, phone_number: str):
        """In-memory session management."""
        from datetime import datetime

        if session_id not in self._sessions:
            self._sessions[session_id] = _MemorySession(
                session_id=session_id,
                phone_number=phone_number,
            )
        # Replace self.db with a no-op object so parent's .commit() calls work
        self.db = _NoOpDB()
        return self._sessions[session_id]

    def _is_session_valid(self, session) -> bool:
        from datetime import datetime
        return (datetime.utcnow() - session.last_activity) < self.session_timeout

    async def _cleanup_expired_session(self, session):
        session.is_active = False

    async def _log_ussd_interaction(self, session, user_input, response):
        pass  # No DB in sandbox


class _NoOpDB:
    """No-op database stand-in so .commit() / .add() / .query() don't crash."""
    def commit(self): pass
    def add(self, obj): pass
    def query(self, *a, **kw): return self
    def filter_by(self, **kw): return self
    def filter(self, *a): return self
    def first(self): return None
    def all(self): return []
    def count(self): return 0


class _MemorySession:
    """Minimal in-memory session object matching USSDSession interface."""

    def __init__(self, session_id: str, phone_number: str):
        from datetime import datetime

        self.session_id = session_id
        self.phone_number = phone_number
        self.student_id = None
        self.current_menu = "main"
        self.menu_history: list = []
        self.current_data: dict = {}
        self.last_activity = datetime.utcnow()
        self.is_active = True

    def commit(self):
        pass  # no-op


_ussd_handler: Optional[_InMemoryUSSDHandler] = None
_sms_handler: Optional[SMSGateway] = None


def _get_ussd_handler() -> _InMemoryUSSDHandler:
    global _ussd_handler
    if _ussd_handler is None:
        _ussd_handler = _InMemoryUSSDHandler()
    return _ussd_handler


def _get_sms_handler() -> SMSGateway:
    global _sms_handler
    if _sms_handler is None:
        _sms_handler = SMSGateway.__new__(SMSGateway)
        _sms_handler.db = None
        _sms_handler.providers = []
        _sms_handler.message_templates = {}
        _sms_handler.rate_limits = {
            "daily_limit": 10,
            "weekly_limit": 50,
            "monthly_limit": 200,
            "cost_limit_cents": 1000,
        }
        _sms_handler._load_message_templates()

        # Try to init AT provider from settings
        from src.config import settings
        if getattr(settings, "AFRICASTALKING_API_KEY", ""):
            from src.channels.sms_gateway import AfricasTalkingSMSProvider
            _sms_handler.providers.append(
                AfricasTalkingSMSProvider(
                    username=settings.AFRICASTALKING_USERNAME,
                    api_key=settings.AFRICASTALKING_API_KEY,
                    shortcode=getattr(settings, "AFRICASTALKING_SHORTCODE", ""),
                    environment=getattr(settings, "AFRICASTALKING_ENVIRONMENT", "sandbox"),
                )
            )
    return _sms_handler
