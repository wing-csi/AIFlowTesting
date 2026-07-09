# AIFlowTesting

Demo repository for AI agent-team development workflows and GitHub merge governance.

## Branching rules (CRITICAL)

- NEVER commit directly to `main`. Before making any code change, create or switch to a feature
  branch: `feature/<short-name>` or `fix/<short-name>`.
- `main` is protected on GitHub: changes only land via a pull request with 2 approving reviews,
  passing CI tests, CodeQL code scan, and security checks.
- Do not push and do not open PRs unless explicitly asked — those are manual steps.

## Agent team workflow

For non-trivial work (multi-file changes, new features, refactors, bugs with unclear root cause),
the main session acts as orchestrator and dispatches subagents instead of doing the work inline:

1. **Plan** — dispatch `ecc:planner`, return plan to user.
2. **Checkpoint** — wait for user approval (one word is fine). Do not proceed without it.
3. **Execute end-to-end on approval, no further prompts:**
   - `ecc:tdd-guide` writes tests first, then implementation.
   - **Record test cases** in the test case log (see below) immediately after tests are written.
   - `ecc:code-reviewer` reviews the diff; fix CRITICAL/HIGH and re-review once.
   - `ecc:security-reviewer` if auth, user input, API endpoints, or secrets are touched.
     Run in parallel with code-reviewer when independent.
   - Create a local commit on the current branch **with the `AI-Level` trailer (see Commit
     rules below)**. **Do not push, do not open a PR** — those are manual.

Skip the orchestration for trivial edits, typos, questions, and exploration.

## Commit rules (CRITICAL)

Every commit message MUST end with an `AI-Level: Lx` git trailer recording how
autonomously the task was completed. Self-assess from what actually happened in THIS
session — not from the size or quality of the diff:

| Level | When to use |
|---|---|
| L2 | User drove the task: you produced code per individual prompt; user reviewed and assembled piece by piece |
| L3 | You completed the whole task, but a human gate occurred — the plan checkpoint counts, as do mid-task corrections or redirections |
| L4 | You ran end-to-end including tests, with no plan checkpoint and zero mid-task intervention; user only reviews the final diff |

(L5 = fully autonomous incl. auto-merge — not reachable while `main` requires manual PRs.)

Format — the trailer is the last line of the message, separated by a blank line:

```
feat: add discount codes

optional body

AI-Level: L3
```

- Under the agent team workflow above, the plan checkpoint makes those tasks L3 by
  definition. Only tasks executed without any approval gate may claim L4.
- One task = one level. If commits on a branch would disagree, put the definitive
  `AI-Level: Lx` line in the PR description — it takes precedence in the telemetry.
- Never omit the trailer: untagged commits appear as unclassified gaps in the
  ManagementDashboard coverage metric.

## Test case log (CRITICAL)

Every test case created or modified during a task MUST be documented under `testcases/`:

- **Folder per branch:** `testcases/<branch-name>/`, replacing `/` in the branch name with `-`.
  Example: branch `feature/discount-codes` → folder `testcases/feature-discount-codes/`.
- **Filename carries a datetime:** the FIRST time test cases are recorded on a branch, create
  `testcases_<yyyyMMdd_HHmmss>.md` inside the branch folder. Get the timestamp with:
  `Get-Date -Format "yyyyMMdd_HHmmss"` (PowerShell).
- **Append within the same branch:** if the branch folder already contains a testcase file,
  do NOT create a new file — append a new section to the existing file.

Each recording appends one section in this format:

```markdown
## <yyyy-MM-dd HH:mm:ss> — <short task description>

| # | Test case | Type | Test file | Expected result |
|---|-----------|------|-----------|-----------------|
| 1 | Discount code WELCOME10 applies 10% off | unit | tests/test_cart.py | total reduced by 10% |
```

- Include every new or changed test: unit, integration, and edge cases.
- Commit the testcase file together with the code changes it describes.

## Project layout

- `src/aiflow_demo/` — application code (immutable patterns: frozen dataclasses, methods return
  new objects, never mutate).
- `tests/` — pytest suite. Run with `python -m pytest -v`. Keep coverage at 80%+.
- `testcases/` — per-branch test case logs (convention above).
- `.github/workflows/` — CI (`tests`), CodeQL (`Analyze (python)`), security (`security-scan`).
