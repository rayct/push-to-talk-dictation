"""Tests for window_manager module."""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestWindowManager:
    """Test cases for WindowManager class."""

    @pytest.fixture(autouse=True)
    def setup(self, temp_config_dir, monkeypatch):
        """Setup for each test."""
        # Mock home directory
        monkeypatch.setenv('HOME', temp_config_dir)
        import importlib
        import window_manager
        importlib.reload(window_manager)
        self.temp_config_dir = temp_config_dir

    def test_initialization_creates_config_dir(self):
        """Test WindowManager creates config directory."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            assert manager.config_dir.exists()

    def test_initialization_sets_correct_path(self):
        """Test WindowManager sets correct config directory path."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            expected_path = Path.home() / '.local' / 'share' / 'push-to-talk-dict'
            assert str(manager.config_dir) == str(expected_path)

    def test_initialization_sets_window_file_path(self):
        """Test WindowManager sets window file path."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            expected_file = manager.config_dir / 'selected_window.json'
            assert manager.window_file == expected_file

    def test_list_windows(self):
        """Test list_windows delegates to injector."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_windows = [
            {'id': '1', 'name': 'Window 1'},
            {'id': '2', 'name': 'Window 2'},
        ]
        mock_injector.list_windows.return_value = mock_windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            windows = manager.list_windows()
            
            assert windows == mock_windows

    def test_list_windows_empty(self):
        """Test list_windows when no windows available."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_injector.list_windows.return_value = []
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            windows = manager.list_windows()
            
            assert windows == []

    def test_get_current_window(self):
        """Test getting currently active window."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_window = {'id': '1', 'name': 'Active Window'}
        mock_injector.get_active_window.return_value = mock_window
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            window = manager.get_current_window()
            
            assert window == mock_window

    def test_save_window_success(self):
        """Test saving window to file."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            window = {'id': '123', 'name': 'Test Window'}
            
            result = manager.save_window(window)
            
            assert result is True
            assert manager.window_file.exists()

    def test_save_window_content(self):
        """Test saved window content is correct."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            window = {'id': '456', 'name': 'Another Window'}
            
            manager.save_window(window)
            
            with open(manager.window_file) as f:
                saved_window = json.load(f)
            
            assert saved_window == window

    def test_save_window_overwrites_existing(self):
        """Test save_window overwrites previous file."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            window1 = {'id': '1', 'name': 'Window 1'}
            window2 = {'id': '2', 'name': 'Window 2'}
            
            manager.save_window(window1)
            manager.save_window(window2)
            
            with open(manager.window_file) as f:
                saved_window = json.load(f)
            
            assert saved_window['id'] == '2'

    def test_save_window_exception_handling(self):
        """Test save_window handles exceptions."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            window = {'id': '1', 'name': 'Window'}
            
            # Mock open to raise exception
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = manager.save_window(window)
                
                assert result is False

    def test_load_window_success(self):
        """Test loading saved window."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            window_to_save = {'id': '789', 'name': 'Saved Window'}
            
            manager.save_window(window_to_save)
            loaded_window = manager.load_window()
            
            assert loaded_window == window_to_save

    def test_load_window_file_not_exists(self):
        """Test load_window when file doesn't exist."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            window = manager.load_window()
            
            assert window is None

    def test_load_window_invalid_json(self):
        """Test load_window handles invalid JSON."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            # Create invalid JSON file
            with open(manager.window_file, 'w') as f:
                f.write("invalid json {")
            
            window = manager.load_window()
            
            assert window is None

    def test_load_window_corrupted_file(self):
        """Test load_window handles corrupted file gracefully."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            # Create empty file
            manager.window_file.touch()
            
            window = manager.load_window()
            
            assert window is None

    def test_verify_window_exists_true(self):
        """Test verify_window_exists returns True for existing window."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_injector.list_windows.return_value = [
            {'id': '123', 'name': 'Window 1'},
            {'id': '456', 'name': 'Window 2'},
        ]
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            window = {'id': '123', 'name': 'Window 1'}
            
            result = manager.verify_window_exists(window)
            
            assert result is True

    def test_verify_window_exists_false(self):
        """Test verify_window_exists returns False for non-existing window."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_injector.list_windows.return_value = [
            {'id': '123', 'name': 'Window 1'},
        ]
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            window = {'id': '999', 'name': 'Non-existent Window'}
            
            result = manager.verify_window_exists(window)
            
            assert result is False

    def test_verify_window_exists_no_windows(self):
        """Test verify_window_exists with no available windows."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_injector.list_windows.return_value = []
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            window = {'id': '123', 'name': 'Window'}
            
            result = manager.verify_window_exists(window)
            
            assert result is False

    def test_pick_window_interactive_no_windows(self, monkeypatch):
        """Test interactive window picking with no windows."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        mock_injector.list_windows.return_value = []
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            # Capture output
            captured = StringIO()
            with patch('sys.stdout', captured):
                window = manager.pick_window_interactive()
            
            assert window is None

    def test_pick_window_interactive_valid_selection(self, monkeypatch):
        """Test interactive window picking with valid selection."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        windows = [
            {'id': '1', 'name': 'Window 1'},
            {'id': '2', 'name': 'Window 2'},
            {'id': '3', 'name': 'Window 3'},
        ]
        mock_injector.list_windows.return_value = windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            # Mock user input to select window 2
            with patch('builtins.input', return_value='2'):
                window = manager.pick_window_interactive()
            
            assert window == windows[1]

    def test_pick_window_interactive_invalid_selection(self, monkeypatch):
        """Test interactive window picking with invalid selection."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        windows = [
            {'id': '1', 'name': 'Window 1'},
            {'id': '2', 'name': 'Window 2'},
        ]
        mock_injector.list_windows.return_value = windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            # Mock user input with invalid selection
            with patch('builtins.input', return_value='99'):
                window = manager.pick_window_interactive()
            
            assert window is None

    def test_pick_window_interactive_non_numeric_input(self):
        """Test interactive window picking with non-numeric input."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        windows = [{'id': '1', 'name': 'Window 1'}]
        mock_injector.list_windows.return_value = windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            with patch('builtins.input', return_value='invalid'):
                window = manager.pick_window_interactive()
            
            assert window is None

    def test_pick_window_interactive_keyboard_interrupt(self):
        """Test interactive window picking handles keyboard interrupt."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        windows = [{'id': '1', 'name': 'Window 1'}]
        mock_injector.list_windows.return_value = windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            with patch('builtins.input', side_effect=KeyboardInterrupt):
                window = manager.pick_window_interactive()
            
            assert window is None

    def test_pick_window_interactive_filters_desktop(self):
        """Test interactive window picking filters out desktop windows."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        windows = [
            {'id': '1', 'name': 'desktop'},
            {'id': '2', 'name': 'Real Window'},
            {'id': '3', 'name': 'Another Window'},
        ]
        mock_injector.list_windows.return_value = windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            with patch('builtins.input', return_value='1'):
                window = manager.pick_window_interactive()
            
            # Should select from filtered list (Real Window would be index 1)
            assert window is not None

    def test_config_directory_permissions(self):
        """Test config directory is created with proper permissions."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            
            assert manager.config_dir.exists()
            assert manager.config_dir.is_dir()

    def test_multiple_managers_same_config(self):
        """Test multiple WindowManager instances share same config file."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager1 = WindowManager()
            manager2 = WindowManager()
            
            window = {'id': '1', 'name': 'Test'}
            manager1.save_window(window)
            
            loaded = manager2.load_window()
            
            assert loaded == window

    def test_window_file_json_format(self):
        """Test window file is valid JSON."""
        from window_manager import WindowManager
        
        with patch('window_manager.X11Injector'):
            manager = WindowManager()
            window = {'id': '123', 'name': 'Test Window', 'extra': 'data'}
            
            manager.save_window(window)
            
            # Should be readable as JSON
            with open(manager.window_file) as f:
                loaded = json.load(f)
            
            assert loaded['id'] == '123'
            assert loaded['name'] == 'Test Window'
            assert loaded['extra'] == 'data'

    def test_save_and_verify_window_workflow(self):
        """Test complete workflow: save, verify, and load window."""
        from window_manager import WindowManager
        
        mock_injector = MagicMock()
        windows = [
            {'id': '1', 'name': 'Target Window'},
            {'id': '2', 'name': 'Other Window'},
        ]
        mock_injector.list_windows.return_value = windows
        
        with patch('window_manager.X11Injector', return_value=mock_injector):
            manager = WindowManager()
            
            # Save window
            window_to_save = windows[0]
            manager.save_window(window_to_save)
            
            # Verify it exists
            assert manager.verify_window_exists(window_to_save)
            
            # Load and verify content
            loaded = manager.load_window()
            assert loaded == window_to_save
