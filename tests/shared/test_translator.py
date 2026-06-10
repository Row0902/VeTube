"""Tests for servicios.shared.translator — MessageTranslator"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from servicios.shared.translator import MessageTranslator


class TestMessageTranslatorSuccess:
    """R-VL-002a: Wraps translator and returns translated text."""

    def test_translate_success(self):
        mock_wrapper = MagicMock()
        mock_wrapper.translate.return_value = "Hello world"

        with patch("servicios.shared.translator.TranslatorWrapper", return_value=mock_wrapper):
            mt = MessageTranslator("en")
            result = mt.translate("Hola mundo")
            assert result == "Hello world"

    def test_translate_calls_wrapper_with_correct_args(self):
        mock_wrapper = MagicMock()
        mock_wrapper.translate.return_value = "translated"

        with patch("servicios.shared.translator.TranslatorWrapper", return_value=mock_wrapper):
            mt = MessageTranslator("fr")
            mt.translate("Hello")
            mock_wrapper.translate.assert_called_once_with(text="Hello", target="fr")


class TestMessageTranslatorFailure:
    """R-VL-002b: On translation error, returns original text."""

    def test_translate_error_returns_original(self):
        mock_wrapper = MagicMock()
        mock_wrapper.translate.side_effect = Exception("service unavailable")

        with patch("servicios.shared.translator.TranslatorWrapper", return_value=mock_wrapper):
            mt = MessageTranslator("en")
            result = mt.translate("Hola")
            assert result == "Hola"


class TestMessageTranslatorEmpty:
    """R-VL-002c: Empty/None input returns empty string."""

    def test_empty_string_returns_empty(self):
        mock_wrapper = MagicMock()

        with patch("servicios.shared.translator.TranslatorWrapper", return_value=mock_wrapper):
            mt = MessageTranslator("en")
            result = mt.translate("")
            assert result == ""

    def test_none_target_skips_translation(self):
        mt = MessageTranslator(None)
        result = mt.translate("Hola mundo")
        assert result == "Hola mundo"

    def test_none_target_does_not_create_wrapper(self):
        with patch("servicios.shared.translator.TranslatorWrapper") as mock_cls:
            mt = MessageTranslator(None)
            mock_cls.assert_not_called()
            result = mt.translate("test")
            assert result == "test"
