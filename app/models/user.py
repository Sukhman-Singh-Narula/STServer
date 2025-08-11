from pydantic import BaseModel, EmailStr
from typing import List, Optional

class ChildProfile(BaseModel):
    name: str
    age: int
    interests: List[str]
    image_url: Optional[str] = None  # URL to child's profile image
    avatar_seed: Optional[str] = None  # Custom seed for avatar generation
    avatar_style: Optional[str] = "avataaars"  # Avatar style (avataaars, etc.)
    avatar_generated: Optional[bool] = False  # Whether avatar has been generated

class ParentProfile(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    avatar_seed: Optional[str] = None  # Custom seed for parent avatar
    avatar_style: Optional[str] = "avataaars"  # Avatar style
    avatar_generated: Optional[bool] = False  # Whether avatar has been generated

class UserRegistration(BaseModel):
    firebase_token: str
    parent: ParentProfile
    child: ChildProfile
    system_prompt: Optional[str] = None
    child_image_base64: Optional[str] = None  # Base64 encoded image data

class UserProfileUpdate(BaseModel):
    firebase_token: str
    parent: Optional[ParentProfile] = None
    child: Optional[ChildProfile] = None
    system_prompt: Optional[str] = None
    child_image_base64: Optional[str] = None  # Base64 encoded image data

class UserProfileResponse(BaseModel):
    user_id: str
    parent: ParentProfile
    child: ChildProfile
    system_prompt: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    story_count: Optional[int] = 0
    last_active: Optional[str] = None

class AvatarUpdateRequest(BaseModel):
    firebase_token: str
    target: str  # "child" or "parent"
    avatar_seed: str
    avatar_style: Optional[str] = "avataaars"