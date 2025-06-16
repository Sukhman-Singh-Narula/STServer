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
    image_size: str = "960x540"  # Changed from 1024x1024 to 960x540
    
    # CORS settings - Fixed to include React Native port 8081
    cors_origins: str = "*"
    
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
        """Convert cors_origins string to list with React Native defaults"""
        # Always include React Native development origins
        react_native_origins = [
            "http://localhost:8081",    # Expo web default
            "http://127.0.0.1:8081",    # Alternative localhost
            "http://localhost:19006",   # Expo web alternative
            "http://127.0.0.1:19006",   # Alternative localhost
            "http://localhost:3000",    # Common React dev server
            "http://127.0.0.1:3000",    # Alternative localhost
            "http://localhost:8080",    # Common dev port
            "http://127.0.0.1:8080",    # Alternative localhost
        ]
        
        if self.cors_origins == "*":
            return ["*"]
        
        # Parse custom origins
        custom_origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        
        # Combine custom and default origins, remove duplicates
        all_origins = list(set(react_native_origins + custom_origins))
        
        # If "*" is in the list, just return ["*"]
        if "*" in all_origins:
            return ["*"]
            
        return all_origins
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()