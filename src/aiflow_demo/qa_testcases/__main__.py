"""CLI: python -m aiflow_demo.qa_testcases — generate a QA test-case .docx."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .generator import GeneratorError, collect_source_context, generate_test_plan
from .render import RenderMeta, render_document


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a QA test-case document.")
    parser.add_argument("--project", default="AIFlowTesting", help="Project name")
    parser.add_argument("--branch", default="", help="Branch or tag under test")
    parser.add_argument("--src-root", default="src", help="Source root to read")
    parser.add_argument("--out", default="qa", help="Output directory for the .docx")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Read source, generate the plan via Claude, render the .docx; return exit code."""
    args = _build_parser().parse_args(argv)
    src_root = Path(args.src_root)
    if not src_root.is_dir():
        print(f"ERROR: source root not found: {src_root}", file=sys.stderr)
        return 1

    context = collect_source_context(src_root)
    now = datetime.now(timezone.utc)
    try:
        plan = generate_test_plan(args.project, context)
    except GeneratorError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # API / credential / network failure — fail cleanly
        print(f"ERROR: test-case generation failed: {exc}", file=sys.stderr)
        return 1

    meta = RenderMeta(
        branch=args.branch or args.project,
        generated_at=now.strftime("%Y-%m-%d %H:%M UTC"),
        date_stamp=now.strftime("%Y%m%d"),
    )
    out_path = render_document(plan, meta, Path(args.out))
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
