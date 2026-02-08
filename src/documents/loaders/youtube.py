"""YouTube video transcript loader."""
import logging
from youtube_transcript_api import YouTubeTranscriptApi
import re

logger = logging.getLogger(__name__)

class YouTubeLoader:
    """Fetch transcripts from YouTube videos."""

    async def load(self, video_id: str, language: str = "en") -> dict:
        """Load transcript for a YouTube video.

        Args:
            video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ') or full URL
        """
        # Extract video ID from URL if full URL provided
        vid = self._extract_video_id(video_id)

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(vid)
            # Try requested language, fall back to auto-generated, then any available
            try:
                transcript = transcript_list.find_transcript([language])
            except Exception:
                transcript = transcript_list.find_generated_transcript([language])

            entries = transcript.fetch()
            # Combine transcript entries into continuous text
            text_parts = [entry.text for entry in entries]
            full_text = " ".join(text_parts)

            # Calculate duration from last entry
            duration_seconds = 0
            if entries:
                last = entries[-1]
                duration_seconds = int(last.start + last.duration)

            return {
                "text": full_text,
                "title": f"YouTube Video: {vid}",
                "metadata": {
                    "source_type": "youtube",
                    "video_id": vid,
                    "language": language,
                    "duration_seconds": duration_seconds,
                    "segment_count": len(entries),
                },
                "source_type": "youtube",
            }
        except Exception as exc:
            logger.error("Failed to load YouTube transcript for %s: %s", vid, exc)
            raise ValueError(f"Could not load transcript for video '{vid}': {exc}") from exc

    def _extract_video_id(self, input_str: str) -> str:
        """Extract video ID from URL or return as-is if already an ID."""
        # Match common YouTube URL patterns
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'^([a-zA-Z0-9_-]{11})$',
        ]
        for pattern in patterns:
            match = re.search(pattern, input_str)
            if match:
                return match.group(1)
        return input_str  # Return as-is, let the API handle validation
