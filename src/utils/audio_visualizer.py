"""
Audio visualization utilities for SpeechTide.
Provides real-time audio waveform and volume level visualization.
"""

import numpy as np
import logging
from typing import List, Tuple, Optional
import threading
import time


class AudioVisualizer:
    """Real-time audio visualization for voice input feedback."""
    
    def __init__(self, sample_rate: int = 16000, buffer_size: int = 1024):
        """Initialize audio visualizer.
        
        Args:
            sample_rate: Audio sample rate
            buffer_size: Size of audio buffer for processing
        """
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.logger = logging.getLogger(__name__)
        
        # Visualization data
        self.volume_history = []
        self.max_history_length = 100
        self.current_volume = 0.0
        self.peak_volume = 0.0
        
        # Waveform data
        self.waveform_data = np.zeros(buffer_size)
        self.frequency_data = np.zeros(buffer_size // 2)
        
        # Smoothing parameters
        self.volume_smoothing = 0.8  # Exponential smoothing factor
        self.peak_decay = 0.95       # Peak hold decay rate
        
        self.logger.info("AudioVisualizer initialized")
    
    def process_audio_chunk(self, audio_data: bytes) -> None:
        """Process an audio chunk for visualization.
        
        Args:
            audio_data: Raw audio data
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return
            
            # Normalize to [-1, 1]
            normalized_audio = audio_array.astype(np.float32) / 32768.0
            
            # Calculate volume (RMS)
            rms_volume = np.sqrt(np.mean(normalized_audio**2))
            
            # Smooth volume changes
            self.current_volume = (self.volume_smoothing * self.current_volume + 
                                 (1 - self.volume_smoothing) * rms_volume)
            
            # Update peak with decay
            if self.current_volume > self.peak_volume:
                self.peak_volume = self.current_volume
            else:
                self.peak_volume *= self.peak_decay
            
            # Store volume history
            self.volume_history.append(self.current_volume)
            if len(self.volume_history) > self.max_history_length:
                self.volume_history.pop(0)
            
            # Store waveform data (resample if necessary)
            if len(normalized_audio) >= self.buffer_size:
                self.waveform_data = normalized_audio[:self.buffer_size]
            else:
                # Pad or repeat data to fill buffer
                padded_audio = np.resize(normalized_audio, self.buffer_size)
                self.waveform_data = padded_audio
            
            # Calculate frequency spectrum (FFT)
            self._calculate_frequency_spectrum()
            
        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
    
    def _calculate_frequency_spectrum(self) -> None:
        """Calculate frequency spectrum from waveform data."""
        try:
            # Apply windowing to reduce spectral leakage
            windowed_data = self.waveform_data * np.hanning(len(self.waveform_data))
            
            # Calculate FFT
            fft_data = np.fft.rfft(windowed_data)
            
            # Calculate magnitude spectrum
            magnitude_spectrum = np.abs(fft_data)
            
            # Convert to dB scale with floor
            db_spectrum = 20 * np.log10(magnitude_spectrum + 1e-10)
            
            # Normalize to [0, 1] range
            self.frequency_data = np.clip((db_spectrum + 100) / 100, 0, 1)
            
        except Exception as e:
            self.logger.debug(f"Error calculating frequency spectrum: {e}")
    
    def get_volume_level(self) -> float:
        """Get current volume level.
        
        Returns:
            Current volume level (0.0 to 1.0)
        """
        return min(self.current_volume, 1.0)
    
    def get_peak_level(self) -> float:
        """Get peak volume level.
        
        Returns:
            Peak volume level (0.0 to 1.0)
        """
        return min(self.peak_volume, 1.0)
    
    def get_volume_history(self, length: Optional[int] = None) -> List[float]:
        """Get volume history for visualization.
        
        Args:
            length: Number of recent samples to return (None for all)
            
        Returns:
            List of volume levels
        """
        if length is None:
            return self.volume_history.copy()
        else:
            return self.volume_history[-length:] if len(self.volume_history) >= length else self.volume_history.copy()
    
    def get_waveform_data(self) -> np.ndarray:
        """Get current waveform data.
        
        Returns:
            Waveform data as numpy array
        """
        return self.waveform_data.copy()
    
    def get_frequency_data(self) -> np.ndarray:
        """Get frequency spectrum data.
        
        Returns:
            Frequency spectrum as numpy array
        """
        return self.frequency_data.copy()
    
    def get_visualization_bars(self, num_bars: int = 20) -> List[float]:
        """Get frequency data as bars for visualization.
        
        Args:
            num_bars: Number of frequency bars to return
            
        Returns:
            List of bar heights (0.0 to 1.0)
        """
        try:
            if len(self.frequency_data) == 0:
                return [0.0] * num_bars
            
            # Group frequency bins into bars
            bins_per_bar = len(self.frequency_data) // num_bars
            if bins_per_bar == 0:
                bins_per_bar = 1
            
            bars = []
            for i in range(num_bars):
                start_idx = i * bins_per_bar
                end_idx = min((i + 1) * bins_per_bar, len(self.frequency_data))
                
                if start_idx < len(self.frequency_data):
                    bar_value = np.mean(self.frequency_data[start_idx:end_idx])
                    bars.append(float(bar_value))
                else:
                    bars.append(0.0)
            
            return bars
            
        except Exception as e:
            self.logger.error(f"Error generating visualization bars: {e}")
            return [0.0] * num_bars
    
    def is_speech_detected(self, threshold: float = 0.01) -> bool:
        """Detect if speech is present in current audio.
        
        Args:
            threshold: Volume threshold for speech detection
            
        Returns:
            True if speech is detected, False otherwise
        """
        return self.current_volume > threshold
    
    def get_speech_confidence(self) -> float:
        """Get confidence level for speech detection.
        
        Returns:
            Speech confidence (0.0 to 1.0)
        """
        # Simple heuristic based on volume consistency
        if len(self.volume_history) < 10:
            return 0.0
        
        recent_volumes = self.volume_history[-10:]
        avg_volume = np.mean(recent_volumes)
        volume_stability = 1.0 - (np.std(recent_volumes) / (avg_volume + 1e-6))
        
        # Combine volume level and stability
        confidence = min(avg_volume * 10, 1.0) * volume_stability
        return max(0.0, min(confidence, 1.0))
    
    def reset(self) -> None:
        """Reset visualization data."""
        self.volume_history.clear()
        self.current_volume = 0.0
        self.peak_volume = 0.0
        self.waveform_data.fill(0.0)
        self.frequency_data.fill(0.0)
        self.logger.debug("Audio visualizer reset")
    
    def set_smoothing(self, volume_smoothing: float, peak_decay: float) -> None:
        """Set smoothing parameters.
        
        Args:
            volume_smoothing: Volume smoothing factor (0.0 to 1.0)
            peak_decay: Peak decay rate (0.0 to 1.0)
        """
        self.volume_smoothing = max(0.0, min(1.0, volume_smoothing))
        self.peak_decay = max(0.0, min(1.0, peak_decay))
        self.logger.info(f"Smoothing parameters updated: volume={self.volume_smoothing}, peak_decay={self.peak_decay}")


class WaveformGenerator:
    """Generates smooth waveform visualizations for display."""
    
    def __init__(self, width: int = 400, height: int = 100):
        """Initialize waveform generator.
        
        Args:
            width: Width of generated waveform in pixels
            height: Height of generated waveform in pixels
        """
        self.width = width
        self.height = height
        self.logger = logging.getLogger(__name__)
        
    def generate_volume_wave(self, volume_history: List[float], 
                           wave_type: str = "smooth") -> List[Tuple[int, int]]:
        """Generate waveform points from volume history.
        
        Args:
            volume_history: List of volume levels
            wave_type: Type of wave ("smooth", "bars", "line")
            
        Returns:
            List of (x, y) coordinate tuples
        """
        if not volume_history:
            return [(x, self.height // 2) for x in range(0, self.width, 10)]
        
        if wave_type == "smooth":
            return self._generate_smooth_wave(volume_history)
        elif wave_type == "bars":
            return self._generate_bar_wave(volume_history)
        else:
            return self._generate_line_wave(volume_history)
    
    def _generate_smooth_wave(self, volume_history: List[float]) -> List[Tuple[int, int]]:
        """Generate smooth waveform with interpolation.
        
        Args:
            volume_history: Volume level history
            
        Returns:
            List of coordinate points
        """
        points = []
        center_y = self.height // 2
        
        # Interpolate volume history to match width
        if len(volume_history) < self.width // 2:
            # Extend data by repeating last values
            extended_history = volume_history + [volume_history[-1]] * (self.width // 2 - len(volume_history))
        else:
            # Downsample data
            step = len(volume_history) / (self.width // 2)
            extended_history = [volume_history[int(i * step)] for i in range(self.width // 2)]
        
        # Generate wave points
        for i, volume in enumerate(extended_history):
            x = int((i / len(extended_history)) * self.width)
            
            # Create wave amplitude based on volume
            amplitude = volume * (self.height // 3)
            
            # Add some wave motion for visual appeal
            phase = (i / len(extended_history)) * 2 * np.pi * 3
            wave_offset = np.sin(phase) * amplitude * 0.3
            
            y = center_y + int(amplitude * np.sin(i * 0.2) + wave_offset)
            y = max(0, min(self.height - 1, y))
            
            points.append((x, y))
        
        return points
    
    def _generate_bar_wave(self, volume_history: List[float]) -> List[Tuple[int, int]]:
        """Generate bar-style waveform.
        
        Args:
            volume_history: Volume level history
            
        Returns:
            List of coordinate points (bar tops)
        """
        points = []
        num_bars = min(20, self.width // 10)
        bar_width = self.width // num_bars
        
        # Group volume history into bars
        if len(volume_history) < num_bars:
            bar_volumes = volume_history + [0.0] * (num_bars - len(volume_history))
        else:
            step = len(volume_history) / num_bars
            bar_volumes = [volume_history[int(i * step)] for i in range(num_bars)]
        
        for i, volume in enumerate(bar_volumes):
            x = i * bar_width + bar_width // 2
            bar_height = int(volume * self.height * 0.8)
            y = self.height - bar_height
            
            points.append((x, y))
        
        return points
    
    def _generate_line_wave(self, volume_history: List[float]) -> List[Tuple[int, int]]:
        """Generate simple line waveform.
        
        Args:
            volume_history: Volume level history
            
        Returns:
            List of coordinate points
        """
        points = []
        
        for i, volume in enumerate(volume_history):
            x = int((i / len(volume_history)) * self.width)
            y = int((1.0 - volume) * self.height)
            y = max(0, min(self.height - 1, y))
            
            points.append((x, y))
        
        return points
    
    def generate_spectrum_bars(self, frequency_data: np.ndarray, 
                             num_bars: int = 20) -> List[Tuple[int, int, int]]:
        """Generate frequency spectrum bars.
        
        Args:
            frequency_data: Frequency spectrum data
            num_bars: Number of bars to generate
            
        Returns:
            List of (x, y, width) tuples for bars
        """
        bars = []
        bar_width = self.width // num_bars
        
        # Group frequency data into bars
        if len(frequency_data) < num_bars:
            bar_values = list(frequency_data) + [0.0] * (num_bars - len(frequency_data))
        else:
            step = len(frequency_data) / num_bars
            bar_values = [frequency_data[int(i * step)] for i in range(num_bars)]
        
        for i, value in enumerate(bar_values):
            x = i * bar_width
            bar_height = int(value * self.height * 0.9)
            y = self.height - bar_height
            
            bars.append((x, y, bar_width - 2))  # -2 for spacing
        
        return bars