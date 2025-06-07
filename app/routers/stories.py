# ===== app/routers/stories.py =====
from fastapi import APIRouter, HTTPException
from app.models.story import StoryPromptRequest, SystemPromptUpdate
from app.services.story_service import StoryService
from app.services.media_service import MediaService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from app.dependencies import verify_firebase_token
from app.utils.helpers import calculate_audio_duration
from openai import OpenAI
import groq
from app.config import settings

router = APIRouter(prefix="/stories", tags=["stories"])

# Initialize services
user_service = UserService()
groq_client = groq.Groq(api_key=settings.groq_api_key)
openai_client = OpenAI(api_key=settings.openai_api_key)
story_service = StoryService(groq_client, user_service)
media_service = MediaService(openai_client)
storage_service = StorageService()

@router.post("/generate")
async def generate_story(request: StoryPromptRequest):
    """Main endpoint to generate a complete story with media"""
    try:
        # Verify Firebase token
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        
        # Generate unique story ID
        story_id = story_service.generate_story_id()
        
        # Generate story scenes
        scenes, title = await story_service.generate_story_scenes(request.prompt, user_id)
        
        # Process each scene
        processed_scenes = []
        current_time = 0
        
        for scene in scenes:
            # Generate audio
            audio_data = await media_service.generate_audio(scene.text, scene.scene_number)
            audio_url = await storage_service.upload_audio(audio_data, story_id, scene.scene_number)
            
            # Generate image
            temp_image_url = await media_service.generate_image(scene.visual_prompt, scene.scene_number)
            image_url = await storage_service.upload_image_from_url(temp_image_url, story_id, scene.scene_number)
            
            # Calculate timing
            audio_duration = calculate_audio_duration(scene.text)
            
            scene.audio_url = audio_url
            scene.image_url = image_url
            scene.start_time = current_time
            
            processed_scenes.append(scene)
            current_time += audio_duration
        
        # Build manifest
        segments = []
        for scene in processed_scenes:
            # Add image segment
            segments.append({
                "type": "image",
                "url": scene.image_url,
                "start": scene.start_time
            })
            # Add audio segment
            segments.append({
                "type": "audio",
                "url": scene.audio_url,
                "start": scene.start_time
            })
        
        manifest = {
            "story_id": story_id,
            "title": title,
            "total_duration": current_time,
            "segments": segments
        }
        
        # Save to Firestore
        await storage_service.save_story_metadata(
            story_id, user_id, title, request.prompt, manifest
        )
        
        return manifest
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

@router.post("/system-prompt")
async def update_system_prompt(request: SystemPromptUpdate):
    """Update system prompt for a user"""
    try:
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        
        # Update system prompt
        user_service.update_system_prompt(user_id, request.system_prompt)
        
        return {
            "success": True,
            "message": "System prompt updated successfully",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_token}")
async def get_user_stories(user_token: str):
    """Get all stories for a user"""
    try:
        user_info = await verify_firebase_token(user_token)
        user_id = user_info['uid']
        
        story_list = await storage_service.get_user_stories(user_id)
        return {"stories": story_list}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))