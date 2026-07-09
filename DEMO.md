# Demo walkthrough

Two demo cases, run in order. Demo 1 is fully local; Demo 2 needs the repo published to GitHub
with the ruleset applied.

---

## One-time setup

1. Push the baseline to GitHub (workflows must run once so the status checks register):

   ```powershell
   git push -u origin main
   ```

2. Make sure the repo is **public** (or on GitHub Pro/Team — rulesets are not enforced on
   private repos under the Free plan), and add **at least 2 collaborators** with write access
   (Settings → Collaborators) so the 2-approval rule can be satisfied.

3. Apply the branch ruleset (token needs repository **Administration: write**):

   ```powershell
   $env:GITHUB_TOKEN = '<token>'
   .\scripts\setup-branch-protection.ps1
   ```

   Alternative without a token: GitHub → Settings → Rules → Rulesets → New ruleset →
   Import a ruleset → upload `.github/ruleset-main.json`.

---

## Demo 1 — Agent-team workflow with test case logging

**Goal:** show Claude Code executing a whole feature through the orchestrated flow defined in
[AGENTS.md](AGENTS.md): plan → approval checkpoint → TDD → code review → security review →
local commit, with test cases logged per branch.

1. Start Claude Code in this repo and give it a feature request, for example:

   > Add support for percentage discount codes to the cart. Valid codes: WELCOME10 = 10% off,
   > VIP20 = 20% off. Any other code must be rejected with a clear error.

2. **Watch for** (talking points):
   - Claude creates a feature branch (e.g. `feature/discount-codes`) — never works on `main`.
   - `ecc:planner` produces a plan, then Claude **stops and waits for approval**.
   - Say "approved" — the rest runs end-to-end with no further prompts.
   - `ecc:tdd-guide` writes failing tests first, then the implementation.
   - A test case log appears at `testcases/feature-discount-codes/testcases_<datetime>.md`.
   - `ecc:code-reviewer` + `ecc:security-reviewer` run (discount codes are user input, so the
     security reviewer is triggered).
   - A local commit is created; Claude does **not** push or open a PR.

3. **Show the append behavior** — on the same branch, give a follow-up request:

   > Also cap the total discount at $50.

   The new test cases are **appended** as a new timestamped section to the SAME file —
   no second file is created.

4. Verify locally: `python -m pytest -v` — everything green.

---

## Demo 2 — Merge governance (protected main)

**Goal:** show that `main` cannot be updated directly and a PR needs 2 approvals + code scan +
security check + CI before merging.

1. **Direct push is rejected** — from `main`, make a trivial change and try to push:

   ```powershell
   git checkout main
   "demo" | Out-File -Append demo.txt; git add demo.txt
   git commit -m "chore: try direct push to main"
   git push
   ```

   GitHub rejects the push: *"Changes must be made through a pull request"*. Clean up with:

   ```powershell
   git reset --hard origin/main
   ```

2. **Open a PR from the Demo 1 branch:**

   ```powershell
   git checkout feature/discount-codes
   git push -u origin feature/discount-codes
   ```

   Then open the PR on GitHub (the link is printed by the push, or use the web UI).

3. **Show the merge gate on the PR page:**
   - Merge button is blocked: *"Review required — 2 approving reviews"*.
   - Required checks running/queued: `tests` (CI), `security-scan` (Bandit + dependency
     review), `Analyze (python)` (CodeQL).
   - Have reviewer 1 approve → still blocked (1 of 2).
   - Have reviewer 2 approve + checks green → merge unlocks.

4. Optional extra: push a commit containing an obvious Bandit finding (e.g.
   `password = "hunter2"` plus `eval(user_input)`) to show `security-scan` failing and
   blocking the merge even with 2 approvals.

---

## Troubleshooting

- **Status checks not listed as required:** check names must match the workflow **job names**
  exactly: `tests`, `security-scan`, `Analyze (python)`. They appear after the first run.
- **Ruleset not enforced:** repo is private on a Free plan — make it public.
- **Can't get 2 approvals:** approvals must come from collaborators with write access who are
  not the PR author.
- **CodeQL fails with "code scanning is not enabled":** Settings → Security → Code security →
  enable Code scanning.
