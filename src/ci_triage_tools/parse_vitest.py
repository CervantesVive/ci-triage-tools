from __future__ import annotations
import json
from pathlib import Path
from ci_triage_tools.schema import Failure

# Vitest blob reporter uses a flat intern table: every dict value that is a
# digit string is a reference to data[int(val)]. Primitives are inline.
# Structure: data[0] = root, file tasks at subsequent indices, each with a
# 'tasks' list of test task refs, each test task has a 'result' ref.


def _r(data: list, val: object) -> object:
    """Resolve one hop: int or digit-string → data[index], anything else → as-is."""
    if isinstance(val, int):
        return data[val]
    if isinstance(val, str) and val.isdigit():
        return data[int(val)]
    return val


def _rstr(data: list, val: object) -> str:
    v = _r(data, val)
    return v if isinstance(v, str) else ""


def parse_blob(path: Path) -> list[Failure]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []

    failures: list[Failure] = []

    for item in data:
        if not isinstance(item, dict):
            continue
        if "result" not in item or "type" not in item or "name" not in item:
            continue
        if _rstr(data, item["type"]) != "test":
            continue

        result = _r(data, item["result"])
        if not isinstance(result, dict) or _rstr(data, result.get("state", "")) != "fail":
            continue

        full_name = _rstr(data, item.get("fullName") or item.get("name", ""))

        file_path: str | None = None
        file_task = _r(data, item.get("file"))
        if isinstance(file_task, dict):
            file_path = _rstr(data, file_task.get("name", "")) or None

        error_msg = ""
        stack: str | None = None
        errors_raw = _r(data, result.get("errors"))
        if isinstance(errors_raw, list) and errors_raw:
            first_err = _r(data, errors_raw[0])
            if isinstance(first_err, dict):
                error_msg = _rstr(data, first_err.get("message", ""))
                stack_val = _r(data, first_err.get("stack"))
                stack = stack_val if isinstance(stack_val, str) else None

        failures.append(Failure(
            test_name=full_name,
            file=file_path,
            error_message=error_msg,
            stack_trace=stack,
            source="vitest",
        ))

    return failures
