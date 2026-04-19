"""
Pytest configuration and fixtures for push-to-talk dictation tests.

Provides mocks and fixtures for:
- X11 Display and Window operations
- Audio device and recording
- Keyboard input
- Configuration management
- Test data and temporary files
"""

import pytest
import logging
import json
import yaml
from pathlib import Path
from unittest.mock import MagicMock
from typing import Dict, Any


# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# X11 and Display Fixtures
# ============================================================================

@pytest.fixture
def mock_display():
    """Mock Xlib Display object for testing X11 operations without a real display."""
    display = MagicMock()
    display.screen().root = MagicMock()
    display.screen().root.warp_pointer = MagicMock()
    display.sync = MagicMock()
    display.get_input_focus = MagicMock(return_value=(MagicMock(id=1), 0))
    return display


@pytest.fixture
def mock_window():
    """Mock Xlib Window object for testing window operations."""
    window = MagicMock()
    window.id = 12345
    window.get_wm_name = MagicMock(return_value="Test Window")
    window.get_geometry = MagicMock(return_value=MagicMock(
        x=100, y=100, width=800, height=600, border_width=0
    ))
    window.set_wm_name = MagicMock()
    window.change_attributes = MagicMock()
    window.get_full_property = MagicMock(return_value=MagicMock(value=[b"test"]))
    return window


@pytest.fixture
def mock_x11_injector(mock_display, mock_window):
    """Mock X11Injector for testing text injection without real X11."""
    injector = MagicMock()
    injector.display = mock_display
    injector.target_window = mock_window
    injector.delay_ms = 50
    
    injector.list_windows = MagicMock(return_value={
        1: "WezTerm",
        2: "Firefox",
        3: "Test Window"
    })
    
    injector.set_target_window = MagicMock(return_value=True)
    injector.focus_window = MagicMock(return_value=True)
    injector.inject_text = MagicMock(return_value=True)
    injector.inject_text_raw = MagicMock(return_value=True)
    
    return injector


# ============================================================================
# Audio and Recording Fixtures
# ============================================================================

@pytest.fixture
def mock_audio_device():
    """Mock audio device for testing audio operations."""
    device = {
        'name': 'Built-in Microphone',
        'index': 0,
        'kind': 'input',
        'hostapi': 0,
        'channels': 1,
        'samplerate': 16000.0,
    }
    return device


@pytest.fixture
def mock_audio_capture():
    """Mock AudioCapture for testing recording without real hardware."""
    capture = MagicMock()
    capture.sample_rate = 16000
    capture.channels = 1
    capture.device_index = 0
    capture.recording = False
    capture.audio_data = None
    
    capture.list_devices = MagicMock(return_value={
        0: "Built-in Microphone",
        1: "USB Headset",
    })
    
    capture.start_recording = MagicMock(return_value=True)
    capture.stop_recording = MagicMock(return_value=True)
    capture.get_audio_data = MagicMock(return_value=b"mock_audio_data")
    capture.record_until_silence = MagicMock(return_value=b"mock_audio_data")
    
    return capture


@pytest.fixture
def mock_transcriber():
    """Mock WhisperTranscriber for testing transcription without model download."""
    transcriber = MagicMock()
    transcriber.model_name = "base"
    transcriber.model = None
    transcriber.device = "cpu"
    
    transcriber.transcribe = MagicMock(return_value={
        'text': 'This is a test transcription',
        'language': 'en'
    })
    
    transcriber.load_model = MagicMock(return_value=True)
    transcriber.get_available_models = MagicMock(return_value=[
        'tiny', 'base', 'small', 'medium', 'large'
    ])
    
    return transcriber


# ============================================================================
# Keyboard and Input Fixtures
# ============================================================================

@pytest.fixture
def mock_keyboard():
    """Mock keyboard module for testing keyboard operations."""
    keyboard = MagicMock()
    keyboard.add_hotkey = MagicMock(return_value=None)
    keyboard.remove_hotkey = MagicMock(return_value=None)
    keyboard.write = MagicMock(return_value=None)
    keyboard.press = MagicMock(return_value=None)
    keyboard.release = MagicMock(return_value=None)
    keyboard.is_pressed = MagicMock(return_value=False)
    return keyboard


@pytest.fixture
def mock_input_listener(mock_keyboard):
    """Mock InputListener for testing keyboard/input detection."""
    listener = MagicMock()
    listener.hotkey = 'ctrl+m'
    listener.on_press = None
    listener.on_release = None
    listener.running = False
    listener.keyboard = mock_keyboard
    
    listener.start = MagicMock(return_value=True)
    listener.stop = MagicMock(return_value=True)
    listener.simulate_press = MagicMock(return_value=True)
    
    return listener


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config_dict() -> Dict[str, Any]:
    """Test configuration dictionary matching config.yaml structure."""
    return {
        'whisper_model': 'base',
        'audio': {
            'sample_rate': 16000,
            'chunk_size': 1024,
            'channels': 1,
            'device_index': None,
        },
        'injection': {
            'delay_ms': 50,
        },
        'window': {
            'persist_selection': True,
            'remember_by': 'WM_NAME',
        },
        'logging': {
            'level': 'INFO',
            'file': None,
        }
    }


@pytest.fixture
def temp_config_file(tmp_path, test_config_dict) -> Path:
    """Temporary config file for testing configuration loading."""
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(test_config_dict, f)
    return config_file


@pytest.fixture
def temp_window_selection(tmp_path) -> Path:
    """Temporary window selection file for testing persistence."""
    window_file = tmp_path / "selected_window.json"
    window_data = {
        'window_id': 12345,
        'window_name': 'Test Window',
        'timestamp': '2024-01-01T00:00:00'
    }
    with open(window_file, 'w') as f:
        json.dump(window_data, f)
    return window_file


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_audio_data() -> bytes:
    """Sample audio data for testing transcription and injection."""
    wav_header = b'RIFF' + b'\x00' * 4 + b'WAVE'
    fmt_chunk = b'fmt ' + b'\x10\x00\x00\x00'
    fmt_chunk += b'\x01\x00' + b'\x01\x00'
    fmt_chunk += b'\x80\x3e\x00\x00'
    fmt_chunk += b'\x00\x7e\x00\x02'
    fmt_chunk += b'\x10\x00'
    
    data_chunk = b'data' + b'\x00\x01\x00\x00'
    data_chunk += b'\x00' * 256
    
    return wav_header + fmt_chunk + data_chunk


@pytest.fixture
def sample_transcription_text() -> str:
    """Sample transcribed text for testing injection."""
    return "Hello, this is a test of the push to talk dictation system."


@pytest.fixture
def sample_window_list() -> Dict[int, str]:
    """Sample list of available windows for testing window selection."""
    return {
        1: "WezTerm",
        2: "Firefox - GitHub",
        3: "Text Editor",
        4: "File Manager",
        5: "Settings"
    }


# ============================================================================
# Virtual Environment Fixtures
# ============================================================================

@pytest.fixture
def venv_path(tmp_path) -> Path:
    """Temporary virtual environment path for testing."""
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "bin").mkdir()
    (venv_dir / "lib").mkdir()
    return venv_dir


@pytest.fixture
def mock_venv_bin(venv_path) -> Dict[str, Path]:
    """Mock virtual environment binaries."""
    binaries = {}
    for binary in ['python3', 'pip', 'python']:
        bin_path = venv_path / "bin" / binary
        bin_path.touch()
        bin_path.chmod(0o755)
        binaries[binary] = bin_path
    return binaries


# ============================================================================
# System Environment Fixtures
# ============================================================================

@pytest.fixture
def mock_display_env(monkeypatch):
    """Mock DISPLAY environment variable for X11 testing."""
    monkeypatch.setenv('DISPLAY', ':99')
    return ':99'


@pytest.fixture
def mock_home_dir(tmp_path, monkeypatch):
    """Mock home directory for testing config/data persistence."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv('HOME', str(home))
    
    (home / ".config").mkdir()
    (home / ".local" / "share").mkdir(parents=True)
    
    return home


# ============================================================================
# Integration Fixtures
# ============================================================================

@pytest.fixture
def mock_daemon(mock_audio_capture, mock_transcriber, mock_x11_injector, 
                mock_input_listener, test_config_dict):
    """Mock DictationDaemon with all components mocked."""
    daemon = MagicMock()
    daemon.config = test_config_dict
    daemon.audio_capture = mock_audio_capture
    daemon.transcriber = mock_transcriber
    daemon.x11_injector = mock_x11_injector
    daemon.mouse_listener = mock_input_listener
    daemon.recording = False
    daemon.target_window = None
    
    daemon.start = MagicMock(return_value=True)
    daemon.stop = MagicMock(return_value=True)
    daemon.on_trigger_press = MagicMock()
    daemon.on_trigger_release = MagicMock()
    daemon.process_recording = MagicMock(return_value="Transcribed text")
    
    return daemon


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def caplog_debug(caplog):
    """Capture logs at DEBUG level for detailed test diagnostics."""
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def test_logger() -> logging.Logger:
    """Logger instance for tests."""
    logger = logging.getLogger('test_module')
    logger.setLevel(logging.DEBUG)
    return logger


# ============================================================================
# Cleanup and Teardown
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_mocks():
    """Automatically cleanup mock objects after each test."""
    yield
    # Cleanup happens automatically with fixtures


# ============================================================================
# Pytest Hooks and Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "slow: slow tests")


@pytest.fixture(scope="session")
def disable_x11_warnings():
    """Disable X11 import warnings during test session."""
    import warnings
    warnings.filterwarnings("ignore", category=ImportWarning)
    warnings.filterwarnings("ignore", message=".*X11.*")
    return True
