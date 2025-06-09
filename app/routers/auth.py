# File: app/routers/auth.py - FINAL CORRECTED VERSION
from fastapi import APIRouter, HTTPException, Depends, Response, Request
from app.models.auth import AuthResponse, TokenVerificationRequest
from app.models.user import UserRegistration, UserProfileUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from datetime import datetime

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

# CORRECTED: This is the proper way to define a POST endpoint with Pydantic request body
@router.post("/verify-token")
async def verify_token_endpoint(
    token_request: TokenVerificationRequest,  # This MUST be the first parameter for request body
    response: Response, 
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify Firebase token and return user info - CORRECTED VERSION"""
    add_cors_headers(response)
    
    print(f"🔍 verify-token endpoint called")
    print(f"📝 Received token_request: {token_request}")
    print(f"📝 Token (first 20 chars): {token_request.firebase_token[:20] if token_request.firebase_token else 'None'}...")
    
    return await auth_service.verify_token(token_request.firebase_token)

# DEBUG ENDPOINTS for testing
@router.post("/test-simple")
async def test_simple_endpoint(response: Response):
    """Simple test endpoint to verify server is working"""
    add_cors_headers(response)
    return {"message": "Server is working", "timestamp": datetime.utcnow().isoformat()}

@router.post("/test-echo")
async def test_echo_endpoint(request: Request, response: Response):
    """Echo endpoint to test request body parsing"""
    add_cors_headers(response)
    
    # Get raw body
    body = await request.body()
    
    # Try to parse headers
    headers = dict(request.headers)
    
    return {
        "message": "Echo test",
        "method": request.method,
        "url": str(request.url),
        "headers": headers,
        "body_raw": body.decode('utf-8') if body else None,
        "body_length": len(body) if body else 0,
        "content_type": headers.get('content-type', 'Not set')
    }

@router.post("/verify-token-debug")
async def verify_token_debug(
    request: Request,
    response: Response, 
    auth_service: AuthService = Depends(get_auth_service)
):
    """DEBUG: Alternative token verification that accepts raw request body"""
    add_cors_headers(response)
    
    # Get raw body
    body = await request.body()
    print(f"🔍 DEBUG endpoint - Raw body: {body}")
    print(f"🔍 DEBUG endpoint - Body type: {type(body)}")
    print(f"🔍 DEBUG endpoint - Body length: {len(body)}")
    
    try:
        import json
        # Try to parse as JSON
        if body:
            body_str = body.decode('utf-8')
            print(f"🔍 DEBUG endpoint - Body as string: {body_str}")
            
            # Try different parsing approaches
            try:
                # Method 1: Parse as object
                parsed = json.loads(body_str)
                print(f"🔍 DEBUG endpoint - Parsed as object: {parsed}")
                
                if isinstance(parsed, dict) and 'firebase_token' in parsed:
                    token = parsed['firebase_token']
                    print(f"🔍 DEBUG endpoint - Extracted token: {token[:20]}...")
                    return await auth_service.verify_token(token)
                elif isinstance(parsed, str):
                    # Maybe it's a quoted string
                    print(f"🔍 DEBUG endpoint - Parsed as string: {parsed}")
                    return await auth_service.verify_token(parsed)
                else:
                    return {"error": f"Unexpected parsed type: {type(parsed)}", "parsed": parsed}
                    
            except json.JSONDecodeError as e:
                print(f"🔍 DEBUG endpoint - JSON decode error: {e}")
                return {"error": f"JSON decode error: {e}", "body": body_str}
        else:
            return {"error": "Empty body received"}
            
    except Exception as e:
        print(f"🔍 DEBUG endpoint - Exception: {e}")
        return {"error": str(e)}

@router.options("/register")
@router.options("/profile/{firebase_token}")
@router.options("/verify-token")
@router.options("/verify-token-debug")
@router.options("/test-simple")
@router.options("/test-echo")
async def auth_options(response: Response):
    """Handle preflight OPTIONS requests for auth endpoints"""
    add_cors_headers(response)
    return {"message": "OK"}