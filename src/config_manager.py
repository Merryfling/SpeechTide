"""
Configuration management for SpeechTide application.
Handles loading, saving, and validating application settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging


class ConfigManager:
    """Manages application configuration settings."""
    
    DEFAULT_CONFIG = {
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model_realtime": "gpt-4o-mini-realtime-preview",
            "model_transcribe": "gpt-4o-mini"
        },
        "hotkeys": {
            "primary": "right_cmd",
            "secondary": "right_option"
        },
        "ui": {
            "window_position": "bottom_center",
            "show_animation": True,
            "auto_hide_delay": 2.0,
            "floating_window": {
                "width": 400,
                "height": 100,
                "opacity": 0.9
            }
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "chunk_size": 1024,
            "format": "int16"
        },
        "behavior": {
            "auto_start_threshold": 0.01,
            "silence_timeout": 2.0,
            "max_recording_duration": 60.0
        },
        "logging": {
            "enable_conversation_logging": True,
            "log_level": "INFO",
            "max_log_files": 10
        }
    }
    
    def __init__(self, config_path: str = "config/settings.json"):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self.DEFAULT_CONFIG.copy()
        self.logger = logging.getLogger(__name__)
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self.config, file_config)
                self.logger.info(f"Configuration loaded from {self.config_path}")
            else:
                self.logger.info("Configuration file not found, using defaults")
                self.save_config()  # Create default config file
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self.logger.info("Using default configuration")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            os.makedirs(self.config_path.parent, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Current configuration dictionary
        """
        return self.config.copy()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by key path.
        
        Args:
            key_path: Dot-separated key path (e.g., "openai.api_key")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value by key path.
        
        Args:
            key_path: Dot-separated key path (e.g., "openai.api_key")
            value: Value to set
        """
        keys = key_path.split('.')
        config_ref = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # Set the final value
        config_ref[keys[-1]] = value
        self.logger.info(f"Configuration updated: {key_path} = {value}")
    
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key is configured.
        
        Returns:
            True if API key is configured and non-empty
        """
        api_key = self.get("openai.api_key", "")
        return bool(api_key and api_key.strip())
    
    def _merge_config(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            update: Update configuration dictionary
        """
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value