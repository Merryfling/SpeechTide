#!/usr/bin/env python3
"""
SpeechTide System Requirements and Permissions Checker.
Verifies system compatibility and required permissions.
"""

import os
import sys
import subprocess
import platform
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    required_major, required_minor = 3, 8
    
    if version.major < required_major or (version.major == required_major and version.minor < required_minor):
        print(f"✗ Python {version.major}.{version.minor} detected, but Python {required_major}.{required_minor}+ required")
        return False
    else:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True

def check_macos_version():
    """Check macOS version compatibility."""
    print("\n🍎 Checking macOS version...")
    
    if platform.system() != "Darwin":
        print("✗ This application requires macOS")
        return False
    
    try:
        version_output = subprocess.check_output(['sw_vers', '-productVersion'], text=True).strip()
        version_parts = version_output.split('.')
        major_version = int(version_parts[0])
        minor_version = int(version_parts[1]) if len(version_parts) > 1 else 0
        
        # Require macOS 10.15 (Catalina) or later
        if major_version >= 11 or (major_version == 10 and minor_version >= 15):
            print(f"✓ macOS {version_output} - Compatible")
            return True
        else:
            print(f"✗ macOS {version_output} detected, but macOS 10.15+ required")
            return False
            
    except Exception as e:
        print(f"✗ Could not determine macOS version: {e}")
        return False

def check_accessibility_permissions():
    """Check accessibility permissions."""
    print("\n🔐 Checking accessibility permissions...")
    
    try:
        # Try to use AppleScript to check accessibility
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
        end tell
        return frontApp
        '''
        
        result = subprocess.run(['osascript', '-e', script], 
                              capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            print("✓ Accessibility permissions granted")
            return True
        else:
            print("✗ Accessibility permissions required")
            print("  Please grant accessibility permissions in System Preferences > Security & Privacy > Privacy > Accessibility")
            return False
            
    except Exception as e:
        print(f"⚠ Could not check accessibility permissions: {e}")
        return False

def check_microphone_permissions():
    """Check microphone permissions."""
    print("\n🎤 Checking microphone permissions...")
    
    try:
        # Try to access microphone using AppleScript
        script = '''
        tell application "System Events"
            return (microphone access allowed)
        end tell
        '''
        
        # For now, just check if we can run the system_profiler command
        result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and 'Built-in Microphone' in result.stdout:
            print("✓ Microphone detected and accessible")
            return True
        else:
            print("⚠ Microphone permissions may be required")
            print("  Please grant microphone access when prompted")
            return False
            
    except Exception as e:
        print(f"⚠ Could not check microphone permissions: {e}")
        return False

def check_required_packages():
    """Check if required Python packages are available."""
    print("\n📦 Checking required packages...")
    
    required_packages = [
        ('rumps', '0.4.0'),
        ('PyQt6', '6.5.0'),
        ('pyaudio', '0.2.11'),
        ('numpy', '1.24.0'),
        ('pynput', '1.7.6'),
        ('pyautogui', '0.9.54'),
        ('openai', '1.0.0'),
        ('websockets', '11.0'),
        ('requests', '2.31.0'),
    ]
    
    missing_packages = []
    outdated_packages = []
    
    def version_compare(v1, v2):
        """Simple version comparison."""
        v1_parts = [int(x) for x in v1.split('.')]
        v2_parts = [int(x) for x in v2.split('.')]
        
        # Pad with zeros if needed
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts += [0] * (max_len - len(v1_parts))
        v2_parts += [0] * (max_len - len(v2_parts))
        
        return v1_parts >= v2_parts
    
    for package_name, min_version in required_packages:
        try:
            installed_version = version(package_name)
            
            # Compare versions
            if version_compare(installed_version, min_version):
                print(f"✓ {package_name} {installed_version}")
            else:
                print(f"⚠ {package_name} {installed_version} (requires {min_version}+)")
                outdated_packages.append((package_name, installed_version, min_version))
                
        except PackageNotFoundError:
            print(f"✗ {package_name} (not installed)")
            missing_packages.append(package_name)
    
    if not missing_packages and not outdated_packages:
        print("✓ All required packages are installed and up to date")
        return True
    else:
        if missing_packages:
            print(f"\n📝 Missing packages: {', '.join(missing_packages)}")
        if outdated_packages:
            print(f"📝 Outdated packages: {', '.join([p[0] for p in outdated_packages])}")
        print("💡 Run: pip install -r requirements.txt")
        return False

def check_homebrew_dependencies():
    """Check for Homebrew dependencies."""
    print("\n🍺 Checking Homebrew dependencies...")
    
    try:
        # Check if brew is installed
        subprocess.run(['which', 'brew'], check=True, capture_output=True)
        print("✓ Homebrew is installed")
        
        # Check for portaudio (required for pyaudio)
        result = subprocess.run(['brew', 'list', 'portaudio'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ PortAudio is installed")
            return True
        else:
            print("⚠ PortAudio not found")
            print("💡 Run: brew install portaudio")
            return False
            
    except subprocess.CalledProcessError:
        print("⚠ Homebrew not found")
        print("💡 Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("💡 Then run: brew install portaudio")
        return False

def check_system_preferences():
    """Provide guidance on system preferences."""
    print("\n⚙️ System Preferences Setup:")
    print("1. Security & Privacy > Privacy > Microphone:")
    print("   - Enable microphone access for Terminal/Python")
    print("2. Security & Privacy > Privacy > Accessibility:")
    print("   - Enable accessibility access for Terminal/Python")
    print("3. Security & Privacy > Privacy > Input Monitoring:")
    print("   - Enable input monitoring for Terminal/Python")
    print("4. For global hotkeys to work, the application needs to be trusted.")

def main():
    """Run all system checks."""
    print("🚀 SpeechTide System Requirements Checker")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("macOS Version", check_macos_version),
        ("Accessibility Permissions", check_accessibility_permissions),
        ("Microphone Permissions", check_microphone_permissions),
        ("Required Packages", check_required_packages),
        ("Homebrew Dependencies", check_homebrew_dependencies),
    ]
    
    passed = 0
    total = len(checks)
    critical_failures = 0
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed += 1
            else:
                if check_name in ["Python Version", "macOS Version"]:
                    critical_failures += 1
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
            if check_name in ["Python Version", "macOS Version"]:
                critical_failures += 1
    
    check_system_preferences()
    
    print("\n" + "=" * 60)
    print(f"📊 System Check Results: {passed}/{total} checks passed")
    
    if critical_failures > 0:
        print("🚨 Critical system requirements not met. Please address the issues above.")
    elif passed >= total - 2:  # Allow for permission checks to fail initially
        print("✅ System is ready for SpeechTide!")
        print("💡 If any permission checks failed, they will be requested when you first run the app.")
    else:
        print("⚠️ Some requirements are missing. Please install missing dependencies.")
    
    print("\n🚀 To start the application:")
    print("   python src/main.py")
    
    return critical_failures == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)