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
    replicate_api_token: str = ""
    deepimage_api_key: str = ""  # DeepImage API key for face swapping
    deepai_api_key: str = ""  # DeepAI API key for image generation
    
    
    # Story settings
    max_scenes: int = 5
    audio_format: str = "wav"  # Changed from mp3 to wav
    image_size: str = "1200x2600"  # Portrait format for optimized mobile story visualization
    replicate_generation_size: str = "768x768"  # Generate at optimal SDXL size
    
    # Performance optimization settings
    max_concurrent_scenes: int = 2  # Process 2 scenes in parallel for SDXL
    enable_batch_audio: bool = True  # Enable batch OpenAI TTS generation
    enable_batch_images: bool = True  # Enable batch Replicate SDXL image generation
    enable_parallel_uploads: bool = True  # Enable parallel Firebase uploads
    
    # Audio optimization settings
    audio_generation_timeout: int = 30  # Seconds per audio file
    batch_audio_timeout: int = 120  # Seconds for entire batch (OpenAI TTS only)
    firebase_web_api_key: str = ""  # NEW: Required for authentication
    # Image optimization settings
    image_generation_timeout: int = 60  # Seconds per image (SDXL takes longer than DALL-E)
    batch_image_timeout: int = 300  # Seconds for entire image batch (Replicate SDXL)
    
    # Upload optimization settings
    upload_timeout: int = 30  # Seconds per upload
    parallel_upload_timeout: int = 60  # Seconds for parallel uploads
    
    # CORS settings - Fixed to include React Native port 8081
    cors_origins: str = "*"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # System prompt for story generation
    default_system_prompt: str = """You are a creative children's storyteller specializing in creating completely safe, educational, and fun stories for children aged 4-10. 

    CRITICAL SAFETY REQUIREMENTS:
    - Create only wholesome, positive, and age-appropriate content
    - NO violence, scary themes, dangerous activities, or inappropriate content
    - Focus on friendship, kindness, learning, family, nature, and positive adventures
    - Use simple, clear language that children can understand
    - Promote positive values like sharing, helping others, and being kind

    STORY STRUCTURE:
    - Structure your story into clear scenes (2-5 scenes total)
    - Each scene should be 2-3 sentences long and paint a vivid, safe picture
    - End with a positive message or lesson

    VISUAL PROMPT GUIDELINES (VERY IMPORTANT):
    - Create visual descriptions that are completely child-safe and innocent
    - Use bright, colorful, cartoon-like imagery suitable for children's books
    - Focus on cute animals, friendly characters, beautiful landscapes, toys, or magical but safe scenarios
    - Avoid any content that could be interpreted as scary, violent, or inappropriate
    - Use descriptive words like: cheerful, bright, colorful, friendly, cute, magical, happy, peaceful
    - Examples: "A happy bunny playing in a sunny meadow with colorful flowers"
    - Ensure all characters and scenes are clearly child-appropriate and wholesome

    Remember: Every word and image description must pass the highest child safety standards."""
    
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
    
    @property
    def effective_image_size(self) -> str:
        """Get effective image size - use 1200x2600 for optimized portrait format"""
        return "1200x2600"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()