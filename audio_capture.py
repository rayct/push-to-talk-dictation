"""
Audio capture module for recording microphone input using sounddevice.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
from threading import Thread, Event
from queue import Queue
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """Capture audio from microphone using sounddevice."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1, 
                 device_index: int = None, duration_seconds: int = 30):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.duration_seconds = duration_seconds
        
        self.stream = None
        self.recording = False
        self.audio_data = None
        
    def list_devices(self):
        """List available audio devices."""
        devices = sd.query_devices()
        audio_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                audio_devices.append({
                    'index': i,
                    'name': device['name'],
                    'input_channels': device['max_input_channels'],
                    'sample_rate': int(device['default_samplerate'])
                })
        return audio_devices

    def start_recording(self):
        """Start recording audio."""
        if self.recording:
            logger.warning("Already recording")
            return

        try:
            logger.info(f"Starting audio recording at {self.sample_rate}Hz...")
            self.audio_data = []
            self.recording = True
            
            # Use blocking recording in a thread
            def record_thread():
                try:
                    audio = sd.rec(int(self.sample_rate * self.duration_seconds),
                                   samplerate=self.sample_rate,
                                   channels=self.channels,
                                   device=self.device_index,
                                   blocking=True)
                    self.audio_data = audio
                except Exception as e:
                    logger.error(f"Recording error: {e}")
                finally:
                    self.recording = False
            
            self.record_thread = Thread(target=record_thread, daemon=True)
            self.record_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.recording = False
            raise

    def stop_recording(self) -> bytes:
        """Stop recording and return audio data."""
        if not self.recording:
            logger.warning("Not recording")
            return b''

        try:
            self.recording = False
            
            # Wait for recording thread to finish
            if hasattr(self, 'record_thread'):
                self.record_thread.join(timeout=2)
            
            if self.audio_data is not None and len(self.audio_data) > 0:
                # Convert numpy array to bytes
                audio_float32 = np.float32(self.audio_data)
                audio_bytes = audio_float32.tobytes()
                logger.info(f"Recording stopped ({len(audio_bytes)} bytes)")
                return audio_bytes
            else:
                logger.warning("No audio data captured")
                return b''
                
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return b''

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.recording:
                self.recording = False
                if hasattr(self, 'record_thread'):
                    self.record_thread.join(timeout=1)
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
