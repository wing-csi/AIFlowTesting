# Test cases — feature/sample

## 2026-06-10 09:00:00 — First task

This section covers the initial set of test cases for the first task.

| # | Test case | Type | Test file | Expected result |
|---|-----------|------|-----------|-----------------|
| 1 | Cart adds item correctly | unit | tests/test_cart.py | new cart returned with item |
| 2 | Cart rejects blank name | unit | tests/test_cart.py | CartError raised |

## 2026-06-11 10:30:00 — Second task

| # | Test case | Type | Test file | Expected result |
|---|-----------|------|-----------|-----------------|
| 3 | Discount WELCOME10 applies 10% off | unit | tests/test_cart.py | total reduced by 10% |
| too few cells here |
| 5 | VIP20 applies 20% off | unit | tests/test_cart.py | total reduced by 20% |
