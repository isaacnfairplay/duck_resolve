from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class FactSchema:
    fact_id: Any
    py_type: type
    description: str
    normalize: Callable[[Any], Any] | None = None
    allow_ambiguity: bool = False

    def apply_normalization(self, value: Any) -> Any:
        if self.normalize:
            return self.normalize(value)
        return value


FACT_SCHEMAS: Dict[Any, FactSchema] = {}


def register_fact_schema(schema: FactSchema):
    if schema.fact_id in FACT_SCHEMAS:
        raise ValueError(f"Schema for {schema.fact_id} already registered")
    FACT_SCHEMAS[schema.fact_id] = schema
    return schema
