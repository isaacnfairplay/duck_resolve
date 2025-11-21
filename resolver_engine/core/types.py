from enum import Enum
from dataclasses import dataclass, field
from typing import Any, List, Optional


class FactStatus(Enum):
    SOLID = "solid"
    AMBIGUOUS = "ambiguous"
    CONFLICT = "conflict"


@dataclass
class FactValue:
    fact_id: Any
    value: Any
    status: FactStatus = FactStatus.SOLID
    provenance: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    confidence: float = 1.0
