from fastapi import APIRouter, HTTPException, Depends, Response
from app.models.auth import AuthResponse
from app.models.user import UserRegistration, UserProfileUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["authentication"])

# Dependency to get services (lazy initialization)
def get_user_service():
    return UserService()

def get_auth_service(user_service: UserService = Depends(get_user_service)):
    return AuthService(user_service)

def add_cors_headers(response: Response):
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"

@router.post("/register", response_model=AuthResponse)
async def register_user(request: UserRegistration, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    """Register a new user with parent and child profiles"""
    add_cors_headers(response)
    return await auth_service.register_user(request)

@router.get("/profile/{firebase_token}")
async def get_user_profile_endpoint(firebase_token: str, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    """Get user profile information"""
    add_cors_headers(response)
    return await auth_service.get_user_profile(firebase_token)

@router.put("/profile", response_model=AuthResponse)
async def update_user_profile_endpoint(request: UserProfileUpdate, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    """Update user profile information"""
    add_cors_headers(response)
    return await auth_service.update_user_profile(request)

@router.delete("/profile/{firebase_token}")
async def delete_user_profile(firebase_token: str, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    """Delete user profile and associated data"""
    add_cors_headers(response)
    return await auth_service.delete_user_profile(firebase_token)

@router.post("/verify-token")
async def verify_token_endpoint(firebase_token: str, response: Response, auth_service: AuthService = Depends(get_auth_service)):
    """Verify Firebase token and return user info"""
    add_cors_headers(response)
    return await auth_service.verify_token(firebase_token)

@router.options("/register")
@router.options("/profile/{firebase_token}")
@router.options("/verify-token")
async def auth_options(response: Response):
    """Handle preflight OPTIONS requests for auth endpoints"""
    add_cors_headers(response)
    return {"message": "OK"}