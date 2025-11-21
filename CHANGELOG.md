# Changelog

## Current Branch
- Add initial resolver-engine core framework with schema registration, merge semantics, planner, caching, and FastAPI API.
- Introduce demo user system schemas and resolvers plus UI utilities and history handling helper.
- Provide comprehensive pytest suite derived from `tests_meta.md` covering core, demo, API, UI, caching, and invariants.
- Rename the shared execution context to `ResolutionContext` for clarity and align tests/build with the new name.
- Normalize FastAPI `/api/run` responses so DuckDB relations serialize cleanly for documentation and browser consumers.
- Add Playwright-based Demo UI guides with screenshots for the demo user system and vector-to-scalar transition flows.
- Keep the Demo UI screenshots inline as base64 data URIs so the docs stay self-contained without binary assets while rendering in GitHub clients.
- Expand the Demo UI docs with multi-step (entry, selection, progress, results) Playwright captures and add a demo app entrypoint that pre-registers demo schemas/resolvers for live runs.
- Rename the Demo UI documentation folder and clean up binary assets now that the inline base64 embeddings display correctly on GitHub.
