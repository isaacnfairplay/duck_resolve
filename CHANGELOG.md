# Changelog

## Current Branch
- Add initial resolver-engine core framework with schema registration, merge semantics, planner, caching, and FastAPI API.
- Introduce demo user system schemas and resolvers plus UI utilities and history handling helper.
- Provide comprehensive pytest suite derived from `tests_meta.md` covering core, demo, API, UI, caching, and invariants.
- Rename the shared execution context to `ResolutionContext` for clarity and align tests/build with the new name.
- Add a vectorized-to-scalar demo that processes DuckDB relations, refines a representative user, and roundtrips back to a
  relation to illustrate mixed execution modes.
- Clarify that the vector-scalar demo's DuckDB relations are in-process conveniences and adopt ``StrEnum`` for its fact keys.
- Support parquet/Arrow batch inputs in the vector-scalar demo to prefer portable interchange over in-process relations.
