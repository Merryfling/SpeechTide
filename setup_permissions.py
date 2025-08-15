#!/usr/bin/env python3
"""
macOS Permissions Setup Guide for SpeechTide
"""

import sys
import subprocess


def main():
    print("🔐 SpeechTide macOS Permissions Setup Guide")
    print("=" * 50)
    print()
    
    print("📝 REQUIRED PERMISSIONS:")
    print("1. ✅ Microphone access - for voice recording")
    print("2. ✅ Accessibility access - for text insertion")
    print("3. ✅ Input Monitoring - for global hotkeys")
    print()
    
    print("🛠️  STEP-BY-STEP FIX:")
    print("=" * 30)
    print()
    
    print("📱 Step 1: Open System Settings")
    print("   • Click Apple menu > System Settings")
    print("   • Or search 'System Settings' in Spotlight")
    print()
    
    print("🔒 Step 2: Go to Privacy & Security")
    print("   • Click 'Privacy & Security' in the sidebar")
    print()
    
    print("🎤 Step 3: Enable Microphone Access")
    print("   • Click 'Microphone'")
    print("   • Find 'Terminal' in the list")
    print("   • Turn ON the switch next to Terminal")
    print()
    
    print("♿ Step 4: Enable Accessibility Access") 
    print("   • Go back and click 'Accessibility'")
    print("   • Click the '+' button to add an app")
    print("   • Navigate to Applications > Utilities")
    print("   • Select 'Terminal' and click 'Open'")
    print("   • Make sure Terminal has a ✓ checkmark")
    print()
    
    print("⌨️  Step 5: Enable Input Monitoring")
    print("   • Go back and click 'Input Monitoring'") 
    print("   • Click the '+' button to add an app")
    print("   • Navigate to Applications > Utilities")
    print("   • Select 'Terminal' and click 'Open'")
    print("   • Make sure Terminal has a ✓ checkmark")
    print()
    
    print("🔄 Step 6: Restart Terminal")
    print("   • Quit Terminal completely (Cmd+Q)")
    print("   • Reopen Terminal")
    print("   • Navigate back to your project directory")
    print()
    
    print("🧪 Step 7: Test SpeechTide")
    print("   • Run: ./start.sh")
    print("   • If you still see permission warnings, repeat steps 4-5")
    print()
    
    print("💡 TROUBLESHOOTING:")
    print("=" * 20)
    print("• If Terminal doesn't appear in the lists, try adding Python directly:")
    print("  - Find Python at: /usr/bin/python3")
    print("  - Or check: which python3")
    print()
    print("• If problems persist, try adding these to Accessibility:")
    print("  - Terminal.app")
    print("  - Python.app (if exists)")
    print("  - osascript")
    print()
    
    print("✨ After setup, SpeechTide will automatically paste text!")
    print("   If auto-paste fails, you'll get a notification to paste manually.")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())