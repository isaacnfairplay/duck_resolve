# Changelog

## Current Branch
- Add initial resolver-engine core framework with schema registration, merge semantics, planner, caching, and FastAPI API.
- Introduce demo user system schemas and resolvers plus UI utilities and history handling helper.
- Provide comprehensive pytest suite derived from `tests_meta.md` covering core, demo, API, UI, caching, and invariants.
- Rename the shared execution context to `ResolutionContext` for clarity and align tests/build with the new name.
- Normalize FastAPI `/api/run` responses so DuckDB relations serialize cleanly for documentation and browser consumers.
- Add Playwright-based Demo UI guides with screenshots for the demo user system and vector-to-scalar transition flows.
- Wrap the inline base64 Demo UI screenshots in HTML figure blocks so GitHub renders them directly without odd redirects.
- Keep the Demo UI docs self-contained by removing the temporary PNG assets while preserving the multi-step Playwright captures.
- Rename the Demo UI documentation folder and clean up binary assets now that the inline base64 embeddings display correctly on GitHub.
- Add two additional demos (weather planner and support triage) with schemas, resolvers, tests, and UI walkthroughs registered in the FastAPI app.
- Add a pull-request workflow that uses Playwright to regenerate demo markdowns with linked screenshots instead of base64 embeds.
- Refresh the built-in FastAPI UI with a structured layout, themed styling, and in-browser planner execution controls.
- Move the FastAPI UI into packaged templates/assets and add table-friendly relation inputs so DuckDB facts can be provided as structured rows.
- Replace relation JSON textareas with an interactive table builder, keeping a JSON fallback for power users while guiding everyone else toward structured rows.
- Add Playwright-powered UI interaction tests that exercise the relation table builder workflows.
- Escape fact metadata before injecting it into the playground templates and extend Playwright coverage to verify clearing relation rows resets previews and JSON.
