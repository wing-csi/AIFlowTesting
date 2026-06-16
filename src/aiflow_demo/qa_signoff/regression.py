"""Load pytest regression results from JUnit XML and coverage JSON."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import FailureDetail, RegressionResult

_PASSED_ATTR = "tests"
_FAILED_ATTR = "failures"
_ERROR_ATTR = "errors"
_SKIPPED_ATTR = "skipped"
_TIME_ATTR = "time"


def _collect_failures(root: ET.Element) -> tuple[FailureDetail, ...]:
    """Gather FailureDetail from all <failure> and <error> child elements."""
    details: list[FailureDetail] = []
    for tc in root.iter("testcase"):
        classname = tc.get("classname", "")
        name = tc.get("name", "")
        test_id = f"{classname}.{name}"
        for tag in ("failure", "error"):
            node = tc.find(tag)
            if node is not None:
                message = node.get("message", "")
                details.append(FailureDetail(test_id=test_id, message=message))
    return tuple(details)


def _suite_int(suite: ET.Element, attr: str) -> int:
    try:
        return int(suite.get(attr, "0"))
    except ValueError:
        return 0


def _suite_float(suite: ET.Element, attr: str) -> float:
    try:
        return float(suite.get(attr, "0"))
    except ValueError:
        return 0.0


def _parse_junit(
    path: Path,
) -> tuple[int, int, int, int, float, ET.Element] | None:
    """Return (total, failed, errors, skipped, duration, root) or None on error.

    The XML is parsed exactly once and the parsed root is returned so the caller
    can collect failures without a second ET.parse (which, if it raised, would
    escape the unavailable() contract). The JUnit file is pytest output from the
    same CI run — a trusted boundary, so stdlib ElementTree is acceptable here.
    """
    try:
        tree = ET.parse(str(path))
    except (OSError, ET.ParseError):
        return None

    root = tree.getroot()
    suites: list[ET.Element] = []
    if root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    elif root.tag == "testsuite":
        suites = [root]
    else:
        suites = list(root.iter("testsuite"))

    total = sum(_suite_int(s, _PASSED_ATTR) for s in suites)
    failed = sum(_suite_int(s, _FAILED_ATTR) for s in suites)
    errors = sum(_suite_int(s, _ERROR_ATTR) for s in suites)
    skipped = sum(_suite_int(s, _SKIPPED_ATTR) for s in suites)
    duration = sum(_suite_float(s, _TIME_ATTR) for s in suites)
    return total, failed, errors, skipped, duration, root


def _parse_coverage(path: Path) -> float | None:
    """Return coverage percent (1 dp) or None when unavailable/malformed."""
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        raw_pct = data["totals"]["percent_covered"]
        return round(float(raw_pct), 1)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def load_regression(junit_path: Path, coverage_path: Path) -> RegressionResult:
    """Load regression data from JUnit XML + coverage JSON into a RegressionResult."""
    junit = _parse_junit(junit_path)
    if junit is None:
        return RegressionResult.unavailable()

    total, failed, errors, skipped, duration, root = junit
    passed = max(total - failed - errors - skipped, 0)

    coverage_pct = _parse_coverage(coverage_path)
    failures = _collect_failures(root)

    return RegressionResult(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        errors=errors,
        duration_s=round(duration, 6),
        coverage_pct=coverage_pct,
        failures=failures,
        available=True,
    )
