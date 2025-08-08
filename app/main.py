import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

from app.config import settings
from app.utils.firebase_init import initialize_firebase

# Initialize Firebase IMMEDIATELY, before any imports that might use it
initialize_firebase()

# Validate OpenAI API key early
if settings.openai_api_key and settings.openai_api_key != "test":
    try:
        from openai import OpenAI
        # Test the API key
        client = OpenAI(api_key=settings.openai_api_key)
        print("✅ OpenAI client initialized successfully")
        print("🎵 Using OpenAI TTS for audio generation")
        print("🖼️ Using DeepAI for fast image generation")
    except Exception as e:
        print(f"⚠️ OpenAI initialization failed: {str(e)}")
else:
    print("⚠️ OpenAI API key not configured - story generation will not work")

# Initialize FastAPI app
app = FastAPI(
    title="ESP32 Storytelling Server - Optimized OpenAI Edition", 
    version="3.0.0",
    description="Optimized FastAPI server for ESP32 storytelling device - OpenAI TTS + DeepAI with parallel processing"
)

# Enhanced CORS middleware for React Native compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],
    max_age=86400,  # 24 hours preflight cache
)

# ENHANCED DEBUG MIDDLEWARE
@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    print(f"\n🌐 === INCOMING REQUEST ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Headers: {dict(request.headers)}")
    
    # Log request body for POST requests
    if request.method in ["POST", "PUT", "PATCH"]:
        # Read the body (this consumes it, so we need to reconstruct the request)
        body = await request.body()
        print(f"Body (raw bytes): {body}")
        print(f"Body (length): {len(body)}")
        
        if body:
            try:
                body_str = body.decode('utf-8')
                print(f"Body (decoded): {body_str}")
                
                # Try to parse as JSON
                try:
                    body_json = json.loads(body_str)
                    print(f"Body (parsed JSON): {body_json}")
                except json.JSONDecodeError:
                    print(f"Body (not valid JSON): {body_str}")
            except UnicodeDecodeError:
                print(f"Body (binary data): {body[:100]}...")
        else:
            print("Body: Empty")
        
        # Reconstruct request with body
        from fastapi import Request as FastAPIRequest
        from starlette.requests import Request as StarletteRequest
        
        # Create a new request with the body
        receive = request._receive
        
        async def new_receive():
            return {"type": "http.request", "body": body, "more_body": False}
        
        # Replace the receive callable
        request._receive = new_receive
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        print("✅ Handling OPTIONS preflight request")
        response = JSONResponse({"message": "OK"})
        
        # Add comprehensive CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        
        print(f"✅ OPTIONS response headers: {dict(response.headers)}")
        return response
    
    # Process the request
    try:
        response = await call_next(request)
        print(f"✅ Response status: {response.status_code}")
        return response
    except Exception as e:
        print(f"❌ Request processing error: {e}")
        import traceback
        traceback.print_exc()
        raise

# NOW we can safely import routers (Firebase is already initialized)
from app.routers import auth, health

app.include_router(auth.router)
app.include_router(health.router)

# Conditionally include other routers that depend on external services
try:
    from app.routers import stories, websocket
    app.include_router(stories.router)
    app.include_router(websocket.router)
    print("✅ All routers loaded successfully")
except ImportError as e:
    print(f"⚠️ Some routers could not be loaded: {str(e)}")
    print("📝 Basic functionality will still work")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup completion and configuration"""
    print("🚀 ESP32 Storytelling Server started successfully!")
    print(f"📊 Environment: {'Development' if settings.debug else 'Production'}")
    print(f"🌐 CORS Origins: {settings.cors_origins_list}")
    print("🤖 AI Services:")
    print(f"  - OpenAI: {'✅ Configured' if settings.openai_api_key and settings.openai_api_key != 'test' else '❌ Not configured'}")
    print(f"  - Firebase: {'✅ Connected' if initialize_firebase() else '❌ Not connected'}")
    print("📖 Story Generation: OpenAI TTS + DeepAI with Full Parallel Processing")
    print("⚡ Optimizations:")
    print(f"  - Parallel Scene Processing: {settings.max_concurrent_scenes} concurrent scenes")
    print(f"  - DeepAI for Fast Images: ✅ Enabled")
    print(f"  - Batch Audio Generation: {'✅ Enabled' if settings.enable_batch_audio else '❌ Disabled'}")
    print(f"  - Batch Image Generation: {'✅ Enabled' if settings.enable_batch_images else '❌ Disabled'}")
    print(f"  - Parallel Uploads: {'✅ Enabled' if settings.enable_parallel_uploads else '❌ Disabled'}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ESP32 Storytelling Server API - Optimized OpenAI Edition",
        "version": "3.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
        "ai_stack": "OpenAI TTS + DALL-E 2 with Full Parallel Processing",
        "optimizations": {
            "parallel_processing": settings.max_concurrent_scenes,
            "dalle_2_enabled": settings.use_dalle_2_for_speed,
            "batch_audio": settings.enable_batch_audio,
            "batch_images": settings.enable_batch_images,
            "parallel_uploads": settings.enable_parallel_uploads
        },
        "cors_origins": settings.cors_origins_list
    }

# Global OPTIONS handler for any missed routes
@app.options("/{path:path}")
async def global_options_handler(path: str, request: Request):
    """Handle preflight OPTIONS requests for any path"""
    print(f"🔧 Global OPTIONS handler for /{path}")
    
    response = JSONResponse({"message": "OK"})
    
    # Add comprehensive CORS headers
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    # Check for required environment variables only if not in test mode
    if not settings.debug:
        required_vars = [
            "OPENAI_API_KEY",  # Required for GPT-4, TTS
            "REPLICATE_API_TOKEN",  # Required for SDXL image generation
            "FIREBASE_CREDENTIALS_PATH", 
            "FIREBASE_STORAGE_BUCKET"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var) or os.getenv(var) == "test"]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these environment variables before running the server.")
            print("💡 Tip: Set DEBUG=true for development/testing mode")
            print("🤖 Note: Using OpenAI TTS + DeepAI for optimal performance")
            exit(1)
    else:
        print("🧪 Running in debug mode - external services may not work")
    
    print("🔧 Starting optimized server...")
    print("⚡ Performance features enabled:")
    print(f"   - Parallel processing: {settings.max_concurrent_scenes} scenes")
    print(f"   - DeepAI: True")
    print(f"   - Batch audio: {settings.enable_batch_audio}")
    print(f"   - Batch images: {settings.enable_batch_images}")
    print(f"   - Parallel uploads: {settings.enable_parallel_uploads}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )