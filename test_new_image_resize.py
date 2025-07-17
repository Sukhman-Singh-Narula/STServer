#!/usr/bin/env python3
"""
Quick test for the new image generation functionality
"""

import asyncio
import time
import httpx
import json

async def test_story_generation():
    """Test story generation with new image resize functionality"""
    try:
        # Read Firebase token
        with open('firebase_id_token.txt', 'r') as f:
            firebase_token = f.read().strip()
        
        # Story generation request
        story_request = {
            "firebase_token": firebase_token,
            "prompt": "A simple story about a robot learning to paint beautiful pictures"
        }
        
        print("🤖 Testing story generation with new 1024x1024 → 304x304 image resize...")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Start story generation
            print("📝 Starting story generation...")
            response = await client.post(
                "http://localhost:8000/stories/generate",
                json=story_request
            )
            
            if response.status_code == 200:
                result = response.json()
                story_id = result["story_id"]
                print(f"✅ Story generation started: {story_id}")
                
                # Wait and check story status
                print("⏳ Waiting for story completion...")
                await asyncio.sleep(45)  # Wait for story to complete
                
                # Get story details
                story_response = await client.get(f"http://localhost:8000/stories/{story_id}")
                
                if story_response.status_code == 200:
                    story_data = story_response.json()
                    print(f"📖 Story Title: {story_data['title']}")
                    print(f"📊 Status: {story_data['status']}")
                    print(f"📊 Total Scenes: {story_data['total_scenes']}")
                    
                    # Check if images were generated
                    scenes = story_data.get('scenes', [])
                    if scenes:
                        print(f"🖼️ Checking image generation for {len(scenes)} scenes...")
                        for i, scene in enumerate(scenes):
                            if scene.get('image_url'):
                                print(f"✅ Scene {i+1} has colored image: {scene['image_url'][:80]}...")
                            if scene.get('grayscale_image_url'):
                                print(f"✅ Scene {i+1} has grayscale image: {scene['grayscale_image_url'][:80]}...")
                    
                    return True
                else:
                    print(f"❌ Failed to get story details: {story_response.status_code}")
                    return False
                    
            else:
                print(f"❌ Story generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_story_generation())
