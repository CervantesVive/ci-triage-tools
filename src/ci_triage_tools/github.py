from __future__ import annotations
import json
import re
import subprocess
from dataclasses import dataclass


@dataclass
class RunInfo:
    run_id: str
    workflow_name: str
    run_url: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract (owner, repo, pr_number) from a GitHub PR URL."""
    match = re.fullmatch(
        r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?",
        url.rstrip("/"),
    )
    if not match:
        raise ValueError(f"Not a valid GitHub PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def _gh(args: list[str]) -> dict | list:
    result = subprocess.run(["gh"] + args, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_head_sha(owner: str, repo: str, pr_number: int) -> str:
    data = _gh(["api", f"/repos/{owner}/{repo}/pulls/{pr_number}"])
    return data["head"]["sha"]


def get_failing_runs(owner: str, repo: str, sha: str) -> list[RunInfo]:
    data = _gh([
        "api",
        f"/repos/{owner}/{repo}/actions/runs?head_sha={sha}&event=pull_request&per_page=50",
    ])
    return [
        RunInfo(
            run_id=str(run["id"]),
            workflow_name=run.get("name", "unknown"),
            run_url=run.get("html_url", ""),
        )
        for run in data.get("workflow_runs", [])
        if run.get("conclusion") == "failure"
    ]
