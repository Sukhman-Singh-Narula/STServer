from pydantic import BaseModel
from typing import Dict, Any, Optional

class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    profile: Optional[Dict[str, Any]] = None

class TokenVerification(BaseModel):
    firebase_token: str