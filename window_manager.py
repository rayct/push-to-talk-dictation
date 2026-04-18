"""
Window selection and persistence module.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from x11_injector import X11Injector

logger = logging.getLogger(__name__)


class WindowManager:
    """Manage window selection with persistence."""

    def __init__(self):
        self.config_dir = Path.home() / '.local' / 'share' / 'push-to-talk-dict'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.window_file = self.config_dir / 'selected_window.json'
        self.injector = X11Injector()

    def list_windows(self) -> list:
        """Get list of available windows."""
        return self.injector.list_windows()

    def pick_window_interactive(self) -> Optional[dict]:
        """Interactively pick a window."""
        print("\n=== Select Target Window ===\n")
        
        windows = self.list_windows()
        if not windows:
            print("No windows found!")
            return None

        # Filter out window manager/desktop windows
        filtered = [w for w in windows if 'desktop' not in w.get('name', '').lower()]
        
        if not filtered:
            filtered = windows

        for i, w in enumerate(filtered, 1):
            print(f"{i}. {w.get('name', 'Unknown')}")

        try:
            choice = input(f"\nSelect window (1-{len(filtered)}): ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(filtered):
                return filtered[idx]
            else:
                print("Invalid selection")
                return None
                
        except (ValueError, KeyboardInterrupt):
            print("Cancelled")
            return None

    def get_current_window(self) -> Optional[dict]:
        """Get the currently active/focused window."""
        return self.injector.get_active_window()

    def save_window(self, window: dict) -> bool:
        """Save selected window to file."""
        try:
            with open(self.window_file, 'w') as f:
                json.dump(window, f)
            logger.info(f"Window saved: {window.get('name', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to save window: {e}")
            return False

    def load_window(self) -> Optional[dict]:
        """Load previously selected window."""
        if not self.window_file.exists():
            return None

        try:
            with open(self.window_file, 'r') as f:
                window = json.load(f)
            logger.info(f"Loaded saved window: {window.get('name', 'Unknown')}")
            return window
        except Exception as e:
            logger.error(f"Failed to load saved window: {e}")
            return None

    def verify_window_exists(self, window: dict) -> bool:
        """Check if a window still exists."""
        windows = self.list_windows()
        window_ids = [w.get('id') for w in windows]
        return window.get('id') in window_ids
