from pydantic import BaseModel, EmailStr
from typing import List, Optional

class ChildProfile(BaseModel):
    name: str
    age: int
    interests: List[str]

class ParentProfile(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None

class UserRegistration(BaseModel):
    firebase_token: str
    parent: ParentProfile
    child: ChildProfile
    system_prompt: Optional[str] = None

class UserProfileUpdate(BaseModel):
    firebase_token: str
    parent: Optional[ParentProfile] = None
    child: Optional[ChildProfile] = None
    system_prompt: Optional[str] = None