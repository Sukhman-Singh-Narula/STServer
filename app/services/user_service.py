from datetime import datetime
from typing import Dict, Any, Optional
import base64
from fastapi import HTTPException
from app.models.user import ParentProfile, ChildProfile
from app.utils.firebase_init import get_firestore_client, is_firebase_available
from app.services.storage_service import StorageService
from app.config import settings

class UserService:
    def __init__(self):
        self.users_collection = 'users'
        self.system_prompts = {}  # In-memory cache
        # Don't initialize Firebase client here - do it lazily
        self._db = None
        self._storage_service = None
    
    @property
    def db(self):
        """Lazy initialization of Firestore client"""
        if self._db is None:
            self._db = get_firestore_client()
        return self._db
    
    @property
    def storage_service(self):
        """Lazy initialization of Storage service"""
        if self._storage_service is None:
            self._storage_service = StorageService()
        return self._storage_service
    
    async def create_user_profile(self, user_id: str, parent: ParentProfile, child: ChildProfile, system_prompt: str = None, child_image_base64: str = None) -> Dict[str, Any]:
        """Create a new user profile in Firestore"""
        try:
            # Check if Firebase is available
            if not is_firebase_available() or self.db is None:
                raise HTTPException(status_code=503, detail="Firebase service is not available")
            
            # Generate personalized system prompt based on child's info
            if not system_prompt:
                system_prompt = self._generate_personalized_prompt(child)
            
            # Handle image upload if provided
            image_url = None
            if child_image_base64:
                try:
                    # Decode base64 image
                    image_data = base64.b64decode(child_image_base64)
                    # Upload to Firebase Storage
                    image_url = await self.storage_service.upload_user_image(image_data, user_id)
                    print(f"✅ Child profile image uploaded: {image_url}")
                except Exception as e:
                    print(f"⚠️ Failed to upload child profile image: {str(e)}")
                    # Continue without image rather than failing the entire registration
            
            profile_data = {
                'user_id': user_id,
                'parent': {
                    'name': parent.name,
                    'email': parent.email,
                    'phone_number': parent.phone_number,
                    'avatar_seed': getattr(parent, 'avatar_seed', None),
                    'avatar_style': getattr(parent, 'avatar_style', 'avataaars'),
                    'avatar_generated': getattr(parent, 'avatar_generated', False)
                },
                'child': {
                    'name': child.name,
                    'age': child.age,
                    'interests': child.interests,
                    'image_url': image_url,  # Will be None if no image was provided
                    'avatar_seed': getattr(child, 'avatar_seed', None),
                    'avatar_style': getattr(child, 'avatar_style', 'avataaars'),
                    'avatar_generated': getattr(child, 'avatar_generated', False)
                },
                'system_prompt': system_prompt,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'story_count': 0,
                'last_active': datetime.utcnow()
            }
            
            # Save to Firestore
            doc_ref = self.db.collection(self.users_collection).document(user_id)
            doc_ref.set(profile_data)
            
            # Store system prompt in memory for quick access
            self.system_prompts[user_id] = system_prompt
            
            return profile_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create user profile: {str(e)}")
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Firestore"""
        try:
            if not is_firebase_available() or self.db is None:
                return None
            
            doc_ref = self.db.collection(self.users_collection).document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                profile = doc.to_dict()
                # Load system prompt into memory if not already there
                if user_id not in self.system_prompts and 'system_prompt' in profile:
                    self.system_prompts[user_id] = profile['system_prompt']
                return profile
            return None
            
        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return None
    
    async def update_user_profile(self, user_id: str, parent: ParentProfile = None, child: ChildProfile = None, system_prompt: str = None, child_image_base64: str = None) -> Dict[str, Any]:
        """Update user profile in Firestore"""
        try:
            if not is_firebase_available() or self.db is None:
                raise HTTPException(status_code=503, detail="Firebase service is not available")
            
            doc_ref = self.db.collection(self.users_collection).document(user_id)
            
            # Get existing profile
            existing_profile = await self.get_user_profile(user_id)
            if not existing_profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Prepare updates
            updates = {
                'updated_at': datetime.utcnow(),
                'last_active': datetime.utcnow()
            }
            
            if parent:
                updates['parent'] = {
                    'name': parent.name,
                    'email': parent.email,
                    'phone_number': parent.phone_number,
                    'avatar_seed': getattr(parent, 'avatar_seed', None),
                    'avatar_style': getattr(parent, 'avatar_style', 'avataaars'),
                    'avatar_generated': getattr(parent, 'avatar_generated', False)
                }
            
            if child:
                # Handle image upload if provided
                image_url = existing_profile.get('child', {}).get('image_url')  # Keep existing image URL
                if child_image_base64:
                    try:
                        # Decode base64 image
                        image_data = base64.b64decode(child_image_base64)
                        # Upload new image to Firebase Storage
                        image_url = await self.storage_service.upload_user_image(image_data, user_id)
                        print(f"✅ Child profile image updated: {image_url}")
                    except Exception as e:
                        print(f"⚠️ Failed to upload child profile image: {str(e)}")
                        # Keep existing image if upload fails
                
                updates['child'] = {
                    'name': child.name,
                    'age': child.age,
                    'interests': child.interests,
                    'image_url': image_url,  # Updated or existing image URL
                    'avatar_seed': getattr(child, 'avatar_seed', None),
                    'avatar_style': getattr(child, 'avatar_style', 'avataaars'),
                    'avatar_generated': getattr(child, 'avatar_generated', False)
                }
                # Regenerate system prompt if child info changed
                if not system_prompt:
                    system_prompt = self._generate_personalized_prompt(child)
                    updates['system_prompt'] = system_prompt
            
            if system_prompt:
                updates['system_prompt'] = system_prompt
                self.system_prompts[user_id] = system_prompt
            
            # Update Firestore
            doc_ref.update(updates)
            
            # Return updated profile
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")
    
    async def delete_user_data(self, user_id: str):
        """Delete user profile and associated data"""
        try:
            if not is_firebase_available() or self.db is None:
                raise HTTPException(status_code=503, detail="Firebase service is not available")
            
            # Delete user profile
            user_doc_ref = self.db.collection('users').document(user_id)
            user_doc_ref.delete()
            
            # Delete user stories
            stories_ref = self.db.collection('stories')
            user_stories = stories_ref.where('user_id', '==', user_id).stream()
            
            for story in user_stories:
                story.reference.delete()
            
            # Remove from memory
            if user_id in self.system_prompts:
                del self.system_prompts[user_id]
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete user data: {str(e)}")
    
    def get_user_system_prompt(self, user_id: str) -> str:
        """Get user's system prompt from memory or default"""
        return self.system_prompts.get(user_id, settings.default_system_prompt)
    
    async def update_avatar_settings(self, user_id: str, target: str, avatar_seed: str, avatar_style: str = "avataaars") -> Dict[str, Any]:
        """Update avatar settings for child or parent"""
        try:
            if not is_firebase_available() or self.db is None:
                raise HTTPException(status_code=503, detail="Firebase service is not available")
            
            if target not in ["child", "parent"]:
                raise HTTPException(status_code=400, detail="Target must be 'child' or 'parent'")
            
            doc_ref = self.db.collection(self.users_collection).document(user_id)
            
            # Get existing profile
            existing_profile = await self.get_user_profile(user_id)
            if not existing_profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            # Prepare updates
            updates = {
                f'{target}.avatar_seed': avatar_seed,
                f'{target}.avatar_style': avatar_style,
                f'{target}.avatar_generated': True,
                'updated_at': datetime.utcnow(),
                'last_active': datetime.utcnow()
            }
            
            # Update Firestore
            doc_ref.update(updates)
            
            # Return updated profile
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update avatar settings: {str(e)}")
    
    async def get_avatar_settings(self, user_id: str, target: str) -> Dict[str, Any]:
        """Get avatar settings for child or parent"""
        try:
            if target not in ["child", "parent"]:
                raise HTTPException(status_code=400, detail="Target must be 'child' or 'parent'")
            
            profile = await self.get_user_profile(user_id)
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            target_data = profile.get(target, {})
            return {
                "avatar_seed": target_data.get('avatar_seed'),
                "avatar_style": target_data.get('avatar_style', 'avataaars'),
                "avatar_generated": target_data.get('avatar_generated', False)
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get avatar settings: {str(e)}")

    def update_system_prompt(self, user_id: str, system_prompt: str):
        """Update system prompt in memory and Firestore"""
        self.system_prompts[user_id] = system_prompt
        
        if is_firebase_available() and self.db is not None:
            try:
                # Update in Firestore
                user_ref = self.db.collection('users').document(user_id)
                user_ref.update({
                    'system_prompt': system_prompt,
                    'updated_at': datetime.utcnow()
                })
            except Exception as e:
                print(f"Failed to update system prompt in Firestore: {str(e)}")
    
    def _generate_personalized_prompt(self, child: ChildProfile) -> str:
        """Generate a personalized system prompt based on child's profile"""
        interests_str = ", ".join(child.interests) if child.interests else "various topics"
        
        age_appropriate_language = {
            range(3, 6): "very simple words and short sentences",
            range(6, 9): "simple language with some new vocabulary",
            range(9, 13): "age-appropriate language with educational elements"
        }
        
        language_level = "simple, engaging language"
        for age_range, description in age_appropriate_language.items():
            if child.age in age_range:
                language_level = description
                break
        
        # Add image reference if available
        image_reference = ""
        if hasattr(child, 'image_url') and child.image_url:
            image_reference = f"\n\nWhen {child.name} appears in stories, their appearance should be consistent with their profile image."
        
        personalized_prompt = f"""You are a creative children's storyteller creating stories for {child.name}, who is {child.age} years old and loves {interests_str}.

Create engaging, age-appropriate stories that are educational and fun. Use {language_level} that's perfect for a {child.age}-year-old.

Incorporate themes and elements related to {interests_str} when possible, making {child.name} feel like the stories are made just for them.

Structure your story into clear scenes that can be visualized. Each scene should be 2-3 sentences long and paint a vivid picture.

Make the stories positive, encouraging, and help build {child.name}'s imagination and confidence.{image_reference}"""

        return personalized_prompt