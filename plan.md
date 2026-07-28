# Remediation plan — detected issues

Working tracker for issues detected in this repository, with owners and target dates.
Findings below were verified against the files on `main` as of the review date.

- **Review date:** 2026-07-28
- **Branch reviewed:** `main` (@ `3349fa6`)
- **Scope:** `src/`, `tests/`, `.github/workflows/`, `testcases/`, top-level docs

## Status legend

| Status | Meaning |
|--------|---------|
| 🔴 Overdue | Target date has passed; needs action now |
| 🟠 Nearly due | Target date within 7 days (by 2026-08-04) |
| 🟢 On schedule | Target date beyond 7 days; not yet at risk |

## Issue board

This checklist is the single source of truth for status — tick a box when the fix lands.
The inline markers are machine-read by the metrics dashboard, so keep the format:
`#bug` marks the item a defect, `!P1`/`!P2`/`!P3` = High/Medium/Low severity, and
`due:YYYY-MM-DD` is the target date. The detail section for each ID follows below.

- [ ] P-01 · testcases · Test-case logs on `main` document code that does not exist on `main` #bug !P1 due:2026-07-10
- [ ] P-02 · CI · `lint` required check passes vacuously — its only intended finding is gone #bug !P1 due:2026-07-17
- [ ] P-03 · docs · README/DEMO list 3 required checks; the ruleset requires 5 #bug !P2 due:2026-07-22
- [ ] P-04 · CI · `ruff check src` never lints `tests/` (9 test files unlinted) #bug !P2 due:2026-07-24
- [ ] P-05 · docs · DEMO.md step 3 promises a "$50 discount cap" that `cart.py` does not implement #bug !P2 due:2026-07-30
- [ ] P-06 · qa_signoff · `_fill_table_row` uses `zip(strict=False)` — silently truncates sign-off tables #bug !P2 due:2026-07-31
- [ ] P-07 · qa_signoff · `select_latest_testcase_dir` raises raw `FileNotFoundError` instead of `DiscoveryError` #bug !P2 due:2026-08-03
- [ ] P-08 · CI · CI installs unpinned deps instead of the declared `pyproject.toml` extra #bug !P2 due:2026-08-14
- [ ] P-09 · src · Money handled as binary `float` throughout `cart.py` #bug !P2 due:2026-08-21
- [ ] P-10 · CI · `qa-signoff` job can reach the generator step with no JUnit report #bug !P3 due:2026-09-04
- [ ] P-11 · supply chain · GitHub Actions pinned to floating major tags; no Dependabot #bug !P3 due:2026-09-18

All 11 are owned by *unassigned* — assign by editing the Owner line in the detail section.

---

## 🔴 Overdue

### P-01 — Test-case logs document code that is not on `main`

- **Severity:** High · **Target:** 2026-07-10 · **Owner:** unassigned

**Detected.** `testcases/feature-multiple-discounts/testcases_20260615_192753.md` and
`testcases/feature-export-receipt/testcases_20260615_202026.md` record test cases against
`src/aiflow_demo/orders.py` and `tests/test_orders.py`, and against `Cart.apply_discounts()`,
`Cart.add_discount()`, and the `discount_codes` field. None of these exist on `main`:
`src/aiflow_demo/` contains only `cart.py`, `qa_testcases/`, and `qa_signoff/`, and
[cart.py](src/aiflow_demo/cart.py) exposes a single `discount_code` with no stacking.
The logs also assert "61 passed" / "52/52 tests passing", which cannot hold on `main`.

**Why it matters.** The test-case log is the input to the QA sign-off document
([qa-signoff.yml](.github/workflows/qa-signoff.yml)). A release doc generated today would
attest to test cases for code that was never merged — the governance artifact would be wrong
in the one direction that matters.

**Fix.** Decide per feature: either merge the missing work, or move the two folders to an
`testcases/archive/` path excluded from discovery, or annotate each stale section with a
`> **Not on main**` banner. Then re-run `python -m aiflow_demo.qa_signoff` and confirm the
catalog matches the tree.

---

### P-02 — `lint` required check passes vacuously

- **Severity:** High · **Target:** 2026-07-17 · **Owner:** unassigned

**Detected.** `.github/ruleset-main.json:32` makes `lint` a required status check, and
[lint.yml:20](.github/workflows/lint.yml:20) runs `ruff check src`. The recorded intent
(`testcases/feature-multiple-discounts/…:76-77`) is that this gate fails with
`PLR0913 (10 > 7)` at `orders.py:54`. `orders.py` is absent from `main` (see P-01), so
`ruff check src` now exits 0 with nothing to find.

**Why it matters.** A required gate that is green because its subject vanished is
indistinguishable from a working gate. The demo's central claim — that `lint` catches
maintainability smells CodeQL and Bandit miss — is currently unproven on `main`.

**Fix.** Restore a deliberate smell fixture under `src/` (or ship `orders.py`), and add a
CI assertion that ruff's rule set is actually exercised rather than trivially satisfied.

---

### P-03 — Docs list 3 required checks; the ruleset requires 5

- **Severity:** Medium · **Target:** 2026-07-22 · **Owner:** unassigned

**Detected.** [README.md:11-12](README.md:11) and [DEMO.md:95-97](DEMO.md:95) name
`tests`, `security-scan`, and `Analyze (python)`. `.github/ruleset-main.json:28-34` requires
five: those three plus `lint` and `coverage`. The DEMO troubleshooting note
([DEMO.md:108-109](DEMO.md:108)) repeats the stale three-name list as the thing to match.

**Why it matters.** During a live demo the PR page shows five checks while the script names
three — and the troubleshooting advice sends the presenter looking for the wrong job names.

**Fix.** Update both files to the five-check list and add `coverage`/`lint` to the Demo 2
talking points.

---

### P-04 — `tests/` is never linted

- **Severity:** Medium · **Target:** 2026-07-24 · **Owner:** unassigned

**Detected.** [lint.yml:20](.github/workflows/lint.yml:20) runs `ruff check src`. The rule set
in [pyproject.toml:23-43](pyproject.toml:23) selects reliability rules (`F`, `B`, `PLE`, `PLW`)
that apply just as much to test code, but the nine files under `tests/` are outside the path.

**Why it matters.** Unused imports, mutable default arguments, and shadowed names in tests go
undetected, and the repo's stated 80%-coverage posture rests on code that no gate inspects.

**Fix.** Change to `ruff check src tests`, or set `[tool.ruff] src = ["src", "tests"]` and lint
the repo root. Expect a first-run backlog; fix or scope-suppress per rule.

---

## 🟠 Nearly due

### P-05 — DEMO.md promises a discount cap that does not exist

- **Severity:** Medium · **Target:** 2026-07-30 · **Owner:** unassigned

**Detected.** [DEMO.md:55](DEMO.md:55) scripts the follow-up request *"Also cap the total
discount at $50"* as the way to show append-behavior in the test-case log.
[cart.py:77-80](src/aiflow_demo/cart.py:77) applies `1 - discount_rate` with no cap of any kind.

**Why it matters.** Low blast radius — it is a demo script, not production logic — but a
presenter following DEMO.md verbatim will narrate behavior the code does not have.

**Fix.** Either implement the cap in `cart.py` (with tests logged per the `testcases/`
convention), or reword the DEMO step to a follow-up the current code supports.

---

### P-06 — Sign-off tables truncate silently on a column mismatch

- **Severity:** Medium · **Target:** 2026-07-31 · **Owner:** unassigned

**Detected.** [docx_builder.py:45](src/aiflow_demo/qa_signoff/docx_builder.py:45):
`for cell, value in zip(row.cells, values, strict=False)`. If `values` is longer than the row,
the surplus is dropped without error. `CATALOG_COLUMNS` has five entries and each catalog row
supplies five values, so today it balances — but nothing enforces that, and the neighbouring
`_add_signoff_block` correctly uses `strict=True`.

**Why it matters.** The failure mode is a QA sign-off document that renders cleanly while
missing a column of evidence. Silent truncation in a governance artifact is worse than a crash.

**Fix.** Switch to `strict=True` and let a mismatch fail the generator, matching
[docx_builder.py:164](src/aiflow_demo/qa_signoff/docx_builder.py:164). Add a unit test
covering a row/column mismatch.

---

### P-07 — Missing testcases root raises a raw OS error

- **Severity:** Medium · **Target:** 2026-08-03 · **Owner:** unassigned

**Detected.** [discovery.py:49](src/aiflow_demo/qa_signoff/discovery.py:49) calls
`root.iterdir()` before any existence check. `DiscoveryError` — with its helpful message about
`## YYYY-MM-DD HH:MM:SS — …` headers ([discovery.py:57-61](src/aiflow_demo/qa_signoff/discovery.py:57))
— is only raised when the directory exists but yields no candidates. A missing or non-directory
`--testcases-root` escapes as `FileNotFoundError` / `NotADirectoryError`.

**Why it matters.** This runs at release time on a `v*` tag push
([qa-signoff.yml:38-43](.github/workflows/qa-signoff.yml:38)). A mistyped path fails the release
job with a bare traceback instead of the actionable message the module already has.

**Fix.** Guard with `if not root.is_dir(): raise DiscoveryError(...)` at the top of
`select_latest_testcase_dir`, and add a test for the missing-root path.

---

## 🟢 On schedule

### P-08 — CI installs unpinned dependencies, bypassing `pyproject.toml`

- **Severity:** Medium · **Target:** 2026-08-14 · **Owner:** unassigned

**Detected.** [ci.yml:18](.github/workflows/ci.yml:18) and [ci.yml:31](.github/workflows/ci.yml:31)
run `pip install pytest python-docx` / `pip install pytest pytest-cov python-docx` with no version
constraints, while [pyproject.toml:10](pyproject.toml:10) declares the `qa-testcases` extra and
[qa-signoff.yml:24](.github/workflows/qa-signoff.yml:24) installs via `pip install -e .`. Two
different dependency sources for the same test suite.

**Fix.** Add a `dev` extra to `pyproject.toml` and have every workflow install
`pip install -e ".[dev]"`. Pin at least major versions so a `python-docx` release cannot break
the sign-off generator without a commit.

---

### P-09 — Money is binary `float`

- **Severity:** Medium · **Target:** 2026-08-21 · **Owner:** unassigned

**Detected.** [cart.py:45-46](src/aiflow_demo/cart.py:45) and
[cart.py:77-80](src/aiflow_demo/cart.py:77) accumulate `unit_price * quantity` in `float` and
round only the final total. Per-item subtotals are never rounded, so representation error
accumulates across items before the single `round()`.

**Why it matters.** Not user-visible at demo scale, but it is the kind of defect the demo's
review agents are meant to surface, and the repo's own style rules favour exact modelling.

**Fix.** Move to `decimal.Decimal` with an explicit quantiser, or document the float choice as
a deliberate demo simplification so reviewers stop re-finding it.

---

### P-10 — `qa-signoff` can reach the generator with no JUnit report

- **Severity:** Low · **Target:** 2026-09-04 · **Owner:** unassigned

**Detected.** [qa-signoff.yml:28](.github/workflows/qa-signoff.yml:28) sets
`continue-on-error: true` on the regression step — correct, since a failing suite must still
produce an honest document. But if pytest aborts during collection, `qa-build/pytest-report.xml`
is never written and the generator step at
[qa-signoff.yml:37-44](.github/workflows/qa-signoff.yml:37) runs against a missing file.

**Fix.** Add a step that checks for the report and substitutes an explicit
"regression unavailable" marker, so the doc records *why* results are missing rather than the
job failing on a path error.

---

### P-11 — Actions pinned to floating tags; no Dependabot

- **Severity:** Low · **Target:** 2026-09-18 · **Owner:** unassigned

**Detected.** All five workflows use floating major tags (`actions/checkout@v4`,
`actions/setup-python@v5`, `actions/upload-artifact@v4`,
`actions/dependency-review-action@v4`). There is no `.github/dependabot.yml`.

**Why it matters.** A repo whose headline feature is merge governance should model
supply-chain hygiene for its own CI.

**Fix.** Pin actions to commit SHAs and add a `dependabot.yml` covering `github-actions` and
`pip` so upgrades arrive as reviewable PRs through the same protected-`main` flow.

---

## Working agreement

- Statuses are relative to the **review date** at the top of this file. Re-date the header when
  the board is re-triaged, and move rows between the three sections.
- Overdue items block the next release tag; nearly-due items should be picked up before new
  feature work.
- Fixes follow [CLAUDE.md](CLAUDE.md): feature branch, tests first, test cases logged under
  `testcases/<branch>/`, local commit, PR with 2 approvals.
