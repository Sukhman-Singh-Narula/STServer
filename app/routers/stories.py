# ===== ENHANCED STORIES ROUTER WITH STORY ID ARRAY SUPPORT =====
# Replace your app/routers/stories.py with this enhanced version

import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Response, Query
from app.models.story import StoryPromptRequest, SystemPromptUpdate
from app.services.story_service import StoryService
from app.services.media_service import MediaService
from app.services.storage_service import StorageService
from app.services.user_service import UserService
from app.dependencies import verify_firebase_token
from app.utils.helpers import calculate_audio_duration
from openai import OpenAI
from app.config import settings
from app.models.auth import TokenVerificationRequest

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

# ===== STORY GENERATION (Keep existing methods) =====

async def process_scenes_parallel_optimized(scenes, story_id, media_service, storage_service, user_profile=None, isfemale=True, target_dimensions=(1200, 2600)):
    """Process all scenes in parallel with batch audio AND batch image generation"""
    width, height = target_dimensions
    print(f"\n🔥 Starting FULLY OPTIMIZED parallel processing for {len(scenes)} scenes at {width}x{height}...")
    
    # Extract child information from user profile
    child_info = user_profile.get('child', {}) if user_profile else {}
    child_name = child_info.get('name', 'the child')
    child_image_url = child_info.get('image_url')
    
    # Step 1: Extract all scene texts for batch audio generation
    scene_texts = [{"text": scene.text, "scene_number": scene.scene_number} for scene in scenes]
    
    # Step 2: Extract all visual prompts for batch image generation with child info
    visual_prompts = []
    for scene in scenes:
        prompt_data = {
            "visual_prompt": scene.visual_prompt,
            "scene_number": scene.scene_number,
            "includes_child": scene.includes_child,
            "child_name": child_name,
            "child_image_url": child_image_url
        }
        visual_prompts.append(prompt_data)
    
    # Step 3: Generate ALL audio and ALL images in parallel (major optimization!)
    print(f"🚀 Generating ALL audio and ALL images in parallel...")
    
    # Run both batch operations simultaneously
    batch_tasks = [
        media_service.generate_audio_batch(scene_texts, isfemale=isfemale),
        media_service.generate_image_batch(visual_prompts, child_image_url, target_dimensions)
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
        # Upload audio and both image versions for each scene in parallel
        scene_upload_tasks = [
            storage_service.upload_audio(audio_batch[i], story_id, scene.scene_number),
            storage_service.upload_both_images(image_batch[i], story_id, scene.scene_number)
        ]
        upload_tasks.extend(scene_upload_tasks)
    
    # Execute all uploads in parallel
    upload_results = await asyncio.gather(*upload_tasks)
    
    # Process results and update scenes
    processed_scenes = []
    for i, scene in enumerate(scenes):
        # Get URLs from upload results
        audio_url = upload_results[i * 2]      # Even indices are audio URLs
        image_urls = upload_results[i * 2 + 1]  # Odd indices are image URL dictionaries
        
        # Calculate timing
        audio_duration = calculate_audio_duration(scene.text)
        
        # Update scene with URLs and timing
        scene.audio_url = audio_url
        scene.image_url = image_urls["grayscale_url"]  # Keep grayscale for backward compatibility
        scene.colored_image_url = image_urls["colored_url"]  # Add colored image URL
        scene.start_time = 0  # Will be calculated later
        
        processed_scenes.append((scene, audio_duration))
        
        print(f"✅ Scene {scene.scene_number} processed with parallel uploads:")
        print(f"  Audio: {audio_url}")
        print(f"  Image (grayscale): {scene.image_url}")
        print(f"  Image (colored): {scene.colored_image_url}")
    
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
            "generation_method": "fully_optimized_parallel_dalle2_openai_tts_with_id_arrays",
            "optimizations": [
                "parallel_scene_processing",
                "dalle2_for_speed", 
                "batch_openai_tts_generation",
                "batch_dalle2_image_generation",
                "parallel_firebase_uploads",
                "story_id_array_tracking",
                "full_parallelization"
            ]
        }
        
        # Save initial story metadata with "processing" status and add to user's story_ids array
        await storage_service.save_story_metadata(
            story_id, user_id, "Generating...", request.prompt, initial_manifest
        )
        
        # Start background task for story generation
        asyncio.create_task(
            generate_story_background(
                story_id, request.prompt, user_id, 
                story_service, media_service, storage_service,
                isfemale=request.isfemale,
                dimensions=request.dimensions
            )
        )
        
        print(f"✅ Story generation started in background: {story_id}")
        print(f"📋 Story ID added to user {user_id}'s story_ids array")
        
        # Return immediately with story_id
        return {
            "success": True,
            "message": f"Story generation started! Story ID added to your collection.",
            "story_id": story_id,
            "status": "processing",
            "estimated_completion_time": "30-60 seconds",
            "tracking_method": "story_id_array"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to start story generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start story generation: {str(e)}")

def parse_dimensions(dimensions_str: str) -> tuple:
    """Parse dimensions string like '932x430' into tuple (932, 430)"""
    try:
        width, height = dimensions_str.split('x')
        return (int(width), int(height))
    except:
        # Default to portrait if parsing fails
        return (1200, 2600)

async def generate_story_background(
    story_id: str, 
    prompt: str, 
    user_id: str,
    story_service: StoryService,
    media_service: MediaService,
    storage_service: StorageService,
    isfemale: bool = True,
    dimensions: str = "1200x2600"
):
    """Background task to generate the complete story with story ID array tracking"""
    try:
        print(f"🔄 Background generation started for story: {story_id}")
        print(f"🖼️ Using custom dimensions: {dimensions}")
        
        # Parse dimensions
        target_dimensions = parse_dimensions(dimensions)
        width, height = target_dimensions
        print(f"📐 Parsed dimensions: {width}x{height}")
        
        # Get user profile for child information
        user_service = UserService()
        user_profile = await user_service.get_user_profile(user_id)
        
        # Generate story scenes using OpenAI (fetches user prompt from Firebase)
        print("🤖 Generating story scenes with OpenAI...")
        scenes, title = await story_service.generate_story_scenes(prompt, user_id)
        print(f"✅ Generated {len(scenes)} scenes for story: {title}")
        
        # Update story with title and "generating_media" status
        await storage_service.update_story_status_and_title(story_id, "generating_media", title)
        
        # Process all scenes with FULLY optimized parallel processing
        processed_scenes_with_duration = await process_scenes_parallel_optimized(
            scenes, story_id, media_service, storage_service, user_profile, isfemale=isfemale, target_dimensions=target_dimensions
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
                "image_url": scene.image_url,  # Grayscale image (backward compatibility)
                "colored_image_url": scene.colored_image_url,  # Colored image
                "start_time": scene.start_time,
                "duration": calculate_audio_duration(scene.text),
                "includes_child": scene.includes_child  # Whether this scene includes the child
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
            "generation_method": "fully_optimized_parallel_replicate_sdxl_openai_tts_with_id_arrays",
            "optimizations": [
                "parallel_scene_processing",
                "replicate_sdxl_for_speed", 
                "batch_openai_tts_generation",
                "batch_replicate_sdxl_image_generation",
                "parallel_firebase_uploads",
                "story_id_array_tracking",
                "full_parallelization",
                "dual_image_storage_colored_and_grayscale"
            ]
        }
        
        print(f"💾 Saving completed story metadata to Firebase with ID array update...")
        # Save final story metadata (this will update the story in user's story_ids array)
        await storage_service.save_story_metadata(
            story_id, user_id, title, prompt, manifest
        )
        print(f"✅ Background story generation completed successfully: {story_id}")
        print(f"📋 Story {story_id} is now tracked in user {user_id}'s story_ids array")
        
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

async def cleanup_duplicate_story_ids(self, user_id: str = None):
    """Clean up duplicate story IDs in user documents"""
    try:
        if not self.db:
            return
        
        loop = asyncio.get_event_loop()
        
        def cleanup():
            if user_id:
                # Clean up specific user
                user_ref = self.db.collection('users').document(user_id)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    story_ids = user_data.get('story_ids', [])
                    
                    # Remove duplicates while preserving order
                    unique_story_ids = list(dict.fromkeys(story_ids))
                    
                    if len(unique_story_ids) != len(story_ids):
                        print(f"🧹 Cleaning up duplicates for user {user_id}: {len(story_ids)} -> {len(unique_story_ids)}")
                        
                        user_ref.update({
                            'story_ids': unique_story_ids,
                            'story_count': len(unique_story_ids),
                            'updated_at': datetime.utcnow()
                        })
            else:
                # Clean up all users
                users_ref = self.db.collection('users')
                users = users_ref.stream()
                
                for user_doc in users:
                    user_data = user_doc.to_dict()
                    story_ids = user_data.get('story_ids', [])
                    
                    # Remove duplicates while preserving order
                    unique_story_ids = list(dict.fromkeys(story_ids))
                    
                    if len(unique_story_ids) != len(story_ids):
                        print(f"🧹 Cleaning up duplicates for user {user_doc.id}: {len(story_ids)} -> {len(unique_story_ids)}")
                        
                        user_doc.reference.update({
                            'story_ids': unique_story_ids,
                            'story_count': len(unique_story_ids),
                            'updated_at': datetime.utcnow()
                        })
        
        await loop.run_in_executor(None, cleanup)
        print("✅ Duplicate story IDs cleanup completed")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")

# Add an endpoint to trigger cleanup
@router.post("/stories/cleanup-duplicates")
async def cleanup_duplicate_story_ids_endpoint(
    request: TokenVerificationRequest,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Clean up duplicate story IDs for the current user"""
    add_cors_headers(response)
    
    try:
        # Verify Firebase token
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        
        await storage_service.cleanup_duplicate_story_ids(user_id)
        
        return {
            "success": True,
            "message": "Duplicate story IDs cleaned up successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

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
                    "generation_method": "parallel_processing_with_id_arrays",
                    "tracking_method": "story_id_array"
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

# ===== ENHANCED USER STORY MANAGEMENT ENDPOINTS WITH STORY ID ARRAYS =====

@router.get("/user/{firebase_token}")
async def get_user_stories_endpoint(
    firebase_token: str,
    response: Response,
    limit: int = Query(20, ge=1, le=100, description="Number of stories to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of stories to skip"),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get all stories for a user using story ID arrays with full metadata
    
    This endpoint now uses the story_ids array from the user document for optimal performance.
    
    Usage examples:
    - GET /stories/user/{token} - Get first 20 stories using ID array
    - GET /stories/user/{token}?limit=10 - Get first 10 stories  
    - GET /stories/user/{token}?limit=10&offset=10 - Get stories 11-20
    """
    add_cors_headers(response)
    
    try:
        # Verify Firebase token and get user ID
        user_info = await verify_firebase_token(firebase_token)
        user_id = user_info['uid']
        
        print(f"📚 Fetching stories for user {user_id} using story ID array method")
        print(f"   Pagination: limit={limit}, offset={offset}")
        
        # Get user stories using the enhanced story ID array method
        result = await storage_service.get_user_stories_using_id_array(user_id, limit=limit, offset=offset)
        
        # Enhance response with summary statistics
        response_data = {
            "success": True,
            "user_id": user_id,
            "stories": result["stories"],
            "pagination": result.get("pagination", {}),
            "user_info": result["user_info"],
            "summary": {
                "total_stories_created": result["total_count"],
                "newest_story": result["stories"][0] if result["stories"] else None,
                "stories_this_page": len(result["stories"]),
                "method_used": result.get("method_used", "story_id_array"),
                "performance_info": result.get("performance_info", {})
            },
            "tracking_info": {
                "uses_story_id_array": True,
                "story_ids_array_length": result.get("user_info", {}).get("story_ids_array_length", 0),
                "batch_fetched": True,
                "optimized_for_user_queries": True
            }
        }
        
        print(f"✅ Found {result['total_count']} total stories for user {user_id}")
        print(f"📋 Method used: {result.get('method_used', 'story_id_array')}")
        print(f"📊 Performance: {result.get('performance_info', {})}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching user stories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stories: {str(e)}")

@router.get("/user/{firebase_token}/summary")
async def get_user_stories_summary(
    firebase_token: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get a quick summary of user's story creation activity using story ID arrays"""
    add_cors_headers(response)
    
    try:
        # Verify Firebase token and get user ID
        user_info = await verify_firebase_token(firebase_token)
        user_id = user_info['uid']
        
        # Get basic story count and latest stories using ID array method
        result = await storage_service.get_user_stories_using_id_array(user_id, limit=5, offset=0)
        
        summary = {
            "success": True,
            "user_id": user_id,
            "total_stories": result["total_count"],
            "latest_stories": result["stories"][:3],  # Just the 3 most recent
            "user_info": result["user_info"],
            "activity": {
                "has_stories": result["total_count"] > 0,
                "recent_activity": result["stories"][:5] if result["stories"] else []
            },
            "tracking_method": {
                "uses_story_id_array": True,
                "method": result.get("method_used", "story_id_array"),
                "story_ids_count": result.get("user_info", {}).get("story_ids_array_length", 0)
            }
        }
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

@router.get("/user/{firebase_token}/story-ids")
async def get_user_story_ids(
    firebase_token: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get just the story IDs array for a user (useful for quick checks)"""
    add_cors_headers(response)
    
    try:
        # Verify Firebase token and get user ID
        user_info = await verify_firebase_token(firebase_token)
        user_id = user_info['uid']
        
        print(f"📋 Fetching story IDs array for user {user_id}")
        
        # Get story IDs array
        story_ids = await storage_service.get_user_story_ids(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "story_ids": story_ids,
            "total_count": len(story_ids),
            "newest_first": list(reversed(story_ids)),  # Newest first
            "oldest_first": story_ids,  # As stored (oldest first)
            "summary": {
                "has_stories": len(story_ids) > 0,
                "latest_story_id": story_ids[-1] if story_ids else None,
                "oldest_story_id": story_ids[0] if story_ids else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch story IDs: {str(e)}")

@router.delete("/user/{firebase_token}/story/{story_id}")
async def delete_user_story(
    firebase_token: str,
    story_id: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Delete a specific story for a user and remove from story_ids array"""
    add_cors_headers(response)
    
    try:
        # Verify Firebase token and get user ID
        user_info = await verify_firebase_token(firebase_token)
        user_id = user_info['uid']
        
        print(f"🗑️ Deleting story {story_id} for user {user_id}")
        print(f"📋 Will also remove from user's story_ids array")
        
        # Delete the story (this also updates the story_ids array)
        success = await storage_service.delete_user_story(story_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": f"Story {story_id} deleted successfully and removed from your story collection",
                "story_id": story_id,
                "tracking_info": {
                    "removed_from_story_ids_array": True,
                    "story_count_decremented": True
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Story not found or access denied")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete story: {str(e)}")

# ===== LEGACY ENDPOINTS (KEEP FOR COMPATIBILITY) =====

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
async def get_user_stories_legacy(
    user_token: str,
    response: Response,
    storage_service: StorageService = Depends(get_storage_service)
):
    """Get all stories for a user (legacy endpoint - redirects to new ID array method)"""
    add_cors_headers(response)
    
    try:
        user_info = await verify_firebase_token(user_token)
        user_id = user_info['uid']
        
        result = await storage_service.get_user_stories_using_id_array(user_id, limit=50, offset=0)
        return {
            "stories": result["stories"],
            "total_count": result["total_count"],
            "user_info": result["user_info"],
            "legacy_endpoint_notice": "This endpoint now uses the optimized story ID array method"
        }
        
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

# ===== OPTIONS HANDLERS =====

@router.options("/generate")
@router.options("/fetch/{story_id}")
@router.options("/system-prompt")
@router.options("/list/{user_token}")
@router.options("/details/{story_id}")
@router.options("/user/{firebase_token}")
@router.options("/user/{firebase_token}/summary") 
@router.options("/user/{firebase_token}/story/{story_id}")
@router.options("/user/{firebase_token}/story-ids")
async def stories_options(response: Response):
    """Handle preflight OPTIONS requests for all story endpoints"""
    add_cors_headers(response)
    return {"message": "OK"}