# Demo User System helper form

This guide describes the current `/` helper form for the scalar demo facts now that the page renders an interactive request helper instead of a static row of inputs.

## What you see
- The form now loads from `/api/schema` and renders all demo fact inputs together, including scalar and vector-oriented facts.
- A dedicated field accepts comma-separated required fact IDs so you can direct the planner from the UI.
- A "Run demo" button triggers a POST to `/api/run` using the values you entered.
- A results pane shows the JSON response (facts plus executed resolver trace).

## How to use it
1. Open `/` to load the schema-driven helper form.
2. Enter scalar demo values such as `DemoFacts.USER_NAME`, `DemoFacts.USER_ID`, and `DemoFacts.FAVORITE_COLOR` (leave any unused fields blank).
3. If you want to force certain outputs, type their fact IDs into **Required facts** (comma-separated, e.g., `demo.user_name,demo.user_id`).
4. Click **Run demo** to call `/api/run`; the page will show the resolved facts and trace below the button.
