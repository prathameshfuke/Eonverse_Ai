"""Vision utilities for extracting cues from meeting screenshots."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from ..utils.model_registry import get_captioner
from .data_structures import VisualInsight


CAPTION_PROMPT = (
    "Caption the meeting slide or whiteboard and include any visible action cues or deadlines."
)


def _iter_images(image_dir: Path) -> Iterable[Path]:
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.webp"]
    for pattern in patterns:
        for path in sorted(image_dir.glob(pattern)):
            yield path


def analyze_images(image_dir: Path) -> List[VisualInsight]:
    captioner = get_captioner()
    visuals: List[VisualInsight] = []
    for image_path in _iter_images(image_dir):
        result = captioner(str(image_path), prompt=CAPTION_PROMPT)
        caption = result[0]["generated_text"].strip()
        visuals.append(
            VisualInsight(
                image_path=str(image_path.resolve()),
                caption=caption,
                linked_topics=[],
            )
        )
    return visuals
