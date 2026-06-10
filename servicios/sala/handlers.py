"""Sala service handlers — message processing and routing dispatch.

Pure message processing logic. No wx imports, no direct UI calls.
The service instance is passed as the first argument for access to
translator, router, and _ui_call.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from globals import data_store
from servicios.message_router import RoutableMessage

if TYPE_CHECKING:
    from servicios.sala.client import ServicioSala


def process_message(service: ServicioSala, message: dict) -> None:
    """Process a single Sala message: translate if needed, then route.

    Args:
        service: The ServicioSala instance (for translator, router, _ui_call).
        message: Dict with keys 'type', 'message', 'author'.
    """
    # Normalize None message text to empty string
    if message["message"] is None:
        message["message"] = ""

    # Translate if translator is configured
    if data_store.dst and service.translator is not None:
        message["message"] = service.translator.translate(
            text=message["message"], target=data_store.dst
        )

    # Route based on message type using match/case
    match message["type"]:
        case "private":
            msg = RoutableMessage(
                text=message["message"],
                author=message["author"],
                category="member",
                platform="sala",
                sound_index=2,
            )
        case _:
            msg = RoutableMessage(
                text=message["message"],
                author=message["author"],
                category="general",
                platform="sala",
            )

    service.router.route(msg)
