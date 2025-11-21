from enum import Enum

from ...core.schema import FactSchema, register_fact_schema, FACT_SCHEMAS


class DemoFacts(str, Enum):
    USER_NAME = "demo.user_name"
    USER_ID = "demo.user_id"
    FAVORITE_COLOR = "demo.favorite_color"


def register_demo_schemas():
    if DemoFacts.USER_NAME not in FACT_SCHEMAS:
        register_fact_schema(FactSchema(DemoFacts.USER_NAME, py_type=str, description="User name"))
    if DemoFacts.USER_ID not in FACT_SCHEMAS:
        register_fact_schema(FactSchema(DemoFacts.USER_ID, py_type=int, description="User id"))
    if DemoFacts.FAVORITE_COLOR not in FACT_SCHEMAS:
        register_fact_schema(
            FactSchema(
                DemoFacts.FAVORITE_COLOR,
                py_type=str,
                description="Favorite color",
                allow_ambiguity=True,
            )
        )
