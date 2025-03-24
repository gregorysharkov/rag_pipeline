from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ShortsOptions:
    """Options and results for the YouTube Shorts generation step."""

    shorts_count: int = field(default=3)
    shorts_duration: int = field(default=30)
    shorts_focus: List[str] = field(default_factory=list)
    generated_shorts: List[dict] = field(default_factory=list)
    is_complete: bool = field(default=False)

    def get_shorts_data(self) -> List[str]:
        """Get a list of formatted shorts content for the template."""
        if not self.generated_shorts:
            return []

        # Convert generated_shorts to list of content strings for backward compatibility
        return [short.get("content", "") for short in self.generated_shorts if short.get("content")]

    @classmethod
    def from_dict(cls, data: dict) -> "ShortsOptions":
        """Create a ShortsOptions instance from a dictionary."""
        if not data:
            return cls()

        return cls(
            shorts_count=data.get("shorts_count", 3),
            shorts_duration=data.get("shorts_duration", 30),
            shorts_focus=data.get("shorts_focus", []),
            generated_shorts=data.get("generated_shorts", []),
            is_complete=data.get("is_complete", False),
        )
