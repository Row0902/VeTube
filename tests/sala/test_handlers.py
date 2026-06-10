"""Tests for servicios.sala.handlers — message dispatch and routing."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from servicios.sala.client import ServicioSala
from servicios.message_router import RoutableMessage


@pytest.fixture
def sala_service(fake_chat_controller):
    """Create a ServicioSala with mocked PlayroomHelper."""
    svc = ServicioSala(
        main_controller=MagicMock(),
        url="sala",
        frame=MagicMock(),
        plataforma="sala",
        chat_controller=fake_chat_controller,
    )
    # Mock the chat helper
    svc.chat = MagicMock()
    svc.chat.new_messages = []
    svc._running = True
    return svc


class TestSalaReceivePublicMessage:
    """Public messages route as category='general'."""

    def test_public_message_routes_general(self, sala_service):
        sala_service.chat.new_messages = [
            {"type": "public", "message": "hello", "author": "alice"},
        ]
        with patch.object(sala_service.router, "route") as mock_route:
            with patch.object(sala_service.estadisticas_manager, "agregar_mensaje"):
                sala_service.receive()
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert isinstance(msg, RoutableMessage)
                assert msg.category == "general"
                assert msg.author == "alice"
                assert msg.platform == "sala"

    def test_public_message_tracks_stats(self, sala_service):
        sala_service.chat.new_messages = [
            {"type": "public", "message": "hello", "author": "bob"},
        ]
        with patch.object(sala_service.router, "route"):
            with patch.object(sala_service.estadisticas_manager, "agregar_mensaje") as mock_stats:
                sala_service.receive()
                mock_stats.assert_called_once_with("bob")


class TestSalaReceivePrivateMessage:
    """Private messages route as category='member' with sound_index=2."""

    def test_private_message_routes_member(self, sala_service):
        sala_service.chat.new_messages = [
            {"type": "private", "message": "secret", "author": "carol"},
        ]
        with patch.object(sala_service.router, "route") as mock_route:
            with patch.object(sala_service.estadisticas_manager, "agregar_mensaje"):
                sala_service.receive()
                mock_route.assert_called_once()
                msg = mock_route.call_args[0][0]
                assert msg.category == "member"
                assert msg.sound_index == 2
                assert msg.author == "carol"


class TestSalaReceiveNoneMessage:
    """None message text is treated as empty string."""

    def test_none_message_becomes_empty(self, sala_service):
        sala_service.chat.new_messages = [
            {"type": "public", "message": None, "author": "dave"},
        ]
        with patch.object(sala_service.router, "route") as mock_route:
            with patch.object(sala_service.estadisticas_manager, "agregar_mensaje"):
                sala_service.receive()
                msg = mock_route.call_args[0][0]
                assert msg.text == ""


class TestSalaReceiveMultipleMessages:
    """Multiple messages are all routed."""

    def test_multiple_messages_all_routed(self, sala_service):
        sala_service.chat.new_messages = [
            {"type": "public", "message": "one", "author": "a"},
            {"type": "private", "message": "two", "author": "b"},
            {"type": "public", "message": "three", "author": "c"},
        ]
        with patch.object(sala_service.router, "route") as mock_route:
            with patch.object(sala_service.estadisticas_manager, "agregar_mensaje"):
                sala_service.receive()
                assert mock_route.call_count == 3


class TestSalaReceiveStopsOnFlag:
    """receive() breaks out of loop when _running becomes False."""

    def test_stop_during_receive(self, sala_service):
        sala_service.chat.new_messages = [
            {"type": "public", "message": "one", "author": "a"},
            {"type": "public", "message": "two", "author": "b"},
        ]
        with patch.object(sala_service.router, "route") as mock_route:
            with patch.object(sala_service.estadisticas_manager, "agregar_mensaje"):
                # Stop after first message
                def stop_after_first(msg):
                    sala_service._running = False

                mock_route.side_effect = stop_after_first
                sala_service.receive()
                # Only first message should be routed
                assert mock_route.call_count == 1


class TestSalaReceiveErrorHandling:
    """receive() reports errors and does not crash."""

    def test_error_in_receive_reports_and_continues(self, sala_service):
        sala_service.chat.get_new_messages = MagicMock(side_effect=Exception("boom"))
        with patch.object(sala_service, "notify_error") as mock_err:
            sala_service.receive()
            mock_err.assert_called_once()


class TestSalaReceiveTranslation:
    """When translator is configured, messages are translated."""

    def test_translated_message(self, sala_service):
        mock_translator = MagicMock()
        mock_translator.translate.return_value = "translated text"
        sala_service.translator = mock_translator

        sala_service.chat.new_messages = [
            {"type": "public", "message": "texto original", "author": "x"},
        ]
        with patch("servicios.sala.handlers.data_store") as mock_ds:
            mock_ds.dst = "en"
            with patch.object(sala_service.router, "route") as mock_route:
                with patch.object(sala_service.estadisticas_manager, "agregar_mensaje"):
                    sala_service.receive()
                    msg = mock_route.call_args[0][0]
                    assert msg.text == "translated text"
