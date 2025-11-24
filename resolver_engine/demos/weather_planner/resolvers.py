from typing import List

from ...core.resolver_base import BaseResolver, ResolverOutput, ResolverSpec
from ...core.state import ResolutionContext
from .schemas import WeatherFacts


registered = False

WEATHER_DB = {
    "seattle": {"temperature": 58.0, "precip": 0.68},
    "phoenix": {"temperature": 88.0, "precip": 0.05},
    "new york": {"temperature": 72.0, "precip": 0.32},
}


def register_weather_resolvers() -> None:
    global registered
    if registered:
        return

    @BaseResolver.register(
        ResolverSpec(
            name="WeatherLookupResolver",
            description="Look up forecasted weather for a location",
            input_facts={WeatherFacts.LOCATION},
            output_facts={WeatherFacts.TEMPERATURE_F, WeatherFacts.PRECIP_PROBABILITY},
            impact={WeatherFacts.TEMPERATURE_F: 0.6, WeatherFacts.PRECIP_PROBABILITY: 0.4},
        )
    )
    class WeatherLookupResolver(BaseResolver):
        def run(self, ctx: ResolutionContext) -> List[ResolverOutput]:
            location = str(ctx.state[WeatherFacts.LOCATION].value).lower().strip()
            forecast = WEATHER_DB.get(location, {"temperature": 70.0, "precip": 0.15})
            return [
                ResolverOutput(WeatherFacts.TEMPERATURE_F, forecast["temperature"], source="demo.weather"),
                ResolverOutput(WeatherFacts.PRECIP_PROBABILITY, forecast["precip"], source="demo.weather"),
            ]

    @BaseResolver.register(
        ResolverSpec(
            name="WardrobePlannerResolver",
            description="Recommend clothing and umbrella choice based on forecast",
            input_facts={WeatherFacts.TEMPERATURE_F, WeatherFacts.PRECIP_PROBABILITY},
            output_facts={WeatherFacts.WARDROBE, WeatherFacts.UMBRELLA_NEEDED},
            impact={WeatherFacts.WARDROBE: 0.5, WeatherFacts.UMBRELLA_NEEDED: 0.7},
        )
    )
    class WardrobePlannerResolver(BaseResolver):
        def run(self, ctx: ResolutionContext) -> List[ResolverOutput]:
            temperature = float(ctx.state[WeatherFacts.TEMPERATURE_F].value)
            precip = float(ctx.state[WeatherFacts.PRECIP_PROBABILITY].value)
            if temperature < 50:
                outfit = "Warm coat and layers"
            elif temperature < 70:
                outfit = "Light jacket"
            else:
                outfit = "T-shirt"
            umbrella = precip >= 0.5
            return [
                ResolverOutput(WeatherFacts.WARDROBE, outfit, source="demo.weather"),
                ResolverOutput(WeatherFacts.UMBRELLA_NEEDED, umbrella, source="demo.weather"),
            ]

    registered = True
