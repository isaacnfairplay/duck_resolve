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

## 6. UI Experience Documenter (Agent: `ui-playwright-doc-writer`)

**Mission:**  
Generate clear, easy-to-understand Markdown walkthroughs of the user interface and experience for the demo projects, using Playwright in Codex Cloud to drive the app and capture real screenshots.

This agent does *not* change core logic. Its job is to **show** how things feel to a human using the system.

**Responsibilities:**

- For each demo (e.g. `demo_user_system` and future demos):
  - Launch the FastAPI app in the Codex Cloud environment.
  - Use Playwright to:
    - Open key pages (`/`, `/report.html`, any demo-specific pages).
    - Fill in inputs, click buttons, and run a few realistic flows.
    - Capture screenshots at important states (before/after running, error states, etc.).
  - Produce **Markdown documents** that:
    - Embed or link to those screenshots.
    - Describe, in plain language:
      - What the user sees on each screen.
      - What actions the user can take.
      - What happens when they submit or run a resolver.
      - How scalar vs vectorized flows appear to the user (where applicable).
    - Are easy to read for non-developers and new team members.

**Inputs:**

- Running demo app inside Codex Cloud (using `create_app()` and uvicorn).
- Playwright (Chromium) inside Codex Cloud.
- Fact schemas for the active demo (from `/api/schema`).
- Existing tests and routes (`/`, `/api/run`, `/report.html`, `/api/explain`).

**Typical workflow:**

1. **Select a demo**  
   - Start with `demo_user_system`, later apply to other demos (up to 20+).
   - Identify the “happy path” and 1–2 interesting edge cases (e.g. ambiguity/conflict).

2. **Spin up the app in the Codex Cloud sandbox**  
   - Install dependencies via `uv`.
   - Run `uvicorn resolver_engine.app:create_app` on a local port.
   - Wait until health check (`/health`) returns `{"status": "ok"}`.

3. **Drive the UI with Playwright**  
   - Open the index page (`/`), wait for form elements to render.
   - Fill in typical demo inputs (e.g. `demo.user_name = "Alice"`).
   - Capture a screenshot of the empty form.
   - Submit or navigate to `/report.html?demo.user_name=Alice` (or equivalent).
   - Capture a screenshot after history has been updated.
   - For vectorization demos:
     - Show one screenshot with scalar input.
     - Show one screenshot with batch/vector input.
     - Show how the results differ visually.

4. **Generate Markdown documentation**  
   - Create a new Markdown file, e.g. `docs/ui_demo_user_system.md`.
   - Include:
     - A short scenario intro (“As a user, I want to…”).
     - Step-by-step numbered steps:
       1. Go to `/`.
       2. Enter this value…
       3. Press this button…
       4. Observe these results…
     - For each step, embed or link to the screenshot:
       - `![Index form](./screenshots/demo_user_system/index.png)`
       - `![Report after run](./screenshots/demo_user_system/report.png)`
     - Explain key concepts in plain language:
       - What “facts” are in this UI.
       - What the “trace” means.
       - Where history is stored/displayed.
       - How vectorized vs scalar runs appear different (if demo supports it).

5. **Keep docs in sync with reality**  
   - If the UI or endpoints change:
     - Re-run Playwright.
     - Update screenshots.
     - Adjust the Markdown steps so they match the current experience.
   - Confirm tests still pass so code + docs are consistent.

**Deliverables:**

- One Markdown file per demo (e.g. `docs/ui_demo_<demo_name>.md`) that:
  - Uses simple language and screenshots.
  - Can be sent to internal stakeholders or new engineers as a “tour” of the tool.
  - Demonstrates scalar and vectorized flows where appropriate.

**Notes:**

- Prefer clarity over completeness: prioritize showing the main user journey end-to-end.
- Avoid implementation jargon in the docs; focus on “what the user does and sees”.
- For vectorization, explicitly call out:
  - When the user is providing “many items at once” vs “one item at a time”.
  - How that changes what is shown in the UI (tables, results, history).

---

## 7. Agent Collaboration Pattern

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

## 8. Notes on Using Codex in TDD Mode

- Always **start from tests**:
  - The first task for a coding agent is to implement or update `tests/` according to `tests_meta.md`.
  - Only then implement the minimal code to pass those tests.
- Encourage the agent to:
  - Run tests frequently (`pytest` via `uv run` in your environment).
  - Keep changes small and incremental.
  - Use the centralized APIs, not ad-hoc workarounds.
- Use `agents.md` as the contract:
  - When you switch roles (e.g., from architect to demo-builder), remind the agent which responsibilities and scope apply to that role.

