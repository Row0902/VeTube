"""Tests for servicios.kick.client — ServicioKick lifecycle."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from servicios.kick.client import ServicioKick
from servicios.base import BaseChatService


class TestServicioKickInheritance:
    """ServicioKick must inherit from BaseChatService."""

    def test_inherits_base_chat_service(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        assert isinstance(svc, BaseChatService)


class TestServicioKickStart:
    """start() sets _running=True and spawns worker thread."""

    def test_start_sets_running(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        with patch("servicios.kick.client.threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            svc.start()
            assert svc._running is True

    def test_start_spawns_daemon_thread(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        with patch("servicios.kick.client.threading.Thread") as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            svc.start()
            mock_thread.assert_called_once()
            call_kwargs = mock_thread.call_args[1]
            assert call_kwargs["daemon"] is True
            mock_thread_instance.start.assert_called_once()


class TestServicioKickStop:
    """stop() sets _running=False, releases resources, idempotent."""

    def test_stop_sets_running_false(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        svc._running = True
        svc.stop()
        assert svc._running is False

    def test_stop_releases_media_controller(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        svc._running = True
        mock_media = MagicMock()
        svc.media_controller = mock_media
        svc.stop()
        mock_media.release.assert_called_once()

    def test_stop_terminates_bypass_process(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        svc._running = True
        mock_bypass = MagicMock()
        svc.bypass_process = mock_bypass
        svc.stop()
        mock_bypass.terminate.assert_called_once()
        mock_bypass.wait.assert_called_once()

    def test_stop_idempotent(self, fake_chat_controller):
        svc = ServicioKick(
            main_controller=MagicMock(),
            url="testchannel",
            frame=MagicMock(),
            plataforma="kick",
            chat_controller=fake_chat_controller,
        )
        svc.stop()
        svc.stop()
        assert svc._running is False


class TestServicioKickNoDirectWxCallAfter:
    """Verify no direct wx.CallAfter in the kick package."""

    def test_client_module_no_wx_callafter(self):
        """client.py should not contain wx.CallAfter."""
        import inspect
        from servicios.kick import client
        source = inspect.getsource(client)
        assert "wx.CallAfter" not in source, "client.py must use _ui_call(), not wx.CallAfter"

    def test_handlers_module_no_wx_callafter(self):
        """handlers.py should not contain wx.CallAfter."""
        import inspect
        from servicios.kick import handlers
        source = inspect.getsource(handlers)
        assert "wx.CallAfter" not in source, "handlers.py must use _ui_call(), not wx.CallAfter"
