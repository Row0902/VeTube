"""Pure-function message translation module.

No wxPython, no data_store, no UI imports. Safe to import without a running wx.App.
"""
from __future__ import annotations

import traceback

from utils.translator import TranslatorWrapper


class MessageTranslator:
    """Wraps googletrans via TranslatorWrapper for message translation.

    The target language is a constructor parameter — never reads data_store directly.
    Services resolve data_store.dst and pass it in.
    """

    def __init__(self, target_lang: str | None) -> None:
        self._target = target_lang
        self._wrapper: TranslatorWrapper | None = (
            TranslatorWrapper() if target_lang else None
        )

    def translate(self, text: str) -> str:
        """Translate text to the configured target language.

        Args:
            text: The text to translate.

        Returns:
            Translated text on success, original text on failure or if no target.
        """
        if not self._wrapper or not text:
            return text if text else ""

        try:
            return self._wrapper.translate(text=text, target=self._target)
        except Exception:
            traceback.print_exc()
            return text
