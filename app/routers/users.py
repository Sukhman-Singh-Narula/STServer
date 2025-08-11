from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from app.models.user import (
    UserRegistration, 
    UserProfileUpdate, 
    UserProfileResponse, 
    AvatarUpdateRequest,
    ParentProfile,
    ChildProfile
)
from app.services.user_service import UserService
from app.dependencies import verify_firebase_token

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()

@router.post("/register", response_model=Dict[str, Any])
async def register_user(request: UserRegistration):
    """Register a new user with parent and child profiles"""
    try:
        # Verify Firebase token and get user ID
        user_id = await verify_firebase_token(request.firebase_token)
        
        # Check if user already exists
        existing_profile = await user_service.get_user_profile(user_id)
        if existing_profile:
            raise HTTPException(status_code=409, detail="User profile already exists")
        
        # Create user profile
        profile = await user_service.create_user_profile(
            user_id=user_id,
            parent=request.parent,
            child=request.child,
            system_prompt=request.system_prompt,
            child_image_base64=request.child_image_base64
        )
        
        return {
            "success": True,
            "message": "User profile created successfully",
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.get("/profile", response_model=Dict[str, Any])
async def get_user_profile(firebase_token: str):
    """Get user profile with avatar information"""
    try:
        # Verify Firebase token and get user ID
        user_id = await verify_firebase_token(firebase_token)
        
        # Get user profile
        profile = await user_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Format dates for JSON serialization
        if 'created_at' in profile:
            profile['created_at'] = profile['created_at'].isoformat() if profile['created_at'] else None
        if 'updated_at' in profile:
            profile['updated_at'] = profile['updated_at'].isoformat() if profile['updated_at'] else None
        if 'last_active' in profile:
            profile['last_active'] = profile['last_active'].isoformat() if profile['last_active'] else None
        
        return {
            "success": True,
            "profile": profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@router.put("/profile", response_model=Dict[str, Any])
async def update_user_profile(request: UserProfileUpdate):
    """Update user profile"""
    try:
        # Verify Firebase token and get user ID
        user_id = await verify_firebase_token(request.firebase_token)
        
        # Update user profile
        updated_profile = await user_service.update_user_profile(
            user_id=user_id,
            parent=request.parent,
            child=request.child,
            system_prompt=request.system_prompt,
            child_image_base64=request.child_image_base64
        )
        
        # Format dates for JSON serialization
        if 'created_at' in updated_profile:
            updated_profile['created_at'] = updated_profile['created_at'].isoformat() if updated_profile['created_at'] else None
        if 'updated_at' in updated_profile:
            updated_profile['updated_at'] = updated_profile['updated_at'].isoformat() if updated_profile['updated_at'] else None
        if 'last_active' in updated_profile:
            updated_profile['last_active'] = updated_profile['last_active'].isoformat() if updated_profile['last_active'] else None
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "profile": updated_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

@router.delete("/profile")
async def delete_user_profile(firebase_token: str):
    """Delete user profile and all associated data"""
    try:
        # Verify Firebase token and get user ID
        user_id = await verify_firebase_token(firebase_token)
        
        # Delete user data
        await user_service.delete_user_data(user_id)
        
        return {
            "success": True,
            "message": "User profile and data deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete profile: {str(e)}")

@router.put("/avatar", response_model=Dict[str, Any])
async def update_avatar_settings(request: AvatarUpdateRequest):
    """Update avatar settings for child or parent"""
    try:
        # Verify Firebase token and get user ID
        user_id = await verify_firebase_token(request.firebase_token)
        
        # Update avatar settings
        updated_profile = await user_service.update_avatar_settings(
            user_id=user_id,
            target=request.target,
            avatar_seed=request.avatar_seed,
            avatar_style=request.avatar_style
        )
        
        # Format dates for JSON serialization
        if 'created_at' in updated_profile:
            updated_profile['created_at'] = updated_profile['created_at'].isoformat() if updated_profile['created_at'] else None
        if 'updated_at' in updated_profile:
            updated_profile['updated_at'] = updated_profile['updated_at'].isoformat() if updated_profile['updated_at'] else None
        if 'last_active' in updated_profile:
            updated_profile['last_active'] = updated_profile['last_active'].isoformat() if updated_profile['last_active'] else None
        
        return {
            "success": True,
            "message": f"Avatar settings updated for {request.target}",
            "profile": updated_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update avatar: {str(e)}")

@router.get("/avatar/{target}", response_model=Dict[str, Any])
async def get_avatar_settings(target: str, firebase_token: str):
    """Get avatar settings for child or parent"""
    try:
        # Verify Firebase token and get user ID
        user_id = await verify_firebase_token(firebase_token)
        
        # Get avatar settings
        avatar_settings = await user_service.get_avatar_settings(user_id, target)
        
        return {
            "success": True,
            "target": target,
            "avatar_settings": avatar_settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get avatar settings: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint for user service"""
    try:
        # Simple health check - try to access Firestore
        from app.utils.firebase_init import is_firebase_available
        
        return {
            "success": True,
            "service": "user_service",
            "firebase_available": is_firebase_available(),
            "status": "healthy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Additional endpoints for managing child and parent data separately

@router.put("/child", response_model=Dict[str, Any])
async def update_child_profile(firebase_token: str, child: ChildProfile):
    """Update only child profile information"""
    try:
        user_id = await verify_firebase_token(firebase_token)
        
        # Create UserProfileUpdate with only child data
        update_request = UserProfileUpdate(
            firebase_token=firebase_token,
            child=child
        )
        
        updated_profile = await user_service.update_user_profile(
            user_id=user_id,
            child=child
        )
        
        return {
            "success": True,
            "message": "Child profile updated successfully",
            "child": updated_profile.get('child')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update child profile: {str(e)}")

@router.put("/parent", response_model=Dict[str, Any])
async def update_parent_profile(firebase_token: str, parent: ParentProfile):
    """Update only parent profile information"""
    try:
        user_id = await verify_firebase_token(firebase_token)
        
        updated_profile = await user_service.update_user_profile(
            user_id=user_id,
            parent=parent
        )
        
        return {
            "success": True,
            "message": "Parent profile updated successfully",
            "parent": updated_profile.get('parent')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update parent profile: {str(e)}")

@router.get("/child", response_model=Dict[str, Any])
async def get_child_profile(firebase_token: str):
    """Get only child profile with avatar information"""
    try:
        user_id = await verify_firebase_token(firebase_token)
        
        profile = await user_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        child_data = profile.get('child', {})
        
        return {
            "success": True,
            "child": child_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get child profile: {str(e)}")

@router.get("/parent", response_model=Dict[str, Any])
async def get_parent_profile(firebase_token: str):
    """Get only parent profile with avatar information"""
    try:
        user_id = await verify_firebase_token(firebase_token)
        
        profile = await user_service.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        parent_data = profile.get('parent', {})
        
        return {
            "success": True,
            "parent": parent_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get parent profile: {str(e)}")