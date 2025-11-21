from enum import Enum

from resolver_engine.core.schema import FactSchema, FACT_SCHEMAS, register_fact_schema
from resolver_engine.core.resolver_base import BaseResolver, ResolverSpec, ResolverOutput, RESOLVER_REGISTRY
from resolver_engine.core.planner import Planner
from resolver_engine.core.state import LineContext
from resolver_engine.core.merge import merge_outputs


class DemoFacts(str, Enum):
    FOO = "demo.foo"
    BAR = "demo.bar"


def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()


def test_planner_runs_minimal_resolvers_to_satisfy_single_fact():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))

    spec_a = ResolverSpec(
        name="ResA",
        description="cheap",
        input_facts=set(),
        output_facts={DemoFacts.FOO},
        cost=1,
        impact={DemoFacts.FOO: 0.5},
    )
    spec_b = ResolverSpec(
        name="ResB",
        description="expensive",
        input_facts=set(),
        output_facts={DemoFacts.FOO},
        cost=10,
        impact={DemoFacts.FOO: 0.6},
    )

    @BaseResolver.register(spec_a)
    class ResA(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "a")]

    @BaseResolver.register(spec_b)
    class ResB(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "b")]

    ctx = LineContext()
    planner = Planner(required_facts={DemoFacts.FOO}, user_priority={DemoFacts.FOO: 1.0})
    result = planner.run(ctx)

    assert DemoFacts.FOO in ctx.state
    assert result.executed_resolvers == ["ResB"] or result.executed_resolvers == ["ResA"]
    # ensure cheaper per impact should be chosen; impact/cost better ResA (0.5) vs ResB (0.06)
    assert result.executed_resolvers[0] == "ResA"


def test_planner_respects_required_facts():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    register_fact_schema(FactSchema(DemoFacts.BAR, py_type=str, description="bar"))

    @BaseResolver.register(
        ResolverSpec(
            name="ResFoo",
            description="foo",
            input_facts=set(),
            output_facts={DemoFacts.FOO},
            impact={DemoFacts.FOO: 1.0},
        )
    )
    class ResFoo(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "foo")]

    @BaseResolver.register(
        ResolverSpec(
            name="ResBar",
            description="bar",
            input_facts={DemoFacts.FOO},
            output_facts={DemoFacts.BAR},
            impact={DemoFacts.BAR: 1.0},
        )
    )
    class ResBar(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.BAR, ctx.state[DemoFacts.FOO].value + "bar")]

    ctx = LineContext()
    planner = Planner(required_facts={DemoFacts.FOO, DemoFacts.BAR}, user_priority={})
    result = planner.run(ctx)

    assert set(result.executed_resolvers) == {"ResFoo", "ResBar"}
    assert DemoFacts.FOO in ctx.state and DemoFacts.BAR in ctx.state


def test_planner_stops_when_no_more_eligible_resolvers():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    register_fact_schema(FactSchema(DemoFacts.BAR, py_type=str, description="bar"))

    @BaseResolver.register(
        ResolverSpec(
            name="NeedsMissing",
            description="needs missing",
            input_facts={DemoFacts.BAR},
            output_facts={DemoFacts.FOO},
            impact={DemoFacts.FOO: 1.0},
        )
    )
    class NeedsMissing(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "foo")]

    ctx = LineContext()
    planner = Planner(required_facts=set(), user_priority={})
    result = planner.run(ctx)

    assert result.executed_resolvers == []
    assert DemoFacts.FOO not in ctx.state


def test_planner_uses_impact_and_cost_in_scheduling():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))

    @BaseResolver.register(
        ResolverSpec(
            name="CheapLowImpact",
            description="cheap",
            input_facts=set(),
            output_facts={DemoFacts.FOO},
            cost=10,
            impact={DemoFacts.FOO: 0.1},
        )
    )
    class CheapLowImpact(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "cheap")]

    @BaseResolver.register(
        ResolverSpec(
            name="ExpensiveHighImpact",
            description="expensive",
            input_facts=set(),
            output_facts={DemoFacts.FOO},
            cost=30,
            impact={DemoFacts.FOO: 0.9},
        )
    )
    class ExpensiveHighImpact(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "expensive")]

    ctx = LineContext()
    planner = Planner(required_facts={DemoFacts.FOO}, user_priority={DemoFacts.FOO: 1.0})
    result = planner.run(ctx)

    assert result.executed_resolvers
    assert result.executed_resolvers[0] == "ExpensiveHighImpact"
