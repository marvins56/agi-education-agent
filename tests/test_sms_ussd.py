"""
Tests for SMS/USSD channel endpoints and handlers.

Uses the in-memory handlers so no database or external services needed.
"""

import pytest
from httpx import AsyncClient, ASGITransport

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def app():
    """Create a minimal FastAPI app with only the sms_ussd router."""
    from fastapi import FastAPI
    from src.api.routers.sms_ussd import router
    _app = FastAPI()
    _app.include_router(router, prefix="/api/v1")
    return _app


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# USSD Tests
# ---------------------------------------------------------------------------

class TestUSSDFlow:
    """Test the full USSD learning flow: Welcome → Subject → Topic → Lesson → Quiz → Score"""

    @pytest.mark.anyio
    async def test_welcome_menu(self, client):
        """First USSD request shows welcome menu."""
        resp = await client.post("/api/v1/channels/ussd/callback", data={
            "sessionId": "sess1",
            "phoneNumber": "+256700000001",
            "serviceCode": "*384*123#",
            "text": "",
        })
        assert resp.status_code == 200
        body = resp.text
        assert body.startswith("CON ")
        assert "EduAGI" in body
        assert "Start Learning" in body

    @pytest.mark.anyio
    async def test_select_subject(self, client):
        """Selecting '1' from main menu shows subjects."""
        # First request (welcome)
        await client.post("/api/v1/channels/ussd/callback", data={
            "sessionId": "sess2", "phoneNumber": "+256700000002",
            "serviceCode": "*384*123#", "text": "",
        })
        # Select "Start Learning"
        resp = await client.post("/api/v1/channels/ussd/callback", data={
            "sessionId": "sess2", "phoneNumber": "+256700000002",
            "serviceCode": "*384*123#", "text": "1",
        })
        assert resp.status_code == 200
        body = resp.text
        assert "CON " in body
        assert "Mathematics" in body

    @pytest.mark.anyio
    async def test_full_learning_flow(self, client):
        """Walk through: Welcome → Subject → Topic → Lesson → Content → Quiz."""
        sid = "sess_full"
        phone = "+256700000003"
        base = {"sessionId": sid, "phoneNumber": phone, "serviceCode": "*384*123#"}

        # 1. Welcome
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": ""})
        assert "EduAGI" in r.text

        # 2. Start Learning (option 1)
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        assert "Mathematics" in r.text

        # 3. Select Mathematics (option 1)
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        assert "Basic Numbers" in r.text

        # 4. Select Basic Numbers (option 1)
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        assert "Counting 1-10" in r.text

        # 5. Select Counting 1-10 (option 1)
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        assert "numbers" in r.text.lower()

        # 6. Take Quiz (option 1)
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        assert "Quiz" in r.text or "question" in r.text.lower()

        # 7. Answer quiz (correct answer is option 2 = "4")
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "2"})
        assert "Correct" in r.text or "correct" in r.text.lower()

    @pytest.mark.anyio
    async def test_back_navigation(self, client):
        """Pressing 0 goes back."""
        sid = "sess_back"
        phone = "+256700000004"
        base = {"sessionId": sid, "phoneNumber": phone, "serviceCode": "*384*123#"}

        # Welcome → Start Learning → Back
        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": ""})
        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "0"})
        assert "EduAGI" in r.text  # Back to main menu

    @pytest.mark.anyio
    async def test_home_navigation(self, client):
        """Pressing # goes to main menu from anywhere."""
        sid = "sess_home"
        phone = "+256700000005"
        base = {"sessionId": sid, "phoneNumber": phone, "serviceCode": "*384*123#"}

        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": ""})
        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "1"})
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "#"})
        assert "EduAGI" in r.text

    @pytest.mark.anyio
    async def test_help_menu(self, client):
        """Pressing * shows help."""
        sid = "sess_help"
        phone = "+256700000006"
        base = {"sessionId": sid, "phoneNumber": phone, "serviceCode": "*384*123#"}

        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": ""})
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "*"})
        assert "Help" in r.text

    @pytest.mark.anyio
    async def test_invalid_option(self, client):
        """Invalid menu option returns error message."""
        sid = "sess_invalid"
        phone = "+256700000007"
        base = {"sessionId": sid, "phoneNumber": phone, "serviceCode": "*384*123#"}

        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": ""})
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "9"})
        assert "Invalid" in r.text or "invalid" in r.text.lower()

    @pytest.mark.anyio
    async def test_progress_menu(self, client):
        """Option 2 from main menu shows progress."""
        sid = "sess_prog"
        phone = "+256700000008"
        base = {"sessionId": sid, "phoneNumber": phone, "serviceCode": "*384*123#"}

        await client.post("/api/v1/channels/ussd/callback", data={**base, "text": ""})
        r = await client.post("/api/v1/channels/ussd/callback", data={**base, "text": "2"})
        assert "Progress" in r.text


# ---------------------------------------------------------------------------
# SMS Tests
# ---------------------------------------------------------------------------

class TestSMSFlow:
    """Test SMS callback and command handling."""

    @pytest.mark.anyio
    async def test_sms_callback_start(self, client):
        """START command returns welcome message."""
        resp = await client.post("/api/v1/channels/sms/callback", data={
            "from": "+256700000010",
            "to": "12345",
            "text": "START",
            "date": "2026-02-19",
            "id": "msg1",
        })
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_sms_callback_help(self, client):
        """HELP command returns command list."""
        resp = await client.post("/api/v1/channels/sms/callback", data={
            "from": "+256700000011",
            "to": "12345",
            "text": "HELP",
        })
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_sms_callback_lesson(self, client):
        """LESSON command returns lesson content."""
        resp = await client.post("/api/v1/channels/sms/callback", data={
            "from": "+256700000012",
            "to": "12345",
            "text": "LESSON",
        })
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_sms_callback_quiz_answer(self, client):
        """Single letter quiz answer is handled."""
        resp = await client.post("/api/v1/channels/sms/callback", data={
            "from": "+256700000013",
            "to": "12345",
            "text": "B",
        })
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_sms_delivery_report(self, client):
        """Delivery report endpoint accepts data."""
        resp = await client.post("/api/v1/channels/sms/delivery", data={
            "id": "msg123",
            "status": "Delivered",
            "phoneNumber": "+256700000014",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Channel Health
# ---------------------------------------------------------------------------

class TestChannelHealth:

    @pytest.mark.anyio
    async def test_health(self, client):
        resp = await client.get("/api/v1/channels/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "sms" in data["channels"]
        assert "ussd" in data["channels"]


# ---------------------------------------------------------------------------
# Unit tests for SMS Gateway helpers
# ---------------------------------------------------------------------------

class TestSMSGatewayHelpers:

    def test_truncate_for_sms(self):
        from src.channels.sms_gateway import SMSGateway
        gw = SMSGateway.__new__(SMSGateway)
        short = "Hello world"
        assert gw._truncate_for_sms(short) == short

        long_text = "A" * 200
        result = gw._truncate_for_sms(long_text)
        assert len(result) <= 163  # 160 + "..."

    def test_split_long_message(self):
        from src.channels.sms_gateway import SMSGateway
        gw = SMSGateway.__new__(SMSGateway)

        short = "Hello"
        assert gw.split_long_message(short) == [short]

        long_text = "Word " * 50  # ~250 chars
        parts = gw.split_long_message(long_text)
        assert len(parts) >= 2

    def test_format_message(self):
        from src.channels.sms_gateway import SMSGateway
        gw = SMSGateway.__new__(SMSGateway)
        gw.message_templates = {"hello": "Hi {name}!"}
        result = gw.format_message("hello", name="Thor")
        assert result == "Hi Thor!"


# ---------------------------------------------------------------------------
# Unit tests for USSD menu formatting
# ---------------------------------------------------------------------------

class TestUSSDMenuFormatting:

    def test_format_menu_within_limit(self):
        from src.api.routers.sms_ussd import _InMemoryUSSDHandler
        handler = _InMemoryUSSDHandler()
        result = handler._format_menu(
            title="Test",
            options=[("1", "Option A"), ("2", "Option B")],
            footer="0=Back",
        )
        assert "1. Option A" in result
        assert len(result) <= handler.max_text_length
