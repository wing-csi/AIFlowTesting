"""Immutable shopping cart — the demo target for AI workflow exercises.

Every operation returns a new object; existing objects are never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

MAX_QUANTITY_PER_ITEM = 999
MAX_ECHOED_CODE_LENGTH = 64

DISCOUNT_RATES: MappingProxyType[str, float] = MappingProxyType(
    {"WELCOME10": 0.10, "VIP20": 0.20}
)


def _printable_excerpt(text: str, max_length: int = MAX_ECHOED_CODE_LENGTH) -> str:
    """Strip non-printable characters and truncate, for safe echoing in errors."""
    return "".join(ch for ch in text[:max_length] if ch.isprintable())


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
    discount_code: str | None = None

    def add_item(self, name: str, unit_price: float, quantity: int = 1) -> Cart:
        """Return a new cart with the item appended; this cart is unchanged."""
        return Cart(
            items=self.items + (CartItem(name, unit_price, quantity),),
            discount_code=self.discount_code,
        )

    def apply_discount(self, code: str) -> Cart:
        """Return a new cart with the discount code applied; this cart is unchanged."""
        normalized = code.strip().upper()
        if not normalized:
            raise CartError("Discount code must not be empty.")
        if normalized not in DISCOUNT_RATES:
            raise CartError(f"Unknown discount code: {_printable_excerpt(normalized)!r}.")
        return Cart(items=self.items, discount_code=normalized)

    @property
    def item_count(self) -> int:
        """Total number of units across all items in the cart."""
        return sum(item.quantity for item in self.items)

    @property
    def discount_rate(self) -> float:
        """Return the discount rate for the applied code, or 0.0 if none."""
        if self.discount_code is None:
            return 0.0
        return DISCOUNT_RATES.get(self.discount_code, 0.0)

    def total(self) -> float:
        """Sum of all item subtotals with discount applied, rounded to 2 decimal places."""
        raw = sum(item.subtotal for item in self.items)
        return round(raw * (1 - self.discount_rate), 2)
