#!/usr/bin/env python3
"""
Fixed Test Script for ESP32 Storytelling API
Run this script to validate your API is working correctly.
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def get_firebase_token():
    """Get Firebase token from environment or user input"""
    # Check environment variable first
    env_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImE0YTEwZGVjZTk4MzY2ZDZmNjNlMTY3Mjg2YWU5YjYxMWQyYmFhMjciLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1MDA2ODQxNiwidXNlcl9pZCI6InRlc3QtdXNlci0xMjM0NSIsInN1YiI6InRlc3QtdXNlci0xMjM0NSIsImlhdCI6MTc1MDA2ODQxNiwiZXhwIjoxNzUwMDcyMDE2LCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.PU0xOw7EgAsGKOXvFpBqR_g9Mig21cEWVStE9gqaSXElVq_DupicZdPrUfxGpIgOdX7pdhozshX6XRsieiYTaV2WKJrI8uUOuJEpD7zXxlnyt1dZhQFcuzQS8PIT-sTTNsAIn5kwawgpZYPkBAtqAoBhZu4Wn3LnhJBw5vi7MI2Qq9DIoc0ByXXZBZ5B_PEy8Z9BqWcVYqXSgNsOZ02IdglRWIzW0PeHTwG6mMdjt8X72Jj1uKeRl5_jZ8f3Qm_o6LdJMX07nKn_WwwBBFO4zW33LkPrlnoD9NeyueH8E1pyJvc_B54aThyxSB5pusEEXyE59jnHxRKsD3bm6GTdMg"
    
    return env_token
    
    # Check if we can use debug token
    print_header("Firebase Token Setup")
    print_info("Firebase token needed for authenticated endpoints")
    print_info("Options:")
    print_info("1. Use 'test_token' for debug mode (if DEBUG=true in server)")
    print_info("2. Generate real token with get_test_token.py script")
    print_info("3. Set environment variable: FIREBASE_TOKEN=your_token")
    
    try:
        token = input(f"\n{Colors.YELLOW}Enter Firebase token (or 'test_token' for debug): {Colors.END}")
        if token.strip():
            return token.strip()
        else:
            return "test_token"  # Default to debug token
    except KeyboardInterrupt:
        print_info("\nUsing debug token: test_token")
        return "test_token"

def test_server_connection():
    """Test if server is running"""
    print_header("Testing Server Connection")
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Server is running: {data['message']}")
            print_info(f"Version: {data['version']}")
            print_info(f"AI Stack: {data.get('ai_stack', 'Unknown')}")
            return True
        else:
            print_error(f"Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Is it running on http://localhost:8000?")
        print_info("Start the server with: python app/main.py")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def test_health_check():
    """Test health endpoint"""
    print_header("Testing Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed: {data['status']}")
            
            services = data.get('services', {})
            for service, status in services.items():
                if status in ['connected', 'configured']:
                    print_success(f"{service.title()}: {status}")
                else:
                    print_warning(f"{service.title()}: {status}")
            
            return data['status'] == 'healthy'
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False

def test_cors():
    """Test CORS headers"""
    print_header("Testing CORS Configuration")
    
    try:
        response = requests.options(
            f"{BASE_URL}/auth/test-simple",
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            print_success("CORS preflight request successful")
            for header, value in cors_headers.items():
                if value:
                    print_info(f"{header}: {value}")
                else:
                    print_warning(f"{header}: Not set")
            
            return True
        else:
            print_error(f"CORS test failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"CORS test error: {str(e)}")
        return False

def test_simple_endpoint():
    """Test a simple endpoint without authentication"""
    print_header("Testing Simple Endpoint (No Auth)")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/test-simple", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Simple endpoint working: {data['message']}")
            return True
        else:
            print_error(f"Simple endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Simple endpoint error: {str(e)}")
        return False

def test_user_registration(firebase_token):
    """Test user registration"""
    print_header("Testing User Registration")
    
    payload = {
        "firebase_token": firebase_token,
        "parent": {
            "name": "Test Parent",
            "email": "test@example.com",
            "phone_number": "+1234567890"
        },
        "child": {
            "name": "TestChild",
            "age": 6,
            "interests": ["robots", "space", "adventures"]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"User registration successful: {data['message']}")
            print_info(f"User ID: {data['user_id']}")
            return True
        elif response.status_code == 400 and "already exists" in response.text:
            print_warning("User already registered (this is fine)")
            return True
        else:
            print_error(f"Registration failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Registration error: {str(e)}")
        return False

def test_story_generation_quick(firebase_token):
    """Test story generation with a simple prompt"""
    print_header("Testing Story Generation (Quick Test)")
    
    print_info("This will test story generation with OpenAI...")
    print_warning("This may take 2-5 minutes and will use OpenAI API credits")
    
    # Ask for confirmation
    try:
        confirm = input(f"{Colors.YELLOW}Continue with story generation test? (y/n): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Skipping story generation test")
            return True
    except KeyboardInterrupt:
        print_info("\nSkipping story generation test")
        return True
    
    payload = {
        "firebase_token": firebase_token,
        "prompt": "Create a very short story about a friendly robot (test story)"
    }
    
    print_info("Starting story generation...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/stories/generate", 
            json=payload,
            timeout=300  # 5 minutes
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            story = data['story']
            
            print_success(f"Story generated in {duration:.1f} seconds!")
            print_info(f"Title: {story['title']}")
            print_info(f"Story ID: {story['story_id']}")
            print_info(f"Scenes: {story['total_scenes']}")
            print_info(f"Duration: {story['total_duration']/1000:.1f} seconds")
            
            # Check first scene
            if story['scenes']:
                scene = story['scenes'][0]
                print_success("First scene generated successfully:")
                print_info(f"  Text: {scene['text'][:80]}...")
                print_info(f"  Audio URL: {'✓' if scene['audio_url'] else '✗'}")
                print_info(f"  Image URL: {'✓' if scene['image_url'] else '✗'}")
            
            return True
        else:
            print_error(f"Story generation failed: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Story generation timed out (>5 minutes)")
        return False
    except Exception as e:
        print_error(f"Story generation error: {str(e)}")
        return False

def test_get_stories(firebase_token):
    """Test getting user stories"""
    print_header("Testing Get User Stories")
    
    try:
        response = requests.get(f"{BASE_URL}/stories/list/{firebase_token}", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            stories = data['stories']
            print_success(f"Found {len(stories)} stories for user")
            
            if stories:
                for i, story in enumerate(stories[:3]):  # Show first 3
                    print_info(f"  {i+1}. {story['title']} ({story['total_scenes']} scenes)")
            else:
                print_info("No stories found (run story generation test first)")
            
            return True
        else:
            print_error(f"Get stories failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Get stories error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests in sequence"""
    print_header("ESP32 Storytelling API Test Suite")
    print_info(f"Testing server at: {BASE_URL}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get Firebase token
    firebase_token = get_firebase_token()
    
    tests = [
        ("Server Connection", lambda: test_server_connection()),
        ("Health Check", lambda: test_health_check()),
        ("CORS Configuration", lambda: test_cors()),
        ("Simple Endpoint", lambda: test_simple_endpoint()),
        ("User Registration", lambda: test_user_registration(firebase_token)),
        ("Get User Stories", lambda: test_get_stories(firebase_token)),
        ("Story Generation", lambda: test_story_generation_quick(firebase_token)),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{Colors.MAGENTA}Running: {test_name}{Colors.END}")
            results[test_name] = test_func()
        except KeyboardInterrupt:
            print_error(f"\nTest interrupted: {test_name}")
            results[test_name] = False
            break
        except Exception as e:
            print_error(f"Test crashed: {test_name} - {str(e)}")
            results[test_name] = False
    
    # Summary
    print_header("Test Results Summary")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}")
            passed += 1
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print_success("🎉 All tests passed! Your API is working correctly.")
    elif passed >= total * 0.8:
        print_warning(f"⚠️  Most tests passed ({passed}/{total}). Check failed tests above.")
    else:
        print_error(f"❌ Many tests failed ({passed}/{total}). Check your configuration.")
    
    return passed == total

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print_error("\n\nTests interrupted by user")
    except Exception as e:
        print_error(f"\nTest suite crashed: {str(e)}")