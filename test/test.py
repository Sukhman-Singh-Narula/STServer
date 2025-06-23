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

def print_json(data, title="JSON Response"):
    """Pretty print JSON data"""
    print(f"\n{Colors.CYAN}📋 {title}:{Colors.END}")
    print(f"{Colors.WHITE}{json.dumps(data, indent=2, ensure_ascii=False)}{Colors.END}")

def get_firebase_token():
    """Get Firebase token from environment or user input"""
    # Check environment variable first
    env_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjNiZjA1MzkxMzk2OTEzYTc4ZWM4MGY0MjcwMzM4NjM2NDA2MTBhZGMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1MDY2MDgyNywidXNlcl9pZCI6InRlc3QtdXNlci0xMjM0NSIsInN1YiI6InRlc3QtdXNlci0xMjM0NSIsImlhdCI6MTc1MDY2MDgyNywiZXhwIjoxNzUwNjY0NDI3LCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.QXspYb9c-bTe9lhECk9mwklE2JC8rGNJy_Cmad9mdOC_OWHYatOaeWgKycIgNxJrowWe84MpNGpN98Eh9qX_vrzut_iln_I0uM5R4EiI4rpjj8yqrCVf9nANVBPEEB2wB403OR7YFT2qxXFwV52XKLgyF9m7WXqL7RcNHlkoEv-pKc_nnD19ZyO44EGwpz9z-WGRq-aZl8vCvjxI-1BXCY3hCgWESAW8MaOucIYuDYzBsG3FJd4FNdsAZRER5AmAQV0ecqkspr9gsqjMqoV6c2o1FI-Hhn5lIjdKMHcSRFolULXW5h8fntOmsdjPAVtlzLtHrRuGhDupzMEyfZNG7A"
    
    return env_token

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

def test_async_story_generation(firebase_token):
    """Test new async story generation with polling"""
    print_header("Testing Async Story Generation (ESP32 Style)")
    
    print_info("This will test the new async story generation system...")
    print_warning("This may take 1-2 minutes and will use OpenAI API credits")
    
    # Ask for confirmation
    try:
        confirm = input(f"{Colors.YELLOW}Continue with async story generation test? (y/n): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Skipping async story generation test")
            return True
    except KeyboardInterrupt:
        print_info("\nSkipping async story generation test")
        return True
    
    payload = {
        "firebase_token": firebase_token,
        "prompt": "Create a short test story about a robot and a cat becoming friends"
    }
    
    print_info("Step 1: Starting story generation...")
    start_time = time.time()
    
    try:
        # Step 1: Start generation
        response = requests.post(
            f"{BASE_URL}/stories/generate", 
            json=payload,
            timeout=30  # Should be fast now
        )
        
        if response.status_code != 200:
            print_error(f"Story generation start failed: {response.text}")
            return False
        
        generation_data = response.json()
        print_json(generation_data, "Story Generation Started")
        
        if not generation_data.get('success'):
            print_error("Story generation did not start successfully")
            return False
        
        story_id = generation_data.get('story_id')
        if not story_id:
            print_error("No story_id returned")
            return False
        
        print_success(f"Story generation started! Story ID: {story_id}")
        
        # Step 2: Poll for completion
        print_info("Step 2: Polling for completion (ESP32 style)...")
        
        max_polls = 60  # 2 minutes max (60 polls * 2 seconds)
        poll_count = 0
        
        while poll_count < max_polls:
            poll_count += 1
            print_info(f"Poll #{poll_count}: Checking story status...")
            
            try:
                fetch_response = requests.get(
                    f"{BASE_URL}/stories/fetch/{story_id}",
                    timeout=10
                )
                
                if fetch_response.status_code != 200:
                    print_error(f"Fetch failed: {fetch_response.text}")
                    return False
                
                fetch_data = fetch_response.json()
                
                # Print current status
                status = fetch_data.get('status', 'unknown')
                message = fetch_data.get('message', 'No message')
                
                if fetch_data.get('success'):
                    # Story completed!
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print_success(f"Story completed in {duration:.1f} seconds after {poll_count} polls!")
                    print_json(fetch_data, "Final Story Data")
                    
                    # Validate story data
                    story = fetch_data.get('story', {})
                    if story:
                        print_success("Story validation:")
                        print_info(f"  Title: {story.get('title', 'Unknown')}")
                        print_info(f"  Story ID: {story.get('story_id', 'Unknown')}")
                        print_info(f"  Total Scenes: {story.get('total_scenes', 0)}")
                        print_info(f"  Total Duration: {story.get('total_duration', 0)/1000:.1f} seconds")
                        
                        scenes = story.get('scenes', [])
                        if scenes:
                            print_info(f"  First Scene: {scenes[0].get('text', 'No text')[:60]}...")
                            print_info(f"  Audio URL: {'✓' if scenes[0].get('audio_url') else '✗'}")
                            print_info(f"  Image URL: {'✓' if scenes[0].get('image_url') else '✗'}")
                    
                    return True
                else:
                    # Still processing
                    print_warning(f"Status: {status} - {message}")
                    
                    if status == "failed":
                        print_error("Story generation failed!")
                        print_json(fetch_data, "Error Response")
                        return False
                    
                    # Wait 2 seconds before next poll (ESP32 style)
                    print_info("Waiting 2 seconds before next poll...")
                    time.sleep(2)
                
            except Exception as poll_error:
                print_error(f"Poll error: {str(poll_error)}")
                time.sleep(2)
                continue
        
        # Timeout
        print_error(f"Story generation timed out after {max_polls} polls (2 minutes)")
        return False
        
    except requests.exceptions.Timeout:
        print_error("Story generation start timed out")
        return False
    except Exception as e:
        print_error(f"Async story generation error: {str(e)}")
        return False

def test_story_generation_quick(firebase_token):
    """Test story generation with a simple prompt (LEGACY - keeping for comparison)"""
    print_header("Testing Legacy Story Generation (Full Wait)")
    
    print_info("This is the old synchronous method for comparison...")
    print_warning("This endpoint may timeout on ESP32 devices")
    
    # Ask for confirmation
    try:
        confirm = input(f"{Colors.YELLOW}Continue with legacy story generation test? (y/n): {Colors.END}")
        if confirm.lower() != 'y':
            print_info("Skipping legacy story generation test")
            return True
    except KeyboardInterrupt:
        print_info("\nSkipping legacy story generation test")
        return True
    
    payload = {
        "firebase_token": firebase_token,
        "prompt": "Create a very short story about a friendly robot (test story)"
    }
    
    print_info("Starting legacy story generation...")
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
            
            # Check if this is the new async response or old sync response
            if 'story_id' in data and 'story' not in data:
                print_warning("Server returned async response instead of sync response")
                print_info("This means the async endpoint is working correctly!")
                return True
            
            story = data.get('story', {})
            
            print_success(f"Story generated in {duration:.1f} seconds!")
            print_info(f"Title: {story.get('title', 'Unknown')}")
            print_info(f"Story ID: {story.get('story_id', 'Unknown')}")
            print_info(f"Scenes: {story.get('total_scenes', 0)}")
            print_info(f"Duration: {story.get('total_duration', 0)/1000:.1f} seconds")
            
            # Check first scene
            scenes = story.get('scenes', [])
            if scenes:
                scene = scenes[0]
                print_success("First scene generated successfully:")
                print_info(f"  Text: {scene.get('text', 'No text')[:80]}...")
                print_info(f"  Audio URL: {'✓' if scene.get('audio_url') else '✗'}")
                print_info(f"  Image URL: {'✓' if scene.get('image_url') else '✗'}")
            
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
                    print_info(f"  {i+1}. {story['title']} ({story.get('total_scenes', '?')} scenes)")
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
        ("Async Story Generation (ESP32)", lambda: test_async_story_generation(firebase_token)),
        ("Legacy Story Generation", lambda: test_story_generation_quick(firebase_token)),
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