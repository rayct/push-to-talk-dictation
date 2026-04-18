#!/usr/bin/env python3
"""
Integration test suite for push-to-talk dictation components.
Run this to verify all components are working correctly.
"""

import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TestRunner:
    def __init__(self):
        self.venv_dir = Path(__file__).parent / 'venv'
        self.passed = 0
        self.failed = 0

    def test(self, name: str, func):
        """Run a test and record results."""
        try:
            logger.info(f"\n[TEST] {name}...")
            result = func()
            if result:
                logger.info(f"  ✓ PASSED")
                self.passed += 1
            else:
                logger.info(f"  ✗ FAILED")
                self.failed += 1
        except Exception as e:
            logger.info(f"  ✗ ERROR: {e}")
            self.failed += 1

    def test_system_check(self):
        """Test system requirements."""
        result = subprocess.run([sys.executable, 'sysinfo_check.py'],
                              capture_output=True, timeout=10)
        return result.returncode == 0

    def test_imports(self):
        """Test Python imports."""
        try:
            import pynput
            import pyaudio
            import whisper
            import yaml
            from Xlib import display
            return True
        except ImportError as e:
            logger.error(f"Import error: {e}")
            return False

    def test_audio_devices(self):
        """Test audio device detection."""
        try:
            from audio_capture import AudioCapture
            ac = AudioCapture()
            devices = ac.list_devices()
            logger.info(f"  Found {len(devices)} audio devices")
            return len(devices) > 0
        except Exception as e:
            logger.error(f"Audio test failed: {e}")
            return False

    def test_x11_windows(self):
        """Test X11 window detection."""
        try:
            from x11_injector import X11Injector
            inj = X11Injector()
            windows = inj.list_windows()
            logger.info(f"  Found {len(windows)} windows")
            return len(windows) > 0
        except Exception as e:
            logger.error(f"X11 test failed: {e}")
            return False

    def test_mouse_listener(self):
        """Test mouse listener initialization."""
        try:
            from mouse_listener import MouseListener
            ml = MouseListener()
            ml.start()
            ml.stop()
            return True
        except Exception as e:
            logger.error(f"Mouse listener test failed: {e}")
            return False

    def test_config_load(self):
        """Test configuration loading."""
        try:
            import yaml
            with open('config.yaml') as f:
                config = yaml.safe_load(f)
            logger.info(f"  Model: {config.get('whisper_model')}")
            return 'whisper_model' in config
        except Exception as e:
            logger.error(f"Config test failed: {e}")
            return False

    def run_all(self):
        """Run all tests."""
        logger.info("\n" + "="*50)
        logger.info("Push-to-Talk Dictation - Integration Tests")
        logger.info("="*50)

        self.test("System requirements", self.test_system_check)
        self.test("Python imports", self.test_imports)
        self.test("Configuration", self.test_config_load)
        self.test("Audio devices", self.test_audio_devices)
        self.test("X11 windows", self.test_x11_windows)
        self.test("Mouse listener", self.test_mouse_listener)

        logger.info(f"\n{'='*50}")
        logger.info(f"Results: {self.passed} passed, {self.failed} failed")
        logger.info("="*50)

        return self.failed == 0


if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all()
    sys.exit(0 if success else 1)
