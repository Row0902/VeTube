"""Tests for servicios.sala.client — ServicioSala lifecycle."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from servicios.sala.client import ServicioSala
from servicios.base import BaseChatService


class TestServicioSalaInheritance:
    """ServicioSala must inherit from BaseChatService."""

    def test_inherits_base_chat_service(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        assert isinstance(svc, BaseChatService)


class TestServicioSalaStart:
    """start() sets _running=True and spawns worker thread."""

    def test_start_sets_running(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        with patch("servicios.sala.client.PlayroomHelper"):
            with patch("servicios.sala.client.Timer") as mock_timer:
                mock_timer_instance = MagicMock()
                mock_timer.return_value = mock_timer_instance
                svc.start()
                assert svc._running is True

    def test_start_creates_playroom_helper(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        with patch("servicios.sala.client.PlayroomHelper") as mock_ph:
            with patch("servicios.sala.client.Timer"):
                svc.start()
                mock_ph.assert_called_once()

    def test_start_spawns_timer_thread(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        with patch("servicios.sala.client.PlayroomHelper"):
            with patch("servicios.sala.client.Timer") as mock_timer:
                mock_timer_instance = MagicMock()
                mock_timer.return_value = mock_timer_instance
                svc.start()
                mock_timer.assert_called_once_with(0.5, svc.receive)
                mock_timer_instance.start.assert_called_once()

    def test_start_reports_error_on_failure(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        with patch("servicios.sala.client.PlayroomHelper", side_effect=Exception("no playroom")):
            with patch("servicios.sala.client.wx") as mock_wx:
                svc.start()
                # notify_error should have been called
                assert fake_chat_controller.notificar_error.called or mock_wx.CallAfter.called


class TestServicioSalaStop:
    """stop() sets _running=False, idempotent."""

    def test_stop_sets_running_false(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        svc._running = True
        svc.stop()
        assert svc._running is False

    def test_stop_idempotent(self, fake_chat_controller):
        svc = ServicioSala(
            main_controller=MagicMock(),
            url="sala",
            frame=MagicMock(),
            plataforma="sala",
            chat_controller=fake_chat_controller,
        )
        svc.stop()
        svc.stop()
        assert svc._running is False
