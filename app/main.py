import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.firebase_init import initialize_firebase

# Initialize Firebase IMMEDIATELY, before any imports that might use it
initialize_firebase()

# Initialize ElevenLabs if available
if settings.elevenlabs_api_key and settings.elevenlabs_api_key != "test":
    try:
        from elevenlabs import set_api_key
        set_api_key(settings.elevenlabs_api_key)
        print("✅ ElevenLabs initialized successfully")
    except Exception as e:
        print(f"⚠️ ElevenLabs initialization failed: {str(e)}")

# Initialize FastAPI app
app = FastAPI(
    title="ESP32 Storytelling Server", 
    version="1.0.0",
    description="Modular FastAPI server for ESP32 storytelling device"
)

# Enhanced CORS middleware for React Native compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language", 
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
        "User-Agent",
        "Cache-Control",
        "Pragma",
    ],
    expose_headers=["*"],
    max_age=86400,  # 24 hours preflight cache
)

# Add a custom CORS middleware for debugging and extra handling
@app.middleware("http")
async def enhanced_cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    
    # Log all requests for debugging
    print(f"🌐 {method} Request from origin: {origin}")
    
    # Handle preflight OPTIONS requests manually
    if method == "OPTIONS":
        response = JSONResponse({"message": "OK"})
        
        # Add comprehensive CORS headers
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
            
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        
        print(f"✅ OPTIONS response sent to {origin}")
        return response
    
    # Process the request
    response = await call_next(request)
    
    # Add CORS headers to all responses
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
        
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

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

# Startup event (now mainly for logging)
@app.on_event("startup")
async def startup_event():
    """Log startup completion and CORS configuration"""
    print("🚀 ESP32 Storytelling Server started successfully!")
    print(f"📊 Environment: {'Development' if settings.debug else 'Production'}")
    print(f"🌐 CORS Origins: {settings.cors_origins_list}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "ESP32 Storytelling Server API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
        "cors_origins": settings.cors_origins_list
    }

# Global OPTIONS handler for any missed routes
@app.options("/{path:path}")
async def global_options_handler(path: str, request: Request):
    """Handle preflight OPTIONS requests for any path"""
    origin = request.headers.get("origin")
    print(f"🔧 Global OPTIONS handler for /{path} from {origin}")
    
    response = JSONResponse({"message": "OK"})
    
    # Add comprehensive CORS headers
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
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
            "GROQ_API_KEY", 
            "OPENAI_API_KEY", 
            "ELEVENLABS_API_KEY", 
            "FIREBASE_CREDENTIALS_PATH", 
            "FIREBASE_STORAGE_BUCKET"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var) or os.getenv(var) == "test"]
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these environment variables before running the server.")
            print("💡 Tip: Set DEBUG=true for development/testing mode")
            exit(1)
    else:
        print("🧪 Running in debug mode - external services may not work")
    
    print("🔧 Starting server...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )