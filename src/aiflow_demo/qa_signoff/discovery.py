"""Discover the most-recently-updated testcases folder."""

from __future__ import annotations

import contextlib
import re
from datetime import datetime
from pathlib import Path
from typing import Iterator

SECTION_HEADER_RE = re.compile(
    r"^##\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+—"
)

_DATE_FMT = "%Y-%m-%d %H:%M:%S"


class DiscoveryError(RuntimeError):
    """Raised when no selectable testcases folder can be found."""


def _iter_section_datetimes(text: str) -> Iterator[datetime]:
    """Yield parsed datetimes from section headers; skip malformed ones."""
    for line in text.splitlines():
        match = SECTION_HEADER_RE.match(line)
        if match:
            with contextlib.suppress(ValueError):
                yield datetime.strptime(match.group(1), _DATE_FMT)


def _folder_max_datetime(folder: Path) -> datetime | None:
    """Return the maximum section datetime across all *.md files, or None."""
    best: datetime | None = None
    for md_file in folder.glob("*.md"):
        text = md_file.read_text(encoding="utf-8", errors="replace")
        for dt in _iter_section_datetimes(text):
            if best is None or dt > best:
                best = dt
    return best


def select_latest_testcase_dir(root: Path) -> Path:
    """Return the immediate subdirectory of *root* with the newest section header.

    Tie-break by folder name descending (alphabetically last wins).
    Raises DiscoveryError when no qualifying folder is found.
    """
    candidates: list[tuple[datetime, str, Path]] = []
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        best = _folder_max_datetime(entry)
        if best is not None:
            candidates.append((best, entry.name, entry))

    if not candidates:
        raise DiscoveryError(
            f"No selectable testcases folder found under {root}. "
            "Ensure at least one subdirectory contains a *.md file "
            "with a '## YYYY-MM-DD HH:MM:SS — …' section header."
        )

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]
