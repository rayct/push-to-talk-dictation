"""
Audio capture module for recording microphone input.
"""

import pyaudio
import numpy as np
from threading import Thread, Event
from queue import Queue
import logging

logger = logging.getLogger(__name__)


class AudioCapture:
    """Capture audio from microphone using PyAudio."""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024, 
                 channels: int = 1, device_index: int = None):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.device_index = device_index
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.audio_queue = Queue()
        
    def list_devices(self):
        """List available audio devices."""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            devices.append({
                'index': i,
                'name': info['name'],
                'input_channels': info['maxInputChannels'],
                'sample_rate': int(info['defaultSampleRate'])
            })
        return devices

    def start_recording(self) -> Queue:
        """Start recording and return queue of audio chunks."""
        if self.recording:
            logger.warning("Already recording")
            return self.audio_queue

        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.recording = True
            self.stream.start_stream()
            logger.info("Audio recording started")
            return self.audio_queue
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise

    def stop_recording(self) -> bytes:
        """Stop recording and return collected audio data."""
        if not self.recording:
            logger.warning("Not recording")
            return b''

        try:
            self.recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            
            logger.info("Audio recording stopped")
            
            # Collect all audio from queue
            audio_data = b''
            while not self.audio_queue.empty():
                chunk = self.audio_queue.get_nowait()
                if isinstance(chunk, bytes):
                    audio_data += chunk
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return b''

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        if self.recording:
            self.audio_queue.put(in_data)
        
        return (in_data, pyaudio.paContinue)

    def get_audio_frames(self) -> list:
        """Get all recorded audio frames as list."""
        frames = []
        while not self.audio_queue.empty():
            try:
                frames.append(self.audio_queue.get_nowait())
            except:
                break
        return frames

    def cleanup(self):
        """Clean up audio resources."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        try:
            self.audio.terminate()
        except:
            pass
