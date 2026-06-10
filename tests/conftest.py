import os
import sys
from unittest.mock import MagicMock

# Set test mode BEFORE any application imports
os.environ["VETUBE_TEST_MODE"] = "1"

# Install gettext _() as builtin for test mode (normally done by languageHandler)
import builtins
if not hasattr(builtins, "_") or not callable(getattr(builtins, "_", None)):
    builtins._ = lambda s: s

# Ensure project root is on sys.path so tests can import application modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock wx module for test environment (wxPython not installed in CI/test)
if "wx" not in sys.modules:
    _wx_mock = MagicMock()
    _wx_mock.CallAfter = MagicMock(side_effect=lambda fn, *a, **kw: fn(*a, **kw))
    _wx_mock.EVT_BUTTON = MagicMock()
    _wx_mock.EVT_TEXT = MagicMock()
    _wx_mock.EVT_CHECKBOX = MagicMock()
    _wx_mock.EVT_CHOICE = MagicMock()
    _wx_mock.EVT_CHAR_HOOK = MagicMock()
    _wx_mock.EVT_CLOSE = MagicMock()
    _wx_mock.ID_YES = 5103
    _wx_mock.ICON_ERROR = MagicMock()
    sys.modules["wx"] = _wx_mock

# Mock setup module attributes that are only defined outside test mode
import setup
if not hasattr(setup, "player"):
    setup.player = MagicMock()
if not hasattr(setup, "reader"):
    setup.reader = MagicMock()

# Mock globals.resources (heavy imports: TTS, googletrans, etc.)
if "globals.resources" not in sys.modules:
    _res_mock = MagicMock()
    _res_mock.rutasonidos = [f"sounds/test/sound{i}.mp3" for i in range(13)]
    _res_mock.idiomas_disponibles = ["", "english", "spanish"]
    _res_mock.monedas = ["Por defecto", "USD"]
    _res_mock.lista_voces = ["voice1"]
    sys.modules["globals.resources"] = _res_mock

# Mock utils.translator (googletrans dependency)
if "utils.translator" not in sys.modules:
    _trans_mod = MagicMock()
    _trans_mod.TranslatorWrapper = MagicMock
    sys.modules["utils.translator"] = _trans_mod

import pytest
from servicios.estadisticas_manager import EstadisticasManager


@pytest.fixture
def fake_chat_controller():
    """Minimal ChatController stub for service tests."""
    from types import SimpleNamespace
    cc = SimpleNamespace()
    cc.estadisticas_manager = EstadisticasManager()
    cc.notificar_error = MagicMock()
    cc.agregar_titulo = MagicMock()
    cc.agregar_mensaje_general = MagicMock()
    cc.agregar_mensaje_miembro = MagicMock()
    cc.agregar_mensaje_moderador = MagicMock()
    cc.agregar_mensaje_verificado = MagicMock()
    cc.agregar_mensaje_donacion = MagicMock()
    cc.agregar_mensaje_evento = MagicMock()
    cc.chat_dialog = MagicMock()
    return cc


@pytest.fixture
def recording_router(monkeypatch):
    """Fixture that records all messages routed through MessageRouter."""
    recorded = []

    class FakeRouter:
        def __init__(self, chat_controller):
            self.chat_controller = chat_controller

        def route(self, msg):
            recorded.append(msg)

    return FakeRouter, recorded


@pytest.fixture
def sample_stats():
    """Return a pre-populated EstadisticasManager for testing."""
    mgr = EstadisticasManager()
    mgr.agregar_mensaje("alice")
    mgr.agregar_mensaje("bob")
    mgr.agregar_seguidor()
    mgr.actualizar_megusta(1)
    mgr.agregar_unido()
    mgr.agregar_compartida()
    return mgr
