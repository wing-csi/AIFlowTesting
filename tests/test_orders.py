"""Tests for the 10-parameter order-builder demo artifact (orders.create_order)."""

from dataclasses import FrozenInstanceError

import pytest

from aiflow_demo.orders import Order, OrderError, create_order


def _valid_order() -> Order:
    return create_order(
        "Ada Lovelace",
        "ada@example.com",
        "1 Analytical Way",
        "London",
        "EC1A 1AA",
        "UK",
        3,
        100.0,
        5.0,
        10.0,
    )


class TestCreateOrder:
    def test_create_order_populates_all_fields(self):
        order = _valid_order()
        assert order.customer_name == "Ada Lovelace"
        assert order.email == "ada@example.com"
        assert order.street == "1 Analytical Way"
        assert order.city == "London"
        assert order.postal_code == "EC1A 1AA"
        assert order.country == "UK"
        assert order.item_count == 3
        assert order.subtotal == 100.0
        assert order.shipping == 5.0
        assert order.discount == 10.0

    def test_total_is_subtotal_plus_shipping_less_discount(self):
        # 100.0 + 5.0 - 10.0 = 95.0
        assert _valid_order().total == 95.0

    def test_total_rounds_to_two_decimals(self):
        order = create_order(
            "Grace Hopper", "grace@example.com", "2 Cobol St", "New York",
            "10001", "US", 1, 3.333, 0.0, 0.0,
        )
        assert order.total == 3.33

    def test_total_floored_at_zero_when_discount_exceeds(self):
        order = create_order(
            "Alan Turing", "alan@example.com", "3 Enigma Rd", "Manchester",
            "M1 1AA", "UK", 1, 10.0, 0.0, 50.0,
        )
        assert order.total == 0.0

    def test_order_is_immutable(self):
        order = _valid_order()
        with pytest.raises(FrozenInstanceError):
            order.subtotal = 0.0


class TestValidation:
    def test_blank_customer_name_raises(self):
        with pytest.raises(OrderError, match="name"):
            create_order(
                "   ", "x@example.com", "s", "c", "p", "UK", 1, 0.0, 0.0, 0.0,
            )

    def test_invalid_email_raises(self):
        with pytest.raises(OrderError, match="Email"):
            create_order(
                "Ada", "no-at-symbol", "s", "c", "p", "UK", 1, 0.0, 0.0, 0.0,
            )

    def test_zero_item_count_raises(self):
        with pytest.raises(OrderError, match="Item count"):
            create_order(
                "Ada", "x@example.com", "s", "c", "p", "UK", 0, 0.0, 0.0, 0.0,
            )

    def test_negative_amount_raises(self):
        with pytest.raises(OrderError, match="negative"):
            create_order(
                "Ada", "x@example.com", "s", "c", "p", "UK", 1, -1.0, 0.0, 0.0,
            )
