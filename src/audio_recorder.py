"""
Audio recording functionality for SpeechTide.
Handles microphone input, audio processing, and recording management.
"""

import pyaudio
import wave
import numpy as np
import threading
import time
import io
import logging
from typing import Optional, Callable, Dict, Any


class AudioRecorder:
    """Handles audio recording and basic processing."""
    
    def __init__(self, audio_config: Dict[str, Any]):
        """Initialize audio recorder.
        
        Args:
            audio_config: Audio configuration dictionary
        """
        self.config = audio_config
        self.sample_rate = audio_config['sample_rate']
        self.channels = audio_config['channels']
        self.chunk_size = audio_config['chunk_size']
        
        # Initialize logger first to avoid destructor issues
        self.logger = logging.getLogger(__name__)
        
        # Map format strings to pyaudio constants
        format_mapping = {
            'int16': pyaudio.paInt16,
            'int24': pyaudio.paInt24,
            'int32': pyaudio.paInt32,
            'float32': pyaudio.paFloat32,
            'uint8': pyaudio.paUInt8
        }
        
        format_str = audio_config.get('format', 'int16').lower()
        if format_str in format_mapping:
            self.format = format_mapping[format_str]
        else:
            self.logger.warning(f"Unknown audio format '{format_str}', defaulting to paInt16")
            self.format = pyaudio.paInt16
        
        # Recording state
        self.is_recording = False
        self.audio_data = []
        self.audio_stream: Optional[pyaudio.Stream] = None
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        
        # Audio level monitoring
        self.current_volume = 0.0
        self.volume_callback: Optional[Callable[[float], None]] = None
        
        # Initialize PyAudio
        self._init_audio()
    
    def _init_audio(self) -> None:
        """Initialize PyAudio instance."""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # Find default input device
            default_device = self.pyaudio_instance.get_default_input_device_info()
            self.logger.info(f"Default audio input device: {default_device['name']}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize audio: {e}")
            raise
    
    def start_recording(self) -> None:
        """Start audio recording."""
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return
        
        try:
            self.audio_data = []
            self.is_recording = True
            
            # Open audio stream
            self.audio_stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.audio_stream.start_stream()
            self.logger.info("Audio recording started")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            raise
    
    def stop_recording(self) -> bytes:
        """Stop audio recording and return recorded data.
        
        Returns:
            Recorded audio data as WAV bytes
        """
        if not self.is_recording:
            self.logger.warning("No recording in progress")
            return b""
        
        try:
            self.is_recording = False
            
            # Stop and close audio stream
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            # Convert recorded data to WAV format
            if self.audio_data:
                wav_data = self._create_wav_data()
                self.logger.info(f"Recording stopped, {len(wav_data)} bytes recorded")
                return wav_data
            else:
                self.logger.warning("No audio data recorded")
                return b""
                
        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return b""
    
    def _audio_callback(self, in_data: bytes, frame_count: int, 
                       time_info: Dict, status_flags: int) -> tuple:
        """PyAudio callback for processing audio frames.
        
        Args:
            in_data: Input audio data
            frame_count: Number of frames
            time_info: Timing information
            status_flags: Status flags
            
        Returns:
            Tuple of (output_data, continue_flag)
        """
        if self.is_recording:
            # Store audio data
            self.audio_data.append(in_data)
            
            # Calculate volume level for visualization
            audio_array = np.frombuffer(in_data, dtype=np.int16)
            if len(audio_array) > 0:
                # Handle potential invalid values in audio data
                audio_squared = audio_array.astype(np.float64) ** 2
                mean_val = np.mean(audio_squared)
                if np.isfinite(mean_val) and mean_val >= 0:
                    volume = np.sqrt(mean_val)
                else:
                    volume = 0.0
                self.current_volume = volume / 32768.0  # Normalize to 0-1
            else:
                self.current_volume = 0.0
            
            # Notify volume callback if set
            if self.volume_callback:
                try:
                    self.volume_callback(self.current_volume)
                except Exception as e:
                    self.logger.error(f"Error in volume callback: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def _create_wav_data(self) -> bytes:
        """Create WAV file data from recorded audio chunks.
        
        Returns:
            WAV file data as bytes
        """
        try:
            # Combine all audio chunks
            audio_bytes = b''.join(self.audio_data)
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.pyaudio_instance.get_sample_size(self.format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_bytes)
            
            wav_buffer.seek(0)
            return wav_buffer.read()
            
        except Exception as e:
            self.logger.error(f"Failed to create WAV data: {e}")
            return b""
    
    def get_current_volume(self) -> float:
        """Get current audio volume level.
        
        Returns:
            Volume level between 0.0 and 1.0
        """
        return self.current_volume
    
    def set_volume_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for volume level updates.
        
        Args:
            callback: Function to call with volume level (0.0 to 1.0)
        """
        self.volume_callback = callback
    
    def test_microphone(self) -> bool:
        """Test microphone functionality.
        
        Returns:
            True if microphone is working, False otherwise
        """
        try:
            # Try to open a stream briefly
            test_stream = self.pyaudio_instance.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            # Record for a short time
            test_data = test_stream.read(self.chunk_size)
            test_stream.close()
            
            # Check if we got data
            if len(test_data) > 0:
                audio_array = np.frombuffer(test_data, dtype=np.int16)
                # Check if there's some variation in the signal (not just zeros)
                has_signal = np.std(audio_array) > 0
                self.logger.info(f"Microphone test: {'passed' if has_signal else 'no signal detected'}")
                return has_signal
            
            return False
            
        except Exception as e:
            self.logger.error(f"Microphone test failed: {e}")
            return False
    
    def get_input_devices(self) -> list:
        """Get list of available audio input devices.
        
        Returns:
            List of device information dictionaries
        """
        devices = []
        try:
            for i in range(self.pyaudio_instance.get_device_count()):
                device_info = self.pyaudio_instance.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
        except Exception as e:
            self.logger.error(f"Failed to get input devices: {e}")
        
        return devices
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        try:
            if self.is_recording:
                self.stop_recording()
            
            if self.audio_stream:
                self.audio_stream.close()
                self.audio_stream = None
            
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
            
            self.logger.info("Audio resources cleaned up")
            
        except Exception as e:
            self.logger.error(f"Error during audio cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            self.cleanup()
        except Exception:
            # Silently handle cleanup errors in destructor
            pass