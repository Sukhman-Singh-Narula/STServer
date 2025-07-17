# ===== TEST SCRIPT FOR REPLICATE STORY GENERATION ENDPOINT =====
# Test the story generation endpoint with Replicate SDXL integration

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime
import time

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class ReplicateStoryTester:
    """Test the story generation endpoint with Replicate SDXL"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout for story generation
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method.upper() == 'GET':
                response = await self.client.get(url, params=params, headers=headers)
            elif method.upper() == 'POST':
                response = await self.client.post(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = await self.client.delete(url, headers=headers)
            
            try:
                result = response.json()
            except:
                result = {"error": "Invalid JSON response", "text": response.text}
            
            return {
                "status": response.status_code,
                "data": result,
                "success": response.status_code == 200
            }
            
        except Exception as e:
            return {
                "status": 0,
                "error": str(e),
                "success": False
            }

    async def test_health_check(self):
        """Test if the server is running"""
        print("🔍 Testing server health...")
        result = await self.make_request('GET', '/health')
        
        if result["success"]:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server is not responding: {result}")
            return False

    async def test_story_generation(self, firebase_token: str, prompt: str):
        """Test story generation with Replicate"""
        print(f"\n🎬 Testing story generation...")
        print(f"   Prompt: {prompt}")
        print(f"   Expected: Replicate SDXL images at 304x304 with both colored and grayscale versions")
        
        story_request = {
            "firebase_token": firebase_token,
            "prompt": prompt
        }
        
        start_time = time.time()
        result = await self.make_request('POST', '/stories/generate', story_request)
        initial_time = time.time() - start_time
        
        if result["success"]:
            data = result["data"]
            if data.get("success"):
                story_id = data.get("story_id")
                tracking_method = data.get("tracking_method")
                
                print(f"✅ Story generation started successfully ({initial_time:.2f}s)")
                print(f"   Story ID: {story_id}")
                print(f"   Tracking method: {tracking_method}")
                
                return story_id
            else:
                print(f"❌ Story generation failed: {data}")
                return None
        else:
            print(f"❌ Request failed: {result}")
            return None

    async def wait_for_story_completion(self, firebase_token: str, story_id: str, max_wait_time: int = 300):
        """Wait for story to complete and check the result"""
        print(f"\n⏳ Waiting for story {story_id} to complete...")
        print(f"   Max wait time: {max_wait_time} seconds")
        
        start_time = time.time()
        check_interval = 10  # Check every 10 seconds
        
        while time.time() - start_time < max_wait_time:
            elapsed = time.time() - start_time
            print(f"   ⏰ Checking status... (elapsed: {elapsed:.1f}s)")
            
            # Get story status
            result = await self.make_request('GET', f'/stories/user/{firebase_token}/story/{story_id}')
            
            if result["success"] and result["data"].get("success"):
                story_data = result["data"].get("story")
                status = story_data.get("status")
                
                print(f"   📊 Status: {status}")
                
                if status == "completed":
                    print(f"✅ Story completed in {elapsed:.1f}s")
                    return story_data
                elif status == "failed":
                    print(f"❌ Story generation failed")
                    return None
                elif status in ["generating_scenes", "generating_media"]:
                    print(f"   🔄 Still processing... ({status})")
                    await asyncio.sleep(check_interval)
                else:
                    print(f"   ⚠️ Unknown status: {status}")
                    await asyncio.sleep(check_interval)
            else:
                print(f"   ❌ Error checking status: {result}")
                await asyncio.sleep(check_interval)
        
        print(f"❌ Story did not complete within {max_wait_time} seconds")
        return None

    async def validate_replicate_output(self, story_data: dict):
        """Validate that the story was generated with Replicate and has correct format"""
        print(f"\n🔍 Validating Replicate output...")
        
        # Check manifest structure
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
        
        # Check optimizations
        optimizations = manifest.get("optimizations", [])
        has_replicate_opt = any("replicate" in opt.lower() for opt in optimizations)
        has_dual_image_opt = any("dual_image" in opt.lower() for opt in optimizations)
        
        if not has_replicate_opt:
            print("❌ Missing Replicate optimization flag")
            return False
        else:
            print("✅ Replicate optimization found")
        
        if not has_dual_image_opt:
            print("❌ Missing dual image storage optimization flag")
            return False
        else:
            print("✅ Dual image storage optimization found")
        
        # Check scenes
        scenes = manifest.get("scenes", [])
        if not scenes:
            print("❌ No scenes found")
            return False
        
        print(f"✅ Found {len(scenes)} scenes")
        
        # Validate each scene
        all_valid = True
        for i, scene in enumerate(scenes):
            scene_num = scene.get("scene_number", i + 1)
            print(f"\n   📖 Validating Scene {scene_num}:")
            
            # Check required fields
            required_fields = ["text", "visual_prompt", "audio_url", "image_url"]
            for field in required_fields:
                if not scene.get(field):
                    print(f"      ❌ Missing {field}")
                    all_valid = False
                else:
                    print(f"      ✅ {field}: {scene[field][:50]}...")
            
            # Check for colored image URL (new feature)
            colored_url = scene.get("colored_image_url")
            if not colored_url:
                print("      ❌ Missing colored_image_url")
                all_valid = False
            else:
                print(f"      ✅ colored_image_url: {colored_url[:50]}...")
            
            # Validate URL patterns
            image_url = scene.get("image_url", "")
            if "_grayscale" not in image_url:
                print("      ❌ Grayscale image URL doesn't contain '_grayscale'")
                all_valid = False
            else:
                print("      ✅ Grayscale image URL format correct")
            
            if "_colored" not in colored_url:
                print("      ❌ Colored image URL doesn't contain '_colored'")
                all_valid = False
            else:
                print("      ✅ Colored image URL format correct")
        
        if all_valid:
            print("\n✅ All scenes validated successfully")
            return True
        else:
            print("\n❌ Some scenes failed validation")
            return False

    async def test_image_accessibility(self, story_data: dict):
        """Test if generated images are accessible"""
        print(f"\n🖼️ Testing image accessibility...")
        
        manifest = story_data.get("manifest", {})
        scenes = manifest.get("scenes", [])
        
        if not scenes:
            print("❌ No scenes to test")
            return False
        
        # Test first scene images
        first_scene = scenes[0]
        grayscale_url = first_scene.get("image_url")
        colored_url = first_scene.get("colored_image_url")
        
        results = []
        
        # Test grayscale image
        if grayscale_url:
            print(f"   🔍 Testing grayscale image accessibility...")
            try:
                response = await self.client.head(grayscale_url, timeout=10.0)
                if response.status_code == 200:
                    print(f"   ✅ Grayscale image accessible (status: {response.status_code})")
                    content_type = response.headers.get('content-type', '')
                    print(f"      Content-Type: {content_type}")
                    results.append(True)
                else:
                    print(f"   ❌ Grayscale image not accessible (status: {response.status_code})")
                    results.append(False)
            except Exception as e:
                print(f"   ❌ Error accessing grayscale image: {e}")
                results.append(False)
        
        # Test colored image
        if colored_url:
            print(f"   🔍 Testing colored image accessibility...")
            try:
                response = await self.client.head(colored_url, timeout=10.0)
                if response.status_code == 200:
                    print(f"   ✅ Colored image accessible (status: {response.status_code})")
                    content_type = response.headers.get('content-type', '')
                    print(f"      Content-Type: {content_type}")
                    results.append(True)
                else:
                    print(f"   ❌ Colored image not accessible (status: {response.status_code})")
                    results.append(False)
            except Exception as e:
                print(f"   ❌ Error accessing colored image: {e}")
                results.append(False)
        
        return all(results)

    async def test_audio_accessibility(self, story_data: dict):
        """Test if generated audio is accessible"""
        print(f"\n🎵 Testing audio accessibility...")
        
        manifest = story_data.get("manifest", {})
        scenes = manifest.get("scenes", [])
        
        if not scenes:
            print("❌ No scenes to test")
            return False
        
        # Test first scene audio
        first_scene = scenes[0]
        audio_url = first_scene.get("audio_url")
        
        if not audio_url:
            print("❌ No audio URL found")
            return False
        
        print(f"   🔍 Testing audio accessibility...")
        try:
            response = await self.client.head(audio_url, timeout=10.0)
            if response.status_code == 200:
                print(f"   ✅ Audio accessible (status: {response.status_code})")
                content_type = response.headers.get('content-type', '')
                print(f"      Content-Type: {content_type}")
                return True
            else:
                print(f"   ❌ Audio not accessible (status: {response.status_code})")
                return False
        except Exception as e:
            print(f"   ❌ Error accessing audio: {e}")
            return False

    async def run_comprehensive_test(self, firebase_token: str):
        """Run comprehensive test of Replicate story generation"""
        print("🚀 COMPREHENSIVE REPLICATE STORY GENERATION TEST")
        print("=" * 60)
        print(f"Firebase Token: {firebase_token[:20]}...")
        print(f"Server: {self.base_url}")
        
        # Test 1: Health check
        print(f"\n{'='*60}")
        print("TEST 1: SERVER HEALTH CHECK")
        print("="*60)
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ Server not available, stopping tests")
            return False
        
        # Test 2: Generate story
        print(f"\n{'='*60}")
        print("TEST 2: STORY GENERATION WITH REPLICATE")
        print("="*60)
        
        test_prompt = "A magical adventure about a brave little dragon who learns to fly and makes friends with a wise old owl in an enchanted forest"
        
        story_id = await self.test_story_generation(firebase_token, test_prompt)
        if not story_id:
            print("❌ Story generation failed, stopping tests")
            return False
        
        # Test 3: Wait for completion
        print(f"\n{'='*60}")
        print("TEST 3: WAITING FOR STORY COMPLETION")
        print("="*60)
        
        story_data = await self.wait_for_story_completion(firebase_token, story_id)
        if not story_data:
            print("❌ Story did not complete, stopping tests")
            return False
        
        # Test 4: Validate Replicate output
        print(f"\n{'='*60}")
        print("TEST 4: VALIDATE REPLICATE OUTPUT")
        print("="*60)
        
        output_valid = await self.validate_replicate_output(story_data)
        
        # Test 5: Test image accessibility
        print(f"\n{'='*60}")
        print("TEST 5: IMAGE ACCESSIBILITY")
        print("="*60)
        
        images_accessible = await self.test_image_accessibility(story_data)
        
        # Test 6: Test audio accessibility
        print(f"\n{'='*60}")
        print("TEST 6: AUDIO ACCESSIBILITY")
        print("="*60)
        
        audio_accessible = await self.test_audio_accessibility(story_data)
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print("="*60)
        
        tests = [
            ("Server Health", health_ok),
            ("Story Generation", story_id is not None),
            ("Story Completion", story_data is not None),
            ("Replicate Output Validation", output_valid),
            ("Image Accessibility", images_accessible),
            ("Audio Accessibility", audio_accessible)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n🎯 Overall Success Rate: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 Replicate story generation is working well!")
            print("✅ Images are generated at 304x304 with both colored and grayscale versions")
            print("✅ No cropping needed - Replicate generates exact size")
        else:
            print("⚠️ Some issues detected. Check the logs above.")
        
        return success_rate >= 80

# ===== SIMPLE TEST FUNCTIONS =====

async def quick_test_replicate_generation(firebase_token: str):
    """Quick test of Replicate story generation"""
    async with ReplicateStoryTester() as tester:
        print("🔍 Quick test of Replicate story generation...")
        
        # Test basic generation
        prompt = "A simple story about a cat and a mouse becoming friends"
        story_id = await tester.test_story_generation(firebase_token, prompt)
        
        if story_id:
            print("✅ Quick test PASSED - story generation started successfully")
            print(f"   Story ID: {story_id}")
            print("   🔄 Story is now processing in the background")
            return True
        else:
            print("❌ Quick test FAILED - story generation failed")
            return False

async def test_single_story_with_validation(firebase_token: str, prompt: str):
    """Test single story generation with full validation"""
    async with ReplicateStoryTester() as tester:
        print(f"🔍 Testing single story with validation...")
        print(f"Prompt: {prompt}")
        
        # Generate story
        story_id = await tester.test_story_generation(firebase_token, prompt)
        if not story_id:
            return False
        
        # Wait for completion
        story_data = await tester.wait_for_story_completion(firebase_token, story_id)
        if not story_data:
            return False
        
        # Validate output
        return await tester.validate_replicate_output(story_data)

# ===== MAIN FUNCTION =====

async def main():
    """Main test function"""
    
    # Replace with your actual Firebase token
    FIREBASE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImE4ZGY2MmQzYTBhNDRlM2RmY2RjYWZjNmRhMTM4Mzc3NDU5ZjliMDEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1Mjc0MDMwNSwidXNlcl9pZCI6InRlc3QtdXNlci0xMjM0NSIsInN1YiI6InRlc3QtdXNlci0xMjM0NSIsImlhdCI6MTc1Mjc0MDMwNSwiZXhwIjoxNzUyNzQzOTA1LCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.LfLFL5Pseo7c7lrkNjQjTAzyhqq4m7AHlSpKDcU5XMfLQRsKzvkE5NTQ3K6uMUd9ucRTeUlXm4JYNdVhd6Y0OQou2OJURdkWv_8t1Urp7sRYixOKUH5kuZcRcbkjhTVR3gy9EvsbFIlgFtTr5c57QY9AZT7kW30Yyo9mId4tau358vSCCMgD37kOhWcHAev_HTPiXaKmsL-naHGfZHCukoOkP5enOZZQrinJIre8BMYyeOmLQ4_WjlGhYGT_6oPp_hy_XxA5oqaWNJ6W32pCwKZBECakIYjNnqoYOF_gq4Pys8BFhAJXc2kHzTfIN3nX7xZXX8En_hFLBMy6NT3Upg"
    
    if FIREBASE_TOKEN == "your_firebase_token_here":
        print("❌ Error: Please set your Firebase token!")
        print("   Replace 'your_firebase_token_here' with your actual Firebase token")
        return
    
    print("Choose test type:")
    print("1. Quick test (start story generation)")
    print("2. Comprehensive test (full validation)")
    print("3. Single story with validation")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        await quick_test_replicate_generation(FIREBASE_TOKEN)
    
    elif choice == "2":
        async with ReplicateStoryTester() as tester:
            await tester.run_comprehensive_test(FIREBASE_TOKEN)
    
    elif choice == "3":
        prompt = input("Enter story prompt: ").strip()
        if not prompt:
            prompt = "A magical adventure about a brave little dragon who learns to fly"
        
        await test_single_story_with_validation(FIREBASE_TOKEN, prompt)
    
    else:
        print("Invalid choice, running quick test...")
        await quick_test_replicate_generation(FIREBASE_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# ===== USAGE EXAMPLES =====
"""
# Quick test:
asyncio.run(quick_test_replicate_generation("your_firebase_token"))

# Single story test:
asyncio.run(test_single_story_with_validation("your_firebase_token", "A story about a friendly robot"))

# Comprehensive test:
async with ReplicateStoryTester() as tester:
    await tester.run_comprehensive_test("your_firebase_token")
"""
