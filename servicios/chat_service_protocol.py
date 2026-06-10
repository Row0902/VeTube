from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from controller.chat_controller import ChatController
    from controller.media_controller import MediaController
    from servicios.estadisticas_manager import EstadisticasManager


@runtime_checkable
class ChatService(Protocol):
    """Structural protocol for all platform chat services.

    Every service (TikTok, Kick, YouTube, Twitch, Sala, YouTubeRealTime)
    must expose these attributes and methods so that controllers can
    interact with them uniformly.
    """

    url: str
    plataforma: str
    chat_controller: ChatController
    estadisticas_manager: EstadisticasManager
    media_controller: Optional[MediaController]

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def receive(self) -> None: ...

    # Optional methods — not all services implement these
    def is_live(self) -> bool: ...
    def send_message(self, text: str) -> None: ...
