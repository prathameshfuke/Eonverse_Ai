"""Lazy-loaded Hugging Face pipelines used across the project."""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict

from transformers import pipeline

# Model catalog keeps the primary models in one place so we can swap if needed
MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "summarizer": {
        "task": "summarization",
        # DistilBART CNN checkpoint (small + public)
        "model": "sshleifer/distilbart-cnn-12-6",
        "kwargs": {"max_length": 180, "min_length": 40, "truncation": True},
    },
    "action_generator": {
        "task": "text2text-generation",
        "model": "google/flan-t5-small",
        "kwargs": {"max_new_tokens": 192, "temperature": 0.0},
    },
    "decision_generator": {
        "task": "text2text-generation",
        "model": "google/flan-t5-small",
        "kwargs": {"max_new_tokens": 160, "temperature": 0.0},
    },
    "captioner": {
        "task": "image-to-text",
        "model": "Salesforce/blip-image-captioning-base",
        "kwargs": {"max_new_tokens": 60},
    },
}


def _build_pipeline(name: str):
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model alias: {name}")
    info = MODEL_REGISTRY[name]
    return pipeline(task=info["task"], model=info["model"], **info.get("kwargs", {}))


@lru_cache(maxsize=None)
def get_summarizer():
    """Return a cached summarization pipeline."""
    return _build_pipeline("summarizer")


@lru_cache(maxsize=None)
def get_action_generator():
    """Return a cached text-generation pipeline for action extraction."""
    return _build_pipeline("action_generator")


@lru_cache(maxsize=None)
def get_decision_generator():
    """Return a cached text-generation pipeline for decisions/agenda summaries."""
    return _build_pipeline("decision_generator")


@lru_cache(maxsize=None)
def get_captioner():
    """Return a cached BLIP captioning pipeline."""
    return _build_pipeline("captioner")
