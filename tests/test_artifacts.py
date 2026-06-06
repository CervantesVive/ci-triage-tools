import pytest
from ci_triage_tools.artifacts import detect_artifact_type


@pytest.mark.parametrize("name, expected", [
    # vitest
    ("blob-report-1", "vitest"),
    ("blob-report-16", "vitest"),
    ("blob-report-shard-4-16", "vitest"),
    # playwright
    ("playwright-report", "playwright"),
    ("Playwright-Blob-Report", "playwright"),
    ("e2e-blob-5", "playwright"),
    ("e2e-blob-report", "playwright"),
    # known non-test — silently skipped
    ("coverage-merged", "skip"),
    ("coverage-report", "skip"),
    ("merge-coverage", "skip"),
    ("matrix-artifacts", "skip"),
    ("deploy-metrics-app", "skip"),
    ("deploy-metrics-web", "skip"),
    # truly unknown — should warn
    ("some-random-artifact", None),
    ("blob-report", None),   # no suffix after dash → no match
    ("vitest-results", None),
])
def test_detect_artifact_type(name, expected):
    assert detect_artifact_type(name) == expected
