from dataclasses import dataclass, field
from typing import Any, Dict

from .types import FactValue


@dataclass
class LineContext:
    state: Dict[Any, FactValue] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add_trace(self, entry: str):
        self.trace.append(entry)
