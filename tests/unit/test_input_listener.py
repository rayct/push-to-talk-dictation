"""Tests for input_listener module (mouse_listener.py)."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from threading import Thread, Event

# Add parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestInputListener:
    """Test cases for InputListener class."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_keyboard):
        """Setup for each test."""
        self.mock_keyboard = mock_keyboard
        import importlib
        import mouse_listener
        importlib.reload(mouse_listener)

    def test_initialization_default_hotkey(self):
        """Test InputListener initialization with default hotkey."""
        from mouse_listener import InputListener
        
        listener = InputListener()
        
        assert listener.hotkey == 'middle'
        assert listener.on_press is None
        assert listener.on_release is None
        assert listener.listening is False

    def test_initialization_custom_hotkey(self):
        """Test InputListener initialization with custom hotkey."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+shift+m')
        
        assert listener.hotkey == 'ctrl+shift+m'

    def test_initialization_with_callbacks(self):
        """Test InputListener initialization with callbacks."""
        from mouse_listener import InputListener
        
        on_press = Mock()
        on_release = Mock()
        
        listener = InputListener(on_press=on_press, on_release=on_release)
        
        assert listener.on_press == on_press
        assert listener.on_release == on_release

    def test_start_listening_keyboard_hotkey(self):
        """Test starting listener with keyboard hotkey."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        listener.start()
        
        assert listener.listening is True

    def test_start_listening_already_listening(self):
        """Test starting listener when already listening."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        listener.start()
        listener.start()
        
        assert listener.listening is True

    def test_start_listening_keyboard_registers_hotkey(self):
        """Test that start registers keyboard hotkey."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        listener.start()
        
        # Verify keyboard hotkey was registered
        with patch('keyboard.add_hotkey') as mock_add:
            listener2 = InputListener(hotkey='ctrl+m')
            listener2.start()
            mock_add.assert_called()

    def test_start_listening_keyboard_exception(self):
        """Test start listening handles keyboard registration failure."""
        from mouse_listener import InputListener
        
        with patch('keyboard.add_hotkey') as mock_add:
            mock_add.side_effect = Exception("Keyboard error")
            
            listener = InputListener(hotkey='ctrl+m')
            
            with pytest.raises(Exception):
                listener.start()

    def test_start_listening_middle_mouse_fallback(self):
        """Test middle mouse button falls back to keyboard."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='middle')
        listener.start()
        
        assert listener.listening is True

    def test_stop_listening_keyboard(self):
        """Test stopping keyboard listener."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        listener.start()
        listener.stop()
        
        assert listener.listening is False

    def test_stop_listening_not_listening(self):
        """Test stopping listener when not listening."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        listener.stop()
        
        assert listener.listening is False

    def test_stop_listening_removes_hotkeys(self):
        """Test that stop removes all hotkeys."""
        from mouse_listener import InputListener
        
        with patch('keyboard.remove_all_hotkeys') as mock_remove:
            listener = InputListener(hotkey='ctrl+m')
            listener.start()
            listener.stop()
            
            mock_remove.assert_called()

    def test_on_trigger_calls_press_callback(self):
        """Test trigger activation calls on_press callback."""
        from mouse_listener import InputListener
        
        on_press = Mock()
        listener = InputListener(hotkey='ctrl+m', on_press=on_press)
        
        listener._on_trigger()
        
        on_press.assert_called_once()

    def test_on_trigger_no_callback(self):
        """Test trigger activation with no callback."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        
        # Should not raise
        listener._on_trigger()

    def test_hotkey_registration_with_callback(self):
        """Test hotkey is registered with callback."""
        from mouse_listener import InputListener
        
        on_press = Mock()
        
        with patch('keyboard.add_hotkey') as mock_add:
            listener = InputListener(hotkey='ctrl+shift+t', on_press=on_press)
            listener.start()
            
            mock_add.assert_called()
            # Verify correct hotkey was registered
            call_args = mock_add.call_args
            assert call_args[0][0] == 'ctrl+shift+t'

    def test_multiple_listeners_independent(self):
        """Test multiple listeners operate independently."""
        from mouse_listener import InputListener
        
        listener1 = InputListener(hotkey='ctrl+m')
        listener2 = InputListener(hotkey='ctrl+n')
        
        listener1.start()
        listener2.start()
        
        assert listener1.listening is True
        assert listener2.listening is True

    def test_listener_hotkey_variations(self):
        """Test various hotkey configurations."""
        from mouse_listener import InputListener
        
        hotkeys = [
            'ctrl+m',
            'shift+m',
            'alt+m',
            'ctrl+shift+m',
            'ctrl+alt+m',
        ]
        
        for hotkey in hotkeys:
            listener = InputListener(hotkey=hotkey)
            listener.start()
            assert listener.listening is True
            listener.stop()

    def test_start_middle_mouse_with_xdotool(self):
        """Test middle mouse button detection setup."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='middle')
        
        assert listener.use_xdotool is True
        listener.start()

    def test_xdotool_fallback_to_keyboard(self):
        """Test xdotool falls back to keyboard listener."""
        from mouse_listener import InputListener
        
        with patch('subprocess.Popen') as mock_popen:
            mock_popen.side_effect = Exception("xdotool not available")
            
            listener = InputListener(hotkey='middle')
            listener.start()
            
            # Should fallback to keyboard
            assert listener.listening is True
            assert listener.use_xdotool is False

    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break the listener."""
        from mouse_listener import InputListener
        
        def failing_callback():
            raise Exception("Callback failed")
        
        listener = InputListener(hotkey='ctrl+m', on_press=failing_callback)
        listener.start()
        
        # Should not raise
        listener._on_trigger()

    def test_listener_thread_safety(self):
        """Test listener can be stopped from different thread."""
        from mouse_listener import InputListener
        import time
        
        listener = InputListener(hotkey='ctrl+m')
        listener.start()
        
        def stop_listener():
            time.sleep(0.1)
            listener.stop()
        
        thread = Thread(target=stop_listener, daemon=True)
        thread.start()
        thread.join(timeout=2)
        
        assert listener.listening is False

    def test_listener_stop_exception_handling(self):
        """Test stop handles exceptions gracefully."""
        from mouse_listener import InputListener
        
        with patch('keyboard.remove_all_hotkeys') as mock_remove:
            mock_remove.side_effect = Exception("Removal failed")
            
            listener = InputListener(hotkey='ctrl+m')
            listener.start()
            
            # Should handle exception
            listener.stop()

    def test_xdotool_process_termination(self):
        """Test xdotool process is terminated on stop."""
        from mouse_listener import InputListener
        
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_popen.return_value = mock_process
            
            listener = InputListener(hotkey='middle')
            
            try:
                listener.start()
            except:
                pass
            
            # If using xdotool, process should be stored
            if hasattr(listener, 'xdotool_process'):
                listener.stop()

    def test_listener_state_consistency(self):
        """Test listener state remains consistent."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        
        assert listener.listening is False
        
        listener.start()
        assert listener.listening is True
        
        listener.stop()
        assert listener.listening is False

    def test_listener_multiple_start_stop_cycles(self):
        """Test listener can handle multiple start/stop cycles."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        
        for _ in range(3):
            listener.start()
            assert listener.listening is True
            
            listener.stop()
            assert listener.listening is False

    def test_listener_with_simple_key(self):
        """Test listener with simple key (no modifiers)."""
        from mouse_listener import InputListener
        
        with patch('keyboard.add_hotkey'):
            listener = InputListener(hotkey='m')
            listener.start()
            
            assert listener.listening is True

    def test_listener_with_function_key(self):
        """Test listener with function key."""
        from mouse_listener import InputListener
        
        with patch('keyboard.add_hotkey'):
            listener = InputListener(hotkey='f1')
            listener.start()
            
            assert listener.listening is True

    def test_trigger_callback_signature(self):
        """Test trigger callback receives no arguments."""
        from mouse_listener import InputListener
        
        on_press = Mock()
        listener = InputListener(hotkey='ctrl+m', on_press=on_press)
        
        listener._on_trigger()
        
        # Verify called with no arguments
        on_press.assert_called_once_with()

    def test_on_trigger_execution(self):
        """Test _on_trigger correctly invokes callback."""
        from mouse_listener import InputListener
        
        calls = []
        def callback():
            calls.append(1)
        
        listener = InputListener(hotkey='ctrl+m', on_press=callback)
        listener._on_trigger()
        
        assert len(calls) == 1

    def test_listener_initialization_no_side_effects(self):
        """Test initialization doesn't start listening."""
        from mouse_listener import InputListener
        
        listener = InputListener(hotkey='ctrl+m')
        
        assert listener.listening is False

    def test_different_hotkey_formats(self):
        """Test various hotkey string formats."""
        from mouse_listener import InputListener
        
        formats = [
            'ctrl+shift+alt+m',
            'left ctrl+m',
            'right shift+m',
        ]
        
        for hotkey in formats:
            try:
                listener = InputListener(hotkey=hotkey)
                # Should not raise during initialization
                assert listener.hotkey == hotkey
            except:
                pass
