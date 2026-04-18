"""
Mouse listener module for detecting middle mouse button presses.
"""

import logging
from pynput import mouse
from threading import Event

logger = logging.getLogger(__name__)


class MouseListener:
    """Listen for middle mouse button press and release."""

    def __init__(self, on_press=None, on_release=None):
        self.on_press = on_press
        self.on_release = on_release
        self.listening = False
        self.listener = None

    def start(self):
        """Start listening for mouse events."""
        if self.listening:
            logger.warning("Already listening")
            return

        try:
            self.listener = mouse.Listener(
                on_click=self._on_click,
                on_scroll=self._on_scroll
            )
            self.listener.start()
            self.listening = True
            logger.info("Mouse listener started")
        except Exception as e:
            logger.error(f"Failed to start mouse listener: {e}")
            raise

    def stop(self):
        """Stop listening for mouse events."""
        if not self.listening:
            return

        try:
            if self.listener:
                self.listener.stop()
            self.listening = False
            logger.info("Mouse listener stopped")
        except Exception as e:
            logger.error(f"Error stopping mouse listener: {e}")

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if button != mouse.Button.middle:
            return

        if pressed and self.on_press:
            self.on_press()
        elif not pressed and self.on_release:
            self.on_release()

    def _on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events (unused but required by listener)."""
        pass
