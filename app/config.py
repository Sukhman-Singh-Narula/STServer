import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Firebase
    firebase_credentials_path: str = "./firebase-credentials.json"
    firebase_storage_bucket: str = ""
    
    # API Keys
    groq_api_key: str = ""
    openai_api_key: str = ""
    elevenlabs_api_key: str = ""
    
    # Story settings
    max_scenes: int = 6
    audio_format: str = "mp3"
    image_size: str = "1024x1024"
    
    # CORS settings
    cors_origins: str = "http://localhost:8081,http://localhost:3000,http://localhost:19006,*"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # System prompt for story generation
    default_system_prompt: str = """You are a creative children's storyteller. Create engaging, age-appropriate stories that are educational and fun. 
    Structure your story into clear scenes that can be visualized. Each scene should be 2-3 sentences long and paint a vivid picture.
    Keep the language simple and appropriate for children aged 4-10."""
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert cors_origins string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()