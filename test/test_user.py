# ===== TEST SCRIPT FOR STORY ID ARRAY FUNCTIONALITY =====
# Save as test/test_story_id_arrays.py

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class StoryIDArrayTester:
    """Test the complete story ID array functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
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

    async def test_get_story_ids_array(self, firebase_token: str):
        """Test getting the story IDs array"""
        print(f"\n📋 Testing get story IDs array...")
        
        result = await self.make_request('GET', f'/stories/user/{firebase_token}/story-ids')
        
        if result["success"]:
            data = result["data"]
            if data.get("success"):
                story_ids = data.get("story_ids", [])
                newest_first = data.get("newest_first", [])
                
                print(f"✅ Story IDs array retrieved successfully")
                print(f"   Total stories: {data.get('total_count', 0)}")
                print(f"   Story IDs (oldest first): {story_ids}")
                print(f"   Story IDs (newest first): {newest_first}")
                print(f"   Has stories: {data.get('summary', {}).get('has_stories', False)}")
                print(f"   Latest story ID: {data.get('summary', {}).get('latest_story_id', 'None')}")
                
                return data
            else:
                print(f"❌ API error: {data}")
                return None
        else:
            print(f"❌ Request failed: {result}")
            return None

    async def test_get_user_stories_with_arrays(self, firebase_token: str, limit: int = 10):
        """Test getting user stories using the ID array method"""
        print(f"\n📚 Testing get user stories with ID arrays (limit: {limit})...")
        
        result = await self.make_request('GET', f'/stories/user/{firebase_token}', params={"limit": limit})
        
        if result["success"]:
            data = result["data"]
            if data.get("success"):
                stories = data.get("stories", [])
                pagination = data.get("pagination", {})
                user_info = data.get("user_info", {})
                tracking_info = data.get("tracking_info", {})
                
                print(f"✅ User stories retrieved using ID array method")
                print(f"   Method used: {data.get('summary', {}).get('method_used', 'unknown')}")
                print(f"   Uses story ID array: {tracking_info.get('uses_story_id_array', False)}")
                print(f"   Story IDs array length: {tracking_info.get('story_ids_array_length', 0)}")
                print(f"   Total stories: {pagination.get('total_count', 0)}")
                print(f"   Returned this page: {len(stories)}")
                print(f"   Batch fetched: {tracking_info.get('batch_fetched', False)}")
                
                # Show user info
                if user_info:
                    print(f"   Child: {user_info.get('child_name', 'Unknown')} (age {user_info.get('child_age', '?')})")
                    print(f"   Story statistics: {user_info.get('story_statistics', {})}")
                
                # Show first few stories
                print(f"\n📖 Stories preview:")
                for i, story in enumerate(stories[:3]):
                    print(f"   {i+1}. {story.get('title', 'Untitled')} ({story.get('story_id')})")
                    print(f"      Status: {story.get('status')} | Scenes: {story.get('total_scenes')} | {story.get('days_ago')} days ago")
                    print(f"      Position in collection: {story.get('position_in_user_stories', '?')}/{story.get('total_user_stories', '?')}")
                
                return data
            else:
                print(f"❌ API error: {data}")
                return None
        else:
            print(f"❌ Request failed: {result}")
            return None

    async def test_pagination_with_arrays(self, firebase_token: str):
        """Test pagination using story ID arrays"""
        print(f"\n📄 Testing pagination with story ID arrays...")
        
        # Test different pages
        pages_to_test = [
            {"limit": 3, "offset": 0, "name": "Page 1"},
            {"limit": 3, "offset": 3, "name": "Page 2"},
            {"limit": 2, "offset": 1, "name": "Custom pagination"}
        ]
        
        for page_test in pages_to_test:
            print(f"\n   Testing {page_test['name']} (limit: {page_test['limit']}, offset: {page_test['offset']})")
            
            params = {"limit": page_test["limit"], "offset": page_test["offset"]}
            result = await self.make_request('GET', f'/stories/user/{firebase_token}', params=params)
            
            if result["success"] and result["data"].get("success"):
                data = result["data"]
                stories = data.get("stories", [])
                pagination = data.get("pagination", {})
                
                print(f"      ✅ Found {len(stories)} stories")
                print(f"      Total available: {pagination.get('total_count', 0)}")
                print(f"      Current page: {pagination.get('current_page', '?')}")
                print(f"      Has more: {pagination.get('has_more', False)}")
                
                # Show story IDs for this page
                story_ids_this_page = [s.get('story_id') for s in stories]
                print(f"      Story IDs this page: {story_ids_this_page}")
            else:
                print(f"      ❌ Failed: {result}")

    async def test_generate_and_track_story(self, firebase_token: str):
        """Test generating a story and verify it's added to the ID array"""
        print(f"\n🎬 Testing story generation with ID array tracking...")
        
        # Get current story IDs before generation
        print("   📋 Getting current story IDs...")
        before_result = await self.test_get_story_ids_array(firebase_token)
        story_ids_before = before_result.get("story_ids", []) if before_result else []
        count_before = len(story_ids_before)
        
        # Generate a test story
        print("   🚀 Generating test story...")
        story_request = {
            "firebase_token": firebase_token,
            "prompt": "A test story about array tracking for a brave little mouse"
        }
        
        result = await self.make_request('POST', '/stories/generate', story_request)
        
        if result["success"] and result["data"].get("success"):
            story_id = result["data"].get("story_id")
            tracking_method = result["data"].get("tracking_method")
            
            print(f"   ✅ Story generation started: {story_id}")
            print(f"   📋 Tracking method: {tracking_method}")
            
            # Wait a moment then check if ID was added to array
            print("   ⏰ Waiting 3 seconds then checking story IDs array...")
            await asyncio.sleep(3)
            
            # Get story IDs after generation
            after_result = await self.test_get_story_ids_array(firebase_token)
            story_ids_after = after_result.get("story_ids", []) if after_result else []
            count_after = len(story_ids_after)
            
            print(f"   📊 Story count: {count_before} → {count_after}")
            
            if count_after > count_before:
                print(f"   ✅ Story ID added to array successfully!")
                if story_id in story_ids_after:
                    print(f"   ✅ Confirmed: {story_id} is in the story_ids array")
                    position = story_ids_after.index(story_id) + 1
                    print(f"   📍 Position in array: {position}/{count_after}")
                else:
                    print(f"   ⚠️ Story ID not found in array (may still be processing)")
            else:
                print(f"   ⚠️ Story count didn't increase (may still be processing)")
            
            return story_id
        else:
            print(f"   ❌ Story generation failed: {result}")
            return None

    async def test_delete_and_array_update(self, firebase_token: str, story_id: str):
        """Test deleting a story and verify it's removed from the ID array"""
        print(f"\n🗑️ Testing story deletion with ID array update...")
        
        # Get current story IDs before deletion
        print("   📋 Getting current story IDs...")
        before_result = await self.test_get_story_ids_array(firebase_token)
        story_ids_before = before_result.get("story_ids", []) if before_result else []
        count_before = len(story_ids_before)
        
        if story_id not in story_ids_before:
            print(f"   ⚠️ Story {story_id} not found in current array")
            return False
        
        print(f"   📍 Story {story_id} found at position {story_ids_before.index(story_id) + 1}/{count_before}")
        
        # Delete the story
        print("   🗑️ Deleting story...")
        result = await self.make_request('DELETE', f'/stories/user/{firebase_token}/story/{story_id}')
        
        if result["success"] and result["data"].get("success"):
            tracking_info = result["data"].get("tracking_info", {})
            
            print(f"   ✅ Story deleted successfully")
            print(f"   📋 Removed from array: {tracking_info.get('removed_from_story_ids_array', False)}")
            print(f"   📊 Count decremented: {tracking_info.get('story_count_decremented', False)}")
            
            # Verify removal from array
            print("   🔍 Verifying removal from story IDs array...")
            after_result = await self.test_get_story_ids_array(firebase_token)
            story_ids_after = after_result.get("story_ids", []) if after_result else []
            count_after = len(story_ids_after)
            
            print(f"   📊 Story count: {count_before} → {count_after}")
            
            if story_id not in story_ids_after:
                print(f"   ✅ Confirmed: {story_id} removed from story_ids array")
            else:
                print(f"   ❌ Error: {story_id} still in story_ids array")
            
            if count_after == count_before - 1:
                print(f"   ✅ Story count correctly decremented")
            else:
                print(f"   ❌ Story count not decremented correctly")
            
            return True
        else:
            print(f"   ❌ Story deletion failed: {result}")
            return False

    async def test_performance_comparison(self, firebase_token: str):
        """Test performance of different methods"""
        print(f"\n⚡ Testing performance comparison...")
        
        methods_to_test = [
            {"endpoint": "/stories/user/{token}", "name": "ID Array Method"},
            {"endpoint": "/stories/user/{token}/summary", "name": "Summary Method"}
        ]
        
        for method in methods_to_test:
            print(f"\n   🔬 Testing {method['name']}...")
            start_time = datetime.now()
            
            endpoint = method["endpoint"].format(token=firebase_token)
            result = await self.make_request('GET', endpoint)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if result["success"]:
                data = result["data"]
                if data.get("success"):
                    stories_count = len(data.get("stories", []))
                    total_count = data.get("total_stories") or data.get("pagination", {}).get("total_count", 0)
                    
                    print(f"      ✅ Success in {duration:.3f}s")
                    print(f"      📊 Stories returned: {stories_count}")
                    print(f"      📊 Total stories: {total_count}")
                    
                    # Show method-specific info
                    if "tracking_info" in data:
                        tracking = data["tracking_info"]
                        print(f"      🔧 Uses story ID array: {tracking.get('uses_story_id_array', False)}")
                        print(f"      🔧 Batch fetched: {tracking.get('batch_fetched', False)}")
                else:
                    print(f"      ❌ API error: {data}")
            else:
                print(f"      ❌ Request failed in {duration:.3f}s: {result}")

    async def run_comprehensive_test(self, firebase_token: str):
        """Run all story ID array tests"""
        print("🚀 COMPREHENSIVE STORY ID ARRAY FUNCTIONALITY TEST")
        print("=" * 60)
        print(f"Firebase Token: {firebase_token[:20]}...")
        print(f"Server: {self.base_url}")
        
        test_results = {}
        
        # Test 1: Get story IDs array
        print(f"\n{'='*60}")
        print("TEST 1: GET STORY IDS ARRAY")
        print("="*60)
        test_results["story_ids_array"] = await self.test_get_story_ids_array(firebase_token)
        
        # Test 2: Get user stories with ID arrays
        print(f"\n{'='*60}")
        print("TEST 2: GET USER STORIES WITH ID ARRAYS")
        print("="*60)
        test_results["user_stories"] = await self.test_get_user_stories_with_arrays(firebase_token, limit=5)
        
        # Test 3: Pagination
        print(f"\n{'='*60}")
        print("TEST 3: PAGINATION WITH ID ARRAYS")
        print("="*60)
        await self.test_pagination_with_arrays(firebase_token)
        
        # Test 4: Performance comparison
        print(f"\n{'='*60}")
        print("TEST 4: PERFORMANCE COMPARISON")
        print("="*60)
        await self.test_performance_comparison(firebase_token)
        
        # Test 5: Generate story and track in array
        print(f"\n{'='*60}")
        print("TEST 5: GENERATE STORY AND TRACK IN ARRAY")
        print("="*60)
        new_story_id = await self.test_generate_and_track_story(firebase_token)
        
        # Test 6: Delete story and update array (only if story was generated)
        if new_story_id:
            print(f"\n{'='*60}")
            print("TEST 6: DELETE STORY AND UPDATE ARRAY")
            print("="*60)
            delete_success = await self.test_delete_and_array_update(firebase_token, new_story_id)
            test_results["delete_story"] = delete_success
        
        # Final summary
        print(f"\n{'='*60}")
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for test_name, result in test_results.items():
            total_tests += 1
            if result:
                passed_tests += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎯 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 Story ID array functionality is working well!")
        else:
            print("⚠️ Some issues detected. Check the logs above.")
        
        return test_results

# ===== SIMPLE TEST FUNCTIONS =====

async def quick_test_story_arrays(firebase_token: str):
    """Quick test of story ID array functionality"""
    async with StoryIDArrayTester() as tester:
        print("🔍 Quick test of story ID array functionality...")
        
        # Test basic functionality
        ids_result = await tester.test_get_story_ids_array(firebase_token)
        stories_result = await tester.test_get_user_stories_with_arrays(firebase_token, limit=5)
        
        if ids_result and stories_result:
            print("✅ Quick test PASSED - story ID arrays are working")
            return True
        else:
            print("❌ Quick test FAILED")
            return False

async def test_specific_functionality(firebase_token: str, test_type: str):
    """Test specific functionality"""
    async with StoryIDArrayTester() as tester:
        if test_type == "ids":
            return await tester.test_get_story_ids_array(firebase_token)
        elif test_type == "stories":
            return await tester.test_get_user_stories_with_arrays(firebase_token)
        elif test_type == "pagination":
            return await tester.test_pagination_with_arrays(firebase_token)
        elif test_type == "performance":
            return await tester.test_performance_comparison(firebase_token)
        else:
            print(f"Unknown test type: {test_type}")
            return None

# ===== MAIN FUNCTION =====

async def main():
    """Main test function"""
    
    # Replace with your actual Firebase token
    FIREBASE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjZkZTQwZjA0ODgxYzZhMDE2MTFlYjI4NGE0Yzk1YTI1MWU5MTEyNTAiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1Mzg2NjA4NywidXNlcl9pZCI6InRlc3QtdXNlci0xMjM0NSIsInN1YiI6InRlc3QtdXNlci0xMjM0NSIsImlhdCI6MTc1Mzg2NjA4NywiZXhwIjoxNzUzODY5Njg3LCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.aOiih5-2_73dPxXHcchSjayJOq8aa-KAVFEEuW6DI-x9pKPMGetHusf7HIAnCdm83GGv01PUgU9duqulKr0b81_0Qbr5awLSg6T61DPxM5_4NfvlCYGsjhRpiZIN11WS0CzT7v0lSurbTi-EJ7lG0xND_cTcWnSowYERMD4P7AOd1sL5_cU_lSdvDwNff9yl_uoLBnwCZufY_OggB-xJcYWYsW13SJ2fxLnc3hzmqav9VzQkPfwX-47QKqa21ibfpnOCuqisr4HDJhYCyaPxJtoQrFneKPu632LBLQ4F5NDgeXBQt9SbsWTHWKIOUDaczxmaxtg08DJtTsPhnVzevA"
    
    if FIREBASE_TOKEN == "your_firebase_token_here":
        print("❌ Error: Please set your Firebase token!")
        print("   Replace 'your_firebase_token_here' with your actual Firebase token")
        return
    
    print("Choose test type:")
    print("1. Quick test (basic functionality)")
    print("2. Comprehensive test (all functionality)")
    print("3. Test specific feature")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        await quick_test_story_arrays(FIREBASE_TOKEN)
    
    elif choice == "2":
        async with StoryIDArrayTester() as tester:
            await tester.run_comprehensive_test(FIREBASE_TOKEN)
    
    elif choice == "3":
        print("\nSpecific tests:")
        print("a. Story IDs array")
        print("b. User stories with arrays") 
        print("c. Pagination")
        print("d. Performance comparison")
        
        specific_choice = input("Enter choice (a-d): ").strip().lower()
        
        test_map = {
            "a": "ids",
            "b": "stories", 
            "c": "pagination",
            "d": "performance"
        }
        
        if specific_choice in test_map:
            await test_specific_functionality(FIREBASE_TOKEN, test_map[specific_choice])
        else:
            print("Invalid choice")
    
    else:
        print("Invalid choice, running quick test...")
        await quick_test_story_arrays(FIREBASE_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# ===== USAGE EXAMPLES =====
"""
# Quick test:
asyncio.run(quick_test_story_arrays("your_firebase_token"))

# Test specific functionality:
asyncio.run(test_specific_functionality("your_firebase_token", "ids"))
asyncio.run(test_specific_functionality("your_firebase_token", "stories"))

# Comprehensive test:
async with StoryIDArrayTester() as tester:
    await tester.run_comprehensive_test("your_firebase_token")
"""