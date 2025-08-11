# ===== COMPLETE STORY ID ARRAY IMPLEMENTATION - STORAGE SERVICE =====
# Replace your entire storage_service.py with this enhanced version

import tempfile
import io
import asyncio
from datetime import datetime, timezone
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

    # ===== MEDIA UPLOAD METHODS (Keep existing) =====
    
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
        """Upload grayscale image data directly to Firebase Storage (legacy method)"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Uploading grayscale image data: {len(image_data)} bytes")
            
            # Validate image data
            if len(image_data) < 1000:  # Less than 1KB is probably an error
                raise Exception(f"Image data too small: {len(image_data)} bytes")
            
            # Always use JPEG format for all images
            content_type = "image/jpeg"
            file_extension = "jpg"
            print(f"🖼️ Storing as JPEG format (grayscale)")
            
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

    async def upload_colored_image(self, image_data: bytes, story_id: str, scene_number: int) -> str:
        """Upload colored image data directly to Firebase Storage"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Uploading colored image data: {len(image_data)} bytes")
            
            # Validate image data
            if len(image_data) < 1000:  # Less than 1KB is probably an error
                raise Exception(f"Image data too small: {len(image_data)} bytes")
            
            # Always use JPEG format for all images
            content_type = "image/jpeg"
            file_extension = "jpg"
            print(f"🖼️ Storing as JPEG format (colored)")
            
            # Use _colored suffix to indicate the original colored image
            filename = f"stories/{story_id}/images/scene_{scene_number}_colored.{file_extension}"
            
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
            
            print(f"✅ Colored image uploaded successfully: {public_url}")
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Colored image upload failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    async def upload_both_images(self, image_data: bytes, story_id: str, scene_number: int) -> Dict[str, str]:
        """Upload both colored and grayscale versions of the same image"""
        try:
            from PIL import Image
            import io
            
            # Convert image to grayscale using PIL
            image = Image.open(io.BytesIO(image_data))
            
            # Image should already be 2600x1200 from media service, but verify
            if image.size != (2600, 1200):
                print(f"⚠️ Unexpected image size {image.size}, resizing to 2600x1200")
                image = image.resize((2600, 1200), Image.LANCZOS)
            else:
                print(f"✅ Image already at correct size: {image.size}")
            
            # Create grayscale version
            grayscale_image = image.convert('L')
            
            # Save grayscale image to bytes
            grayscale_buffer = io.BytesIO()
            
            # Determine format from original image
            format = image.format if image.format else 'JPEG'
            if format not in ['JPEG', 'PNG']:
                format = 'JPEG'  # Default to JPEG for unsupported formats
            
            # Save grayscale image with optimized compression for 2600x1200 images
            if format == 'JPEG':
                grayscale_image.save(grayscale_buffer, format='JPEG', quality=85, optimize=True)
            else:
                grayscale_image.save(grayscale_buffer, format=format, optimize=True)
            
            grayscale_data = grayscale_buffer.getvalue()
            
            # Upload both versions in parallel
            colored_task = self.upload_colored_image(image_data, story_id, scene_number)
            grayscale_task = self.upload_image_data(grayscale_data, story_id, scene_number)
            
            colored_url, grayscale_url = await asyncio.gather(colored_task, grayscale_task)
            
            return {
                "colored_url": colored_url,
                "grayscale_url": grayscale_url
            }
            
        except Exception as e:
            error_msg = f"Both image uploads failed for scene {scene_number}: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    async def upload_user_image(self, image_data: bytes, user_id: str) -> str:
        """Upload user profile image to Firebase Storage"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Uploading user profile image: {len(image_data)} bytes")
            
            # Validate image data
            if len(image_data) < 1000:  # Less than 1KB is probably an error
                raise Exception(f"Image data too small: {len(image_data)} bytes")
            
            # Always use JPEG format for all images
            content_type = "image/jpeg"
            file_extension = "jpg"
            print(f"🖼️ Storing as JPEG format (user profile)")
            
            # Use timestamp to avoid conflicts
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"users/{user_id}/profile_image_{timestamp}.{file_extension}"
            
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
            
            print(f"✅ User profile image uploaded successfully: {public_url}")
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"User profile image upload failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    async def upload_image(self, image_data: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """Generic image upload method for temporary files"""
        try:
            if not self.bucket:
                raise HTTPException(status_code=503, detail="Firebase Storage not available")
            
            print(f"📤 Uploading image: {filename} ({len(image_data)} bytes)")
            
            # Validate image data
            if len(image_data) < 1000:  # Less than 1KB is probably an error
                raise Exception(f"Image data too small: {len(image_data)} bytes")
            
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
            
            print(f"✅ Image uploaded successfully: {public_url}")
            return public_url
            
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Image upload failed: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

    async def delete_file(self, filename: str) -> bool:
        """Delete a file from Firebase Storage"""
        try:
            if not self.bucket:
                print("⚠️ Firebase Storage not available - cannot delete file")
                return False
            
            print(f"🗑️ Deleting file: {filename}")
            
            # Run deletion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def delete_file_sync():
                blob = self.bucket.blob(filename)
                if blob.exists():
                    blob.delete()
                    return True
                else:
                    print(f"⚠️ File {filename} does not exist")
                    return False
            
            # Run deletion in thread pool
            result = await loop.run_in_executor(None, delete_file_sync)
            
            if result:
                print(f"✅ File deleted successfully: {filename}")
            
            return result
            
        except Exception as e:
            print(f"❌ File deletion failed for {filename}: {str(e)}")
            return False

    # ===== ENHANCED STORY METADATA MANAGEMENT WITH STORY ID ARRAYS =====
    
    async def save_story_metadata(self, story_id: str, user_id: str, title: str, prompt: str, manifest: Dict):
        """Save story metadata with story ID array tracking for each user"""
        try:
            if not self.db:
                print("⚠️ Firestore not available - skipping metadata save")
                return
            
            # Run Firestore operations in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def save_metadata_with_story_arrays():
                current_time = datetime.utcnow()
                
                # 1. MAIN STORY DOCUMENT
                story_doc = {
                    'story_id': story_id,
                    'user_id': user_id,
                    'title': title,
                    'user_prompt': prompt,
                    'manifest': manifest,
                    'created_at': current_time,
                    'updated_at': current_time,
                    'status': manifest.get('status', 'completed'),
                    'total_scenes': manifest.get('total_scenes', 0),
                    'total_duration': manifest.get('total_duration', 0),
                    'generation_method': manifest.get('generation_method', 'optimized_parallel'),
                    'image_format': 'grayscale_2600x1200_from_deepai',
                    'scenes_data': manifest.get('scenes', []),
                    'optimizations': manifest.get('optimizations', []),
                    'ai_models_used': {
                        'text_generation': 'gpt-4',
                        'image_generation': 'dall-e-2',
                        'audio_generation': 'openai-tts-1'
                    }
                }
                
                # Get thumbnail from first scene
                scenes = manifest.get('scenes', [])
                if scenes and len(scenes) > 0:
                    story_doc['thumbnail_url'] = scenes[0].get('image_url')
                
                # Save to main stories collection
                doc_ref = self.db.collection('stories').document(story_id)
                doc_ref.set(story_doc)
                
                # 2. UPDATE USER DOCUMENT WITH STORY ID ARRAY
                user_ref = self.db.collection('users').document(user_id)
                user_doc = user_ref.get()
                
                current_story_count = 0
                existing_story_ids = []
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    current_story_count = user_data.get('story_count', 0)
                    existing_story_ids = user_data.get('story_ids', [])
                
                # 🚫 FIX: Only add story_id if it's not already in the array
                if story_id not in existing_story_ids:
                    updated_story_ids = existing_story_ids + [story_id]
                    new_story_count = len(updated_story_ids)
                else:
                    updated_story_ids = existing_story_ids
                    new_story_count = len(updated_story_ids)
                    print(f"📝 Story {story_id} already exists in user's story_ids array")
                
                # Update story document with story number
                story_doc['story_number'] = new_story_count
                doc_ref.update({'story_number': new_story_count})
                
                # Enhanced user document update with story ID array
                user_update_data = {
                    'story_count': new_story_count,
                    'story_ids': updated_story_ids,  # CRITICAL: Array of all story IDs
                    'last_active': current_time,
                    'last_story_created': current_time,
                    'last_story_id': story_id,
                    'last_story_title': title,
                    # Enhanced statistics
                    'story_statistics': {
                        'total_stories': new_story_count,
                        'total_scenes_created': sum(story.get('total_scenes', 0) for story in [story_doc]),
                        'total_duration_seconds': sum(story.get('total_duration', 0) for story in [story_doc]) / 1000,
                        'last_generation_method': story_doc['generation_method'],
                        'creation_dates': existing_story_ids + [{'story_id': story_id, 'created_at': current_time}]
                    }
                }
                
                # Update main user document
                if user_doc.exists:
                    user_ref.update(user_update_data)
                else:
                    user_update_data.update({
                        'created_at': current_time,
                        'user_id': user_id
                    })
                    user_ref.set(user_update_data)
                
                print(f"📝 Updated user {user_id} story_ids array: {len(updated_story_ids)} stories")
                print(f"📝 Story IDs: {updated_story_ids}")
                
                return True
            
            # Execute in thread pool
            await loop.run_in_executor(None, save_metadata_with_story_arrays)
            
            print(f"✅ Story metadata saved with ID array tracking: {story_id} for user {user_id}")
            
        except Exception as e:
            print(f"⚠️ Failed to save story metadata with arrays: {str(e)}")

    async def get_user_stories_using_id_array(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get user stories using the story ID array - MAIN METHOD with timezone fix"""
        try:
            if not self.db:
                print("⚠️ Firestore not available")
                return {
                    "stories": [],
                    "total_count": 0,
                    "has_more": False,
                    "user_info": None,
                    "method_used": "firestore_unavailable"
                }
            
            # Run Firestore query in thread pool
            loop = asyncio.get_event_loop()
            
            def get_stories_from_id_array():
                # 1. GET USER DOCUMENT WITH STORY ID ARRAY
                user_ref = self.db.collection('users').document(user_id)
                user_doc = user_ref.get()
                
                if not user_doc.exists:
                    return {
                        "stories": [],
                        "total_count": 0,
                        "has_more": False,
                        "user_info": None,
                        "method_used": "user_not_found"
                    }
                
                user_data = user_doc.to_dict()
                story_ids = user_data.get('story_ids', [])
                
                # Remove duplicates from story_ids
                story_ids = list(dict.fromkeys(story_ids))
                total_count = len(story_ids)
                
                print(f"📋 Found {total_count} unique story IDs for user {user_id}")
                print(f"📋 Story IDs: {story_ids}")
                
                if not story_ids:
                    user_info = self._extract_user_info(user_data)
                    return {
                        "stories": [],
                        "total_count": 0,
                        "has_more": False,
                        "user_info": user_info,
                        "method_used": "story_id_array_empty"
                    }
                
                # 2. APPLY PAGINATION TO STORY IDS (newest first)
                story_ids_reversed = list(reversed(story_ids))
                paginated_story_ids = story_ids_reversed[offset:offset + limit]
                
                print(f"📄 Paginated IDs (offset:{offset}, limit:{limit}): {paginated_story_ids}")
                
                # 3. BATCH FETCH STORY DOCUMENTS USING STORY IDS
                stories_data = []
                
                def safe_datetime_conversion(dt_value):
                    """Safely convert datetime values with timezone handling"""
                    if dt_value is None:
                        return None
                    
                    try:
                        # If it's already a datetime object
                        if isinstance(dt_value, datetime):
                            # If it's naive, make it timezone aware (UTC)
                            if dt_value.tzinfo is None:
                                return dt_value.replace(tzinfo=timezone.utc)
                            return dt_value
                        
                        # If it's a Firestore timestamp
                        if hasattr(dt_value, 'seconds'):
                            return datetime.fromtimestamp(dt_value.seconds, tz=timezone.utc)
                        
                        # If it's a string, try to parse it
                        if isinstance(dt_value, str):
                            try:
                                parsed_dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                                if parsed_dt.tzinfo is None:
                                    return parsed_dt.replace(tzinfo=timezone.utc)
                                return parsed_dt
                            except:
                                return datetime.now(timezone.utc)  # Fallback
                        
                        return datetime.now(timezone.utc)  # Final fallback
                    except Exception as e:
                        print(f"⚠️ Datetime conversion error: {e}")
                        return datetime.now(timezone.utc)
                
                # Fetch each story document
                for story_id in paginated_story_ids:
                    try:
                        print(f"📖 Fetching story document: {story_id}")
                        story_ref = self.db.collection('stories').document(story_id)
                        story_doc = story_ref.get()
                        
                        if story_doc.exists:
                            story_data = story_doc.to_dict()
                            print(f"✅ Found story: {story_data.get('title', 'Unknown')}")
                            
                            # Safe datetime conversion
                            created_at = safe_datetime_conversion(story_data.get('created_at'))
                            updated_at = safe_datetime_conversion(story_data.get('updated_at'))
                            
                            # Calculate days ago safely
                            days_ago = None
                            created_at_formatted = None
                            
                            try:
                                if created_at:
                                    now_utc = datetime.now(timezone.utc)
                                    days_ago = (now_utc - created_at).days
                                    created_at_formatted = created_at.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                print(f"⚠️ Date calculation error: {e}")
                                days_ago = 0
                                created_at_formatted = "Unknown"
                            
                            # Build story summary with safe datetime handling
                            story_summary = {
                                'story_id': story_doc.id,
                                'title': story_data.get('title', 'Untitled Story'),
                                'user_prompt': story_data.get('user_prompt', ''),
                                'created_at': created_at,
                                'updated_at': updated_at,
                                'total_scenes': story_data.get('total_scenes', 0),
                                'total_duration': story_data.get('total_duration', 0),
                                'status': story_data.get('status', 'unknown'),
                                'story_number': story_data.get('story_number', 0),
                                'thumbnail_url': story_data.get('thumbnail_url'),
                                'generation_method': story_data.get('generation_method', 'unknown'),
                                'ai_models_used': story_data.get('ai_models_used', {}),
                                'image_format': story_data.get('image_format', 'unknown'),
                                'optimizations': story_data.get('optimizations', []),
                                'scenes_data': story_data.get('scenes_data', []),
                                'manifest': story_data.get('manifest', {}),
                                # Formatted timestamps
                                'created_at_formatted': created_at_formatted,
                                'days_ago': days_ago,
                                # Position in user's story collection
                                'position_in_user_stories': story_ids.index(story_id) + 1 if story_id in story_ids else 0,
                                'total_user_stories': total_count
                            }
                            
                            stories_data.append(story_summary)
                            print(f"✅ Story {story_id} processed successfully")
                            
                        else:
                            print(f"⚠️ Story document not found: {story_id}")
                            
                    except Exception as story_error:
                        print(f"❌ Error fetching story {story_id}: {str(story_error)}")
                        continue
                
                # 4. BUILD USER INFO with safe datetime handling
                user_info = self._extract_user_info(user_data)
                
                # 5. BUILD PAGINATION INFO
                pagination_info = {
                    "current_page": (offset // limit) + 1,
                    "total_pages": (total_count + limit - 1) // limit,
                    "page_size": limit,
                    "offset": offset,
                    "returned_count": len(stories_data),
                    "total_count": total_count,
                    "has_more": (offset + limit) < total_count
                }
                
                print(f"✅ Successfully fetched {len(stories_data)} stories using ID array method")
                
                return {
                    "stories": stories_data,
                    "total_count": total_count,
                    "has_more": (offset + limit) < total_count,
                    "user_info": user_info,
                    "pagination": pagination_info,
                    "method_used": "story_id_array",
                    "performance_info": {
                        "total_story_ids": len(story_ids),
                        "fetched_stories": len(stories_data),
                        "pagination_applied": True,
                        "batch_fetched": True
                    }
                }
            
            # Execute in thread pool
            result = await loop.run_in_executor(None, get_stories_from_id_array)
            return result
            
        except Exception as e:
            print(f"❌ Error fetching user stories using ID array: {str(e)}")
            return {
                "stories": [],
                "total_count": 0,
                "has_more": False,
                "user_info": None,
                "error": str(e),
                "method_used": "error"
            }

    def _extract_user_info(self, user_data: Dict) -> Dict:
        """Extract user info from user document with timezone-aware datetime handling"""
        def safe_datetime(dt_value):
            """Safely handle datetime conversion with timezone awareness"""
            if dt_value is None:
                return None
            
            # If it's already a datetime object
            if isinstance(dt_value, datetime):
                # If it's naive (no timezone), make it UTC
                if dt_value.tzinfo is None:
                    return dt_value.replace(tzinfo=timezone.utc)
                return dt_value
            
            # If it's a string, try to parse it
            if isinstance(dt_value, str):
                try:
                    parsed_dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
                    if parsed_dt.tzinfo is None:
                        return parsed_dt.replace(tzinfo=timezone.utc)
                    return parsed_dt
                except:
                    return None
            
            # If it's a Firestore timestamp, convert it
            if hasattr(dt_value, 'seconds'):  # Firestore Timestamp
                return datetime.fromtimestamp(dt_value.seconds, tz=timezone.utc)
            
            return None

        return {
            'total_stories': user_data.get('story_count', 0),
            'story_ids_array_length': len(user_data.get('story_ids', [])),
            'last_active': safe_datetime(user_data.get('last_active')),
            'last_story_created': safe_datetime(user_data.get('last_story_created')),
            'last_story_id': user_data.get('last_story_id'),
            'last_story_title': user_data.get('last_story_title'),
            'child_name': user_data.get('child', {}).get('name', 'Your child'),
            'child_age': user_data.get('child', {}).get('age'),
            'child_interests': user_data.get('child', {}).get('interests', []),
            'story_statistics': user_data.get('story_statistics', {}),
            'created_at': safe_datetime(user_data.get('created_at')),
            'story_ids_preview': user_data.get('story_ids', [])[-5:] if user_data.get('story_ids') else []
        }


    async def get_story_details(self, story_id: str, user_id: str = None) -> Dict[str, Any]:
        """Get complete story details with optional user verification"""
        try:
            if not self.db:
                raise HTTPException(status_code=503, detail="Firestore not available")
            
            # Run Firestore query in thread pool
            loop = asyncio.get_event_loop()
            
            def get_story_sync():
                doc_ref = self.db.collection('stories').document(story_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    story_data = doc.to_dict()
                    
                    # Optional: Verify user ownership using story_ids array
                    if user_id:
                        story_owner_id = story_data.get('user_id')
                        if story_owner_id != user_id:
                            return None  # User doesn't own this story
                        
                        # Double-check: Verify story ID is in user's story_ids array
                        user_ref = self.db.collection('users').document(user_id)
                        user_doc = user_ref.get()
                        
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            story_ids = user_data.get('story_ids', [])
                            
                            if story_id not in story_ids:
                                print(f"⚠️ Story {story_id} not found in user {user_id}'s story_ids array")
                                return None
                    
                    return story_data
                else:
                    return None
            
            # Execute in thread pool
            story_data = await loop.run_in_executor(None, get_story_sync)
            
            if story_data:
                return story_data
            else:
                raise HTTPException(status_code=404, detail="Story not found or access denied")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching story details: {str(e)}")

    async def delete_user_story(self, story_id: str, user_id: str) -> bool:
        """Delete a story and remove it from user's story_ids array"""
        try:
            if not self.db:
                raise HTTPException(status_code=503, detail="Firestore not available")
            
            loop = asyncio.get_event_loop()
            
            def delete_story_with_array_update():
                # 1. Verify the story belongs to the user and get current arrays
                user_ref = self.db.collection('users').document(user_id)
                user_doc = user_ref.get()
                
                if not user_doc.exists:
                    return False
                
                user_data = user_doc.to_dict()
                story_ids = user_data.get('story_ids', [])
                
                if story_id not in story_ids:
                    print(f"⚠️ Story {story_id} not found in user {user_id}'s story_ids array")
                    return False
                
                # 2. Verify story document exists and belongs to user
                story_ref = self.db.collection('stories').document(story_id)
                story_doc = story_ref.get()
                
                if not story_doc.exists:
                    return False
                
                story_data = story_doc.to_dict()
                if story_data.get('user_id') != user_id:
                    return False
                
                # 3. Delete from main stories collection
                story_ref.delete()
                
                # 4. Remove story ID from user's story_ids array
                updated_story_ids = [sid for sid in story_ids if sid != story_id]
                
                # 5. Update user document
                user_ref.update({
                    'story_ids': updated_story_ids,
                    'story_count': len(updated_story_ids),
                    'updated_at': datetime.utcnow()
                })
                
                print(f"✅ Removed story {story_id} from user {user_id}'s story_ids array")
                print(f"📋 Updated story_ids: {updated_story_ids}")
                
                return True
            
            result = await loop.run_in_executor(None, delete_story_with_array_update)
            return result
            
        except Exception as e:
            print(f"❌ Error deleting story with array update: {str(e)}")
            return False

    # ===== UTILITY METHODS =====
    
    async def get_user_story_ids(self, user_id: str) -> List[str]:
        """Get just the story IDs array for a user"""
        try:
            if not self.db:
                return []
            
            loop = asyncio.get_event_loop()
            
            def get_ids():
                user_ref = self.db.collection('users').document(user_id)
                user_doc = user_ref.get()
                
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    return user_data.get('story_ids', [])
                return []
            
            result = await loop.run_in_executor(None, get_ids)
            return result
            
        except Exception as e:
            print(f"❌ Error getting user story IDs: {str(e)}")
            return []

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