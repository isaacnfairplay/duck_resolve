# Vector-to-Scalar helper form

This companion guide captures the interactive `/` helper form for the vector-to-scalar demo inputs now that the page posts directly to `/api/run`.

## What you see
- The helper form fetches `/api/schema` and lists every vector-scalar fact alongside the scalar demo facts in one grouped fieldset.
- A separate **Required facts** box lets you request specific outputs in a single click.
- The **Run demo** button posts the collected values to `/api/run` and streams the JSON response into the results pane.

## How to use it
1. Open `/` to load the unified form.
2. Enter vector inputs such as `vector_scalar.user_records`, `vector_scalar.user_batch_relation`, or `vector_scalar.user_count` as needed, leaving unused inputs blank.
3. Add any targeted outputs to **Required facts** (comma-separated identifiers like `vector_scalar.user_count`).
4. Click **Run demo**; the page will display the returned facts and executed resolver trace so you can confirm how vector inputs translate to scalar outputs.
