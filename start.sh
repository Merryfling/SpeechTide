#!/bin/bash
# SpeechTide Startup Script

echo "🚀 Starting SpeechTide Voice Input Application"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if settings file exists
if [ ! -f "config/settings.json" ]; then
    echo "⚠️  Configuration file not found. Creating from template..."
    cp config/settings.example.json config/settings.json
    echo "📝 Please edit config/settings.json to add your OpenAI API key"
fi

# Check for required permissions
echo "🔍 Checking system permissions..."
echo "   If you see permission warnings, please:"
echo "   1. Open System Preferences → Security & Privacy → Privacy"
echo "   2. Add Terminal/Python to:"
echo "      - Microphone access"
echo "      - Accessibility access" 
echo "      - Input Monitoring access"
echo ""

# Start the application
echo "🎤 Starting SpeechTide..."
echo "   Use ⌘+Q to quit the application"
echo "   Look for the 🎤 icon in your menu bar"
echo ""

python src/main.py "$@"