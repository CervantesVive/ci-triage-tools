import pytest
from ci_triage_tools.github import parse_pr_url


def test_parse_pr_url_standard():
    owner, repo, number = parse_pr_url("https://github.com/octocat/Hello-World/pull/6537")
    assert owner == "octocat"
    assert repo == "Hello-World"
    assert number == 6537


def test_parse_pr_url_trailing_slash():
    owner, repo, number = parse_pr_url("https://github.com/octocat/Hello-World/pull/6537/")
    assert owner == "octocat"
    assert repo == "Hello-World"
    assert number == 6537


def test_parse_pr_url_rejects_issue_url():
    with pytest.raises(ValueError, match="Not a valid GitHub PR URL"):
        parse_pr_url("https://github.com/octocat/Hello-World/issues/123")


def test_parse_pr_url_rejects_non_github():
    with pytest.raises(ValueError, match="Not a valid GitHub PR URL"):
        parse_pr_url("https://gitlab.com/owner/repo/merge_requests/1")


def test_parse_pr_url_rejects_plain_string():
    with pytest.raises(ValueError, match="Not a valid GitHub PR URL"):
        parse_pr_url("not-a-url")
