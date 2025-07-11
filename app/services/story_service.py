# ===== app/services/story_service.py =====
import json
import uuid
from typing import List, Tuple
from fastapi import HTTPException
from openai import OpenAI
from app.models.story import StoryScene
from app.config import settings

class StoryService:
    def __init__(self, openai_client: OpenAI, user_service):
        self.openai_client = openai_client
        self.user_service = user_service
    
    async def generate_story_scenes(self, user_prompt: str, user_id: str) -> Tuple[List[StoryScene], str]:
        """Generate story scenes using OpenAI GPT"""
        try:
            # Get user-specific system prompt from Firebase
            user_profile = await self.user_service.get_user_profile(user_id)
            if not user_profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Extract user preferences from profile
            child_info = user_profile.get('child', {})
            child_name = child_info.get('name', 'the child')
            child_age = child_info.get('age', 6)
            child_interests = child_info.get('interests', [])
            
            # Get personalized system prompt from user profile
            system_prompt = user_profile.get('system_prompt', settings.default_system_prompt)
            
            # Create comprehensive story generation prompt
            story_generation_prompt = f"""
            Based on this user request: "{user_prompt}"
            
            Create a personalized story for {child_name} (age {child_age}) who loves {', '.join(child_interests) if child_interests else 'adventure and learning'}.
            
            Structure your response as exactly {settings.max_scenes} scenes. Each scene should be engaging and age-appropriate.
            
            For each scene, provide:
            1. The scene text
            2. A detailed visual description for DALL-E image generation anime style illustration
            
            Format your response as valid JSON:
            {{
                "title": "Story Title (include {child_name} if appropriate)",
                "scenes": [
                    {{
                        "scene_number": 1,
                        "text": "Scene text here",
                        "visual_prompt": "Detailed visual description for DALL-E image generation. Style: Children's book illustration, colorful and friendly..."
                    }},
                    {{
                        "scene_number": 2,
                        "text": "Scene text here...",
                        "visual_prompt": "Detailed visual description for DALL-E image generation. Style: Children's book illustration, colorful and friendly..."
                    }}
                ]
            }}
            
            Make the story educational, positive, and personalized for {child_name}'s interests.
            """
            
            # Generate story using OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": story_generation_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Parse the response
            story_content = response.choices[0].message.content
            print(f"Raw OpenAI response: {story_content}")
            
            try:
                story_data = json.loads(story_content)
            except json.JSONDecodeError:
                # Try to extract JSON from the response if it's wrapped in markdown
                if "```json" in story_content:
                    json_start = story_content.find("```json") + 7
                    json_end = story_content.find("```", json_start)
                    story_content = story_content[json_start:json_end].strip()
                    story_data = json.loads(story_content)
                else:
                    raise HTTPException(status_code=500, detail="Failed to parse story response as JSON")
            
            # Convert to StoryScene objects
            scenes = []
            for scene_data in story_data["scenes"]:
                scene = StoryScene(
                    scene_number=scene_data["scene_number"],
                    text=scene_data["text"],
                    visual_prompt=scene_data["visual_prompt"]
                )
                scenes.append(scene)
            
            title = story_data.get("title", f"A Story for {child_name}")
            
            return scenes, title
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Story generation error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")
    
    def generate_story_id(self) -> str:
        """Generate unique story ID"""
        return f"story_{uuid.uuid4().hex[:8]}"