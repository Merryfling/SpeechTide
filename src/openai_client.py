"""
OpenAI API client for speech recognition and real-time processing.
Handles both transcription and real-time voice processing using GPT-4o models.
"""

import openai
import asyncio
import websockets
import json
import base64
import io
import logging
from typing import Optional, Dict, Any, Callable, AsyncGenerator
import threading
import time


class OpenAIClient:
    """Client for OpenAI speech recognition services."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            base_url: Base URL for OpenAI API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Real-time connection state
        self.realtime_connected = False
        self.realtime_websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.realtime_task: Optional[asyncio.Task] = None
        
        self.logger.info("OpenAI client initialized")
    
    def transcribe_audio(self, audio_data: bytes, model: str = "gpt-4o-mini", language: Optional[str] = None) -> str:
        """Transcribe audio using OpenAI Whisper/transcription API.
        
        Args:
            audio_data: Audio data in WAV format
            model: Model to use for transcription
            language: Language code for transcription (e.g., 'zh', 'en'). Auto-detect if None.
            
        Returns:
            Transcribed text
        """
        try:
            lang_info = f" (language: {language})" if language else " (auto-detect)"
            self.logger.info(f"Starting transcription with model: {model}{lang_info}")
            
            # Create audio file object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"  # Required for the API
            
            # Prepare API call parameters
            api_params = {
                "model": "whisper-1",  # Currently the main Whisper model
                "file": audio_file,
                "response_format": "text"
            }
            
            # Add language parameter if specified
            if language:
                api_params["language"] = language
            
            # Call OpenAI transcription API
            response = self.client.audio.transcriptions.create(**api_params)
            
            transcription = response.strip() if isinstance(response, str) else str(response).strip()
            self.logger.info(f"Transcription completed: {len(transcription)} characters")
            
            return transcription
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}", exc_info=True)
            raise
    
    def transcribe_audio_with_timestamps(self, audio_data: bytes) -> Dict[str, Any]:
        """Transcribe audio with word-level timestamps.
        
        Args:
            audio_data: Audio data in WAV format
            
        Returns:
            Dictionary with transcription and timestamp information
        """
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"
            
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )
            
            return {
                "text": response.text,
                "duration": response.duration,
                "words": response.words if hasattr(response, 'words') else []
            }
            
        except Exception as e:
            self.logger.error(f"Timestamped transcription failed: {e}")
            raise
    
    async def start_realtime_session(self, 
                                   on_transcript: Callable[[str, bool], None],
                                   on_error: Callable[[str], None]) -> None:
        """Start real-time speech recognition session.
        
        Args:
            on_transcript: Callback for transcript updates (text, is_final)
            on_error: Callback for error handling
        """
        try:
            self.logger.info("Starting real-time session")
            
            # Real-time API endpoint (this is a placeholder - actual endpoint may differ)
            realtime_url = self.base_url.replace("v1", "realtime").replace("https://", "wss://")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            async with websockets.connect(
                realtime_url,
                extra_headers=headers
            ) as websocket:
                
                self.realtime_websocket = websocket
                self.realtime_connected = True
                
                # Send session configuration
                await self._send_session_config(websocket)
                
                # Start message processing loop
                async for message in websocket:
                    await self._process_realtime_message(message, on_transcript, on_error)
                    
        except Exception as e:
            self.logger.error(f"Real-time session failed: {e}", exc_info=True)
            self.realtime_connected = False
            on_error(f"Real-time connection failed: {str(e)}")
    
    async def _send_session_config(self, websocket) -> None:
        """Send session configuration for real-time API.
        
        Args:
            websocket: WebSocket connection
        """
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "You are a helpful voice assistant. Transcribe speech accurately.",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                }
            }
        }
        
        await websocket.send(json.dumps(config))
        self.logger.debug("Sent session configuration")
    
    async def _process_realtime_message(self, 
                                      message: str,
                                      on_transcript: Callable[[str, bool], None],
                                      on_error: Callable[[str], None]) -> None:
        """Process incoming real-time messages.
        
        Args:
            message: Raw message from WebSocket
            on_transcript: Callback for transcript updates
            on_error: Callback for error handling
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "input_audio_buffer.speech_started":
                self.logger.debug("Speech started")
                
            elif message_type == "input_audio_buffer.speech_stopped":
                self.logger.debug("Speech stopped")
                
            elif message_type == "conversation.item.input_audio_transcription.completed":
                # Partial transcript
                transcript = data.get("transcript", "")
                on_transcript(transcript, False)
                
            elif message_type == "conversation.item.input_audio_transcription.failed":
                error_msg = data.get("error", {}).get("message", "Transcription failed")
                self.logger.error(f"Transcription error: {error_msg}")
                on_error(error_msg)
                
            elif message_type == "response.audio_transcript.delta":
                # Real-time transcript delta
                delta = data.get("delta", "")
                on_transcript(delta, False)
                
            elif message_type == "response.audio_transcript.done":
                # Final transcript
                transcript = data.get("transcript", "")
                on_transcript(transcript, True)
                
            elif message_type == "error":
                error_msg = data.get("error", {}).get("message", "Unknown error")
                self.logger.error(f"Real-time API error: {error_msg}")
                on_error(error_msg)
            
        except Exception as e:
            self.logger.error(f"Error processing real-time message: {e}")
            on_error(f"Message processing error: {str(e)}")
    
    async def send_audio_data(self, audio_chunk: bytes) -> None:
        """Send audio data to real-time session.
        
        Args:
            audio_chunk: Raw audio data (PCM16)
        """
        if not self.realtime_connected or not self.realtime_websocket:
            return
        
        try:
            # Encode audio data as base64
            audio_base64 = base64.b64encode(audio_chunk).decode('utf-8')
            
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            await self.realtime_websocket.send(json.dumps(message))
            
        except Exception as e:
            self.logger.error(f"Failed to send audio data: {e}")
    
    def stop_realtime_session(self) -> None:
        """Stop the real-time session."""
        try:
            self.realtime_connected = False
            
            if self.realtime_task and not self.realtime_task.done():
                self.realtime_task.cancel()
            
            if self.realtime_websocket:
                asyncio.create_task(self.realtime_websocket.close())
                
            self.logger.info("Real-time session stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping real-time session: {e}")
    
    def update_api_key(self, api_key: str) -> None:
        """Update API key.
        
        Args:
            api_key: New OpenAI API key
        """
        self.api_key = api_key
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )
        self.logger.info("API key updated")
    
    def update_base_url(self, base_url: str) -> None:
        """Update base URL.
        
        Args:
            base_url: New OpenAI API base URL (empty string uses default)
        """
        self.base_url = base_url if base_url else "https://api.openai.com/v1"
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.logger.info(f"Base URL updated to: {self.base_url}")
    
    def test_connection(self) -> bool:
        """Test connection to OpenAI API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple completion request
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=1
            )
            
            self.logger.info("API connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            return False
    
    def get_available_models(self) -> list:
        """Get list of available models.
        
        Returns:
            List of available model names
        """
        try:
            models = self.client.models.list()
            model_names = [model.id for model in models.data]
            return model_names
            
        except Exception as e:
            self.logger.error(f"Failed to get models: {e}")
            return []


class RealtimeSessionManager:
    """Manages real-time speech recognition sessions."""
    
    def __init__(self, openai_client: OpenAIClient):
        """Initialize real-time session manager.
        
        Args:
            openai_client: OpenAI client instance
        """
        self.client = openai_client
        self.logger = logging.getLogger(__name__)
        
        # Session state
        self.is_active = False
        self.current_transcript = ""
        self.transcript_callback: Optional[Callable[[str, bool], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        
        # Asyncio event loop for real-time processing
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
    
    def start_session(self, 
                     on_transcript: Callable[[str, bool], None],
                     on_error: Callable[[str], None]) -> None:
        """Start a new real-time session.
        
        Args:
            on_transcript: Callback for transcript updates
            on_error: Callback for error handling
        """
        if self.is_active:
            self.logger.warning("Real-time session already active")
            return
        
        self.transcript_callback = on_transcript
        self.error_callback = on_error
        self.is_active = True
        
        # Start asyncio event loop in separate thread
        self.loop_thread = threading.Thread(
            target=self._run_session_loop,
            daemon=True
        )
        self.loop_thread.start()
        
        self.logger.info("Real-time session started")
    
    def stop_session(self) -> None:
        """Stop the current real-time session."""
        if not self.is_active:
            return
        
        self.is_active = False
        self.client.stop_realtime_session()
        
        self.logger.info("Real-time session stopped")
    
    def send_audio(self, audio_data: bytes) -> None:
        """Send audio data to the real-time session.
        
        Args:
            audio_data: Raw audio data
        """
        if self.is_active and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.client.send_audio_data(audio_data),
                self.loop
            )
    
    def _run_session_loop(self) -> None:
        """Run the asyncio event loop for real-time session."""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            self.loop.run_until_complete(
                self.client.start_realtime_session(
                    on_transcript=self._handle_transcript,
                    on_error=self._handle_error
                )
            )
            
        except Exception as e:
            self.logger.error(f"Real-time session loop error: {e}")
            if self.error_callback:
                self.error_callback(f"Session error: {str(e)}")
        finally:
            self.is_active = False
    
    def _handle_transcript(self, text: str, is_final: bool) -> None:
        """Handle transcript updates from real-time session.
        
        Args:
            text: Transcript text
            is_final: Whether this is the final transcript
        """
        if not is_final:
            self.current_transcript = text
        else:
            self.current_transcript = text
        
        if self.transcript_callback:
            self.transcript_callback(text, is_final)
    
    def _handle_error(self, error_message: str) -> None:
        """Handle errors from real-time session.
        
        Args:
            error_message: Error message
        """
        self.logger.error(f"Real-time session error: {error_message}")
        if self.error_callback:
            self.error_callback(error_message)