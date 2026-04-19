# Testing Push-to-Talk Dictation

Comprehensive pytest test infrastructure for the push-to-talk dictation project.

## Quick Start

### Installation

```bash
cd /home/ray/Repos/github.com/rayct/push-to-talk-dictation

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
pip install -r tests/requirements-test.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_audio_capture.py

# Run specific test
pytest tests/unit/test_audio_capture.py::test_audio_device_list

# Run tests matching pattern
pytest -k "audio" -v

# Run tests in parallel (faster)
pytest -n auto
```

## Test Structure

```
tests/
├── __init__.py                 # Test package marker
├── conftest.py                 # Shared fixtures and configuration
├── requirements-test.txt       # Testing dependencies
├── unit/                       # Unit tests (isolated component tests)
│   ├── __init__.py
│   ├── test_audio_capture.py
│   ├── test_transcriber.py
│   ├── test_x11_injector.py
│   ├── test_window_manager.py
│   ├── test_mouse_listener.py
│   └── test_config.py
├── integration/                # Integration tests (component interaction)
│   ├── __init__.py
│   ├── test_daemon_flow.py
│   ├── test_recording_pipeline.py
│   └── test_injection_pipeline.py
├── installation/               # Installation and environment tests
│   ├── __init__.py
│   ├── test_dependencies.py
│   └── test_system_check.py
├── performance/                # Performance and benchmark tests
│   ├── __init__.py
│   └── test_performance.py
└── test_data/                  # Test data files and fixtures
    ├── sample_audio.wav
    └── test_config.yaml
```

## Fixtures Overview

### X11 and Display Fixtures

- **`mock_display`** - Simulates Xlib Display object
- **`mock_window`** - Simulates Xlib Window object
- **`mock_x11_injector`** - Mocked X11Injector with text injection methods
- **`mock_display_env`** - Sets DISPLAY environment variable

### Audio Fixtures

- **`mock_audio_device`** - Mock audio device properties
- **`mock_audio_capture`** - Mocked AudioCapture class
- **`mock_transcriber`** - Mocked WhisperTranscriber
- **`sample_audio_data`** - Test audio bytes (WAV format)

### Input and Control Fixtures

- **`mock_input_listener`** - Mocked keyboard/mouse listener
- **`sample_window_list`** - Sample window list for testing

### Configuration Fixtures

- **`test_config_dict`** - Test configuration dictionary
- **`temp_config_file`** - Temporary config.yaml file
- **`temp_window_selection`** - Temporary window selection JSON
- **`mock_home_dir`** - Temporary home directory

### Integration Fixtures

- **`mock_daemon`** - Fully mocked DictationDaemon
- **`sample_transcription_text`** - Sample transcribed text

### Utility Fixtures

- **`caplog_debug`** - Debug-level log capture
- **`test_logger`** - Logger instance for tests
- **`venv_path`** - Virtual environment directory
- **`mock_venv_bin`** - Mock venv binaries

## Writing Tests

### Unit Test Template

```python
import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.unit
class TestAudioCapture:
    """Unit tests for AudioCapture class."""

    def test_list_devices(self, mock_audio_capture):
        """Test listing audio devices."""
        devices = mock_audio_capture.list_devices()
        assert devices
        assert 0 in devices
        assert devices[0] == "Built-in Microphone"

    def test_start_recording(self, mock_audio_capture):
        """Test starting a recording."""
        result = mock_audio_capture.start_recording()
        assert result is True
        mock_audio_capture.start_recording.assert_called_once()
```

### Integration Test Template

```python
import pytest


@pytest.mark.integration
class TestRecordingPipeline:
    """Integration tests for recording pipeline."""

    def test_record_and_transcribe(self, mock_daemon, sample_audio_data):
        """Test complete recording and transcription flow."""
        # Setup
        daemon = mock_daemon
        
        # Execute
        daemon.audio_capture.record_until_silence.return_value = sample_audio_data
        daemon.transcriber.transcribe.return_value = {
            'text': 'test transcription'
        }
        
        # Assert
        result = daemon.process_recording()
        assert result == "Transcribed text"
```

### Test Markers

Mark tests with appropriate markers:

```python
@pytest.mark.unit
def test_something():
    """Unit test."""
    pass

@pytest.mark.integration
def test_interaction():
    """Integration test."""
    pass

@pytest.mark.slow
def test_heavy_computation():
    """Slow test."""
    pass

@pytest.mark.x11
def test_x11_operation(mock_display):
    """Test requiring X11."""
    pass

@pytest.mark.audio
def test_audio_operation(mock_audio_capture):
    """Test requiring audio."""
    pass
```

## Running Tests by Category

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run unit and integration (skip slow)
pytest -m "not slow"

# Run only X11 tests
pytest -m x11

# Run only audio tests
pytest -m audio

# Run fast tests only
pytest --timeout=10
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
pytest --cov=. --cov-report=html --cov-report=term

# View report
open htmlcov/index.html
```

### Generate Coverage Report with Exclusions

```bash
pytest --cov=. --cov-report=term-missing
```

### Check Coverage Thresholds

```bash
pytest --cov=. --cov-fail-under=80
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt -r tests/requirements-test.txt
      - run: pytest --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Mocking Best Practices

### Mock Return Values

```python
def test_with_return_value(mock_audio_capture):
    mock_audio_capture.list_devices.return_value = {0: "Mic"}
    result = mock_audio_capture.list_devices()
    assert result == {0: "Mic"}
```

### Mock Side Effects

```python
def test_with_side_effect(mock_audio_capture):
    mock_audio_capture.start_recording.side_effect = [True, False]
    assert mock_audio_capture.start_recording() is True
    assert mock_audio_capture.start_recording() is False
```

### Verify Mock Calls

```python
def test_verify_calls(mock_audio_capture):
    mock_audio_capture.list_devices()
    mock_audio_capture.start_recording()
    
    # Verify called
    assert mock_audio_capture.list_devices.called
    assert mock_audio_capture.start_recording.called
    
    # Verify call count
    assert mock_audio_capture.list_devices.call_count == 1
    
    # Verify called with args
    mock_audio_capture.list_devices.assert_called_once()
    mock_audio_capture.start_recording.assert_called_once_with()
```

## Environment Variables for Testing

Tests automatically handle:
- **DISPLAY**: Mocked to `:99` (no real X11 needed)
- **HOME**: Temporary directory (safe file I/O)
- **Audio devices**: Mocked (no hardware needed)
- **Keyboard input**: Mocked (no actual key presses)

## Debugging Tests

### Run with Verbose Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Drop into Debugger

```python
def test_something():
    import pdb; pdb.set_trace()
    # Or with Python 3.7+:
    breakpoint()
```

### Show Full Diff

```bash
pytest -vv --tb=long
```

## Common Issues

### "ImportError: No module named 'Xlib'"

This is expected in headless environments. Tests use mocks to avoid needing Xlib.

### Tests Hanging

Tests have a 300-second timeout. If a test hangs:

```bash
pytest --timeout=10  # 10 second timeout
```

### Mock Not Working

Ensure fixtures are passed as parameters:

```python
def test_something(mock_audio_capture):  # ← fixture parameter
    mock_audio_capture.list_devices()
```

## Adding New Tests

1. Create test file in appropriate directory: `tests/unit/test_module.py`
2. Import fixtures from conftest.py
3. Use appropriate markers: `@pytest.mark.unit`
4. Follow naming convention: `test_function_name`
5. Add docstrings to tests
6. Run tests to verify: `pytest tests/unit/test_module.py -v`

## Performance Testing

```bash
# Run performance tests only
pytest tests/performance/ -v

# Profile test execution
pytest --profile

# Generate flame graph
pytest --profile-svg
```

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- ✅ No X11 display required (all mocked)
- ✅ No audio hardware required (all mocked)
- ✅ No actual microphone input (test data used)
- ✅ Tests run in parallel with `-n auto`
- ✅ Full coverage reporting available
- ✅ Fast execution (mocks avoid real I/O)

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest Markers](https://docs.pytest.org/en/stable/example/markers.html)

## Support

For issues with testing:

1. Check test output: `pytest -vv`
2. Review logs: `pytest -s --log-cli-level=DEBUG`
3. Run single test: `pytest tests/unit/test_file.py::test_function -vv`
4. Check fixtures: `pytest --fixtures` (lists all available fixtures)

## License

Same as parent project.
