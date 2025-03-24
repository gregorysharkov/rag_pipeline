from dataclasses import dataclass, field


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str
    id: str = field(default="")
