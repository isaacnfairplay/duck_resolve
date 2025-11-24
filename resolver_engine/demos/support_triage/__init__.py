"""Support triage demo that grades severity and picks an assignee."""

from .schemas import SupportFacts, register_support_schemas
from .resolvers import register_support_resolvers

__all__ = [
    "SupportFacts",
    "register_support_schemas",
    "register_support_resolvers",
]
