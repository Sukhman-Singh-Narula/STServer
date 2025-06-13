# ===== app/services/media_service.py - FIXED DALL-E IMAGE HANDLING =====
import io
import base64
from typing import Union
from fastapi import HTTPException
from openai import OpenAI
from app.config import settings

class MediaService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
    
    async def generate_audio(self, text: str, scene_number: int) -> bytes:
        """Generate audio using ElevenLabs TTS (faster than OpenAI)"""
        try:
            # Check if ElevenLabs is available
            if not settings.elevenlabs_api_key or settings.elevenlabs_api_key == "test":
                print(f"⚠️ ElevenLabs not configured, falling back to OpenAI TTS")
                return await self.generate_audio_openai(text, scene_number)
            
            # Use ElevenLabs for faster TTS
            from elevenlabs import generate, Voice
            
            print(f"🎵 Using ElevenLabs TTS for scene {scene_number}")
            
            audio = generate(
                text=text,
                voice=Voice(voice_id="21m00Tcm4TlvDq8ikWAM"),  # Rachel voice (child-friendly)
                model="eleven_monolingual_v1"
            )
            
            print(f"✅ ElevenLabs audio generated for scene {scene_number}: {len(audio)} bytes")
            return audio
            
        except ImportError:
            print(f"⚠️ ElevenLabs not installed, falling back to OpenAI TTS")
            return await self.generate_audio_openai(text, scene_number)
        except Exception as e:
            print(f"❌ ElevenLabs TTS error for scene {scene_number}: {str(e)}")
            print(f"🔄 Falling back to OpenAI TTS...")
            return await self.generate_audio_openai(text, scene_number)
    
    async def generate_audio_openai(self, text: str, scene_number: int) -> bytes:
        """Fallback: Generate audio using OpenAI Text-to-Speech"""
        try:
            print(f"🎵 Using OpenAI TTS for scene {scene_number}")
            
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # Faster model
                voice="nova",   # Child-friendly voice
                input=text,
                response_format="mp3"
            )
            
            # Convert response to bytes
            audio_bytes = b""
            for chunk in response.iter_bytes():
                audio_bytes += chunk
                
            print(f"✅ OpenAI audio generated for scene {scene_number}: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            print(f"❌ OpenAI TTS error for scene {scene_number}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Audio generation failed for scene {scene_number}: {str(e)}"
            )
    
    async def generate_image(self, visual_prompt: str, scene_number: int) -> bytes:
        """Generate image using OpenAI DALL-E and return image data directly"""
        try:
            print(f"🖼️ Generating image for scene {scene_number}")
            
            # Enhance the prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            # Request image with base64 response format to avoid URL expiration issues
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=settings.image_size,
                quality="standard",
                n=1,
                response_format="b64_json"  # Get base64 data instead of URL
            )
            
            # Extract base64 image data
            image_b64 = response.data[0].b64_json
            image_data = base64.b64decode(image_b64)
            
            print(f"✅ Image generated for scene {scene_number}: {len(image_data)} bytes")
            return image_data
            
        except Exception as e:
            print(f"❌ DALL-E error for scene {scene_number}: {str(e)}")
            
            # Fallback: try URL method if base64 fails
            try:
                print(f"🔄 Trying fallback URL method for scene {scene_number}...")
                return await self.generate_image_url_fallback(visual_prompt, scene_number)
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Image generation failed for scene {scene_number}: {str(e)}"
                )
    
    async def generate_image_url_fallback(self, visual_prompt: str, scene_number: int) -> bytes:
        """Fallback: Generate image with URL method and immediately download"""
        import httpx
        
        try:
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=settings.image_size,
                quality="standard",
                n=1,
                response_format="url"
            )
            
            image_url = response.data[0].url
            print(f"🔗 Generated URL, attempting immediate download...")
            
            # Immediately download with aggressive timeout settings
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                download_response = await client.get(image_url)
                download_response.raise_for_status()
                
                image_data = download_response.content
                print(f"✅ Fallback download successful: {len(image_data)} bytes")
                return image_data
                
        except Exception as e:
            print(f"❌ Fallback method failed: {str(e)}")
            raise e