"""
Development conversation recorder for SpeechTide project.
Records the actual dialogue between user and AI assistant.
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Any


class ConversationRecorder:
    """Records development conversations between user and assistant."""
    
    def __init__(self, conversations_dir: str = "dev_conversations"):
        """Initialize conversation recorder."""
        self.conversations_dir = Path(conversations_dir)
        self.conversations_dir.mkdir(exist_ok=True)
        
        # Current session
        self.current_conversation = None
        self.session_number = self._get_next_session_number()
        
    def start_conversation(self, title: str = None) -> None:
        """Start recording a new conversation."""
        self.current_conversation = {
            "session_number": self.session_number,
            "title": title or f"开发对话 #{self.session_number}",
            "start_time": datetime.datetime.now().isoformat(),
            "messages": []
        }
        
    def record_user_message(self, message: str, context: str = None) -> None:
        """Record user prompt/message."""
        if not self.current_conversation:
            self.start_conversation()
            
        self.current_conversation["messages"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "role": "user",
            "content": message,
            "context": context
        })
        
        self._save_conversation()
    
    def record_assistant_message(self, message: str, actions: List[str] = None) -> None:
        """Record assistant response and actions taken."""
        if not self.current_conversation:
            self.start_conversation()
            
        self.current_conversation["messages"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "role": "assistant", 
            "content": message,
            "actions": actions or []
        })
        
        self._save_conversation()
    
    def end_conversation(self, summary: str = None) -> None:
        """End current conversation recording."""
        if not self.current_conversation:
            return
            
        self.current_conversation["end_time"] = datetime.datetime.now().isoformat()
        if summary:
            self.current_conversation["summary"] = summary
            
        self._save_conversation()
        self.current_conversation = None
        self.session_number += 1
    
    def _get_next_session_number(self) -> int:
        """Get next session number."""
        existing_files = list(self.conversations_dir.glob("conversation_*.json"))
        if not existing_files:
            return 1
            
        numbers = []
        for file in existing_files:
            try:
                num = int(file.stem.split("_")[1])
                numbers.append(num)
            except (IndexError, ValueError):
                continue
                
        return max(numbers, default=0) + 1
    
    def _save_conversation(self) -> None:
        """Save current conversation to file."""
        if not self.current_conversation:
            return
            
        filename = f"conversation_{self.session_number:03d}.json"
        filepath = self.conversations_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_conversation, f, 
                         indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存对话记录失败: {e}")


# Global recorder instance
conversation_recorder = ConversationRecorder()

# 记录当前对话
conversation_recorder.start_conversation("SpeechTide语音输入应用开发")

# 记录用户的初始需求
conversation_recorder.record_user_message(
    """你是一个精通Mac上python应用开发的高级工程师，我希望你能和我一起开发一个语音输入应用，让我们先探讨一下这个应用的MVP，它应当是在状态栏上的，菜单很简洁，当前初版我希望支持GPT-4o-mini-realtime-preview以及GPT-4o-mini-transcribe，通过自定义快捷键唤起，比如键盘上右command键、右option键，点按唤起，点按结束或者长按知道说完话，说完话后自动转录为文字并输入到当前光标位置，语音输入过程中要在屏幕正下方中央出一个小浮窗，或者是在屏幕上方屏幕"刘海下方"有一个小浮窗，可以考虑根据声音有一个声浪的动画，展示是有声音的，对于realtime模型来说，可以在浮窗里面展示当前识别的句子。需要支持自定义api key和api base url，可以把我们的对话放入一个文件夹，附上序号和标题，记录我的prompt以及你完成的事情，注意写入.gitignore，这个仅用于本地记录，并且我git只初始化了readme标题，请完善并注意git""",
    "项目初始需求"
)