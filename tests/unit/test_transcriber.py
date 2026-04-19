"""Tests for transcriber module."""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import transcriber


class TestWhisperTranscriber:
    """Test cases for WhisperTranscriber class."""

    def test_initialization_default_params(self):
        """Test WhisperTranscriber initialization with default parameters."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            
            assert transcriber_obj.model_name == "base"
            assert transcriber_obj.device == "cpu"
            assert transcriber_obj.model is not None

    def test_initialization_custom_params(self):
        """Test WhisperTranscriber initialization with custom parameters."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber(model="tiny", device="cuda")
            
            assert transcriber_obj.model_name == "tiny"
            assert transcriber_obj.device == "cuda"

    def test_model_loading_success(self):
        """Test successful model loading."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            
            assert transcriber_obj.model is not None

    def test_model_loading_with_different_models(self):
        """Test loading different model sizes."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            for model_name in ["tiny", "base", "small"]:
                transcriber_obj = transcriber.WhisperTranscriber(model=model_name)
                assert transcriber_obj.model is not None

    def test_model_loading_failure_raises_exception(self):
        """Test that model loading failure raises an exception."""
        with patch('whisper.load_model') as mock_load:
            mock_load.side_effect = Exception("Model not found")
            
            with pytest.raises(Exception):
                transcriber.WhisperTranscriber()

    def test_transcribe_success(self):
        """Test successful transcription."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {'text': 'This is a test transcription.'}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result == "This is a test transcription."

    def test_transcribe_returns_string(self):
        """Test that transcribe returns a string."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {'text': 'Test'}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert isinstance(result, str)

    def test_transcribe_empty_audio_returns_none(self):
        """Test transcription with empty audio returns None."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(b'')
            
            assert result is None

    def test_transcribe_empty_result_returns_none(self):
        """Test transcription when model returns empty string."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {'text': '   '}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result is None

    def test_transcribe_strips_whitespace(self):
        """Test that transcribe strips leading/trailing whitespace."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {'text': '  test text  '}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result == "test text"

    def test_transcribe_calls_model_with_english(self):
        """Test that transcribe specifies English language."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {'text': 'Test'}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            transcriber_obj.transcribe(audio_bytes)
            
            # Verify model.transcribe was called with language parameter
            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs.get('language') == 'en'

    def test_transcribe_exception_handling(self):
        """Test transcription error handling."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.side_effect = Exception("Transcription failed")
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result is None

    def test_cleanup_deletes_model(self):
        """Test cleanup removes model from memory."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            assert transcriber_obj.model is not None
            
            transcriber_obj.cleanup()
            
            assert transcriber_obj.model is None

    def test_cleanup_multiple_times(self):
        """Test cleanup can be called multiple times safely."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            
            transcriber_obj.cleanup()
            transcriber_obj.cleanup()
            transcriber_obj.cleanup()
            
            assert transcriber_obj.model is None

    def test_transcribe_after_cleanup_returns_none(self):
        """Test that transcribe returns None after cleanup."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            transcriber_obj.cleanup()
            
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result is None

    def test_concurrent_initialization(self):
        """Test multiple transcriber instances can be created."""
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_load.return_value = mock_model
            
            transcriber1 = transcriber.WhisperTranscriber()
            transcriber2 = transcriber.WhisperTranscriber()
            
            assert transcriber1.model is not None
            assert transcriber2.model is not None
            assert transcriber1 is not transcriber2

    def test_transcribe_preserves_punctuation(self):
        """Test that transcribed text preserves punctuation."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {'text': 'Hello, world!'}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result == "Hello, world!"

    def test_transcribe_with_missing_text_key(self):
        """Test transcription when model response is missing 'text' key."""
        sample_audio = np.sin(np.linspace(0, 2*np.pi, 16000)).astype(np.float32)
        audio_bytes = sample_audio.tobytes()
        
        with patch('whisper.load_model') as mock_load:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {}
            mock_load.return_value = mock_model
            
            transcriber_obj = transcriber.WhisperTranscriber()
            result = transcriber_obj.transcribe(audio_bytes)
            
            assert result is None
