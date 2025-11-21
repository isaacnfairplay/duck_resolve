from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Set

from .resolver_base import RESOLVER_REGISTRY, BaseResolver
from .merge import merge_outputs
from .state import LineContext


@dataclass
class PlannerResult:
    executed_resolvers: List[str] = field(default_factory=list)


class Planner:
    def __init__(self, required_facts: Set[Any], user_priority: Dict[Any, float]):
        self.required_facts = set(required_facts)
        self.user_priority = user_priority

    def _score_resolver(self, resolver: BaseResolver) -> float:
        impact = sum(
            resolver.spec.impact.get(fid, 0) * self.user_priority.get(fid, 1.0)
            for fid in resolver.spec.output_facts
        )
        cost = resolver.spec.cost if resolver.spec.cost else 1.0
        return impact / cost

    def run(self, ctx: LineContext) -> PlannerResult:
        executed: List[str] = []
        pending = set(RESOLVER_REGISTRY.keys())

        while True:
            # stop if required satisfied
            if self.required_facts and self.required_facts.issubset(ctx.state.keys()):
                break

            eligible = [
                RESOLVER_REGISTRY[name]
                for name in list(pending)
                if RESOLVER_REGISTRY[name].can_run(ctx)
            ]
            if not eligible:
                break
            # pick best by score
            best = max(eligible, key=self._score_resolver)
            pending.remove(best.spec.name)
            outputs = best.execute(ctx)
            merge_outputs(ctx, outputs)
            executed.append(best.spec.name)

        return PlannerResult(executed_resolvers=executed)
