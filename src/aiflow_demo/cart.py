"""Immutable shopping cart — the demo target for AI workflow exercises.

Every operation returns a new object; existing objects are never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

MAX_QUANTITY_PER_ITEM = 999
MAX_ECHOED_CODE_LENGTH = 64
MAX_DISCOUNT_RATE = 1.0

DISCOUNT_RATES: MappingProxyType[str, float] = MappingProxyType(
    {"WELCOME10": 0.10, "VIP20": 0.20}
)


class CartError(ValueError):
    """Raised when a cart operation receives invalid input."""


def _printable_excerpt(text: str, max_length: int = MAX_ECHOED_CODE_LENGTH) -> str:
    """Strip non-printable characters and truncate, for safe echoing in errors."""
    return "".join(ch for ch in text[:max_length] if ch.isprintable())


def _normalize_code(code: str) -> str:
    """Validate and normalize a single discount code; raise CartError if invalid."""
    if not isinstance(code, str):
        raise CartError("Discount code must be a string.")
    normalized = code.strip().upper()
    if not normalized:
        raise CartError("Discount code must not be empty.")
    if normalized not in DISCOUNT_RATES:
        raise CartError(f"Unknown discount code: {_printable_excerpt(normalized)!r}.")
    return normalized


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
    discount_codes: tuple[str, ...] = ()

    def add_item(self, name: str, unit_price: float, quantity: int = 1) -> Cart:
        """Return a new cart with the item appended; this cart is unchanged."""
        return Cart(
            items=self.items + (CartItem(name, unit_price, quantity),),
            discount_code=self.discount_code,
            discount_codes=self.discount_codes,
        )

    def apply_discount(self, code: str) -> Cart:
        """Return a new cart with the discount code applied; this cart is unchanged."""
        normalized = _normalize_code(code)
        return Cart(
            items=self.items,
            discount_code=normalized,
            discount_codes=self.discount_codes,
        )

    def apply_discounts(self, *codes: str) -> Cart:
        """Return a new cart with all given codes stacked; this cart is unchanged.

        No-op when called with no arguments. Atomic: all codes are validated
        before any state change. Duplicate codes are deduplicated order-preservingly.
        """
        if not codes:
            return self
        # Validate ALL codes atomically before constructing anything.
        normalized_new = tuple(_normalize_code(c) for c in codes)
        # Union onto existing stack, order-preserving dedupe.
        combined = tuple(
            dict.fromkeys(self.discount_codes + normalized_new)
        )
        return Cart(
            items=self.items,
            discount_code=self.discount_code,
            discount_codes=combined,
        )

    def add_discount(self, code: str) -> Cart:
        """Return a new cart with one additional discount code stacked."""
        return self.apply_discounts(code)

    @property
    def discount_rate(self) -> float:
        """Return the combined discount rate from both the legacy field and the stack."""
        legacy: list[str] = [self.discount_code] if self.discount_code is not None else []
        all_codes = list(dict.fromkeys(legacy + list(self.discount_codes)))
        total = round(sum(DISCOUNT_RATES[c] for c in all_codes), 10)
        return max(0.0, min(total, MAX_DISCOUNT_RATE))

    def total(self) -> float:
        """Sum of all item subtotals with discount applied, rounded to 2 decimal places."""
        raw = sum(item.subtotal for item in self.items)
        return round(raw * (1 - self.discount_rate), 2)
