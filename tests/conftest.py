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

# Mock wx module for test environment (always mock, even if wxPython is installed)
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
_res_mock = MagicMock()
_res_mock.rutasonidos = [f"sounds/test/sound{i}.mp3" for i in range(13)]
_res_mock.idiomas_disponibles = ["", "english", "spanish"]
_res_mock.monedas = ["Por defecto", "USD"]
_res_mock.lista_voces = ["voice1"]
sys.modules["globals.resources"] = _res_mock

# Mock utils.translator (googletrans dependency)
_trans_mod = MagicMock()
_trans_mod.TranslatorWrapper = MagicMock
sys.modules["utils.translator"] = _trans_mod

# Mock TikTokLive for test environment (pytest import machinery conflicts with real package)
_tiktok_mock = MagicMock()
_tiktok_mock.client = MagicMock()
_tiktok_mock.client.client = MagicMock()
_tiktok_mock.client.client.TikTokLiveClient = MagicMock
_tiktok_mock.types = MagicMock()
_tiktok_mock.types.events = MagicMock()
_tiktok_mock.types.events.CommentEvent = MagicMock
_tiktok_mock.types.events.ConnectEvent = MagicMock
_tiktok_mock.types.events.DisconnectEvent = MagicMock
_tiktok_mock.types.events.EmoteEvent = MagicMock
_tiktok_mock.types.events.EnvelopeEvent = MagicMock
_tiktok_mock.types.events.FollowEvent = MagicMock
_tiktok_mock.types.events.GiftEvent = MagicMock
_tiktok_mock.types.events.JoinEvent = MagicMock
_tiktok_mock.types.events.LikeEvent = MagicMock
_tiktok_mock.types.events.LiveEndEvent = MagicMock
_tiktok_mock.types.events.ShareEvent = MagicMock
_tiktok_mock.types.events.ViewerUpdateEvent = MagicMock
sys.modules["TikTokLive"] = _tiktok_mock
sys.modules["TikTokLive.client"] = _tiktok_mock.client
sys.modules["TikTokLive.client.client"] = _tiktok_mock.client.client
sys.modules["TikTokLive.types"] = _tiktok_mock.types
sys.modules["TikTokLive.types.events"] = _tiktok_mock.types.events

# Mock globals.data_store for test environment
_data_store_mock = MagicMock()
_data_store_mock.config = {}
_data_store_mock.dst = ""
_data_store_mock.divisa = "Por defecto"
sys.modules["globals.data_store"] = _data_store_mock

# Mock TikTokLive module (not installed in test environment)
_tiktok_mock = MagicMock()
_tiktok_mock.client = MagicMock()
_tiktok_mock.client.client = MagicMock()
_tiktok_mock.client.client.TikTokLiveClient = MagicMock
sys.modules["TikTokLive"] = _tiktok_mock
sys.modules["TikTokLive.client"] = _tiktok_mock.client
sys.modules["TikTokLive.client.client"] = _tiktok_mock.client.client
sys.modules["TikTokLive.events"] = MagicMock()

# Mock kick module (not installed in test environment)
# Use a proper mock module that doesn't interfere with pytest collection
_kick_mock = MagicMock()
_kick_mock.__path__ = []  # Make it look like a package
_kick_mock.Client = MagicMock
_kick_mock.Message = MagicMock
_kick_mock.User = MagicMock
sys.modules["kick"] = _kick_mock

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
    # Add ui attribute with list boxes for handler tests
    cc.ui = SimpleNamespace()
    cc.ui.list_box_general = MagicMock()
    cc.ui.list_box_miembros = MagicMock()
    cc.ui.list_box_moderadores = MagicMock()
    cc.ui.list_box_verificados = MagicMock()
    cc.ui.list_box_donaciones = MagicMock()
    cc.ui.list_box_eventos = MagicMock()
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
