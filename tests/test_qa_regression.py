"""Unit tests for qa_signoff.regression — load_regression."""

from pathlib import Path

import pytest

from aiflow_demo.qa_signoff.regression import load_regression

FIXTURES = Path(__file__).parent / "fixtures" / "qa"


class TestPassingJunit:
    def test_passing_junit_verdict_is_pass(self):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.verdict == "PASS"
        assert result.available is True

    def test_passing_junit_counts(self):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.total == 3
        assert result.passed == 3
        assert result.failed == 0
        assert result.errors == 0
        assert result.skipped == 0

    def test_passing_junit_duration(self):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.duration_s == pytest.approx(0.42)

    def test_passing_junit_no_failures(self):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.failures == ()


class TestFailingJunit:
    def test_failing_junit_verdict_is_fail(self):
        result = load_regression(
            FIXTURES / "pytest-report.failing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.verdict == "FAIL"

    def test_failing_junit_counts(self):
        result = load_regression(
            FIXTURES / "pytest-report.failing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.total == 3
        assert result.failed == 1
        assert result.skipped == 1
        assert result.errors == 0

    def test_failing_junit_failure_ids_and_messages(self):
        result = load_regression(
            FIXTURES / "pytest-report.failing.xml",
            FIXTURES / "coverage.json",
        )
        assert len(result.failures) == 1
        assert result.failures[0].test_id == "tests.test_y.test_fail"
        assert "assert 1 == 2" in result.failures[0].message


class TestCoverage:
    def test_coverage_pct_read(self):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            FIXTURES / "coverage.json",
        )
        assert result.coverage_pct == pytest.approx(87.5)

    def test_missing_coverage_keeps_counts_pct_none(self, tmp_path: Path):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            tmp_path / "nonexistent.json",
        )
        assert result.available is True
        assert result.total == 3
        assert result.coverage_pct is None

    def test_malformed_coverage_pct_none(self):
        result = load_regression(
            FIXTURES / "pytest-report.passing.xml",
            FIXTURES / "coverage.malformed.json",
        )
        assert result.available is True
        assert result.coverage_pct is None


class TestMissingAndMalformedJunit:
    def test_missing_junit_returns_unavailable(self, tmp_path: Path):
        result = load_regression(
            tmp_path / "nonexistent.xml",
            FIXTURES / "coverage.json",
        )
        assert result.available is False
        assert result.verdict == "FAIL"

    def test_missing_junit_no_exception_raised(self, tmp_path: Path):
        result = load_regression(
            tmp_path / "nonexistent.xml",
            FIXTURES / "coverage.json",
        )
        assert result is not None

    def test_malformed_xml_returns_unavailable(self, tmp_path: Path):
        bad_xml = tmp_path / "bad.xml"
        bad_xml.write_text("<broken><<", encoding="utf-8")
        result = load_regression(bad_xml, FIXTURES / "coverage.json")
        assert result.available is False


class TestMultiTestsuite:
    def test_multi_testsuite_counts_summed(self, tmp_path: Path):
        xml = tmp_path / "multi.xml"
        xml.write_text(
            '<?xml version="1.0"?>'
            "<testsuites>"
            '<testsuite name="s1" tests="2" failures="0" errors="0" skipped="0" time="0.1">'
            '<testcase classname="a" name="t1"/>'
            '<testcase classname="a" name="t2"/>'
            "</testsuite>"
            '<testsuite name="s2" tests="1" failures="1" errors="0" skipped="0" time="0.2">'
            '<testcase classname="b" name="t3"><failure message="boom"/></testcase>'
            "</testsuite>"
            "</testsuites>",
            encoding="utf-8",
        )
        result = load_regression(xml, tmp_path / "no.json")
        assert result.total == 3
        assert result.failed == 1
        assert result.passed == 2

    def test_single_testsuite_root_without_wrapper(self, tmp_path: Path):
        xml = tmp_path / "single.xml"
        xml.write_text(
            '<?xml version="1.0"?>'
            '<testsuite name="pytest" tests="2" failures="0" errors="0" skipped="0" time="0.5">'
            '<testcase classname="x" name="t1"/>'
            '<testcase classname="x" name="t2"/>'
            "</testsuite>",
            encoding="utf-8",
        )
        result = load_regression(xml, tmp_path / "no.json")
        assert result.total == 2
        assert result.available is True
