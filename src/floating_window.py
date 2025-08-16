"""
Floating window for voice input visualization.
Provides real-time feedback during voice recording with wave animation.
"""

import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QProgressBar)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
import numpy as np
import logging
from typing import Dict, Any, Optional, List
import threading


class VoiceVisualizationWidget(QWidget):
    """Custom widget for displaying voice wave animation."""
    
    def __init__(self):
        super().__init__()
        self.setFixedHeight(60)
        self.volume_levels = [0.0] * 50  # Store recent volume levels
        self.current_volume = 0.0
        self.animation_phase = 0.0
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animation)
        self.animation_timer.start(50)  # Update every 50ms (20 FPS)
    
    def update_volume(self, volume: float) -> None:
        """Update current volume level.
        
        Args:
            volume: Volume level between 0.0 and 1.0
        """
        self.current_volume = max(0.0, min(1.0, volume))
        
        # Shift volume levels and add new one
        self.volume_levels = self.volume_levels[1:] + [self.current_volume]
        
        self.update()  # Trigger repaint
    
    def _update_animation(self) -> None:
        """Update animation phase for smooth wave motion."""
        self.animation_phase += 0.2
        if self.animation_phase > 2 * np.pi:
            self.animation_phase = 0.0
        self.update()
    
    def paintEvent(self, event) -> None:
        """Paint the voice visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(30, 30, 30, 200))
        
        # Draw voice wave
        if any(level > 0.01 for level in self.volume_levels):
            self._draw_wave(painter)
        else:
            self._draw_idle_state(painter)
    
    def _draw_wave(self, painter: QPainter) -> None:
        """Draw animated voice wave visualization.
        
        Args:
            painter: QPainter instance
        """
        width = self.width()
        height = self.height()
        center_y = height // 2
        
        # Set up pen for wave
        pen = QPen(QColor(100, 200, 255, 180))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # Draw multiple wave layers for depth
        for layer in range(3):
            points = []
            layer_opacity = 255 - (layer * 60)
            layer_amplitude = 1.0 - (layer * 0.3)
            
            pen.setColor(QColor(100, 200, 255, layer_opacity))
            painter.setPen(pen)
            
            # Generate wave points
            for i in range(len(self.volume_levels)):
                x = int((i / len(self.volume_levels)) * width)
                
                # Create wave effect
                volume = self.volume_levels[i] * layer_amplitude
                wave_offset = np.sin(self.animation_phase + i * 0.3) * 5
                amplitude = volume * (height // 4) + wave_offset
                
                y = center_y + amplitude * np.sin(i * 0.5 + self.animation_phase)
                points.append((x, int(y)))
            
            # Draw wave line
            if len(points) > 1:
                for i in range(len(points) - 1):
                    painter.drawLine(points[i][0], points[i][1], 
                                   points[i+1][0], points[i+1][1])
        
        # Draw current volume indicator
        current_radius = int(self.current_volume * 20) + 5
        center_x = width - 30
        
        brush = QBrush(QColor(100, 200, 255, 100))
        painter.setBrush(brush)
        painter.setPen(QPen(QColor(100, 200, 255, 200)))
        painter.drawEllipse(center_x - current_radius//2, center_y - current_radius//2, 
                           current_radius, current_radius)
    
    def _draw_idle_state(self, painter: QPainter) -> None:
        """Draw idle state visualization.
        
        Args:
            painter: QPainter instance
        """
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        
        # Draw pulsing circle
        pulse_radius = int(15 + np.sin(self.animation_phase) * 3)
        
        brush = QBrush(QColor(150, 150, 150, 100))
        painter.setBrush(brush)
        painter.setPen(QPen(QColor(150, 150, 150, 150)))
        painter.drawEllipse(center_x - pulse_radius, center_y - pulse_radius,
                           pulse_radius * 2, pulse_radius * 2)
        
        # Draw microphone icon (simple representation)
        painter.setPen(QPen(QColor(200, 200, 200, 200), 2))
        painter.drawRect(center_x - 8, center_y - 12, 16, 20)
        painter.drawLine(center_x, center_y + 8, center_x, center_y + 18)
        painter.drawLine(center_x - 6, center_y + 18, center_x + 6, center_y + 18)


class FloatingWindow(QWidget):
    """Main floating window for voice input interface."""
    
    # Signals
    close_requested = pyqtSignal()
    
    def __init__(self, ui_config: Dict[str, Any]):
        """Initialize floating window.
        
        Args:
            ui_config: UI configuration dictionary
        """
        # Ensure QApplication exists before creating QWidget
        ensure_qt_application()
        
        super().__init__()
        
        self.ui_config = ui_config
        self.logger = logging.getLogger(__name__)
        
        # Window properties
        self.is_visible = False
        self.current_text = ""
        
        # Setup UI
        self._setup_window()
        self._setup_ui()
        self._setup_positioning()
        
        # Volume update timer for smoothing
        self.volume_smoothing_timer = QTimer()
        self.volume_smoothing_timer.timeout.connect(self._update_smooth_volume)
        
        self.logger.info("FloatingWindow initialized")
    
    def _setup_window(self) -> None:
        """Setup window properties."""
        window_config = self.ui_config.get('floating_window', {})
        
        # Window flags for floating behavior - prevent appearing as separate app
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |  # Use Tool window to prevent dock appearance
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, True)
        self.setAttribute(Qt.WidgetAttribute.WA_X11DoNotAcceptFocus, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, False)  # Ensure it's visible but not in dock
        
        # Set window title to prevent showing as "Python"
        self.setWindowTitle("SpeechTide Voice Input")
        
        # Try to set additional macOS-specific properties
        try:
            import platform
            if platform.system() == 'Darwin':
                # Try to set window level to floating panel level
                try:
                    import objc
                    import Cocoa
                    from ctypes import c_void_p
                    # Get the native window handle
                    native_view = self.winId()
                    if native_view:
                        # Set window to floating panel level to prevent dock appearance
                        ns_window = objc.objc_object(c_void_p=native_view)
                        if hasattr(ns_window, 'window'):
                            window = ns_window.window()
                            if window:
                                # NSFloatingWindowLevel = 3
                                window.setLevel_(3)
                                window.setHidesOnDeactivate_(False)
                                window.setCanHide_(False)
                                print("✅ Set floating window to panel level")
                except Exception as e:
                    print(f"⚠️  Could not set window level: {e}")
        except Exception as e:
            self.logger.debug(f"Could not set macOS window properties: {e}")
        
        # Window properties
        width = window_config.get('width', 400)
        height = window_config.get('height', 100)
        opacity = window_config.get('opacity', 0.9)
        
        self.resize(width, height)
        self.setWindowOpacity(opacity)
        
        # Styling
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 220);
                border-radius: 15px;
                border: 1px solid rgba(100, 200, 255, 100);
            }
            QLabel {
                color: white;
                font-size: 14px;
                background: transparent;
                padding: 5px;
            }
            QPushButton {
                background-color: rgba(100, 200, 255, 150);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(100, 200, 255, 200);
            }
            QPushButton:pressed {
                background-color: rgba(80, 180, 235, 200);
            }
        """)
    
    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(5)
        
        # Status label
        self.status_label = QLabel("🎤 Listening...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("SF Pro Text", 12))
        layout.addWidget(self.status_label)
        
        # Voice visualization
        self.voice_widget = VoiceVisualizationWidget()
        layout.addWidget(self.voice_widget)
        
        # Real-time text display (for real-time mode)
        self.text_label = QLabel("")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setFont(QFont("SF Pro Text", 11))
        self.text_label.setStyleSheet("color: rgba(255, 255, 255, 180);")
        self.text_label.setWordWrap(True)
        self.text_label.hide()  # Hidden by default
        layout.addWidget(self.text_label)
        
        # Control buttons (hidden by default, shown on hover)
        button_layout = QHBoxLayout()
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.hide()
        
        button_layout.addStretch()
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _setup_positioning(self) -> None:
        """Setup window positioning based on configuration."""
        position = self.ui_config.get('window_position', 'bottom_center')
        
        if position == 'bottom_center':
            self._position_bottom_center()
        elif position == 'top_center':
            self._position_top_center()
        else:
            self._position_bottom_center()  # Default fallback
    
    def _position_bottom_center(self) -> None:
        """Position window at bottom center of screen."""
        try:
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            
            # Position at bottom center with some margin
            x = (screen_geometry.width() - self.width()) // 2
            y = screen_geometry.height() - self.height() - 100
            
            self.move(x, y)
            
        except Exception as e:
            self.logger.error(f"Failed to position window: {e}")
    
    def _position_top_center(self) -> None:
        """Position window at top center of screen (below notch on newer Macs)."""
        try:
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            
            # Position at top center with margin for notch
            x = (screen_geometry.width() - self.width()) // 2
            y = 50  # Below notch area
            
            self.move(x, y)
            
        except Exception as e:
            self.logger.error(f"Failed to position window: {e}")
    
    def show(self) -> None:
        """Show the floating window without stealing focus."""
        if not self.is_visible:
            self.is_visible = True
            
            try:
                # Simple and direct window display - the NSApplicationActivationPolicyAccessory
                # should already prevent focus stealing at the application level
                self.logger.debug("Showing floating window...")
                
                # Use standard show() method since we're now in Accessory mode
                super().show()
                
                # Ensure window is on top but don't activate
                self.raise_()
                
                self.logger.debug("✅ Floating window displayed")
                
            except Exception as e:
                self.logger.error(f"Failed to show floating window: {e}")
            
            # Start volume smoothing
            self.volume_smoothing_timer.start(30)
            
        else:
            # If already visible, just ensure it's on top
            self.raise_()
    
    def hide(self) -> None:
        """Hide the floating window."""
        if self.is_visible:
            self.is_visible = False
            super().hide()
            
            # Stop volume smoothing
            self.volume_smoothing_timer.stop()
            
            self.logger.debug("Floating window hidden")
    
    def update_volume(self, volume: float) -> None:
        """Update volume level for visualization.
        
        Args:
            volume: Volume level between 0.0 and 1.0
        """
        if self.is_visible:
            self.voice_widget.update_volume(volume)
    
    def update_text(self, text: str) -> None:
        """Update real-time transcription text.
        
        Args:
            text: Current transcription text
        """
        self.current_text = text
        if text and text.strip():
            self.text_label.setText(text)
            self.text_label.show()
            
            # Adjust window height if needed
            self._adjust_height_for_text()
        else:
            self.text_label.hide()
            self._reset_height()
    
    def set_status(self, status: str) -> None:
        """Set status message.
        
        Args:
            status: Status message to display
        """
        self.status_label.setText(status)
    
    def set_mode(self, mode: str) -> None:
        """Set display mode.
        
        Args:
            mode: "listening", "processing", "error"
        """
        if mode == "listening":
            self.status_label.setText("🎤 Listening...")
            self.setStyleSheet(self.styleSheet().replace("rgba(100, 200, 255, 100)", 
                                                        "rgba(100, 200, 255, 100)"))
        elif mode == "processing":
            self.status_label.setText("⚡ Processing...")
            self.setStyleSheet(self.styleSheet().replace("rgba(100, 200, 255, 100)", 
                                                        "rgba(255, 200, 100, 100)"))
        elif mode == "error":
            self.status_label.setText("❌ Error")
            self.setStyleSheet(self.styleSheet().replace("rgba(100, 200, 255, 100)", 
                                                        "rgba(255, 100, 100, 100)"))
    
    def _adjust_height_for_text(self) -> None:
        """Adjust window height to accommodate text display."""
        if self.text_label.isVisible():
            text_height = self.text_label.sizeHint().height()
            new_height = self.ui_config.get('floating_window', {}).get('height', 100) + text_height + 20
            self.resize(self.width(), min(new_height, 200))  # Cap at reasonable height
    
    def _reset_height(self) -> None:
        """Reset window to default height."""
        default_height = self.ui_config.get('floating_window', {}).get('height', 100)
        self.resize(self.width(), default_height)
    
    def _update_smooth_volume(self) -> None:
        """Update volume with smoothing (placeholder for future enhancement)."""
        # This could implement volume smoothing if needed
        pass
    
    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        self.close_requested.emit()
    
    def enterEvent(self, event) -> None:
        """Show controls on mouse enter."""
        if self.is_visible:
            self.stop_button.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Hide controls on mouse leave."""
        self.stop_button.hide()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse clicks for window interaction."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Allow dragging the window
            self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event) -> None:
        """Handle window dragging."""
        if (event.buttons() == Qt.MouseButton.LeftButton and 
            hasattr(self, 'drag_start_position')):
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.hide()
        event.accept()


# Qt Application singleton management for the floating window
_qt_app: Optional[QApplication] = None
_app_thread: Optional[threading.Thread] = None

def ensure_qt_application():
    """Ensure QApplication is available."""
    global _qt_app
    
    if _qt_app is None:
        # Check if there's already a QApplication instance
        existing_app = QApplication.instance()
        if existing_app:
            _qt_app = existing_app
        else:
            raise RuntimeError("No QApplication found. QApplication must be created in main thread before creating FloatingWindow.")
    
    return _qt_app