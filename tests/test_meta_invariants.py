from resolver_engine.core.schema import FACT_SCHEMAS
from resolver_engine.core.resolver_base import RESOLVER_REGISTRY
from resolver_engine.demos.demo_user_system.schemas import register_demo_schemas
from resolver_engine.demos.demo_user_system import resolvers as demo_resolvers


def setup_module(module):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()
    register_demo_schemas()
    demo_resolvers.register_demo_resolvers()


def test_all_registered_facts_have_schemas():
    missing = []
    for resolver in RESOLVER_REGISTRY.values():
        for fact_id in resolver.spec.input_facts | resolver.spec.output_facts:
            if fact_id not in FACT_SCHEMAS:
                missing.append(fact_id)
    assert not missing, f"Missing schemas for: {missing}"


def test_no_duplicate_resolver_names():
    names = list(RESOLVER_REGISTRY.keys())
    assert len(names) == len(set(names))


def test_resolver_specs_have_impact_entries_for_all_output_facts():
    for resolver in RESOLVER_REGISTRY.values():
        missing = [f for f in resolver.spec.output_facts if f not in resolver.spec.impact]
        assert not missing, f"Resolver {resolver.spec.name} missing impact for {missing}"
