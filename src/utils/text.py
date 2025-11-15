"""Utility helpers for working with long meeting transcripts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class TextChunk:
    """Represents a chunk of text split from a longer document."""

    content: str
    start: int
    end: int


def chunk_text(text: str, max_chars: int = 3500, overlap: int = 200) -> List[TextChunk]:
    """Split long transcripts into overlapping windows for model consumption."""
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    chunks: List[TextChunk] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end]
        chunks.append(TextChunk(content=chunk, start=start, end=end))
        if end == length:
            break
        start = max(0, end - overlap)
    return chunks


def merge_bullets(items: Iterable[str]) -> str:
    """Render a list of bullet strings as newline separated list."""
    return "\n".join(f"- {line.strip()}" for line in items if line and line.strip())
