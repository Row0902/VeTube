"""TikTok service client — TikTokLive connection and lifecycle management.

Inherits from BaseChatService. Uses _ui_call() for all UI dispatch.
"""
from __future__ import annotations

import asyncio
import threading
import traceback
from typing import TYPE_CHECKING, Any, Optional

from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.types.events import (
    CommentEvent,
    ConnectEvent,
    DisconnectEvent,
    EmoteEvent,
    EnvelopeEvent,
    FollowEvent,
    GiftEvent,
    JoinEvent,
    LikeEvent,
    LiveEndEvent,
    ShareEvent,
    ViewerUpdateEvent,
)

from globals import data_store
from servicios.base import BaseChatService
from servicios.shared.translator import MessageTranslator

if TYPE_CHECKING:
    from controller.chat_controller import ChatController


class ServicioTiktok(BaseChatService):
    """TikTok chat service using TikTokLive async client.

    Connects to TikTok live streams, receives events via async handlers,
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
        self.chat: Optional[TikTokLiveClient] = None
        self.last_live_status: Optional[bool] = None
        self.translator: Optional[MessageTranslator] = None

    def start(self) -> None:
        """Start the TikTok chat service.

        Sets _running=True and spawns a daemon thread that runs the asyncio event loop.
        """
        self._running = True
        self._thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self._thread.start()

    def _start_async_loop(self) -> None:
        """Worker thread entry: creates and runs the asyncio event loop."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.create_task(self._initialize_and_run_client())
            self._loop.run_forever()
        except Exception as e:
            print(f"Fatal error in TikTok connection thread: {e}")
            traceback.print_exc()
        finally:
            if self._loop and self._loop.is_running():
                pending = asyncio.all_tasks(loop=self._loop)
                for task in pending:
                    task.cancel()
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            if self._loop:
                self._loop.close()

    async def _initialize_and_run_client(self) -> None:
        """Initialize TikTokLiveClient and start the connection loop."""
        try:
            from utils import funciones
            user_id = funciones.extractUser(self.url)
            self.chat = TikTokLiveClient(unique_id=user_id)
            self._add_listeners()
            await self._run_client_async()
        except Exception as e:
            print(f"Error during TikTok client initialization: {e}")
            traceback.print_exc()
            self.notify_error(str(e))
            self.stop()

    async def _run_client_async(self) -> None:
        """Main loop: check live status and connect when live."""
        from setup import reader

        while self._running:
            try:
                room_info = await self.chat.retrieve_room_info()
                if room_info:
                    if self.last_live_status is not True:
                        self._ui_call(reader.leer_sapi, _("El usuario está en vivo. Conectando..."))
                    self.last_live_status = True
                    if data_store.dst:
                        self.translator = MessageTranslator(data_store.dst)
                    await self.chat.start()
                    break
                else:
                    if self.last_live_status is not False:
                        self._ui_call(reader.leer_sapi, _("El usuario no está en vivo. Reintentando en un minuto."))
                    self.last_live_status = False
                    if self._running:
                        await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:
                    print(f"Error in TikTok client loop: {e}.")
                    traceback.print_exc()
                    self.notify_error(str(e))
                    self.stop()

    def stop(self) -> None:
        """Stop the TikTok chat service. Idempotent."""
        if self.media_controller:
            self.media_controller.release()
            self.media_controller = None

        if self._running and self._loop and self._loop.is_running():
            self._running = False
            if self.chat:
                self.chat.stop()
            self._loop.call_soon_threadsafe(self._loop.stop)
        else:
            self._running = False

    def receive(self) -> None:
        """Not used for TikTok — events are handled via async listeners."""
        pass

    def prepare_player(self) -> None:
        """Initialize video playback for the TikTok stream."""
        try:
            from utils.play_mp4 import extract_stream_url
            video_url = extract_stream_url(self.url, format_preference='best')
            if video_url:
                from controller.media_controller import MediaController
                self.media_controller = MediaController(
                    url=video_url,
                    state_callback=self.chat_controller.chat_dialog.on_media_player_state_change,
                )
                self.chat_controller.set_media_controller(self.media_controller)
        except Exception as e:
            print(f"Error starting TikTok video playback: {e}")

    def _add_listeners(self) -> None:
        """Register event listeners on the TikTokLiveClient."""
        from servicios.tiktok import handlers

        self.chat.add_listener(ConnectEvent, lambda e: handlers.on_connect(self, e))

        if data_store.config['categorias'][0]:
            self.chat.add_listener(CommentEvent, lambda e: handlers.on_comment(self, e))

        self.chat.add_listener(LiveEndEvent, lambda e: handlers.finalizado(self, e))
        self.chat.add_listener(DisconnectEvent, lambda e: handlers.on_disconnect(self, e))

        if data_store.config['categorias'][2]:
            self.chat.add_listener(EmoteEvent, lambda e: handlers.on_emote(self, e))

        if data_store.config['categorias'][1]:
            self.chat.add_listener(EnvelopeEvent, lambda e: handlers.on_chest(self, e))
            self.chat.add_listener(FollowEvent, lambda e: handlers.on_follow(self, e))

        if data_store.config['categorias'][3]:
            self.chat.add_listener(GiftEvent, lambda e: handlers.on_gift(self, e))

        if data_store.config['categorias'][1]:
            self.chat.add_listener(JoinEvent, lambda e: handlers.on_join(self, e))
            self.chat.add_listener(LikeEvent, lambda e: handlers.on_like(self, e))
            self.chat.add_listener(ShareEvent, lambda e: handlers.on_share(self, e))

        self.chat.add_listener(ViewerUpdateEvent, lambda e: handlers.on_view(self, e))
