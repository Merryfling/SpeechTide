#!/usr/bin/env python3
"""
SpeechTide - Voice Input Application for macOS
Main application entry point.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from menu_bar import SpeechTideApp
from config_manager import ConfigManager

# Initialize Qt in the main thread
from PyQt6.QtWidgets import QApplication
import signal

# Global Qt application instance
qt_app = None


def setup_logging(config):
    """Setup application logging."""
    log_level = config.get('logging', {}).get('log_level', 'INFO')
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/speechtide.log')
        ]
    )


def init_qt_application():
    """Initialize Qt application in main thread."""
    global qt_app
    
    if qt_app is None:
        # Check if there's already a QApplication instance
        existing_app = QApplication.instance()
        if existing_app:
            qt_app = existing_app
        else:
            # Create new QApplication in main thread
            qt_app = QApplication(sys.argv)
            
            # Set application display name to prevent showing as "Python"
            qt_app.setApplicationName("SpeechTide")
            qt_app.setApplicationDisplayName("SpeechTide")
            qt_app.setApplicationVersion("1.0")
            qt_app.setOrganizationName("SpeechTide")
            
            # Set macOS application policy to Accessory mode
            # This prevents the app from appearing in Cmd+Tab and stealing focus
            try:
                import platform
                if platform.system() == 'Darwin':  # macOS
                    try:
                        # Try using PyObjC to set NSApplicationActivationPolicyAccessory
                        import objc
                        from Foundation import NSBundle
                        
                        # Get the main bundle and set activation policy
                        bundle = NSBundle.mainBundle()
                        if bundle:
                            # Set bundle display name to prevent "Python" appearance
                            info_dict = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                            if info_dict:
                                info_dict.setValue_forKey_("SpeechTide", "CFBundleDisplayName")
                                info_dict.setValue_forKey_("SpeechTide", "CFBundleName")
                            
                            # NSApplicationActivationPolicyAccessory = 1
                            # This makes the app behave like a status bar app
                            import Cocoa
                            NSApp = Cocoa.NSApplication.sharedApplication()
                            NSApp.setActivationPolicy_(1)  # NSApplicationActivationPolicyAccessory
                            
                            print("✅ Set macOS app to Accessory mode with SpeechTide branding")
                    except ImportError:
                        print("⚠️  PyObjC not available - app may appear in Cmd+Tab")
                    except Exception as e:
                        print(f"⚠️  Failed to set Accessory mode: {e}")
            except Exception as e:
                print(f"⚠️  Failed to configure macOS app mode: {e}")
            
            # Set up signal handlers for clean shutdown
            signal.signal(signal.SIGINT, lambda signum, frame: qt_app.quit())
            signal.signal(signal.SIGTERM, lambda signum, frame: qt_app.quit())
    
    return qt_app


def main():
    """Main application entry point."""
    global qt_app
    
    parser = argparse.ArgumentParser(description='SpeechTide Voice Input Application')
    parser.add_argument('--dev', action='store_true', help='Run in development mode')
    parser.add_argument('--config', default='config/settings.json', help='Config file path')
    args = parser.parse_args()

    # Ensure required directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('conversations', exist_ok=True)
    os.makedirs('config', exist_ok=True)

    # Load configuration
    config_manager = ConfigManager(args.config)
    config = config_manager.get_config()
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    if args.dev:
        logger.info("Starting SpeechTide in development mode")
    else:
        logger.info("Starting SpeechTide")

    # Initialize Qt application in main thread FIRST
    logger.info("Initializing Qt application in main thread")
    qt_app = init_qt_application()

    # Check for required permissions
    if not check_permissions():
        logger.error("Required permissions not granted")
        return 1

    try:
        # Initialize and run the application
        app = SpeechTideApp(config_manager, dev_mode=args.dev, qt_app=qt_app)
        app.run()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1
    finally:
        # Clean up Qt application
        if qt_app:
            try:
                qt_app.quit()
            except Exception:
                pass


def check_permissions():
    """Check if required macOS permissions are granted."""
    # TODO: Implement permission checks
    # - Microphone access
    # - Accessibility permissions
    # - Input monitoring
    return True


if __name__ == '__main__':
    sys.exit(main())