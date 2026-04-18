"""
X11 input injection module for typing text into windows.
"""

import subprocess
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class X11Injector:
    """Inject text into X11 windows using xdotool."""

    def __init__(self, delay_ms: int = 50):
        self.delay_ms = delay_ms
        self._check_xdotool()

    def _check_xdotool(self):
        """Verify xdotool is available."""
        try:
            result = subprocess.run(['which', 'xdotool'], 
                                  capture_output=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError("xdotool not found. Install with: sudo apt install xdotool")
        except Exception as e:
            logger.error(f"xdotool check failed: {e}")
            raise

    def get_active_window(self) -> Optional[dict]:
        """Get the currently active window."""
        try:
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return {
                    'id': result.stdout.split()[0],
                    'name': result.stdout.split(maxsplit=1)[1] if len(result.stdout.split()) > 1 else ''
                }
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
        
        return None

    def list_windows(self) -> list:
        """List all visible windows."""
        try:
            result = subprocess.run(['wmctrl', '-l'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                windows = []
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    parts = line.split(maxsplit=3)
                    if len(parts) >= 4:
                        windows.append({
                            'id': parts[0],
                            'desktop': parts[1],
                            'pid': parts[2],
                            'name': parts[3]
                        })
                return windows
        except Exception as e:
            logger.warning(f"Failed to list windows (wmctrl): {e}")
        
        # Fallback: use xdotool
        try:
            result = subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', ''],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                windows = []
                for wid in result.stdout.strip().split('\n'):
                    if wid:
                        try:
                            name_result = subprocess.run(['xdotool', 'getwindowname', wid],
                                                       capture_output=True, text=True, timeout=5)
                            if name_result.returncode == 0:
                                windows.append({
                                    'id': wid,
                                    'name': name_result.stdout.strip()
                                })
                        except:
                            pass
                return windows
        except Exception as e:
            logger.error(f"Failed to list windows (xdotool): {e}")
        
        return []

    def inject_text(self, text: str, window_id: Optional[str] = None) -> bool:
        """
        Inject text into a window.
        
        Args:
            text: Text to inject
            window_id: Target window ID; if None, uses active window
            
        Returns:
            True if successful, False otherwise
        """
        if not text:
            logger.warning("Empty text to inject")
            return False

        try:
            # Activate window if specified
            if window_id:
                subprocess.run(['xdotool', 'windowactivate', window_id],
                             check=True, timeout=5)
                time.sleep(0.1)
            
            # Type the text
            # Escape special characters for xdotool
            escaped_text = text
            # xdotool type handles most characters, but some need special handling
            
            subprocess.run(['xdotool', 'type', '--delay', str(self.delay_ms), 
                          escaped_text],
                         check=True, timeout=30)
            
            logger.info(f"Text injected successfully ({len(text)} chars)")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("Text injection timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Text injection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during injection: {e}")
            return False

    def get_focused_window_class(self) -> Optional[str]:
        """Get the WM_CLASS of the focused window."""
        try:
            result = subprocess.run(['xdotool', 'getactivewindow', 'getwindowname'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get window class: {e}")
        
        return None
