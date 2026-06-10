"""Tests for servicios.kick.handlers — event handler dispatch."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from servicios.kick.client import ServicioKick
from servicios.message_router import RoutableMessage


@pytest.fixture
def kick_service(fake_chat_controller):
    """Create a ServicioKick with mocked dependencies."""
    svc = ServicioKick(
        main_controller=MagicMock(),
        url="testchannel",
        frame=MagicMock(),
        plataforma="kick",
        chat_controller=fake_chat_controller,
    )
    svc._running = True
    svc.client = MagicMock()
    return svc


class TestOnMessage:
    """on_message handler: badge-based routing with priority."""

    @pytest.mark.asyncio
    async def test_general_message_routes_general(self, kick_service):
        """Message with no badges routes to general."""
        message = SimpleNamespace(
            author=SimpleNamespace(
                username="alice",
                badges=[],
            ),
            content="hello",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True] + [False] * 9,
                "categorias": [True] + [False] * 5,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_message
                await on_message(kick_service, message)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert isinstance(msg, RoutableMessage)
                assert msg.category == "general"
                assert msg.author == "alice"

    @pytest.mark.asyncio
    async def test_moderator_message_routes_moderator(self, kick_service):
        """Message with moderator badge routes to moderator."""
        message = SimpleNamespace(
            author=SimpleNamespace(
                username="mod_bob",
                badges=[{"type": "moderator"}],
            ),
            content="mod message",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 4 + [True] + [False] * 5,
                "categorias": [False] * 4 + [True] + [False],
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_message
                await on_message(kick_service, message)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "moderator"

    @pytest.mark.asyncio
    async def test_subscriber_message_routes_member(self, kick_service):
        """Message with subscriber badge routes to member."""
        message = SimpleNamespace(
            author=SimpleNamespace(
                username="sub_carol",
                badges=[{"type": "subscriber"}],
            ),
            content="sub message",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False, True] + [False] * 8,
                "categorias": [False, False, True] + [False] * 3,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_message
                await on_message(kick_service, message)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "member"

    @pytest.mark.asyncio
    async def test_verified_message_routes_verified(self, kick_service):
        """Message with verified badge routes to verified."""
        message = SimpleNamespace(
            author=SimpleNamespace(
                username="verified_dave",
                badges=[{"type": "verified"}],
            ),
            content="verified message",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 5 + [True] + [False] * 4,
                "categorias": [False] * 5 + [True],
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_message
                await on_message(kick_service, message)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "verified"

    @pytest.mark.asyncio
    async def test_moderator_priority_over_subscriber(self, kick_service):
        """Moderator badge takes priority over subscriber."""
        message = SimpleNamespace(
            author=SimpleNamespace(
                username="mod_sub",
                badges=[{"type": "moderator"}, {"type": "subscriber"}],
            ),
            content="priority test",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True, True, False, False, True] + [False] * 5,
                "categorias": [True, False, True, False, True] + [False],
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_message
                await on_message(kick_service, message)
                msg = mock_route.call_args[0][0]
                assert msg.category == "moderator"

    @pytest.mark.asyncio
    async def test_message_tracks_stats(self, kick_service):
        """on_message tracks message stats."""
        message = SimpleNamespace(
            author=SimpleNamespace(
                username="eve",
                badges=[],
            ),
            content="test",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True] + [False] * 9,
                "categorias": [True] + [False] * 5,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route"):
                with patch.object(kick_service.estadisticas_manager, "agregar_mensaje") as mock_stats:
                    from servicios.kick.handlers import on_message
                    await on_message(kick_service, message)
                    mock_stats.assert_called_once_with("eve")

    @pytest.mark.asyncio
    async def test_message_translates_when_configured(self, kick_service):
        """on_message translates content when translator is configured."""
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "hola"
        kick_service.translator = mock_translator

        message = SimpleNamespace(
            author=SimpleNamespace(
                username="frank",
                badges=[],
            ),
            content="hello",
        )
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [True] + [False] * 9,
                "categorias": [True] + [False] * 5,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = "es"
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_message
                await on_message(kick_service, message)
                msg = mock_route.call_args[0][0]
                assert msg.text == "hola"


class TestOnFollow:
    """on_follow handler: follower event routing."""

    @pytest.mark.asyncio
    async def test_follow_routes_event(self, kick_service):
        user = SimpleNamespace(username="grace")
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 7 + [True] + [False] * 2,
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route") as mock_route:
                from servicios.kick.handlers import on_follow
                await on_follow(kick_service, user)
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "event"
                assert msg.event_type == "follow"

    @pytest.mark.asyncio
    async def test_follow_tracks_stats(self, kick_service):
        user = SimpleNamespace(username="heidi")
        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "eventos": [False] * 7 + [True] + [False] * 2,
                "categorias": [False] + [True] + [False] * 4,
                "sonidos": False,
                "listasonidos": [False] * 13,
                "reader": False,
                "unread": [False] * 10,
            }
            mock_ds.dst = ""
            with patch.object(kick_service.router, "route"):
                with patch.object(kick_service.estadisticas_manager, "agregar_seguidor") as mock_stats:
                    from servicios.kick.handlers import on_follow
                    await on_follow(kick_service, user)
                    mock_stats.assert_called_once()


class TestOnReady:
    """on_ready handler: entry sound and title update."""

    @pytest.mark.asyncio
    async def test_ready_calls_ui_for_title(self, kick_service):
        """on_ready updates title via _ui_call."""
        mock_user = SimpleNamespace(
            chatroom=SimpleNamespace(
                streamer=SimpleNamespace(
                    livestream=SimpleNamespace(title="Test Stream"),
                ),
                connect=AsyncMock(),
            ),
        )
        kick_service.client.fetch_user = AsyncMock(return_value=mock_user)

        with patch("servicios.kick.handlers.data_store") as mock_ds:
            mock_ds.config = {
                "sonidos": False,
                "listasonidos": [False] * 13,
            }
            mock_ds.dst = ""
            with patch.object(kick_service, "_ui_call") as mock_ui:
                with patch("utils.play_mp4.extract_stream_url", return_value=None):
                    from servicios.kick.handlers import on_ready
                    await on_ready(kick_service)
                    # Should have called _ui_call for title update
                    assert mock_ui.called
