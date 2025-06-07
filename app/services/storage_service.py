# ===== app/services/storage_service.py =====
import tempfile
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
import httpx
from firebase_admin import firestore
from app.utils.firebase_init import get_storage_bucket, get_firestore_client
from app.config import settings

class StorageService:
    def __init__(self):
        self.bucket = get_storage_bucket()
        self.db = get_firestore_client()
    
    async def upload_audio(self, audio_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload audio to Firebase Storage"""
        try:
            filename = f"stories/{story_id}/scene{scene_number}.{settings.audio_format}"
            blob = self.bucket.blob(filename)
            
            # Upload audio data
            with tempfile.NamedTemporaryFile() as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                blob.upload_from_filename(temp_file.name, content_type=f"audio/{settings.audio_format}")
            
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
            
            # Update user's story count
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'story_count': firestore.Increment(1),
                'last_active': datetime.utcnow()
            })
            
        except Exception as e:
            print(f"Failed to save story metadata: {str(e)}")
    
    async def get_user_stories(self, user_id: str) -> list:
        """Get all stories for a user"""
        stories_ref = self.db.collection('stories')
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
        
        return story_list
    
    async def update_story_status(self, story_id: str, status: str):
        """Update story playback status"""
        try:
            doc_ref = self.db.collection('stories').document(story_id)
            doc_ref.update({
                'last_played': datetime.utcnow(),
                'playback_status': status
            })
        except Exception as e:
            print(f"Failed to update story status: {str(e)}")