#!/usr/bin/env python3
"""
ESP32 Storyteller API Test Suite
Tests all authentication and story endpoints for ESP32 integration
"""

import requests
import json
import time
import random
import string
from typing import Dict, Any, Optional

class StorytellerAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.firebase_token = None
        self.refresh_token = None
        self.user_info = None
        self.test_results = {}
        
        # Generate unique test user
        random_suffix = ''.join(random.choices(string.digits, k=6))
        self.test_email = f"test_user_{random_suffix}@example.com"
        self.test_password = "TestPassword123!"
        self.test_name = f"Test User {random_suffix}"
        
        print(f"🧪 ESP32 Storyteller API Test Suite")
        print(f"📍 Testing server: {self.base_url}")
        print(f"👤 Test user: {self.test_email}")
        print("-" * 60)

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results[test_name] = {
            "success": success,
            "details": details
        }

    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}, 0
            
            try:
                response_data = response.json()
            except:
                response_data = {"text_response": response.text}
            
            return response.status_code < 400, response_data, response.status_code
            
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection failed - is server running?"}, 0
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout"}, 0
        except Exception as e:
            return False, {"error": str(e)}, 0

    def test_server_health(self):
        """Test if server is running"""
        print("\n🔍 Testing Server Health...")
        
        success, data, status = self.make_request("GET", "/health")
        
        if success:
            self.log_test("Server Health Check", True, 
                         f"Status: {data.get('status', 'unknown')}")
        else:
            self.log_test("Server Health Check", False, 
                         f"Server not responding: {data.get('error', 'Unknown error')}")
            return False
        
        return True

    def test_signup(self):
        """Test user signup"""
        print("\n🔐 Testing Authentication Endpoints...")
        
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "display_name": self.test_name
        }
        
        success, data, status = self.make_request("POST", "/auth/signup", payload)
        
        if success and data.get("success"):
            self.firebase_token = data.get("firebase_token")
            self.refresh_token = data.get("refresh_token")
            self.user_info = data.get("user_info", {})
            
            self.log_test("User Signup", True, 
                         f"User ID: {self.user_info.get('localId', 'unknown')}")
            return True
        else:
            self.log_test("User Signup", False, 
                         f"Error: {data.get('detail', data.get('message', 'Unknown error'))}")
            return False

    def test_signin(self):
        """Test user signin"""
        payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, data, status = self.make_request("POST", "/auth/signin", payload)
        
        if success and data.get("success"):
            self.firebase_token = data.get("firebase_token")
            self.refresh_token = data.get("refresh_token")
            self.user_info = data.get("user_info", {})
            
            self.log_test("User Signin", True, 
                         f"Token length: {len(self.firebase_token) if self.firebase_token else 0}")
            return True
        else:
            self.log_test("User Signin", False, 
                         f"Error: {data.get('detail', data.get('message', 'Unknown error'))}")
            return False

    def test_token_verification(self):
        """Test token verification"""
        if not self.firebase_token:
            self.log_test("Token Verification", False, "No token available")
            return False
        
        payload = {
            "firebase_token": self.firebase_token
        }
        
        success, data, status = self.make_request("POST", "/auth/verify-token", payload)
        
        if success and data.get("success") and data.get("valid"):
            self.log_test("Token Verification", True, 
                         f"Valid for user: {data.get('user_info', {}).get('email', 'unknown')}")
            return True
        else:
            self.log_test("Token Verification", False, 
                         f"Invalid token: {data.get('error', 'Unknown error')}")
            return False

    def test_refresh_token(self):
        """Test token refresh"""
        if not self.refresh_token:
            self.log_test("Token Refresh", False, "No refresh token available")
            return False
        
        payload = {
            "refresh_token": self.refresh_token
        }
        
        success, data, status = self.make_request("POST", "/auth/refresh-token", payload)
        
        if success and data.get("success"):
            old_token = self.firebase_token
            self.firebase_token = data.get("firebase_token")
            self.refresh_token = data.get("refresh_token")
            
            self.log_test("Token Refresh", True, 
                         f"New token different: {old_token != self.firebase_token}")
            return True
        else:
            self.log_test("Token Refresh", False, 
                         f"Error: {data.get('detail', 'Unknown error')}")
            return False

    def test_password_reset(self):
        """Test password reset email"""
        payload = {
            "email": self.test_email
        }
        
        success, data, status = self.make_request("POST", "/auth/password-reset", payload)
        
        # Password reset should always return success for security
        if success:
            self.log_test("Password Reset", True, 
                         "Reset email request processed")
            return True
        else:
            self.log_test("Password Reset", False, 
                         f"Error: {data.get('detail', 'Unknown error')}")
            return False

    def test_profile_registration(self):
        """Test profile registration after authentication"""
        print("\n👤 Testing Profile Management...")
        
        if not self.firebase_token:
            self.log_test("Profile Registration", False, "No authentication token")
            return False
        
        payload = {
            "firebase_token": self.firebase_token,
            "parent": {
                "name": "Test Parent",
                "email": self.test_email,
                "phone_number": "+1234567890"
            },
            "child": {
                "name": "Test Child",
                "age": 6,
                "interests": ["animals", "space", "adventure"]
            }
        }
        
        success, data, status = self.make_request("POST", "/auth/register", payload)
        
        if success and data.get("success"):
            self.log_test("Profile Registration", True, 
                         f"Profile created for: {data.get('profile', {}).get('child', {}).get('name', 'unknown')}")
            return True
        else:
            self.log_test("Profile Registration", False, 
                         f"Error: {data.get('detail', data.get('message', 'Unknown error'))}")
            return False

    def test_story_generation(self):
        """Test story generation (async)"""
        print("\n📚 Testing Story Operations...")
        
        if not self.firebase_token:
            self.log_test("Story Generation", False, "No authentication token")
            return False
        
        payload = {
            "firebase_token": self.firebase_token,
            "prompt": "Tell a story about a brave robot and a friendly dragon"
        }
        
        success, data, status = self.make_request("POST", "/stories/generate", payload)
        
        if success and data.get("success"):
            story_id = data.get("story_id")
            self.log_test("Story Generation Started", True, 
                         f"Story ID: {story_id}")
            
            # Wait a bit and check story status
            if story_id:
                print("   ⏳ Waiting 5 seconds to check story progress...")
                time.sleep(5)
                
                success2, data2, status2 = self.make_request("GET", f"/stories/fetch/{story_id}")
                
                if success2:
                    story_status = data2.get("status", "unknown")
                    self.log_test("Story Status Check", True, 
                                 f"Status: {story_status}")
                    return story_id
                else:
                    self.log_test("Story Status Check", False, 
                                 f"Could not check status")
            
            return story_id
        else:
            self.log_test("Story Generation", False, 
                         f"Error: {data.get('detail', data.get('message', 'Unknown error'))}")
            return None

    def test_story_fetching(self):
        """Test fetching user stories"""
        if not self.firebase_token:
            self.log_test("Story Fetching", False, "No authentication token")
            return False
        
        success, data, status = self.make_request("GET", f"/stories/user/{self.firebase_token}?limit=5")
        
        if success and data.get("success"):
            stories = data.get("stories", [])
            total_count = data.get("total_count", 0)
            
            self.log_test("Story List Fetch", True, 
                         f"Found {len(stories)} stories (total: {total_count})")
            
            # Test story details if we have stories
            if stories:
                story_id = stories[0].get("story_id")
                if story_id:
                    success2, data2, status2 = self.make_request("GET", f"/stories/details/{story_id}")
                    
                    if success2 and data2.get("success"):
                        story_details = data2.get("story", {})
                        scenes = story_details.get("scenes", [])
                        
                        self.log_test("Story Details Fetch", True, 
                                     f"Title: '{story_details.get('title', 'unknown')}', Scenes: {len(scenes)}")
                        
                        # Check if audio/image URLs are present
                        if scenes:
                            first_scene = scenes[0]
                            has_audio = bool(first_scene.get("audio_url"))
                            has_image = bool(first_scene.get("image_url"))
                            
                            self.log_test("Scene Media URLs", has_audio and has_image, 
                                         f"Audio: {has_audio}, Image: {has_image}")
                    else:
                        self.log_test("Story Details Fetch", False, 
                                     f"Could not fetch story details")
            
            return True
        else:
            self.log_test("Story List Fetch", False, 
                         f"Error: {data.get('detail', data.get('message', 'Unknown error'))}")
            return False

    def test_esp32_simulation(self):
        """Simulate ESP32 setup portal flow"""
        print("\n🤖 Simulating ESP32 Setup Portal Flow...")
        
        print("   📱 Step 1: User connects to ESP32 WiFi hotspot")
        print("   🌐 Step 2: User opens 192.168.4.1 in browser")
        print("   📝 Step 3: User enters WiFi + login credentials")
        print("   🔐 Step 4: ESP32 authenticates with server...")
        
        # This is what ESP32 would do during setup
        signin_payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, data, status = self.make_request("POST", "/auth/signin", signin_payload)
        
        if success and data.get("success"):
            esp32_token = data.get("firebase_token")
            esp32_refresh = data.get("refresh_token")
            
            print(f"   ✅ ESP32 received token: {esp32_token[:20]}...")
            print(f"   💾 ESP32 stores token + WiFi credentials in flash")
            print(f"   🔄 ESP32 switches to home WiFi...")
            print(f"   📡 ESP32 ready for story operations!")
            
            # Test story fetching as ESP32 would
            success2, data2, status2 = self.make_request("GET", f"/stories/user/{esp32_token}?limit=3")
            
            if success2 and data2.get("success"):
                stories = data2.get("stories", [])
                self.log_test("ESP32 Story Fetch Simulation", True, 
                             f"ESP32 can access {len(stories)} stories")
                
                # Show what ESP32 would display
                print("   📺 ESP32 Display would show:")
                for i, story in enumerate(stories[:3]):
                    print(f"      {i+1}. {story.get('title', 'Unknown Story')}")
                
                return True
            else:
                self.log_test("ESP32 Story Fetch Simulation", False, 
                             "ESP32 cannot fetch stories")
                return False
        else:
            self.log_test("ESP32 Authentication Simulation", False, 
                         "ESP32 authentication failed")
            return False

    def test_signout(self):
        """Test user signout"""
        print("\n👋 Testing Cleanup...")
        
        if not self.firebase_token:
            self.log_test("User Signout", False, "No token to sign out")
            return False
        
        payload = {
            "firebase_token": self.firebase_token
        }
        
        success, data, status = self.make_request("POST", "/auth/signout", payload)
        
        if success and data.get("success"):
            self.log_test("User Signout", True, "Token revoked")
            
            # Clear tokens
            self.firebase_token = None
            self.refresh_token = None
            return True
        else:
            self.log_test("User Signout", False, 
                         f"Error: {data.get('detail', 'Unknown error')}")
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result["success"]:
                    print(f"   • {test_name}: {result['details']}")
        
        print("\n🤖 ESP32 INTEGRATION READINESS:")
        critical_tests = [
            "User Signin",
            "Token Verification", 
            "Token Refresh",
            "Story List Fetch",
            "ESP32 Story Fetch Simulation"
        ]
        
        critical_passed = sum(1 for test in critical_tests 
                            if self.test_results.get(test, {}).get("success", False))
        
        if critical_passed == len(critical_tests):
            print("✅ READY - All critical endpoints working for ESP32!")
        else:
            print(f"⚠️  NOT READY - {len(critical_tests) - critical_passed} critical tests failed")
        
        print("\n💡 NEXT STEPS:")
        if failed_tests == 0:
            print("   • Your API is fully ready for ESP32 integration!")
            print("   • Start implementing the ESP32 setup portal")
            print("   • Use the /auth/signin endpoint during device setup")
            print("   • Use /stories/user/{token} to fetch story lists")
        else:
            print("   • Fix the failed endpoints before ESP32 integration")
            print("   • Check your .env file has FIREBASE_WEB_API_KEY set")
            print("   • Verify Firebase credentials are correct")

    def run_all_tests(self):
        """Run complete test suite"""
        try:
            # Core server tests
            if not self.test_server_health():
                print("❌ Server not available - stopping tests")
                return
            
            # Authentication flow tests
            if self.test_signup():
                # If signup works, continue with that account
                self.test_token_verification()
                self.test_refresh_token()
            else:
                # If signup fails (user exists), try signin
                if self.test_signin():
                    self.test_token_verification()
                    self.test_refresh_token()
                else:
                    print("❌ Cannot authenticate - stopping critical tests")
                    self.print_summary()
                    return
            
            # Profile and story tests
            self.test_password_reset()
            self.test_profile_registration()
            
            # Generate a test story (this may take time)
            story_id = self.test_story_generation()
            
            # Wait for story generation if needed
            if story_id:
                print("   ⏳ Waiting 30 seconds for story generation...")
                time.sleep(30)
                
                # Check final story status
                success, data, status = self.make_request("GET", f"/stories/fetch/{story_id}")
                if success:
                    final_status = data.get("status", "unknown")
                    print(f"   📖 Final story status: {final_status}")
            
            # Test story operations
            self.test_story_fetching()
            
            # ESP32 simulation
            self.test_esp32_simulation()
            
            # Cleanup
            self.test_signout()
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Test suite error: {str(e)}")
        finally:
            self.print_summary()

if __name__ == "__main__":
    import sys
    
    # Allow custom server URL
    server_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("🚀 Starting ESP32 Storyteller API Test Suite...")
    print("⚠️  Make sure your server is running with the new auth endpoints!")
    print("📋 This will test the complete flow an ESP32 device would use.")
    
    # Wait for user confirmation
    input("\nPress Enter to start testing...")
    
    tester = StorytellerAPITester(server_url)
    tester.run_all_tests()