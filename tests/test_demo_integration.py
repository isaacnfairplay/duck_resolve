from resolver_engine.demos.demo_user_system.schemas import register_demo_schemas, DemoFacts
from resolver_engine.demos.demo_user_system import resolvers as demo_resolvers
from resolver_engine.core.schema import FACT_SCHEMAS
from resolver_engine.core.resolver_base import RESOLVER_REGISTRY
from resolver_engine.core.state import ResolutionContext
from resolver_engine.core.planner import Planner
def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()
    demo_resolvers.registered = False


def test_demo_plugin_registers_fact_schemas_at_startup():
    register_demo_schemas()
    assert DemoFacts.USER_NAME in FACT_SCHEMAS
    assert DemoFacts.USER_ID in FACT_SCHEMAS
    assert DemoFacts.FAVORITE_COLOR in FACT_SCHEMAS


def test_demo_resolver_registration():
    register_demo_schemas()
    demo_resolvers.register_demo_resolvers()

    assert any("UserIdResolver" == name for name in RESOLVER_REGISTRY)
    resolver = RESOLVER_REGISTRY.get("UserIdResolver")
    assert resolver
    assert DemoFacts.USER_ID in resolver.spec.output_facts


def test_demo_end_to_end_smt_like_flow():
    register_demo_schemas()
    demo_resolvers.register_demo_resolvers()

    ctx = ResolutionContext()
    # provide base fact user name
    from resolver_engine.core.merge import merge_outputs
    from resolver_engine.core.resolver_base import ResolverOutput

    merge_outputs(ctx, [ResolverOutput(DemoFacts.USER_NAME, "Alice")])

    planner = Planner(required_facts={DemoFacts.USER_ID, DemoFacts.FAVORITE_COLOR}, user_priority={})
    result = planner.run(ctx)

    assert DemoFacts.USER_ID in ctx.state
    assert DemoFacts.FAVORITE_COLOR in ctx.state
    assert set(result.executed_resolvers)
