"""Guest session management with limited capabilities."""

from dataclasses import dataclass, field

from src.auth.security import create_guest_token

MAX_GUEST_MESSAGES = 5


@dataclass
class GuestSession:
    """Temporary guest session with limited capabilities.

    - 5 message limit
    - No persistent data saved
    - Short-lived JWT (1 hour)
    """

    token: str = ""
    message_count: int = 0
    max_messages: int = MAX_GUEST_MESSAGES
    topics: list[str] = field(default_factory=list)

    @classmethod
    def create(cls) -> "GuestSession":
        """Create a new guest session with a token."""
        token = create_guest_token()
        return cls(token=token)

    @property
    def can_send_message(self) -> bool:
        """Check if guest can still send messages."""
        return self.message_count < self.max_messages

    @property
    def remaining_messages(self) -> int:
        return max(0, self.max_messages - self.message_count)

    def record_message(self, topic: str | None = None) -> None:
        """Record a sent message and optionally track the topic."""
        self.message_count += 1
        if topic and topic not in self.topics:
            self.topics.append(topic)

    def to_dict(self) -> dict:
        """Serialize for Redis/response."""
        return {
            "token": self.token,
            "message_count": self.message_count,
            "max_messages": self.max_messages,
            "remaining_messages": self.remaining_messages,
            "topics": self.topics,
        }
