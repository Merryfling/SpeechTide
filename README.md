# SpeechTide

A powerful voice input application for macOS that provides seamless speech-to-text functionality using OpenAI's GPT-4o models.

## Features

### Core Functionality
- **Status Bar Integration**: Lightweight menu bar presence with clean interface
- **Dual Recognition Modes**:
  - GPT-4o-mini-realtime-preview for real-time streaming transcription
  - GPT-4o-mini-transcribe for batch transcription
- **Global Hotkeys**: Activate with Right Command or Right Option keys
- **Smart Input**: Click to start/stop or long press until speech completion
- **Floating UI**: Voice visualization window (bottom center or below notch)
- **Real-time Display**: Live transcription preview during recognition
- **Auto Text Injection**: Seamlessly insert transcribed text at cursor position

### Advanced Features  
- **Voice Wave Animation**: Visual feedback during recording
- **Custom Configuration**: Configurable API keys and base URLs
- **Session Logging**: Local conversation recording with numbering and titles
- **Privacy First**: All conversations stored locally, never shared

## Installation

### Prerequisites
- macOS 10.15 or later
- Python 3.8 or later
- Microphone access permissions

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd speechtide

# Install dependencies
pip install -r requirements.txt

# Configure your OpenAI API key
cp config/settings.example.json config/settings.json
# Edit config/settings.json with your API key
```

## Usage

### First Run
1. Launch SpeechTide: `python src/main.py`
2. Grant microphone and accessibility permissions when prompted
3. Configure your OpenAI API key in the status bar menu
4. Set your preferred hotkeys and recognition mode

### Voice Input
- **Quick Mode**: Press and release hotkey to start, press again to stop
- **Hold Mode**: Hold hotkey while speaking, release when done
- **Visual Feedback**: Watch the floating window for real-time transcription
- **Auto Input**: Transcribed text automatically appears at your cursor

## Configuration

### API Settings
```json
{
  "openai": {
    "api_key": "your-api-key-here",
    "base_url": "https://api.openai.com/v1",
    "model_realtime": "gpt-4o-mini-realtime-preview", 
    "model_transcribe": "gpt-4o-mini"
  },
  "hotkeys": {
    "primary": "right_cmd",
    "secondary": "right_option"
  },
  "ui": {
    "window_position": "bottom_center",
    "show_animation": true,
    "auto_hide_delay": 2.0
  }
}
```

### Permissions
SpeechTide requires the following macOS permissions:
- **Microphone**: For voice recording
- **Accessibility**: For global hotkey detection and text injection
- **Input Monitoring**: For cursor position detection

## Architecture

```
src/
├── main.py              # Application entry point
├── menu_bar.py          # Status bar application logic  
├── audio_recorder.py    # Audio capture and processing
├── hotkey_manager.py    # Global keyboard event handling
├── floating_window.py   # Voice input UI overlay
├── openai_client.py     # GPT-4o API integration
├── text_injector.py     # System text input automation
├── config_manager.py    # Settings and configuration
├── conversation_logger.py # Session recording and management
└── utils/
    └── audio_visualizer.py # Real-time voice wave visualization
```

## Development

### Running in Development Mode
```bash
python src/main.py --dev
```

### Building for Distribution
```bash  
python setup.py build_app
```

### Testing
```bash
pytest tests/
```

## Privacy & Security

- **Local Processing**: All conversations stored locally in `conversations/`
- **API Security**: API keys encrypted and stored in system keychain
- **No Telemetry**: No usage data or audio sent to third parties
- **Open Source**: Full source code available for audit

## Troubleshooting

### Common Issues
- **Microphone not working**: Check System Preferences > Security & Privacy > Microphone
- **Hotkeys not responding**: Enable Accessibility permissions for SpeechTide
- **Text not inserting**: Grant Input Monitoring permissions in Security settings

### Logs
Application logs are stored in `logs/speechtide.log` for debugging.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4o API
- Contributors to the rumps, PyQt6, and pynput libraries
- The macOS development community
