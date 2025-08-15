#!/usr/bin/env python3
"""
Quick permissions check for SpeechTide
"""

import sys
import subprocess
from pynput.keyboard import Key, Controller as KeyboardController


def check_accessibility_permissions():
    """Check if accessibility permissions are granted"""
    print("🔐 Checking Accessibility permissions...")
    
    try:
        # Try to create keyboard controller and press a safe key
        keyboard = KeyboardController()
        keyboard.press(Key.f13)  # F13 is safe to test
        keyboard.release(Key.f13)
        print("✅ Accessibility permissions: GRANTED")
        return True
    except Exception as e:
        print(f"❌ Accessibility permissions: DENIED")
        print(f"   Error: {e}")
        return False


def check_system_events():
    """Check if we can access System Events via AppleScript"""
    print("🖥️  Checking System Events access...")
    
    try:
        result = subprocess.run([
            'osascript', '-e', 
            'tell application "System Events" to get name of first process'
        ], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✅ System Events access: GRANTED")
            return True
        else:
            print("❌ System Events access: DENIED")
            return False
    except Exception as e:
        print(f"❌ System Events access: ERROR - {e}")
        return False


def main():
    print("🚀 SpeechTide Permission Checker")
    print("=" * 40)
    
    accessibility_ok = check_accessibility_permissions()
    system_events_ok = check_system_events()
    
    print("\n📋 Summary:")
    print("-" * 20)
    
    if accessibility_ok and system_events_ok:
        print("🎉 All permissions granted! Text insertion should work.")
    else:
        print("⚠️  Some permissions missing. Text insertion may fail.")
        print("\n🔧 To fix:")
        print("1. Open System Settings")
        print("2. Go to Privacy & Security > Accessibility")
        print("3. Click the '+' button")
        print("4. Add Terminal app")
        print("5. Make sure Terminal is checked ✓")
        print("6. Restart Terminal and try again")
        
    return 0 if (accessibility_ok and system_events_ok) else 1


if __name__ == "__main__":
    sys.exit(main())