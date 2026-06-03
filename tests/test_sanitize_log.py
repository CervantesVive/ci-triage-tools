from ci_triage_tools.sanitize_log import sanitize

# Compact representative slice of a real GitHub Actions log
SAMPLE_LOG = """\
2026-06-03T00:58:54.2970238Z Current runner version: '2.334.0'
2026-06-03T00:58:54.2994451Z ##[group]Runner Image Provisioner
2026-06-03T00:58:54.2995943Z Version: 20260128.488
2026-06-03T00:58:54.2998634Z ##[endgroup]
2026-06-03T00:58:56.9872868Z ##[group]Run actions/checkout@v6
2026-06-03T00:58:56.9873540Z with:
2026-06-03T00:58:56.9873849Z   ref: b12f782158119c0ea77b2ce60ae530a6e1691541
2026-06-03T00:58:56.9877344Z   token: ***
2026-06-03T00:58:56.9881143Z ##[endgroup]
2026-06-03T00:59:02.7021043Z Updating files:  45% (8957/19733)
2026-06-03T00:59:02.7135033Z Updating files:  46% (9078/19733)
2026-06-03T00:59:36.4168379Z Scope: all 18 workspace projects
2026-06-03T00:59:37.1604046Z Packages: +4615
2026-06-03T00:59:37.1778429Z ++++++++++++++++++++++++++++++++++++++++++++++++++
2026-06-03T00:59:43.6699264Z ##[group]Run pnpm test:shard --reporter=blob
2026-06-03T00:59:43.6700111Z pnpm test:shard --reporter=blob
2026-06-03T00:59:43.6731400Z shell: /usr/bin/bash -e {0}
2026-06-03T00:59:43.6732273Z env:
2026-06-03T00:59:43.6732862Z   VITEST_SHARD_NUMBER: 4
2026-06-03T00:59:43.6782998Z   VITEST_SHARD_TOTAL: 16
2026-06-03T00:59:43.6782184Z ##[endgroup]
2026-06-03T01:01:03.8743696Z blob report written to .vitest-reports/blob-4-16.json
2026-06-03T01:01:04.0531955Z  ELIFECYCLE  Command failed with exit code 1.
2026-06-03T01:01:04.0765574Z ##[error]Process completed with exit code 1.
2026-06-03T01:01:05.1258553Z Post job cleanup.
2026-06-03T01:01:05.1328796Z Cleaning up orphan processes
"""

ANSI_LOG = (
    "2026-06-03T00:59:43.6699264Z ##[group]Run pnpm test:shard\n"
    "2026-06-03T01:00:00.0000000Z \x1b[31mERROR\x1b[0m: something failed"
)


def test_discards_pre_sentinel_content():
    result = sanitize(SAMPLE_LOG)
    assert "Runner Image Provisioner" not in result
    assert "actions/checkout@v6" not in result
    assert "Scope: all 18 workspace projects" not in result


def test_drops_progress_bars():
    result = sanitize(SAMPLE_LOG)
    assert "Updating files:" not in result


def test_drops_pnpm_install_noise():
    result = sanitize(SAMPLE_LOG)
    assert "Packages: +4615" not in result
    assert "++++++++++" not in result


def test_drops_env_block_values():
    result = sanitize(SAMPLE_LOG)
    assert "VITEST_SHARD_NUMBER" not in result
    assert "VITEST_SHARD_TOTAL" not in result


def test_keeps_sentinel_line():
    result = sanitize(SAMPLE_LOG)
    assert "Run pnpm test:shard --reporter=blob" in result


def test_keeps_error_lines():
    result = sanitize(SAMPLE_LOG)
    assert "##[error]Process completed with exit code 1." in result
    assert "ELIFECYCLE" in result


def test_keeps_blob_report_line():
    result = sanitize(SAMPLE_LOG)
    assert "blob report written to" in result


def test_preserves_timestamps_on_error_lines():
    result = sanitize(SAMPLE_LOG)
    assert "2026-06-03T01:01:04.0765574Z ##[error]" in result


def test_discards_post_cleanup():
    result = sanitize(SAMPLE_LOG)
    assert "Post job cleanup." not in result
    assert "Cleaning up orphan processes" not in result


def test_strips_ansi_codes():
    result = sanitize(ANSI_LOG)
    assert "\x1b[" not in result
    assert "ERROR" in result


def test_empty_input():
    assert sanitize("") == ""
