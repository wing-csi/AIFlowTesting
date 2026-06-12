"""Baseline test suite for the demo cart. Must stay green on main."""

import pytest

from aiflow_demo.cart import Cart, CartError


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
