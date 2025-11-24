from enum import Enum

from ...core.schema import FactSchema, FACT_SCHEMAS, register_fact_schema


class WeatherFacts(str, Enum):
    LOCATION = "demo.weather.location"
    TEMPERATURE_F = "demo.weather.temperature_f"
    PRECIP_PROBABILITY = "demo.weather.precip_probability"
    WARDROBE = "demo.weather.wardrobe"
    UMBRELLA_NEEDED = "demo.weather.umbrella_needed"


def register_weather_schemas() -> None:
    if WeatherFacts.LOCATION not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(WeatherFacts.LOCATION, py_type=str, description="City or region to look up"),
        )
    if WeatherFacts.TEMPERATURE_F not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                WeatherFacts.TEMPERATURE_F,
                py_type=float,
                description="Forecasted high temperature in Fahrenheit",
                normalize=lambda value: float(value),
            )
        )
    if WeatherFacts.PRECIP_PROBABILITY not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                WeatherFacts.PRECIP_PROBABILITY,
                py_type=float,
                description="Chance of precipitation as a probability between 0 and 1",
                normalize=lambda value: max(0.0, min(1.0, float(value))),
            )
        )
    if WeatherFacts.WARDROBE not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                WeatherFacts.WARDROBE,
                py_type=str,
                description="Suggested outfit description based on conditions",
            )
        )
    if WeatherFacts.UMBRELLA_NEEDED not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                WeatherFacts.UMBRELLA_NEEDED,
                py_type=bool,
                description="Whether to pack an umbrella",
                normalize=bool,
            )
        )
