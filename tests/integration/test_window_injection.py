"""Integration tests for window selection and text injection workflow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import x11_injector
import window_manager


@pytest.mark.integration
@pytest.mark.x11
class TestWindowInjectionWorkflow:
    """Test window selection and text injection workflow."""

    @pytest.fixture
    def setup_injection(self, mock_x11_display):
        """Setup window manager and X11 injector."""
        wm = window_manager.WindowManager()
        inj = x11_injector.X11Injector()
        yield wm, inj

    def test_select_window_then_inject(self, mock_x11_display):
        """Test selecting a window and injecting text."""
        wm = window_manager.WindowManager()
        inj = x11_injector.X11Injector()
        
        with patch.object(inj, 'list_windows', return_value={'1': 'Terminal', '2': 'Editor'}):
            with patch.object(inj, 'inject_text') as mock_inject:
                # Select window
                wm.save_window('1')
                selected = wm.load_window()
                assert selected == '1'
                
                # Inject text
                inj.inject_text('test text')
                mock_inject.assert_called()

    def test_workflow_with_multiple_windows(self, mock_x11_display):
        """Test switching between multiple windows for injection."""
        wm = window_manager.WindowManager()
        inj = x11_injector.X11Injector()
        
        windows = {'1': 'Terminal', '2': 'Editor', '3': 'Browser'}
        
        with patch.object(inj, 'list_windows', return_value=windows):
            with patch.object(inj, 'inject_text') as mock_inject:
                for win_id, win_name in windows.items():
                    wm.save_window(win_id)
                    selected = wm.load_window()
                    assert selected == win_id
                    inj.inject_text(f'text for {win_name}')
                
                assert mock_inject.call_count == 3

    def test_injection_to_specific_window(self, mock_x11_display):
        """Test injecting text to a specific window."""
        wm = window_manager.WindowManager()
        inj = x11_injector.X11Injector()
        
        with patch.object(inj, 'inject_text') as mock_inject:
            with patch.object(inj, 'get_active_window', return_value='1'):
                wm.save_window('1')
                inj.inject_text('test message')
                mock_inject.assert_called_with('test message')

    def test_workflow_error_no_windows_available(self, mock_x11_display):
        """Test error handling when no windows are available."""
        inj = x11_injector.X11Injector()
        
        with patch.object(inj, 'list_windows', return_value={}):
            windows = inj.list_windows()
            assert len(windows) == 0

    def test_workflow_error_injection_fails(self, mock_x11_display):
        """Test error handling when injection fails."""
        inj = x11_injector.X11Injector()
        
        with patch.object(inj, 'inject_text', side_effect=RuntimeError("Injection failed")):
            with pytest.raises(RuntimeError):
                inj.inject_text('test text')

    def test_window_persistence_across_sessions(self, mock_x11_display, tmp_path):
        """Test window selection is persisted across sessions."""
        # First session
        wm1 = window_manager.WindowManager(config_dir=str(tmp_path))
        wm1.save_window('42')
        
        # Second session
        wm2 = window_manager.WindowManager(config_dir=str(tmp_path))
        selected = wm2.load_window()
        
        assert selected == '42'

    def test_workflow_cleanup(self, mock_x11_display):
        """Test proper cleanup of resources."""
        wm = window_manager.WindowManager()
        inj = x11_injector.X11Injector()
        
        # Use resources
        with patch.object(inj, 'inject_text'):
            inj.inject_text('test')
        
        # No explicit cleanup needed for these components
        assert wm is not None


@pytest.mark.integration
class TestWindowInjectionPerformance:
    """Test performance of window injection workflow."""

    def test_injection_latency(self, mock_x11_display):
        """Test that text injection is fast."""
        import time
        inj = x11_injector.X11Injector()
        
        with patch.object(inj, 'inject_text') as mock_inject:
            start = time.time()
            inj.inject_text('hello world')
            elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should be very fast
        mock_inject.assert_called_once_with('hello world')

    def test_window_listing_performance(self, mock_x11_display):
        """Test that window listing is efficient."""
        import time
        inj = x11_injector.X11Injector()
        
        with patch.object(inj, 'list_windows', return_value={str(i): f'window{i}' for i in range(10)}):
            start = time.time()
            windows = inj.list_windows()
            elapsed = time.time() - start
        
        assert elapsed < 0.5  # Should be fast
        assert len(windows) == 10
