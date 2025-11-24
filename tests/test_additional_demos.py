from resolver_engine.core.merge import merge_outputs
from resolver_engine.core.planner import Planner
from resolver_engine.core.resolver_base import RESOLVER_REGISTRY, ResolverOutput
from resolver_engine.core.schema import FACT_SCHEMAS
from resolver_engine.core.state import ResolutionContext
from resolver_engine.demos.weather_planner.schemas import WeatherFacts, register_weather_schemas
from resolver_engine.demos.weather_planner import resolvers as weather_resolvers
from resolver_engine.demos.support_triage.schemas import SupportFacts, register_support_schemas
from resolver_engine.demos.support_triage import resolvers as support_resolvers


def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()
    weather_resolvers.registered = False
    support_resolvers.registered = False


def test_weather_demo_flow():
    register_weather_schemas()
    weather_resolvers.register_weather_resolvers()

    ctx = ResolutionContext()
    merge_outputs(ctx, [ResolverOutput(WeatherFacts.LOCATION, "Seattle", source="demo.input")])

    planner = Planner(required_facts={WeatherFacts.WARDROBE, WeatherFacts.UMBRELLA_NEEDED}, user_priority={})
    planner.run(ctx)

    assert WeatherFacts.TEMPERATURE_F in ctx.state
    assert WeatherFacts.PRECIP_PROBABILITY in ctx.state
    assert ctx.state[WeatherFacts.WARDROBE].value == "Light jacket"
    assert ctx.state[WeatherFacts.UMBRELLA_NEEDED].value is True


def test_support_triage_demo_flow():
    register_support_schemas()
    support_resolvers.register_support_resolvers()

    ctx = ResolutionContext()
    merge_outputs(
        ctx,
        [ResolverOutput(SupportFacts.INCIDENT_SUMMARY, "Site outage for multiple users", source="demo.input")],
    )

    planner = Planner(
        required_facts={SupportFacts.ASSIGNED_TEAM, SupportFacts.ETA_DAYS, SupportFacts.CUSTOMER_IMPACT},
        user_priority={},
    )
    planner.run(ctx)

    assert ctx.state[SupportFacts.SEVERITY].value == "critical"
    assert ctx.state[SupportFacts.ASSIGNED_TEAM].value == "SRE"
    assert ctx.state[SupportFacts.ETA_DAYS].value == 1
