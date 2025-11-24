import json
import time
from string import Template
from typing import Any, Callable

import duckdb

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from .core.schema import FACT_SCHEMAS
from .core.merge import merge_outputs
from .core.resolver_base import RESOLVER_REGISTRY, ResolverOutput
from .core.state import ResolutionContext
from .core.planner import Planner

_rate_buckets: dict[str, list[float]] = {}


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
    """Convert resolver outputs to JSON-serializable structures.

    DuckDB relations are fetched into in-memory rows so the API response
    remains serializable for documentation renders and browser clients.
    Non-serializable values are stringified as a last resort.
    """

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


def create_app(rate_limit_per_minute: int = 60, include_demo_data: bool = False) -> FastAPI:
    _rate_buckets.clear()

    if include_demo_data:
        _register_demo_data()

    app = FastAPI()

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
        inputs_html = "".join(
            f"<label>{fid}<input name='{fid}' /></label>" for fid in FACT_SCHEMAS.keys()
        )
        return f"<html><body><form>{inputs_html}</form></body></html>"

    @app.get("/report.html", response_class=PlainTextResponse)
    def report(request: Request) -> str:
        query = request.url.query
        template = Template(
            """
function parseQuery(q) {
  var parts = q.split('&');
  var items = [];
  for (var i=0;i<parts.length;i++) {
    if(!parts[i]) continue;
    var kv = parts[i].split('=');
    if(kv.length>=2 && kv[1] !== '') {
      items.push([decodeURIComponent(kv[0]), decodeURIComponent(kv[1])]);
    }
  }
  return items;
}
var entries = parseQuery('$query');
var current = JSON.parse(localStorage.getItem('resolverHistory') || '{}');
for (var i=0;i<entries.length;i++) {
  var pair = entries[i];
  current[pair[0]] = pair[1];
}
localStorage.setItem('resolverHistory', JSON.stringify(current));
 """
        )
        script = template.substitute(query=query)
        return script

    return app
