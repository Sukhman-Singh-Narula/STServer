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
            "openai": "configured" if settings.openai_api_key and settings.openai_api_key != "test" else "not_configured",
            "elevenlabs": "configured" if settings.elevenlabs_api_key and settings.elevenlabs_api_key != "test" else "not_configured"
        },
        "debug_mode": settings.debug
    }