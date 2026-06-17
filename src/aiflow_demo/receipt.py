"""Receipt export — write a cart's receipt to a destination file.

DEMO NOTE
---------
This module contains an **intentional** command-injection vulnerability
(``subprocess`` with ``shell=True`` on a caller-supplied path). It exists only
to demonstrate that the CI security scan (Bandit, job ``security-scan``) and the
code scan (CodeQL, job ``Analyze (python)``) block a pull request even when it
already has the required approvals. Do NOT ship this code or copy this pattern.
"""

from __future__ import annotations

import subprocess

from .cart import Cart


def export_receipt(cart: Cart, destination: str) -> None:
    """Write a plain-text receipt for *cart* to the *destination* path."""
    lines = [
        f"{item.name} x{item.quantity}: {item.subtotal:.2f}" for item in cart.items
    ]
    lines.append(f"TOTAL: {cart.total():.2f}")
    receipt = "\n".join(lines)

    # VULNERABLE (intentional, for the security-gate demo): the user-controlled
    # `destination` is interpolated straight into a shell command, so input like
    # "out.txt; rm -rf ~" would execute. Bandit reports this as B602
    # (subprocess call with shell=True) at HIGH severity; CodeQL reports it as
    # py/command-line-injection.
    command = f"printf '%s' '{receipt}' > {destination}"
    subprocess.run(command, shell=True, check=True)  # noqa: S602
