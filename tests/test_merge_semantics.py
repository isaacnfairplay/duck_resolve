from enum import Enum

from resolver_engine.core.schema import FactSchema, FACT_SCHEMAS, register_fact_schema
from resolver_engine.core.state import ResolutionContext
from resolver_engine.core.merge import merge_outputs
from resolver_engine.core.resolver_base import ResolverOutput
from resolver_engine.core.types import FactStatus


class DemoFacts(str, Enum):
    FOO = "demo.foo"


def setup_function(function):
    FACT_SCHEMAS.clear()


def test_merge_creates_solid_value_when_empty():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    ctx = ResolutionContext()

    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "x", source="r1")])

    fact = ctx.state[DemoFacts.FOO]
    assert fact.status is FactStatus.SOLID
    assert fact.value == "x"
    assert fact.provenance == ["r1"]


def test_merge_same_value_updates_provenance_but_not_ambiguous():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    ctx = ResolutionContext()
    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "x", source="r1")])

    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "x", source="r2")])

    fact = ctx.state[DemoFacts.FOO]
    assert fact.status is FactStatus.SOLID
    assert fact.value == "x"
    assert fact.provenance == ["r1", "r2"]


def test_merge_different_values_becomes_ambiguous_if_allowed():
    register_fact_schema(
        FactSchema(DemoFacts.FOO, py_type=str, description="foo", allow_ambiguity=True)
    )
    ctx = ResolutionContext()
    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "x", source="r1")])

    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "y", source="r2")])

    fact = ctx.state[DemoFacts.FOO]
    assert fact.status is FactStatus.AMBIGUOUS
    assert set(fact.value) == {"x", "y"}
    assert fact.provenance == ["r1", "r2"]


def test_merge_disallowed_ambiguity_becomes_conflict():
    register_fact_schema(
        FactSchema(DemoFacts.FOO, py_type=str, description="foo", allow_ambiguity=False)
    )
    ctx = ResolutionContext()
    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "x", source="r1")])

    merge_outputs(ctx, [ResolverOutput(DemoFacts.FOO, "y", source="r2")])

    fact = ctx.state[DemoFacts.FOO]
    assert fact.status is FactStatus.CONFLICT
    assert "x" in fact.value and "y" in fact.value


def test_merge_preserves_notes_and_confidence():
    register_fact_schema(FactSchema(DemoFacts.FOO, py_type=str, description="foo"))
    ctx = ResolutionContext()
    merge_outputs(
        ctx,
        [ResolverOutput(DemoFacts.FOO, "x", source="r1", note="first", confidence=0.6)],
    )

    merge_outputs(
        ctx,
        [ResolverOutput(DemoFacts.FOO, "x", source="r2", note="second", confidence=0.9)],
    )

    fact = ctx.state[DemoFacts.FOO]
    assert "first" in fact.notes and "second" in fact.notes
    assert fact.confidence == 0.9
