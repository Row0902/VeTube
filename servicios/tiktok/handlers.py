"""TikTok service handlers — event processing and routing dispatch.

Pure message processing logic. No wx imports, no direct UI calls.
The service instance is passed as the first argument for access to
translator, router, and _ui_call.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from globals import data_store
from globals.resources import rutasonidos
from servicios.message_router import RoutableMessage
from servicios.shared.currency import CurrencyConverter
from setup import player, reader

if TYPE_CHECKING:
    from servicios.tiktok.client import ServicioTiktok


async def on_connect(service: ServicioTiktok, event) -> None:
    """Handle ConnectEvent: entry sound and player preparation."""
    service.last_live_status = True
    service._ui_call(reader.leer_sapi, _("Ingresando al chat"))

    if not service.media_controller:
        threading.Thread(target=service.prepare_player, daemon=True).start()

    if data_store.config['sonidos'] and data_store.config['listasonidos'][6]:
        service._ui_call(player.play, rutasonidos[6])


async def on_comment(service: ServicioTiktok, event) -> None:
    """Handle CommentEvent: route general message with optional translation."""
    if not (data_store.config['eventos'][0] and hasattr(service.chat_controller.ui, 'list_box_general')):
        return

    service._ui_call(service.estadisticas_manager.agregar_mensaje, event.user.nickname)

    text = event.comment if event.comment is not None else ''
    if data_store.dst and service.translator is not None:
        text = service.translator.translate(text)

    msg = RoutableMessage(
        text=text,
        author=event.user.nickname,
        category="general",
        platform="tiktok",
    )
    service.router.route(msg)


async def on_emote(service: ServicioTiktok, event) -> None:
    """Handle EmoteChatEvent: route member message."""
    if not (data_store.config['eventos'][1] and hasattr(service.chat_controller.ui, 'list_box_miembros')):
        return

    service._ui_call(service.estadisticas_manager.agregar_mensaje, event.user.nickname)

    text = event.user.nickname + _(" envió un emogi.")
    msg = RoutableMessage(
        text=text,
        author="",
        category="member",
        platform="tiktok",
    )
    service.router.route(msg)


async def on_chest(service: ServicioTiktok, event) -> None:
    """Handle EnvelopeEvent: route chest event."""
    if not (data_store.config['eventos'][9] and hasattr(service.chat_controller.ui, 'list_box_eventos')):
        return

    text = event.user.nickname + _(" ha enviado un cofre!")
    msg = RoutableMessage(
        text=text,
        author="",
        category="event",
        event_type="chest",
        platform="tiktok",
        eventos_index=9,
        sound_index=12,
    )
    service.router.route(msg)


async def on_follow(service: ServicioTiktok, event) -> None:
    """Handle FollowEvent: route follow event."""
    if not (data_store.config['eventos'][7] and hasattr(service.chat_controller.ui, 'list_box_eventos')):
        return

    service._ui_call(service.estadisticas_manager.agregar_seguidor)

    text = event.user.nickname + _(" comenzó a seguirte!")
    msg = RoutableMessage(
        text=text,
        author="",
        category="event",
        event_type="follow",
        platform="tiktok",
        eventos_index=7,
        sound_index=10,
    )
    service.router.route(msg)


async def on_gift(service: ServicioTiktok, event) -> None:
    """Handle GiftEvent: route donation with currency conversion."""
    if not (data_store.config['eventos'][3] and hasattr(service.chat_controller.ui, 'list_box_donaciones')):
        return

    text = ""
    diamond_value = event.gift.diamond_count * event.repeat_count

    # Check if streak is complete (streakable and not currently streaking)
    if event.gift.streakable and not event.streaking:
        text = _format_gift_message(service, event, diamond_value)
    elif not event.gift.streakable:
        text = _format_gift_message(service, event, diamond_value)

    if text:
        msg = RoutableMessage(
            text=text,
            author="",
            category="donation",
            platform="tiktok",
        )
        service.router.route(msg)


def _format_gift_message(service: ServicioTiktok, event, diamond_value: int) -> str:
    """Format the gift donation message with optional currency conversion."""
    if data_store.divisa != "Por defecto":
        amount_cents = diamond_value  # diamonds are treated as cents for conversion
        converted, currency_code = CurrencyConverter.convert(amount_cents, "USD", data_store.divisa)

        if converted is not None:
            return _('%s ha enviado %s %s (%s %s)') % (
                event.user.nickname,
                str(event.repeat_count),
                event.gift.name,
                str(converted),
                data_store.divisa,
            )
        else:
            # Conversion failed, fall back to diamonds
            return _('%s ha enviado %s %s (%s diamante)') % (
                event.user.nickname,
                str(event.repeat_count),
                event.gift.name,
                str(event.gift.diamond_count),
            )
    else:
        return _('%s ha enviado %s %s (%s diamante)') % (
            event.user.nickname,
            str(event.repeat_count),
            event.gift.name,
            str(event.gift.diamond_count),
        )


async def on_join(service: ServicioTiktok, event) -> None:
    """Handle JoinEvent: route join event."""
    if not (data_store.config['eventos'][2] and hasattr(service.chat_controller.ui, 'list_box_eventos')):
        return

    service._ui_call(service.estadisticas_manager.agregar_unido)

    text = event.user.nickname + _(" se ha unido a tu en vivo.")
    msg = RoutableMessage(
        text=text,
        author="",
        category="event",
        event_type="join",
        platform="tiktok",
        eventos_index=2,
        sound_index=2,
    )
    service.router.route(msg)


async def on_like(service: ServicioTiktok, event) -> None:
    """Handle LikeEvent: route like event."""
    if not (data_store.config['eventos'][6] and hasattr(service.chat_controller.ui, 'list_box_eventos')):
        return

    service._ui_call(service.estadisticas_manager.actualizar_megusta, event.total)

    text = event.user.nickname + _(" le ha dado me gusta a tu en vivo.")
    msg = RoutableMessage(
        text=text,
        author="",
        category="event",
        event_type="like",
        platform="tiktok",
        eventos_index=6,
        sound_index=9,
    )
    service.router.route(msg)


async def on_share(service: ServicioTiktok, event) -> None:
    """Handle ShareEvent: route share event."""
    if not (data_store.config['eventos'][8] and hasattr(service.chat_controller.ui, 'list_box_eventos')):
        return

    service._ui_call(service.estadisticas_manager.agregar_compartida)

    text = event.user.nickname + _(" ha compartido tu en vivo!")
    msg = RoutableMessage(
        text=text,
        author="",
        category="event",
        event_type="share",
        platform="tiktok",
        eventos_index=8,
        sound_index=11,
    )
    service.router.route(msg)


async def on_view(service: ServicioTiktok, event) -> None:
    """Handle RoomUserSeqEvent: update viewer count in title."""
    title = service.chat.unique_id + _(' en vivo, actualmente ') + str(event.m_total) + _(' viendo ahora')
    service._ui_call(service.chat_controller.agregar_titulo, title)
    service._ui_call(
        service.chat_controller.chat_dialog.update_chat_page_title,
        service.chat_controller,
        title,
    )


async def on_disconnect(service: ServicioTiktok, event) -> None:
    """Handle DisconnectEvent: stop the service."""
    if service._running:
        service._running = False
        service._ui_call(reader.leer_sapi, _("Se ha perdido la conexión. El servicio se ha detenido."))


async def finalizado(service: ServicioTiktok, event) -> None:
    """Handle LiveEndEvent: update live status."""
    service.last_live_status = False
    service._ui_call(reader.leer_sapi, _("El directo ha finalizado. Se buscará de nuevo en un minuto."))
