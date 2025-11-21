import duckdb

from ...core.resolver_base import BaseResolver, ResolverOutput, ResolverSpec
from ...core.state import ResolutionContext
from .schemas import VectorScalarFacts


registered = False


def register_vector_scalar_resolvers():
    global registered
    if registered:
        return

    @BaseResolver.register(
        ResolverSpec(
            name="VectorizedUserBatchResolver",
            description="Process a DuckDB relation of users in a single vectorized pass",
            input_facts={VectorScalarFacts.USER_BATCH_RELATION},
            output_facts={VectorScalarFacts.USER_RECORDS, VectorScalarFacts.USER_COUNT},
            impact={VectorScalarFacts.USER_RECORDS: 1.0, VectorScalarFacts.USER_COUNT: 0.5},
        )
    )
    class VectorizedUserBatchResolver(BaseResolver):
        def run(self, ctx: ResolutionContext):
            relation = ctx.state[VectorScalarFacts.USER_BATCH_RELATION].value
            columns = relation.columns
            records = [dict(zip(columns, row)) for row in relation.fetchall()]
            return [
                ResolverOutput(VectorScalarFacts.USER_RECORDS, records, source="duckdb.vectorized"),
                ResolverOutput(VectorScalarFacts.USER_COUNT, len(records), source="duckdb.vectorized"),
            ]

    @BaseResolver.register(
        ResolverSpec(
            name="PrimaryUserResolver",
            description="Pick a representative user from the vectorized records",
            input_facts={VectorScalarFacts.USER_RECORDS},
            output_facts={VectorScalarFacts.PRIMARY_USER_NAME, VectorScalarFacts.PRIMARY_USER_EMAIL},
            impact={
                VectorScalarFacts.PRIMARY_USER_NAME: 1.0,
                VectorScalarFacts.PRIMARY_USER_EMAIL: 0.8,
            },
        )
    )
    class PrimaryUserResolver(BaseResolver):
        def run(self, ctx: ResolutionContext):
            records = ctx.state[VectorScalarFacts.USER_RECORDS].value
            if not records:
                return []
            # Choose the first user_id to emphasize scalar extraction from a batch.
            primary = sorted(records, key=lambda row: row.get("user_id", 0))[0]
            return [
                ResolverOutput(VectorScalarFacts.PRIMARY_USER_NAME, primary.get("name"), source="scalar"),
                ResolverOutput(VectorScalarFacts.PRIMARY_USER_EMAIL, primary.get("email"), source="scalar"),
            ]

    @BaseResolver.register(
        ResolverSpec(
            name="ScalarToRelationResolver",
            description="Show how scalar facts can be packed back into a vectorized relation",
            input_facts={VectorScalarFacts.PRIMARY_USER_NAME, VectorScalarFacts.PRIMARY_USER_EMAIL},
            output_facts={VectorScalarFacts.PRIMARY_USER_AS_RELATION},
            impact={VectorScalarFacts.PRIMARY_USER_AS_RELATION: 0.6},
        )
    )
    class ScalarToRelationResolver(BaseResolver):
        def run(self, ctx: ResolutionContext):
            name = ctx.state[VectorScalarFacts.PRIMARY_USER_NAME].value
            email = ctx.state[VectorScalarFacts.PRIMARY_USER_EMAIL].value
            relation = duckdb.sql(
                "SELECT * FROM (VALUES (1, ?, ?)) AS users(user_id, name, email)", [name, email]
            )
            return [
                ResolverOutput(
                    VectorScalarFacts.PRIMARY_USER_AS_RELATION,
                    relation,
                    source="scalar-to-vector",
                    note="Re-vectorized from scalar facts",
                )
            ]

    registered = True
