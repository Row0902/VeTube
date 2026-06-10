"""Kick service handlers — event processing and routing dispatch.

Pure message processing logic. No wx imports, no direct UI calls.
The service instance is passed as the first argument for access to
translator, router, and _ui_call.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import kick

from globals import data_store
from globals.resources import rutasonidos
from servicios.message_router import RoutableMessage
from servicios.shared.badge_parser import BadgeParser
from setup import player, reader

if TYPE_CHECKING:
    from servicios.kick.client import ServicioKick


async def on_ready(service: ServicioKick) -> None:
    """Handle on_ready: entry sound, fetch user, connect chatroom, setup media."""
    from utils.play_mp4 import extract_stream_url
    from controller.media_controller import MediaController

    service._ui_call(reader.leer_sapi, _("Ingresando al chat"))

    if data_store.config['sonidos'] and data_store.config['listasonidos'][6]:
        service._ui_call(player.play, rutasonidos[6])

    if data_store.dst:
        service.translator = __import__(
            'servicios.shared.translator', fromlist=['MessageTranslator']
        ).MessageTranslator(data_store.dst)

    try:
        user = await service.client.fetch_user(service.url)
        title = user.chatroom.streamer.livestream.title
        service._ui_call(service.chat_controller.agregar_titulo, title)
        service._ui_call(
            service.chat_controller.chat_dialog.update_chat_page_title,
            service.chat_controller,
            title,
        )
        await user.chatroom.connect()

        kick_page_url = f"https://kick.com/{service.url}"
        video_url = extract_stream_url(kick_page_url)
        if video_url and not service.media_controller:
            service.media_controller = MediaController(
                url=video_url,
                state_callback=service.chat_controller.chat_dialog.on_media_player_state_change,
            )
            service.chat_controller.set_media_controller(service.media_controller)
    except Exception as e:
        print(f"Error connecting to Kick chatroom: {e}")
        service._ui_call(reader.leer_sapi, _("error_conectar_kick_chatroom"))
        service.stop()


async def on_message(service: ServicioKick, message: kick.Message) -> None:
    """Handle on_message: badge-based routing with priority."""
    service._ui_call(service.estadisticas_manager.agregar_mensaje, message.author.username)

    text = message.content
    if data_store.dst and service.translator is not None:
        text = service.translator.translate(text)

    # Parse role using BadgeParser
    role = BadgeParser.parse_role(message.author, "kick")

    full_message = f"{message.author.username}: {text}"

    # Route based on role using match/case
    match role:
        case "moderator":
            if data_store.config['eventos'][4] and data_store.config['categorias'][4]:
                msg = RoutableMessage(
                    text=text,
                    author=message.author.username,
                    category="moderator",
                    platform="kick",
                )
                service.router.route(msg)
                return

        case "subscriber":
            if data_store.config['eventos'][1] and data_store.config['categorias'][2]:
                msg = RoutableMessage(
                    text=text,
                    author=message.author.username,
                    category="member",
                    platform="kick",
                )
                service.router.route(msg)
                return

        case "verified":
            if data_store.config['eventos'][5] and data_store.config['categorias'][5]:
                msg = RoutableMessage(
                    text=text,
                    author=message.author.username,
                    category="verified",
                    platform="kick",
                )
                service.router.route(msg)
                return

    # Fallback: general
    if data_store.config['eventos'][0]:
        msg = RoutableMessage(
            text=text,
            author=message.author.username,
            category="general",
            platform="kick",
        )
        service.router.route(msg)


async def on_follow(service: ServicioKick, user: kick.User) -> None:
    """Handle on_follow: route follow event."""
    if not (data_store.config['eventos'][7] and hasattr(service.chat_controller.ui, 'list_box_eventos')):
        return

    service._ui_call(service.estadisticas_manager.agregar_seguidor)

    text = user.username + _(" comenzó a seguirte!")
    msg = RoutableMessage(
        text=text,
        author="",
        category="event",
        event_type="follow",
        platform="kick",
        eventos_index=7,
        sound_index=10,
    )
    service.router.route(msg)
