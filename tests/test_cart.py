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


class TestItemCount:
    def test_item_count_of_empty_cart_is_zero(self):
        assert Cart().item_count == 0

    def test_item_count_sums_quantities_across_items(self):
        cart = Cart().add_item("Notebook", 25.0, 2).add_item("Pen", 1.5, 4)
        assert cart.item_count == 6

    def test_item_count_counts_single_unit_default_quantity(self):
        assert Cart().add_item("Pen", 1.5).item_count == 1

    def test_item_count_is_unchanged_on_original_after_add(self):
        original = Cart().add_item("Notebook", 25.0, 2)
        _ = original.add_item("Pen", 1.5, 4)
        assert original.item_count == 2


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
