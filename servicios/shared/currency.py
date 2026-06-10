"""Pure-function currency conversion module.

No wxPython, no data_store, no UI imports. Safe to import without a running wx.App.
"""
from __future__ import annotations

import json
import traceback

import google_currency


class CurrencyConverter:
    """Stateless currency conversion using google_currency API."""

    @staticmethod
    def convert(amount_cents: float, source: str, target: str) -> tuple[float | None, str | None]:
        """Convert an amount from source to target currency.

        Args:
            amount_cents: Amount in cents (e.g. 500 = $5.00).
            source: Source currency code (e.g. "USD").
            target: Target currency code, "USD", or "Por defecto".

        Returns:
            (converted_amount, currency_code) on success.
            (None, None) when target is "Por defecto" (no conversion needed).
            (None, error_string) on API failure.
        """
        if target == "Por defecto":
            return None, None

        if target == "USD":
            return amount_cents / 100.0, "USD"

        try:
            raw = google_currency.convert(source, target, int(amount_cents / 100))
            data = json.loads(raw)
            if data.get("converted"):
                return data["amount"], target
            return None, "conversion returned converted=False"
        except Exception as e:
            traceback.print_exc()
            return None, str(e)
