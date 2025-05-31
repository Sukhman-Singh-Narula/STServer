import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import tempfile
import base64

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, auth, storage, firestore
import httpx
from openai import OpenAI
import groq
from elevenlabs import generate, set_api_key, Voice
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="ESP32 Storytelling Server", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    # Firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "gs://storyteller-7ece7.firebasestorage.app")
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ", "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")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    
    # Story settings
    MAX_SCENES = 6
    AUDIO_FORMAT = "mp3"
    IMAGE_SIZE = "1024x1024"
    
    # System prompt for story generation
    DEFAULT_SYSTEM_PROMPT = """You are a creative children's storyteller. Create engaging, age-appropriate stories that are educational and fun. 
    Structure your story into clear scenes that can be visualized. Each scene should be 2-3 sentences long and paint a vivid picture.
    Keep the language simple and appropriate for children aged 4-10."""

config = Config()

# Initialize services
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'storageBucket': config.FIREBASE_STORAGE_BUCKET
        })

def initialize_apis():
    """Initialize external API clients"""
    # OpenAI
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Groq
    groq_client = groq.Groq(api_key=config.GROQ_API_KEY)
    
    # ElevenLabs
    set_api_key(config.ELEVENLABS_API_KEY)
    
    return openai_client, groq_client

# Initialize services
initialize_firebase()
openai_client, groq_client = initialize_apis()

# Data models
class StoryPromptRequest(BaseModel):
    firebase_token: str
    prompt: str

class SystemPromptUpdate(BaseModel):
    firebase_token: str
    system_prompt: str

@dataclass
class StoryScene:
    scene_number: int
    text: str
    visual_prompt: str
    audio_url: str = ""
    image_url: str = ""
    start_time: int = 0

@dataclass
class StoryManifest:
    story_id: str
    title: str
    total_duration: int
    segments: List[Dict[str, Any]]

# Global system prompt storage (in production, use a database)
system_prompts = {}

# Authentication dependency
async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """Verify Firebase ID token and return user info"""
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {str(e)}")

# Story generation utilities
class StoryGenerator:
    def __init__(self, groq_client, system_prompt: str):
        self.groq_client = groq_client
        self.system_prompt = system_prompt
    
    async def generate_story_scenes(self, prompt: str, user_id: str) -> List[StoryScene]:
        """Generate story scenes using Groq Llama"""
        try:
            # Get user-specific system prompt or use default
            user_system_prompt = system_prompts.get(user_id, config.DEFAULT_SYSTEM_PROMPT)
            
            full_prompt = f"""
            {user_system_prompt}
            
            Create a story based on this prompt: "{prompt}"
            
            Structure your response as exactly {config.MAX_SCENES} scenes. For each scene, provide:
            1. The scene text (2-3 sentences)
            2. A detailed visual description for image generation
            
            Format your response as JSON:
            {{
                "title": "Story Title",
                "scenes": [
                    {{
                        "scene_number": 1,
                        "text": "Scene text here...",
                        "visual_prompt": "Detailed visual description for image generation..."
                    }}
                ]
            }}
            """
            
            response = self.groq_client.chat.completions.create(
                model="llama3-8b-8192",  # or llama3-70b-8192 for better quality
                messages=[
                    {"role": "system", "content": user_system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            story_data = json.loads(response.choices[0].message.content)
            
            scenes = []
            for scene_data in story_data["scenes"]:
                scene = StoryScene(
                    scene_number=scene_data["scene_number"],
                    text=scene_data["text"],
                    visual_prompt=scene_data["visual_prompt"]
                )
                scenes.append(scene)
            
            return scenes, story_data.get("title", "Generated Story")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

class MediaGenerator:
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    async def generate_audio(self, text: str, scene_number: int) -> bytes:
        """Generate audio using ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice=Voice(voice_id="21m00Tcm4TlvDq8ikWAM"),  # Rachel voice
                model="eleven_monolingual_v1"
            )
            return audio
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio generation failed for scene {scene_number}: {str(e)}")
    
    async def generate_image(self, visual_prompt: str, scene_number: int) -> str:
        """Generate image using OpenAI DALL-E"""
        try:
            # Enhance the prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly: {visual_prompt}"
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=config.IMAGE_SIZE,
                quality="standard",
                n=1
            )
            
            return response.data[0].url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image generation failed for scene {scene_number}: {str(e)}")

class FirebaseStorage:
    def __init__(self):
        self.bucket = storage.bucket()
        self.db = firestore.client()
    
    async def upload_audio(self, audio_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload audio to Firebase Storage"""
        try:
            filename = f"stories/{story_id}/scene{scene_number}.{config.AUDIO_FORMAT}"
            blob = self.bucket.blob(filename)
            
            # Upload audio data
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                blob.upload_from_filename(temp_file.name, content_type=f"audio/{config.AUDIO_FORMAT}")
            
            # Make publicly accessible
            blob.make_public()
            return blob.public_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")
    
    async def upload_image_from_url(self, image_url: str, story_id: str, scene_number: int) -> str:
        """Download image from URL and upload to Firebase Storage"""
        try:
            # Download image
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content
            
            filename = f"stories/{story_id}/scene{scene_number}.jpg"
            blob = self.bucket.blob(filename)
            
            # Upload image
            blob.upload_from_string(image_data, content_type="image/jpeg")
            blob.make_public()
            
            return blob.public_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")
    
    async def save_story_metadata(self, story_id: str, user_id: str, title: str, prompt: str, manifest: Dict):
        """Save story metadata to Firestore"""
        try:
            doc_ref = self.db.collection('stories').document(story_id)
            doc_ref.set({
                'user_id': user_id,
                'title': title,
                'prompt': prompt,
                'manifest': manifest,
                'created_at': datetime.utcnow(),
                'status': 'completed'
            })
        except Exception as e:
            print(f"Failed to save story metadata: {str(e)}")

# Initialize services
firebase_storage = FirebaseStorage()
media_generator = MediaGenerator(openai_client)

# Calculate audio duration (approximate)
def calculate_audio_duration(text: str) -> int:
    """Estimate audio duration in milliseconds based on text length"""
    # Approximate: 150 words per minute, average 5 characters per word
    words = len(text) / 5
    duration_minutes = words / 150
    return int(duration_minutes * 60 * 1000)

# API Endpoints
@app.post("/system-prompt")
async def update_system_prompt(request: SystemPromptUpdate):
    """Update system prompt for a user"""
    try:
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        
        # Store system prompt for user
        system_prompts[user_id] = request.system_prompt
        
        return {
            "success": True,
            "message": "System prompt updated successfully",
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/generate-story")
async def generate_story(request: StoryPromptRequest):
    """Main endpoint to generate a complete story with media"""
    try:
        # Verify Firebase token
        user_info = await verify_firebase_token(request.firebase_token)
        user_id = user_info['uid']
        
        # Generate unique story ID
        story_id = f"story_{uuid.uuid4().hex[:8]}"
        
        # Initialize story generator
        story_generator = StoryGenerator(groq_client, config.DEFAULT_SYSTEM_PROMPT)
        
        # Generate story scenes
        scenes, title = await story_generator.generate_story_scenes(request.prompt, user_id)
        
        # Process each scene
        processed_scenes = []
        current_time = 0
        
        for scene in scenes:
            # Generate audio
            audio_data = await media_generator.generate_audio(scene.text, scene.scene_number)
            audio_url = await firebase_storage.upload_audio(audio_data, story_id, scene.scene_number)
            
            # Generate image
            temp_image_url = await media_generator.generate_image(scene.visual_prompt, scene.scene_number)
            image_url = await firebase_storage.upload_image_from_url(temp_image_url, story_id, scene.scene_number)
            
            # Calculate timing
            audio_duration = calculate_audio_duration(scene.text)
            
            scene.audio_url = audio_url
            scene.image_url = image_url
            scene.start_time = current_time
            
            processed_scenes.append(scene)
            current_time += audio_duration
        
        # Build manifest
        segments = []
        for scene in processed_scenes:
            # Add image segment
            segments.append({
                "type": "image",
                "url": scene.image_url,
                "start": scene.start_time
            })
            # Add audio segment
            segments.append({
                "type": "audio",
                "url": scene.audio_url,
                "start": scene.start_time
            })
        
        manifest = {
            "story_id": story_id,
            "title": title,
            "total_duration": current_time,
            "segments": segments
        }
        
        # Save to Firestore
        await firebase_storage.save_story_metadata(
            story_id, user_id, title, request.prompt, manifest
        )
        
        return manifest
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Story generation failed: {str(e)}")

@app.websocket("/ws/{user_token}")
async def websocket_endpoint(websocket: WebSocket, user_token: str):
    """WebSocket endpoint for real-time communication with ESP32"""
    await websocket.accept()
    
    try:
        # Verify token
        user_info = await verify_firebase_token(user_token)
        user_id = user_info['uid']
        
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "user_id": user_id,
            "message": "Connected successfully"
        }))
        
        while True:
            # Wait for messages from ESP32
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "story_status":
                # Handle story playback status from ESP32
                story_id = message.get("story_id")
                status = message.get("status")
                
                # Log status to Firestore
                try:
                    doc_ref = firebase_storage.db.collection('stories').document(story_id)
                    doc_ref.update({
                        'last_played': datetime.utcnow(),
                        'playback_status': status
                    })
                except Exception as e:
                    print(f"Failed to update story status: {str(e)}")
                
                # Send acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "status_received",
                    "story_id": story_id,
                    "status": status
                }))
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "firebase": "connected",
            "groq": "configured" if config.GROQ_API_KEY else "not_configured",
            "openai": "configured" if config.OPENAI_API_KEY else "not_configured",
            "elevenlabs": "configured" if config.ELEVENLABS_API_KEY else "not_configured"
        }
    }

@app.get("/stories/{user_token}")
async def get_user_stories(user_token: str):
    """Get all stories for a user"""
    try:
        user_info = await verify_firebase_token(user_token)
        user_id = user_info['uid']
        
        # Query Firestore for user's stories
        stories_ref = firebase_storage.db.collection('stories')
        query = stories_ref.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING)
        stories = query.stream()
        
        story_list = []
        for story in stories:
            story_data = story.to_dict()
            story_list.append({
                'story_id': story.id,
                'title': story_data.get('title'),
                'created_at': story_data.get('created_at'),
                'manifest': story_data.get('manifest')
            })
        
        return {"stories": story_list}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    # Make sure to set environment variables before running
    required_vars = ["GROQ_API_KEY", "OPENAI_API_KEY", "ELEVENLABS_API_KEY", "FIREBASE_CREDENTIALS_PATH", "FIREBASE_STORAGE_BUCKET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these environment variables before running the server.")
        exit(1)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)