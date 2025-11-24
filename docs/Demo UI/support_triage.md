# Support triage demo walkthrough

The support triage demo turns a free-text incident summary into actionable ownership and ETA guidance.

## Steps
1. Enter a short summary for `demo.support.incident_summary` (for example `Site outage for multiple users`).
2. Mark `demo.support.assigned_team`, `demo.support.eta_days`, and optionally `demo.support.customer_impact` as required facts.
3. The planner first classifies severity and impact, then assigns the appropriate team with a timeline.
4. The response lists the resolved severity, impact, assigned team, and ETA along with the executed resolver trace.

## What to expect
- Outage keywords are treated as `critical`, routed to `SRE` with a one-day ETA.
- Degraded or slow reports become `major` incidents for the backend team, while everything else is a `minor` ticket for the frontline support queue.
- The trace shows the severity classification running before the assignment resolver, making the dependency order explicit.
