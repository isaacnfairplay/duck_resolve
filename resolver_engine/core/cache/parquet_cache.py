from pathlib import Path


class ParquetCachePolicy:
    def __init__(self, base_path: Path, max_total_bytes: int = 10_000_000):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_total_bytes = max_total_bytes

    def enforce_limit(self):
        files = sorted(self.base_path.glob("*.parquet"), key=lambda p: p.stat().st_mtime)
        total = sum(p.stat().st_size for p in files)
        while total > self.max_total_bytes and files:
            file_to_remove = files.pop(0)
            size = file_to_remove.stat().st_size
            file_to_remove.unlink(missing_ok=True)
            total -= size
