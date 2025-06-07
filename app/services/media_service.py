# ===== app/services/media_service.py =====
from typing import Union
from fastapi import HTTPException
from openai import OpenAI
from elevenlabs import generate, Voice
from app.config import settings

class MediaService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
    
    async def generate_audio(self, text: str, scene_number: int) -> bytes:
        """Generate audio using ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice=Voice(voice_id="21m00Tcm4TlvDq8ikWAM"),  # Rachel voice
                model="eleven_monolingual_v1"
            )
            return audio
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio generation failed for scene {scene_number}: {str(e)}")
    
    async def generate_image(self, visual_prompt: str, scene_number: int) -> str:
        """Generate image using OpenAI DALL-E"""
        try:
            # Enhance the prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly: {visual_prompt}"
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=settings.image_size,
                quality="standard",
                n=1
            )
            
            return response.data[0].url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image generation failed for scene {scene_number}: {str(e)}")