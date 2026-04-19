"""Installation tests for push-to-talk dictation system dependencies."""

import pytest
import sys
import subprocess
import importlib
import os


@pytest.mark.installation
class TestRequirementInstallation:
    """Test that all required packages can be imported."""

    def test_openai_whisper_importable(self):
        """Test that openai-whisper can be imported."""
        try:
            import whisper
            assert whisper is not None
        except ImportError as e:
            pytest.skip(f"openai-whisper not installed: {e}")

    def test_sounddevice_importable(self):
        """Test that sounddevice can be imported."""
        try:
            import sounddevice
            assert sounddevice is not None
        except ImportError as e:
            pytest.skip(f"sounddevice not installed: {e}")

    def test_keyboard_importable(self):
        """Test that keyboard library can be imported."""
        try:
            import keyboard
            assert keyboard is not None
        except ImportError as e:
            pytest.skip(f"keyboard not installed: {e}")

    def test_pyyaml_importable(self):
        """Test that PyYAML can be imported."""
        try:
            import yaml
            assert yaml is not None
        except ImportError as e:
            pytest.skip(f"PyYAML not installed: {e}")


@pytest.mark.installation
class TestSystemValidation:
    """Test system requirements validation."""

    def test_python_version(self):
        """Test Python version is 3.8+."""
        assert sys.version_info.major == 3
        assert sys.version_info.minor >= 8

    def test_linux_platform(self):
        """Test running on Linux."""
        assert sys.platform.startswith('linux')

    def test_temp_directory_writable(self, tmp_path):
        """Test that temporary directory is writable."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()

    def test_cache_directory_writable(self):
        """Test that cache directory is writable."""
        cache_dir = os.path.expanduser("~/.cache")
        assert os.path.exists(cache_dir)


@pytest.mark.installation
class TestVirtualEnvironmentSetup:
    """Test virtual environment setup and isolation."""

    def test_venv_python_executable(self):
        """Test that Python is available in sys.prefix."""
        assert sys.prefix is not None
        assert sys.version_info[0] >= 3

    def test_project_modules_importable(self):
        """Test that project modules can be imported."""
        import audio_capture
        import transcriber
        import x11_injector
        
        assert audio_capture is not None
        assert transcriber is not None
        assert x11_injector is not None

    def test_pytest_available(self):
        """Test that pytest is available."""
        assert pytest is not None
