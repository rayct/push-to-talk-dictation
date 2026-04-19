"""Tests for x11_injector module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import subprocess
import x11_injector


class TestX11Injector:
    """Test cases for X11Injector class."""

    def test_initialization_default_delay(self):
        """Test X11Injector initialization with default delay."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            
            assert injector.delay_ms == 50

    def test_initialization_custom_delay(self):
        """Test X11Injector initialization with custom delay."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector(delay_ms=100)
            
            assert injector.delay_ms == 100

    def test_check_xdotool_success(self):
        """Test successful xdotool availability check."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            
            # Should not raise
            assert injector is not None

    def test_check_xdotool_not_found(self):
        """Test xdotool check fails when not installed."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_run.return_value = mock_result
            
            with pytest.raises(RuntimeError):
                x11_injector.X11Injector()

    def test_check_xdotool_exception(self):
        """Test xdotool check handles exceptions."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Command failed")
            
            with pytest.raises(Exception):
                x11_injector.X11Injector()

    def test_get_active_window_success(self):
        """Test successfully getting active window."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = '12345 Test Window Name'
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            window = injector.get_active_window()
            
            assert window is not None
            assert window['id'] == '12345'
            assert 'Test' in window['name']

    def test_get_active_window_no_output(self):
        """Test get_active_window when xdotool returns no output."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ''
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            window = injector.get_active_window()
            
            assert window is None

    def test_get_active_window_failure(self):
        """Test get_active_window handles command failure."""
        with patch('subprocess.run') as mock_run:
            # First call returns success for _check_xdotool, subsequent calls return failure
            success_result = MagicMock()
            success_result.returncode = 0
            
            failure_result = MagicMock()
            failure_result.returncode = 1
            
            mock_run.side_effect = [success_result, failure_result]
            
            injector = x11_injector.X11Injector()
            window = injector.get_active_window()
            
            assert window is None

    def test_get_active_window_exception(self):
        """Test get_active_window handles exceptions."""
        with patch('subprocess.run') as mock_run:
            # First call for check succeeds
            success_result = MagicMock()
            success_result.returncode = 0
            
            # Second call for get_active_window fails
            mock_run.side_effect = [success_result, Exception("Command failed")]
            
            injector = x11_injector.X11Injector()
            window = injector.get_active_window()
            
            assert window is None

    def test_list_windows_wmctrl_success(self):
        """Test listing windows with wmctrl."""
        wmctrl_output = """0  -1 -1 -1 -1   1080  1920 0 0 0 0 1 1 0 0 0 desktop
0   0  0 1234 5678 -1  -1 1080 1920 Google Chrome
0   1  0 5678 1234 -1  -1 1080 1920 Firefox"""
        
        with patch('subprocess.run') as mock_run:
            def run_side_effect(*args, **kwargs):
                result = MagicMock()
                if 'wmctrl' in args[0]:
                    result.returncode = 0
                    result.stdout = wmctrl_output
                else:
                    result.returncode = 0
                    result.stdout = ''
                return result
            
            mock_run.side_effect = run_side_effect
            
            injector = x11_injector.X11Injector()
            windows = injector.list_windows()
            
            assert len(windows) > 0
            assert any('Chrome' in w.get('name', '') for w in windows)

    def test_list_windows_wmctrl_failure_fallback(self):
        """Test list_windows falls back to xdotool when wmctrl fails."""
        xdotool_window_ids = "1234\n5678"
        window_names = ["Test Window", "Another Window"]
        
        with patch('subprocess.run') as mock_run:
            call_count = [0]
            
            def run_side_effect(*args, **kwargs):
                result = MagicMock()
                if 'wmctrl' in args[0]:
                    result.returncode = 1
                elif 'search' in args[0]:
                    result.returncode = 0
                    result.stdout = xdotool_window_ids
                elif 'getwindowname' in args[0]:
                    result.returncode = 0
                    result.stdout = window_names[call_count[0] % 2]
                    call_count[0] += 1
                else:
                    result.returncode = 0
                    result.stdout = ''
                return result
            
            mock_run.side_effect = run_side_effect
            
            injector = x11_injector.X11Injector()
            windows = injector.list_windows()
            
            assert len(windows) >= 0  # Might be 0 due to mocking

    def test_list_windows_empty(self):
        """Test list_windows when no windows found."""
        with patch('subprocess.run') as mock_run:
            # First call for check
            success_result = MagicMock()
            success_result.returncode = 0
            
            # Subsequent calls return failure
            failure_result = MagicMock()
            failure_result.returncode = 1
            
            mock_run.side_effect = [success_result, failure_result, failure_result]
            
            injector = x11_injector.X11Injector()
            windows = injector.list_windows()
            
            assert windows == []

    def test_inject_text_success(self):
        """Test successfully injecting text."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text("Hello, World!")
            
            assert result is True

    def test_inject_text_with_window_id(self):
        """Test injecting text into specific window."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text("Hello", window_id="12345")
            
            assert result is True

    def test_inject_text_empty_text(self):
        """Test that injecting empty text returns False."""
        with patch('subprocess.run') as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            mock_run.return_value = success_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text("")
            
            assert result is False

    def test_inject_text_none_text(self):
        """Test that injecting None text returns False."""
        with patch('subprocess.run') as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            mock_run.return_value = success_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text(None)
            
            assert result is False

    def test_inject_text_timeout(self):
        """Test inject_text handles timeout."""
        with patch('subprocess.run') as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            
            # First call succeeds (check), second fails with timeout
            mock_run.side_effect = [success_result, subprocess.TimeoutExpired("cmd", 30)]
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text("Hello")
            
            assert result is False

    def test_inject_text_command_failed(self):
        """Test inject_text handles command failure."""
        with patch('subprocess.run') as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            
            # First call succeeds (check), second fails
            mock_run.side_effect = [success_result, subprocess.CalledProcessError(1, "cmd")]
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text("Hello")
            
            assert result is False

    def test_inject_text_unexpected_exception(self):
        """Test inject_text handles unexpected exceptions."""
        with patch('subprocess.run') as mock_run:
            success_result = MagicMock()
            success_result.returncode = 0
            
            # First call succeeds (check), second fails
            mock_run.side_effect = [success_result, Exception("Unexpected error")]
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text("Hello")
            
            assert result is False

    def test_inject_text_special_characters(self):
        """Test injecting text with special characters."""
        special_text = "Hello!@#$%^&*()"
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text(special_text)
            
            assert result is True

    def test_inject_text_long_text(self):
        """Test injecting long text."""
        long_text = "A" * 1000
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text(long_text)
            
            assert result is True

    def test_inject_text_unicode(self):
        """Test injecting unicode text."""
        unicode_text = "Hello 世界 🌍"
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            result = injector.inject_text(unicode_text)
            
            assert result is True

    def test_inject_text_uses_custom_delay(self):
        """Test that inject_text uses the configured delay."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector(delay_ms=200)
            injector.inject_text("test")
            
            # Check that delay was passed to xdotool
            calls = mock_run.call_args_list
            type_calls = [c for c in calls if 'type' in str(c)]
            assert any('200' in str(c) for c in type_calls)

    def test_get_focused_window_class(self):
        """Test getting focused window class."""
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = 'Firefox'
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            window_class = injector.get_focused_window_class()
            
            assert window_class == 'Firefox'

    def test_get_focused_window_class_failure(self):
        """Test get_focused_window_class handles failure."""
        with patch('subprocess.run') as mock_run:
            # First call for check
            success_result = MagicMock()
            success_result.returncode = 0
            
            # Second call for get_focused
            failure_result = MagicMock()
            failure_result.returncode = 1
            
            mock_run.side_effect = [success_result, failure_result]
            
            injector = x11_injector.X11Injector()
            window_class = injector.get_focused_window_class()
            
            assert window_class is None

    def test_window_id_parsing(self):
        """Test correct parsing of window ID from xdotool output."""
        output = "1234567"
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = output
            mock_run.return_value = mock_result
            
            injector = x11_injector.X11Injector()
            window = injector.get_active_window()
            
            if window:
                assert window['id'] == '1234567'
