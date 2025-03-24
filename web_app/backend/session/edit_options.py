from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class EditOptions:
    """Options and results for the script editing step."""

    edit_options: List[str] = field(default_factory=list)
    additional_instructions: str = field(default="")
    edited_script: str = field(default="")
    is_complete: bool = field(default=False)

    @classmethod
    def from_dict(cls, data: dict) -> "EditOptions":
        """Create an EditOptions instance from a dictionary."""
        if not data:
            return cls()

        return cls(
            edit_options=data.get("edit_options", []),
            additional_instructions=data.get("additional_instructions", ""),
            edited_script=data.get("edited_script", ""),
            is_complete=data.get("is_complete", False),
        )
