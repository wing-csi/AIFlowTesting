# AIFlowTesting

Sample project for demoing AI-assisted development with Claude Code.

It demonstrates two things:

1. **Agent-team workflow** — feature requests are executed by an orchestrated flow
   (plan → approval checkpoint → TDD → code review → security review → local commit), with every
   created test case logged to a per-branch, datetime-named file under [testcases/](testcases/).
2. **Merge governance** — `main` cannot be updated directly. All changes go through a pull
   request requiring **2 approving reviews**, a passing **CodeQL code scan**, a **security
   check** (Bandit + dependency review), and green **CI tests**.

See [DEMO.md](DEMO.md) for the full demo walkthrough and [CLAUDE.md](CLAUDE.md) for the workflow
rules the AI follows.

## The demo app

A small, intentionally simple immutable shopping cart (`src/aiflow_demo/cart.py`) that serves as
the target for live feature requests during demos.

```powershell
pip install pytest
python -m pytest -v
```

## Repository setup (one-time)

```powershell
git push -u origin main                          # publish the baseline
$env:GITHUB_TOKEN = '<token with repo admin>'    # fine-grained: Administration read/write
.\scripts\setup-branch-protection.ps1            # apply the 'protect-main' ruleset
```

Notes:

- Branch rulesets are only **enforced on public repos** under the GitHub Free plan (private repos
  need Pro/Team).
- The 2-approval rule needs at least 2 collaborators with write access besides the PR author.
