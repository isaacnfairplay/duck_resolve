from enum import StrEnum
from typing import Any
import os

import duckdb
import pyarrow as pa


from ...core.schema import FACT_SCHEMAS, FactSchema, register_fact_schema


class VectorScalarFacts(StrEnum):
    USER_BATCH_RELATION = "vector_scalar.user_batch_relation"
    USER_RECORDS = "vector_scalar.user_records"
    USER_COUNT = "vector_scalar.user_count"
    PRIMARY_USER_NAME = "vector_scalar.primary_user_name"
    PRIMARY_USER_EMAIL = "vector_scalar.primary_user_email"
    PRIMARY_USER_AS_RELATION = "vector_scalar.primary_user_as_relation"


def _normalize_user_batch(value: Any):
    """Normalize arbitrary input into a DuckDB relation.

    The demo accepts in-process DuckDB relations, parquet/Arrow payloads, or a Python
    list of dictionaries containing ``user_id``, ``name``, and ``email`` columns.
    Parquet or Arrow inputs are preferred for cross-process interchange; DuckDB can
    ingest them directly while keeping the engine agnostic to the storage mechanism.
    Lists are packed into a VALUES clause so the resolver can still operate on a
    vectorized relation when no columnar format is provided.

    The core engine does not require ``DuckDBPyRelation`` objects; they are used here
    solely to illustrate vectorized execution inside a single process. Callers that
    need cross-process safety can pass parquet/Arrow tables or list-of-dicts inputs
    and let DuckDB rebuild an in-process relation when the vectorized resolver runs.
    """

    if isinstance(value, duckdb.DuckDBPyRelation):
        return value

    if  isinstance(value, pa.Table):
        return duckdb.arrow(value)

    if isinstance(value, (str, os.PathLike)) and str(value).lower().endswith(".parquet"):
        return duckdb.read_parquet(value)

    # Allow a list-of-dicts for convenience in the demo.
    if isinstance(value, list) and value and isinstance(value[0], dict):
        columns = list(value[0].keys())
        placeholders = "(" + ", ".join(["?"] * len(columns)) + ")"
        values_clause = ", ".join([placeholders for _ in value])
        flattened: list[Any] = []
        for row in value:
            flattened.extend(row.get(col) for col in columns)
        query = f"SELECT * FROM (VALUES {values_clause}) AS users({', '.join(columns)})"
        return duckdb.sql(query, flattened)

    if isinstance(value, list) and not value:
        return duckdb.sql(
            "SELECT * FROM (VALUES (NULL::INT, NULL::VARCHAR, NULL::VARCHAR)) "
            "AS users(user_id, name, email) WHERE 1=0"
        )

    raise TypeError("User batch must be a DuckDB relation or list of dictionaries")


def register_vector_scalar_schemas():
    if VectorScalarFacts.USER_BATCH_RELATION not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                VectorScalarFacts.USER_BATCH_RELATION,
                py_type=duckdb.DuckDBPyRelation,
                description="DuckDB relation containing user batch records",
                normalize=_normalize_user_batch,
            )
        )
    if VectorScalarFacts.USER_RECORDS not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                VectorScalarFacts.USER_RECORDS,
                py_type=list,
                description="Vectorized user records extracted from the relation",
            )
        )
    if VectorScalarFacts.USER_COUNT not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                VectorScalarFacts.USER_COUNT,
                py_type=int,
                description="Number of rows in the vectorized input relation",
            )
        )
    if VectorScalarFacts.PRIMARY_USER_NAME not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                VectorScalarFacts.PRIMARY_USER_NAME,
                py_type=str,
                description="Representative user name refined from the vectorized output",
            )
        )
    if VectorScalarFacts.PRIMARY_USER_EMAIL not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                VectorScalarFacts.PRIMARY_USER_EMAIL,
                py_type=str,
                description="Representative user email refined from the vectorized output",
            )
        )
    if VectorScalarFacts.PRIMARY_USER_AS_RELATION not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                VectorScalarFacts.PRIMARY_USER_AS_RELATION,
                py_type=duckdb.DuckDBPyRelation,
                description="One-row relation rebuilt from scalar facts to show scalar-to-vector transition",
            )
        )
