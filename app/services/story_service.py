# ===== app/services/story_service.py =====
import json
import uuid
from typing import List, Tuple
from fastapi import HTTPException
import groq
from app.models.story import StoryScene
from app.config import settings

class StoryService:
    def __init__(self, groq_client: groq.Groq, user_service):
        self.groq_client = groq_client
        self.user_service = user_service
    
    async def generate_story_scenes(self, prompt: str, user_id: str) -> Tuple[List[StoryScene], str]:
        """Generate story scenes using Groq Llama"""
        try:
            # Get user-specific system prompt or use default
            user_system_prompt = self.user_service.get_user_system_prompt(user_id)
            
            full_prompt = f"""
            {user_system_prompt}
            
            Create a story based on this prompt: "{prompt}"
            
            Structure your response as exactly {settings.max_scenes} scenes. For each scene, provide:
            1. The scene text (2-3 sentences)
            2. A detailed visual description for image generation
            
            Format your response as JSON:
            {{
                "title": "Story Title",
                "scenes": [
                    {{
                        "scene_number": 1,
                        "text": "Scene text here...",
                        "visual_prompt": "Detailed visual description for image generation..."
                    }}
                ]
            }}
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": user_system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            story_data = json.loads(response.choices[0].message.content)
            
            scenes = []
            for scene_data in story_data["scenes"]:
                scene = StoryScene(
                    scene_number=scene_data["scene_number"],
                    text=scene_data["text"],
                    visual_prompt=scene_data["visual_prompt"]
                )
                scenes.append(scene)
            
            return scenes, story_data.get("title", "Generated Story")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")
    
    def generate_story_id(self) -> str:
        """Generate unique story ID"""
        return f"story_{uuid.uuid4().hex[:8]}"