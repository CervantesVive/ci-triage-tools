# ci-triage

PR-centric CI failure triage. Given a GitHub PR URL, downloads all failing CI artifacts (Vitest unit test blobs and Playwright e2e blobs), parses them into structured failures, and renders a clean summary grouped by workflow. Also accepts a raw GitHub Actions log file for noise-stripped inspection.

## Install

```bash
uv tool install .
```

Or within the workspace:
```bash
uv sync
uv run ci-triage --help
```

## Prerequisites

The `gh` CLI must be installed and authenticated against GitHub:

```bash
gh auth login
```

## Commands

| Command | Description |
|---------|-------------|
| `ci-triage analyze <pr-url>` | Download all failing CI runs for a PR, parse failures, render summary |
| `ci-triage from-file <path>` | Strip CI noise from a previously downloaded raw GitHub Actions log |

## Usage

```bash
# Analyze all failing runs for a PR
ci-triage analyze https://github.com/octocat/Hello-World/pull/1347

# Also write a markdown file
ci-triage analyze https://github.com/octocat/Hello-World/pull/1347 --output triage.md

# Bust the artifact cache and re-download
ci-triage analyze https://github.com/octocat/Hello-World/pull/1347 --refresh

# Verbose output
ci-triage analyze https://github.com/octocat/Hello-World/pull/1347 -v

# Inspect a raw log file (strips CI noise, keeps errors + stack traces)
ci-triage from-file /path/to/job.log

# Inspect and also write the sanitized output
ci-triage from-file /path/to/job.log --output sanitized.md
```

## Output

Terminal output always. Failures are grouped by workflow:

```
━━━ Run Unit Tests (shard 4/16) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FAIL  src/components/Button.test.tsx
        Button > renders correctly
        Expected: "Submit"
        Received: "Send"
        at Button.test.tsx:42

━━━ E2E Tests ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  FAIL  Login flow > should redirect after login
        ...
```

`--output` additionally writes a markdown file with the same structure.

## Cache

Parsed failures are cached at `~/.cache/ci-triage/{run_id}/failures.json`. Artifacts are cached at `~/.cache/ci-triage/{run_id}/artifacts/`. Repeat runs hit the cache instead of re-downloading. Use `--refresh` to force a re-download.

## Supported artifact types

| Artifact name pattern | Type | Notes |
|-----------------------|------|-------|
| `blob-report-*` | Vitest blob JSON | Sharded — all shards are merged |
| `*playwright*`, `*e2e*blob*` | Playwright blob ZIP | Contains `report.json` or `.jsonl` |
| anything else | skipped | Warning printed to stderr |

## Log sanitization (`from-file`)

Strips GitHub Actions infrastructure noise:
- Everything before the first `##[group]Run pnpm ...` sentinel (setup/checkout)
- Everything after `Post job cleanup.`
- ANSI escape codes, progress bars, pnpm install noise, git internal commands

Always preserves: `##[error]` lines, `FAIL`, `Error:`, stack traces (`at ... .ts:N`), timestamps.
