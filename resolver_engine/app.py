import html
import json
import os
import time
from importlib import resources
from pathlib import Path
from string import Template
from typing import Any, Callable

import duckdb
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from .core.merge import merge_outputs
from .core.planner import Planner
from .core.resolver_base import RESOLVER_REGISTRY, ResolverOutput
from .core.schema import FACT_SCHEMAS
from .core.state import ResolutionContext
from .web.templates.fragments import InputFragment

DEFAULT_RELATION_SAMPLE = [
    {"user_id": 1, "name": "Ada Lovelace", "email": "ada@example.com"},
    {"user_id": 2, "name": "Alan Turing", "email": "alan@example.com"},
]

RELATION_SAMPLE_OVERRIDES: dict[str, list[dict[str, object]]] = {
    "vector_scalar.user_batch_relation": DEFAULT_RELATION_SAMPLE,
    "vector_scalar.primary_user_as_relation": DEFAULT_RELATION_SAMPLE,
}

_template_cache: dict[str, Template] = {}
_rate_buckets: dict[str, list[float]] = {}


def _load_template(name: str) -> Template:
    cached = _template_cache.get(name)
    if cached:
        return cached

    template_path = resources.files("resolver_engine.web.templates").joinpath(name)
    content = template_path.read_text(encoding="utf-8")
    template = Template(content)
    _template_cache[name] = template
    return template


def _check_rate_limit(rate_limit_per_minute: int) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        now = time.time()
        window = 60
        limit = rate_limit_per_minute
        key = request.client.host if request.client else "unknown"
        timestamps = _rate_buckets.get(key, [])
        timestamps = [t for t in timestamps if now - t < window]
        if len(timestamps) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        timestamps.append(now)
        _rate_buckets[key] = timestamps

    return dependency


def _normalize_json_value(value: Any) -> Any:
    """Convert resolver outputs to JSON-serializable structures."""

    if isinstance(value, duckdb.DuckDBPyRelation):
        try:
            return value.fetchall()
        except duckdb.ConnectionException:
            return "DuckDB relation (connection closed)"
        except Exception:
            return str(value)

    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _register_demo_data() -> None:
    """Register the bundled demo schemas and resolvers if they are missing."""

    from .demos.demo_user_system.schemas import register_demo_schemas
    from .demos.demo_user_system.resolvers import register_demo_resolvers
    from .demos.vector_scalar_transition.schemas import register_vector_scalar_schemas
    from .demos.vector_scalar_transition.resolvers import register_vector_scalar_resolvers
    from .demos.weather_planner.schemas import register_weather_schemas
    from .demos.weather_planner.resolvers import register_weather_resolvers
    from .demos.support_triage.schemas import register_support_schemas
    from .demos.support_triage.resolvers import register_support_resolvers

    register_demo_schemas()
    register_demo_resolvers()
    register_vector_scalar_schemas()
    register_vector_scalar_resolvers()
    register_weather_schemas()
    register_weather_resolvers()
    register_support_schemas()
    register_support_resolvers()


def _build_fact_inputs() -> str:
    fact_inputs: list[str] = []
    for fid, schema in sorted(FACT_SCHEMAS.items(), key=lambda item: str(item[0])):
        fact_id_key = getattr(fid, "value", str(fid))
        hint_raw = schema.description or ""
        python_type_raw = schema.py_type.__name__
        placeholder_raw = hint_raw or "a value"

        fact_id = html.escape(fact_id_key, quote=True)
        hint = html.escape(hint_raw, quote=True)
        python_type = html.escape(python_type_raw, quote=True)
        placeholder = html.escape(placeholder_raw, quote=True)

        if schema.py_type is duckdb.DuckDBPyRelation:
            sample_rows = RELATION_SAMPLE_OVERRIDES.get(fact_id_key, DEFAULT_RELATION_SAMPLE)
            fact_inputs.append(
                InputFragment.TABLE.value.format(
                    fact_id=fact_id,
                    hint=hint,
                    python_type=python_type,
                    placeholder=html.escape(json.dumps(sample_rows, indent=2), quote=True),
                    sample_rows=InputFragment.serialize_sample_rows(sample_rows),
                )
            )
        else:
            fact_inputs.append(
                InputFragment.TEXT.value.format(
                    fact_id=fact_id,
                    hint=hint,
                    python_type=python_type,
                    placeholder=placeholder,
                )
            )

    return "\n".join(fact_inputs) or "<p class='muted'>No facts are registered yet.</p>"


def create_app(rate_limit_per_minute: int = 60, include_demo_data: bool = False) -> FastAPI:
    _rate_buckets.clear()

    include_demo_env = os.getenv("RESOLVER_INCLUDE_DEMO_DATA")
    if include_demo_env is not None:
        include_demo_data = include_demo_env.lower() in {"1", "true", "yes", "on"}

    if include_demo_data:
        _register_demo_data()

    app = FastAPI()
    assets_path = Path(__file__).parent / "web" / "assets"
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/schema")
    def get_schema() -> dict[str, dict[str, str]]:
        return {
            getattr(fid, "value", str(fid)): {
                "description": schema.description,
                "type": schema.py_type.__name__,
            }
            for fid, schema in FACT_SCHEMAS.items()
        }

    @app.post("/api/run", dependencies=[Depends(_check_rate_limit(rate_limit_per_minute))])
    def run(body: dict[str, Any]) -> dict[str, Any]:
        def resolve_fact_id(identifier: object) -> object:
            for fid in FACT_SCHEMAS.keys():
                if str(fid) == str(identifier):
                    return fid
            return identifier

        inputs = {resolve_fact_id(k): v for k, v in body.get("inputs", {}).items()}
        required = {resolve_fact_id(fid) for fid in body.get("required_facts", [])}
        ctx = ResolutionContext()
        merge_outputs(
            ctx,
            [ResolverOutput(fact_id, value, source="input") for fact_id, value in inputs.items()],
        )
        planner = Planner(required_facts=required, user_priority={})
        result = planner.run(ctx)
        facts = {
            getattr(fid, "value", str(fid)): _normalize_json_value(fv.value)
            for fid, fv in ctx.state.items()
        }
        return {"facts": facts, "trace": result.executed_resolvers}

    @app.get("/api/explain")
    def explain() -> dict[str, list[dict[str, Any]]]:
        def _stringify_fact_id(fact_id: object) -> str:
            return getattr(fact_id, "value", str(fact_id))

        resolvers = [
            {
                "name": resolver.spec.name,
                "description": resolver.spec.description,
                "inputs": sorted(_stringify_fact_id(fid) for fid in resolver.spec.input_facts),
                "outputs": sorted(_stringify_fact_id(fid) for fid in resolver.spec.output_facts),
                "impact": {
                    _stringify_fact_id(fid): weight
                    for fid, weight in sorted(resolver.spec.impact.items(), key=lambda item: str(item[0]))
                },
                "cost": resolver.spec.cost,
            }
            for resolver in sorted(RESOLVER_REGISTRY.values(), key=lambda r: r.spec.name)
        ]

        return {"resolvers": resolvers}

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        template = _load_template("index.html")
        return template.substitute(inputs_html=_build_fact_inputs(), schema_count=len(FACT_SCHEMAS))

    @app.get("/report.html", response_class=PlainTextResponse)
    def report(request: Request) -> str:
        query = request.url.query
        template = _load_template("history.js")
        return template.substitute(query=query)

    return app
