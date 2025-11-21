"""Small demo that bridges vectorized and scalar resolver execution.

The flow is:
1. Accept a batch of user records as a DuckDB relation (vectorized input).
2. Use a vectorized resolver to pull all rows into a list of dictionaries plus a count fact.
3. Use scalar resolvers to refine one representative user from that batch.
4. Optionally pack that scalar back into a one-row DuckDB relation to show the reverse direction.

Note: The demo keeps DuckDB relations in-process for simplicity; the resolver engine
itself remains agnostic to the storage type. Callers that need cross-process safety
can provide parquet/Arrow payloads (preferred) or list inputs and rely on DuckDB to
build a temporary relation during vectorized resolution.
"""

from typing import Any, Mapping, Sequence

from ...core.merge import merge_outputs
from ...core.planner import Planner
from ...core.resolver_base import ResolverOutput
from ...core.schema import FACT_SCHEMAS
from ...core.state import ResolutionContext
from .resolvers import register_vector_scalar_resolvers
from .schemas import VectorScalarFacts, register_vector_scalar_schemas


EXAMPLE_USERS: list[Mapping[str, Any]] = [
    {"user_id": 1, "name": "Ada Lovelace", "email": "ada@example.com"},
    {"user_id": 2, "name": "Grace Hopper", "email": "hopper@example.com"},
]


def run_vector_to_scalar_demo(
    user_batch: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the vectorized-to-scalar demonstration end-to-end.

    Args:
        user_batch: Optional iterable of user dictionaries. If omitted the built-in
            :data:`EXAMPLE_USERS` sample is used.

    Returns:
        A dictionary summarizing the facts that were resolved and the resolvers that
        executed, ready to be printed or inspected in tests or notebooks.
    """

    register_vector_scalar_schemas()
    register_vector_scalar_resolvers()

    ctx = ResolutionContext()
    batch = user_batch or EXAMPLE_USERS
    normalized = FACT_SCHEMAS[VectorScalarFacts.USER_BATCH_RELATION].apply_normalization(batch)
    merge_outputs(
        ctx,
        [
            ResolverOutput(
                VectorScalarFacts.USER_BATCH_RELATION,
                normalized,
                source="demo.input",
                note="Vectorized input provided to the resolver stack",
            )
        ],
    )

    planner = Planner(
        required_facts={VectorScalarFacts.PRIMARY_USER_NAME, VectorScalarFacts.PRIMARY_USER_AS_RELATION},
        user_priority={},
    )
    result = planner.run(ctx)

    primary_relation_value = ctx.state.get(VectorScalarFacts.PRIMARY_USER_AS_RELATION)
    primary_rows = primary_relation_value.value.fetchall() if primary_relation_value else []

    return {
        "executed_resolvers": result.executed_resolvers,
        "user_count": ctx.state[VectorScalarFacts.USER_COUNT].value,
        "primary_user_name": (
            ctx.state[VectorScalarFacts.PRIMARY_USER_NAME].value
            if VectorScalarFacts.PRIMARY_USER_NAME in ctx.state
            else None
        ),
        "primary_user_email": (
            ctx.state[VectorScalarFacts.PRIMARY_USER_EMAIL].value
            if VectorScalarFacts.PRIMARY_USER_EMAIL in ctx.state
            else None
        ),
        "roundtrip_relation_rows": primary_rows,
    }
