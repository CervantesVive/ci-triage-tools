import json
from pathlib import Path
import pytest
from ci_triage_tools.parse_vitest import parse_blob

# Vitest blob reporter format: a flat intern table where every string-digit
# dict value is a reference to data[int(val)]. We build minimal blobs here
# that mirror the real format observed from actual CI artifacts.
#
# Index layout used by all fixtures below:
#   0  "4.1.0"                    version
#   1  "pass"                     state literal
#   2  "fail"                     state literal
#   3  "test"                     type literal
#   4  "suite"                    type literal
#   5  "run"                      mode literal
#   6  <file-task name>           relative filepath string
#   7  <test fullName>            fully-qualified test name
#   8  <test name>                bare test name
#   9  <error message>            error message string
#  10  <stack trace>              stack trace string
#  11  {"message":"9","stack":"10"}  error object
#  12  ["11"]                     errors list
#  13  {"state":"2","errors":"12",...}  failing result
#  14  {"state":"1",...}          passing result
#  15  {"id":...,"name":"6","type":"4","result":"14","file":"15",...}  file task (self-ref at 15)
#  16  {"id":...,"name":"8","fullName":"7","type":"3","result":"13","file":"15",...} failing test task


def _make_blob(
    file_name: str = "src/Button.test.tsx",
    test_full_name: str = "Button > renders correctly",
    test_name: str = "renders correctly",
    error_msg: str = "AssertionError: expected 'foo'",
    stack: str = "AssertionError\n    at Button.test.tsx:5",
) -> list:
    return [
        "4.1.0",                            # 0
        "pass",                             # 1
        "fail",                             # 2
        "test",                             # 3
        "suite",                            # 4
        "run",                              # 5
        file_name,                          # 6 — file task name
        test_full_name,                     # 7 — test fullName
        test_name,                          # 8 — test name
        error_msg,                          # 9
        stack,                              # 10
        {"message": "9", "stack": "10"},    # 11 — error object
        ["11"],                             # 12 — errors list
        {"state": "2", "errors": "12", "startTime": 0, "duration": 1},   # 13 — fail result
        {"state": "1", "startTime": 0, "duration": 100},                 # 14 — pass result
        {                                   # 15 — file task (self-ref via "file":"15")
            "id": "-1", "name": "6", "fullName": "6",
            "type": "4", "mode": "5",
            "filepath": "6", "result": "14", "file": "15",
            "tasks": "16",
        },
        {                                   # 16 — failing test task
            "id": "-2", "name": "8", "fullName": "7",
            "type": "3", "mode": "5",
            "result": "13", "file": "15",
        },
    ]


def test_extracts_failure(tmp_path: Path):
    blob = tmp_path / "blob-4-16.json"
    blob.write_text(json.dumps(_make_blob()))

    failures = parse_blob(blob)

    assert len(failures) == 1


def test_failure_fields(tmp_path: Path):
    blob = tmp_path / "blob-4-16.json"
    blob.write_text(json.dumps(_make_blob()))

    failures = parse_blob(blob)
    f = failures[0]

    assert f.test_name == "Button > renders correctly"
    assert f.file == "src/Button.test.tsx"
    assert "expected 'foo'" in f.error_message
    assert f.stack_trace is not None
    assert "Button.test.tsx:5" in f.stack_trace
    assert f.source == "vitest"


def test_skips_passing_tests(tmp_path: Path):
    # Build a blob with only a passing test task (result -> state -> "pass")
    data = list(_make_blob())
    # Replace the failing test task at index 16 with a passing one
    data[16] = {
        "id": "-2", "name": "8", "fullName": "7",
        "type": "3", "mode": "5",
        "result": "14",   # -> pass result
        "file": "15",
    }
    blob = tmp_path / "blob-1-16.json"
    blob.write_text(json.dumps(data))

    failures = parse_blob(blob)

    assert failures == []


def test_skips_suite_type_entries(tmp_path: Path):
    # File tasks (type="suite") must not be collected as failures
    data = list(_make_blob())
    # Verify the file task (index 15) is not included
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps(data))

    failures = parse_blob(blob)

    # Only one failure (the test task), not the file task
    assert len(failures) == 1
    assert failures[0].test_name == "Button > renders correctly"


def test_nested_full_name(tmp_path: Path):
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps(_make_blob(
        test_full_name="Outer > Inner > deep test",
        test_name="deep test",
    )))

    failures = parse_blob(blob)

    assert failures[0].test_name == "Outer > Inner > deep test"


def test_tolerates_missing_errors(tmp_path: Path):
    data = list(_make_blob())
    # Replace fail result with one that has no errors list
    data[13] = {"state": "2", "startTime": 0, "duration": 1}
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps(data))

    failures = parse_blob(blob)

    assert len(failures) == 1
    assert failures[0].error_message == ""
    assert failures[0].stack_trace is None


def test_returns_empty_for_non_list_json(tmp_path: Path):
    blob = tmp_path / "blob.json"
    blob.write_text(json.dumps({"not": "the right format"}))

    assert parse_blob(blob) == []
