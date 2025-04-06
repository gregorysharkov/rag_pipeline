import json
import re
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class CollectedInformation:
    title: str
    url: str
    summary: str
    collector_func: Callable
    content: Optional[str] = None

    def fetch_content(self) -> str:
        self.content = self.collector_func(self.url)

    def __str__(self) -> str:
        return (
            f"Collected_item\n"
            f"\tTitle: {self.title}\n"
            f"\tURL: {self.url}\n"
            f"\tSummary: {self.summary}\n"
            f"\tContent: {self.content[:100]}...\n"
        )

    def _generate_file_name(self, title: str) -> str:
        file_name = title.lower()
        file_name = re.sub(r"[^a-z0-9]+", " ", file_name)
        file_name = re.sub(r"\s+", "_", file_name)
        max_len = 30
        file_name = file_name[: min(len(file_name), max_len)]
        return file_name

    def dump_string(self, base_path: str) -> None:
        file_name = self._generate_file_name(self.title)
        with open(f"{base_path}/{file_name}.txt", "w") as f:
            f.write(str(self))

    def dump_json(self, base_path: str) -> None:
        file_name = self._generate_file_name(self.title)
        with open(f"{base_path}/{file_name}.json", "w") as f:
            json.dump(self, f)
