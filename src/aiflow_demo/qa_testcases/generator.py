"""Generate a QA test-case plan from source code via the Claude API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import TestPlan, plan_from_dict

MODEL = "claude-opus-4-8"
_MAX_TOKENS = 16000
_MAX_FILE_BYTES = 100_000

SYSTEM_PROMPT = (
    "You are a senior QA engineer writing a manual test plan for QA engineers. "
    "From the provided source code, infer the user stories and acceptance criteria, "
    "then design test cases covering FOUR scenario types per story: Positive (happy "
    "path), Negative (invalid input / error handling), Boundary (edge values: empty, "
    "zero, min, max, limits), and Permission (access control, immutability, "
    "unauthorised actions). Write concrete, numbered test steps a human can follow, "
    "and realistic synthetic test data. Leave test results for the QA engineer to "
    "fill in. Group cases by module and order them positive, negative, boundary, "
    "permission. The coverage-table counts MUST match the test cases you produce. "
    "Return the plan via the required structured format."
)

_COVERAGE_ITEM = {
    "type": "object",
    "properties": {
        "module": {"type": "string"},
        "user_stories": {"type": "integer"},
        "total": {"type": "integer"},
        "positive": {"type": "integer"},
        "negative": {"type": "integer"},
        "boundary": {"type": "integer"},
        "permission": {"type": "integer"},
    },
    "required": [
        "module", "user_stories", "total",
        "positive", "negative", "boundary", "permission",
    ],
    "additionalProperties": False,
}

_CASE_ITEM = {
    "type": "object",
    "properties": {
        "user_story": {"type": "string"},
        "acceptance_criteria": {"type": "string"},
        "test_case": {"type": "string"},
        "test_steps": {"type": "string"},
        "test_data": {"type": "string"},
        "scenario_type": {
            "type": "string",
            "enum": ["Positive", "Negative", "Boundary", "Permission"],
        },
    },
    "required": [
        "user_story", "acceptance_criteria", "test_case",
        "test_steps", "test_data", "scenario_type",
    ],
    "additionalProperties": False,
}

TEST_PLAN_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "project": {"type": "string"},
        "summary": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "coverage": {"type": "array", "items": _COVERAGE_ITEM},
        "test_cases": {"type": "array", "items": _CASE_ITEM},
    },
    "required": ["project", "summary", "assumptions", "coverage", "test_cases"],
    "additionalProperties": False,
}


class GeneratorError(RuntimeError):
    """Raised when the model response cannot be turned into a TestPlan."""


def collect_source_context(src_root: Path) -> str:
    """Concatenate Python source under src_root into a labeled context blob."""
    parts: list[str] = []
    for path in sorted(src_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")[:_MAX_FILE_BYTES]
        parts.append(f"# ===== {path.relative_to(src_root)} =====\n{text}")
    return "\n\n".join(parts)


def _user_prompt(project: str, source_context: str) -> str:
    return (
        f"Project: {project}\n\n"
        "Generate a comprehensive manual QA test plan for the application below. "
        "Cover every module and all four scenario types per user story.\n\n"
        f"=== SOURCE CODE ===\n{source_context}"
    )


def _default_client() -> Any:
    import anthropic  # lazy: only needed for a real generation run

    return anthropic.Anthropic()


def _extract_json(message: Any) -> dict:
    for block in message.content:
        if getattr(block, "type", None) == "text":
            try:
                return json.loads(block.text)
            except json.JSONDecodeError as exc:
                raise GeneratorError(f"invalid JSON in model response: {exc}") from exc
    raise GeneratorError("model returned no text block with the test plan")


def generate_test_plan(
    project: str, source_context: str, client: Any = None
) -> TestPlan:
    """Call Claude to produce a structured TestPlan from source context."""
    active = client if client is not None else _default_client()
    response = active.messages.create(
        model=MODEL,
        max_tokens=_MAX_TOKENS,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        output_config={"format": {"type": "json_schema", "schema": TEST_PLAN_SCHEMA}},
        messages=[{"role": "user", "content": _user_prompt(project, source_context)}],
    )
    return plan_from_dict(_extract_json(response))
