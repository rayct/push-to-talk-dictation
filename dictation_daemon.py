#!/usr/bin/env python3
"""
Main daemon for push-to-talk dictation.
Combines mouse listener, audio capture, transcription, and X11 injection.
"""

import sys
import logging
import signal
import yaml
from pathlib import Path
from typing import Optional

from mouse_listener import MouseListener
from audio_capture import AudioCapture
from transcriber import WhisperTranscriber
from x11_injector import X11Injector
from window_manager import WindowManager


class DictationDaemon:
    """Main daemon coordinating all components."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        self.window_manager = WindowManager()
        self.target_window = None
        
        self.audio_capture = None
        self.transcriber = None
        self.x11_injector = X11Injector(
            delay_ms=self.config['injection'].get('delay_ms', 50)
        )
        
        self.mouse_listener = MouseListener(
            on_press=self.on_mouse_press,
            on_release=self.on_mouse_release
        )
        
        self.recording = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent / 'config.yaml'
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            print(f"Failed to load config: {e}")
            sys.exit(1)

    def _setup_logging(self):
        """Set up logging."""
        log_level = self.config.get('logging', {}).get('level', 'INFO')
        log_file = self.config.get('logging', {}).get('file')
        
        if log_file:
            log_file = Path(log_file).expanduser()
            log_file.parent.mkdir(parents=True, exist_ok=True)
        
        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)

    def initialize(self) -> bool:
        """Initialize all components."""
        try:
            logger.info("Initializing dictation daemon...")
            
            # Initialize audio capture
            audio_config = self.config.get('audio', {})
            self.audio_capture = AudioCapture(
                sample_rate=audio_config.get('sample_rate', 16000),
                chunk_size=audio_config.get('chunk_size', 1024),
                channels=audio_config.get('channels', 1),
                device_index=audio_config.get('device_index')
            )
            
            # Initialize transcriber
            whisper_model = self.config.get('whisper_model', 'base')
            self.transcriber = WhisperTranscriber(model=whisper_model)
            
            # Load or select window
            if self.config.get('window', {}).get('persist_selection', True):
                self.target_window = self.window_manager.load_window()
                
                if self.target_window and not self.window_manager.verify_window_exists(self.target_window):
                    logger.warning(f"Saved window no longer exists")
                    self.target_window = None
            
            if not self.target_window:
                logger.info("Launching window picker...")
                self.target_window = self.window_manager.pick_window_interactive()
                
                if self.target_window:
                    self.window_manager.save_window(self.target_window)
                else:
                    logger.error("No window selected")
                    return False
            
            logger.info(f"Target window: {self.target_window.get('name', 'Unknown')}")
            logger.info("Daemon initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            return False

    def run(self):
        """Run the daemon."""
        if not self.initialize():
            sys.exit(1)
        
        try:
            logger.info("Starting mouse listener... (hold middle mouse button to dictate)")
            self.mouse_listener.start()
            
            # Keep daemon running
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.shutdown()

    def on_mouse_press(self):
        """Callback when middle mouse button is pressed."""
        if self.recording:
            logger.debug("Already recording")
            return
        
        self.recording = True
        logger.debug("Recording started")
        
        try:
            self.audio_capture.start_recording()
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.recording = False

    def on_mouse_release(self):
        """Callback when middle mouse button is released."""
        if not self.recording:
            return
        
        self.recording = False
        logger.debug("Recording stopped")
        
        try:
            # Stop recording and get audio
            audio_bytes = self.audio_capture.stop_recording()
            
            if not audio_bytes:
                logger.warning("No audio captured")
                return
            
            # Transcribe
            text = self.transcriber.transcribe(audio_bytes)
            
            if not text:
                logger.warning("Transcription returned empty result")
                return
            
            # Inject text
            success = self.x11_injector.inject_text(
                text, 
                window_id=self.target_window.get('id') if self.target_window else None
            )
            
            if success:
                logger.info(f"Injected: {text}")
            else:
                logger.error("Failed to inject text")
                
        except Exception as e:
            logger.error(f"Error in mouse release handler: {e}", exc_info=True)

    def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down...")
        
        self.mouse_listener.stop()
        
        if self.audio_capture:
            try:
                self.audio_capture.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up audio: {e}")
        
        if self.transcriber:
            try:
                self.transcriber.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up transcriber: {e}")


# Global logger
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Push-to-talk dictation daemon")
    parser.add_argument('--config', help='Path to config file', default=None)
    parser.add_argument('--select-window', action='store_true', help='Pick a window and exit')
    parser.add_argument('--list-windows', action='store_true', help='List available windows and exit')
    args = parser.parse_args()
    
    daemon = DictationDaemon(config_path=args.config)
    
    if args.list_windows:
        print("\n=== Available Windows ===\n")
        for w in daemon.window_manager.list_windows():
            print(f"ID: {w.get('id')}")
            print(f"Name: {w.get('name', 'Unknown')}")
            print()
        sys.exit(0)
    
    if args.select_window:
        window = daemon.window_manager.pick_window_interactive()
        if window:
            daemon.window_manager.save_window(window)
            print(f"Window saved: {window.get('name')}")
        sys.exit(0)
    
    daemon.run()
