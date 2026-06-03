import json
from pathlib import Path
import pytest
from ci_triage_tools.parse_vitest import parse_blob

BLOB_WITH_FAILURES = {
    "version": 2,
    "files": [
        {
            "name": "src/components/Button.test.tsx",
            "type": "suite",
            "tasks": [
                {
                    "type": "suite",
                    "name": "Button",
                    "tasks": [
                        {
                            "type": "test",
                            "name": "renders with correct label",
                            "result": {
                                "state": "fail",
                                "errors": [
                                    {
                                        "message": "AssertionError: expected 'Submit' to equal 'Send'",
                                        "stack": "AssertionError: expected 'Submit' to equal 'Send'\n    at Button.test.tsx:15:5",
                                    }
                                ],
                            },
                        },
                        {
                            "type": "test",
                            "name": "is accessible",
                            "result": {"state": "pass"},
                        },
                    ],
                }
            ],
        },
        {
            "name": "src/hooks/useAuth.test.ts",
            "type": "suite",
            "tasks": [
                {
                    "type": "test",
                    "name": "returns user when authenticated",
                    "result": {
                        "state": "fail",
                        "errors": [
                            {
                                "message": "TypeError: Cannot read properties of undefined (reading 'user')",
                                "stack": "TypeError: Cannot read properties of undefined\n    at useAuth.test.ts:8:21",
                            }
                        ],
                    },
                }
            ],
        },
    ],
}

BLOB_ALL_PASSING = {
    "version": 2,
    "files": [
        {
            "name": "src/utils.test.ts",
            "type": "suite",
            "tasks": [
                {"type": "test", "name": "works", "result": {"state": "pass"}}
            ],
        }
    ],
}


def test_extracts_failures(tmp_path: Path):
    blob = tmp_path / "blob-4-16.json"
    blob.write_text(json.dumps(BLOB_WITH_FAILURES))

    failures = parse_blob(blob)

    assert len(failures) == 2


def test_failure_fields(tmp_path: Path):
    blob = tmp_path / "blob-4-16.json"
    blob.write_text(json.dumps(BLOB_WITH_FAILURES))

    failures = parse_blob(blob)
    button_failure = next(f for f in failures if "Button" in f.test_name)

    assert button_failure.test_name == "Button > renders with correct label"
    assert button_failure.file == "src/components/Button.test.tsx"
    assert "expected 'Submit' to equal 'Send'" in button_failure.error_message
    assert button_failure.source == "vitest"
    assert button_failure.stack_trace is not None
    assert "Button.test.tsx:15" in button_failure.stack_trace


def test_skips_passing_tests(tmp_path: Path):
    blob = tmp_path / "blob-1-16.json"
    blob.write_text(json.dumps(BLOB_ALL_PASSING))

    failures = parse_blob(blob)

    assert failures == []


def test_nested_suite_name(tmp_path: Path):
    data = {
        "version": 2,
        "files": [
            {
                "name": "src/feature.test.ts",
                "type": "suite",
                "tasks": [
                    {
                        "type": "suite",
                        "name": "Outer",
                        "tasks": [
                            {
                                "type": "suite",
                                "name": "Inner",
                                "tasks": [
                                    {
                                        "type": "test",
                                        "name": "deep test",
                                        "result": {
                                            "state": "fail",
                                            "errors": [{"message": "oops", "stack": None}],
                                        },
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps(data))

    failures = parse_blob(blob)

    assert len(failures) == 1
    assert failures[0].test_name == "Outer > Inner > deep test"


def test_bare_list_format(tmp_path: Path):
    # Real Vitest blob reporter output is a bare list, not {"files": [...]}
    data = [
        {
            "name": "src/components/Button.test.tsx",
            "type": "suite",
            "tasks": [
                {
                    "type": "test",
                    "name": "renders correctly",
                    "result": {
                        "state": "fail",
                        "errors": [{"message": "expected true", "stack": "at Button.test.tsx:5"}],
                    },
                }
            ],
        }
    ]
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps(data))

    failures = parse_blob(blob)

    assert len(failures) == 1
    assert failures[0].test_name == "renders correctly"
    assert failures[0].file == "src/components/Button.test.tsx"


def test_tolerates_missing_errors(tmp_path: Path):
    data = {
        "version": 2,
        "files": [
            {
                "name": "src/x.test.ts",
                "type": "suite",
                "tasks": [
                    {
                        "type": "test",
                        "name": "broken",
                        "result": {"state": "fail", "errors": []},
                    }
                ],
            }
        ],
    }
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps(data))

    failures = parse_blob(blob)

    assert len(failures) == 1
    assert failures[0].error_message == ""
    assert failures[0].stack_trace is None
