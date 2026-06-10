"""Tests for servicios.shared.currency — CurrencyConverter.convert()"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from servicios.shared.currency import CurrencyConverter


class TestCurrencyConverterUSD:
    """R-VL-001b: When target is USD, returns (amount/100, 'USD') without API call."""

    def test_usd_target_skips_api(self):
        result, code = CurrencyConverter.convert(500, "USD", "USD")
        assert result == 5.0
        assert code == "USD"

    def test_usd_target_does_not_call_google_currency(self):
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            CurrencyConverter.convert(500, "USD", "USD")
            mock_gc.convert.assert_not_called()

    def test_usd_small_amount(self):
        result, code = CurrencyConverter.convert(50, "USD", "USD")
        assert result == 0.5
        assert code == "USD"


class TestCurrencyConverterDefault:
    """R-VL-001c: When target is 'Por defecto', returns (None, None)."""

    def test_por_defecto_returns_none(self):
        result, code = CurrencyConverter.convert(500, "USD", "Por defecto")
        assert result is None
        assert code is None

    def test_por_defecto_does_not_call_api(self):
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            CurrencyConverter.convert(500, "USD", "Por defecto")
            mock_gc.convert.assert_not_called()


class TestCurrencyConverterAPI:
    """R-VL-001a: Converts via google_currency on success."""

    def test_successful_conversion(self):
        mock_response = json.dumps({
            "converted": True,
            "amount": 4500.0,
        })
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            mock_gc.convert.return_value = mock_response
            result, code = CurrencyConverter.convert(500, "USD", "ARS")
            assert result == 4500.0
            assert code == "ARS"

    def test_api_returns_not_converted(self):
        mock_response = json.dumps({
            "converted": False,
        })
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            mock_gc.convert.return_value = mock_response
            result, code = CurrencyConverter.convert(500, "USD", "XYZ")
            assert result is None
            assert code is not None  # error message


class TestCurrencyConverterError:
    """R-VL-001d: On API error, returns (None, error_string), never crashes."""

    def test_connection_error_returns_none(self):
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            mock_gc.convert.side_effect = ConnectionError("network down")
            result, code = CurrencyConverter.convert(100, "USD", "ARS")
            assert result is None
            assert "network down" in code

    def test_json_error_returns_none(self):
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            mock_gc.convert.return_value = "not valid json"
            result, code = CurrencyConverter.convert(100, "USD", "ARS")
            assert result is None
            assert code is not None

    def test_generic_exception_returns_none(self):
        with patch("servicios.shared.currency.google_currency") as mock_gc:
            mock_gc.convert.side_effect = RuntimeError("unexpected")
            result, code = CurrencyConverter.convert(100, "USD", "EUR")
            assert result is None
            assert "unexpected" in code
