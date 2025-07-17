# ===== app/models/story.py =====
from pydantic import BaseModel
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


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
    colored_image_url: str = ""
    start_time: int = 0

@dataclass
class StoryManifest:
    story_id: str
    title: str
    total_duration: int
    segments: List[Dict[str, Any]]

class UserStoriesRequest(BaseModel):
    firebase_token: str
    limit: Optional[int] = 20
    offset: Optional[int] = 0

class StoryListItem(BaseModel):
    story_id: str
    title: str
    user_prompt: str
    created_at: datetime
    total_scenes: int
    total_duration: int
    status: str
    story_number: int
    thumbnail_url: Optional[str] = None
    created_at_formatted: str
    days_ago: int

class UserStoriesResponse(BaseModel):
    success: bool
    user_id: str
    stories: List[StoryListItem]
    total_count: int
    has_more: bool
    user_info: Optional[Dict[str, Any]] = None