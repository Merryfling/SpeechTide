"""
Conversation logging functionality for SpeechTide.
Records user interactions, transcriptions, and maintains session history.
"""

import os
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path


class ConversationLogger:
    """Handles logging and management of conversation sessions."""
    
    def __init__(self, conversations_dir: str = "conversations"):
        """Initialize conversation logger.
        
        Args:
            conversations_dir: Directory to store conversation logs
        """
        self.conversations_dir = Path(conversations_dir)
        self.logger = logging.getLogger(__name__)
        
        # Ensure conversations directory exists
        self.conversations_dir.mkdir(exist_ok=True)
        
        # Current session
        self.current_session: Optional[Dict[str, Any]] = None
        self.session_counter = self._get_next_session_number()
        
        self.logger.info(f"ConversationLogger initialized, next session: {self.session_counter}")
    
    def start_session(self, mode: str = "transcribe") -> str:
        """Start a new conversation session.
        
        Args:
            mode: Recording mode ("transcribe" or "realtime")
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        self.current_session = {
            "session_id": session_id,
            "session_number": self.session_counter,
            "mode": mode,
            "start_time": timestamp.isoformat(),
            "end_time": None,
            "interactions": [],
            "total_duration": 0.0,
            "word_count": 0,
            "title": f"Session {self.session_counter}"
        }
        
        self.logger.info(f"Started new session: {session_id} (#{self.session_counter})")
        return session_id
    
    def log_interaction(self, 
                       audio_data: bytes,
                       transcription: str,
                       mode: str,
                       duration: Optional[float] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log a single voice interaction.
        
        Args:
            audio_data: Raw audio data
            transcription: Transcribed text
            mode: Recording mode used
            duration: Audio duration in seconds
            metadata: Additional metadata
        """
        if not self.current_session:
            self.start_session(mode)
        
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        interaction = {
            "interaction_id": interaction_id,
            "timestamp": timestamp.isoformat(),
            "mode": mode,
            "transcription": transcription,
            "duration": duration or 0.0,
            "audio_length": len(audio_data),
            "word_count": len(transcription.split()) if transcription else 0,
            "metadata": metadata or {}
        }
        
        # Save audio file if enabled
        if self._should_save_audio():
            audio_filename = f"{interaction_id}.wav"
            audio_path = self.conversations_dir / f"session_{self.session_counter}" / "audio" / audio_filename
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            
            interaction["audio_file"] = str(audio_path.relative_to(self.conversations_dir))
        
        # Add to current session
        self.current_session["interactions"].append(interaction)
        self.current_session["total_duration"] += interaction["duration"]
        self.current_session["word_count"] += interaction["word_count"]
        
        # Update session title based on first meaningful transcription
        if transcription and len(transcription.strip()) > 0:
            self._update_session_title(transcription)
        
        # Save session incrementally
        self._save_current_session()
        
        self.logger.info(f"Logged interaction: {transcription[:50]}{'...' if len(transcription) > 50 else ''}")
    
    def end_session(self) -> Optional[Dict[str, Any]]:
        """End the current conversation session.
        
        Returns:
            Session data if session was active, None otherwise
        """
        if not self.current_session:
            return None
        
        self.current_session["end_time"] = datetime.now().isoformat()
        
        # Final save
        self._save_current_session()
        
        session_data = self.current_session.copy()
        self.current_session = None
        self.session_counter += 1
        
        self.logger.info(f"Ended session: {session_data['session_id']}")
        return session_data
    
    def get_session_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent session history.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        sessions = []
        
        try:
            # Scan conversations directory for session files
            session_files = list(self.conversations_dir.glob("session_*/session.json"))
            session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for session_file in session_files[:limit]:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        
                        # Create summary
                        summary = {
                            "session_number": session_data.get("session_number"),
                            "title": session_data.get("title"),
                            "start_time": session_data.get("start_time"),
                            "end_time": session_data.get("end_time"),
                            "mode": session_data.get("mode"),
                            "interaction_count": len(session_data.get("interactions", [])),
                            "total_duration": session_data.get("total_duration", 0),
                            "word_count": session_data.get("word_count", 0),
                            "file_path": str(session_file)
                        }
                        sessions.append(summary)
                        
                except Exception as e:
                    self.logger.error(f"Error reading session file {session_file}: {e}")
            
        except Exception as e:
            self.logger.error(f"Error getting session history: {e}")
        
        return sessions
    
    def get_session_details(self, session_number: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific session.
        
        Args:
            session_number: Session number to retrieve
            
        Returns:
            Full session data or None if not found
        """
        try:
            session_file = self.conversations_dir / f"session_{session_number}" / "session.json"
            
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
        except Exception as e:
            self.logger.error(f"Error reading session {session_number}: {e}")
        
        return None
    
    def delete_session(self, session_number: int) -> bool:
        """Delete a session and all its data.
        
        Args:
            session_number: Session number to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session_dir = self.conversations_dir / f"session_{session_number}"
            
            if session_dir.exists():
                import shutil
                shutil.rmtree(session_dir)
                self.logger.info(f"Deleted session {session_number}")
                return True
            
        except Exception as e:
            self.logger.error(f"Error deleting session {session_number}: {e}")
        
        return False
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search sessions by transcription content.
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching sessions with context
        """
        results = []
        query_lower = query.lower()
        
        try:
            session_files = list(self.conversations_dir.glob("session_*/session.json"))
            
            for session_file in session_files:
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # Search in session interactions
                    for interaction in session_data.get("interactions", []):
                        transcription = interaction.get("transcription", "").lower()
                        
                        if query_lower in transcription:
                            result = {
                                "session_number": session_data.get("session_number"),
                                "title": session_data.get("title"),
                                "interaction_id": interaction.get("interaction_id"),
                                "timestamp": interaction.get("timestamp"),
                                "transcription": interaction.get("transcription"),
                                "match_context": self._get_match_context(transcription, query_lower)
                            }
                            results.append(result)
                            
                            if len(results) >= limit:
                                break
                    
                    if len(results) >= limit:
                        break
                        
                except Exception as e:
                    self.logger.error(f"Error searching session file {session_file}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error during session search: {e}")
        
        return results[:limit]
    
    def export_session(self, session_number: int, format: str = "json") -> Optional[str]:
        """Export session data to various formats.
        
        Args:
            session_number: Session number to export
            format: Export format ("json", "txt", "csv")
            
        Returns:
            Path to exported file or None if failed
        """
        session_data = self.get_session_details(session_number)
        if not session_data:
            return None
        
        try:
            export_dir = self.conversations_dir / "exports"
            export_dir.mkdir(exist_ok=True)
            
            filename = f"session_{session_number}.{format}"
            export_path = export_dir / filename
            
            if format == "json":
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            elif format == "txt":
                self._export_to_text(session_data, export_path)
            
            elif format == "csv":
                self._export_to_csv(session_data, export_path)
            
            else:
                self.logger.error(f"Unsupported export format: {format}")
                return None
            
            self.logger.info(f"Exported session {session_number} to {export_path}")
            return str(export_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting session {session_number}: {e}")
            return None
    
    def _get_next_session_number(self) -> int:
        """Get the next session number.
        
        Returns:
            Next available session number
        """
        existing_sessions = list(self.conversations_dir.glob("session_*"))
        if not existing_sessions:
            return 1
        
        # Extract session numbers and find the highest
        session_numbers = []
        for session_dir in existing_sessions:
            try:
                number = int(session_dir.name.split("_")[1])
                session_numbers.append(number)
            except (IndexError, ValueError):
                continue
        
        return max(session_numbers, default=0) + 1
    
    def _update_session_title(self, transcription: str) -> None:
        """Update session title based on transcription content.
        
        Args:
            transcription: Transcription text to generate title from
        """
        if not self.current_session or self.current_session.get("title") != f"Session {self.session_counter}":
            return  # Title already customized
        
        # Generate title from first meaningful words
        words = transcription.strip().split()
        if words:
            title_words = words[:6]  # First 6 words
            title = " ".join(title_words)
            if len(title) > 50:
                title = title[:47] + "..."
            
            self.current_session["title"] = title
    
    def _save_current_session(self) -> None:
        """Save current session to disk."""
        if not self.current_session:
            return
        
        try:
            session_dir = self.conversations_dir / f"session_{self.session_counter}"
            session_dir.mkdir(exist_ok=True)
            
            session_file = session_dir / "session.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving session: {e}")
    
    def _should_save_audio(self) -> bool:
        """Check if audio files should be saved."""
        # For now, save audio files. This could be made configurable
        return True
    
    def _get_match_context(self, text: str, query: str, context_length: int = 50) -> str:
        """Get context around a search match.
        
        Args:
            text: Full text
            query: Search query
            context_length: Characters of context to include
            
        Returns:
            Text with match context highlighted
        """
        match_pos = text.find(query)
        if match_pos == -1:
            return text[:context_length]
        
        start = max(0, match_pos - context_length)
        end = min(len(text), match_pos + len(query) + context_length)
        
        context = text[start:end]
        if start > 0:
            context = "..." + context
        if end < len(text):
            context = context + "..."
        
        return context
    
    def _export_to_text(self, session_data: Dict[str, Any], file_path: Path) -> None:
        """Export session to plain text format.
        
        Args:
            session_data: Session data to export
            file_path: Output file path
        """
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"SpeechTide Session Export\n")
            f.write(f"========================\n\n")
            f.write(f"Session: {session_data.get('title')}\n")
            f.write(f"Number: {session_data.get('session_number')}\n")
            f.write(f"Mode: {session_data.get('mode')}\n")
            f.write(f"Start Time: {session_data.get('start_time')}\n")
            f.write(f"End Time: {session_data.get('end_time')}\n")
            f.write(f"Total Duration: {session_data.get('total_duration', 0):.2f}s\n")
            f.write(f"Word Count: {session_data.get('word_count', 0)}\n\n")
            
            f.write("Transcriptions:\n")
            f.write("-" * 50 + "\n")
            
            for i, interaction in enumerate(session_data.get('interactions', []), 1):
                f.write(f"\n{i}. [{interaction.get('timestamp')}]\n")
                f.write(f"   {interaction.get('transcription', '')}\n")
    
    def _export_to_csv(self, session_data: Dict[str, Any], file_path: Path) -> None:
        """Export session to CSV format.
        
        Args:
            session_data: Session data to export
            file_path: Output file path
        """
        import csv
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'Session Number', 'Interaction ID', 'Timestamp', 'Mode',
                'Transcription', 'Duration', 'Word Count'
            ])
            
            # Data rows
            session_number = session_data.get('session_number')
            for interaction in session_data.get('interactions', []):
                writer.writerow([
                    session_number,
                    interaction.get('interaction_id'),
                    interaction.get('timestamp'),
                    interaction.get('mode'),
                    interaction.get('transcription', ''),
                    interaction.get('duration', 0),
                    interaction.get('word_count', 0)
                ])