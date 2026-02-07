"""Result re-ranker combining semantic distance and keyword overlap."""

import re
from collections import Counter


class ResultRanker:
    """Re-rank retrieval results using hybrid semantic + keyword scoring."""

    def rank(self, results: list[dict], query: str) -> list[dict]:
        """Re-rank results by combining semantic distance score with keyword overlap."""
        if not results:
            return results

        query_terms = self._tokenize(query)
        if not query_terms:
            return results

        query_counter = Counter(query_terms)

        scored = []
        for r in results:
            # Semantic score: lower distance is better, convert to 0-1 similarity
            distance = r.get("distance", 0.0)
            semantic_score = max(0.0, 1.0 - distance)

            # Keyword overlap score
            content = r.get("content_preview", "") or ""
            doc_terms = self._tokenize(content)
            keyword_score = self._keyword_overlap(query_counter, doc_terms)

            # Combined score: weighted average
            combined = 0.7 * semantic_score + 0.3 * keyword_score
            scored.append({**r, "_rank_score": combined})

        scored.sort(key=lambda x: x["_rank_score"], reverse=True)
        return scored

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Extract lowercase words of 2+ chars."""
        return re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())

    @staticmethod
    def _keyword_overlap(query_counter: Counter, doc_terms: list[str]) -> float:
        """Compute keyword overlap ratio between query and document."""
        if not doc_terms or not query_counter:
            return 0.0
        doc_counter = Counter(doc_terms)
        overlap = sum((query_counter & doc_counter).values())
        total = sum(query_counter.values())
        return min(overlap / total, 1.0) if total > 0 else 0.0
