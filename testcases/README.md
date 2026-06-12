# Test case logs

Every task that creates or modifies tests must record its test cases here. The convention
(defined in [CLAUDE.md](../CLAUDE.md)) is:

- **One folder per branch**, with `/` replaced by `-`:
  branch `feature/discount-codes` → `testcases/feature-discount-codes/`
- **One file per branch, named with the datetime of its first recording**:
  `testcases_<yyyyMMdd_HHmmss>.md` (e.g. `testcases_20260612_143000.md`)
- **Later recordings on the same branch append** a new timestamped section to that same file —
  never create a second file for the same branch.

Example file content after two recordings on one branch:

```markdown
# Test cases — feature/discount-codes

## 2026-06-12 14:30:00 — Add percentage discount codes

| # | Test case | Type | Test file | Expected result |
|---|-----------|------|-----------|-----------------|
| 1 | WELCOME10 applies 10% off | unit | tests/test_cart.py | total reduced by 10% |
| 2 | Unknown code is rejected | unit | tests/test_cart.py | CartError raised |

## 2026-06-12 15:10:00 — Cap discount at $50

| # | Test case | Type | Test file | Expected result |
|---|-----------|------|-----------|-----------------|
| 1 | Discount never exceeds $50 | unit | tests/test_cart.py | discount capped at 50.00 |
```
