# Weather planner demo walkthrough

This scenario highlights how a single location fact can drive a multi-step chain: a weather lookup followed by wardrobe advice.

## Steps
1. Provide `demo.weather.location` (for example `Seattle`).
2. Request `demo.weather.wardrobe` and `demo.weather.umbrella_needed` as required facts.
3. The planner first resolves `demo.weather.temperature_f` and `demo.weather.precip_probability` and then maps them to the wardrobe and umbrella guidance.
4. The final response returns the resolved facts plus the executed resolver trace, showing the vector of dependencies.

## What to expect
- Cooler or rainy cities suggest a "Light jacket" and an umbrella, while hot/dry inputs come back with a simple `T-shirt` recommendation.
- The trace lists `WeatherLookupResolver` followed by `WardrobePlannerResolver`, making it clear how intermediate weather facts flow into wardrobe choices.
