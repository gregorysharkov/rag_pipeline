from dataclasses import dataclass, field
from typing import Optional, List, Union, Dict

from .reference_file import ReferenceFile
from .web_link import WebLink
from .web_search_result import WebSearchResult
from .plan import Plan
from .edit_options import EditOptions
from .shorts_options import ShortsOptions


@dataclass
class ScriptSession:
    """Class for storing session data."""

    topic: str = field(default="")
    additional_context: str = field(default="")
    target_audience: str = field(default="")
    content_type: str = field(default="")
    tone: str = field(default="")
    use_web_search: bool = field(default=True)
    reference_files: List[dict] = field(default_factory=list)
    web_links: List[WebLink] = field(default_factory=list)
    web_search_results: List[WebSearchResult] = field(default_factory=list)
    selected_search_results: List[str] = field(default_factory=list)  # IDs of selected results
    web_search_viewed: bool = field(default=False)
    plan: Optional[Plan] = field(default=None)
    video_title: str = field(default="")
    video_audience: str = field(default="")
    video_duration: str = field(default="")
    script_sections: List[dict] = field(default_factory=list)
    script_complete: bool = field(default=False)
    edit_options: EditOptions = field(default_factory=EditOptions)
    shorts_options: ShortsOptions = field(default_factory=ShortsOptions)

    def as_dict(self) -> Dict:
        """Convert to dictionary."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if hasattr(field_value, "as_dict"):
                result[field_name] = field_value.as_dict()
            elif (
                isinstance(field_value, list) and field_value and hasattr(field_value[0], "as_dict")
            ):
                result[field_name] = [item.as_dict() for item in field_value]
            else:
                result[field_name] = field_value
        return result
