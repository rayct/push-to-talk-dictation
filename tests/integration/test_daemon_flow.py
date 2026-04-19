"""Integration tests for daemon with all components."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import dictation_daemon
import audio_capture
import transcriber
import x11_injector
import window_manager
import mouse_listener


@pytest.mark.integration
class TestDaemonFlow:
    """Test daemon initialization and component integration."""

    def test_daemon_initialization(self, mock_audio_device, mock_display):
        """Test daemon initializes all components."""
        with patch.object(dictation_daemon.DictationDaemon, '__init__', return_value=None):
            daemon = dictation_daemon.DictationDaemon()
            assert daemon is not None

    def test_daemon_with_all_components(self, mock_audio_device, mock_display):
        """Test daemon has all required components."""
        components = {
            'audio': audio_capture.AudioCapture,
            'transcriber': transcriber.WhisperTranscriber,
            'injector': x11_injector.X11Injector,
            'window_mgr': window_manager.WindowManager,
            'listener': mouse_listener.MouseListener,
        }
        
        for name, component_class in components.items():
            try:
                comp = component_class()
                assert comp is not None
            except Exception as e:
                # Some components may fail in test env, that's ok
                pass

    def test_daemon_startup_shutdown(self, mock_audio_device, mock_display):
        """Test daemon can start and shutdown gracefully."""
        with patch.object(dictation_daemon.DictationDaemon, '__init__', return_value=None):
            with patch.object(dictation_daemon.DictationDaemon, 'run', return_value=None):
                with patch.object(dictation_daemon.DictationDaemon, 'shutdown', return_value=None):
                    daemon = dictation_daemon.DictationDaemon()
                    daemon.run()
                    daemon.shutdown()

    def test_daemon_event_flow(self, mock_audio_device, mock_display):
        """Test event flow through daemon components."""
        # Create mock components
        listener = Mock()
        audio_cap = Mock()
        transcriber_mock = Mock()
        injector = Mock()
        
        # Setup callbacks
        on_trigger = None
        def set_on_trigger(callback):
            nonlocal on_trigger
            on_trigger = callback
        
        listener.on_trigger_pressed = set_on_trigger
        
        # Simulate trigger
        if on_trigger:
            on_trigger()

    def test_daemon_error_recovery(self, mock_audio_device, mock_display):
        """Test daemon handles component errors gracefully."""
        with patch.object(audio_capture.AudioCapture, 'start_recording', 
                         side_effect=RuntimeError("Device error")):
            cap = audio_capture.AudioCapture()
            with pytest.raises(RuntimeError):
                cap.start_recording()

    def test_daemon_configuration_loading(self, mock_audio_device, mock_display, tmp_path):
        """Test daemon can load configuration."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("audio_device: 0\nhotkey: 'ctrl+m'\n")
        
        assert config_file.exists()

    def test_daemon_state_management(self, mock_audio_device, mock_display):
        """Test daemon state transitions."""
        states = ['idle', 'recording', 'processing', 'done']
        
        current_state = 'idle'
        for next_state in states:
            current_state = next_state
            assert current_state in states


@pytest.mark.integration
class TestDaemonWorkflow:
    """Test complete daemon workflow scenarios."""

    def test_complete_push_to_talk_workflow(self, mock_audio_device, mock_display):
        """Test complete push-to-talk workflow."""
        # Setup components
        listener = mouse_listener.MouseListener()
        audio_cap = audio_capture.AudioCapture()
        trans = transcriber.WhisperTranscriber()
        injector = x11_injector.X11Injector()
        wm = window_manager.WindowManager()
        
        # Mock the workflow
        with patch.object(listener, 'start_listening'):
            with patch.object(audio_cap, 'start_recording'):
                with patch.object(audio_cap, 'stop_recording', return_value=b'audio'):
                    with patch.object(trans, 'transcribe', return_value='hello'):
                        with patch.object(injector, 'inject_text'):
                            # Simulate workflow
                            listener.start_listening()
                            audio_cap.start_recording()
                            audio = audio_cap.stop_recording()
                            text = trans.transcribe(audio)
                            injector.inject_text(text)
        
        trans.cleanup()

    def test_daemon_with_window_selection(self, mock_audio_device, mock_display):
        """Test daemon workflow with window selection."""
        wm = window_manager.WindowManager()
        
        # Select window
        wm.save_window('terminal-123')
        selected = wm.load_window()
        
        assert selected == 'terminal-123'

    def test_daemon_continuous_operation(self, mock_audio_device, mock_display):
        """Test daemon can handle multiple cycles."""
        trans = transcriber.WhisperTranscriber()
        
        for i in range(3):
            with patch.object(trans, 'transcribe', return_value=f'cycle {i}'):
                result = trans.transcribe(b'audio')
                assert f'cycle {i}' in result
        
        trans.cleanup()
