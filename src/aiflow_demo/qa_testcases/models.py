"""Frozen dataclasses and dict mapping for the QA test-case plan."""

from __future__ import annotations

from dataclasses import dataclass

SCENARIO_TYPES = ("Positive", "Negative", "Boundary", "Permission")


@dataclass(frozen=True)
class TestCaseRow:
    """One row of the manual test-case table."""

    __test__ = False  # domain model, not a pytest test class (despite Test* name)

    user_story: str
    acceptance_criteria: str
    test_case: str
    test_steps: str
    test_data: str
    scenario_type: str


@dataclass(frozen=True)
class ModuleCoverage:
    """One row of the coverage-summary table."""

    module: str
    user_stories: int
    total: int
    positive: int
    negative: int
    boundary: int
    permission: int


@dataclass(frozen=True)
class TestPlan:
    """A full QA test-case plan ready to render."""

    __test__ = False  # domain model, not a pytest test class (despite Test* name)

    project: str
    summary: str
    assumptions: tuple[str, ...]
    coverage: tuple[ModuleCoverage, ...]
    test_cases: tuple[TestCaseRow, ...]


def _coverage_from_dict(item: dict) -> ModuleCoverage:
    return ModuleCoverage(
        module=str(item.get("module", "")),
        user_stories=int(item.get("user_stories", 0)),
        total=int(item.get("total", 0)),
        positive=int(item.get("positive", 0)),
        negative=int(item.get("negative", 0)),
        boundary=int(item.get("boundary", 0)),
        permission=int(item.get("permission", 0)),
    )


def _row_from_dict(item: dict) -> TestCaseRow:
    return TestCaseRow(
        user_story=str(item.get("user_story", "")),
        acceptance_criteria=str(item.get("acceptance_criteria", "")),
        test_case=str(item.get("test_case", "")),
        test_steps=str(item.get("test_steps", "")),
        test_data=str(item.get("test_data", "")),
        scenario_type=str(item.get("scenario_type", "")),
    )


def plan_from_dict(data: dict) -> TestPlan:
    """Build a TestPlan from the model's structured-output dict (defensive)."""
    return TestPlan(
        project=str(data.get("project", "")),
        summary=str(data.get("summary", "")),
        assumptions=tuple(str(a) for a in data.get("assumptions", ())),
        coverage=tuple(_coverage_from_dict(c) for c in data.get("coverage", ())),
        test_cases=tuple(_row_from_dict(r) for r in data.get("test_cases", ())),
    )
