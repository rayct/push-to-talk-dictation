"""
Transcription module using OpenAI Whisper.
"""

import whisper
import numpy as np
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """Transcribe audio using OpenAI Whisper."""

    def __init__(self, model: str = "base", device: str = "cpu"):
        self.model_name = model
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load Whisper model."""
        try:
            logger.info(f"Loading Whisper model '{self.model_name}'...")
            
            # Set model cache directory
            cache_dir = Path.home() / '.cache' / 'whisper'
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"Whisper model '{self.model_name}' loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio_bytes: bytes) -> Optional[str]:
        """
        Transcribe audio bytes to text.
        
        Args:
            audio_bytes: Raw audio data (float32 or int16)
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if not self.model:
            logger.error("Model not loaded")
            return None

        try:
            # Convert bytes to numpy array (assuming float32)
            audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
            
            if len(audio_data) == 0:
                logger.warning("Empty audio data")
                return None
            
            logger.info(f"Transcribing {len(audio_data)} samples...")
            
            result = self.model.transcribe(
                audio_data,
                language="en",
                verbose=False
            )
            
            text = result.get("text", "").strip()
            logger.info(f"Transcription complete: '{text}'")
            
            return text if text else None
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def cleanup(self):
        """Clean up resources."""
        if self.model:
            del self.model
            self.model = None
