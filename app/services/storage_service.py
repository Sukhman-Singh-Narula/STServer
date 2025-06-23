# ===== app/services/storage_service.py - OPTIMIZED WITH PARALLEL UPLOADS =====
import tempfile
import io
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Tuple
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
    
    async def upload_media_parallel(self, audio_data: bytes, image_data: bytes, story_id: str, scene_number: int) -> Tuple[str, str]:
        """Upload audio and image files in parallel to Firebase Storage"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Starting parallel upload for scene {scene_number}...")
            print(f"  Audio size: {len(audio_data)} bytes")
            print(f"  Image size: {len(image_data)} bytes")
            
            # Create upload tasks for parallel execution
            upload_tasks = [
                self.upload_audio(audio_data, story_id, scene_number),
                self.upload_image_data(image_data, story_id, scene_number)
            ]
            
            # Execute uploads in parallel
            print(f"🚀 Executing parallel uploads for scene {scene_number}...")
            results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Check for any upload failures
            audio_url = results[0]
            image_url = results[1]
            
            if isinstance(audio_url, Exception):
                raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(audio_url)}")
            
            if isinstance(image_url, Exception):
                raise HTTPException(status_code=500, detail=f"Image upload failed: {str(image_url)}")
            
            print(f"✅ Parallel upload completed for scene {scene_number}:")
            print(f"  Audio URL: {audio_url}")
            print(f"  Image URL: {image_url}")
            
            return audio_url, image_url
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Parallel upload failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def upload_audio(self, audio_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload audio to Firebase Storage with improved error handling"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            filename = f"stories/{story_id}/audio/scene_{scene_number}.{settings.audio_format}"
            
            print(f"📤 Uploading audio: {filename} ({len(audio_data)} bytes)")
            
            # Create blob and upload in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def upload_audio_sync():
                blob = self.bucket.blob(filename)
                
                # Upload with proper content type
                blob.upload_from_string(
                    audio_data, 
                    content_type=f"audio/{settings.audio_format}"
                )
                
                # Make publicly accessible
                blob.make_public()
                
                # Verify upload
                if blob.exists():
                    return blob.public_url
                else:
                    raise Exception("Upload completed but file verification failed")
            
            # Run upload in thread pool
            public_url = await loop.run_in_executor(None, upload_audio_sync)
            
            print(f"✅ Audio uploaded successfully: {public_url}")
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Audio upload failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def upload_image_data(self, image_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload grayscale image data directly to Firebase Storage"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Uploading grayscale image data: {len(image_data)} bytes")
            
            # Validate image data
            if len(image_data) < 1000:  # Less than 1KB is probably an error
                raise Exception(f"Image data too small: {len(image_data)} bytes")
            
            # Detect image format and set filename accordingly
            content_type = "image/jpeg"
            file_extension = "jpg"
            
            if image_data.startswith(b'\x89PNG'):
                content_type = "image/png"
                file_extension = "png"
                print(f"🖼️ Detected PNG format (grayscale)")
            elif image_data.startswith(b'\xff\xd8'):
                content_type = "image/jpeg"
                file_extension = "jpg"
                print(f"🖼️ Detected JPEG format (grayscale)")
            else:
                print(f"⚠️ Unknown image format, assuming JPEG (grayscale)")
            
            # Use _grayscale suffix to indicate the image has been processed
            filename = f"stories/{story_id}/images/scene_{scene_number}_grayscale.{file_extension}"
            
            # Create blob and upload in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def upload_image_sync():
                blob = self.bucket.blob(filename)
                
                # Upload image data
                blob.upload_from_string(image_data, content_type=content_type)
                blob.make_public()
                
                # Verify upload
                if blob.exists():
                    return blob.public_url
                else:
                    raise Exception("Upload completed but file verification failed")
            
            # Run upload in thread pool
            public_url = await loop.run_in_executor(None, upload_image_sync)
            
            print(f"✅ Grayscale image uploaded successfully: {public_url}")
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Grayscale image upload failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    
    async def upload_batch_media(self, media_list: List[Dict]) -> List[Dict]:
        """Upload multiple media files in parallel (batch upload optimization)"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Starting batch upload for {len(media_list)} media files...")
            
            # Create upload tasks for all media files
            upload_tasks = []
            for media in media_list:
                if media['type'] == 'audio':
                    task = self.upload_audio(
                        media['data'], 
                        media['story_id'], 
                        media['scene_number']
                    )
                elif media['type'] == 'image':
                    task = self.upload_image_data(
                        media['data'], 
                        media['story_id'], 
                        media['scene_number']
                    )
                else:
                    continue
                
                upload_tasks.append({
                    'task': task,
                    'type': media['type'],
                    'scene_number': media['scene_number']
                })
            
            # Execute all uploads in parallel
            print(f"🚀 Executing {len(upload_tasks)} parallel uploads...")
            results = await asyncio.gather(
                *[task_info['task'] for task_info in upload_tasks], 
                return_exceptions=True
            )
            
            # Process results
            upload_results = []
            for i, result in enumerate(results):
                task_info = upload_tasks[i]
                
                if isinstance(result, Exception):
                    print(f"❌ Upload failed for {task_info['type']} scene {task_info['scene_number']}: {result}")
                    upload_results.append({
                        'type': task_info['type'],
                        'scene_number': task_info['scene_number'],
                        'success': False,
                        'error': str(result)
                    })
                else:
                    upload_results.append({
                        'type': task_info['type'],
                        'scene_number': task_info['scene_number'],
                        'success': True,
                        'url': result
                    })
            
            successful_uploads = len([r for r in upload_results if r['success']])
            print(f"✅ Batch upload completed: {successful_uploads}/{len(upload_results)} successful")
            
            return upload_results
            
        except Exception as e:
            error_msg = f"Batch upload failed: {str(e)}"
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
                
                # Now use the direct upload method (which will handle grayscale)
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
        """Save comprehensive story metadata to Firestore (optimized for parallel execution)"""
        try:
            if not self.db:
                print("⚠️ Firestore not available - skipping metadata save")
                return
            
            # Run Firestore operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def save_metadata_sync():
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
                    'generation_method': 'fully_optimized_parallel_dalle2_openai_tts',
                    'image_format': 'grayscale_960x540_from_dalle2',
                    'scenes_data': manifest.get('scenes', []),
                    'optimizations': manifest.get('optimizations', [])
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
                
                return True
            
            # Execute in thread pool
            await loop.run_in_executor(None, save_metadata_sync)
            
            print(f"✅ Story metadata saved to Firestore: {story_id}")
            
        except Exception as e:
            print(f"⚠️ Failed to save story metadata (non-critical): {str(e)}")
    
    async def get_user_stories(self, user_id: str) -> list:
        """Get all stories for a user with enhanced data"""
        try:
            if not self.db:
                print("⚠️ Firestore not available")
                return []
            
            # Run Firestore query in thread pool
            loop = asyncio.get_event_loop()
            
            def get_stories_sync():
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
                        'image_format': story_data.get('image_format', 'unknown'),
                        'generation_method': story_data.get('generation_method', 'unknown'),
                        'optimizations': story_data.get('optimizations', []),
                        'thumbnail_url': None
                    }
                    
                    # Get first scene image as thumbnail
                    scenes_data = story_data.get('scenes_data', [])
                    if scenes_data and len(scenes_data) > 0:
                        story_summary['thumbnail_url'] = scenes_data[0].get('image_url')
                    
                    story_list.append(story_summary)
                
                return story_list
            
            # Execute in thread pool
            story_list = await loop.run_in_executor(None, get_stories_sync)
            return story_list
            
        except Exception as e:
            print(f"❌ Error fetching user stories: {str(e)}")
            return []
    
    async def get_story_details(self, story_id: str) -> Dict[str, Any]:
        """Get complete story details including all scenes data"""
        try:
            if not self.db:
                raise HTTPException(status_code=503, detail="Firestore not available")
            
            # Run Firestore query in thread pool
            loop = asyncio.get_event_loop()
            
            def get_story_sync():
                doc_ref = self.db.collection('stories').document(story_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    return doc.to_dict()
                else:
                    return None
            
            # Execute in thread pool
            story_data = await loop.run_in_executor(None, get_story_sync)
            
            if story_data:
                return story_data
            else:
                raise HTTPException(status_code=404, detail="Story not found")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching story details: {str(e)}")
    
    async def update_story_status_and_title(self, story_id: str, status: str, title: str = None):
        """Update story status and optionally title"""
        try:
            if not self.db:
                print("⚠️ Firestore not available - skipping status update")
                return
            
            # Run update in thread pool
            loop = asyncio.get_event_loop()
            
            def update_status_sync():
                doc_ref = self.db.collection('stories').document(story_id)
                update_data = {
                    'status': status,
                    'updated_at': datetime.utcnow()
                }
                
                if title:
                    update_data['title'] = title
                    
                doc_ref.update(update_data)
            
            await loop.run_in_executor(None, update_status_sync)
            print(f"✅ Story {story_id} status updated to: {status}")
            
        except Exception as e:
            print(f"⚠️ Failed to update story status: {str(e)}")
    
    async def update_story_status(self, story_id: str, status: str):
        """Update story playback status"""
        try:
            if not self.db:
                print("⚠️ Firestore not available - skipping status update")
                return
            
            # Run update in thread pool
            loop = asyncio.get_event_loop()
            
            def update_status_sync():
                doc_ref = self.db.collection('stories').document(story_id)
                doc_ref.update({
                    'playback_status': status,
                    'last_played': datetime.utcnow()
                })
            
            await loop.run_in_executor(None, update_status_sync)
            
        except Exception as e:
            print(f"⚠️ Failed to update story status: {str(e)}")
    
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