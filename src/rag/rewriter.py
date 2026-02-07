"""Query rewriter for RAG enhancement."""

from typing import Any


class QueryRewriter:
    """Expand and improve search queries for better retrieval."""

    def __init__(self, llm: Any | None = None):
        self.llm = llm

    async def rewrite(self, query: str, context: dict | None = None) -> str:
        """Rewrite query with synonyms or decomposition. Falls back to original if no LLM."""
        if self.llm is None:
            return query

        try:
            ctx_str = ""
            if context:
                if context.get("subject"):
                    ctx_str += f" Subject: {context['subject']}."
                if context.get("grade_level"):
                    ctx_str += f" Grade level: {context['grade_level']}."

            prompt = (
                "Rewrite this educational search query to improve retrieval. "
                "Add relevant synonyms and expand abbreviations. "
                "Return ONLY the rewritten query, nothing else.\n\n"
                f"Original query: {query}{ctx_str}"
            )
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            return content.strip() or query
        except Exception:
            return query
