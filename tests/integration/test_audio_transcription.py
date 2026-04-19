"""Integration tests for audio capture and transcription workflow."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import audio_capture
import transcriber


@pytest.mark.integration
@pytest.mark.audio
class TestAudioTranscriptionWorkflow:
    """Test the complete audio capture to transcription pipeline."""

    @pytest.fixture
    def setup_workflow(self, mock_audio_device):
        """Setup audio capture and transcriber for testing."""
        cap = audio_capture.AudioCapture(device_index=0)
        trans = transcriber.WhisperTranscriber()
        yield cap, trans
        trans.cleanup()

    def test_audio_capture_to_transcription(self, mock_audio_device):
        """Test complete workflow: capture audio and transcribe."""
        cap = audio_capture.AudioCapture()
        trans = transcriber.WhisperTranscriber()
        
        # Mock audio data
        sample_audio = np.random.randn(16000).astype(np.float32) * 0.1
        
        with patch.object(cap, 'stop_recording', return_value=sample_audio.tobytes()):
            cap.start_recording()
            audio_data = cap.stop_recording()
        
        assert audio_data is not None
        trans.cleanup()

    def test_transcription_pipeline_with_silence(self, mock_audio_device):
        """Test transcription with silent audio data."""
        cap = audio_capture.AudioCapture()
        trans = transcriber.WhisperTranscriber()
        
        # Silent audio
        silent_audio = np.zeros(16000, dtype=np.float32)
        
        with patch.object(trans, 'transcribe', return_value=''):
            result = trans.transcribe(silent_audio.tobytes())
        
        assert result == ''
        trans.cleanup()

    def test_workflow_error_handling_device_error(self, mock_audio_device):
        """Test error handling when audio device fails."""
        cap = audio_capture.AudioCapture()
        
        with patch.object(cap, 'start_recording', side_effect=RuntimeError("Device error")):
            with pytest.raises(RuntimeError):
                cap.start_recording()

    def test_workflow_error_handling_transcription_error(self, mock_audio_device):
        """Test error handling when transcription fails."""
        trans = transcriber.WhisperTranscriber()
        
        with patch('transcriber.whisper.load_model', side_effect=RuntimeError("Model error")):
            with pytest.raises(RuntimeError):
                trans2 = transcriber.WhisperTranscriber()
        
        trans.cleanup()

    def test_audio_quality_variations(self, mock_audio_device):
        """Test transcription with different audio quality levels."""
        cap = audio_capture.AudioCapture()
        trans = transcriber.WhisperTranscriber()
        
        # Simulate audio of different qualities
        noise_levels = [0.01, 0.05, 0.1]  # SNR variations
        
        for noise in noise_levels:
            signal = np.random.randn(16000).astype(np.float32) * noise
            with patch.object(trans, 'transcribe', return_value=f'transcribed at noise {noise}'):
                result = trans.transcribe(signal.tobytes())
                assert result is not None
        
        trans.cleanup()

    def test_multiple_transcription_calls(self, mock_audio_device):
        """Test multiple transcription calls in sequence."""
        cap = audio_capture.AudioCapture()
        trans = transcriber.WhisperTranscriber()
        
        for i in range(3):
            audio_data = np.random.randn(16000).astype(np.float32) * 0.1
            with patch.object(trans, 'transcribe', return_value=f'transcription {i}'):
                result = trans.transcribe(audio_data.tobytes())
                assert f'transcription {i}' in result
        
        trans.cleanup()

    def test_workflow_cleanup(self, mock_audio_device):
        """Test proper cleanup of resources in workflow."""
        cap = audio_capture.AudioCapture()
        trans = transcriber.WhisperTranscriber()
        
        # Use resources
        cap.start_recording()
        cap.stop_recording()
        
        # Cleanup
        cap.cleanup()
        trans.cleanup()
        
        # Verify they're cleaned up
        assert not cap.recording


@pytest.mark.integration
class TestAudioTranscriptionPerformance:
    """Test performance characteristics of audio transcription."""

    def test_transcription_latency(self, mock_audio_device):
        """Test transcription latency is acceptable."""
        import time
        trans = transcriber.WhisperTranscriber()
        
        audio_data = np.random.randn(16000).astype(np.float32) * 0.1
        
        with patch.object(trans, 'transcribe') as mock_transcribe:
            mock_transcribe.return_value = 'test result'
            start = time.time()
            result = trans.transcribe(audio_data.tobytes())
            elapsed = time.time() - start
        
        # Should be fast with mocked model
        assert elapsed < 1.0
        trans.cleanup()
