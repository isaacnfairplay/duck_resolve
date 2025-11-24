from enum import Enum

from ...core.schema import FactSchema, FACT_SCHEMAS, register_fact_schema


class SupportFacts(str, Enum):
    INCIDENT_SUMMARY = "demo.support.incident_summary"
    SEVERITY = "demo.support.severity"
    CUSTOMER_IMPACT = "demo.support.customer_impact"
    ASSIGNED_TEAM = "demo.support.assigned_team"
    ETA_DAYS = "demo.support.eta_days"


def register_support_schemas() -> None:
    if SupportFacts.INCIDENT_SUMMARY not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                SupportFacts.INCIDENT_SUMMARY,
                py_type=str,
                description="Short description of the incident submitted by a user",
            )
        )
    if SupportFacts.SEVERITY not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                SupportFacts.SEVERITY,
                py_type=str,
                description="Categorized severity level",  # e.g. critical, major, minor
            )
        )
    if SupportFacts.CUSTOMER_IMPACT not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                SupportFacts.CUSTOMER_IMPACT,
                py_type=str,
                description="Human-readable impact summary",
            )
        )
    if SupportFacts.ASSIGNED_TEAM not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                SupportFacts.ASSIGNED_TEAM,
                py_type=str,
                description="Team that will handle the incident",
            )
        )
    if SupportFacts.ETA_DAYS not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                SupportFacts.ETA_DAYS,
                py_type=int,
                description="Estimated days until resolution",
                normalize=int,
            )
        )
