from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Failure:
    test_name: str
    file: str | None
    error_message: str
    stack_trace: str | None
    source: str  # "vitest" | "playwright"


@dataclass
class WorkflowResult:
    workflow_name: str
    run_id: str
    run_url: str
    failures: list[Failure] = field(default_factory=list)


@dataclass
class TriageReport:
    pr_url: str
    head_sha: str
    workflows: list[WorkflowResult] = field(default_factory=list)
