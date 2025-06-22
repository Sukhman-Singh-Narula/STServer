from datetime import datetime
from fastapi import APIRouter
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
            "dalle_2_enabled": settings.use_dalle_2_for_speed,
            "batch_audio_enabled": settings.enable_batch_audio,
            "batch_images_enabled": settings.enable_batch_images,
            "parallel_uploads_enabled": settings.enable_parallel_uploads
        },
        "ai_stack": "OpenAI TTS + DALL-E 2",
        "debug_mode": settings.debug
    }