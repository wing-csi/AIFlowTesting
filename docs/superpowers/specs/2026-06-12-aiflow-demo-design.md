# AIFlowTesting — AI Workflow Demo Project Design

Date: 2026-06-12
Status: Approved for implementation (built autonomously; assumptions listed below)

## Purpose

A sample repository for demoing AI-assisted development with Claude Code, covering two demo cases:

1. **Demo 1 — Agent-team workflow:** a feature request is executed by the orchestrated agent flow
   (planner → user checkpoint → tdd-guide → code-reviewer → security-reviewer → local commit),
   and every created test case is logged to a per-branch, datetime-named markdown file.
2. **Demo 2 — Merge governance:** `main` cannot be updated directly; all changes go through a PR
   that requires 2 approving reviews, a passing code scan (CodeQL), a security check (Bandit +
   dependency review), and passing CI tests.

## Assumptions

- "herminsu flow" in the request is interpreted as the agent-team orchestration flow defined in
  the referenced `StitchesNewSystem/CLAUDE.md`.
- Python chosen as the demo stack: zero build step, fast tests, CodeQL support, Bandit for SAST.
- The GitHub repo (`wing-csi/AIFlowTesting`) should be **public** for the demo, or on a paid plan —
  branch rulesets are not enforced on private repos under the Free plan.
- Two collaborators with write access are needed to satisfy the 2-approval rule (the PR author
  cannot approve their own PR).

## Components

| Component | Path | Role |
|---|---|---|
| Workflow rules | `CLAUDE.md` | Agent flow, branching rules, test case log convention |
| Demo target app | `src/aiflow_demo/cart.py` | Immutable shopping cart; features get added live in demos |
| Baseline tests | `tests/test_cart.py` | Passing pytest suite proving the starting point is green |
| Test case logs | `testcases/<branch>/testcases_<datetime>.md` | Generated during Demo 1 |
| CI | `.github/workflows/ci.yml` | pytest on PRs and main |
| Code scan | `.github/workflows/codeql.yml` | CodeQL analysis (python) |
| Security check | `.github/workflows/security.yml` | Bandit SAST + dependency review on PRs |
| Ruleset | `.github/ruleset-main.json` | Importable branch ruleset for `main` |
| Setup script | `scripts/setup-branch-protection.ps1` | Creates the ruleset via GitHub REST API |
| Demo script | `DEMO.md` | Step-by-step walkthrough of both demo cases |

## Test case log convention

- Folder per branch under `testcases/`, with `/` in branch names replaced by `-`
  (`feature/discount-codes` → `testcases/feature-discount-codes/`).
- First recording on a branch creates `testcases_<yyyyMMdd_HHmmss>.md` (local time).
- Subsequent recordings on the same branch **append** a new timestamped section to the existing
  file — never create a second file for the same branch.
- Each section: timestamp + task description heading, then a table of test cases
  (name, type, test file, expected result).

## Merge governance design

GitHub branch ruleset `protect-main` targeting the default branch:

- Require a pull request before merging; **2 required approving reviews**; stale reviews dismissed
  on new pushes; review threads must be resolved.
- Required status checks: `tests` (CI), `security-scan` (Bandit), `Analyze (python)` (CodeQL),
  strict (branch must be up to date).
- Block force pushes and branch deletion.

Applied either by `scripts/setup-branch-protection.ps1` (REST API, needs a token with repo
administration write) or manually via GitHub → Settings → Rules → Rulesets → Import a ruleset.

## Error handling / edge cases

- The setup script fails fast with a clear message when `GITHUB_TOKEN` is missing.
- Required status check names only become selectable in the GitHub UI after each workflow has run
  at least once; the ruleset JSON pre-registers them by name so this is not blocking.
- Cart code validates all inputs and raises `CartError` with specific messages; all data
  structures are immutable (frozen dataclasses).

## Out of scope

- No deployment, no database, no external services — the app exists only as a demo target.
- CODEOWNERS-based review routing (can be added later if the demo needs it).
