"""Unit tests for qa_signoff.discovery — select_latest_testcase_dir."""

import pytest
from pathlib import Path

from aiflow_demo.qa_signoff.discovery import DiscoveryError, select_latest_testcase_dir


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestSelectLatestTestcaseDir:
    def test_globally_newest_folder_wins(self, tmp_path: Path):
        old_dir = tmp_path / "feature-old"
        new_dir = tmp_path / "feature-new"
        _write(
            old_dir / "cases.md",
            "## 2026-06-10 09:00:00 — Task A\n\nsome text",
        )
        _write(
            new_dir / "cases.md",
            "## 2026-06-11 10:30:00 — Task B\n\nsome text",
        )
        result = select_latest_testcase_dir(tmp_path)
        assert result == new_dir

    def test_max_across_multiple_files_in_folder(self, tmp_path: Path):
        dir_a = tmp_path / "folder-a"
        dir_b = tmp_path / "folder-b"
        _write(dir_a / "file1.md", "## 2026-06-12 08:00:00 — Task X\n")
        _write(dir_a / "file2.md", "## 2026-06-13 09:00:00 — Task Y\n")
        _write(dir_b / "only.md", "## 2026-06-12 10:00:00 — Task Z\n")
        result = select_latest_testcase_dir(tmp_path)
        assert result == dir_a

    def test_ignores_readme_at_root(self, tmp_path: Path):
        (tmp_path / "README.md").write_text("# readme", encoding="utf-8")
        folder = tmp_path / "feature-x"
        _write(folder / "cases.md", "## 2026-06-10 09:00:00 — Task A\n")
        result = select_latest_testcase_dir(tmp_path)
        assert result == folder

    def test_ignores_non_md_files(self, tmp_path: Path):
        folder = tmp_path / "feature-y"
        folder.mkdir()
        (folder / "notes.txt").write_text(
            "## 2026-06-10 09:00:00 — Not parsed", encoding="utf-8"
        )
        _write(folder / "cases.md", "## 2026-06-10 09:00:00 — Task A\n")
        result = select_latest_testcase_dir(tmp_path)
        assert result == folder

    def test_ignores_headerless_md_in_scoring(self, tmp_path: Path):
        folder_good = tmp_path / "good"
        folder_headerless = tmp_path / "headerless"
        _write(folder_good / "cases.md", "## 2026-06-10 09:00:00 — Task A\n")
        _write(folder_headerless / "empty.md", "# Just a title\nNo section headers here.")
        result = select_latest_testcase_dir(tmp_path)
        assert result == folder_good

    def test_tiebreak_name_descending(self, tmp_path: Path):
        folder_a = tmp_path / "zzz"
        folder_b = tmp_path / "aaa"
        same_ts = "## 2026-06-10 09:00:00 — Same time\n"
        _write(folder_a / "cases.md", same_ts)
        _write(folder_b / "cases.md", same_ts)
        result = select_latest_testcase_dir(tmp_path)
        assert result == folder_a

    def test_empty_root_raises_discovery_error(self, tmp_path: Path):
        with pytest.raises(DiscoveryError, match="No selectable"):
            select_latest_testcase_dir(tmp_path)

    def test_no_parseable_headers_raises_discovery_error(self, tmp_path: Path):
        folder = tmp_path / "feature-z"
        _write(folder / "empty.md", "# Title only\nNo section headers.")
        with pytest.raises(DiscoveryError, match="No selectable"):
            select_latest_testcase_dir(tmp_path)

    def test_malformed_header_ignored_not_crash(self, tmp_path: Path):
        folder_a = tmp_path / "feature-a"
        folder_b = tmp_path / "feature-b"
        _write(
            folder_a / "cases.md",
            "## not-a-date — bad header\n## 2026-06-10 09:00:00 — Valid\n",
        )
        _write(folder_b / "cases.md", "## 2026-06-09 08:00:00 — Older\n")
        result = select_latest_testcase_dir(tmp_path)
        assert result == folder_a
