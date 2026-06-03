from __future__ import annotations
import json
from pathlib import Path
from ci_triage_tools.schema import Failure


def parse_blob(path: Path) -> list[Failure]:
    data = json.loads(path.read_text(encoding="utf-8"))
    failures: list[Failure] = []
    for file_entry in data.get("files", []):
        file_path: str | None = file_entry.get("name") or file_entry.get("filepath")
        _walk(file_entry.get("tasks", []), [], file_path, failures)
    return failures


def _walk(tasks: list, prefix: list[str], file_path: str | None, out: list[Failure]) -> None:
    for task in tasks:
        name = task.get("name", "")
        task_type = task.get("type", "test")
        if task_type == "suite":
            _walk(task.get("tasks", []), prefix + [name], file_path, out)
        else:
            result = task.get("result") or {}
            if result.get("state") != "fail":
                continue
            errors = result.get("errors") or []
            error_msg = errors[0].get("message", "") if errors else ""
            stack = errors[0].get("stack") if errors else None
            full_name = " > ".join(prefix + [name]) if prefix else name
            out.append(Failure(
                test_name=full_name,
                file=file_path,
                error_message=error_msg,
                stack_trace=stack or None,
                source="vitest",
            ))
