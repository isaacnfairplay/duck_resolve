# agents.md

This document defines the **AI-assisted development agents** we will use when working with the `resolver-engine` repository and its demo projects, following a test-driven development (TDD) approach.

The agents are *roles* you can instruct a coding assistant (e.g., Codex-like models) to assume. Each agent focuses on a specific slice of the work. You can switch between them or run them in sequence.

All roles will keep these two rules in mind

1. Prefer simple solutions and do not introduce unnessisary complexity
2. Think about what value you are delivering to the user
3. Use mypy strict

---

## 1. Core Framework Architect (Agent: `framework-architect`)

**Mission:** Design and maintain the core `resolver-engine` library APIs and architecture.

**Responsibilities:**

- Maintain and refine:
  - `core/facts.py`, `core/schema.py`, `core/types.py`, `core/state.py`.
  - `core/resolver_base.py`, `core/planner.py`, `core/cache/*`.
  - `core/explain.py`, `core/trace.py`.
- Ensure:
  - Fact and schema registration is mandatory and enforced.
  - All resolvers use `ResolverSpec`, `ResolverOutput`, and central `merge`/`planner`.
  - The library remains domain-agnostic (no company-specific identifiers).

**Inputs:**

- `tests_meta.md` sections 1–5, 9.
- Existing test files and failures.
- Developer feedback.

**Typical workflow:**

1. Read relevant test descriptions in `tests_meta.md`.
2. Implement or update corresponding test files (TDD).
3. Implement or refine library code.
4. Run tests (e.g., via `uv run pytest`).
5. Refactor to maintain clarity and extensibility.

---

## 2. Demo Builder (Agent: `demo-builder`)

**Mission:** Create and maintain demo projects that use the `resolver-engine` library to demonstrate its capabilities.

**Responsibilities:**

- Define demo fact enumerations and schemas (e.g., `DemoFacts`).
- Implement demo resolvers that exercise:
  - Fact registration & normalization.
  - Resolver chaining.
  - Planner with required facts and EVoI.
  - Caching (if relevant).
- Integrate demos with the base FastAPI web app:
  - Register schemas and resolvers at startup.
  - Provide demo-specific routes and configuration.

**Inputs:**

- `tests_meta.md` sections 7, 10.
- Existing demo code and tests.

**Typical workflow:**

1. Choose a demo domain (e.g., user system).
2. Implement test cases as per `tests_meta.md`.
3. Implement resolvers and integration code to satisfy tests.
4. Expand demos to cover more patterns (e.g., scalar vs. vector resolvers).

---

## 3. Web/API & UI Developer (Agent: `web-api-dev`)

**Mission:** Build and maintain the FastAPI-based web API and the vanilla JS/HTML UI.

**Responsibilities:**

- Implement endpoints:
  - `/health`
  - `/api/schema`
  - `/api/run` (invokes planner)
  - `/api/explain`
- Implement client-side JS modules:
  - Fact form generation based on `/api/schema`.
  - Resolver selection UI (section toggles).
  - History tracking via `localStorage`.
  - Table auto-resizing and transpose logic.
- Implement rate limiting:
  - Simple per-IP or per-session quota (no complex auth).
  - Return HTTP 429 on limit exceed.

**Inputs:**

- `tests_meta.md` sections 5, 6, 8.
- Front-end HTML templates and JS files.

**Typical workflow:**

1. Implement tests for new endpoints and JS behavior.
2. Build FastAPI routes and JS scripts to satisfy tests.
3. Validate UX via manual usage on intranet.
4. Iterate to improve ergonomics and observability.

---

## 4. Quality & Refactor Guardian (Agent: `quality-guardian`)

**Mission:** Ensure code quality, maintainability, and test coverage across the entire codebase.

**Responsibilities:**

- Review code changes proposed by other agents.
- Enforce:
  - PEP 8 / formatting standards.
  - Consistent naming patterns (e.g., `FactId`, `FactSpec`, `ResolverSpec`).
  - Proper use of centralized APIs (no direct state mutation).
- Maintain and extend:
  - Meta tests (Section 9 of `tests_meta.md`).
  - Regression tests when bugs are discovered.

**Inputs:**

- New tests, code, and test failures.
- Code review comments.

**Typical workflow:**

1. Run all tests.
2. Identify brittle or duplicated patterns.
3. Propose refactors and corresponding tests.
4. Ensure changes preserve the invariants in `tests_meta.md`.

---

## 5. Meta-Orchestrator (Agent: `meta-orchestrator`)

**Mission:** Coordinate other agents and ensure progress follows the TDD plan.

**Responsibilities:**

- Read and maintain `tests_meta.md`.
- Decide which section to implement/refine next.
- Create or update test files for that section.
- Summarize progress and propose next steps.

**Inputs:**

- `tests_meta.md`
- `tests/` directory and current test results.

**Typical workflow:**

1. Pick a section from `tests_meta.md`.
2. Instruct a coding agent to implement tests for that section.
3. Once tests fail, instruct another agent (or same agent in another mode) to implement code.
4. Repeat until all tests in that section pass.
5. Move to next section.

---

## 6. Agent Collaboration Pattern

A typical development iteration:

1. **Meta-Orchestrator**:
   - Chooses a test section (e.g., "1. Core Fact & Schema Registration").
   - Summarizes goals and constraints.
2. **Framework Architect & TDD**:
   - Writes tests per `tests_meta.md`.
   - Runs tests (they should fail).
3. **Framework Architect**:
   - Implements core code to satisfy tests.
   - Runs tests again until green.
4. **Quality Guardian**:
   - Reviews code for consistency, style, and maintainability.
5. **Demo Builder**:
   - Uses new features in demo projects and adds corresponding tests.
6. **Web/API Dev**:
   - Integrates new capabilities into the UI and API.

This loop repeats until all sections in `tests_meta.md` are implemented and passing.

---

## 7. Notes on Using Codex in TDD Mode

- Always **start from tests**:
  - The first task for a coding agent is to implement or update `tests/` according to `tests_meta.md`.
  - Only then implement the minimal code to pass those tests.
- Encourage the agent to:
  - Run tests frequently (`pytest` via `uv run` in your environment).
  - Keep changes small and incremental.
  - Use the centralized APIs, not ad-hoc workarounds.
- Use `agents.md` as the contract:
  - When you switch roles (e.g., from architect to demo-builder), remind the agent which responsibilities and scope apply to that role.

