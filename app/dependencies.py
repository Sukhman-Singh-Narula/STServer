# ===== app/dependencies.py =====
from fastapi import HTTPException, Depends
from firebase_admin import auth
from typing import Dict, Any
from app.models.auth import TokenVerification

async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {str(e)}")

async def get_current_user(token_data: TokenVerification) -> Dict[str, Any]:
    """Dependency to get current user from token"""
    return await verify_firebase_token(token_data.firebase_token)
