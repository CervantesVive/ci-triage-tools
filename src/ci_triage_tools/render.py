from __future__ import annotations
from pathlib import Path
from ci_triage_tools.schema import TriageReport

_BAR = "━" * 70


def render_terminal(report: TriageReport) -> None:
    if not report.workflows:
        print("No failing workflow runs found.")
        return
    for wf in report.workflows:
        total = len(wf.failures)
        noun = "failure" if total == 1 else "failures"
        print(f"\n{_BAR}")
        print(f"  {wf.workflow_name} — {total} {noun}")
        print(f"  {wf.run_url}")
        print(_BAR)
        if not wf.failures:
            if wf.log_fallback:
                print("  (no structured test failures — sanitized job log:)\n")
                for line in wf.log_fallback.splitlines():
                    print(f"  {line}")
            else:
                print("  (no structured failures parsed)")
            continue
        for failure in wf.failures:
            print(f"\n  ✗  {failure.file or '(unknown file)'}")
            print(f"     {failure.test_name}")
            print(f"     {failure.error_message}")
            if failure.stack_trace:
                for line in failure.stack_trace.splitlines()[:3]:
                    stripped = line.strip()
                    if stripped:
                        print(f"     {stripped}")


def render_markdown(report: TriageReport, output: Path) -> None:
    lines: list[str] = [
        f"# CI Triage: {report.pr_url}\n\n",
        f"SHA: `{report.head_sha}`\n",
    ]
    for wf in report.workflows:
        total = len(wf.failures)
        noun = "failure" if total == 1 else "failures"
        lines.append(f"\n## {wf.workflow_name} — {total} {noun}\n\n")
        lines.append(f"Run: {wf.run_url}\n")
        if not wf.failures:
            if wf.log_fallback:
                lines.append("\n_(no structured test failures — sanitized job log)_\n\n")
                lines.append(f"```\n{wf.log_fallback}\n```\n")
            else:
                lines.append("\n_(no structured failures parsed)_\n")
            continue
        for failure in wf.failures:
            lines.append(f"\n### ✗ {failure.test_name}\n\n")
            lines.append(f"**File:** `{failure.file or 'unknown'}`  \n")
            lines.append(f"```\n{failure.error_message}\n```\n")
            if failure.stack_trace:
                lines.append(f"\n```\n{failure.stack_trace}\n```\n")
    output.write_text("".join(lines), encoding="utf-8")


def render_sanitized_log(text: str, output: Path | None) -> None:
    print(text)
    if output:
        output.write_text(text, encoding="utf-8")
