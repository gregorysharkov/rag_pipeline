from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PlanSection:
    """A section of the script plan with name, key message, and points."""

    name: str
    key_message: str
    points: List[str]


@dataclass
class Plan:
    """A structured plan for a video script."""

    title: str
    target_audience: str
    duration: str
    sections: List[PlanSection] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        """Create a Plan instance from a dictionary."""
        if not data:
            return None

        sections = []
        for section_data in data.get("sections", []):
            sections.append(
                PlanSection(
                    name=section_data.get("name", ""),
                    key_message=section_data.get("key_message", ""),
                    points=section_data.get("points", []),
                )
            )

        return cls(
            title=data.get("title", ""),
            target_audience=data.get("target_audience", ""),
            duration=data.get("duration", ""),
            sections=sections,
        )
