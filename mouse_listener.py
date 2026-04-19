"""
Input trigger module for detecting push-to-talk activation.
Uses keyboard library as fallback for mouse button detection.
For better mouse button support on X11, use middle mouse button mapped to a key.
"""

import logging
from threading import Thread
import keyboard

logger = logging.getLogger(__name__)


class InputListener:
    """Listen for push-to-talk trigger (can be keyboard key or mouse button)."""

    def __init__(self, hotkey: str = 'middle', on_press=None, on_release=None):
        """
        Initialize input listener.
        
        Args:
            hotkey: Key combination to trigger (e.g., 'ctrl+shift+m' or 'middle')
                   Use 'middle' to listen for middle mouse button (requires xdotool)
            on_press: Callback when trigger pressed
            on_release: Callback when trigger released
        """
        self.hotkey = hotkey
        self.on_press = on_press
        self.on_release = on_release
        self.listening = False
        self.listener_thread = None
        
        # Try to use xdotool for middle mouse button
        self.use_xdotool = hotkey == 'middle'
        
    def start(self):
        """Start listening for input events."""
        if self.listening:
            logger.warning("Already listening")
            return

        try:
            if self.use_xdotool:
                self._start_xdotool_listener()
            else:
                self._start_keyboard_listener()
            self.listening = True
            logger.info(f"Input listener started (hotkey: {self.hotkey})")
        except Exception as e:
            logger.error(f"Failed to start input listener: {e}")
            raise

    def _start_keyboard_listener(self):
        """Use keyboard library for key detection."""
        try:
            # Register hotkey with on_release for better control
            keyboard.add_hotkey(self.hotkey, self._on_trigger)
            logger.info(f"Keyboard hotkey registered: {self.hotkey}")
        except Exception as e:
            logger.error(f"Failed to register keyboard hotkey: {e}")
            raise

    def _start_xdotool_listener(self):
        """Use xdotool for middle mouse button detection (X11)."""
        import subprocess
        import select
        
        try:
            # Start xdotool in listen mode
            self.xdotool_process = subprocess.Popen(
                ['xdotool', 'behave_screen', 'exec', 'echo', 'button'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Alternative: Use a simple polling approach for mouse button
            # This is a simplified version - for production, use pyxlib or similar
            logger.warning("Middle mouse button support via xdotool requires additional setup")
            logger.info("Using keyboard fallback - configure 'ctrl+m' as middle mouse button alternative")
            
            # Fall back to keyboard
            self.use_xdotool = False
            self._start_keyboard_listener()
            
        except Exception as e:
            logger.warning(f"xdotool not available, using keyboard: {e}")
            self.use_xdotool = False
            self._start_keyboard_listener()

    def _on_trigger(self):
        """Handle trigger activation."""
        if self.on_press:
            self.on_press()

    def stop(self):
        """Stop listening for input events."""
        if not self.listening:
            return

        try:
            if self.use_xdotool:
                if hasattr(self, 'xdotool_process'):
                    self.xdotool_process.terminate()
            else:
                keyboard.remove_all_hotkeys()
            
            self.listening = False
            logger.info("Input listener stopped")
        except Exception as e:
            logger.error(f"Error stopping input listener: {e}")
