"""Shared dataclasses used across the meeting analysis workflow."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ActionItem:
    description: str
    owner: str
    deadline: str
    support: str


@dataclass
class DecisionPoint:
    summary: str
    support: str


@dataclass
class VisualInsight:
    image_path: str
    caption: str
    linked_topics: List[str] = field(default_factory=list)


@dataclass
class MeetingReport:
    agenda_summary: str
    action_items: List[ActionItem]
    decisions: List[DecisionPoint]
    visuals: List[VisualInsight]

    def as_markdown_table(self) -> str:
        header = "| Action Item | Responsible | Deadline | Supporting Quote/Visual |\n"
        header += "| --- | --- | --- | --- |\n"
        rows = [
            f"| {ai.description} | {ai.owner} | {ai.deadline} | {ai.support} |"
            for ai in self.action_items
        ]
        return header + "\n".join(rows)

    def action_records(self) -> List[dict]:
        return [
            {
                "action_item": ai.description,
                "responsible": ai.owner,
                "deadline": ai.deadline,
                "support": ai.support,
            }
            for ai in self.action_items
        ]

    def decision_records(self) -> List[dict]:
        return [
            {
                "decision": dp.summary,
                "support": dp.support,
            }
            for dp in self.decisions
        ]

    def visual_records(self) -> List[dict]:
        return [
            {
                "image_path": v.image_path,
                "caption": v.caption,
                "linked_topics": ", ".join(v.linked_topics),
            }
            for v in self.visuals
        ]

    def to_dict(self) -> dict:
        return {
            "agenda_summary": self.agenda_summary,
            "action_items": [
                {
                    "description": ai.description,
                    "owner": ai.owner,
                    "deadline": ai.deadline,
                    "support": ai.support,
                }
                for ai in self.action_items
            ],
            "decisions": [
                {
                    "summary": dp.summary,
                    "support": dp.support,
                }
                for dp in self.decisions
            ],
            "visuals": [
                {
                    "image_path": v.image_path,
                    "caption": v.caption,
                    "linked_topics": v.linked_topics,
                }
                for v in self.visuals
            ],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "MeetingReport":
        return cls(
            agenda_summary=payload.get("agenda_summary", ""),
            action_items=[
                ActionItem(
                    description=item.get("description", ""),
                    owner=item.get("owner", ""),
                    deadline=item.get("deadline", ""),
                    support=item.get("support", ""),
                )
                for item in payload.get("action_items", [])
            ],
            decisions=[
                DecisionPoint(summary=item.get("summary", ""), support=item.get("support", ""))
                for item in payload.get("decisions", [])
            ],
            visuals=[
                VisualInsight(
                    image_path=item.get("image_path", ""),
                    caption=item.get("caption", ""),
                    linked_topics=item.get("linked_topics", []) or [],
                )
                for item in payload.get("visuals", [])
            ],
        )
