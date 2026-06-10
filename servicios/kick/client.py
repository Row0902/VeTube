"""Kick service client — kick.Client connection and lifecycle management.

Inherits from BaseChatService. Uses _ui_call() for all UI dispatch.
"""
from __future__ import annotations

import asyncio
import os
import platform
import subprocess
import threading
import traceback
from typing import TYPE_CHECKING, Any, Optional

import kick

from globals import data_store
from servicios.base import BaseChatService
from servicios.shared.translator import MessageTranslator

if TYPE_CHECKING:
    from controller.chat_controller import ChatController


class ServicioKick(BaseChatService):
    """Kick chat service using kick.Client with bypass subprocess.

    Connects to Kick chatrooms, receives events via async handlers,
    and routes them through the standard pipeline.
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
        self.client: Optional[kick.Client] = None
        self.bypass_process: Optional[subprocess.Popen] = None
        self.client_task: Any = None
        self.translator: Optional[MessageTranslator] = None

    def start(self) -> None:
        """Start the Kick chat service.

        Sets _running=True and spawns a daemon thread that runs the asyncio event loop.
        """
        self._running = True
        self._thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self._thread.start()

    def _run_bypass_and_wait(self) -> bool:
        """Run the bypass executable and wait for it to signal readiness."""
        from setup import reader

        dir_current_script = os.path.dirname(os.path.abspath(__file__))
        arch = "64" if platform.architecture()[0][:2] == "64" else "32"
        path_to_arch_dir = os.path.join(os.getcwd(), arch)
        bypass_executable = os.path.join(path_to_arch_dir, f"bypass{arch}.exe")

        if not os.path.exists(bypass_executable):
            print(f"Error: Bypass executable not found at '{bypass_executable}'.")
            self._ui_call(reader.leer_sapi, _("error_bypass_no_encontrado"))
            return False

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            self.bypass_process = subprocess.Popen(
                [bypass_executable],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creation_flags,
            )
        except Exception as e:
            print(f"Error starting bypass executable {bypass_executable}: {e}")
            return False

        for line in iter(self.bypass_process.stdout.readline, ''):
            if not self._running:
                return False
            if "starting" in line.lower():
                return True
        return False

    def _start_async_loop(self) -> None:
        """Worker thread entry: runs bypass, creates client, starts asyncio loop."""
        from setup import reader

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._ui_call(reader.leer_sapi, _("Cargando..."))

            if not self._run_bypass_and_wait():
                if self._running:
                    self._ui_call(reader.leer_sapi, _("error_iniciar_bypass"))
                self.stop()
                return

            self.client = kick.Client()
            self._add_listeners()

            self.client_task = self._loop.create_task(self.client.start())
            self._loop.run_forever()
        except Exception as e:
            if self._running:
                print(f"Fatal error in Kick connection thread: {e}")
                self.notify_error(str(e))
        finally:
            if self._loop and self._loop.is_running():
                self._loop.close()
            print("Kick thread finalized.")

    def _add_listeners(self) -> None:
        """Register event listeners on the kick.Client."""
        from servicios.kick import handlers

        self.client.event(lambda: handlers.on_ready(self))
        self.client.event(lambda msg: handlers.on_message(self, msg))
        self.client.event(lambda user: handlers.on_follow(self, user))

    def stop(self) -> None:
        """Stop the Kick chat service. Idempotent."""
        if not self._running:
            return

        self._running = False
        print("Stopping Kick service...")

        if self.media_controller:
            self.media_controller.release()
            self.media_controller = None

        if self._loop and self._loop.is_running():
            if self.client:
                asyncio.run_coroutine_threadsafe(self.client.close(), self._loop)
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self.bypass_process:
            try:
                print("Terminating bypass process...")
                self.bypass_process.terminate()
                self.bypass_process.wait()
                print("Bypass process terminated.")
            except Exception as e:
                print(f"Error terminating bypass process: {e}")
            self.bypass_process = None

        print("Kick service stopped completely.")

    def receive(self) -> None:
        """Not used for Kick — events are handled via async listeners."""
        pass
