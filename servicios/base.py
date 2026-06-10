"""BaseChatService ABC — single chokepoint for thread→UI dispatch.

All platform services inherit from this class. The _ui_call() method is the
ONLY place in the service layer where wx.CallAfter is invoked.
"""
from __future__ import annotations

import threading
import traceback
import warnings
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Optional

import wx

from servicios.message_router import MessageRouter

if TYPE_CHECKING:
    from controller.chat_controller import ChatController
    from controller.media_controller import MediaController
    from servicios.estadisticas_manager import EstadisticasManager


class BaseChatService(ABC):
    """Abstract base class for all platform chat services.

    Provides:
    - Shared constructor with common attributes
    - _ui_call(): centralized wx.CallAfter wrapper with exception trapping
    - notify_error(): convenience method for error reporting
    - Abstract lifecycle methods: start(), stop(), receive()
    - Deprecated Spanish aliases for backward compatibility
    """

    def __init__(
        self,
        main_controller: Any,
        url: str,
        frame: Any,
        plataforma: str,
        chat_controller: ChatController,
    ) -> None:
        self.main_controller = main_controller
        self.url = url
        self.frame = frame
        self.plataforma = plataforma
        self.chat_controller = chat_controller
        self.estadisticas_manager: EstadisticasManager = chat_controller.estadisticas_manager
        self.media_controller: Optional[MediaController] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Any = None
        self.router = MessageRouter(chat_controller)

    def _ui_call(self, callable: Callable, *args: Any, **kwargs: Any) -> None:
        """Single chokepoint for thread→main UI dispatch.

        Wraps wx.CallAfter and traps exceptions so a faulty UI callable
        never crashes the worker thread.

        Args:
            callable: The function to execute on the main thread.
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.
        """
        def _safe():
            try:
                callable(*args, **kwargs)
            except Exception:
                traceback.print_exc()

        wx.CallAfter(_safe)

    def notify_error(self, message: str) -> None:
        """Report an error to the chat controller via _ui_call.

        Args:
            message: Error message to display.
        """
        self._ui_call(self.chat_controller.notificar_error, message)

    @abstractmethod
    def start(self) -> None:
        """Start the chat service. Sets _running=True, spawns worker thread."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the chat service. Sets _running=False, releases resources. Idempotent."""
        ...

    @abstractmethod
    def receive(self) -> None:
        """Message reception loop. MUST NOT be called from the main thread."""
        ...

    # --- Deprecated Spanish aliases (backward compat for Phase 1) ---

    def iniciar_chat(self) -> None:
        """Deprecated: Use start() instead."""
        warnings.warn(
            "iniciar_chat() is deprecated, use start() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.start()

    def detener(self) -> None:
        """Deprecated: Use stop() instead."""
        warnings.warn(
            "detener() is deprecated, use stop() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.stop()
