# ===== app/routers/stories.py - UPDATED FOR BASE64 IMAGE HANDLING =====
from fastapi import APIRouter, HTTPException, Depends, Response
from app.models.story import StoryPromptRequest, SystemPromptUpdate
from app.services.story_service import StoryService
from app.services.media_service import MediaService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from app.dependencies import verify_firebase_token
from app.utils.helpers import calculate_audio_duration
from openai import OpenAI
from app.config import settings

router = APIRouter(prefix="/stories", tags=["stories"])

# Initialize services with OpenAI client
def get_user_service():
    return UserService()

def get_openai_client():
    return OpenAI(api_key=settings.openai_api_key)

def get_story_service(
    openai_client: OpenAI = Depends(get_openai_client),
    user_service: UserService = Depends(get_user_service)
):
    return StoryService(openai_client, user_service)

def get_media_service(openai_client: OpenAI = Depends(get_openai_client)):
    return MediaService(openai_client)

def get_storage_service():
    return StorageService()

def add_cors_headers(response: Response):
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"

async def process_scene_with_base64_images(scene, story_id, media_service, storage_service):
    """Process a single scene with base64 image handling (no URL expiration issues)"""
    print(f"\n🎨 Processing scene {scene.scene_number}: {scene.text[:50]}...")
    
    try:
        # Step 1: Generate audio (fast with ElevenLabs)
        print(f"🎵 Generating audio for scene {scene.scene_number}...")
        audio_data = await media_service.generate_audio(scene.text, scene.scene_number)
        print(f"✅ Audio generated: {len(audio_data)} bytes")
        
        # Step 2: Generate image as base64 data (no URL expiration issues)
        print(f"🖼️ Generating image for scene {scene.scene_number}...")
        image_data = await media_service.generate_image(scene.visual_prompt, scene.scene_number)
        print(f"✅ Image generated as binary data: {len(image_data)} bytes")
        
        # Step 3: Upload image data directly to Firebase (no download needed)
        print(f"☁️ Uploading image data to Firebase...")
        image_url = await storage_service.upload_image_data(image_data, story_id, scene.scene_number)
        print(f"✅ Image uploaded: {image_url}")
        
        # Step 4: Upload audio to Firebase Storage
        print(f"☁️ Uploading audio to Firebase...")
        audio_url = await storage_service.upload_audio(audio_data, story_id, scene.scene_number)
        print(f"✅ Audio uploaded: {audio_url}")
        
        # Calculate timing
        audio_duration = calculate_audio_duration(scene.text)
        
        # Update scene with URLs and timing
        scene.audio_url = audio_url
        scene.image_url = image_url
        scene.start_time = 0  # Will be calculated later
        
        print(f"✅ Scene {scene.scene_number} processed successfully")
        return scene, audio_duration
        
    except Exception as scene_error:
        print(f"❌ Error processing scene {scene.scene_number}: {str(scene_error)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process scene {scene.scene_number}: {str(scene_error)}"
        )

@router.post("/generate")
async def generate_story(
    request: StoryPromptRequest,
    response: Response,
    story_service: StoryService = Depends(get_story_service),
    media_service: MediaService = Depends(get_media_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Main endpoint to generate a complete story with base64 image handling"""
    add_cors_headers(response)
    
    try:
        print(f"🎬 Starting story generation for prompt: {request.prompt}")
        
        # Verify Firebase token
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        print(f"👤 Verified user: {user_id}")
        
        # Generate unique story ID
        story_id = story_service.generate_story_id()
        print(f"📖 Generated story ID: {story_id}")
        
        # Generate story scenes using OpenAI (fetches user prompt from Firebase)
        print("🤖 Generating story scenes with OpenAI...")
        scenes, title = await story_service.generate_story_scenes(request.prompt, user_id)
        print(f"✅ Generated {len(scenes)} scenes for story: {title}")
        
        # Process all scenes with base64 image handling
        processed_scenes = []
        current_time = 0
        
        for scene in scenes:
            processed_scene, duration = await process_scene_with_base64_images(
                scene, story_id, media_service, storage_service
            )
            
            # Set start time
            processed_scene.start_time = current_time
            processed_scenes.append(processed_scene)
            current_time += duration
        
        # Build comprehensive manifest with scene-wise data
        scenes_data = []
        for scene in processed_scenes:
            scene_data = {
                "scene_number": scene.scene_number,
                "text": scene.text,
                "visual_prompt": scene.visual_prompt,
                "audio_url": scene.audio_url,
                "image_url": scene.image_url,
                "start_time": scene.start_time,
                "duration": calculate_audio_duration(scene.text)
            }
            scenes_data.append(scene_data)
        
        # Create final manifest
        manifest = {
            "story_id": story_id,
            "title": title,
            "user_prompt": request.prompt,
            "total_scenes": len(processed_scenes),
            "total_duration": current_time,
            "scenes": scenes_data,
            "generated_at": "now",
            "status": "completed"
        }
        
        print(f"💾 Saving story metadata to Firebase...")
        # Save to Firestore
        await storage_service.save_story_metadata(
            story_id, user_id, title, request.prompt, manifest
        )
        print(f"✅ Story saved successfully!")
        
        # Return the complete manifest
        return {
            "success": True,
            "message": f"Story '{title}' generated successfully!",
            "story": manifest
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Story generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

@router.post("/system-prompt")
async def update_system_prompt(
    request: SystemPromptUpdate,
    response: Response,
    user_service: UserService = Depends(get_user_service)
):
    """Update system prompt for a user"""
    add_cors_headers(response)
    
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

@router.get("/list/{user_token}")
async def get_user_stories(
    user_token: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get all stories for a user (summary list)"""
    add_cors_headers(response)
    
    try:
        user_info = await verify_firebase_token(user_token)
        user_id = user_info['uid']
        
        story_list = await storage_service.get_user_stories(user_id)
        return {"stories": story_list}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/details/{story_id}")
async def get_story_details(
    story_id: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get complete story details including all scenes data"""
    add_cors_headers(response)
    
    try:
        story_details = await storage_service.get_story_details(story_id)
        return {
            "success": True,
            "story": story_details
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.options("/generate")
@router.options("/system-prompt")
@router.options("/list/{user_token}")
@router.options("/details/{story_id}")
async def stories_options(response: Response):
    """Handle preflight OPTIONS requests for stories endpoints"""
    add_cors_headers(response)
    return {"message": "OK"}