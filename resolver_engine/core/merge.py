from typing import Iterable, TYPE_CHECKING, Any

from .schema import FACT_SCHEMAS
from .types import FactStatus, FactValue
from .state import ResolutionContext

if TYPE_CHECKING:  # pragma: no cover
    from .resolver_base import ResolverOutput


def merge_outputs(ctx: ResolutionContext, outputs: Iterable[Any]):
    for output in outputs:
        fact_id = output.fact_id
        if fact_id not in FACT_SCHEMAS:
            raise KeyError(f"Schema for {fact_id} not registered")
        schema = FACT_SCHEMAS[fact_id]
        normalized = schema.apply_normalization(output.value)

        if fact_id not in ctx.state:
            ctx.state[fact_id] = FactValue(
                fact_id=fact_id,
                value=normalized,
                status=FactStatus.SOLID,
                provenance=[output.source] if output.source else [],
                notes=[output.note] if output.note else [],
                confidence=output.confidence,
            )
            continue

        existing = ctx.state[fact_id]
        # same value
        if existing.value == normalized or (
            isinstance(existing.value, list) and normalized in existing.value
        ):
            existing.provenance += [output.source] if output.source else []
            if output.note:
                existing.notes.append(output.note)
            existing.confidence = max(existing.confidence, output.confidence)
            continue

        # conflict or ambiguity
        if schema.allow_ambiguity:
            values = existing.value if isinstance(existing.value, list) else [existing.value]
            if normalized not in values:
                values.append(normalized)
            existing.value = values
            existing.status = FactStatus.AMBIGUOUS
        else:
            values = existing.value if isinstance(existing.value, list) else [existing.value]
            if normalized not in values:
                values.append(normalized)
            existing.value = values
            existing.status = FactStatus.CONFLICT
        existing.provenance += [output.source] if output.source else []
        if output.note:
            existing.notes.append(output.note)
        existing.confidence = max(existing.confidence, output.confidence)

    return ctx
