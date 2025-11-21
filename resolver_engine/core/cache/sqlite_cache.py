import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable, List

from ..resolver_base import ResolverOutput, ResolverSpec


class SQLiteCachePolicy:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._ensure()

    def _ensure(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("CREATE TABLE IF NOT EXISTS cache (cache_key TEXT PRIMARY KEY, payload TEXT)")
        conn.commit()
        conn.close()

    def clear(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM cache")
        conn.commit()
        conn.close()

    def build_cache_key(self, ctx, spec: ResolverSpec) -> str:
        key_parts = {str(fid): ctx.state[fid].value for fid in spec.input_facts if fid in ctx.state}
        return json.dumps(key_parts, sort_keys=True)

    def fetch(self, cache_key: str):
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT payload FROM cache WHERE cache_key=?", (cache_key,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        payload = json.loads(row[0])
        return [
            ResolverOutput(item["fact_id"], item["value"], item.get("source"), item.get("note"), item.get("confidence", 1.0))
            for item in payload
        ]

    def store(self, cache_key: str, outputs: Iterable[ResolverOutput]):
        payload = [
            {
                "fact_id": out.fact_id,
                "value": out.value,
                "source": out.source,
                "note": out.note,
                "confidence": out.confidence,
            }
            for out in outputs
        ]
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO cache(cache_key, payload) VALUES (?, ?)",
            (cache_key, json.dumps(payload)),
        )
        conn.commit()
        conn.close()
