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
- Add Mermaid diagrams that summarize the demo UI screenshots and the shared user story flow for scalar and vector runs.
- Refresh Demo UI guides after reviewing a new Playwright capture of `/`, replacing inline base64 embeds with concise text and updated Mermaid diagrams that match the current helper form layout.
- Convert the `/` helper into an interactive schema-driven runner with a required-facts field, inline `/api/run` execution, and refreshed Demo UI documentation to match.
