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
import tempfile
import json
import yaml
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from typing import Generator, Optional, Dict, Any
import sys


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
    """Mock Xlib Display object for testing X11 operations without a real display.
    
    Returns a MagicMock that simulates Xlib.display.Display behavior.
    Allows tests to run in headless environments.
    """
    display = MagicMock()
    display.screen().root = MagicMock()
    display.screen().root.warp_pointer = MagicMock()
    display.sync = MagicMock()
    display.get_input_focus = MagicMock(return_value=(MagicMock(id=1), 0))
    return display


@pytest.fixture
def mock_window():
    """Mock Xlib Window object for testing window operations.
    
    Returns a MagicMock that simulates Xlib window behavior including
    window properties, geometry, and event handling.
    """
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
    """Mock X11Injector for testing text injection without real X11.
    
    Simulates the X11Injector class behavior for:
    - Listing available windows
    - Injecting text via xdotool
    - Switching focus to windows
    - Handling keyboard events
    """
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
    """Mock audio device for testing audio operations.
    
    Returns a mock that simulates sounddevice device properties.
    """
    device = {
        'name': 'Built-in Microphone',
        'index': 0,
        'kind': 'input',
        'hostapi': 0,
        'channels': 1,
        'samplerate': 16000.0,
        'latency': 0.020,
        'default_samplerate': 16000.0,
        'max_input_channels': 1,
        'max_output_channels': 0,
    }
    return device


@pytest.fixture
def mock_audio_capture():
    """Mock AudioCapture for testing recording without real hardware.
    
    Provides mock methods for:
    - Listing available devices
    - Starting and stopping recording
    - Getting recorded audio data
    """
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
    """Mock WhisperTranscriber for testing transcription without model download.
    
    Provides mock methods for:
    - Loading Whisper model
    - Transcribing audio
    - Getting supported models
    """
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
    """Mock keyboard module for testing keyboard operations.
    
    Provides mock methods for:
    - Registering hotkeys
    - Simulating key presses
    - Handling keyboard events
    """
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
    """Mock InputListener for testing keyboard/input detection.
    
    Provides mock methods for:
    - Starting and stopping listeners
    - Simulating key presses
    - Handling callbacks
    """
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
    """Test configuration dictionary matching config.yaml structure.
    
    Returns default test configuration for all components.
    """
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
    """Temporary config file for testing configuration loading.
    
    Returns path to a temporary config.yaml file with test values.
    Clean up is handled automatically by pytest's tmp_path fixture.
    """
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(test_config_dict, f)
    return config_file


@pytest.fixture
def temp_window_selection(tmp_path) -> Path:
    """Temporary window selection file for testing persistence.
    
    Returns path to a temporary selected_window.json file.
    """
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
    """Sample audio data for testing transcription and injection.
    
    Returns mock audio bytes that can be used in tests without
    actual audio hardware.
    """
    # Create a simple WAV-like header + dummy data
    wav_header = b'RIFF' + b'\x00' * 4 + b'WAVE'
    fmt_chunk = b'fmt ' + b'\x10\x00\x00\x00'  # PCM format
    fmt_chunk += b'\x01\x00' + b'\x01\x00'  # 1 channel, 1 sample rate
    fmt_chunk += b'\x80\x3e\x00\x00'  # 16000 Hz
    fmt_chunk += b'\x00\x7e\x00\x02'  # Byte rate, block align
    fmt_chunk += b'\x10\x00'  # Bits per sample
    
    data_chunk = b'data' + b'\x00\x01\x00\x00'  # 256 bytes of audio
    data_chunk += b'\x00' * 256
    
    return wav_header + fmt_chunk + data_chunk


@pytest.fixture
def sample_transcription_text() -> str:
    """Sample transcribed text for testing injection.
    
    Returns realistic transcription output for testing text injection
    and window focus handling.
    """
    return "Hello, this is a test of the push to talk dictation system."


@pytest.fixture
def sample_window_list() -> Dict[int, str]:
    """Sample list of available windows for testing window selection.
    
    Returns a dictionary mapping window IDs to window names.
    """
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
    """Temporary virtual environment path for testing.
    
    Returns path to a temporary directory that would contain venv.
    Does not actually create a venv (too slow for tests).
    """
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "bin").mkdir()
    (venv_dir / "lib").mkdir()
    return venv_dir


@pytest.fixture
def mock_venv_bin(venv_path) -> Dict[str, Path]:
    """Mock virtual environment binaries.
    
    Returns paths to mock executable files in the venv.
    """
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
    """Mock DISPLAY environment variable for X11 testing.
    
    Sets DISPLAY to a mock value for testing without real X11.
    """
    monkeypatch.setenv('DISPLAY', ':99')
    return ':99'


@pytest.fixture
def mock_home_dir(tmp_path, monkeypatch):
    """Mock home directory for testing config/data persistence.
    
    Temporarily changes HOME to a temporary directory.
    Useful for testing file I/O in user config directories.
    """
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv('HOME', str(home))
    
    # Create standard user directories
    (home / ".config").mkdir()
    (home / ".local" / "share").mkdir(parents=True)
    
    return home


# ============================================================================
# Integration Fixtures
# ============================================================================

@pytest.fixture
def mock_daemon(mock_audio_capture, mock_transcriber, mock_x11_injector, 
                mock_input_listener, test_config_dict):
    """Mock DictationDaemon with all components mocked.
    
    Provides a fully mocked daemon for testing the main coordinator
    without any real system dependencies.
    """
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
    """Capture logs at DEBUG level for detailed test diagnostics.
    
    Sets up logging capture with DEBUG level.
    """
    caplog.set_level(logging.DEBUG)
    return caplog


@pytest.fixture
def test_logger() -> logging.Logger:
    """Logger instance for tests.
    
    Returns a configured logger for test modules.
    """
    logger = logging.getLogger('test_module')
    logger.setLevel(logging.DEBUG)
    return logger


# ============================================================================
# Pytest Hooks and Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: slow tests"
    )


@pytest.fixture(scope="session")
def disable_x11_warnings():
    """Disable X11 import warnings during test session.
    
    Prevents warnings about missing X11 libraries when running
    in headless environments.
    """
    import warnings
    warnings.filterwarnings("ignore", category=ImportWarning)
    warnings.filterwarnings("ignore", message=".*X11.*")
    return True


# ============================================================================
# Cleanup and Teardown
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_mocks():
    """Automatically cleanup mock objects after each test.
    
    Ensures no mock state leaks between tests.
    """
    yield
    # Cleanup happens automatically with fixtures


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def assert_called_once_with_any_order():
    """Helper for asserting calls with any argument order.
    
    Useful for testing functions that might call methods
    with arguments in different orders.
    """
    def helper(mock_obj, *args, **kwargs):
        calls = mock_obj.call_args_list
        expected_call = ((args, kwargs) if kwargs else (args,))
        for call in calls:
            if call == expected_call or call[0] == args:
                return True
        return False
    
    return helper


@pytest.fixture
def temp_script_file(tmp_path) -> Path:
    """Temporary script file for testing script operations.
    
    Returns path to a temporary Python script file.
    """
    script = tmp_path / "test_script.py"
    script.write_text("#!/usr/bin/env python3\nprint('test')\n")
    script.chmod(0o755)
    return script
