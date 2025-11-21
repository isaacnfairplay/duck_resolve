from enum import Enum

import pytest
from fastapi.testclient import TestClient

from resolver_engine.app import create_app
from resolver_engine.core.schema import FactSchema, FACT_SCHEMAS, register_fact_schema
from resolver_engine.core.resolver_base import BaseResolver, ResolverSpec, ResolverOutput, RESOLVER_REGISTRY
from resolver_engine.core.state import LineContext


class DemoFacts(str, Enum):
    USER_NAME = "demo.user_name"
    USER_ID = "demo.user_id"


def setup_function(function):
    FACT_SCHEMAS.clear()
    RESOLVER_REGISTRY.clear()


def _setup_demo_resolver():
    register_fact_schema(FactSchema(DemoFacts.USER_NAME, py_type=str, description="name"))
    register_fact_schema(FactSchema(DemoFacts.USER_ID, py_type=int, description="id"))

    @BaseResolver.register(
        ResolverSpec(
            name="UserIdResolver",
            description="maps name to id",
            input_facts={DemoFacts.USER_NAME},
            output_facts={DemoFacts.USER_ID},
            impact={DemoFacts.USER_ID: 1.0},
        )
    )
    class UserIdResolver(BaseResolver):
        def run(self, ctx: LineContext):
            name = ctx.state[DemoFacts.USER_NAME].value
            return [ResolverOutput(DemoFacts.USER_ID, len(name))]

    return UserIdResolver


def test_health_endpoint_ok():
    app = create_app()
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_schema_endpoint_returns_registered_facts():
    _setup_demo_resolver()
    app = create_app()
    client = TestClient(app)

    resp = client.get("/api/schema")
    data = resp.json()

    assert resp.status_code == 200
    assert DemoFacts.USER_NAME.value in data
    assert data[DemoFacts.USER_NAME.value]["description"] == "name"


def test_run_endpoint_invokes_planner_and_returns_facts():
    _setup_demo_resolver()
    app = create_app()
    client = TestClient(app)

    resp = client.post(
        "/api/run",
        json={
            "inputs": {DemoFacts.USER_NAME.value: "Alice"},
            "required_facts": [DemoFacts.USER_ID.value],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["facts"][DemoFacts.USER_ID.value] == 5
    assert body["trace"]


def test_rate_limit_blocks_excessive_requests():
    _setup_demo_resolver()
    app = create_app(rate_limit_per_minute=5)
    client = TestClient(app)

    for i in range(6):
        resp = client.post(
            "/api/run",
            json={
                "inputs": {DemoFacts.USER_NAME.value: f"User{i}"},
                "required_facts": [DemoFacts.USER_ID.value],
            },
        )
    assert resp.status_code == 429
    assert resp.json()["detail"]
