"""YouTube video transcript loader."""

import logging
import re

from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)


class YouTubeLoader:
    """Fetch transcripts from YouTube videos."""

    async def load(self, video_id: str, language: str = "en") -> dict:
        """Load transcript for a YouTube video.

        Args:
            video_id: YouTube video ID (e.g., 'dQw4w9WgXcQ') or full URL
            language: Language code (default 'en')
        """
        vid = self._extract_video_id(video_id)

        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(vid, languages=(language,))

            snippets = list(transcript.snippets)
            text_parts = [s.text for s in snippets]
            full_text = " ".join(text_parts)

            duration_seconds = 0
            if snippets:
                last = snippets[-1]
                duration_seconds = int(last.start + last.duration)

            return {
                "text": full_text,
                "title": f"YouTube Video: {vid}",
                "metadata": {
                    "source_type": "youtube",
                    "video_id": vid,
                    "language": transcript.language_code,
                    "duration_seconds": duration_seconds,
                    "segment_count": len(snippets),
                },
                "source_type": "youtube",
            }
        except Exception as exc:
            logger.error("Failed to load YouTube transcript for %s: %s", vid, exc)
            raise ValueError(
                f"Could not load transcript for video '{vid}': {exc}"
            ) from exc

    def _extract_video_id(self, input_str: str) -> str:
        """Extract video ID from URL or return as-is."""
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
            r"^([a-zA-Z0-9_-]{11})$",
        ]
        for pattern in patterns:
            match = re.search(pattern, input_str)
            if match:
                return match.group(1)
        return input_str
