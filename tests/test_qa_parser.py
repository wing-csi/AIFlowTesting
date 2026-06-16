"""Unit tests for qa_signoff.parser — parse_testcase_file."""

from pathlib import Path

import pytest

from aiflow_demo.qa_signoff.parser import parse_testcase_file

FIXTURES = Path(__file__).parent / "fixtures" / "qa"


class TestParseSingleSection:
    def test_single_section_with_cases(self):
        text = (
            "## 2026-06-10 09:00:00 — First task\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 1 | Cart adds item | unit | tests/test_cart.py | new cart returned |\n"
        )
        outcome = parse_testcase_file(text)
        assert len(outcome.sections) == 1
        section = outcome.sections[0]
        assert section.datetime == "2026-06-10 09:00:00"
        assert section.title == "First task"
        assert len(section.cases) == 1
        assert section.cases[0].number == 1
        assert section.cases[0].description == "Cart adds item"
        assert section.cases[0].type == "unit"
        assert section.cases[0].test_file == "tests/test_cart.py"
        assert section.cases[0].expected == "new cart returned"

    def test_intro_captured_before_table(self):
        text = (
            "## 2026-06-10 09:00:00 — Task\n\n"
            "This is the intro paragraph.\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 1 | A test | unit | f.py | ok |\n"
        )
        outcome = parse_testcase_file(text)
        assert "intro paragraph" in outcome.sections[0].intro

    def test_section_with_no_table_has_empty_cases(self):
        text = "## 2026-06-10 09:00:00 — No table\n\nJust prose, no table.\n"
        outcome = parse_testcase_file(text)
        assert len(outcome.sections) == 1
        assert outcome.sections[0].cases == ()

    def test_empty_file_returns_empty_sections_and_zero_warnings(self):
        outcome = parse_testcase_file("")
        assert outcome.sections == ()
        assert outcome.warnings == 0

    def test_h1_line_ignored(self):
        text = (
            "# Test cases — feature/sample\n\n"
            "## 2026-06-10 09:00:00 — Task\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 1 | A test | unit | f.py | ok |\n"
        )
        outcome = parse_testcase_file(text)
        assert len(outcome.sections) == 1

    def test_pipes_and_whitespace_trimmed(self):
        text = (
            "## 2026-06-10 09:00:00 — Task\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "|  2  |  Some test  |  integration  |  tests/t.py  |  passes  |\n"
        )
        outcome = parse_testcase_file(text)
        case = outcome.sections[0].cases[0]
        assert case.number == 2
        assert case.description == "Some test"
        assert case.type == "integration"
        assert case.test_file == "tests/t.py"
        assert case.expected == "passes"

    def test_non_integer_number_tolerated(self):
        text = (
            "## 2026-06-10 09:00:00 — Task\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| N/A | A test | unit | f.py | ok |\n"
        )
        outcome = parse_testcase_file(text)
        assert len(outcome.sections[0].cases) == 1
        assert outcome.sections[0].cases[0].number == 0


class TestParseMultipleSections:
    def test_multiple_sections_ordered_and_attributed(self):
        text = (
            "## 2026-06-10 09:00:00 — First\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 1 | A | unit | f.py | ok |\n\n"
            "## 2026-06-11 10:30:00 — Second\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 2 | B | integration | g.py | done |\n"
        )
        outcome = parse_testcase_file(text)
        assert len(outcome.sections) == 2
        assert outcome.sections[0].datetime == "2026-06-10 09:00:00"
        assert outcome.sections[0].title == "First"
        assert outcome.sections[1].datetime == "2026-06-11 10:30:00"
        assert outcome.sections[1].title == "Second"
        assert outcome.sections[1].cases[0].description == "B"


class TestParseWarnings:
    def test_malformed_row_skipped_and_counted(self):
        text = (
            "## 2026-06-10 09:00:00 — Task\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 1 | Good row | unit | f.py | ok |\n"
            "| too few cells |\n"
            "| 3 | Another good | unit | g.py | pass |\n"
        )
        outcome = parse_testcase_file(text)
        assert len(outcome.sections[0].cases) == 2
        assert outcome.warnings == 1


class TestFixtureFile:
    def test_fixture_parses_correctly(self):
        text = (FIXTURES / "sample_testcases.md").read_text(encoding="utf-8")
        outcome = parse_testcase_file(text)
        assert len(outcome.sections) == 2
        assert outcome.sections[0].title == "First task"
        assert outcome.sections[1].title == "Second task"
        assert len(outcome.sections[0].cases) == 2
        assert outcome.warnings >= 1

    def test_fixture_second_section_has_valid_cases_only(self):
        text = (FIXTURES / "sample_testcases.md").read_text(encoding="utf-8")
        outcome = parse_testcase_file(text)
        valid_cases = outcome.sections[1].cases
        assert len(valid_cases) == 2
