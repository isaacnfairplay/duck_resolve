from enum import Enum

from resolver_engine.core.schema import FACT_SCHEMAS, FactSchema, register_fact_schema
from resolver_engine.core.resolver_base import BaseResolver, ResolverSpec, ResolverOutput, RESOLVER_REGISTRY
from resolver_engine.core.state import LineContext
from resolver_engine.core.merge import merge_outputs


class DemoFacts(str, Enum):
    FOO = "demo.foo"
    BAR = "demo.bar"


def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()


def test_register_resolver_populates_registry():
    spec = ResolverSpec(
        name="DummyResolver",
        description="dummy",
        input_facts=set(),
        output_facts={DemoFacts.FOO},
        impact={DemoFacts.FOO: 1.0},
    )

    @BaseResolver.register(spec)
    class DummyResolver(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.FOO, "value")]

    assert "DummyResolver" in RESOLVER_REGISTRY
    assert RESOLVER_REGISTRY["DummyResolver"].spec == spec


def test_resolver_cannot_run_without_inputs():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    spec = ResolverSpec(
        name="NeedsFoo",
        description="needs foo",
        input_facts={DemoFacts.FOO},
        output_facts={DemoFacts.BAR},
        impact={DemoFacts.BAR: 1.0},
    )

    @BaseResolver.register(spec)
    class NeedsFoo(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.BAR, "bar")]

    ctx = LineContext()
    resolver = RESOLVER_REGISTRY["NeedsFoo"]
    assert resolver.can_run(ctx) is False


def test_resolver_run_returns_outputs_respected_by_merge():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    register_fact_schema(FactSchema(DemoFacts.BAR, py_type=str, description="bar"))

    spec = ResolverSpec(
        name="MakeBar",
        description="makes bar",
        input_facts={DemoFacts.FOO},
        output_facts={DemoFacts.BAR},
        impact={DemoFacts.BAR: 1.0},
    )

    @BaseResolver.register(spec)
    class MakeBar(BaseResolver):
        def run(self, ctx: LineContext):
            return [ResolverOutput(DemoFacts.BAR, ctx.state[DemoFacts.FOO].value + "bar")]

    ctx = LineContext()
    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "foo")])

    resolver = RESOLVER_REGISTRY["MakeBar"]
    assert resolver.can_run(ctx)
    outputs = resolver.run(ctx)
    merge_outputs(ctx, outputs)

    assert ctx.state[DemoFacts.BAR].value == "foobar"
