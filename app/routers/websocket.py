# ===== app/routers/websocket.py =====
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.dependencies import verify_firebase_token
from app.services.storage_service import StorageService

router = APIRouter(tags=["websocket"])
storage_service = StorageService()

@router.websocket("/ws/{user_token}")
async def websocket_endpoint(websocket: WebSocket, user_token: str):
    """WebSocket endpoint for real-time communication with ESP32"""
    await websocket.accept()
    
    try:
        # Verify token
        user_info = await verify_firebase_token(user_token)
        user_id = user_info['uid']
        
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "user_id": user_id,
            "message": "Connected successfully"
        }))
        
        while True:
            # Wait for messages from ESP32
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "story_status":
                # Handle story playback status from ESP32
                story_id = message.get("story_id")
                status = message.get("status")
                
                # Update story status
                await storage_service.update_story_status(story_id, status)
                
                # Send acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "status_received",
                    "story_id": story_id,
                    "status": status
                }))
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for user: {user_id}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close()
