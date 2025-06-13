import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
FIREBASE_TOKEN = "eyJhbGciOiAiUlMyNTYiLCAidHlwIjogIkpXVCIsICJraWQiOiAiZDcxOWVjM2UyMDFkMzdiYTAzZjVlZjNmMDI1ZGEwMmI5YmM3NGU3NSJ9.eyJpc3MiOiAiZmlyZWJhc2UtYWRtaW5zZGstZmJzdmNAc3Rvcnl0ZWxsZXItN2VjZTcuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iLCAic3ViIjogImZpcmViYXNlLWFkbWluc2RrLWZic3ZjQHN0b3J5dGVsbGVyLTdlY2U3LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwgImF1ZCI6ICJodHRwczovL2lkZW50aXR5dG9vbGtpdC5nb29nbGVhcGlzLmNvbS9nb29nbGUuaWRlbnRpdHkuaWRlbnRpdHl0b29sa2l0LnYxLklkZW50aXR5VG9vbGtpdCIsICJ1aWQiOiAidGVzdC11c2VyLTEyMzQ1IiwgImlhdCI6IDE3NDk3MzE5NTUsICJleHAiOiAxNzQ5NzM1NTU1fQ.dQXdPwqC5oN9TCDP4RNMNzKNKl0nl1bXGiQ20f1314JY_17sOGmdL1tVtsnz_jgZDSKHr-DFH-CvA28UuYvrb8EId1US-byWNQNedihk6EYKMY5DQQl1zR2PCgt1EkoAT-G_5oVI_q1fgwYtjwBJPMXCd5DRl0L4vJYuk1bn-1-q-5ACKIFyyGRIIlVQkHMJDtSwIWRKQRqTc-djwX-HluB6bL7kuVjj6QyhycX2K1URaYDPzfE3Vxde_f9iNBbRNw5X9bkLu0T-1QIzcwqVshQFKMT6tIquENA4ySPS7An1woe-kVX271l4C6SComY1UZdYTgj_i_r1cUJIpX9grA"  # Replace with actual token

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_user_registration():
    """Test user registration"""
    print("\n👤 Testing user registration...")
    
    payload = {
        "firebase_token": FIREBASE_TOKEN,
        "parent": {
            "name": "Test Parent",
            "email": "test@example.com",
            "phone_number": "+1234567890"
        },
        "child": {
            "name": "Test Child",
            "age": 7,
            "interests": ["dinosaurs", "space", "robots"]
        }
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code in [200, 400]  # 400 if user already exists

def test_story_generation():
    """Test story generation (main functionality)"""
    print("\n📖 Testing story generation...")
    print("⚠️ This may take 2-5 minutes...")
    
    payload = {
        "firebase_token": FIREBASE_TOKEN,
        "prompt": "Create a short story about a friendly robot who loves to paint"
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/stories/generate", 
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Duration: {duration:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Story generated successfully!")
            print(f"Title: {data['story']['title']}")
            print(f"Scenes: {data['story']['total_scenes']}")
            print(f"Duration: {data['story']['total_duration']}ms")
            
            # Test first scene URLs
            first_scene = data['story']['scenes'][0]
            print(f"\n🎬 First scene:")
            print(f"Text: {first_scene['text'][:100]}...")
            print(f"Audio URL: {first_scene['audio_url']}")
            print(f"Image URL: {first_scene['image_url']}")
            
            return data['story']['story_id']
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>5 minutes)")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_get_user_stories():
    """Test getting user stories"""
    print("\n📚 Testing get user stories...")
    
    response = requests.get(f"{BASE_URL}/stories/list/{FIREBASE_TOKEN}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        stories = data['stories']
        print(f"✅ Found {len(stories)} stories")
        
        if stories:
            print(f"Latest story: {stories[0]['title']}")
            return stories[0]['story_id']
    else:
        print(f"❌ Error: {response.text}")
    
    return None

def test_get_story_details(story_id):
    """Test getting detailed story data"""
    if not story_id:
        print("\n❌ No story ID provided for details test")
        return
        
    print(f"\n📋 Testing get story details for {story_id}...")
    
    response = requests.get(f"{BASE_URL}/stories/details/{story_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        story = data['story']
        print(f"✅ Story details retrieved")
        print(f"Title: {story['title']}")
        print(f"Total scenes: {len(story.get('scenes_data', []))}")
    else:
        print(f"❌ Error: {response.text}")

def run_all_tests():
    """Run all tests in sequence"""
    print("🚀 Starting API Tests")
    print("=" * 50)
    
    # Basic tests
    if not test_health():
        print("❌ Health check failed - server may not be running")
        return
    
    if not FIREBASE_TOKEN or FIREBASE_TOKEN == "YOUR_FIREBASE_TOKEN":
        print("❌ Please set a valid FIREBASE_TOKEN in the script")
        return
    
    # User registration
    test_user_registration()
    
    # Main story generation test
    story_id = test_story_generation()
    
    # Story retrieval tests
    list_story_id = test_get_user_stories()
    test_get_story_details(story_id or list_story_id)
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    run_all_tests()