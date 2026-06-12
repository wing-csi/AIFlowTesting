"""Immutable shopping cart — the demo target for AI workflow exercises.

Every operation returns a new object; existing objects are never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass

MAX_QUANTITY_PER_ITEM = 999


class CartError(ValueError):
    """Raised when a cart operation receives invalid input."""


@dataclass(frozen=True)
class CartItem:
    name: str
    unit_price: float
    quantity: int

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise CartError("Item name must not be empty.")
        if self.unit_price < 0:
            raise CartError("Unit price must not be negative.")
        if not 1 <= self.quantity <= MAX_QUANTITY_PER_ITEM:
            raise CartError(
                f"Quantity must be between 1 and {MAX_QUANTITY_PER_ITEM}."
            )

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Cart:
    items: tuple[CartItem, ...] = ()

    def add_item(self, name: str, unit_price: float, quantity: int = 1) -> Cart:
        """Return a new cart with the item appended; this cart is unchanged."""
        return Cart(items=self.items + (CartItem(name, unit_price, quantity),))

    def total(self) -> float:
        """Sum of all item subtotals, rounded to 2 decimal places."""
        return round(sum(item.subtotal for item in self.items), 2)
