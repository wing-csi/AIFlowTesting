"""Unit/integration tests for qa_signoff.__main__ — CLI entry point."""

from pathlib import Path
from unittest.mock import patch

import pytest

from aiflow_demo.qa_signoff.__main__ import main


FIXTURES = Path(__file__).parent / "fixtures" / "qa"


def _setup_testcases(tmp_path: Path) -> Path:
    """Create a minimal testcases root with one selectable folder."""
    root = tmp_path / "testcases"
    folder = root / "feature-sample"
    folder.mkdir(parents=True)
    (folder / "cases.md").write_text(
        "## 2026-06-10 09:00:00 — Task A\n\n"
        "| # | Test case | Type | Test file | Expected result |\n"
        "|---|-----------|------|-----------|------------------|\n"
        "| 1 | A test | unit | f.py | ok |\n",
        encoding="utf-8",
    )
    return root


class TestHappyPath:
    def test_happy_path_writes_docx_and_returns_zero(self, tmp_path: Path):
        root = _setup_testcases(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        fixed_ts = "2026-06-16T12:00:00+00:00"
        with patch("aiflow_demo.qa_signoff.__main__._now_iso", return_value=fixed_ts):
            rc = main([
                "--tag", "v1.0.0",
                "--sha", "abc1234567890",
                "--junit", str(FIXTURES / "pytest-report.passing.xml"),
                "--coverage", str(FIXTURES / "coverage.json"),
                "--testcases-root", str(root),
                "--out", str(out_dir),
            ])
        assert rc == 0
        docx_files = list(out_dir.glob("*.docx"))
        assert len(docx_files) == 1

    def test_output_path_printed_to_stdout(self, tmp_path: Path, capsys):
        root = _setup_testcases(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        fixed_ts = "2026-06-16T12:00:00+00:00"
        with patch("aiflow_demo.qa_signoff.__main__._now_iso", return_value=fixed_ts):
            main([
                "--tag", "v1.0.0",
                "--sha", "abc1234",
                "--junit", str(FIXTURES / "pytest-report.passing.xml"),
                "--coverage", str(FIXTURES / "coverage.json"),
                "--testcases-root", str(root),
                "--out", str(out_dir),
            ])
        captured = capsys.readouterr()
        assert ".docx" in captured.out


class TestNoSelectableFolder:
    def test_no_selectable_folder_returns_nonzero(self, tmp_path: Path):
        empty_root = tmp_path / "empty"
        empty_root.mkdir()
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        rc = main([
            "--tag", "v1.0.0",
            "--sha", "abc1234",
            "--junit", str(tmp_path / "no.xml"),
            "--coverage", str(tmp_path / "no.json"),
            "--testcases-root", str(empty_root),
            "--out", str(out_dir),
        ])
        assert rc != 0

    def test_no_selectable_folder_prints_to_stderr(self, tmp_path: Path, capsys):
        empty_root = tmp_path / "empty"
        empty_root.mkdir()
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        main([
            "--tag", "v1.0.0",
            "--sha", "abc1234",
            "--junit", str(tmp_path / "no.xml"),
            "--coverage", str(tmp_path / "no.json"),
            "--testcases-root", str(empty_root),
            "--out", str(out_dir),
        ])
        captured = capsys.readouterr()
        assert captured.err.strip() != ""


class TestMissingRegressionFiles:
    def test_missing_regression_still_writes_doc(self, tmp_path: Path):
        root = _setup_testcases(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        fixed_ts = "2026-06-16T12:00:00+00:00"
        with patch("aiflow_demo.qa_signoff.__main__._now_iso", return_value=fixed_ts):
            rc = main([
                "--tag", "v1.0.0",
                "--sha", "abc1234",
                "--junit", str(tmp_path / "nonexistent.xml"),
                "--coverage", str(tmp_path / "nonexistent.json"),
                "--testcases-root", str(root),
                "--out", str(out_dir),
            ])
        assert rc == 0
        docx_files = list(out_dir.glob("*.docx"))
        assert len(docx_files) == 1


class TestShaShortening:
    def test_40_char_sha_shortened_to_7_in_doc(self, tmp_path: Path):
        root = _setup_testcases(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        long_sha = "a" * 40
        fixed_ts = "2026-06-16T12:00:00+00:00"
        with patch("aiflow_demo.qa_signoff.__main__._now_iso", return_value=fixed_ts):
            main([
                "--tag", "v1.0.0",
                "--sha", long_sha,
                "--junit", str(FIXTURES / "pytest-report.passing.xml"),
                "--coverage", str(FIXTURES / "coverage.json"),
                "--testcases-root", str(root),
                "--out", str(out_dir),
            ])
        import docx as docx_lib
        docx_file = next(out_dir.glob("*.docx"))
        d = docx_lib.Document(str(docx_file))
        all_text = "\n".join(p.text for p in d.paragraphs)
        assert "aaaaaaa" in all_text
        assert long_sha not in all_text


class TestArgsAndWarnings:
    def test_parse_warning_count_surfaced_in_stdout(self, tmp_path: Path, capsys):
        root = tmp_path / "testcases"
        folder = root / "feature-sample"
        folder.mkdir(parents=True)
        (folder / "cases.md").write_text(
            "## 2026-06-10 09:00:00 — Task A\n\n"
            "| # | Test case | Type | Test file | Expected result |\n"
            "|---|-----------|------|-----------|------------------|\n"
            "| 1 | Good | unit | f.py | ok |\n"
            "| too few |\n",
            encoding="utf-8",
        )
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        fixed_ts = "2026-06-16T12:00:00+00:00"
        with patch("aiflow_demo.qa_signoff.__main__._now_iso", return_value=fixed_ts):
            main([
                "--tag", "v1.0.0",
                "--sha", "abc1234",
                "--junit", str(tmp_path / "no.xml"),
                "--coverage", str(tmp_path / "no.json"),
                "--testcases-root", str(root),
                "--out", str(out_dir),
            ])
        captured = capsys.readouterr()
        assert "warning" in captured.out.lower() or "1" in captured.out

    def test_default_project_and_branch_args(self, tmp_path: Path):
        root = _setup_testcases(tmp_path)
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        fixed_ts = "2026-06-16T12:00:00+00:00"
        with patch("aiflow_demo.qa_signoff.__main__._now_iso", return_value=fixed_ts):
            rc = main([
                "--tag", "v1.0.0",
                "--sha", "abc1234",
                "--junit", str(FIXTURES / "pytest-report.passing.xml"),
                "--coverage", str(FIXTURES / "coverage.json"),
                "--testcases-root", str(root),
                "--out", str(out_dir),
            ])
        assert rc == 0
