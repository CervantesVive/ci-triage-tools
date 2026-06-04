from __future__ import annotations
import fnmatch
import json
import shutil
import subprocess
from dataclasses import asdict
from pathlib import Path
from ci_triage_tools.schema import Failure

_CACHE_ROOT = Path.home() / ".cache" / "ci-triage"


def _cache_dir(run_id: str) -> Path:
    return _CACHE_ROOT / run_id


def _failures_path(run_id: str) -> Path:
    return _cache_dir(run_id) / "failures.json"


def _log_path(run_id: str) -> Path:
    return _cache_dir(run_id) / "log_sanitized.txt"


def _artifacts_dir(run_id: str) -> Path:
    return _cache_dir(run_id) / "artifacts"


def load_cached_failures(run_id: str) -> list[Failure] | None:
    p = _failures_path(run_id)
    if not p.exists():
        return None
    return [Failure(**f) for f in json.loads(p.read_text())]


def save_failures(run_id: str, failures: list[Failure]) -> None:
    p = _failures_path(run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps([asdict(f) for f in failures], indent=2))


def load_cached_log(run_id: str) -> str | None:
    p = _log_path(run_id)
    return p.read_text(encoding="utf-8") if p.exists() else None


def save_log(run_id: str, text: str) -> None:
    p = _log_path(run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def clear_run_cache(run_id: str) -> None:
    d = _cache_dir(run_id)
    if d.exists():
        shutil.rmtree(d)


def download_run_artifacts(owner: str, repo: str, run_id: str) -> Path:
    """Download all artifacts for a run into the cache directory. Returns the artifacts dir."""
    dest = _artifacts_dir(run_id)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["gh", "run", "download", run_id, "--repo", f"{owner}/{repo}", "--dir", str(dest)],
        check=True,
        capture_output=True,
    )
    return dest


def detect_artifact_type(artifact_dir_name: str) -> str | None:
    """Return 'vitest', 'playwright', or None based on the artifact directory name."""
    if fnmatch.fnmatch(artifact_dir_name, "blob-report-*"):
        return "vitest"
    lower = artifact_dir_name.lower()
    if "playwright" in lower or "e2e-blob" in lower:
        return "playwright"
    return None
