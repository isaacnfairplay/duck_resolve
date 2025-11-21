import pytest
from enum import Enum

from resolver_engine.core.schema import FactSchema, register_fact_schema, FACT_SCHEMAS
from resolver_engine.core.state import ResolutionContext
from resolver_engine.core.merge import merge_outputs
from resolver_engine.core.resolver_base import ResolverOutput
from resolver_engine.core.types import FactStatus


class DemoFacts(str, Enum):
    USER_NAME = "demo.user_name"
    UNKNOWN_KEY = "demo.unknown"


def setup_function(function):
    FACT_SCHEMAS.clear()


def test_register_fact_schema_success():
    schema = FactSchema(
        fact_id=DemoFacts.USER_NAME,
        py_type=str,
        normalize=lambda v: v.strip(),
        description="User name",
    )

    register_fact_schema(schema)

    assert DemoFacts.USER_NAME in FACT_SCHEMAS
    stored = FACT_SCHEMAS[DemoFacts.USER_NAME]
    assert stored.fact_id == DemoFacts.USER_NAME
    assert stored.py_type is str
    assert stored.description == "User name"
    assert stored.normalize(" test ") == "test"


def test_register_fact_schema_twice_raises():
    schema = FactSchema(
        fact_id=DemoFacts.USER_NAME,
        py_type=str,
        normalize=lambda v: v,
        description="User name",
    )
    register_fact_schema(schema)

    with pytest.raises(ValueError):
        register_fact_schema(schema)


def test_accessing_unregistered_fact_raises():
    ctx = ResolutionContext()

    with pytest.raises(KeyError):
        merge_outputs(ctx, [ResolverOutput(DemoFacts.UNKNOWN_KEY, "x")])


def test_fact_schema_normalization_applied_on_merge():
    schema = FactSchema(
        fact_id=DemoFacts.USER_NAME,
        py_type=str,
        normalize=lambda v: v.strip().lower(),
        description="User name",
    )
    register_fact_schema(schema)
    ctx = ResolutionContext()

    merge_outputs(ctx, [ResolverOutput(DemoFacts.USER_NAME, "  Alice  ")])

    assert ctx.state[DemoFacts.USER_NAME].value == "alice"
    assert ctx.state[DemoFacts.USER_NAME].status is FactStatus.SOLID
