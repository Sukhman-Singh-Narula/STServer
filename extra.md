# ESP32 Storytelling Server - Complete Setup & Testing Guide

## 📋 Prerequisites

### 1. Python Environment
```bash
python --version  # Should be 3.8+
pip install --upgrade pip
```

### 2. Required API Accounts
- **Firebase Project** (free)
- **Groq Account** (free tier available)
- **OpenAI Account** (paid - DALL-E requires credits)
- **ElevenLabs Account** (free tier available)

## 🔧 Environment Setup

### 1. Create `.env` File

Create a `.env` file in your project root:

```env
# === API KEYS ===
GROQ_API_KEY=gsk_your_groq_api_key_here
OPENAI_API_KEY=sk-your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# === FIREBASE CONFIGURATION ===
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com

# === STORY SETTINGS ===
MAX_SCENES=6
AUDIO_FORMAT=mp3
IMAGE_SIZE=1024x1024

# === SERVER SETTINGS ===
DEBUG=true
PORT=8000
HOST=0.0.0.0

# === OPTIONAL SETTINGS ===
# CORS_ORIGINS=http://localhost:3000,http://localhost:8080
# LOG_LEVEL=INFO
```

### 2. Firebase Setup Steps

#### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name (e.g., "storytelling-device")
4. Enable Google Analytics (optional)
5. Wait for project creation

#### Step 2: Enable Required Services
```bash
# Enable Authentication
1. Go to Authentication > Sign-in method
2. Enable "Email/Password"
3. Enable "Anonymous" (for testing)

# Enable Firestore Database
1. Go to Firestore Database
2. Click "Create database"
3. Start in test mode (for development)
4. Choose location (us-central1 recommended)

# Enable Storage
1. Go to Storage
2. Click "Get started"
3. Start in test mode (for development)
4. Choose location (same as Firestore)
```

#### Step 3: Download Service Account Key
1. Go to Project Settings (gear icon)
2. Click "Service accounts" tab
3. Click "Generate new private key"
4. Save as `firebase-credentials.json` in project root

#### Step 4: Get Storage Bucket Name
1. Go to Storage in Firebase Console
2. Copy the bucket name (e.g., `your-project-id.appspot.com`)
3. Add to `.env` file

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv storytelling_env
source storytelling_env/bin/activate  # On Windows: storytelling_env\Scripts\activate

# Install dependencies
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install websockets==12.0
pip install firebase-admin==6.2.0
pip install openai==1.3.5
pip install groq==0.4.1
pip install elevenlabs==0.2.26
pip install httpx==0.25.2
pip install pydantic==2.5.0
pip install python-multipart==0.0.6
pip install python-dotenv==1.0.0
```

Or create `requirements.txt`:
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
websockets==12.0
firebase-admin==6.2.0
openai==1.3.5
groq==0.4.1
elevenlabs==0.2.26
httpx==0.25.2
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0
```

Then: `pip install -r requirements.txt`

## 🚀 Running the Server

### 1. Load Environment Variables

```bash
# Option 1: Export manually
export GROQ_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
# ... etc

# Option 2: Use python-dotenv (recommended)
# Add to main.py top:
from dotenv import load_dotenv
load_dotenv()
```

### 2. Start the Server

```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Verify Server is Running

Open browser: `http://localhost:8000/docs` (FastAPI auto-generated documentation)

## 🧪 Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-05-28T10:30:00",
  "services": {
    "firebase": "connected",
    "groq": "configured",
    "openai": "configured",
    "elevenlabs": "configured"
  }
}
```

### 2. Test Endpoint

```bash
curl http://localhost:8000/test
```

### 3. User Signup (Testing)

```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "display_name": "Test User"
  }'
```

### 4. Generate Story (Full Test)

**Step 1: Get Firebase ID Token**

You'll need a Firebase ID token. For testing, you can:

#### Option A: Use Firebase Auth REST API
```bash
# Replace YOUR_API_KEY with your Firebase Web API Key
curl -X POST https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_API_KEY \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "returnSecureToken": true
  }'
```

#### Option B: Create a Simple Test Script

Create `test_client.py`:
```python
import requests
import json

# 1. Test health
response = requests.get("http://localhost:8000/health")
print("Health:", response.json())

# 2. Create user
signup_data = {
    "email": "test@example.com",
    "password": "testpassword123",
    "display_name": "Test User"
}
response = requests.post("http://localhost:8000/auth/signup", json=signup_data)
print("Signup:", response.json())

# 3. You'll need to get Firebase ID token separately
# For testing, you can use Firebase Admin SDK to create custom tokens
```

**Step 2: Generate Story**
```bash
curl -X POST http://localhost:8000/generate-story \
  -H "Content-Type: application/json" \
  -d '{
    "firebase_token": "your_firebase_id_token_here",
    "prompt": "Tell a story about a brave little mouse who discovers a magical garden"
  }'
```

### 5. WebSocket Testing

Create `test_websocket.py`:
```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/your_firebase_token_here"
    
    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        message = await websocket.recv()
        print(f"Received: {message}")
        
        # Send story status
        status_message = {
            "type": "story_status",
            "story_id": "story_12345",
            "status": "playing"
        }
        await websocket.send(json.dumps(status_message))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Response: {response}")

# Run the test
asyncio.run(test_websocket())
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Firebase Authentication Error
```
Error: Invalid Firebase token
```
**Solution:**
- Verify `firebase-credentials.json` path is correct
- Check Firebase project settings
- Ensure service account has proper permissions

#### 2. Storage Bucket Error
```
Error: The default Firebase app does not exist
```
**Solution:**
- Verify `FIREBASE_STORAGE_BUCKET` is set correctly
- Check bucket name format (no `gs://` prefix)
- Ensure Storage is enabled in Firebase Console

#### 3. API Key Errors
```
Error: Invalid API key
```
**Solution:**
- Verify all API keys are set in environment
- Check API key permissions and quotas
- Ensure keys are not expired

#### 4.