from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.dependencies import verify_firebase_token
from app.models.auth import AuthResponse
from app.models.user import UserRegistration, UserProfileUpdate
from app.services.user_service import UserService

class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
    
    async def register_user(self, request: UserRegistration) -> AuthResponse:
        """Register a new user with parent and child profiles"""
        try:
            # Verify Firebase token
            user_info = await verify_firebase_token(request.firebase_token)
            user_id = user_info['uid']
            
            # Check if user already exists
            existing_profile = await self.user_service.get_user_profile(user_id)
            if existing_profile:
                return AuthResponse(
                    success=False,
                    message="User profile already exists. Use update endpoint to modify.",
                    user_id=user_id,
                    profile=existing_profile
                )
            
            # Create user profile
            profile = await self.user_service.create_user_profile(
                user_id=user_id,
                parent=request.parent,
                child=request.child,
                system_prompt=request.system_prompt
            )
            
            return AuthResponse(
                success=True,
                message="User profile created successfully",
                user_id=user_id,
                profile=profile
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def get_user_profile(self, firebase_token: str) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            # Verify Firebase token
            user_info = await verify_firebase_token(firebase_token)
            user_id = user_info['uid']
            
            # Get user profile
            profile = await self.user_service.get_user_profile(user_id)
            
            if not profile:
                raise HTTPException(status_code=404, detail="User profile not found")
            
            return {
                "success": True,
                "user_id": user_id,
                "profile": profile
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")
    
    async def update_user_profile(self, request: UserProfileUpdate) -> AuthResponse:
        """Update user profile information"""
        try:
            # Verify Firebase token
            user_info = await verify_firebase_token(request.firebase_token)
            user_id = user_info['uid']
            
            # Update user profile
            updated_profile = await self.user_service.update_user_profile(
                user_id=user_id,
                parent=request.parent,
                child=request.child,
                system_prompt=request.system_prompt
            )
            
            return AuthResponse(
                success=True,
                message="User profile updated successfully",
                user_id=user_id,
                profile=updated_profile
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")
    
    async def delete_user_profile(self, firebase_token: str) -> Dict[str, Any]:
        """Delete user profile and associated data"""
        try:
            # Verify Firebase token
            user_info = await verify_firebase_token(firebase_token)
            user_id = user_info['uid']
            
            # Delete user data
            await self.user_service.delete_user_data(user_id)
            
            return {
                "success": True,
                "message": "User profile and associated data deleted successfully",
                "user_id": user_id
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")
    
    async def verify_token(self, firebase_token: str) -> Dict[str, Any]:
        """Verify Firebase token and return user info"""
        try:
            user_info = await verify_firebase_token(firebase_token)
            
            # Get user profile if exists
            profile = await self.user_service.get_user_profile(user_info['uid'])
            
            return {
                "success": True,
                "valid": True,
                "user_info": {
                    "uid": user_info['uid'],
                    "email": user_info.get('email'),
                    "email_verified": user_info.get('email_verified', False)
                },
                "has_profile": profile is not None,
                "profile": profile
            }
            
        except HTTPException as e:
            return {
                "success": False,
                "valid": False,
                "error": str(e.detail)
            }