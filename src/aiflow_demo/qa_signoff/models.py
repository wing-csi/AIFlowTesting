"""Frozen dataclasses for the QA sign-off domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TestCase:
    """A single test case row from a testcase log."""

    __test__ = False  # domain model, not a pytest test class (despite Test* name)

    number: int
    description: str
    type: str
    test_file: str
    expected: str


@dataclass(frozen=True)
class TestSection:
    """One dated section from a testcase markdown file."""

    __test__ = False  # domain model, not a pytest test class (despite Test* name)

    datetime: str
    title: str
    intro: str = ""
    cases: tuple[TestCase, ...] = ()


@dataclass(frozen=True)
class FailureDetail:
    """Details of a single test failure from JUnit XML."""

    test_id: str
    message: str


@dataclass(frozen=True)
class RegressionResult:
    """Outcome of a pytest regression run."""

    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_s: float
    coverage_pct: float | None
    failures: tuple[FailureDetail, ...]
    available: bool

    @classmethod
    def unavailable(cls) -> RegressionResult:
        """Return a sentinel result when regression data cannot be loaded."""
        return cls(
            total=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=0,
            duration_s=0.0,
            coverage_pct=None,
            failures=(),
            available=False,
        )

    @property
    def verdict(self) -> str:
        """Return 'PASS' only when available, clean, and no failures; else 'FAIL'."""
        if not self.available:
            return "FAIL"
        if self.failed != 0 or self.errors != 0 or self.failures:
            return "FAIL"
        return "PASS"


@dataclass(frozen=True)
class SignoffMeta:
    """Metadata describing the release being signed off."""

    project: str
    branch: str
    tag: str
    sha: str
    generated_at: str


@dataclass(frozen=True)
class ParseOutcome:
    """Result of parsing one or more testcase markdown files."""

    sections: tuple[TestSection, ...]
    warnings: int


@dataclass(frozen=True)
class QaDocument:
    """Aggregate document model passed to the docx builder."""

    meta: SignoffMeta
    sections: tuple[TestSection, ...]
    regression: RegressionResult
    gates: tuple[str, ...]
