"""Transcript-focused analysis helpers."""
from __future__ import annotations

import json
import re
from typing import Iterable, List

from ..utils.model_registry import (
    get_action_generator,
    get_decision_generator,
    get_summarizer,
)
from ..utils.text import chunk_text
from .data_structures import ActionItem, DecisionPoint

ACTION_PROMPT = (
    "You are an expert meeting assistant. From this transcript chunk, extract actionable tasks.\n"
    "Return a JSON list where each entry has 'action', 'owner', 'deadline', 'support'."
)

DECISION_PROMPT = (
    "You are an expert meeting analyst. Summarize the concrete decisions and agenda outcomes.\n"
    "Return a JSON list of objects with 'decision' and 'support'."
)


def _safe_json_parse(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Attempt to locate JSON substring
        match = re.search(r"(\[\s*{.*}\s*\])", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return []


def summarize_transcript(transcript: str) -> str:
    summarizer = get_summarizer()
    chunks = chunk_text(transcript)
    if not chunks:
        return ""
    pieces = []
    for chunk in chunks:
        summary = summarizer(chunk.content)[0]["summary_text"]
        pieces.append(summary.strip())
    return " ".join(pieces)


def extract_action_items(transcript: str) -> List[ActionItem]:
    generator = get_action_generator()
    items: List[ActionItem] = []
    for chunk in chunk_text(transcript):
        prompt = f"{ACTION_PROMPT}\nTranscript:\n{chunk.content}"
        result = generator(prompt)[0]["generated_text"]
        payload = _safe_json_parse(result)
        for obj in payload:
            items.append(
                ActionItem(
                    description=obj.get("action", ""),
                    owner=obj.get("owner", ""),
                    deadline=obj.get("deadline", ""),
                    support=obj.get("support", ""),
                )
            )
    return items


def extract_decisions(transcript: str) -> List[DecisionPoint]:
    generator = get_decision_generator()
    decisions: List[DecisionPoint] = []
    for chunk in chunk_text(transcript):
        prompt = f"{DECISION_PROMPT}\nTranscript:\n{chunk.content}"
        result = generator(prompt)[0]["generated_text"]
        payload = _safe_json_parse(result)
        for obj in payload:
            decisions.append(
                DecisionPoint(summary=obj.get("decision", ""), support=obj.get("support", ""))
            )
    return decisions
