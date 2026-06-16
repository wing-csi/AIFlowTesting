"""Parse testcase markdown files into structured models."""

from __future__ import annotations

import re
from typing import NamedTuple

from .models import ParseOutcome, TestCase, TestSection

SECTION_HEADER_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+—\s+(.+)$"
)

_EXPECTED_CELL_COUNT = 5


class _RawSection(NamedTuple):
    datetime_str: str
    title: str
    body: str


def _split_sections(text: str) -> list[_RawSection]:
    """Split markdown text into raw sections starting at ## datetime — title."""
    sections: list[_RawSection] = []
    current_dt: str | None = None
    current_title: str | None = None
    body_lines: list[str] = []

    for line in text.splitlines():
        match = SECTION_HEADER_RE.match(line)
        if match:
            if current_dt is not None and current_title is not None:
                sections.append(
                    _RawSection(current_dt, current_title, "\n".join(body_lines))
                )
            current_dt = match.group(1)
            current_title = match.group(2).strip()
            body_lines = []
        elif current_dt is not None:
            body_lines.append(line)

    if current_dt is not None and current_title is not None:
        sections.append(_RawSection(current_dt, current_title, "\n".join(body_lines)))

    return sections


def _is_separator_row(cells: list[str]) -> bool:
    """Return True when every cell is a Markdown separator like ---."""
    return all(re.match(r"^-+$", cell) for cell in cells if cell)


def _parse_table(body: str) -> tuple[tuple[TestCase, ...], int]:
    """Extract test cases from a markdown table body; return (cases, warnings)."""
    cases: list[TestCase] = []
    warnings = 0
    in_table = False
    header_seen = False

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break
            continue

        in_table = True
        raw_cells = stripped.strip("|").split("|")
        cells = [c.strip() for c in raw_cells]

        if not header_seen:
            header_seen = True
            continue

        if _is_separator_row(cells):
            continue

        if len(cells) != _EXPECTED_CELL_COUNT:
            warnings += 1
            continue

        try:
            number = int(cells[0])
        except ValueError:
            number = 0

        cases.append(
            TestCase(
                number=number,
                description=cells[1],
                type=cells[2],
                test_file=cells[3],
                expected=cells[4],
            )
        )

    return tuple(cases), warnings


def _extract_intro(body: str) -> str:
    """Return lines before the first table as a single stripped string."""
    intro_lines: list[str] = []
    for line in body.splitlines():
        if line.strip().startswith("|"):
            break
        intro_lines.append(line)
    return "\n".join(intro_lines).strip()


def parse_testcase_file(text: str) -> ParseOutcome:
    """Parse a testcase markdown file and return a ParseOutcome."""
    raw_sections = _split_sections(text)
    sections: list[TestSection] = []
    total_warnings = 0

    for raw in raw_sections:
        intro = _extract_intro(raw.body)
        cases, warnings = _parse_table(raw.body)
        total_warnings += warnings
        sections.append(
            TestSection(
                datetime=raw.datetime_str,
                title=raw.title,
                intro=intro,
                cases=cases,
            )
        )

    return ParseOutcome(sections=tuple(sections), warnings=total_warnings)
