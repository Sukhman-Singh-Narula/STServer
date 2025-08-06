from datetime import datetime
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import requests
import io
from app.config import settings
from app.utils.firebase_init import is_firebase_available

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "firebase": "connected" if is_firebase_available() else "not_connected",
            "groq": "configured" if settings.groq_api_key and settings.groq_api_key != "test" else "not_configured",
            "openai": "configured" if settings.openai_api_key and settings.openai_api_key != "test" else "not_configured"
        },
        "optimizations": {
            "parallel_processing": settings.max_concurrent_scenes,
            "replicate_sdxl_enabled": True,
            "batch_audio_enabled": settings.enable_batch_audio,
            "batch_images_enabled": settings.enable_batch_images,
            "parallel_uploads_enabled": settings.enable_parallel_uploads
        },
        "ai_stack": "OpenAI TTS + Replicate SDXL",
        "debug_mode": settings.debug
    }

@router.get("/audiotrial")
async def audio_trial():
    """Fetch and return WAV audio file from Firebase Storage"""
    try:
        # Firebase Storage URL for the test audio file
        audio_url = "https://firebasestorage.googleapis.com/v0/b/storyteller-7ece7.firebasestorage.app/o/stories%2Fstory_f501556e%2Faudio%2Fscene_1.mp3?alt=media&token=4720a3e6-11d3-4cc3-9ded-97a83acd46ad"
        
        print(f"🎵 Fetching audio from: {audio_url}")
        
        # Fetch the audio file from Firebase Storage
        response = requests.get(audio_url, timeout=30)
        
        if response.status_code == 200:
            # Get the audio data
            audio_data = response.content
            
            print(f"✅ Audio fetched successfully: {len(audio_data)} bytes")
            
            # Create an in-memory file-like object
            audio_stream = io.BytesIO(audio_data)
            
            # Return the audio as a streaming response with proper headers
            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/wav",
                headers={
                    "Content-Length": str(len(audio_data))
                }
            )
        else:
            print(f"❌ Failed to fetch audio: HTTP {response.status_code}")
            return {
                "error": "Failed to fetch audio file",
                "status_code": response.status_code,
                "url": audio_url
            }
            
    except Exception as e:
        print(f"❌ Audio trial failed: {str(e)}")
        return {
            "error": "Audio trial failed",
            "message": str(e),
            "url": audio_url
        }

@router.post("/test-voice")
async def test_voice_selection(request_data: dict):
    """Test endpoint to verify voice selection logic"""
    try:
        isfemale = request_data.get('isfemale', True)  # Default to True
        voice = "sage" if isfemale else "onyx"  # Updated to use valid OpenAI voice
        
        return {
            "isfemale": isfemale,
            "voice_selected": voice,
            "voice_type": "female" if isfemale else "male",
            "message": f"Would use {voice} voice for {'female' if isfemale else 'male'} narration"
        }
    except Exception as e:
        return {
            "error": "Voice selection test failed",
            "message": str(e)
        }