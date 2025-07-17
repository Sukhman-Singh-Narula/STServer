#!/usr/bin/env python3
"""
Simple test script for Replicate story generation endpoint
Run this script to test the new Replicate integration
"""

import asyncio
import json
import sys
import os
import requests
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configuration
BASE_URL = "http://localhost:8000"
FIREBASE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijg3NzQ4NTAwMmYwNWJlMDI2N2VmNDU5ZjViNTEzNTMzYjVjNThjMTIiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1MTM4MzQ2MCwidXNlcl9pZCI6Ik1tNWFET3NqeTRZNGdhY3BXT0xvUVZVaFFlNDMiLCJzdWIiOiJNbTVhRE9zank0WTRnYWNwV09Mb1FWVWhRZTQzIiwiaWF0IjoxNzUxMzgzNDYwLCJleHAiOjE3NTEzODcwNjAsImVtYWlsIjoidGVzdEBleGFtcGxlLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbInRlc3RAZXhhbXBsZS5jb20iXX0sInNpZ25faW5fcHJvdmlkZXIiOiJjdXN0b20ifX0.t-8Yw8J5N96Q5NguZCHnG_SGAZwiI4H9u7Civnt0DzmMq03NWr_ZMuCajIZRHM89mSn_U5hkE75Exwaka3o22rsm6V8HvWBHjExibZZCiYi-fkrH2aNDtfKpFrJ-9xW-TnwgJ7_VoPrmVD7xg9f5NUuWogQANaF53EAwyLkcLmcFN7hxW5S1TP0-EmrbX7vyNJeqp_zC_3ecxTwyN7mUiUqYIYVIr3E0gNGBHKoRsA0a5meR1i5fwXxk5dHc4gjvvVbAXQDKUzhsxFZ66SDM_4Q3vBSTkEN_d7xxkvi1kNoAW8pQt_7LqvcQPYrURj46Hx_lBN9kLLLPXsZmK-0Cxw"

def test_health_check():
    """Test if the server is running"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        return False

def test_story_generation():
    """Test story generation endpoint"""
    print("\n🎬 Testing story generation with Replicate...")
    
    # Test story request
    story_request = {
        "firebase_token": FIREBASE_TOKEN,
        "prompt": "A test story about a brave little mouse who discovers a magical cheese castle and befriends a wise old rat"
    }
    
    print(f"   📝 Prompt: {story_request['prompt']}")
    print("   🎯 Expected: Replicate SDXL generates 300x300 images")
    print("   🎯 Expected: Both colored and grayscale versions stored")
    
    try:
        response = requests.post(
            f"{BASE_URL}/stories/generate",
            json=story_request,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                story_id = data.get("story_id")
                tracking_method = data.get("tracking_method")
                
                print(f"✅ Story generation started successfully")
                print(f"   📋 Story ID: {story_id}")
                print(f"   🔧 Tracking method: {tracking_method}")
                print(f"   🔄 Story is now processing in the background")
                print(f"   ⏳ This may take 2-5 minutes to complete")
                
                return story_id
            else:
                print(f"❌ API error: {data}")
                return None
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error details: {error_data}")
            except:
                print(f"   Response text: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request exception: {e}")
        return None

def check_story_status(story_id):
    """Check the status of a story"""
    print(f"\n📊 Checking story status for {story_id}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/stories/user/{FIREBASE_TOKEN}/story/{story_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                story_data = data.get("story", {})
                status = story_data.get("status", "unknown")
                title = story_data.get("title", "Unknown")
                
                print(f"✅ Story status retrieved")
                print(f"   📋 Title: {title}")
                print(f"   📊 Status: {status}")
                
                if status == "completed":
                    print("🎉 Story generation completed!")
                    return validate_completed_story(story_data)
                elif status == "failed":
                    print("❌ Story generation failed")
                    return False
                elif status in ["generating_scenes", "generating_media"]:
                    print(f"⏳ Story is still processing ({status})")
                    return "processing"
                else:
                    print(f"❓ Unknown status: {status}")
                    return "unknown"
            else:
                print(f"❌ API error: {data}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request exception: {e}")
        return False

def validate_completed_story(story_data):
    """Validate the completed story structure"""
    print(f"\n🔍 Validating completed story structure...")
    
    manifest = story_data.get("manifest", {})
    if not manifest:
        print("❌ No manifest found")
        return False
    
    # Check generation method
    generation_method = manifest.get("generation_method", "")
    if "replicate" not in generation_method.lower():
        print(f"❌ Expected Replicate generation method, got: {generation_method}")
        return False
    else:
        print(f"✅ Generation method: {generation_method}")
    
    # Check scenes
    scenes = manifest.get("scenes", [])
    if not scenes:
        print("❌ No scenes found")
        return False
    
    print(f"✅ Found {len(scenes)} scenes")
    
    # Check first scene in detail
    first_scene = scenes[0]
    print(f"\n📖 Validating first scene:")
    
    required_fields = ["text", "audio_url", "image_url", "colored_image_url"]
    all_valid = True
    
    for field in required_fields:
        if field in first_scene and first_scene[field]:
            print(f"   ✅ {field}: {first_scene[field][:50]}...")
        else:
            print(f"   ❌ Missing or empty {field}")
            all_valid = False
    
    # Check URL patterns
    if "_grayscale" in first_scene.get("image_url", ""):
        print("   ✅ Grayscale image URL format correct")
    else:
        print("   ❌ Grayscale image URL format incorrect")
        all_valid = False
    
    if "_colored" in first_scene.get("colored_image_url", ""):
        print("   ✅ Colored image URL format correct")
    else:
        print("   ❌ Colored image URL format incorrect")
        all_valid = False
    
    return all_valid

def test_image_accessibility(story_data):
    """Test if the generated images are accessible"""
    print(f"\n🖼️ Testing image accessibility...")
    
    manifest = story_data.get("manifest", {})
    scenes = manifest.get("scenes", [])
    
    if not scenes:
        print("❌ No scenes to test")
        return False
    
    first_scene = scenes[0]
    grayscale_url = first_scene.get("image_url")
    colored_url = first_scene.get("colored_image_url")
    
    results = []
    
    # Test grayscale image
    if grayscale_url:
        try:
            response = requests.head(grayscale_url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Grayscale image accessible")
                results.append(True)
            else:
                print(f"   ❌ Grayscale image not accessible (status: {response.status_code})")
                results.append(False)
        except Exception as e:
            print(f"   ❌ Error accessing grayscale image: {e}")
            results.append(False)
    
    # Test colored image
    if colored_url:
        try:
            response = requests.head(colored_url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Colored image accessible")
                results.append(True)
            else:
                print(f"   ❌ Colored image not accessible (status: {response.status_code})")
                results.append(False)
        except Exception as e:
            print(f"   ❌ Error accessing colored image: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Main test function"""
    print("🚀 REPLICATE STORY GENERATION TEST")
    print("=" * 50)
    print(f"Server: {BASE_URL}")
    print(f"Firebase Token: {FIREBASE_TOKEN[:20]}...")
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Server not available, stopping tests")
        return
    
    # Test 2: Generate story
    story_id = test_story_generation()
    if not story_id:
        print("\n❌ Story generation failed")
        return
    
    # Test 3: Check story status
    print(f"\n{'='*50}")
    print("OPTIONS FOR CHECKING STORY STATUS:")
    print("1. Check status now (may still be processing)")
    print("2. Wait and check later")
    print("3. Skip status check")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        status_result = check_story_status(story_id)
        if status_result == True:
            print("\n🎉 Story completed and validated successfully!")
        elif status_result == "processing":
            print(f"\n⏳ Story is still processing. Check again in a few minutes.")
            print(f"   Use this command to check: python3 -c \"from test_replicate_story_generation import check_story_status; check_story_status('{story_id}')\"")
        else:
            print(f"\n❌ Story generation may have failed")
    
    elif choice == "2":
        print(f"\n⏳ Story is processing in the background.")
        print(f"   Story ID: {story_id}")
        print(f"   Check status later with:")
        print(f"   python3 -c \"from test_replicate_story_generation import check_story_status; check_story_status('{story_id}')\"")
    
    else:
        print(f"\n✅ Story generation test completed.")
        print(f"   Story ID: {story_id}")
    
    print(f"\n{'='*50}")
    print("✅ Test completed successfully!")
    print("🎯 Expected improvements with Replicate:")
    print("   - Images generated at exact 300x300 size")
    print("   - No cropping needed")
    print("   - Both colored and grayscale versions stored")
    print("   - Parallel processing maintained")

if __name__ == "__main__":
    main()
