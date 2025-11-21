from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Set

from .state import ResolutionContext
from .types import FactStatus, FactValue
from .merge import merge_outputs


RESOLVER_REGISTRY: Dict[str, "BaseResolver"] = {}


@dataclass
class ResolverOutput:
    fact_id: Any
    value: Any
    source: str | None = None
    note: str | None = None
    confidence: float = 1.0


@dataclass
class ResolverSpec:
    name: str
    description: str
    input_facts: Set[Any]
    output_facts: Set[Any]
    impact: Dict[Any, float]
    cost: float = 1.0
    cache_policy: Any | None = None


class BaseResolver:
    spec: ResolverSpec

    @classmethod
    def register(cls, spec: ResolverSpec):
        def decorator(resolver_cls):
            resolver_cls.spec = spec
            RESOLVER_REGISTRY[spec.name] = resolver_cls()
            return resolver_cls

        return decorator

    def can_run(self, ctx: ResolutionContext) -> bool:
        return all(fact_id in ctx.state for fact_id in self.spec.input_facts)

    def run(self, ctx: ResolutionContext) -> Iterable[ResolverOutput]:  # pragma: no cover - abstract
        raise NotImplementedError

    def execute(self, ctx: ResolutionContext, provided_inputs: Optional[Iterable[ResolverOutput]] = None):
        provided_ids = set()
        if provided_inputs:
            for output in provided_inputs:
                provided_ids.add(output.fact_id)
                ctx.state[output.fact_id] = FactValue(
                    fact_id=output.fact_id,
                    value=output.value,
                    status=FactStatus.SOLID,
                    provenance=[output.source] if output.source else [],
                    confidence=output.confidence,
                    notes=[output.note] if output.note else [],
                )
        if self.spec.cache_policy:
            cache_key = self.spec.cache_policy.build_cache_key(ctx, self.spec)
            cached = self.spec.cache_policy.fetch(cache_key)
            if cached is not None:
                for fid in provided_ids:
                    if fid in self.spec.output_facts:
                        ctx.state.pop(fid, None)
                return cached
        outputs = list(self.run(ctx))
        if self.spec.cache_policy:
            cache_key = self.spec.cache_policy.build_cache_key(ctx, self.spec)
            self.spec.cache_policy.store(cache_key, outputs)
        for fid in provided_ids:
            if fid in self.spec.output_facts:
                ctx.state.pop(fid, None)
        return outputs
