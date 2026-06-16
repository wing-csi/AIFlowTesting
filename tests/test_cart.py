"""Baseline test suite for the demo cart. Must stay green on main."""

import pytest

from aiflow_demo.cart import DISCOUNT_RATES, Cart, CartError


class TestAddItem:
    def test_add_item_returns_new_cart_and_leaves_original_unchanged(self):
        empty = Cart()
        cart = empty.add_item("Notebook", 25.0, 2)
        assert empty.items == ()
        assert len(cart.items) == 1
        assert cart.items[0].name == "Notebook"

    def test_add_item_rejects_blank_name(self):
        with pytest.raises(CartError, match="name"):
            Cart().add_item("   ", 10.0)

    def test_add_item_rejects_negative_price(self):
        with pytest.raises(CartError, match="price"):
            Cart().add_item("Pen", -1.0)

    def test_add_item_rejects_zero_quantity(self):
        with pytest.raises(CartError, match="Quantity"):
            Cart().add_item("Pen", 1.0, 0)

    def test_add_item_rejects_excessive_quantity(self):
        with pytest.raises(CartError, match="Quantity"):
            Cart().add_item("Pen", 1.0, 1000)


class TestTotal:
    def test_total_of_empty_cart_is_zero(self):
        assert Cart().total() == 0

    def test_total_sums_item_subtotals(self):
        cart = Cart().add_item("Notebook", 25.0, 2).add_item("Pen", 1.5, 4)
        assert cart.total() == 56.0

    def test_total_rounds_to_two_decimals(self):
        cart = Cart().add_item("Sticker", 0.333, 3)
        assert cart.total() == 1.0

    def test_total_applies_welcome10_discount(self):
        # 10 items at 10.0 each = 100.0 total; WELCOME10 = 10% off → 90.0
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount("WELCOME10")
        assert cart.total() == 90.0

    def test_total_applies_vip20_discount(self):
        # 10 items at 10.0 each = 100.0 total; VIP20 = 20% off → 80.0
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount("VIP20")
        assert cart.total() == 80.0

    def test_total_rounds_discounted_value_to_two_decimals(self):
        # 3 items at 3.33 = 9.99 total; WELCOME10 = 10% off → 9.99 * 0.9 = 8.991 → rounds to 8.99
        cart = Cart().add_item("Sticker", 3.33, 3).apply_discount("WELCOME10")
        assert cart.total() == 8.99


class TestApplyDiscount:
    def test_apply_discount_returns_new_cart_and_leaves_original_unchanged(self):
        original = Cart().add_item("Widget", 50.0, 2)
        discounted = original.apply_discount("WELCOME10")
        # original is unchanged
        assert original.discount_code is None
        assert original.items == discounted.items
        # new cart has discount applied
        assert discounted.discount_code == "WELCOME10"

    def test_welcome10_applies_10_percent_off_100(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount("WELCOME10")
        assert cart.total() == 90.0

    def test_vip20_applies_20_percent_off_100(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount("VIP20")
        assert cart.total() == 80.0

    def test_lowercase_code_accepted_and_normalized(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount("welcome10")
        assert cart.discount_code == "WELCOME10"
        assert cart.total() == 90.0

    def test_whitespace_padded_code_trimmed_and_accepted(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount(" WELCOME10 ")
        assert cart.discount_code == "WELCOME10"
        assert cart.total() == 90.0

    def test_mixed_case_code_accepted(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discount("Welcome10")
        assert cart.discount_code == "WELCOME10"
        assert cart.total() == 90.0

    def test_unknown_code_raises_cart_error(self):
        with pytest.raises(CartError, match="Unknown discount code"):
            Cart().add_item("Widget", 10.0, 1).apply_discount("BOGUS")

    def test_empty_string_raises_cart_error(self):
        with pytest.raises(CartError, match="empty"):
            Cart().add_item("Widget", 10.0, 1).apply_discount("")

    def test_whitespace_only_code_raises_cart_error(self):
        with pytest.raises(CartError, match="empty"):
            Cart().add_item("Widget", 10.0, 1).apply_discount("   ")

    def test_rejected_code_leaves_original_cart_unchanged(self):
        original = Cart().add_item("Widget", 10.0, 2)
        with pytest.raises(CartError):
            original.apply_discount("BOGUS")
        assert original.items[0].name == "Widget"
        assert original.discount_code is None

    def test_valid_code_on_empty_cart_total_is_zero(self):
        assert Cart().apply_discount("VIP20").total() == 0.0

    def test_second_code_replaces_first(self):
        cart = (
            Cart()
            .add_item("Widget", 10.0, 10)
            .apply_discount("WELCOME10")
            .apply_discount("VIP20")
        )
        assert cart.discount_rate == 0.20
        assert cart.total() == 80.0

    def test_discount_rate_is_zero_with_no_code(self):
        cart = Cart().add_item("Widget", 10.0, 1)
        assert cart.discount_rate == 0.0

    def test_long_unknown_code_is_truncated_in_error_message(self):
        with pytest.raises(CartError) as exc_info:
            Cart().apply_discount("X" * 10_000)
        assert len(str(exc_info.value)) < 200

    def test_discount_rates_mapping_is_immutable(self):
        with pytest.raises(TypeError):
            DISCOUNT_RATES["FREE100"] = 1.0


class TestApplyDiscounts:
    # 1. New cart has discount_codes == () by default
    def test_new_cart_has_empty_discount_codes(self):
        assert Cart().discount_codes == ()

    # 2. apply_discounts stacks additively
    def test_apply_discounts_stacks_two_codes_additively(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discounts("WELCOME10", "VIP20")
        assert cart.discount_rate == 0.30
        assert cart.total() == 70.0

    # 3. apply_discounts returns a new cart; original unchanged
    def test_apply_discounts_returns_new_cart_original_unchanged(self):
        original = Cart().add_item("Widget", 10.0, 10)
        new_cart = original.apply_discounts("WELCOME10", "VIP20")
        assert original.discount_codes == ()
        assert original.items == new_cart.items

    # 4. Lowercase/mixed-case codes normalized and accepted
    def test_apply_discounts_normalizes_lowercase_and_mixed_case(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discounts("welcome10", "Vip20")
        assert cart.discount_rate == 0.30
        assert cart.discount_codes == ("WELCOME10", "VIP20")

    # 5. Whitespace-padded codes trimmed and accepted
    def test_apply_discounts_trims_whitespace_padded_codes(self):
        cart = Cart().add_item("Widget", 10.0, 10).apply_discounts(" WELCOME10 ", " VIP20 ")
        assert cart.discount_codes == ("WELCOME10", "VIP20")
        assert cart.discount_rate == 0.30

    # 6. Empty string in batch raises CartError matching "empty"
    def test_apply_discounts_empty_string_raises_cart_error(self):
        with pytest.raises(CartError, match="empty"):
            Cart().apply_discounts("WELCOME10", "")

    # 7. Whitespace-only code in batch raises CartError matching "empty"
    def test_apply_discounts_whitespace_only_code_raises_cart_error(self):
        with pytest.raises(CartError, match="empty"):
            Cart().apply_discounts("WELCOME10", "   ")

    # 8. Unknown code in batch raises CartError matching "Unknown discount code"
    def test_apply_discounts_unknown_code_raises_cart_error(self):
        with pytest.raises(CartError, match="Unknown discount code"):
            Cart().apply_discounts("WELCOME10", "BOGUS")

    # 9. Long unknown code error message is truncated (< 200 chars)
    def test_apply_discounts_long_unknown_code_truncated_in_error_message(self):
        with pytest.raises(CartError) as exc_info:
            Cart().apply_discounts("X" * 10_000)
        assert len(str(exc_info.value)) < 200

    # 10. Rejected batch leaves original cart unchanged (atomic)
    def test_apply_discounts_atomic_leaves_original_unchanged_on_any_failure(self):
        original = Cart().add_item("Widget", 10.0, 2)
        with pytest.raises(CartError):
            original.apply_discounts("WELCOME10", "BOGUS")
        assert original.discount_codes == ()
        # Also verify invalid-then-valid order also doesn't partially apply
        with pytest.raises(CartError):
            original.apply_discounts("BOGUS", "WELCOME10")
        assert original.discount_codes == ()

    # 11. Duplicate code in one call deduped
    def test_apply_discounts_deduplicates_duplicate_code_in_single_call(self):
        cart = Cart().apply_discounts("WELCOME10", "WELCOME10")
        assert cart.discount_rate == 0.10
        assert cart.discount_codes == ("WELCOME10",)

    # 12. Duplicate against already-stacked code deduped
    def test_apply_discounts_deduplicates_against_already_stacked_code(self):
        cart = (
            Cart()
            .apply_discounts("WELCOME10")
            .apply_discounts("WELCOME10", "VIP20")
        )
        assert cart.discount_codes == ("WELCOME10", "VIP20")
        assert cart.discount_rate == 0.30

    # 13. add_discount accumulates
    def test_add_discount_accumulates_codes(self):
        cart = Cart().apply_discounts("WELCOME10").add_discount("VIP20")
        assert cart.discount_rate == 0.30

    # 14. apply_discount (legacy) then add_discount combines rates
    def test_legacy_apply_discount_then_add_discount_combines_rates(self):
        cart = (
            Cart()
            .add_item("Widget", 10.0, 10)
            .apply_discount("WELCOME10")
            .add_discount("VIP20")
        )
        assert cart.discount_rate == 0.30
        assert cart.total() == 70.0
        assert cart.discount_code == "WELCOME10"

    # 15. apply_discount after stacking keeps the stack
    def test_apply_discount_after_stacking_keeps_discount_codes(self):
        cart = (
            Cart()
            .apply_discounts("VIP20")
            .apply_discount("WELCOME10")
        )
        assert cart.discount_codes == ("VIP20",)
        assert cart.discount_code == "WELCOME10"

    # 16. Combined rate clamped to <= 1.0
    def test_combined_discount_rate_clamped_to_max_one(self, monkeypatch):
        from types import MappingProxyType
        import aiflow_demo.cart as cart_module
        monkeypatch.setattr(
            cart_module,
            "DISCOUNT_RATES",
            MappingProxyType({"WELCOME10": 0.10, "VIP20": 0.20, "MEGA": 2.0}),
        )
        cart = Cart().add_item("Widget", 10.0, 10).apply_discounts("MEGA")
        assert cart.discount_rate == 1.0
        assert cart.total() == 0.0

    # 17. apply_discounts on empty cart -> total 0.0
    def test_apply_discounts_on_empty_cart_total_is_zero(self):
        cart = Cart().apply_discounts("WELCOME10", "VIP20")
        assert cart.total() == 0.0

    # 18. apply_discounts discounted total rounds to 2 decimals
    def test_apply_discounts_discounted_total_rounds_to_two_decimals(self):
        # 3 items at 3.33 = 9.99; WELCOME10+VIP20 = 30% off → 9.99 * 0.7 = 6.993 → 6.99
        cart = Cart().add_item("Sticker", 3.33, 3).apply_discounts("WELCOME10", "VIP20")
        assert cart.total() == 6.99

    # 19. apply_discounts() with no args is a no-op
    def test_apply_discounts_no_args_is_noop(self):
        original = Cart().add_item("Widget", 10.0, 10).apply_discounts("WELCOME10")
        result = original.apply_discounts()
        assert result.discount_codes == original.discount_codes
        assert result.total() == original.total()

    # 20. apply_discounts does not mutate original (immutability)
    def test_apply_discounts_does_not_mutate_original(self):
        original = Cart().add_item("Widget", 10.0, 2)
        original.apply_discounts("WELCOME10")
        assert original.discount_codes == ()

    # 21. add_discount does not mutate original
    def test_add_discount_does_not_mutate_original(self):
        original = Cart().add_item("Widget", 10.0, 2)
        original.add_discount("WELCOME10")
        assert original.discount_codes == ()

    # 22. Non-string code is rejected with a clear CartError (boundary validation)
    def test_apply_discounts_rejects_non_string_code(self):
        with pytest.raises(CartError, match="string"):
            Cart().apply_discounts("WELCOME10", 123)

    def test_add_discount_rejects_non_string_code(self):
        with pytest.raises(CartError, match="string"):
            Cart().add_discount(None)

    # 23. apply_discounts must NOT absorb the legacy discount_code into the stack
    def test_apply_discounts_does_not_absorb_legacy_discount_code_into_stack(self):
        cart = Cart().apply_discount("WELCOME10").apply_discounts("VIP20")
        assert cart.discount_code == "WELCOME10"
        assert cart.discount_codes == ("VIP20",)

    # 24. A code in both the legacy field and the stack is counted once (no double charge)
    def test_same_code_in_legacy_and_stack_counted_once(self):
        cart = (
            Cart()
            .add_item("Widget", 10.0, 10)
            .apply_discount("WELCOME10")
            .apply_discounts("WELCOME10", "VIP20")
        )
        assert cart.discount_rate == 0.30
        assert cart.total() == 70.0

    # 25. Combined rate is floored at 0.0 — a negative rate must never overcharge
    def test_combined_discount_rate_floored_at_zero(self, monkeypatch):
        from types import MappingProxyType
        import aiflow_demo.cart as cart_module
        monkeypatch.setattr(
            cart_module,
            "DISCOUNT_RATES",
            MappingProxyType({"WELCOME10": 0.10, "SURCHARGE": -0.5}),
        )
        cart = Cart().add_item("Widget", 10.0, 10).apply_discounts("SURCHARGE")
        assert cart.discount_rate == 0.0
        assert cart.total() == 100.0
