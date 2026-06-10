"""Tests for servicios.base — BaseChatService ABC and _ui_call()"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

import pytest
import wx

from servicios.base import BaseChatService
from servicios.estadisticas_manager import EstadisticasManager


class ConcreteService(BaseChatService):
    """Minimal concrete implementation for testing the ABC."""

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def receive(self) -> None:
        pass


@pytest.fixture
def service(fake_chat_controller):
    return ConcreteService(
        main_controller=MagicMock(),
        url="test://url",
        frame=MagicMock(),
        plataforma="test",
        chat_controller=fake_chat_controller,
    )


class TestBaseChatServiceInit:
    """Constructor sets up shared state correctly."""

    def test_running_defaults_false(self, service):
        assert service._running is False

    def test_stores_chat_controller(self, service, fake_chat_controller):
        assert service.chat_controller is fake_chat_controller

    def test_stores_estadisticas_manager(self, service):
        assert isinstance(service.estadisticas_manager, EstadisticasManager)

    def test_stores_url_and_platform(self, service):
        assert service.url == "test://url"
        assert service.plataforma == "test"

    def test_creates_message_router(self, service):
        assert service.router is not None

    def test_media_controller_defaults_none(self, service):
        assert service.media_controller is None


class TestBaseChatServiceABC:
    """Abstract methods enforce contract."""

    def test_cannot_instantiate_abc(self, fake_chat_controller):
        with pytest.raises(TypeError):
            BaseChatService(
                main_controller=MagicMock(),
                url="test",
                frame=MagicMock(),
                plataforma="test",
                chat_controller=fake_chat_controller,
            )

    def test_concrete_subclass_works(self, service):
        assert isinstance(service, BaseChatService)


class TestUiCall:
    """_ui_call wraps wx.CallAfter with exception trapping."""

    def test_ui_call_invokes_wx_callafter(self, service):
        """_ui_call schedules callable via wx.CallAfter."""
        mock_callable = MagicMock()
        wx.CallAfter.reset_mock()
        service._ui_call(mock_callable, "arg1", kwarg1="val1")
        wx.CallAfter.assert_called_once()
        # The conftest mock executes immediately, so callable was called
        mock_callable.assert_called_once_with("arg1", kwarg1="val1")

    def test_ui_call_traps_exception(self, service):
        """Exception in callable is caught, not propagated."""
        def bad_callable():
            raise ValueError("UI exploded")

        wx.CallAfter.reset_mock()
        # Replace CallAfter with one that captures _safe without executing
        captured = []
        wx.CallAfter.side_effect = lambda fn: captured.append(fn)

        service._ui_call(bad_callable)
        assert len(captured) == 1
        # _safe should not raise even though bad_callable does
        captured[0]()  # Should not raise

        # Restore side_effect
        wx.CallAfter.side_effect = lambda fn, *a, **kw: fn(*a, **kw)

    def test_ui_call_traps_runtime_error(self, service):
        """RuntimeError from deleted wx object is caught."""
        def bad_callable():
            raise RuntimeError("wrapped C++ object has been deleted")

        captured = []
        wx.CallAfter.side_effect = lambda fn: captured.append(fn)

        service._ui_call(bad_callable)
        captured[0]()  # Should not raise

        wx.CallAfter.side_effect = lambda fn, *a, **kw: fn(*a, **kw)


class TestNotifyError:
    """notify_error dispatches to chat_controller via _ui_call."""

    def test_notify_error_calls_chat_controller(self, service, fake_chat_controller):
        wx.CallAfter.reset_mock()
        service.notify_error("something broke")
        wx.CallAfter.assert_called_once()
        # conftest mock executes immediately
        fake_chat_controller.notificar_error.assert_called_once_with("something broke")


class TestLifecycle:
    """Lifecycle methods work as expected."""

    def test_start_sets_running(self, service):
        assert service._running is False
        service.start()
        assert service._running is True

    def test_stop_clears_running(self, service):
        service.start()
        service.stop()
        assert service._running is False

    def test_double_stop_is_safe(self, service):
        service.stop()
        service.stop()  # Should not raise
        assert service._running is False
