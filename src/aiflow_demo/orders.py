"""Order assembly — build an immutable order record from individual fields.

DEMO NOTE
---------
``create_order`` deliberately takes **10 positional parameters**. That trips the
"too many parameters" maintainability smell reported by static analysis:
SonarQube ``python:S107`` (default threshold 7, **Major** code smell) and
pylint ``R0913`` / ruff ``PLR0913`` (default threshold 5). It exists as a demo
artifact for the scan pipeline on this branch. A real design would group these
fields into small value objects (e.g. ``Customer`` + ``Address``) instead of
passing ten loose arguments.
"""

from __future__ import annotations

from dataclasses import dataclass


class OrderError(ValueError):
    """Raised when an order is constructed with invalid input."""


@dataclass(frozen=True)
class Order:
    """An immutable order record."""

    customer_name: str
    email: str
    street: str
    city: str
    postal_code: str
    country: str
    item_count: int
    subtotal: float
    shipping: float
    discount: float

    def __post_init__(self) -> None:
        if not self.customer_name or not self.customer_name.strip():
            raise OrderError("Customer name must not be empty.")
        if "@" not in self.email:
            raise OrderError("Email must contain '@'.")
        if self.item_count < 1:
            raise OrderError("Item count must be at least 1.")
        if min(self.subtotal, self.shipping, self.discount) < 0:
            raise OrderError("Monetary amounts must not be negative.")

    @property
    def total(self) -> float:
        """Amount due: subtotal plus shipping, less discount, floored at 0."""
        return round(max(0.0, self.subtotal + self.shipping - self.discount), 2)


def create_order(
    customer_name: str,
    email: str,
    street: str,
    city: str,
    postal_code: str,
    country: str,
    item_count: int,
    subtotal: float,
    shipping: float,
    discount: float,
) -> Order:
    """Assemble an :class:`Order` from individual fields.

    Ten parameters — intentional ``S107`` code smell; see the module docstring.
    """
    return Order(
        customer_name=customer_name,
        email=email,
        street=street,
        city=city,
        postal_code=postal_code,
        country=country,
        item_count=item_count,
        subtotal=subtotal,
        shipping=shipping,
        discount=discount,
    )
