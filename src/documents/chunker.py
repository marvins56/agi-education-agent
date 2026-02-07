"""Section-aware text chunker with overlap."""


class SemanticChunker:
    """Split text into overlapping chunks, preferring section/paragraph boundaries."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str, metadata: dict | None = None) -> list[dict]:
        """Split text into overlapping chunks with metadata."""
        if not text or not text.strip():
            return []

        sections = self._split_into_sections(text)
        chunks: list[str] = []
        current = ""

        for section in sections:
            # If adding this section would exceed chunk_size, finalize current chunk
            if current and len(current) + len(section) + 1 > self.chunk_size:
                chunks.append(current.strip())
                # Keep overlap from end of current chunk
                overlap_text = current[-self.chunk_overlap:] if len(current) > self.chunk_overlap else current
                current = overlap_text + "\n" + section
            else:
                current = current + "\n" + section if current else section

        if current.strip():
            chunks.append(current.strip())

        # If we got no chunks from section splitting (e.g. one big block), force-split
        if not chunks:
            chunks = self._force_split(text)

        base_meta = metadata or {}
        total = len(chunks)
        return [
            {
                "content": c,
                "metadata": {
                    **base_meta,
                    "chunk_index": i,
                    "total_chunks": total,
                },
            }
            for i, c in enumerate(chunks)
        ]

    def _split_into_sections(self, text: str) -> list[str]:
        """Split text on paragraph boundaries (double newlines), then single newlines."""
        # First try double newlines (paragraphs)
        parts = text.split("\n\n")
        sections = []
        for part in parts:
            stripped = part.strip()
            if not stripped:
                continue
            if len(stripped) <= self.chunk_size:
                sections.append(stripped)
            else:
                # Sub-split long paragraphs on single newlines or sentences
                for sub in self._split_long_block(stripped):
                    sections.append(sub)
        return sections

    def _split_long_block(self, text: str) -> list[str]:
        """Split a long text block on sentence boundaries."""
        result = []
        current = ""
        # Split on '. ' to approximate sentence boundaries
        sentences = text.replace(". ", ".\n").split("\n")
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > self.chunk_size:
                result.append(current.strip())
                current = sentence
            else:
                current = current + " " + sentence if current else sentence
        if current.strip():
            result.append(current.strip())
        return result

    def _force_split(self, text: str) -> list[str]:
        """Force-split text by character count with overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        return chunks
