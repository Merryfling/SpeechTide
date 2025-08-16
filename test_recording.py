#!/usr/bin/env python3
"""
Test complete recording workflow
"""

import sys
import os
sys.path.insert(0, 'src')

def test_recording_workflow():
    """Test the complete recording workflow without GUI interaction."""
    print("🎤 Testing complete recording workflow...")
    
    try:
        from config_manager import ConfigManager
        from menu_bar import SpeechTideApp
        
        # Load configuration
        config_manager = ConfigManager('config/settings.example.json')
        
        print("📋 Creating SpeechTideApp...")
        app = SpeechTideApp(config_manager, dev_mode=True)
        print("✅ SpeechTideApp created successfully!")
        
        # Test starting recording programmatically
        print("🔴 Testing start recording...")
        
        # Simulate the recording start process
        if not app.config_manager.validate_api_key():
            print("⚠️ No API key configured, but that's expected for this test")
            
        # Set up a fake API key for testing UI
        app.config['openai']['api_key'] = 'test-key'
        app.config_manager.set('openai.api_key', 'test-key')
        
        # Try to start recording
        app._start_recording()
        
        if app.floating_window:
            print("✅ FloatingWindow created during recording!")
            app.floating_window.hide()
        
        # Stop recording
        if app.is_recording:
            print("🔴 Stopping recording...")
            app._stop_recording()
            print("✅ Recording stopped successfully!")
        
        # Cleanup
        app.clean_up()
        print("✅ App cleanup successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Recording workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 SpeechTide Recording Workflow Test")
    print("=" * 50)
    
    success = test_recording_workflow()
    
    if success:
        print("\n🎉 Recording workflow test passed!")
        print("💡 The 'Start Recording' button should now work correctly.")
        print("   Try running: python src/main.py")
    else:
        print("\n❌ Recording workflow test failed.")
        print("💡 Check the errors above and fix them before running the main app.")