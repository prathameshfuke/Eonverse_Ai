"""High-level orchestration helpers for meeting analytics."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .data_structures import MeetingReport
from .transcript import extract_action_items, extract_decisions, summarize_transcript
from .vision import analyze_images


def load_transcript(path: Path, limit: int | None = None) -> str:
    """Load transcript text from plaintext or JSON (MeetingBank-style) rows."""
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix == ".jsonl":
        lines = path.read_text(encoding="utf-8").splitlines()
        parts = []
        for idx, line in enumerate(lines):
            if limit is not None and idx >= limit:
                break
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            parts.append(obj.get("source", ""))
        return "\n".join(parts)
    return path.read_text(encoding="utf-8")


def build_meeting_report(
    transcript_path: Path,
    image_dir: Optional[Path] = None,
    jsonl_limit: int | None = None,
) -> MeetingReport:
    transcript_text = load_transcript(transcript_path, limit=jsonl_limit)
    agenda_summary = summarize_transcript(transcript_text)
    actions = extract_action_items(transcript_text)
    decisions = extract_decisions(transcript_text)
    visuals = analyze_images(image_dir) if image_dir and image_dir.exists() else []
    return MeetingReport(
        agenda_summary=agenda_summary,
        action_items=actions,
        decisions=decisions,
        visuals=visuals,
    )
