from enum import Enum

from resolver_engine.core.schema import FactSchema, register_fact_schema, FACT_SCHEMAS
from resolver_engine.core.cache.sqlite_cache import SQLiteCachePolicy
from resolver_engine.core.cache.parquet_cache import ParquetCachePolicy
from resolver_engine.core.resolver_base import BaseResolver, ResolverSpec, ResolverOutput
from resolver_engine.core.state import LineContext
from resolver_engine.core.merge import merge_outputs


class DemoFacts(str, Enum):
    A = "demo.a"
    B = "demo.b"


def setup_function(function):
    FACT_SCHEMAS.clear()


def test_sqlite_cache_hits_return_cached_value(tmp_path):
    register_fact_schema(FactSchema(DemoFacts.A, py_type=str, description="a"))
    cache_policy = SQLiteCachePolicy(db_path=tmp_path / "cache.db")

    spec = ResolverSpec(
        name="CachedRes",
        description="cached",
        input_facts={DemoFacts.A},
        output_facts={DemoFacts.A},
        impact={DemoFacts.A: 1.0},
        cache_policy=cache_policy,
    )

    run_calls = []

    @BaseResolver.register(spec)
    class CachedRes(BaseResolver):
        def run(self, ctx: LineContext):
            run_calls.append(1)
            return [ResolverOutput(DemoFacts.A, ctx.state[DemoFacts.A].value + "!", source="calc")]

    ctx = LineContext()
    cache_policy.clear()

    for _ in range(2):
        outputs = CachedRes().execute(ctx, [ResolverOutput(DemoFacts.A, "x", source="input")])
        merge_outputs(ctx, outputs)

    assert run_calls.count(1) == 1
    assert ctx.state[DemoFacts.A].value.endswith("!")


def test_cache_key_includes_relevant_facts(tmp_path):
    register_fact_schema(FactSchema(DemoFacts.A, py_type=int, description="a"))
    register_fact_schema(FactSchema(DemoFacts.B, py_type=int, description="b"))
    cache = SQLiteCachePolicy(db_path=tmp_path / "cache.db")

    spec = ResolverSpec(
        name="TwoInput",
        description="two input",
        input_facts={DemoFacts.A, DemoFacts.B},
        output_facts={DemoFacts.A},
        impact={DemoFacts.A: 1.0},
        cache_policy=cache,
    )

    @BaseResolver.register(spec)
    class TwoInput(BaseResolver):
        def run(self, ctx: LineContext):
            total = ctx.state[DemoFacts.A].value + ctx.state[DemoFacts.B].value
            return [ResolverOutput(DemoFacts.A, total)]

    ctx = LineContext()
    cache.clear()
    outputs1 = TwoInput().execute(
        ctx, [ResolverOutput(DemoFacts.A, 1), ResolverOutput(DemoFacts.B, 2)]
    )
    outputs2 = TwoInput().execute(
        ctx, [ResolverOutput(DemoFacts.A, 1), ResolverOutput(DemoFacts.B, 3)]
    )

    assert outputs1[0].value != outputs2[0].value


def test_parquet_cache_limit_enforced(tmp_path):
    cache_dir = tmp_path / "parquet"
    cache = ParquetCachePolicy(base_path=cache_dir, max_total_bytes=1500)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # simulate multiple files
    for i in range(3):
        file_path = cache_dir / f"chunk_{i}.parquet"
        file_path.write_bytes(b"x" * 800)
    cache.enforce_limit()

    total = sum(p.stat().st_size for p in cache_dir.glob("*.parquet"))
    assert total <= cache.max_total_bytes
