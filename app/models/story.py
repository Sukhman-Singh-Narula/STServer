# ===== app/models/story.py =====
from pydantic import BaseModel
from dataclasses import dataclass
from typing import List, Dict, Any

class StoryPromptRequest(BaseModel):
    firebase_token: str
    prompt: str

class SystemPromptUpdate(BaseModel):
    firebase_token: str
    system_prompt: str

@dataclass
class StoryScene:
    scene_number: int
    text: str
    visual_prompt: str
    audio_url: str = ""
    image_url: str = ""
    start_time: int = 0

@dataclass
class StoryManifest:
    story_id: str
    title: str
    total_duration: int
    segments: List[Dict[str, Any]]