# tests_meta.md

This document describes the **test plan** and **test cases** for the `resolver-engine` core library and its demo projects.

We will use **test-driven development (TDD)**. The implementation work will follow the structure of this file: for each section, we write tests first, then implement or adjust the library to make tests pass.

The top-level areas:

1. Core Fact & Schema Registration
2. Fact Value & Merge Semantics
3. Resolver Interface & Registry
4. Planner & Expected-Value Scheduling
5. Caching (SQLite / Parquet)
6. Web API (FastAPI) & Rate Limiting
7. Demo Plugin Integration (User System Demo)
8. UI / HTTP Behavior (HTML + JS)
9. Meta & Regression Tests (to protect invariants)
10. Placeholder for Future Demo Suites (20+ demos)

---

## 1. Core Fact & Schema Registration

**Goal:** Verify that fact IDs and schemas must be registered and are enforced correctly.

### 1.1 `test_register_fact_schema_success`

**Pseudocode:**

- Arrange:
  - Define a dummy `FactId` enum value `DemoFacts.USER_NAME`.
  - Create a `FactSchema` with:
    - `fact_id = DemoFacts.USER_NAME`
    - `py_type = str`
    - `normalize = lambda v: v.strip()`
    - `description = "User name"`
- Act:
  - Call `register_fact_schema(schema)`.
- Assert:
  - `FACT_SCHEMAS[DemoFacts.USER_NAME]` exists.
  - Its fields match the input.

### 1.2 `test_register_fact_schema_twice_raises`

**Pseudocode:**

- Arrange:
  - Register a schema for `DemoFacts.USER_NAME` once.
- Act:
  - Attempt to register another `FactSchema` with the same `fact_id`.
- Assert:
  - `register_fact_schema` raises `ValueError`.

### 1.3 `test_accessing_unregistered_fact_raises`

**Pseudocode:**

- Arrange:
  - Create a `ResolutionContext` with empty `state`.
  - Do **not** register any schema for `DemoFacts.UNKNOWN_KEY`.
- Act:
  - Attempt to:
    - Call a helper like `normalize_value(DemoFacts.UNKNOWN_KEY, "some")`, or
    - Use `merge_outputs` with a `ResolverOutput` referencing `DemoFacts.UNKNOWN_KEY`.
- Assert:
  - A clear exception is raised indicating missing schema for that fact ID.

### 1.4 `test_fact_schema_normalization_applied_on_merge`

**Pseudocode:**

- Arrange:
  - Register `DemoFacts.USER_NAME` with `py_type=str` and `normalize=lambda v: v.strip().lower()`.
  - Create an empty `ResolutionContext`.
- Act:
  - Call `merge_outputs` with a `ResolverOutput`:
    - `fact_id=DemoFacts.USER_NAME`
    - `value="  Alice  "`
- Assert:
  - `ctx.state[DemoFacts.USER_NAME].value == "alice"` (normalized).
  - `ctx.state[DemoFacts.USER_NAME].status == FactStatus.SOLID`.

---

## 2. Fact Value & Merge Semantics

**Goal:** Ensure FactValue and `merge_outputs` behave correctly for SOLID, AMBIGUOUS, and CONFLICT states.

### 2.1 `test_merge_creates_solid_value_when_empty`

**Pseudocode:**

- Arrange:
  - Context with empty `state`.
  - Register a simple string schema `DemoFacts.FOO`.
- Act:
  - `merge_outputs` with a single `ResolverOutput(DemoFacts.FOO, "x", source="r1")`.
- Assert:
  - `ctx.state[DemoFacts.FOO].status == FactStatus.SOLID`.
  - Value is `"x"`.
  - `provenance == ["r1"]`.
  - `confidence` equals the default from `ResolverOutput` or provided value.

### 2.2 `test_merge_same_value_updates_provenance_but_not_ambiguous`

**Pseudocode:**

- Arrange:
  - Context with `DemoFacts.FOO` already in `state`:
    - `value="x"`, `status=SOLID`, `provenance=["r1"]`.
- Act:
  - `merge_outputs` with `ResolverOutput(DemoFacts.FOO, "x", source="r2")`.
- Assert:
  - Status remains `SOLID`.
  - Value remains `"x"`.
  - `provenance` contains both `"r1"` and `"r2"`.

### 2.3 `test_merge_different_values_becomes_ambiguous_if_allowed`

**Pseudocode:**

- Arrange:
  - Schema for `DemoFacts.FOO` with `allow_ambiguity=True`.
  - Context with `DemoFacts.FOO` set to `"x"`, status `SOLID`.
- Act:
  - `merge_outputs` with `ResolverOutput(DemoFacts.FOO, "y", source="r2")`.
- Assert:
  - Status becomes `AMORPHOUS` or `FactStatus.AMBIGUOUS`.
  - `value` is a list containing both `"x"` and `"y"`.
  - `provenance` includes both sources.

### 2.4 `test_merge_disallowed_ambiguity_becomes_conflict`

**Pseudocode:**

- Arrange:
  - Schema for `DemoFacts.FOO` with `allow_ambiguity=False`.
  - Context with `DemoFacts.FOO` set to `"x"`, status `SOLID`.
- Act:
  - `merge_outputs` with `ResolverOutput(DemoFacts.FOO, "y", source="r2")`.
- Assert:
  - Status becomes `CONFLICT`.
  - `value` contains enough info to debug (e.g., list of conflicting values or last write).
  - Notes or provenance reflect conflict.

### 2.5 `test_merge_preserves_notes_and_confidence`

**Pseudocode:**

- Arrange:
  - Existing FactValue with some `notes` and `confidence`.
- Act:
  - `merge_outputs` with new outputs that include `note` and `confidence`.
- Assert:
  - Combined notes include previous + new.
  - Confidence is updated according to rule (e.g., max or weighted).

---

## 3. Resolver Interface & Registry

**Goal:** Ensure `BaseResolver` and `register_resolver` behavior is correct.

### 3.1 `test_register_resolver_populates_registry`

**Pseudocode:**

- Arrange:
  - Define a `DummyResolver` class decorated with `@register_resolver(DUMMY_SPEC)`.
- Act:
  - Access `RESERVOIR_REGISTRY["DummyResolverName"]`.
- Assert:
  - Class is present.
  - `DummyResolver.spec` is set correctly.

### 3.2 `test_resolver_cannot_run_without_inputs`

**Pseudocode:**

- Arrange:
  - Spec requires `DemoFacts.FOO`.
  - Context `state` does **not** contain `DemoFacts.FOO`.
- Act:
  - Call `resolver.can_run(ctx)`.
- Assert:
  - Returns `False`.

### 3.3 `test_resolver_run_returns_outputs_respected_by_merge`

**Pseudocode:**

- Arrange:
  - Context with appropriate input fact(s).
  - A resolver that returns a known output.
- Act:
  - Call `resolver.run(ctx)` and then `merge_outputs` with returned outputs.
- Assert:
  - The new facts appear in `ctx.state` with correct values/status.

---

## 4. Planner & Expected-Value Scheduling

**Goal:** Validate that the planner:

- Schedules resolvers based on input availability and EVoI.
- Respects required facts and stops early when satisfied.
- Never runs resolvers that don’t have their inputs.
- Doesn’t get stuck or misbehave with multiple resolvers.

### 4.1 `test_planner_runs_minimal_resolvers_to_satisfy_single_fact`

**Pseudocode:**

- Arrange:
  - Define two resolvers:
    - `ResA`: produces `DemoFacts.FOO` directly from given input.
    - `ResB`: also produces `DemoFacts.FOO` but with higher cost.
  - Set `user_priority` to favor `DemoFacts.FOO`.
  - Create a `ResolutionContext` with necessary base facts for both.
- Act:
  - Run planner with required_facts = `{DemoFacts.FOO}`.
- Assert:
  - Planner runs exactly one resolver (the cheaper one, `ResA`).
  - `ResB` is not executed (not in planner's executed set).

### 4.2 `test_planner_respects_required_facts`

**Pseudocode:**

- Arrange:
  - Two resolvers:
    - `ResFoo` => `DemoFacts.FOO`.
    - `ResBar` => `DemoFacts.BAR`.
  - Required facts: `{DemoFacts.FOO, DemoFacts.BAR}`.
- Act:
  - Run planner.
- Assert:
  - Both `ResFoo` and `ResBar` are executed.
  - Both FOO and BAR appear in `ctx.state`.
  - Planner stops after these facts are produced.

### 4.3 `test_planner_stops_when_no_more_eligible_resolvers`

**Pseudocode:**

- Arrange:
  - Have a resolver `ResNeedsX` that requires `DemoFacts.X` but no resolver produces X.
  - No required_facts given, or required_facts cannot be satisfied.
- Act:
  - Run planner.
- Assert:
  - Planner terminates without error.
  - `ResNeedsX` is never run because its inputs were never satisfied.
  - Log contains an entry indicating no more eligible resolvers.

### 4.4 `test_planner_uses_impact_and_cost_in_scheduling`

**Pseudocode:**

- Arrange:
  - Two resolvers:
    - `ResCheapLowImpact`: cost=10ms, impact on FOO (0.1).
    - `ResExpensiveHighImpact`: cost=30ms, impact on FOO (0.9).
  - Set user_priority[FOO] = 1.0.
- Act:
  - Run planner with required_facts including FOO.
- Assert:
  - Check which resolver runs first by reading planner's trace.
  - Confirm the ratio impact/cost is higher for the chosen one.
  - Optionally, assert on order == expected.

---

## 5. Caching (SQLite / Parquet)

**Goal:** Ensure that cache policies can be plugged into resolvers and behave consistently.

### 5.1 `test_sqlite_cache_hits_return_cached_value`

**Pseudocode:**

- Arrange:
  - A resolver `CachedRes` that:
    - Uses `SQLiteCachePolicy`.
    - For a given input fact, it returns a `ResolverOutput` with known value.
  - First call: run `CachedRes` with input X.
- Act:
  - Run `CachedRes` again with same input X.
- Assert:
  - On second run, resolver uses cached result (can be asserted by:
    - injecting a flag or
    - counting how many DB queries are executed via mocking).
  - Both runs produce same output value.

### 5.2 `test_cache_key_includes_relevant_facts`

**Pseudocode:**

- Arrange:
  - Configure a resolver to depend on two facts: A, B.
  - Provide A=1,B=2 and run once.
  - Provide A=1,B=3 and run again.
- Act:
  - Inspect underlying cache table or mock to ensure two distinct entries (different cache keys).
- Assert:
  - Cache keys differ.
  - Fetching with the first pair returns only the first result.

### 5.3 `test_parquet_cache_limit_enforced`

**Pseudocode:**

- Arrange:
  - Configure Parquet cache with small max size (e.g. 1MB).
  - Simulate writing multiple Parquet files until total > 1MB.
- Act:
  - Call periodic cleanup routine (e.g. `run_cache_cleanup`).
- Assert:
  - Oldest files are removed until total size <= limit.
  - Newest files remain.

---

## 6. Web API (FastAPI) & Rate Limiting

**Goal:** Validate the behavior of the FastAPI app and ensure rate limiting works.

### 6.1 `test_health_endpoint_ok`

**Pseudocode:**

- Arrange:
  - Start FastAPI test client.
- Act:
  - `GET /health`.
- Assert:
  - Status code 200.
  - Response JSON: `{ "status": "ok" }` or similar.

### 6.2 `test_schema_endpoint_returns_registered_facts`

**Pseudocode:**

- Arrange:
  - Register some demo fact schemas.
  - Start FastAPI app with these schemas.
- Act:
  - `GET /api/schema`.
- Assert:
  - Response is 200.
  - Response JSON includes keys for each registered fact ID and their descriptions/types.

### 6.3 `test_run_endpoint_invokes_planner_and_returns_facts`

**Pseudocode:**

- Arrange:
  - Register a simple resolver that maps input fact to output.
  - Start FastAPI test client.
- Act:
  - `POST /api/run` with JSON body:
    - `{"inputs": {"demo.user_name": "Alice"}, "required_facts": ["demo.user_id"]}`
- Assert:
  - Response status 200.
  - Response JSON contains `facts.demo.user_id` with numeric value.
  - Response JSON includes `trace` with at least one resolver step.

### 6.4 `test_rate_limit_blocks_excessive_requests`

**Pseudocode:**

- Arrange:
  - Configure rate limiter to allow, e.g., 5 requests per minute per IP.
  - Use FastAPI dependency or middleware for rate limiting.
  - Use test client with fixed IP.
- Act:
  - Make 6 `POST /api/run` requests in quick succession.
- Assert:
  - First 5 return 200.
  - 6th returns 429 status code.
  - Response body explains rate limit exceeded.

---

## 7. Demo Plugin Integration (User System Demo)

**Goal:** Ensure that demo plugins can register facts, schemas, and resolvers and that the core engine sees them.

### 7.1 `test_demo_plugin_registers_fact_schemas_at_startup`

**Pseudocode:**

- Arrange:
  - Import `demo_user_system.schemas.register_demo_schemas`.
- Act:
  - Call `register_demo_schemas()`.
- Assert:
  - `FACT_SCHEMAS` includes `DemoFacts.USER_NAME`, `DemoFacts.USER_ID`, etc.

### 7.2 `test_demo_resolver_registration`

**Pseudocode:**

- Arrange:
  - Import `demo_user_system.resolvers.user_resolvers` (this triggers `register_resolver`).
- Act:
  - Inspect `RESOLVER_REGISTRY`.
- Assert:
  - Contains `DemoUserIdResolver` keyed by its spec name.
  - Spec’s `input_facts` and `output_facts` both use `DemoFacts`.

### 7.3 `test_demo_end_to_end_smt_like_flow`

**Pseudocode:**

- Arrange:
  - Register all demo schemas/resolvers.
  - Create a `ResolutionContext` with some base facts (e.g., user name).
  - Required facts: `DemoFacts.USER_ID`, `DemoFacts.FAVORITE_COLOR`.
- Act:
  - Run planner.
- Assert:
  - The appropriate resolvers have been executed.
  - `ctx.state` contains both USER_ID and FAVORITE_COLOR with expected values.
  - No unexpected conflicts unless tests are explicitly injecting them.

---

## 8. UI / HTTP Behavior (HTML + Vanilla JS)

**Goal:** Validate basic behavior of the index page and the JS modules.

These are mostly **integration tests** using something like `httpx` + `playwright` or similar, but we can describe them here as pseudocode.

### 8.1 `test_index_page_renders_form_with_registered_facts`

**Pseudocode:**

- Arrange:
  - Start FastAPI app with demo schemas.
- Act:
  - GET `/` (the index route).
- Assert:
  - Response status is 200.
  - HTML contains form inputs for each input fact (e.g. `<input name="Barcode">` or `<input name="demo.user_name">`).
  - Fact names/descriptions are visible.

### 8.2 `test_client_side_history_rendering`

**Pseudocode:**

- Arrange:
  - Simulate a browser hitting `/` and then posting data to `/report_html` with query parameters.
  - The `report.html` includes the `APPEND_HISTORY_REPORT` script.
- Act:
  - Load the report page in a test browser (Playwright or similar).
  - After load, inspect localStorage `smtReelClientReports`.
- Assert:
  - New entry has `inputs` matching the submitted query params (only non-empty fields).
  - History card in DOM shows "Report from ..." and lists each non-empty input key/value.
  - No "No non-empty inputs recorded" if there were actual inputs.

### 8.3 `test_transpose_tables_for_narrow_viewports`

**Pseudocode:**

- Arrange:
  - Create a fake HTML page with a wide `<table class="data-table">` with many columns.
  - Include `JsBlock.TRANSPOSE_TABLES` script.
- Act:
  - Load page at small viewport width (e.g. 400px).
  - Wait for DOMContentLoaded and script execution.
- Assert:
  - Original `.data-table` has been replaced with a `.data-table.transposed`.
  - The new table has rows/columns flipped.
  - Content integrity: cells contain the same text but reorganized.

---

## 9. Meta & Regression Tests

**Goal:** Protect invariants and guard against regressions as more resolvers and demos are added.

### 9.1 `test_all_registered_facts_have_schemas`

**Pseudocode:**

- Arrange:
  - After all plugins and demo projects are imported and schemas registered.
- Act:
  - Iterate over all resolvers in `RESOLVER_REGISTRY`.
  - For each resolver, check each `fact_id` in `input_facts` and `output_facts`.
- Assert:
  - `FACT_SCHEMAS` contains an entry for every `fact_id`.

### 9.2 `test_no_duplicate_resolver_names`

**Pseudocode:**

- Arrange:
  - Inspect keys of `RESOLVER_REGISTRY`.
- Assert:
  - All names are unique.
  - If duplicates are found, fail the test with a message listing them.

### 9.3 `test_resolver_specs_have_impact_entries_for_all_output_facts`

**Pseudocode:**

- Arrange:
  - For each resolver in `RESOLVER_REGISTRY`:
- Assert:
  - Each `fact_id` in `resolver.spec.output_facts` has a corresponding entry in `resolver.spec.impact` dictionary (unless explicitly allowed, e.g., for purely side-effectful resolvers).

---

## 10. Placeholder: Future Demo Suites (20+ Demos)

**Goal:** Prepare space for ~20 demo domains to validate extensibility.

For each future demo domain (e.g., `demo_orders`, `demo_graph`, `demo_metrics`, etc.), define a small set of tests:

- Fact registration tests.
- Resolver registration tests.
- One or two end-to-end flow tests.

**Example skeleton for a future demo:**

### `demo_orders` example tests

- `test_orders_fact_schemas_registered`
- `test_order_id_resolver_computes_id`
- `test_order_total_resolver_aggregates_line_items`
- `test_end_to_end_order_flow_populates_all_required_facts`

Each of these should be written following the same style and invariants defined in Sections 1–9.

