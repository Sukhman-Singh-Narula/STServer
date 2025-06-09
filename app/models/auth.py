# File: app/models/auth.py - Add proper token verification model
from pydantic import BaseModel
from typing import Dict, Any, Optional

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    profile: Optional[Dict[str, Any]] = None

class TokenVerification(BaseModel):
    firebase_token: str

# NEW: Add this model for the verify-token endpoint
class TokenVerificationRequest(BaseModel):
    firebase_token: str