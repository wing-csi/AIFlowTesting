"""CLI entry point: python -m aiflow_demo.qa_signoff."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .discovery import DiscoveryError, select_latest_testcase_dir
from .docx_builder import CONFIGURED_GATES, build_document
from .models import QaDocument, SignoffMeta
from .parser import parse_testcase_file
from .regression import load_regression


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string (injectable in tests)."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _short_sha(sha: str) -> str:
    """Return the first 7 characters of a commit SHA."""
    return sha[:7]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a QA sign-off document for a release."
    )
    parser.add_argument("--tag", required=True, help="Release tag (e.g. v1.0.0)")
    parser.add_argument("--sha", required=True, help="Full commit SHA")
    parser.add_argument("--junit", required=True, help="Path to JUnit XML report")
    parser.add_argument("--coverage", required=True, help="Path to coverage JSON")
    parser.add_argument(
        "--testcases-root", required=True, help="Root testcases/ directory"
    )
    parser.add_argument("--out", required=True, help="Output directory for .docx")
    parser.add_argument(
        "--project", default="AIFlowTesting", help="Project name (default: AIFlowTesting)"
    )
    parser.add_argument(
        "--branch", default=None, help="Branch name (default: selected folder name)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse args, assemble the document, and return an exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    testcases_root = Path(args.testcases_root)
    try:
        selected_dir = select_latest_testcase_dir(testcases_root)
    except DiscoveryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    branch = args.branch if args.branch else selected_dir.name

    sections_list = []
    total_warnings = 0
    for md_file in sorted(selected_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        outcome = parse_testcase_file(text)
        sections_list.extend(outcome.sections)
        total_warnings += outcome.warnings

    # Order sections chronologically so cross-file ordering is deterministic
    # regardless of filename (datetime strings sort lexicographically by time).
    sections_list.sort(key=lambda section: section.datetime)

    if total_warnings:
        print(f"Parse warnings: {total_warnings} malformed row(s) skipped.")

    regression = load_regression(Path(args.junit), Path(args.coverage))
    meta = SignoffMeta(
        project=args.project,
        branch=branch,
        tag=args.tag,
        sha=_short_sha(args.sha),
        generated_at=_now_iso(),
    )

    qa_doc = QaDocument(
        meta=meta,
        sections=tuple(sections_list),
        regression=regression,
        gates=CONFIGURED_GATES,
    )

    out_path = build_document(qa_doc, Path(args.out))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
