"""Tests for scope parsing, verdicts, and CLI exit codes."""
import json

import pytest
from click.testing import CliRunner

from scopematrix.cli import main
from scopematrix.scope import Scope, ScopeError, check, summary

SCOPE_TEXT = """
# demo program scope
+ *.example.com
- admin.example.com
+ https://api.other.org/v1
+ 10.0.0.0/24
+ reports@bugzilla.example.org
"""


def make_scope() -> Scope:
    return Scope.parse(SCOPE_TEXT)


def test_parse_counts_and_kinds():
    scope = make_scope()
    info = summary(scope)
    assert info["total"] == 5
    assert info["includes"] == 4
    assert info["excludes"] == 1
    assert info["by_kind"] == {"wildcard": 1, "domain": 1, "url": 1, "cidr": 1,
                               "email": 1}


def test_wildcard_includes_subdomains():
    scope = make_scope()
    assert check(scope, "www.example.com")["verdict"] == "in-scope"
    assert check(scope, "a.b.example.com")["verdict"] == "in-scope"
    assert check(scope, "example.com")["verdict"] == "in-scope"


def test_exclude_wins_over_include():
    scope = make_scope()
    v = check(scope, "admin.example.com")
    assert v["verdict"] == "out-of-scope"
    assert "exclude" in v["reason"]


def test_url_include_matches_scheme_host_path():
    scope = make_scope()
    assert check(scope, "https://api.other.org/v1/users")["verdict"] == "in-scope"
    assert check(scope, "http://api.other.org/v1/users")["verdict"] == "out-of-scope"
    assert check(scope, "https://api.other.org/v2/users")["verdict"] == "out-of-scope"


def test_cidr_matching_only_for_ips():
    scope = make_scope()
    assert check(scope, "10.0.0.7")["verdict"] == "in-scope"
    assert check(scope, "11.0.0.7")["verdict"] == "out-of-scope"
    # a hostname under an unrelated domain doesn't match the cidr entry
    assert check(scope, "other.net")["verdict"] == "out-of-scope"


def test_no_include_match_is_out():
    scope = make_scope()
    assert check(scope, "notlisted.io")["verdict"] == "out-of-scope"


def test_rejects_malformed_scope():
    with pytest.raises(ScopeError):
        Scope.parse("just some text\n")
    with pytest.raises(ScopeError):
        Scope.parse("# nothing but comments\n")


def test_rejects_unclassifiable_pattern():
    with pytest.raises(ScopeError):
        Scope.parse("+ ???bad???")


def test_cli_parse_and_check_exit_codes():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("scope.txt", "w") as fh:
            fh.write(SCOPE_TEXT)
        parsed = runner.invoke(main, ["parse", "scope.txt", "--json-out"])
        assert parsed.exit_code == 0, parsed.output
        assert json.loads(parsed.output)["total"] == 5

        inside = runner.invoke(main, ["check", "scope.txt", "www.example.com"])
        assert inside.exit_code == 0, inside.output
        assert "in-scope" in inside.output

        outside = runner.invoke(main, ["check", "scope.txt", "admin.example.com"])
        assert outside.exit_code == 1, outside.output
        assert "out-of-scope" in outside.output


def test_cli_batch_exit_code():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("scope.txt", "w") as fh:
            fh.write(SCOPE_TEXT)
        with open("assets.txt", "w") as fh:
            fh.write("www.example.com\n# comment\nadmin.example.com\n")
        result = runner.invoke(main, ["batch", "scope.txt", "assets.txt"])
        assert result.exit_code == 1, result.output
        assert "2 checked, 1 out of scope" in result.output


def test_cli_bad_scope_file_exits_2():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open("scope.txt", "w") as fh:
            fh.write("garbage line\n")
        result = runner.invoke(main, ["parse", "scope.txt"])
        assert result.exit_code == 2, result.output