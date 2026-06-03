from __future__ import annotations
import base64
import io
import json
import re
import zipfile
from pathlib import Path
from ci_triage_tools.schema import Failure

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def parse_blob(zip_path: Path) -> list[Failure]:
    failures: list[Failure] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not (name.endswith("report.json") or name.endswith(".jsonl")):
                continue
            try:
                data = json.loads(zf.read(name))
            except (json.JSONDecodeError, KeyError):
                continue
            if not isinstance(data, dict):
                continue
            if "suites" in data:
                failures.extend(_from_suites(data))
            elif "files" in data:
                failures.extend(_from_files(data, zf))
    return failures


def parse_html(report_dir: Path) -> list[Failure]:
    index_html = report_dir / "index.html"
    content = index_html.read_text(encoding="utf-8")
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", content, re.DOTALL)
    zip_bytes: bytes | None = None
    for script in scripts:
        if script.startswith("data:application/zip;base64,"):
            zip_bytes = base64.b64decode(script[len("data:application/zip;base64,"):])
            break
    if zip_bytes is None:
        raise ValueError(f"No embedded zip found in {index_html}")
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        report_data = json.loads(zf.read("report.json"))
        if "files" in report_data:
            return _from_files(report_data, zf)
        if "suites" in report_data:
            return _from_suites(report_data)
    raise ValueError(f"Unknown report format in {index_html}")


def _from_files(report_data: dict, zf: zipfile.ZipFile) -> list[Failure]:
    failures: list[Failure] = []
    zip_names = set(zf.namelist())
    for file_entry in report_data.get("files", []):
        file_id = file_entry.get("fileId", "")
        file_name = file_entry.get("fileName", "")
        shard = file_entry.get("tests", [])
        if f"{file_id}.json" in zip_names:
            shard = json.loads(zf.read(f"{file_id}.json")).get("tests", [])
        for test in shard:
            if test.get("outcome") != "unexpected":
                continue
            for result in test.get("results", []):
                if result.get("status") not in ("failed", "timedOut"):
                    continue
                path_parts = test.get("path", [])
                title = " > ".join(p for p in path_parts + [test.get("title", "")] if p)
                errors = result.get("errors", [])
                msg = _strip_ansi(errors[0].get("message", "")) if errors else ""
                stack = errors[0].get("stack") if errors else None
                failures.append(Failure(
                    test_name=title,
                    file=test.get("location", {}).get("file", file_name),
                    error_message=msg,
                    stack_trace=stack,
                    source="playwright",
                ))
    return failures


def _from_suites(data: dict) -> list[Failure]:
    failures: list[Failure] = []

    def walk(suites: list, prefix: str) -> None:
        for suite in suites:
            title = suite.get("title", "")
            full = f"{prefix} > {title}".strip(" > ") if prefix else title
            for spec in suite.get("specs", []):
                spec_title = spec.get("title", "")
                for test in spec.get("tests", []):
                    for result in test.get("results", []):
                        if result.get("status") not in ("failed", "timedOut"):
                            continue
                        errors = result.get("errors", [])
                        msg = errors[0].get("message", "") if errors else result.get("error", {}).get("message", "")
                        stack = errors[0].get("stack") if errors else None
                        failures.append(Failure(
                            test_name=f"{full} > {spec_title}",
                            file=spec.get("file", ""),
                            error_message=msg,
                            stack_trace=stack,
                            source="playwright",
                        ))
            walk(suite.get("suites", []), full)

    walk(data.get("suites", []), "")
    return failures


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)
