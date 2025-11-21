# Changelog

## Current Branch
- Add initial resolver-engine core framework with schema registration, merge semantics, planner, caching, and FastAPI API.
- Introduce demo user system schemas and resolvers plus UI utilities and history handling helper.
- Provide comprehensive pytest suite derived from `tests_meta.md` covering core, demo, API, UI, caching, and invariants.
- Rename the shared execution context to `ResolutionContext` for clarity and align tests/build with the new name.
