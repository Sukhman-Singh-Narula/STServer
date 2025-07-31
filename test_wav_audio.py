#!/usr/bin/env python3

"""
Simple test to verify WAV audio format is working
"""

import requests
import json
import time

def test_wav_audio():
    url = "http://localhost:8000/stories/generate"
    
    payload = {
        "prompt": "A simple test story with WAV audio format",
        "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijk1MWRkZTkzMmViYWNkODhhZmIwMDM3YmZlZDhmNjJiMDdmMDg2NmIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1Mzk0NDUyMSwidXNlcl9pZCI6InRlc3QtdXNlci0xMjM0NSIsInN1YiI6InRlc3QtdXNlci0xMjM0NSIsImlhdCI6MTc1Mzk0NDUyMSwiZXhwIjoxNzUzOTQ4MTIxLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.PoxRLuwFggYvK04gx27Ulz1E0dtFmNnLX-fKZ963TpJpho-XB69GlkSR0VT2cYf6d-v6vWYbHwLomql2QjnESu4Gxqu98E6-8VtHc-9_Ib8gtGCXS3v59KdZMzwuduWDF1RjJb_1Lqaw7CSt05WwW6bALxcfk0sHhWEYfRaOduEyrMqKBnxheZS8eSfBbHbYe6MW3tWFjFQbni2LdrScWzQtOCKT9h7bRhs1NxsiWqw6CksCtEDgV_0HKrKJRd2eauRnReIUqJ3dKv95gfWf6iW-GyRWRaFPmgtx2LuCVJ3n-9TbMp4ZaGEkALidKCKZU-WfwiS3WmwmQts3NTtQNQ"
    }
    
    print("🎵 Testing WAV audio format...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            story_id = result.get("story_id")
            print(f"✅ Story created: {story_id}")
            
            # Monitor for completion
            for i in range(10):  # Check for 2.5 minutes
                time.sleep(15)
                
                status_response = requests.get(f"http://localhost:8000/stories/fetch/{story_id}")
                if status_response.status_code == 200:
                    story_data = status_response.json()
                    status = story_data.get("status", "unknown")
                    print(f"   [{i*15}s] Status: {status}")
                    
                    if status == "completed":
                        print("🎉 Story completed!")
                        
                        # Check if audio URLs have .wav extension
                        scenes = story_data.get("scenes", [])
                        wav_count = 0
                        total_audio = 0
                        
                        for scene in scenes:
                            audio_url = scene.get("audio_url", "")
                            if audio_url:
                                total_audio += 1
                                if audio_url.endswith(".wav"):
                                    wav_count += 1
                                    print(f"   ✅ Scene {scene.get('scene_number', '?')}: WAV audio detected")
                                else:
                                    print(f"   ❌ Scene {scene.get('scene_number', '?')}: Non-WAV audio: {audio_url}")
                        
                        print(f"\n📊 WAV Audio Results:")
                        print(f"   Total audio files: {total_audio}")
                        print(f"   WAV files: {wav_count}")
                        print(f"   Success rate: {(wav_count/total_audio)*100:.1f}%" if total_audio > 0 else "No audio files")
                        
                        if wav_count == total_audio and total_audio > 0:
                            print("🎉 WAV format change SUCCESSFUL!")
                            return True
                        else:
                            print("❌ WAV format change FAILED!")
                            return False
                    
                    elif status == "failed":
                        print(f"❌ Story failed: {story_data.get('error', 'Unknown error')}")
                        return False
                
            print("⏰ Timeout waiting for completion")
            return False
            
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_wav_audio()
    
    if success:
        print("\n✅ WAV audio format is working correctly!")
    else:
        print("\n❌ WAV audio format test failed!")
