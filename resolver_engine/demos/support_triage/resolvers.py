from typing import List

from ...core.resolver_base import BaseResolver, ResolverOutput, ResolverSpec
from ...core.state import ResolutionContext
from .schemas import SupportFacts


registered = False


def register_support_resolvers() -> None:
    global registered
    if registered:
        return

    @BaseResolver.register(
        ResolverSpec(
            name="SeverityClassifierResolver",
            description="Roughly classify incident severity from the summary",
            input_facts={SupportFacts.INCIDENT_SUMMARY},
            output_facts={SupportFacts.SEVERITY, SupportFacts.CUSTOMER_IMPACT},
            impact={SupportFacts.SEVERITY: 0.6, SupportFacts.CUSTOMER_IMPACT: 0.4},
        )
    )
    class SeverityClassifierResolver(BaseResolver):
        def run(self, ctx: ResolutionContext) -> List[ResolverOutput]:
            summary = str(ctx.state[SupportFacts.INCIDENT_SUMMARY].value).lower()
            if any(word in summary for word in ("outage", "down", "unavailable")):
                severity = "critical"
                impact = "Widespread impact, service unavailable"
            elif "slow" in summary or "degraded" in summary:
                severity = "major"
                impact = "Performance degradation for some users"
            else:
                severity = "minor"
                impact = "Isolated inconvenience or request"
            return [
                ResolverOutput(SupportFacts.SEVERITY, severity, source="demo.support"),
                ResolverOutput(SupportFacts.CUSTOMER_IMPACT, impact, source="demo.support"),
            ]

    @BaseResolver.register(
        ResolverSpec(
            name="AssignmentResolver",
            description="Assign the best-fit response team based on severity",
            input_facts={SupportFacts.SEVERITY},
            output_facts={SupportFacts.ASSIGNED_TEAM, SupportFacts.ETA_DAYS},
            impact={SupportFacts.ASSIGNED_TEAM: 0.5, SupportFacts.ETA_DAYS: 0.7},
        )
    )
    class AssignmentResolver(BaseResolver):
        def run(self, ctx: ResolutionContext) -> List[ResolverOutput]:
            severity = str(ctx.state[SupportFacts.SEVERITY].value)
            if severity == "critical":
                team = "SRE"
                eta_days = 1
            elif severity == "major":
                team = "Backend"
                eta_days = 3
            else:
                team = "Support"
                eta_days = 5
            return [
                ResolverOutput(SupportFacts.ASSIGNED_TEAM, team, source="demo.support"),
                ResolverOutput(SupportFacts.ETA_DAYS, eta_days, source="demo.support"),
            ]

    registered = True
