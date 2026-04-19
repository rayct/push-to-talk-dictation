"""Tests for audio_capture module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
import audio_capture


class TestAudioCapture:
    """Test cases for AudioCapture class."""

    def test_initialization_default_params(self):
        """Test AudioCapture initialization with default parameters."""
        capture = audio_capture.AudioCapture()
        
        assert capture.sample_rate == 16000
        assert capture.channels == 1
        assert capture.device_index is None
        assert capture.duration_seconds == 30
        assert capture.recording is False
        assert capture.audio_data is None

    def test_initialization_custom_params(self):
        """Test AudioCapture initialization with custom parameters."""
        capture = audio_capture.AudioCapture(
            sample_rate=48000,
            channels=2,
            device_index=1,
            duration_seconds=60
        )
        
        assert capture.sample_rate == 48000
        assert capture.channels == 2
        assert capture.device_index == 1
        assert capture.duration_seconds == 60

    def test_list_devices(self):
        """Test listing available audio devices."""
        with patch('sounddevice.query_devices') as mock_query:
            mock_query.return_value = [
                {
                    'name': 'Microphone',
                    'max_input_channels': 2,
                    'default_samplerate': 48000,
                    'max_output_channels': 0,
                },
                {
                    'name': 'Speaker',
                    'max_input_channels': 0,
                    'default_samplerate': 48000,
                    'max_output_channels': 2,
                },
            ]
            
            capture = audio_capture.AudioCapture()
            devices = capture.list_devices()
            
            assert len(devices) > 0
            assert devices[0]['index'] == 0
            assert devices[0]['name'] == 'Microphone'
            assert devices[0]['input_channels'] == 2
            assert devices[0]['sample_rate'] == 48000

    def test_list_devices_filters_output_only(self):
        """Test that list_devices filters out output-only devices."""
        with patch('sounddevice.query_devices') as mock_query:
            mock_query.return_value = [
                {'name': 'Microphone', 'max_input_channels': 2, 'default_samplerate': 48000},
                {'name': 'Speaker', 'max_input_channels': 0, 'default_samplerate': 48000},
            ]
            
            capture = audio_capture.AudioCapture()
            devices = capture.list_devices()
            
            # Speaker device should be filtered out (0 input channels)
            device_names = [d['name'] for d in devices]
            assert 'Speaker' not in device_names
            assert 'Microphone' in device_names

    def test_list_devices_empty(self):
        """Test list_devices when no input devices available."""
        with patch('sounddevice.query_devices') as mock_query:
            mock_query.return_value = [
                {'name': 'Speaker', 'max_input_channels': 0, 'default_samplerate': 48000}
            ]
            capture = audio_capture.AudioCapture()
            devices = capture.list_devices()
            
            assert devices == []

    def test_start_recording_success(self):
        """Test successfully starting a recording."""
        with patch('sounddevice.rec') as mock_rec:
            import time
            mock_rec.return_value = np.random.randn(16000)
            
            capture = audio_capture.AudioCapture(duration_seconds=1)
            capture.start_recording()
            
            # Give thread time to start
            time.sleep(0.05)
            
            assert hasattr(capture, 'record_thread')

    def test_start_recording_already_recording(self):
        """Test that starting recording when already recording is a no-op."""
        capture = audio_capture.AudioCapture(duration_seconds=1)
        capture.recording = True
        
        capture.start_recording()
        
        assert capture.recording is True

    def test_start_recording_creates_thread(self):
        """Test that start_recording creates a daemon thread."""
        with patch('sounddevice.rec') as mock_rec:
            mock_rec.return_value = np.random.randn(16000)
            
            capture = audio_capture.AudioCapture(duration_seconds=1)
            capture.start_recording()
            
            assert hasattr(capture, 'record_thread')
            assert capture.record_thread.daemon is True

    def test_stop_recording_not_recording(self):
        """Test stop_recording when not recording."""
        capture = audio_capture.AudioCapture()
        result = capture.stop_recording()
        
        assert result == b''
        assert capture.recording is False

    def test_stop_recording_with_audio_data(self):
        """Test stop_recording returns audio bytes."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        
        capture = audio_capture.AudioCapture(duration_seconds=1)
        capture.recording = True
        capture.audio_data = sample_audio
        
        result = capture.stop_recording()
        
        assert result != b''
        assert len(result) > 0
        assert capture.recording is False

    def test_stop_recording_empty_audio_data(self):
        """Test stop_recording with no audio data."""
        capture = audio_capture.AudioCapture()
        capture.recording = True
        capture.audio_data = None
        
        result = capture.stop_recording()
        
        assert result == b''

    def test_stop_recording_empty_array(self):
        """Test stop_recording with empty audio array."""
        capture = audio_capture.AudioCapture()
        capture.recording = True
        capture.audio_data = np.array([])
        
        result = capture.stop_recording()
        
        assert result == b''

    def test_audio_data_conversion_to_bytes(self):
        """Test that audio data is correctly converted to bytes."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        
        capture = audio_capture.AudioCapture(duration_seconds=1)
        capture.recording = True
        capture.audio_data = sample_audio
        
        result = capture.stop_recording()
        
        # Verify we can convert back
        recovered = np.frombuffer(result, dtype=np.float32)
        assert len(recovered) == len(sample_audio)

    def test_cleanup_stops_recording(self):
        """Test cleanup stops recording and waits for thread."""
        with patch('sounddevice.rec') as mock_rec:
            mock_rec.return_value = np.random.randn(16000)
            
            capture = audio_capture.AudioCapture(duration_seconds=1)
            capture.start_recording()
            
            capture.cleanup()
            
            assert capture.recording is False

    def test_cleanup_no_thread(self):
        """Test cleanup when no thread exists."""
        capture = audio_capture.AudioCapture()
        
        # Should not raise
        capture.cleanup()
        assert capture.recording is False

    def test_cleanup_with_exception_handling(self):
        """Test cleanup handles exceptions gracefully."""
        capture = audio_capture.AudioCapture()
        capture.recording = True
        
        # Should handle exceptions during cleanup
        capture.cleanup()

    def test_start_recording_with_device_index(self):
        """Test start_recording uses specified device index."""
        with patch('sounddevice.rec') as mock_rec:
            mock_rec.return_value = np.random.randn(16000)
            
            capture = audio_capture.AudioCapture(device_index=1, duration_seconds=1)
            capture.start_recording()
            
            # Wait a bit for thread to call rec
            import time
            time.sleep(0.1)

    def test_recording_thread_exception_handling(self):
        """Test that recording thread handles exceptions."""
        with patch('sounddevice.rec') as mock_rec:
            mock_rec.side_effect = Exception("Recording failed")
            
            capture = audio_capture.AudioCapture(duration_seconds=1)
            capture.start_recording()
            
            # Wait for thread to fail
            import time
            time.sleep(0.2)
            
            assert capture.recording is False

    def test_recording_context_usage(self):
        """Test typical recording workflow."""
        mock_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        
        with patch('sounddevice.rec') as mock_rec:
            mock_rec.return_value = mock_audio
            
            capture = audio_capture.AudioCapture(duration_seconds=1)
            capture.start_recording()
            
            import time
            time.sleep(0.3)  # Give thread time to complete
            
            audio_bytes = capture.stop_recording()
            
            # Should have some audio data
            assert isinstance(audio_bytes, bytes)
            assert capture.recording is False
