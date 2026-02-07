"""Content enrichment with keyword extraction and optional LLM enhancement."""

import re
from collections import Counter
from typing import Any


# Common English stop words to exclude from keyword extraction
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "it", "as", "was", "are", "be", "has", "had",
    "have", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "shall", "can", "this", "that", "these", "those", "not", "no",
    "so", "if", "then", "than", "too", "very", "just", "about", "also", "more",
    "some", "any", "all", "each", "every", "both", "few", "most", "other",
    "such", "only", "own", "same", "into", "over", "after", "before", "between",
    "under", "again", "further", "once", "here", "there", "when", "where",
    "why", "how", "what", "which", "who", "whom", "up", "out", "off", "down",
    "been", "being", "its", "they", "them", "their", "he", "she", "we", "you",
    "his", "her", "my", "your", "our", "me", "him", "us",
})


class ContentEnricher:
    """Enrich document content with metadata, keywords, and optional LLM analysis."""

    def __init__(self, llm: Any | None = None):
        self.llm = llm

    async def enrich(self, text: str, metadata: dict | None = None) -> dict:
        """Enrich text with auto-detected subject, topic, key terms, and summary."""
        meta = metadata.copy() if metadata else {}
        key_terms = self.extract_key_terms(text)
        meta["key_terms"] = key_terms
        meta["summary"] = text[:200].strip() + ("..." if len(text) > 200 else "")

        if self.llm is not None:
            try:
                enriched = await self._llm_enrich(text)
                meta.update(enriched)
            except Exception:
                pass  # Graceful fallback to basic enrichment

        return meta

    def extract_key_terms(self, text: str, top_n: int = 10) -> list[str]:
        """Extract top-frequency meaningful words from text."""
        # Tokenize: extract words of 3+ chars
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        # Filter stop words
        meaningful = [w for w in words if w not in _STOP_WORDS]
        if not meaningful:
            return []

        counts = Counter(meaningful)
        return [word for word, _ in counts.most_common(top_n)]

    async def _llm_enrich(self, text: str) -> dict:
        """Use LLM to extract subject, topic, and summary."""
        prompt = (
            "Analyze this educational text. Return a JSON with keys: "
            "'subject' (academic subject), 'topic' (specific topic), "
            f"'summary' (2-3 sentence summary).\n\nText:\n{text[:2000]}"
        )
        response = await self.llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        # Basic extraction — in production, parse JSON properly
        return {"llm_analysis": content}
