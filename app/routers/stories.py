# ===== app/routers/stories.py - OPTIMIZED WITH PARALLEL PROCESSING =====
import asyncio
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

async def process_scene_optimized(scene, story_id, media_service, storage_service, scene_texts, scene_index):
    """Process a single scene with optimized parallel operations"""
    print(f"\n🎨 Processing scene {scene.scene_number}: {scene.text[:50]}...")
    
    try:
        # Step 1: Generate image (DALL-E 2 for speed)
        print(f"🖼️ Generating image for scene {scene.scene_number} with DALL-E 2...")
        image_task = media_service.generate_image_dalle2(scene.visual_prompt, scene.scene_number)
        
        # Step 2: Get audio from batch processing (audio is already generated)
        print(f"🎵 Getting pre-generated audio for scene {scene.scene_number}...")
        
        # Wait for image generation to complete
        image_data = await image_task
        print(f"✅ Image generated: {len(image_data)} bytes")
        
        # Get the corresponding audio data from batch processing
        audio_data = scene_texts[scene_index]['audio_data']
        print(f"✅ Audio data retrieved: {len(audio_data)} bytes")
        
        # Step 3: Upload both files in parallel to Firebase
        print(f"☁️ Uploading audio and image to Firebase in parallel...")
        upload_tasks = [
            storage_service.upload_audio(audio_data, story_id, scene.scene_number),
            storage_service.upload_image_data(image_data, story_id, scene.scene_number)
        ]
        
        audio_url, image_url = await asyncio.gather(*upload_tasks)
        
        print(f"✅ Parallel upload completed:")
        print(f"  Audio: {audio_url}")
        print(f"  Image: {image_url}")
        
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

async def process_scenes_parallel_optimized(scenes, story_id, media_service, storage_service):
    """Process all scenes in parallel with batch audio AND batch image generation"""
    print(f"\n🔥 Starting FULLY OPTIMIZED parallel processing for {len(scenes)} scenes...")
    
    # Step 1: Extract all scene texts for batch audio generation
    scene_texts = [{"text": scene.text, "scene_number": scene.scene_number} for scene in scenes]
    
    # Step 2: Extract all visual prompts for batch image generation
    visual_prompts = [{"visual_prompt": scene.visual_prompt, "scene_number": scene.scene_number} for scene in scenes]
    
    # Step 3: Generate ALL audio and ALL images in parallel (major optimization!)
    print(f"🚀 Generating ALL audio and ALL images in parallel...")
    
    # Run both batch operations simultaneously
    batch_tasks = [
        media_service.generate_audio_batch(scene_texts),
        media_service.generate_image_batch(visual_prompts)
    ]
    
    audio_batch, image_batch = await asyncio.gather(*batch_tasks)
    
    print(f"✅ Parallel batch generation completed:")
    print(f"  Audio files: {len(audio_batch)}")
    print(f"  Image files: {len(image_batch)}")
    
    # Step 4: Upload all media files in parallel
    print(f"☁️ Uploading all media files to Firebase in parallel...")
    
    # Create upload tasks for all media files
    upload_tasks = []
    for i, scene in enumerate(scenes):
        # Upload audio and image for each scene in parallel
        scene_upload_tasks = [
            storage_service.upload_audio(audio_batch[i], story_id, scene.scene_number),
            storage_service.upload_image_data(image_batch[i], story_id, scene.scene_number)
        ]
        upload_tasks.extend(scene_upload_tasks)
    
    # Execute all uploads in parallel
    upload_results = await asyncio.gather(*upload_tasks)
    
    # Process results and update scenes
    processed_scenes = []
    for i, scene in enumerate(scenes):
        # Get URLs from upload results
        audio_url = upload_results[i * 2]      # Even indices are audio URLs
        image_url = upload_results[i * 2 + 1]  # Odd indices are image URLs
        
        # Calculate timing
        audio_duration = calculate_audio_duration(scene.text)
        
        # Update scene with URLs and timing
        scene.audio_url = audio_url
        scene.image_url = image_url
        scene.start_time = 0  # Will be calculated later
        
        processed_scenes.append((scene, audio_duration))
        
        print(f"✅ Scene {scene.scene_number} processed with parallel uploads:")
        print(f"  Audio: {audio_url}")
        print(f"  Image: {image_url}")
    
    print(f"🎉 ALL {len(processed_scenes)} scenes processed with FULL parallelization!")
    return processed_scenes

@router.post("/generate")
async def generate_story_async(
    request: StoryPromptRequest,
    response: Response,
    story_service: StoryService = Depends(get_story_service),
    media_service: MediaService = Depends(get_media_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Start story generation asynchronously and return story_id immediately"""
    add_cors_headers(response)
    
    try:
        print(f"🎬 Starting ASYNC story generation for prompt: {request.prompt}")
        
        # Verify Firebase token
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        print(f"👤 Verified user: {user_id}")
        
        # Generate unique story ID
        story_id = story_service.generate_story_id()
        print(f"📖 Generated story ID: {story_id}")
        
        # Create initial story record with "processing" status
        initial_manifest = {
            "story_id": story_id,
            "title": "Generating...",
            "user_prompt": request.prompt,
            "total_scenes": 0,
            "total_duration": 0,
            "scenes": [],
            "generated_at": "now",
            "status": "processing",
            "generation_method": "fully_optimized_parallel_dalle2_openai_tts",
            "optimizations": [
                "parallel_scene_processing",
                "dalle2_for_speed", 
                "batch_openai_tts_generation",
                "batch_dalle2_image_generation",
                "parallel_firebase_uploads",
                "full_parallelization"
            ]
        }
        
        # Save initial story metadata with "processing" status
        await storage_service.save_story_metadata(
            story_id, user_id, "Generating...", request.prompt, initial_manifest
        )
        
        # Start background task for story generation
        asyncio.create_task(
            generate_story_background(
                story_id, request.prompt, user_id, 
                story_service, media_service, storage_service
            )
        )
        
        print(f"✅ Story generation started in background: {story_id}")
        
        # Return immediately with story_id
        return {
            "success": True,
            "message": f"Story generation started! Use story_id to check progress.",
            "story_id": story_id,
            "status": "processing",
            "estimated_completion_time": "30-60 seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to start story generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start story generation: {str(e)}")

async def generate_story_background(
    story_id: str, 
    prompt: str, 
    user_id: str,
    story_service: StoryService,
    media_service: MediaService,
    storage_service: StorageService
):
    """Background task to generate the complete story"""
    try:
        print(f"🔄 Background generation started for story: {story_id}")
        
        # Generate story scenes using OpenAI (fetches user prompt from Firebase)
        print("🤖 Generating story scenes with OpenAI...")
        scenes, title = await story_service.generate_story_scenes(prompt, user_id)
        print(f"✅ Generated {len(scenes)} scenes for story: {title}")
        
        # Update story with title and "generating_media" status
        await storage_service.update_story_status_and_title(story_id, "generating_media", title)
        
        # Process all scenes with FULLY optimized parallel processing
        processed_scenes_with_duration = await process_scenes_parallel_optimized(
            scenes, story_id, media_service, storage_service
        )
        
        # Extract scenes and calculate timings
        processed_scenes = []
        current_time = 0
        
        for scene_result in processed_scenes_with_duration:
            if isinstance(scene_result, tuple):
                scene, duration = scene_result
            else:
                scene = scene_result
                duration = calculate_audio_duration(scene.text)
            
            # Set start time
            scene.start_time = current_time
            processed_scenes.append(scene)
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
            "user_prompt": prompt,
            "total_scenes": len(processed_scenes),
            "total_duration": current_time,
            "scenes": scenes_data,
            "generated_at": "now",
            "status": "completed",
            "generation_method": "fully_optimized_parallel_dalle2_openai_tts",
            "optimizations": [
                "parallel_scene_processing",
                "dalle2_for_speed", 
                "batch_openai_tts_generation",
                "batch_dalle2_image_generation",
                "parallel_firebase_uploads",
                "full_parallelization"
            ]
        }
        
        print(f"💾 Saving completed story metadata to Firebase...")
        # Save final story metadata
        await storage_service.save_story_metadata(
            story_id, user_id, title, prompt, manifest
        )
        print(f"✅ Background story generation completed successfully: {story_id}")
        
    except Exception as e:
        print(f"❌ Background story generation failed for {story_id}: {str(e)}")
        # Update story with error status
        error_manifest = {
            "story_id": story_id,
            "title": "Generation Failed",
            "user_prompt": prompt,
            "status": "failed",
            "error": str(e),
            "generated_at": "now"
        }
        await storage_service.save_story_metadata(
            story_id, user_id, "Generation Failed", prompt, error_manifest
        )

@router.get("/fetch/{story_id}")
async def fetch_story_status(
    story_id: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Fetch story status and data - for ESP32 polling"""
    add_cors_headers(response)
    
    try:
        print(f"📡 Fetching story status for: {story_id}")
        
        # Get story details from Firestore
        story_details = await storage_service.get_story_details(story_id)
        
        if not story_details:
            return {
                "success": False,
                "status": "not_found",
                "message": "Story not found"
            }
        
        story_status = story_details.get('status', 'unknown')
        
        if story_status == "completed":
            # Return the complete story in the same format as the original generate endpoint
            manifest = story_details.get('manifest', story_details)
            
            return {
                "success": True,
                "message": f"Story '{manifest.get('title', 'Unknown')}' generated successfully!",
                "story": manifest,
                "performance_info": {
                    "optimizations_used": manifest.get("optimizations", []),
                    "total_scenes": manifest.get("total_scenes", 0),
                    "generation_method": "parallel_processing"
                }
            }
            
        elif story_status == "failed":
            return {
                "success": False,
                "status": "failed",
                "message": f"Story generation failed: {story_details.get('error', 'Unknown error')}",
                "story_id": story_id
            }
            
        else:
            # Still processing
            return {
                "success": False,
                "status": story_status,
                "message": f"Story is still generating... Status: {story_status}",
                "story_id": story_id,
                "title": story_details.get('title', 'Generating...'),
                "estimated_completion": "Check again in 5-10 seconds"
            }
        
    except Exception as e:
        print(f"❌ Error fetching story {story_id}: {str(e)}")
        return {
            "success": False,
            "status": "error", 
            "message": f"Error fetching story: {str(e)}",
            "story_id": story_id
        }

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
@router.options("/fetch/{story_id}")
@router.options("/system-prompt")
@router.options("/list/{user_token}")
@router.options("/details/{story_id}")
async def stories_options(response: Response):
    """Handle preflight OPTIONS requests for stories endpoints"""
    add_cors_headers(response)
    return {"message": "OK"}