"""
Text injection functionality for SpeechTide.
Handles copying transcribed text to clipboard with notifications.
"""

import logging
import subprocess
from typing import Optional


class TextInjector:
    """Handles copying text to clipboard and notifying user."""
    
    def __init__(self):
        """Initialize text injector."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("TextInjector initialized (clipboard copy + notification only)")
    
    def insert_text(self, text: str) -> bool:
        """Copy text to clipboard and notify user to paste manually.
        
        Args:
            text: Text to copy to clipboard
            
        Returns:
            True if text copied successfully, False otherwise
        """
        if not text or not text.strip():
            self.logger.warning("Empty text provided for insertion")
            return False
        
        try:
            self.logger.info(f"📋 Copying text to clipboard: {text}")
            
            # Simply copy text to clipboard
            if not self._set_clipboard_content(text):
                self.logger.error("❌ Failed to copy text to clipboard")
                return False
            
            self.logger.info(f"✅ Text copied to clipboard: {text}")
            
            # Show notification to user
            self._show_paste_notification(text)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error copying text: {e}", exc_info=True)
            return False
    
    def _show_paste_notification(self, text: str) -> None:
        """Show notification that text is ready to paste."""
        try:
            # Show notification
            try:
                import rumps
                rumps.notification(
                    title="✅ SpeechTide - Text Ready",
                    subtitle=f"'{text}'",
                    message="Text copied to clipboard! Press Cmd+V to paste anywhere."
                )
                self.logger.info("✅ Paste notification shown")
            except Exception as e:
                self.logger.debug(f"Notification failed: {e}")
            
            # Log simple instruction
            self.logger.info(f"📋✨ Text ready: '{text}' - Press Cmd+V to paste")
            
        except Exception as e:
            self.logger.error(f"❌ Notification failed: {e}")
    
    def _get_clipboard_content(self) -> Optional[str]:
        """Get current clipboard content.
        
        Returns:
            Clipboard content as string, or None if failed
        """
        try:
            # Use pbpaste on macOS
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, check=True)
            return result.stdout
        except Exception as e:
            self.logger.debug(f"Failed to get clipboard content: {e}")
            return None
    
    def _set_clipboard_content(self, text: str) -> bool:
        """Set clipboard content.
        
        Args:
            text: Text to set in clipboard
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use pbcopy on macOS
            subprocess.run(['pbcopy'], input=text, text=True, check=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set clipboard content: {e}")
            return False
    
    def test_insertion(self) -> bool:
        """Test text insertion functionality.
        
        Returns:
            True if test successful, False otherwise
        """
        try:
            test_text = "SpeechTide test"
            return self.insert_text(test_text)
        except Exception as e:
            self.logger.error(f"Text insertion test failed: {e}")
            return False