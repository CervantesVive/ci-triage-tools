import io
import json
import zipfile
from pathlib import Path
import pytest
from ci_triage_tools.parse_playwright import parse_blob


def _make_zip(report_data: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("report.json", json.dumps(report_data))
    return buf.getvalue()


SUITES_REPORT = {
    "suites": [
        {
            "title": "Authentication",
            "suites": [],
            "specs": [
                {
                    "title": "should redirect after login",
                    "file": "tests/auth.spec.ts",
                    "tests": [
                        {
                            "projectName": "chromium",
                            "annotations": [],
                            "results": [
                                {
                                    "status": "failed",
                                    "errors": [
                                        {
                                            "message": "Error: Locator not found: button[type=submit]",
                                            "stack": "Error: Locator not found\n    at auth.spec.ts:25:10",
                                        }
                                    ],
                                    "attachments": [],
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]
}

PASSING_REPORT = {
    "suites": [
        {
            "title": "Smoke",
            "suites": [],
            "specs": [
                {
                    "title": "homepage loads",
                    "file": "tests/smoke.spec.ts",
                    "tests": [
                        {
                            "projectName": "chromium",
                            "annotations": [],
                            "results": [{"status": "passed", "errors": [], "attachments": []}],
                        }
                    ],
                }
            ],
        }
    ]
}


def test_parse_blob_suites_format(tmp_path: Path):
    zip_file = tmp_path / "report.zip"
    zip_file.write_bytes(_make_zip(SUITES_REPORT))

    failures = parse_blob(zip_file)

    assert len(failures) == 1
    f = failures[0]
    assert f.test_name == "Authentication > should redirect after login"
    assert f.file == "tests/auth.spec.ts"
    assert "Locator not found" in f.error_message
    assert f.source == "playwright"


def test_parse_blob_no_failures(tmp_path: Path):
    zip_file = tmp_path / "report.zip"
    zip_file.write_bytes(_make_zip(PASSING_REPORT))

    assert parse_blob(zip_file) == []


def test_parse_blob_stack_trace(tmp_path: Path):
    zip_file = tmp_path / "report.zip"
    zip_file.write_bytes(_make_zip(SUITES_REPORT))

    failures = parse_blob(zip_file)

    assert failures[0].stack_trace is not None
    assert "auth.spec.ts:25" in failures[0].stack_trace
