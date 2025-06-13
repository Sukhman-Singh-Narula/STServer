# ===== app/services/storage_service.py - UPDATED FOR DIRECT IMAGE DATA =====
import tempfile
import io
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
import httpx
from firebase_admin import firestore
from app.utils.firebase_init import get_storage_bucket, get_firestore_client
from app.config import settings

class StorageService:
    def __init__(self):
        self.bucket = None
        self.db = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize Firebase clients with error handling"""
        try:
            self.bucket = get_storage_bucket()
            self.db = get_firestore_client()
            
            if self.bucket:
                print(f"✅ Storage Service initialized with bucket: {self.bucket.name}")
            else:
                print("⚠️ Storage Service: No bucket available")
                
        except Exception as e:
            print(f"⚠️ Storage Service initialization error: {str(e)}")
    
    async def upload_audio(self, audio_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload audio to Firebase Storage with improved error handling"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            filename = f"stories/{story_id}/audio/scene_{scene_number}.{settings.audio_format}"
            blob = self.bucket.blob(filename)
            
            print(f"📤 Uploading audio: {filename} ({len(audio_data)} bytes)")
            
            # Upload with proper content type
            blob.upload_from_string(
                audio_data, 
                content_type=f"audio/{settings.audio_format}"
            )
            
            # Make publicly accessible
            blob.make_public()
            
            # Verify upload
            if blob.exists():
                print(f"✅ Audio uploaded successfully: {blob.public_url}")
                return blob.public_url
            else:
                raise Exception("Upload completed but file verification failed")
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Audio upload failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def upload_image_data(self, image_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload image data directly to Firebase Storage (no URL download needed)"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Uploading image data: {len(image_data)} bytes")
            
            # Validate image data
            if len(image_data) < 1000:  # Less than 1KB is probably an error
                raise Exception(f"Image data too small: {len(image_data)} bytes")
            
            # Detect image format and set filename accordingly
            content_type = "image/jpeg"
            file_extension = "jpg"
            
            if image_data.startswith(b'\x89PNG'):
                content_type = "image/png"
                file_extension = "png"
                print(f"🖼️ Detected PNG format")
            elif image_data.startswith(b'\xff\xd8'):
                content_type = "image/jpeg"
                file_extension = "jpg"
                print(f"🖼️ Detected JPEG format")
            else:
                print(f"⚠️ Unknown image format, assuming JPEG")
            
            filename = f"stories/{story_id}/images/scene_{scene_number}.{file_extension}"
            blob = self.bucket.blob(filename)
            
            # Upload image data
            blob.upload_from_string(image_data, content_type=content_type)
            blob.make_public()
            
            # Verify upload
            if blob.exists():
                print(f"✅ Image uploaded successfully: {blob.public_url}")
                return blob.public_url
            else:
                raise Exception("Upload completed but file verification failed")
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Image upload failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def upload_image_from_url(self, image_url: str, story_id: str, scene_number: int) -> str:
        """Download image from URL and upload to Firebase Storage - LEGACY METHOD"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📥 Downloading image from URL...")
            print(f"🔗 URL: {image_url[:100]}...")
            
            # Download image with proper headers and timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0), 
                follow_redirects=True,
                headers=headers
            ) as client:
                
                print(f"🌐 Making request...")
                response = await client.get(image_url)
                
                print(f"📊 Response status: {response.status_code}")
                print(f"📊 Content type: {response.headers.get('content-type', 'unknown')}")
                print(f"📊 Content length: {len(response.content)} bytes")
                
                response.raise_for_status()
                image_data = response.content
                
                # Now use the direct upload method
                return await self.upload_image_data(image_data, story_id, scene_number)
            
        except HTTPException:
            raise
        except httpx.TimeoutException:
            error_msg = f"Image download timeout for scene {scene_number}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=408, detail=error_msg)
        except httpx.HTTPStatusError as e:
            error_msg = f"Image download failed for scene {scene_number}: HTTP {e.response.status_code}"
            print(f"❌ {error_msg}")
            
            if e.response.status_code == 403:
                print(f"🔑 403 Error: OpenAI image URL has expired")
                print(f"💡 Consider using base64 response format instead of URLs")
            
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"Image processing failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def save_story_metadata(self, story_id: str, user_id: str, title: str, prompt: str, manifest: Dict):
        """Save comprehensive story metadata to Firestore"""
        try:
            if not self.db:
                print("⚠️ Firestore not available - skipping metadata save")
                return
            
            current_time = datetime.utcnow()
            
            # Enhanced story document with all scene details
            story_doc = {
                'story_id': story_id,
                'user_id': user_id,
                'title': title,
                'user_prompt': prompt,
                'manifest': manifest,
                'created_at': current_time,
                'updated_at': current_time,
                'status': 'completed',
                'total_scenes': manifest.get('total_scenes', 0),
                'total_duration': manifest.get('total_duration', 0),
                'generation_method': 'elevenlabs_openai_base64',  # Updated method
                'scenes_data': manifest.get('scenes', [])
            }
            
            # Save to Firestore
            doc_ref = self.db.collection('stories').document(story_id)
            doc_ref.set(story_doc)
            
            # Update user's story count and last activity
            user_ref = self.db.collection('users').document(user_id)
            user_ref.update({
                'story_count': firestore.Increment(1),
                'last_active': current_time,
                'last_story_created': current_time,
                'last_story_id': story_id
            })
            
            print(f"✅ Story metadata saved to Firestore: {story_id}")
            
        except Exception as e:
            print(f"⚠️ Failed to save story metadata (non-critical): {str(e)}")
    
    async def get_user_stories(self, user_id: str) -> list:
        """Get all stories for a user with enhanced data"""
        try:
            if not self.db:
                print("⚠️ Firestore not available")
                return []
            
            stories_ref = self.db.collection('stories')
            query = stories_ref.where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING)
            stories = query.stream()
            
            story_list = []
            for story in stories:
                story_data = story.to_dict()
                
                story_summary = {
                    'story_id': story.id,
                    'title': story_data.get('title'),
                    'user_prompt': story_data.get('user_prompt'),
                    'created_at': story_data.get('created_at'),
                    'total_scenes': story_data.get('total_scenes', 0),
                    'total_duration': story_data.get('total_duration', 0),
                    'status': story_data.get('status', 'unknown'),
                    'thumbnail_url': None
                }
                
                # Get first scene image as thumbnail
                scenes_data = story_data.get('scenes_data', [])
                if scenes_data and len(scenes_data) > 0:
                    story_summary['thumbnail_url'] = scenes_data[0].get('image_url')
                
                story_list.append(story_summary)
            
            return story_list
            
        except Exception as e:
            print(f"❌ Error fetching user stories: {str(e)}")
            return []
    
    def test_storage_access(self):
        """Test Firebase Storage access"""
        try:
            if not self.bucket:
                return False, "No storage bucket available"
            
            test_blob = self.bucket.blob("test/connection_test.txt")
            test_blob.upload_from_string("test", content_type="text/plain")
            
            if test_blob.exists():
                test_blob.delete()
                return True, f"Storage access successful: {self.bucket.name}"
            else:
                return False, "Upload test failed"
                
        except Exception as e:
            return False, f"Storage test failed: {str(e)}"