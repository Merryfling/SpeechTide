#!/usr/bin/env python3
"""
SpeechTide - Voice Input Application for macOS
Setup script for building and distributing the application.
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="speechtide",
    version="0.1.0",
    author="SpeechTide Team",
    description="A powerful voice input application for macOS using OpenAI GPT-4o",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Desktop Environment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "speechtide=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md"],
    },
    zip_safe=False,
    # macOS app building options (for py2app)
    options={
        "py2app": {
            "argv_emulation": True,
            "plist": {
                "CFBundleName": "SpeechTide",
                "CFBundleDisplayName": "SpeechTide",
                "CFBundleGetInfoString": "Voice Input Application",
                "CFBundleIdentifier": "com.speechtide.app",
                "CFBundleVersion": "0.1.0",
                "CFBundleShortVersionString": "0.1.0",
                "NSMicrophoneUsageDescription": "SpeechTide needs microphone access to record your voice for transcription.",
                "NSAccessibilityUsageDescription": "SpeechTide needs accessibility access to detect global hotkeys and insert text.",
                "LSUIElement": True,  # Don't show in Dock
            },
            "iconfile": "assets/icon.icns",  # Optional app icon
        }
    },
    setup_requires=["py2app"] if "py2app" in os.sys.argv else [],
)