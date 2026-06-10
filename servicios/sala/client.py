"""Sala service client — PlayroomHelper connection and lifecycle management.

Inherits from BaseChatService. Uses _ui_call() for all UI dispatch.
No direct wx.CallAfter calls in this module.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

import wx

from globals import data_store
from globals.resources import rutasonidos
from helpers.playroom_helper import PlayroomHelper
from helpers.timer import Timer
from setup import player, reader
from servicios.base import BaseChatService
from servicios.sala.handlers import process_message

if TYPE_CHECKING:
    from controller.chat_controller import ChatController


class ServicioSala(BaseChatService):
    """Playroom chat service using PlayroomHelper for message polling.

    Connects to the Playroom application window, polls for new messages
    on a timer thread, and routes them through the standard pipeline.
    """

    def __init__(
        self,
        main_controller: Any,
        url: str,
        frame: Any,
        plataforma: str,
        chat_controller: ChatController,
    ) -> None:
        super().__init__(main_controller, url, frame, plataforma, chat_controller)
        self.chat: Optional[PlayroomHelper] = None
        self.translator: Any = None

    def start(self) -> None:
        """Start the Sala chat service.

        Creates PlayroomHelper connection, optionally initializes translator,
        spawns a timer thread for message polling, and plays entry sound.
        """
        try:
            self._running = True
            self.chat = PlayroomHelper()

            if data_store.dst:
                from utils import translator as translator_module
                self.translator = translator_module.TranslatorWrapper()

            self._thread = Timer(0.5, self.receive)
            self._thread.daemon = True
            self._thread.start()

            player.play(rutasonidos[6])
            reader.leer_sapi(_("Ingresando al chat."))
            title = _("Chat de la sala de juegos")
            self._ui_call(self.chat_controller.agregar_titulo, title)
            self._ui_call(
                self.chat_controller.chat_dialog.update_chat_page_title,
                self.chat_controller,
                title,
            )
        except Exception as e:
            self._running = False
            self.notify_error(str(e))

    def stop(self) -> None:
        """Stop the Sala chat service. Idempotent."""
        self._running = False

    def receive(self) -> None:
        """Message reception loop. Called by Timer thread every 0.5s.

        Fetches new messages from PlayroomHelper and dispatches each
        through the handler pipeline.
        """
        try:
            self.chat.get_new_messages()
            for message in self.chat.new_messages:
                self.estadisticas_manager.agregar_mensaje(message["author"])
                if not self._running:
                    break
                process_message(self, message)
        except Exception as e:
            self.notify_error(str(e))
