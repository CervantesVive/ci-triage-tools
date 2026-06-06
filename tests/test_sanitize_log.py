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


# gh run view --log-failed output format: <workflow>/<job>\t<step>\t<timestamp> <content>
PREFIXED_LOG = (
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:45.1778285Z ##[group]Run pnpm install\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:45.1808318Z shell: /usr/bin/bash -e {0}\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:45.1808594Z env:\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:45.1809069Z   PNPM_HOME: /home/runner/setup-pnpm/node_modules/.bin\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:45.1809438Z   NPM_TOKEN: ***\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:45.1816024Z ##[endgroup]\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:27:54.3863131Z ##[group]Run pnpm test:shard --reporter=blob\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:29:26.5270381Z  ELIFECYCLE  Command failed with exit code 1.\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:29:26.5490306Z ##[error]Process completed with exit code 1.\n"
    "Run Unit Tests / unit-test-web-shard (2, 16)\tUNKNOWN STEP\t"
    "2026-06-06T05:29:27.0000000Z Post job cleanup.\n"
)


def test_prefixed_format_drops_env_block():
    result = sanitize(PREFIXED_LOG)
    assert "PNPM_HOME" not in result
    assert "NPM_TOKEN" not in result


def test_prefixed_format_keeps_sentinel():
    result = sanitize(PREFIXED_LOG)
    assert "Run pnpm test:shard --reporter=blob" in result


def test_prefixed_format_keeps_error_lines():
    result = sanitize(PREFIXED_LOG)
    assert "ELIFECYCLE" in result
    assert "##[error]Process completed with exit code 1." in result


def test_prefixed_format_discards_post_cleanup():
    result = sanitize(PREFIXED_LOG)
    assert "Post job cleanup." not in result


# Combined multi-job log: shard job followed by merge-coverage job.
# Verify that the second job's failure is not discarded by the first job's cleanup.
MULTI_JOB_LOG = (
    # === Shard job ===
    "Shard / shard-2\tUNKNOWN STEP\t2026-06-06T05:27:54.0000000Z ##[group]Run pnpm test:shard\n"
    "Shard / shard-2\tUNKNOWN STEP\t2026-06-06T05:29:26.0000000Z  ELIFECYCLE  Command failed with exit code 1.\n"
    "Shard / shard-2\tUNKNOWN STEP\t2026-06-06T05:29:26.1000000Z ##[error]Process completed with exit code 1.\n"
    "Shard / shard-2\tUNKNOWN STEP\t2026-06-06T05:29:27.0000000Z Post job cleanup.\n"
    # === Merge-coverage job ===
    "Merge / merge-cov\tUNKNOWN STEP\t2026-06-06T05:30:48.0000000Z ##[group]Runner Image Provisioner\n"
    "Merge / merge-cov\tUNKNOWN STEP\t2026-06-06T05:30:48.1000000Z ##[group]Run pnpm vitest --run --merge-reports\n"
    "Merge / merge-cov\tUNKNOWN STEP\t2026-06-06T05:32:02.0000000Z ReferenceError: window is not defined\n"
    "Merge / merge-cov\tUNKNOWN STEP\t2026-06-06T05:32:02.1000000Z ##[error]Process completed with exit code 1.\n"
    "Merge / merge-cov\tUNKNOWN STEP\t2026-06-06T05:32:03.0000000Z Post job cleanup.\n"
)


def test_multi_job_log_captures_both_jobs():
    result = sanitize(MULTI_JOB_LOG)
    assert "ELIFECYCLE" in result
    assert "ReferenceError: window is not defined" in result


def test_multi_job_log_discards_both_cleanups():
    result = sanitize(MULTI_JOB_LOG)
    assert "Post job cleanup." not in result


def test_multi_job_log_discards_preamble_between_jobs():
    result = sanitize(MULTI_JOB_LOG)
    assert "Runner Image Provisioner" not in result
