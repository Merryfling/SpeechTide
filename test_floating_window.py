#!/usr/bin/env python3
"""
Test FloatingWindow creation independently
"""

import sys
import os
sys.path.insert(0, 'src')

def test_floating_window():
    """Test FloatingWindow creation."""
    print("🧪 Testing FloatingWindow creation...")
    
    try:
        from floating_window import FloatingWindow
        
        # Test configuration
        ui_config = {
            "window_position": "bottom_center",
            "show_animation": True,
            "auto_hide_delay": 2.0,
            "floating_window": {
                "width": 400,
                "height": 100,
                "opacity": 0.9
            }
        }
        
        print("📱 Creating FloatingWindow...")
        window = FloatingWindow(ui_config)
        
        print("✅ FloatingWindow created successfully!")
        
        # Try to show it briefly
        print("🔍 Testing window show/hide...")
        window.show()
        
        # Import time after successful creation
        import time
        time.sleep(1)
        
        window.hide()
        print("✅ Window show/hide successful!")
        
        # Clean up
        window.close()
        print("✅ Window cleanup successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ FloatingWindow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_components():
    """Test basic components."""
    print("\n🔧 Testing basic components...")
    
    try:
        from config_manager import ConfigManager
        from audio_recorder import AudioRecorder
        
        # Test config
        config_manager = ConfigManager('config/settings.example.json')
        config = config_manager.get_config()
        print("✅ Config loaded")
        
        # Test audio recorder
        audio_recorder = AudioRecorder(config['audio'])
        print("✅ Audio recorder created")
        audio_recorder.cleanup()
        print("✅ Audio recorder cleanup")
        
        return True
        
    except Exception as e:
        print(f"❌ Components test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 SpeechTide FloatingWindow Test")
    print("=" * 50)
    
    # Test components first
    components_ok = test_components()
    
    if components_ok:
        # Test FloatingWindow
        floating_ok = test_floating_window()
        
        if floating_ok:
            print("\n🎉 All tests passed! FloatingWindow should work correctly.")
        else:
            print("\n⚠️ FloatingWindow test failed. Check the errors above.")
    else:
        print("\n⚠️ Basic components test failed.")
    
    print("\n💡 If tests pass, try running the main application:")
    print("   python src/main.py")