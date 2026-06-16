"""Tests for qa_testcases models, context collection, generator, and CLI."""

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from aiflow_demo.qa_testcases import __main__ as cli
from aiflow_demo.qa_testcases.generator import (
    MODEL,
    GeneratorError,
    collect_source_context,
    generate_test_plan,
)
from aiflow_demo.qa_testcases.models import TestPlan, plan_from_dict

SAMPLE = {
    "project": "DemoApp",
    "summary": "Demo plan.",
    "assumptions": ["A1", "A2"],
    "coverage": [
        {"module": "Cart", "user_stories": 1, "total": 2,
         "positive": 1, "negative": 1, "boundary": 0, "permission": 0},
    ],
    "test_cases": [
        {"user_story": "US-1", "acceptance_criteria": "AC", "test_case": "TC",
         "test_steps": "1. do", "test_data": "x=1", "scenario_type": "Positive"},
    ],
}


class _Block:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _Message:
    def __init__(self, content):
        self.content = content


class _Messages:
    def __init__(self, content, recorder):
        self._content = content
        self._recorder = recorder

    def create(self, **kwargs):
        self._recorder.update(kwargs)
        return _Message(self._content)


class _FakeClient:
    def __init__(self, content):
        self.recorded: dict = {}
        self.messages = _Messages(content, self.recorded)


def test_plan_from_dict_builds_frozen_plan():
    plan = plan_from_dict(SAMPLE)
    assert isinstance(plan, TestPlan)
    assert plan.project == "DemoApp"
    assert plan.coverage[0].total == 2
    assert plan.test_cases[0].scenario_type == "Positive"
    with pytest.raises(FrozenInstanceError):
        plan.test_cases[0].scenario_type = "x"


def test_plan_from_dict_tolerates_missing_keys():
    plan = plan_from_dict({})
    assert plan.project == ""
    assert plan.coverage == ()
    assert plan.test_cases == ()


def test_collect_source_context_reads_py_ignores_pycache(tmp_path: Path):
    (tmp_path / "a.py").write_text("print('alpha')", encoding="utf-8")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "b.py").write_text("ignored_cache", encoding="utf-8")
    ctx = collect_source_context(tmp_path)
    assert "print('alpha')" in ctx
    assert "ignored_cache" not in ctx
    assert "a.py" in ctx


def test_generate_test_plan_uses_opus_and_parses():
    client = _FakeClient([_Block(json.dumps(SAMPLE))])
    plan = generate_test_plan("DemoApp", "source", client=client)
    assert plan.project == "DemoApp"
    assert client.recorded["model"] == MODEL == "claude-opus-4-8"
    assert "format" in client.recorded["output_config"]


def test_generate_test_plan_raises_on_bad_json():
    client = _FakeClient([_Block("not json")])
    with pytest.raises(GeneratorError):
        generate_test_plan("X", "src", client=client)


def test_generate_test_plan_raises_without_text_block():
    client = _FakeClient([])
    with pytest.raises(GeneratorError):
        generate_test_plan("X", "src", client=client)


def test_main_writes_docx(tmp_path: Path, monkeypatch):
    src = tmp_path / "src"
    src.mkdir()
    (src / "m.py").write_text("x = 1", encoding="utf-8")
    out = tmp_path / "qa"
    monkeypatch.setattr(cli, "generate_test_plan", lambda *a, **k: plan_from_dict(SAMPLE))
    rc = cli.main(
        ["--project", "DemoApp", "--branch", "v1.0.0",
         "--src-root", str(src), "--out", str(out)]
    )
    assert rc == 0
    assert list(out.glob("*.docx"))


def test_main_missing_src_root_returns_nonzero(tmp_path: Path, capsys):
    rc = cli.main(["--src-root", str(tmp_path / "nope"), "--out", str(tmp_path)])
    assert rc == 1
    assert "source root not found" in capsys.readouterr().err
