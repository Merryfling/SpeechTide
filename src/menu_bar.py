"""
Status bar application for SpeechTide.
Provides menu bar interface and coordinates all application components.
"""

import rumps
import threading
import logging
from typing import Optional

from config_manager import ConfigManager
from audio_recorder import AudioRecorder
from hotkey_manager import HotkeyManager
from openai_client import OpenAIClient
from text_injector import TextInjector
from conversation_logger import ConversationLogger


class SpeechTideApp(rumps.App):
    """Main status bar application for SpeechTide."""
    
    def __init__(self, config_manager: ConfigManager, dev_mode: bool = False, qt_app=None):
        """Initialize SpeechTide application.
        
        Args:
            config_manager: Configuration manager instance
            dev_mode: Whether running in development mode
            qt_app: Pre-initialized QApplication instance
        """
        super().__init__("🎤", quit_button=None)
        
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.dev_mode = dev_mode
        self.qt_app = qt_app  # Store Qt application reference
        self.logger = logging.getLogger(__name__)
        
        # Application state
        self.is_recording = False
        self.is_transcribing = False  # New state for transcription
        self._recording_lock = threading.Lock()  # Thread safety for recording state
        
        # UI operation flags for main thread handling
        self._pending_start_recording = False
        self._pending_stop_recording = False
        self._pending_set_transcribing = False
        self._pending_clear_transcribing = False
        
        # Initialize components
        self._init_components()
        self._setup_menu()
        
        # Start hotkey manager
        self.hotkey_manager.start()
        
        # Set up main thread UI processing timer
        self._setup_main_thread_timer()
        
        self.logger.info("SpeechTide initialized successfully")
    
    def _setup_main_thread_timer(self):
        """Set up timer to handle UI operations in main thread."""
        import rumps
        
        # Create a timer that checks for pending UI operations every 100ms
        self.ui_timer = rumps.Timer(self._process_pending_ui_operations, 0.1)
        self.ui_timer.start()
    
    def _process_pending_ui_operations(self, timer):
        """Process pending UI operations in main thread."""
        try:
            if self._pending_start_recording and not self.is_recording:
                self._pending_start_recording = False
                self._start_recording_main_thread()
            elif self._pending_stop_recording and self.is_recording:
                self._pending_stop_recording = False
                self._stop_recording_main_thread()
            
            if self._pending_set_transcribing:
                self._pending_set_transcribing = False
                self.is_transcribing = True
                self._update_menu_state()
                self.logger.info("🎤⏳ Started transcribing...")
            
            if self._pending_clear_transcribing:
                self._pending_clear_transcribing = False
                self.is_transcribing = False
                self._update_menu_state()
                self.logger.info("🎤 Transcription completed")
                
        except Exception as e:
            self.logger.error(f"Error processing pending UI operations: {e}", exc_info=True)
    
    def _start_recording_main_thread(self) -> None:
        """Start recording from main thread (called by UI timer)."""
        try:
            if self.is_recording:
                self.logger.warning("Already recording, ignoring start request")
                return

            if not self.config_manager.validate_api_key():
                rumps.alert("API Key Required", 
                           "Please configure your OpenAI API key in Settings.")
                return

            self.is_recording = True
            self.logger.info("Starting recording in transcribe mode (main thread)")
            
            # Start audio recording
            self.audio_recorder.start_recording()
            
            self._update_menu_state()
            
        except Exception as e:
            self.logger.error(f"Error starting recording in main thread: {e}", exc_info=True)
            self.is_recording = False
            rumps.alert("Recording Error", f"Failed to start recording: {str(e)}")
    
    def _stop_recording_main_thread(self) -> None:
        """Stop recording from main thread (called by UI timer)."""
        try:
            if not self.is_recording:
                self.logger.warning("Not recording, ignoring stop request")
                return
            
            self.logger.info("Stopping recording (main thread)")
            self.is_recording = False
            
            # Stop audio recording
            audio_data = self.audio_recorder.stop_recording()
            
            # Process audio in background thread
            processing_thread = threading.Thread(
                target=self._process_audio,
                args=(audio_data,),
                daemon=True
            )
            processing_thread.start()
            
            self._update_menu_state()
            
        except Exception as e:
            self.logger.error(f"Error stopping recording in main thread: {e}", exc_info=True)
            # Ensure recording state is reset even if stopping fails
            self.is_recording = False
            self._update_menu_state()
    
    def _init_components(self) -> None:
        """Initialize application components."""
        try:
            # Audio recording
            self.audio_recorder = AudioRecorder(self.config['audio'])
            
            # OpenAI client
            self.openai_client = OpenAIClient(
                api_key=self.config['openai']['api_key'],
                base_url=self.config['openai']['base_url']
            )
            
            # Text injection
            self.text_injector = TextInjector()
            
            # Conversation logging
            self.conversation_logger = ConversationLogger()
            
            # Hotkey manager
            self.hotkey_manager = HotkeyManager(
                primary_key=self.config['hotkeys']['primary'],
                on_hotkey=self._handle_hotkey
            )
            
        except Exception as e:
            self.logger.error(f"Error initializing components: {e}", exc_info=True)
            raise
    
    def _setup_menu(self) -> None:
        """Setup status bar menu."""
        # Create menu items with references - use a toggle callback
        self.recording_menu_item = rumps.MenuItem("Start Recording", callback=self._toggle_recording)
        
        # Create language submenu using simple approach
        current_language = self.config.get('language', {}).get('recognition', 'auto')
        
        # Create language menu items
        auto_item = rumps.MenuItem("✓ Auto Detect" if current_language == 'auto' else "Auto Detect", 
                                  callback=lambda sender: self._select_language(sender, 'auto'))
        zh_item = rumps.MenuItem("✓ Chinese (简体中文)" if current_language == 'zh' else "Chinese (简体中文)", 
                                callback=lambda sender: self._select_language(sender, 'zh'))
        en_item = rumps.MenuItem("✓ English" if current_language == 'en' else "English", 
                                callback=lambda sender: self._select_language(sender, 'en'))
        
        # Create settings menu items  
        api_item = rumps.MenuItem("Configure API Key", callback=self._configure_api_key)
        url_item = rumps.MenuItem("Configure Base URL", callback=self._configure_base_url)
        hotkey_item = rumps.MenuItem("Hotkey Settings", callback=self._configure_hotkeys)
        audio_item = rumps.MenuItem("Audio Settings", callback=self._configure_audio)
        
        # Build menu structure
        self.menu = [
            self.recording_menu_item,
            None,  # separator
            [
                "Language",
                [auto_item, zh_item, en_item]
            ],
            None,  # separator  
            [
                "Settings",
                [api_item, url_item, hotkey_item, audio_item]
            ],
            None,  # separator
            rumps.MenuItem("Conversations", callback=self._open_conversations),
            None,  # separator
            rumps.MenuItem("About", callback=self._show_about),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        
        # Store references for updates
        self.language_items = [auto_item, zh_item, en_item]
        
        # Update menu state
        self._update_menu_state()
    
    def _create_language_submenu(self) -> rumps.MenuItem:
        """Create language selection submenu with proper rumps syntax."""
        language_options = self.config.get('language', {}).get('options', {})
        current_language = self.config.get('language', {}).get('recognition', 'auto')
        
        # Create parent menu item
        language_menu = rumps.MenuItem("Language")
        
        # Create child menu items
        language_menu_items = []
        for lang_code, lang_name in language_options.items():
            # Mark current selection with checkmark
            title = f"✓ {lang_name}" if lang_code == current_language else lang_name
            menu_item = rumps.MenuItem(title, callback=lambda sender, lang_code=lang_code: self._select_language(sender, lang_code))
            language_menu_items.append(menu_item)
        
        # Assign child items to parent menu
        language_menu.menu = language_menu_items
        
        return language_menu
    
    def _create_settings_submenu(self) -> rumps.MenuItem:
        """Create settings submenu with proper rumps syntax."""
        # Create parent menu item
        settings_menu = rumps.MenuItem("Settings")
        
        # Create child menu items
        settings_menu_items = [
            rumps.MenuItem("Configure API Key", callback=self._configure_api_key),
            rumps.MenuItem("Configure Base URL", callback=self._configure_base_url),
            rumps.MenuItem("Hotkey Settings", callback=self._configure_hotkeys),
            rumps.MenuItem("Audio Settings", callback=self._configure_audio),
        ]
        
        # Assign child items to parent menu
        settings_menu.menu = settings_menu_items
        
        return settings_menu
    
    def _update_menu_state(self) -> None:
        """Update menu item states and icons based on current state."""
        # Update recording button using direct reference
        if hasattr(self, 'recording_menu_item'):
            self.recording_menu_item.title = "Stop Recording" if self.is_recording else "Start Recording"
        
        # Determine the appropriate icon
        new_icon = None
        if not self.config_manager.validate_api_key():
            new_icon = "🎤❌"  # Show error if no API key
        elif self.is_transcribing:
            new_icon = "⏳"  # Transcribing state - clean hourglass
        elif self.is_recording:
            new_icon = "⚡️"  # Recording state - lightning bolt for activity
        else:
            new_icon = "🎤"  # Idle state - microphone ready
        
        # Update title icon and log the change
        if new_icon != self.title:
            old_icon = self.title
            self.title = new_icon
            self.logger.info(f"Status bar icon updated: '{old_icon}' → '{new_icon}' (recording={self.is_recording}, transcribing={self.is_transcribing})")
        else:
            self.logger.debug(f"Status bar icon unchanged: '{new_icon}' (recording={self.is_recording}, transcribing={self.is_transcribing})")
    
    def _handle_hotkey(self, key: str) -> None:
        """Handle hotkey activation.
        
        Args:
            key: The hotkey that was pressed
        """
        try:
            self.logger.info(f"Hotkey activated: {key}")
            
            # Set flags for main thread to process, don't do UI operations here
            if self.is_recording:
                self.logger.info("Hotkey triggered: requesting stop recording")
                self._pending_stop_recording = True
                self._pending_start_recording = False
            else:
                self.logger.info("Hotkey triggered: requesting start recording")
                self._pending_start_recording = True
                self._pending_stop_recording = False
        except Exception as e:
            self.logger.error(f"Error handling hotkey {key}: {e}", exc_info=True)
    
    def _toggle_recording(self, sender: Optional[rumps.MenuItem] = None) -> None:
        """Toggle recording state from menu click."""
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self, sender: Optional[rumps.MenuItem] = None) -> None:
        """Start voice recording."""
        try:
            # Use a simple approach: check if already recording and return early
            if self.is_recording:
                self.logger.warning("Already recording, ignoring start request")
                return

            if not self.config_manager.validate_api_key():
                rumps.alert("API Key Required", 
                           "Please configure your OpenAI API key in Settings.")
                return

            self.is_recording = True
            self.logger.info("Starting recording in transcribe mode")
            
            # Start audio recording
            self.audio_recorder.start_recording()
            
            self._update_menu_state()
            
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}", exc_info=True)
            self.is_recording = False
            rumps.alert("Recording Error", f"Failed to start recording: {str(e)}")
    
    def _stop_recording(self) -> None:
        """Stop voice recording and process audio."""
        try:
            if not self.is_recording:
                self.logger.warning("Not recording, ignoring stop request")
                return
            
            self.logger.info("Stopping recording")
            self.is_recording = False
            
            # Stop audio recording
            audio_data = self.audio_recorder.stop_recording()
            
            # Process audio in background thread
            processing_thread = threading.Thread(
                target=self._process_audio,
                args=(audio_data,),
                daemon=True
            )
            processing_thread.start()
            
            self._update_menu_state()
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}", exc_info=True)
            # Ensure recording state is reset even if stopping fails
            self.is_recording = False
            self._update_menu_state()
    
    def _process_audio(self, audio_data: bytes) -> None:
        """Process recorded audio and insert transcribed text.
        
        Args:
            audio_data: Raw audio data
        """
        try:
            self.logger.info("Processing audio for transcription")
            
            # Signal main thread to set transcribing state
            self._pending_set_transcribing = True
            
            # Get selected language
            selected_language = self.config.get('language', {}).get('recognition', 'auto')
            # Convert 'auto' to None for the API
            language_param = None if selected_language == 'auto' else selected_language
            
            # Transcribe audio using OpenAI
            transcription = self.openai_client.transcribe_audio(
                audio_data,
                model=self.config['openai']['model_transcribe'],
                language=language_param
            )
            
            if transcription and transcription.strip():
                self.logger.info(f"Transcription: {transcription}")
                
                # Log conversation
                self.conversation_logger.log_interaction(
                    audio_data=audio_data,
                    transcription=transcription,
                    mode="transcribe"
                )
                
                # Insert text at cursor position
                self.text_injector.insert_text(transcription)
            else:
                self.logger.warning("No transcription result")
                
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}", exc_info=True)
            # Show error notification
            rumps.notification("SpeechTide", "Transcription Error", 
                             f"Failed to process audio: {str(e)}")
        finally:
            # Signal main thread to clear transcribing state
            self._pending_clear_transcribing = True
    
    def _update_language_menu(self) -> None:
        """Update language menu checkmarks without recreating the entire menu."""
        try:
            current_language = self.config.get('language', {}).get('recognition', 'auto')
            language_options = self.config.get('language', {}).get('options', {})
            
            # Use stored references to update menu items
            if hasattr(self, 'language_items'):
                for i, (lang_code, lang_name) in enumerate(language_options.items()):
                    if i < len(self.language_items):
                        title = f"✓ {lang_name}" if lang_code == current_language else lang_name
                        self.language_items[i].title = title
                            
        except Exception as e:
            self.logger.error(f"Error updating language menu: {e}", exc_info=True)
            # If updating fails, rebuild the entire menu
            self._setup_menu()
    
    def _select_language(self, sender: rumps.MenuItem, language_code: str) -> None:
        """Handle language selection from menu.
        
        Args:
            sender: Menu item that was clicked
            language_code: Selected language code
        """
        try:
            # Update configuration
            self.config_manager.set("language.recognition", language_code)
            self.config_manager.save_config()
            
            # Update local config reference
            self.config = self.config_manager.get_config()
            
            # Update language menu checkmarks
            self._update_language_menu()
            
            # Get language name for notification
            language_name = self.config.get('language', {}).get('options', {}).get(language_code, language_code)
            rumps.notification("SpeechTide", "Language Updated", f"Recognition language set to: {language_name}")
            
            self.logger.info(f"Language changed to: {language_code} ({language_name})")
            
        except Exception as e:
            self.logger.error(f"Error selecting language: {e}", exc_info=True)
            rumps.alert("Error", f"Failed to change language: {str(e)}")
    
    def _configure_api_key(self, sender: rumps.MenuItem) -> None:
        """Configure OpenAI API key."""
        current_key = self.config_manager.get("openai.api_key", "")
        
        # Simple dialog for API key (in a real app, use more secure input)
        response = rumps.Window(
            title="Configure API Key",
            message="Enter your OpenAI API key:",
            default_text=current_key,
            ok="Save",
            cancel="Cancel",
            dimensions=(350, 100)
        ).run()
        
        if response.clicked:
            api_key = response.text.strip()
            if api_key:
                self.config_manager.set("openai.api_key", api_key)
                self.config_manager.save_config()
                
                # Update OpenAI client
                self.openai_client.update_api_key(api_key)
                
                self._update_menu_state()
                rumps.alert("Settings Saved", "API key has been updated.")
            else:
                rumps.alert("Invalid Input", "API key cannot be empty.")
    
    def _configure_base_url(self, sender: rumps.MenuItem) -> None:
        """Configure OpenAI API base URL."""
        current_url = self.config_manager.get("openai.base_url", "")
        
        response = rumps.Window(
            title="Configure Base URL",
            message="Enter OpenAI API base URL (leave empty for default):",
            default_text=current_url,
            ok="Save",
            cancel="Cancel", 
            dimensions=(400, 100)
        ).run()
        
        if response.clicked:
            base_url = response.text.strip()
            # Empty string is valid (uses default)
            self.config_manager.set("openai.base_url", base_url)
            self.config_manager.save_config()
            
            # Update OpenAI client
            self.openai_client.update_base_url(base_url)
            
            url_display = base_url if base_url else "Default (https://api.openai.com/v1)"
            rumps.alert("Settings Saved", f"Base URL has been updated to:\n{url_display}")
    
    def _configure_hotkeys(self, sender: rumps.MenuItem) -> None:
        """Configure hotkey settings."""
        rumps.alert("Hotkey Settings", 
                   f"Current hotkey: {self.config['hotkeys']['primary']}\n\n"
                   "Hotkey customization will be available in a future update.")
    
    def _configure_audio(self, sender: rumps.MenuItem) -> None:
        """Configure audio settings."""
        rumps.alert("Audio Settings", 
                   f"Sample Rate: {self.config['audio']['sample_rate']} Hz\n"
                   f"Channels: {self.config['audio']['channels']}\n"
                   f"Chunk Size: {self.config['audio']['chunk_size']}\n\n"
                   "Audio customization will be available in a future update.")
    
    @rumps.clicked("Conversations")
    def _open_conversations(self, sender: rumps.MenuItem) -> None:
        """Open conversations folder."""
        import subprocess
        try:
            subprocess.run(["open", "conversations/"], check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to open conversations folder: {e}")
            rumps.alert("Error", "Failed to open conversations folder.")
    
    @rumps.clicked("About")
    def _show_about(self, sender: rumps.MenuItem) -> None:
        """Show about dialog."""
        rumps.alert("About SpeechTide",
                   "SpeechTide v0.1.0\n\n"
                   "A powerful voice input application for macOS\n"
                   "using OpenAI GPT-4o models.\n\n"
                   "Features:\n"
                   "• Real-time voice recognition\n"
                   "• Global hotkey activation\n"
                   "• Automatic text insertion\n"
                   "• Conversation logging\n\n"
                   "For support and updates:\n"
                   "github.com/speechtide/speechtide")
    
    def clean_up(self) -> None:
        """Clean up resources before quitting."""
        try:
            if self.is_recording:
                self._stop_recording()
            
            if self.hotkey_manager:
                self.hotkey_manager.stop()
            
            self.logger.info("Application cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}", exc_info=True)