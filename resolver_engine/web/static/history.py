import json
from urllib.parse import parse_qsl


def apply_history_script(storage: dict, script: str):
    start = script.find("parseQuery('")
    if start == -1:
        return
    start += len("parseQuery('")
    end = script.find("')", start)
    query = script[start:end]
    entries = {k: v for k, v in parse_qsl(query) if v}
    storage["resolverHistory"] = json.dumps(entries)
