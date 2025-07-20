from pydantic import BaseModel, EmailStr
from typing import List, Optional

class ChildProfile(BaseModel):
    name: str
    age: int
    interests: List[str]
    image_url: Optional[str] = None  # URL to child's profile image

class ParentProfile(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None

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