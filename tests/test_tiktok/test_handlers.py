"""Tests for servicios.tiktok.handlers — event handler dispatch."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from servicios.tiktok.client import ServicioTiktok
from servicios.message_router import RoutableMessage


@pytest.fixture
def tiktok_service(fake_chat_controller):
    """Create a ServicioTiktok with mocked dependencies."""
    svc = ServicioTiktok(
        main_controller=MagicMock(),
        url="https://tiktok.com/@testuser",
        frame=MagicMock(),
        plataforma="tiktok",
        chat_controller=fake_chat_controller,
    )
    svc._running = True
    svc.chat = MagicMock()
    svc.chat.unique_id = "testuser"
    return svc


class TestOnComment:
    """on_comment handler: routes general messages with translation."""

    @pytest.mark.asyncio
    async def test_comment_routes_general(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="alice"),
            comment="hello world",
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True] + [False] * 9,
                "categorias": [True] + [False] * 5,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_comment
                await on_comment(tiktok_service, event)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert isinstance(msg, RoutableMessage)
                assert msg.category == "general"
                assert msg.author == "alice"
                assert msg.text == "hello world"

    @pytest.mark.asyncio
    async def test_comment_tracks_stats(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="bob"),
            comment="test",
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True] + [False] * 9,
                "categorias": [True] + [False] * 5,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route"):
                with patch.object(tiktok_service.estadisticas_manager, "agregar_mensaje") as mock_stats:
                    from servicios.tiktok.handlers import on_comment
                    await on_comment(tiktok_service, event)
                    mock_stats.assert_called_once_with("bob")

    @pytest.mark.asyncio
    async def test_comment_translates_when_configured(self, tiktok_service):
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "hola mundo"
        tiktok_service.translator = mock_translator

        event = SimpleNamespace(
            user=SimpleNamespace(nickname="carol"),
            comment="hello world",
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True] + [False] * 9,
                "categorias": [True] + [False] * 5,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = "es"
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_comment
                await on_comment(tiktok_service, event)
                msg = mock_route.call_args[0][0]
                assert msg.text == "hola mundo"


class TestOnGift:
    """on_gift handler: currency conversion and donation routing."""

    @pytest.mark.asyncio
    async def test_gift_routes_donation(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="dave"),
            gift=SimpleNamespace(
                name="Rose",
                diamond_count=100,
                streakable=True,
            ),
            repeat_count=5,
            streaking=False,
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False, False, False, True] + [False] * 6,
                "categorias": [False, False, False, True] + [False] * 2,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            mock_ds.divisa = "Por defecto"
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_gift
                await on_gift(tiktok_service, event)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "donation"
                assert "dave" in msg.text
                assert "Rose" in msg.text

    @pytest.mark.asyncio
    async def test_gift_converts_currency(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="eve"),
            gift=SimpleNamespace(
                name="Lion",
                diamond_count=10000,
                streakable=True,
            ),
            repeat_count=1,
            streaking=False,
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False, False, False, True] + [False] * 6,
                "categorias": [False, False, False, True] + [False] * 2,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            mock_ds.divisa = "USD"
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_gift
                await on_gift(tiktok_service, event)
                msg = mock_route.call_args[0][0]
                assert "USD" in msg.text or "100" in msg.text


class TestOnFollow:
    """on_follow handler: follower event routing."""

    @pytest.mark.asyncio
    async def test_follow_routes_event(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="frank"),
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 7 + [True] + [False] * 2,
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_follow
                await on_follow(tiktok_service, event)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "event"
                assert msg.event_type == "follow"

    @pytest.mark.asyncio
    async def test_follow_tracks_stats(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="grace"),
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 7 + [True] + [False] * 2,
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route"):
                with patch.object(tiktok_service.estadisticas_manager, "agregar_seguidor") as mock_stats:
                    from servicios.tiktok.handlers import on_follow
                    await on_follow(tiktok_service, event)
                    mock_stats.assert_called_once()


class TestOnJoin:
    """on_join handler: join event routing."""

    @pytest.mark.asyncio
    async def test_join_routes_event(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="heidi"),
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False, False, True] + [False] * 7,
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_join
                await on_join(tiktok_service, event)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "event"
                assert msg.event_type == "join"


class TestOnLike:
    """on_like handler: like event routing."""

    @pytest.mark.asyncio
    async def test_like_routes_event(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="ivan"),
            total=42,
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 6 + [True] + [False] * 3,
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_like
                await on_like(tiktok_service, event)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "event"
                assert msg.event_type == "like"


class TestOnShare:
    """on_share handler: share event routing."""

    @pytest.mark.asyncio
    async def test_share_routes_event(self, tiktok_service):
        event = SimpleNamespace(
            user=SimpleNamespace(nickname="judy"),
        )
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 8 + [True] + [False],
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service.router, "route") as mock_route:
                from servicios.tiktok.handlers import on_share
                await on_share(tiktok_service, event)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "event"
                assert msg.event_type == "share"


class TestOnView:
    """on_view handler: viewer count title update."""

    @pytest.mark.asyncio
    async def test_view_updates_title(self, tiktok_service):
        event = SimpleNamespace(m_total=150)
        with patch.object(tiktok_service, "_ui_call") as mock_ui:
            from servicios.tiktok.handlers import on_view
            await on_view(tiktok_service, event)
            # Should call _ui_call at least twice (agregar_titulo + update_chat_page_title)
            assert mock_ui.call_count >= 2
            # First call should be agregar_titulo
            first_call_args = mock_ui.call_args_list[0][0]
            assert first_call_args[0] == tiktok_service.chat_controller.agregar_titulo


class TestOnConnect:
    """on_connect handler: entry sound and player preparation."""

    @pytest.mark.asyncio
    async def test_connect_sets_live_status(self, tiktok_service):
        event = SimpleNamespace()
        with patch("servicios.tiktok.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "sonidos": False,
                "listasonidos": [False] * 13,
            }
            mock_ds.dst = ""
            with patch.object(tiktok_service, "_ui_call"):
                from servicios.tiktok.handlers import on_connect
                await on_connect(tiktok_service, event)
                assert tiktok_service.last_live_status is True


class TestOnDisconnect:
    """on_disconnect handler: stops service."""

    @pytest.mark.asyncio
    async def test_disconnect_stops_service(self, tiktok_service):
        event = SimpleNamespace()
        tiktok_service._running = True
        with patch.object(tiktok_service, "_ui_call"):
            from servicios.tiktok.handlers import on_disconnect
            await on_disconnect(tiktok_service, event)
            assert tiktok_service._running is False


class TestFinalizado:
    """finalizado handler (LiveEndEvent): updates live status."""

    @pytest.mark.asyncio
    async def test_finalizado_updates_live_status(self, tiktok_service):
        event = SimpleNamespace()
        with patch.object(tiktok_service, "_ui_call"):
            from servicios.tiktok.handlers import finalizado
            await finalizado(tiktok_service, event)
            assert tiktok_service.last_live_status is False
