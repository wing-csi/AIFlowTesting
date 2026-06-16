"""Unit tests for qa_signoff.models — frozen dataclasses and domain logic."""

import pytest
from dataclasses import FrozenInstanceError

from aiflow_demo.qa_signoff.models import (
    FailureDetail,
    ParseOutcome,
    QaDocument,
    RegressionResult,
    SignoffMeta,
    TestCase,
    TestSection,
)


class TestTestCase:
    def test_fields_populate(self):
        tc = TestCase(
            number=1,
            description="Cart adds item",
            type="unit",
            test_file="tests/test_cart.py",
            expected="new cart returned",
        )
        assert tc.number == 1
        assert tc.description == "Cart adds item"
        assert tc.type == "unit"
        assert tc.test_file == "tests/test_cart.py"
        assert tc.expected == "new cart returned"

    def test_frozen_raises_on_mutation(self):
        tc = TestCase(1, "desc", "unit", "f.py", "ok")
        with pytest.raises(FrozenInstanceError):
            tc.number = 99  # type: ignore[misc]


class TestTestSection:
    def test_fields_populate(self):
        tc = TestCase(1, "desc", "unit", "f.py", "ok")
        section = TestSection(
            datetime="2026-06-10 09:00:00",
            title="First task",
            intro="An intro.",
            cases=(tc,),
        )
        assert section.datetime == "2026-06-10 09:00:00"
        assert section.title == "First task"
        assert section.intro == "An intro."
        assert len(section.cases) == 1

    def test_default_intro_is_empty(self):
        section = TestSection(datetime="2026-06-10 09:00:00", title="T")
        assert section.intro == ""

    def test_default_cases_is_empty_tuple(self):
        section = TestSection(datetime="2026-06-10 09:00:00", title="T")
        assert section.cases == ()

    def test_frozen_raises_on_mutation(self):
        section = TestSection(datetime="2026-06-10 09:00:00", title="T")
        with pytest.raises(FrozenInstanceError):
            section.title = "changed"  # type: ignore[misc]


class TestFailureDetail:
    def test_fields_populate(self):
        fd = FailureDetail(test_id="tests.test_x.test_a", message="assert 1==2")
        assert fd.test_id == "tests.test_x.test_a"
        assert fd.message == "assert 1==2"

    def test_frozen_raises_on_mutation(self):
        fd = FailureDetail(test_id="x.y", message="msg")
        with pytest.raises(FrozenInstanceError):
            fd.message = "changed"  # type: ignore[misc]


class TestRegressionResult:
    def test_fields_populate(self):
        rr = RegressionResult(
            total=3,
            passed=2,
            failed=1,
            skipped=0,
            errors=0,
            duration_s=1.23,
            coverage_pct=87.5,
            failures=(FailureDetail("x.y", "msg"),),
            available=True,
        )
        assert rr.total == 3
        assert rr.passed == 2
        assert rr.failed == 1
        assert rr.coverage_pct == 87.5
        assert rr.available is True

    def test_unavailable_classmethod_shape(self):
        rr = RegressionResult.unavailable()
        assert rr.total == 0
        assert rr.passed == 0
        assert rr.failed == 0
        assert rr.skipped == 0
        assert rr.errors == 0
        assert rr.duration_s == 0.0
        assert rr.coverage_pct is None
        assert rr.failures == ()
        assert rr.available is False

    def test_verdict_pass_when_available_and_clean(self):
        rr = RegressionResult(
            total=3,
            passed=3,
            failed=0,
            skipped=0,
            errors=0,
            duration_s=0.5,
            coverage_pct=90.0,
            failures=(),
            available=True,
        )
        assert rr.verdict == "PASS"

    def test_verdict_fail_when_failures_present(self):
        rr = RegressionResult(
            total=3,
            passed=2,
            failed=1,
            skipped=0,
            errors=0,
            duration_s=0.5,
            coverage_pct=90.0,
            failures=(FailureDetail("x.y", "msg"),),
            available=True,
        )
        assert rr.verdict == "FAIL"

    def test_verdict_fail_when_unavailable(self):
        rr = RegressionResult.unavailable()
        assert rr.verdict == "FAIL"

    def test_verdict_fail_when_errors_nonzero(self):
        rr = RegressionResult(
            total=3,
            passed=2,
            failed=0,
            skipped=0,
            errors=1,
            duration_s=0.5,
            coverage_pct=None,
            failures=(),
            available=True,
        )
        assert rr.verdict == "FAIL"

    def test_frozen_raises_on_mutation(self):
        rr = RegressionResult.unavailable()
        with pytest.raises(FrozenInstanceError):
            rr.total = 99  # type: ignore[misc]


class TestSignoffMeta:
    def test_fields_populate(self):
        meta = SignoffMeta(
            project="AIFlowTesting",
            branch="feature/qa-signoff-doc",
            tag="v1.0.0",
            sha="abc1234",
            generated_at="2026-06-16T12:00:00+00:00",
        )
        assert meta.project == "AIFlowTesting"
        assert meta.branch == "feature/qa-signoff-doc"
        assert meta.tag == "v1.0.0"
        assert meta.sha == "abc1234"
        assert meta.generated_at == "2026-06-16T12:00:00+00:00"

    def test_frozen_raises_on_mutation(self):
        meta = SignoffMeta("P", "b", "v1", "sha", "ts")
        with pytest.raises(FrozenInstanceError):
            meta.project = "Other"  # type: ignore[misc]


class TestParseOutcome:
    def test_fields_populate(self):
        section = TestSection(datetime="2026-06-10 09:00:00", title="T")
        outcome = ParseOutcome(sections=(section,), warnings=2)
        assert len(outcome.sections) == 1
        assert outcome.warnings == 2

    def test_frozen_raises_on_mutation(self):
        outcome = ParseOutcome(sections=(), warnings=0)
        with pytest.raises(FrozenInstanceError):
            outcome.warnings = 99  # type: ignore[misc]


class TestQaDocument:
    def test_fields_populate(self):
        meta = SignoffMeta("P", "b", "v1", "sha", "ts")
        rr = RegressionResult.unavailable()
        doc = QaDocument(
            meta=meta,
            sections=(),
            regression=rr,
            gates=("tests", "coverage"),
        )
        assert doc.meta is meta
        assert doc.sections == ()
        assert doc.regression is rr
        assert doc.gates == ("tests", "coverage")

    def test_frozen_raises_on_mutation(self):
        meta = SignoffMeta("P", "b", "v1", "sha", "ts")
        doc = QaDocument(
            meta=meta,
            sections=(),
            regression=RegressionResult.unavailable(),
            gates=(),
        )
        with pytest.raises(FrozenInstanceError):
            doc.gates = ("x",)  # type: ignore[misc]
