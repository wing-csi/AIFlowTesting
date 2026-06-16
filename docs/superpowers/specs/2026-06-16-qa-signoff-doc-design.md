# QA Sign-off Document — GitHub Action Design Spec

- **Date:** 2026-06-16
- **Branch:** `feature/qa-signoff-doc` (cut from `feature/multiple-discounts`)
- **Status:** Design approved — pending implementation plan
- **Origin:** Brainstorming session (design approved by user: "great, lets mark it")

## 1. Goal

Add a GitHub Actions workflow that, when a **release tag** is pushed, generates a Word
(`.docx`) **QA sign-off report** for the branch under release and publishes it as a downloadable
**workflow artifact**. The report consolidates (a) the branch's logged test cases and (b) a freshly
captured regression run (pass/fail + coverage), plus a signature block for formal sign-off. This
extends the repo's "merge governance" theme to release-time QA governance.

## 2. Decisions (locked)

| Decision | Choice |
|---|---|
| Output format | Word `.docx` (via `python-docx`) |
| Test-case scope | The single most-recently-updated `testcases/<branch>/` folder |
| Trigger | Release tag push (`push: tags: ['v*']`) |
| Delivery | Workflow artifact (`actions/upload-artifact`) |
| Branch resolution | Folder whose newest dated section header is the latest |
| Generation library | `python-docx` (Approach A) — not Pandoc, not docxtpl |
| Code location | `src/aiflow_demo/qa_signoff/` (under existing coverage + lint gates) |
| Required status check? | No — release artifact, not a merge gate |

## 3. Trigger & branch resolution

- Workflow triggers on `push` of tags matching `v*` (e.g. `v1.2.0`).
- A tag references a commit (no branch), so the generator selects the testcases folder
  deterministically:
  1. Enumerate immediate subdirectories of `testcases/` (ignore `README.md`).
  2. For each, scan every `*.md` for section headers of the form `## YYYY-MM-DD HH:MM:SS — …`.
  3. Take each folder's **maximum** section datetime; choose the folder with the global maximum.
  4. Tie-break (equal maxima) by folder name descending — deterministic. Log the choice.
- If no folder qualifies (none found / no parseable headers) → exit non-zero with a clear message
  (no silent empty doc).

## 4. Architecture

Small, single-purpose modules under `src/aiflow_demo/qa_signoff/`:

| Module | Responsibility | Key pure function(s) |
|---|---|---|
| `discovery.py` | Pick the target branch folder | `select_latest_testcase_dir(root) -> Path` |
| `parser.py` | Markdown → structured model | `parse_testcase_file(text) -> tuple[TestSection, ...]` |
| `regression.py` | JUnit XML + coverage JSON → result | `load_regression(junit, coverage) -> RegressionResult` |
| `models.py` | Frozen dataclasses (immutability) | `TestCase`, `TestSection`, `RegressionResult`, `SignoffMeta` |
| `docx_builder.py` | Model → Word document | `build_document(...)` + small section helpers |
| `__main__.py` | Thin CLI / orchestration | arg parse → load → build → save |

**Data flow:** tag push → workflow runs pytest (JUnit + coverage JSON) →
`python -m aiflow_demo.qa_signoff` → discovery → parser + regression → docx_builder → save `.docx`
→ `upload-artifact`.

## 5. Document structure (`.docx`)

1. **Title / header** — "QA Sign-off Report", project name, branch under sign-off, release tag,
   short commit SHA, generated-at (UTC).
2. **Result summary** — headline verdict (PASS/FAIL from regression), one-line metrics
   (passed/failed/skipped, coverage %), and a "Configured quality gates" list (tests, coverage ≥80%,
   ruff lint, CodeQL, security-scan) as declared by the repo.
3. **Test-case catalog** — for the selected branch, each dated section rendered as: a section
   heading (datetime — description), optional intro paragraph, and a Word table with columns
   `# | Test case | Type | Test file | Expected result`. Built-in grid table style.
4. **Regression results** — totals table (tests, passed, failed, skipped, errors, duration),
   coverage %, and — if any failures — a list of failing test ids with messages.
5. **Sign-off block** — a signature table with rows for **QA Lead / Dev Lead / Product Owner** and
   columns **Role | Name | Signature | Date**, followed by a decision line:
   `Release decision:  ☐ Approved   ☐ Rejected`.

## 6. Workflow file (outline)

`.github/workflows/qa-signoff.yml`:

```yaml
name: QA Sign-off
on:
  push:
    tags: ['v*']
permissions:
  contents: read
jobs:
  qa-signoff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e . pytest pytest-cov python-docx
      - name: Capture regression results
        continue-on-error: true          # a failing suite still yields an honest doc
        run: >
          python -m pytest
          --junitxml=qa-build/pytest-report.xml
          --cov=src --cov-report=json:qa-build/coverage.json
      - name: Generate QA sign-off document
        run: >
          python -m aiflow_demo.qa_signoff
          --tag "${{ github.ref_name }}"
          --sha "${{ github.sha }}"
          --junit qa-build/pytest-report.xml
          --coverage qa-build/coverage.json
          --testcases-root testcases
          --out qa-build
      - uses: actions/upload-artifact@v4
        with:
          name: qa-signoff-${{ github.ref_name }}
          path: qa-build/*.docx
          if-no-files-found: error
```

## 7. Data model (frozen dataclasses)

- `TestCase(number, description, type, test_file, expected)`
- `TestSection(datetime, title, intro, cases: tuple[TestCase, ...])`
- `RegressionResult(total, passed, failed, skipped, errors, duration_s, coverage_pct, failures, available)`
- `SignoffMeta(project, branch, tag, sha, generated_at)`

All frozen; functions return new objects (no mutation), per repo coding style.

## 8. Error handling & edge cases

- Missing/malformed JUnit or coverage file → `RegressionResult(available=False, …)`; doc renders a
  "regression data unavailable" note rather than crashing.
- Malformed markdown table rows → skipped defensively; a parse-warning count is surfaced (not
  silently dropped).
- No testcases folder selectable → non-zero exit with an explicit message.
- `continue-on-error` on pytest ensures a FAILED suite still produces a doc honestly recording it.
- All boundaries validated; no secrets; `permissions: contents: read` (least privilege).

## 9. Testing plan (`tests/`)

- `test_qa_discovery.py` — newest-folder selection; tie-break; empty/garbage roots raise.
- `test_qa_parser.py` — well-formed single/multi-section files; malformed rows tolerated; empty file.
- `test_qa_regression.py` — passing JUnit; failing JUnit (failures captured); missing files →
  unavailable.
- `test_qa_docx_builder.py` — build a doc from a fixture model; reopen with python-docx and assert
  the title, at least one catalog table, and the sign-off table's three roles are present.
- Fixtures under `tests/fixtures/qa/`: sample testcase markdown + JUnit XML + coverage JSON.
- Keeps `--cov=src` ≥ 80%; new code stays ruff-clean under configured rules (≤7 args, complexity
  ≤10, no smells).
- **CI impact:** because `qa_signoff` lives under `src/` (measured by `--cov=src`), the existing
  `tests` and `coverage` jobs in `ci.yml` must add `python-docx` to their `pip install` step — else
  test collection fails on the `import docx` and coverage drops below the 80% gate.

## 10. File layout (new / changed)

```
.github/workflows/qa-signoff.yml                          (new)
src/aiflow_demo/qa_signoff/__init__.py                    (new)
src/aiflow_demo/qa_signoff/__main__.py                    (new)
src/aiflow_demo/qa_signoff/models.py                      (new)
src/aiflow_demo/qa_signoff/discovery.py                   (new)
src/aiflow_demo/qa_signoff/parser.py                      (new)
src/aiflow_demo/qa_signoff/regression.py                  (new)
src/aiflow_demo/qa_signoff/docx_builder.py                (new)
tests/test_qa_discovery.py                                (new)
tests/test_qa_parser.py                                   (new)
tests/test_qa_regression.py                               (new)
tests/test_qa_docx_builder.py                             (new)
tests/fixtures/qa/…                                       (new)
testcases/feature-qa-signoff-doc/testcases_<ts>.md        (new)
.github/workflows/ci.yml                                  (add python-docx to tests + coverage install)
pyproject.toml                                            (add python-docx as optional dep group [qa])
docs/superpowers/specs/2026-06-16-qa-signoff-doc-design.md (this spec)
```

## 11. Non-goals

- Not a required merge status check.
- Does not push, tag, or create releases (those stay manual per CLAUDE.md).
- Does not aggregate multiple branches (single newest folder only).
- No PDF/HTML output, no email distribution.
- Does not re-run lint/CodeQL/security inside this workflow (regression suite only; other gates
  listed statically).

## 12. Open defaults flagged for review

- **`continue-on-error: true`** on the pytest step (honest doc even on failure).
- **Generator under `src/aiflow_demo/`** (covered by gates) rather than a separate `tools/`.
- **Branch base:** `feature/qa-signoff-doc` cut from `feature/multiple-discounts` (main lacks the
  suite + testcases the action documents).
