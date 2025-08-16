"""
Global hotkey management for SpeechTide.
Handles system-wide keyboard event detection for activation keys.
"""

import threading
import logging
from typing import Callable, Optional, Dict
from pynput import keyboard
from pynput.keyboard import Key, Listener


class HotkeyManager:
    """Manages global hotkey detection and handling."""
    
    # Map string representations to pynput Key objects
    KEY_MAPPING = {
        'right_cmd': Key.cmd_r,
        'left_cmd': Key.cmd_l,
        'right_option': Key.alt_r,
        'left_option': Key.alt_l,
        'right_alt': Key.alt_r,
        'left_alt': Key.alt_l,
        'right_ctrl': Key.ctrl_r,
        'left_ctrl': Key.ctrl_l,
        'right_shift': Key.shift_r,
        'left_shift': Key.shift_l,
        'space': Key.space,
        'esc': Key.esc,
        'tab': Key.tab,
        'enter': Key.enter,
    }
    
    def __init__(self, primary_key: str, on_hotkey: Callable[[str], None]):
        """Initialize hotkey manager.
        
        Args:
            primary_key: Hotkey identifier
            on_hotkey: Callback function when hotkey is pressed
        """
        self.primary_key = self._get_key_object(primary_key)
        self.primary_key_name = primary_key
        self.on_hotkey = on_hotkey
        
        self.logger = logging.getLogger(__name__)
        
        # State tracking
        self.is_running = False
        self.pressed_keys = set()
        self.listener: Optional[Listener] = None
        
        # Interaction mode tracking
        self.interaction_mode = "click"  # "click" or "hold"
        self.key_pressed_time: Dict[str, float] = {}
        self.hold_threshold = 0.1  # Minimum hold time to distinguish from click
        
        self.logger.info(f"HotkeyManager initialized with key: {primary_key}")
    
    def _get_key_object(self, key_name: str) -> Key:
        """Convert string key name to pynput Key object.
        
        Args:
            key_name: String representation of the key
            
        Returns:
            Corresponding pynput Key object
            
        Raises:
            ValueError: If key name is not recognized
        """
        if key_name in self.KEY_MAPPING:
            return self.KEY_MAPPING[key_name]
        else:
            # Try to handle single character keys
            if len(key_name) == 1:
                return keyboard.KeyCode.from_char(key_name)
            else:
                self.logger.error(f"Unknown key name: {key_name}")
                raise ValueError(f"Unknown key name: {key_name}")
    
    def start(self) -> None:
        """Start listening for global hotkeys."""
        if self.is_running:
            self.logger.warning("Hotkey manager already running")
            return
        
        try:
            self.is_running = True
            
            # Start keyboard listener in a separate thread
            self.listener = Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            
            self.listener.start()
            self.logger.info("Global hotkey listening started")
            
        except Exception as e:
            self.logger.error(f"Failed to start hotkey listener: {e}")
            self.is_running = False
            raise
    
    def stop(self) -> None:
        """Stop listening for global hotkeys."""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            if self.listener:
                self.listener.stop()
                self.listener = None
            
            self.pressed_keys.clear()
            self.key_pressed_time.clear()
            
            self.logger.info("Global hotkey listening stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping hotkey listener: {e}")
    
    def _on_key_press(self, key: Key) -> None:
        """Handle key press events.
        
        Args:
            key: The key that was pressed
        """
        try:
            current_time = threading.current_thread().ident or 0
            
            # Check if this is our hotkey
            if key == self.primary_key:
                self._handle_hotkey_press(self.primary_key_name, current_time)
            
            # Track pressed keys for combination detection
            self.pressed_keys.add(key)
            
        except Exception as e:
            self.logger.error(f"Error in key press handler: {e}")
    
    def _on_key_release(self, key: Key) -> None:
        """Handle key release events.
        
        Args:
            key: The key that was released
        """
        try:
            current_time = threading.current_thread().ident or 0
            
            # Check if this is our hotkey
            if key == self.primary_key:
                self._handle_hotkey_release(self.primary_key_name, current_time)
            
            # Remove from pressed keys
            self.pressed_keys.discard(key)
            
        except Exception as e:
            self.logger.error(f"Error in key release handler: {e}")
    
    def _handle_hotkey_press(self, key_name: str, press_time: float) -> None:
        """Handle hotkey press event.
        
        Args:
            key_name: Name of the pressed hotkey
            press_time: Time when key was pressed
        """
        self.key_pressed_time[key_name] = press_time
        self.logger.debug(f"Hotkey pressed: {key_name}")
        
        # For click mode, trigger immediately on press
        if self.interaction_mode == "click":
            self._trigger_hotkey(key_name)
    
    def _handle_hotkey_release(self, key_name: str, release_time: float) -> None:
        """Handle hotkey release event.
        
        Args:
            key_name: Name of the released hotkey
            release_time: Time when key was released
        """
        if key_name not in self.key_pressed_time:
            return
        
        press_time = self.key_pressed_time[key_name]
        hold_duration = release_time - press_time
        
        self.logger.debug(f"Hotkey released: {key_name}, held for {hold_duration:.3f}s")
        
        # For hold mode, trigger on release after sufficient hold time
        if self.interaction_mode == "hold" and hold_duration >= self.hold_threshold:
            self._trigger_hotkey(key_name)
        
        # Clean up
        del self.key_pressed_time[key_name]
    
    def _trigger_hotkey(self, key_name: str) -> None:
        """Trigger hotkey callback.
        
        Args:
            key_name: Name of the triggered hotkey
        """
        try:
            self.logger.info(f"Hotkey triggered: {key_name}")
            if self.on_hotkey:
                # Run callback in a separate thread to avoid blocking the listener
                callback_thread = threading.Thread(
                    target=self.on_hotkey,
                    args=(key_name,),
                    daemon=True
                )
                callback_thread.start()
        except Exception as e:
            self.logger.error(f"Error triggering hotkey callback: {e}")
    
    def set_interaction_mode(self, mode: str) -> None:
        """Set interaction mode for hotkeys.
        
        Args:
            mode: "click" for press/release activation, "hold" for hold-and-release
        """
        if mode in ["click", "hold"]:
            self.interaction_mode = mode
            self.logger.info(f"Interaction mode set to: {mode}")
        else:
            self.logger.error(f"Invalid interaction mode: {mode}")
    
    def update_hotkeys(self, primary_key: str) -> None:
        """Update hotkey assignment.
        
        Args:
            primary_key: New hotkey identifier
        """
        try:
            was_running = self.is_running
            
            if was_running:
                self.stop()
            
            # Update key
            self.primary_key = self._get_key_object(primary_key)
            self.primary_key_name = primary_key
            
            if was_running:
                self.start()
            
            self.logger.info(f"Hotkey updated to: {primary_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to update hotkey: {e}")
            raise
    
    def test_permissions(self) -> bool:
        """Test if the application has necessary permissions for global hotkey detection.
        
        Returns:
            True if permissions are available, False otherwise
        """
        try:
            # Try to create a temporary listener
            test_listener = Listener(on_press=lambda key: None, on_release=lambda key: None)
            test_listener.start()
            test_listener.stop()
            
            self.logger.info("Accessibility permissions test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Accessibility permissions test failed: {e}")
            return False
    
    def get_available_keys(self) -> list:
        """Get list of available hotkey options.
        
        Returns:
            List of available key names
        """
        return list(self.KEY_MAPPING.keys())
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        if self.is_running:
            self.stop()