#!/usr/bin/env python3
"""
Basic test script for SpeechTide application components.
Tests core functionality without requiring external dependencies.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_imports():
    """Test basic module imports."""
    print("🔍 Testing imports...")
    
    try:
        from config_manager import ConfigManager
        print("✓ ConfigManager imported successfully")
    except Exception as e:
        print(f"✗ ConfigManager import failed: {e}")
        return False
    
    return True

def test_config_manager():
    """Test configuration management."""
    print("\n🔍 Testing ConfigManager...")
    
    try:
        from config_manager import ConfigManager
        
        # Test with example config
        config_manager = ConfigManager('config/settings.example.json')
        config = config_manager.get_config()
        
        # Verify key configuration sections
        required_sections = ['openai', 'hotkeys', 'ui', 'audio', 'behavior', 'logging']
        for section in required_sections:
            if section not in config:
                print(f"✗ Missing config section: {section}")
                return False
        
        print("✓ All required config sections present")
        
        # Test API key validation
        has_key = config_manager.validate_api_key()
        print(f"✓ API key validation: {has_key} (expected False for example config)")
        
        # Test get/set methods
        original_value = config_manager.get("ui.window_position")
        config_manager.set("ui.window_position", "test_position")
        new_value = config_manager.get("ui.window_position")
        
        if new_value == "test_position":
            print("✓ Config get/set methods working")
        else:
            print("✗ Config get/set methods failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ ConfigManager test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files are present."""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        'src/main.py',
        'src/config_manager.py',
        'src/menu_bar.py',
        'src/audio_recorder.py',
        'src/hotkey_manager.py',
        'src/floating_window.py',
        'src/openai_client.py',
        'src/text_injector.py',
        'src/conversation_logger.py',
        'src/utils/audio_visualizer.py',
        'config/settings.example.json',
        'requirements.txt',
        'setup.py',
        '.gitignore',
        'README.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("✗ Missing files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print(f"✓ All {len(required_files)} required files present")
        return True

def test_conversation_logger():
    """Test conversation logger without external dependencies."""
    print("\n🔍 Testing ConversationLogger...")
    
    try:
        from conversation_logger import ConversationLogger
        
        # Test initialization
        logger = ConversationLogger("test_conversations")
        print("✓ ConversationLogger initialized")
        
        # Test session creation
        session_id = logger.start_session("test")
        if session_id:
            print(f"✓ Session started: {session_id}")
        else:
            print("✗ Failed to start session")
            return False
        
        # Test logging interaction
        logger.log_interaction(
            audio_data=b"fake_audio_data",
            transcription="Hello world test",
            mode="transcribe",
            duration=2.5
        )
        print("✓ Interaction logged successfully")
        
        # Test session ending
        session_data = logger.end_session()
        if session_data:
            print(f"✓ Session ended: {session_data['session_id']}")
        else:
            print("✗ Failed to end session")
            return False
        
        # Cleanup test directory
        import shutil
        if os.path.exists("test_conversations"):
            shutil.rmtree("test_conversations")
        
        return True
        
    except Exception as e:
        print(f"✗ ConversationLogger test failed: {e}")
        return False

def test_dev_logger():
    """Test development logger."""
    print("\n🔍 Testing development logger...")
    
    try:
        from dev_logger import log_user_prompt, log_completion, log_progress
        
        # Test logging functions
        log_user_prompt("Test user prompt", "Test context")
        log_progress("Testing dev logger", "All functions working")
        log_completion("Dev logger test", "Successfully tested logging functions")
        
        print("✓ Development logger functions working")
        return True
        
    except Exception as e:
        print(f"✗ Development logger test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 SpeechTide Basic Integration Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("ConfigManager", test_config_manager),
        ("ConversationLogger", test_conversation_logger),
        ("Development Logger", test_dev_logger),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test CRASHED: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All basic tests passed! Core application structure is working.")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)