#!/usr/bin/env python3
"""
SpeechTide Application Status Checker
Quick verification of application readiness
"""

import os
import sys
import json
sys.path.insert(0, 'src')

def check_status():
    """Check application status and readiness."""
    print("🎤 SpeechTide Application Status")
    print("=" * 40)
    
    status = {
        "structure": True,
        "config": False,
        "dependencies": True,
        "ready": False
    }
    
    # Check file structure
    try:
        required_files = ['src/main.py', 'config/settings.example.json', 'requirements.txt']
        for file in required_files:
            if not os.path.exists(file):
                status["structure"] = False
                break
        
        if status["structure"]:
            print("✅ Application structure: OK")
        else:
            print("❌ Application structure: MISSING FILES")
    except Exception as e:
        print(f"❌ Structure check failed: {e}")
        status["structure"] = False
    
    # Check configuration
    try:
        if os.path.exists('config/settings.json'):
            with open('config/settings.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('openai', {}).get('api_key', '')
                if api_key and api_key.strip() and api_key != "":
                    print("✅ Configuration: API key configured")
                    status["config"] = True
                else:
                    print("⚠️  Configuration: API key needed in config/settings.json")
                    status["config"] = False
        else:
            print("⚠️  Configuration: settings.json not found (will use example)")
            status["config"] = False
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        status["config"] = False
    
    # Check dependencies  
    try:
        from config_manager import ConfigManager
        from audio_recorder import AudioRecorder
        print("✅ Dependencies: Core modules imported successfully")
        status["dependencies"] = True
    except Exception as e:
        print(f"❌ Dependencies: Import failed - {e}")
        status["dependencies"] = False
    
    # Overall readiness
    status["ready"] = all([
        status["structure"], 
        status["dependencies"]
    ])
    
    print("\n" + "=" * 40)
    if status["ready"] and status["config"]:
        print("🎉 Status: READY TO USE!")
        print("   Run: ./start.sh")
    elif status["ready"]:
        print("🔧 Status: NEEDS CONFIGURATION")
        print("   1. Copy config/settings.example.json to config/settings.json")
        print("   2. Add your OpenAI API key")
        print("   3. Run: ./start.sh")
    else:
        print("🚨 Status: NEEDS SETUP")
        print("   1. Install dependencies: pip install -r requirements.txt")
        if not status["config"]:
            print("   2. Configure API key in config/settings.json")
        print("   3. Grant system permissions when prompted")
    
    print("\n📖 Quick Help:")
    print("   • Test basic functionality: python test_basic.py")
    print("   • Test FloatingWindow: python test_floating_window.py")
    print("   • Test recording workflow: python test_recording.py")
    print("   • Check system requirements: python check_system.py") 
    print("   • Start application: ./start.sh")
    
    return status["ready"]

if __name__ == "__main__":
    success = check_status()
    sys.exit(0 if success else 1)