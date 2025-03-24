from dataclasses import dataclass, field


@dataclass
class ReferenceFile:
    filename: str
    content: str
    original_name: str = field(default="")
    stored_name: str = field(default="")
