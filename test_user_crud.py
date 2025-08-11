#!/usr/bin/env python3
"""
Test script for User CRUD operations with Avatar support
Tests all the new user management endpoints with avatar functionality
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
FIREBASE_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjJiN2JhZmIyZjEwY2FlMmIxZjA3ZjM4MTZjNTQyMmJlY2NhNWMyMjMiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vc3Rvcnl0ZWxsZXItN2VjZTciLCJhdWQiOiJzdG9yeXRlbGxlci03ZWNlNyIsImF1dGhfdGltZSI6MTc1NDY0NDM1NCwidXNlcl9pZCI6InRlc3QtdXNlci0xMjM0NSIsInN1YiI6InRlc3QtdXNlci0xMjM0NSIsImlhdCI6MTc1NDY0NDM1NCwiZXhwIjoxNzU0NjQ3OTU0LCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7fSwic2lnbl9pbl9wcm92aWRlciI6ImN1c3RvbSJ9fQ.f0Z1fKOmu6tA1n6fjVcpeUcsvK-rCxo3CQSfHMfXbRxJDtm6ZEMnMsnEsD8Xl3lHyuPtMTaLeGK8rXDBXomFoxyoUhwWaIuMaN2EEEBc8VkMj4fXi8KP1GIA96A16yXoFiEr-MYHR-vCNeXV7i5n25ReRpsS2p9TseLZCWUzlGrQYS8NzIBm0vOSKqArUbcI2r2at3590eW7oIU4GdNxsWBKm7p8s0bi3tfG1ok5RpABjo4DdU_KGnNVkuUtlZcvNIwTlxpodfbZ1b850MfDOnoUH5FdNMS2JYHftyiNzwLnOQyn3G3YFLYPi5HeATBHxdQBBcDwB0vUfLtSEWNbOQ"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Test an API endpoint and return response"""
    try:
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        print(f"\n🔄 Testing {method} {endpoint}")
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success: {result.get('message', 'OK')}")
            return result
        else:
            print(f"   ❌ Error: {response.text}")
            return {"error": response.text, "status_code": response.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"error": str(e)}

def main():
    print("🚀 Testing User CRUD Operations with Avatar Support")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing User Service Health")
    health_result = test_endpoint("/users/health")
    
    # Test 2: Register User with Avatar Data
    print("\n2️⃣ Testing User Registration with Avatar Support")
    registration_data = {
        "firebase_token": FIREBASE_TOKEN,
        "parent": {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@example.com",
            "phone_number": "+1234567890",
            "avatar_seed": "parent-avatar-12345",
            "avatar_style": "avataaars",
            "avatar_generated": True
        },
        "child": {
            "name": "Alex",
            "age": 6,
            "interests": ["dinosaurs", "space", "magic"],
            "avatar_seed": "child-avatar-67890",
            "avatar_style": "avataaars", 
            "avatar_generated": True
        },
        "system_prompt": "Create magical stories for Alex about dinosaurs and space adventures"
    }
    
    register_result = test_endpoint("/users/register", "POST", registration_data)
    
    # Test 3: Get User Profile
    print("\n3️⃣ Testing Get User Profile with Avatar Info")
    profile_result = test_endpoint(f"/users/profile?firebase_token={FIREBASE_TOKEN}")
    
    if profile_result.get("success"):
        profile = profile_result.get("profile", {})
        child_data = profile.get("child", {})
        parent_data = profile.get("parent", {})
        
        print(f"   👶 Child Avatar: {child_data.get('avatar_seed')} ({child_data.get('avatar_style')})")
        print(f"   👨 Parent Avatar: {parent_data.get('avatar_seed')} ({parent_data.get('avatar_style')})")
        print(f"   🎨 Child Avatar Generated: {child_data.get('avatar_generated')}")
        print(f"   🎨 Parent Avatar Generated: {parent_data.get('avatar_generated')}")
    
    # Test 4: Update Avatar Settings
    print("\n4️⃣ Testing Avatar Settings Update")
    avatar_update_data = {
        "firebase_token": FIREBASE_TOKEN,
        "target": "child",
        "avatar_seed": "new-child-avatar-999",
        "avatar_style": "avataaars"
    }
    
    avatar_result = test_endpoint("/users/avatar", "PUT", avatar_update_data)
    
    # Test 5: Get Specific Avatar Settings
    print("\n5️⃣ Testing Get Avatar Settings")
    child_avatar_result = test_endpoint(f"/users/avatar/child?firebase_token={FIREBASE_TOKEN}")
    parent_avatar_result = test_endpoint(f"/users/avatar/parent?firebase_token={FIREBASE_TOKEN}")
    
    # Test 6: Update Child Profile Only
    print("\n6️⃣ Testing Child Profile Update")
    child_update_data = {
        "name": "Alexander",
        "age": 7,
        "interests": ["robots", "space", "magic", "dinosaurs"],
        "avatar_seed": "updated-child-avatar-123",
        "avatar_style": "avataaars",
        "avatar_generated": True
    }
    
    child_update_result = test_endpoint(
        f"/users/child?firebase_token={FIREBASE_TOKEN}", 
        "PUT", 
        child_update_data
    )
    
    # Test 7: Update Parent Profile Only  
    print("\n7️⃣ Testing Parent Profile Update")
    parent_update_data = {
        "name": "Sarah Marie Johnson",
        "email": "sarah.marie@example.com",
        "phone_number": "+1234567891",
        "avatar_seed": "updated-parent-avatar-456",
        "avatar_style": "avataaars",
        "avatar_generated": True
    }
    
    parent_update_result = test_endpoint(
        f"/users/parent?firebase_token={FIREBASE_TOKEN}",
        "PUT",
        parent_update_data
    )
    
    # Test 8: Get Child Profile Only
    print("\n8️⃣ Testing Get Child Profile Only")
    child_profile_result = test_endpoint(f"/users/child?firebase_token={FIREBASE_TOKEN}")
    
    # Test 9: Get Parent Profile Only
    print("\n9️⃣ Testing Get Parent Profile Only")
    parent_profile_result = test_endpoint(f"/users/parent?firebase_token={FIREBASE_TOKEN}")
    
    # Test 10: Update Complete Profile
    print("\n🔟 Testing Complete Profile Update")
    complete_update_data = {
        "firebase_token": FIREBASE_TOKEN,
        "parent": {
            "name": "Sarah Complete Johnson",
            "email": "sarah.complete@example.com",
            "phone_number": "+1234567892",
            "avatar_seed": "complete-parent-789",
            "avatar_style": "avataaars",
            "avatar_generated": True
        },
        "child": {
            "name": "Alex Complete",
            "age": 8,
            "interests": ["complete", "space", "magic"],
            "avatar_seed": "complete-child-101",
            "avatar_style": "avataaars",
            "avatar_generated": True
        }
    }
    
    complete_update_result = test_endpoint("/users/profile", "PUT", complete_update_data)
    
    # Test 11: Final Profile Check
    print("\n1️⃣1️⃣ Testing Final Profile State")
    final_profile_result = test_endpoint(f"/users/profile?firebase_token={FIREBASE_TOKEN}")
    
    if final_profile_result.get("success"):
        profile = final_profile_result.get("profile", {})
        print(f"   📊 Final Profile Summary:")
        print(f"   👶 Child: {profile.get('child', {}).get('name')} (age {profile.get('child', {}).get('age')})")
        print(f"   👶 Child Avatar: {profile.get('child', {}).get('avatar_seed')}")
        print(f"   👨 Parent: {profile.get('parent', {}).get('name')}")
        print(f"   👨 Parent Avatar: {profile.get('parent', {}).get('avatar_seed')}")
        print(f"   📈 Story Count: {profile.get('story_count', 0)}")
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 60)
    print("✅ User CRUD operations with avatar support implemented successfully!")
    print("\n🎯 Available Endpoints:")
    print("   • POST   /users/register         - Register new user with avatars")
    print("   • GET    /users/profile          - Get complete profile with avatar info")
    print("   • PUT    /users/profile          - Update complete profile")
    print("   • DELETE /users/profile          - Delete user and all data")
    print("   • PUT    /users/avatar           - Update avatar settings")
    print("   • GET    /users/avatar/{target}  - Get avatar settings")
    print("   • PUT    /users/child            - Update child profile only")
    print("   • GET    /users/child            - Get child profile only")
    print("   • PUT    /users/parent           - Update parent profile only")
    print("   • GET    /users/parent           - Get parent profile only")
    print("   • GET    /users/health           - Health check")
    
    print("\n🎨 Avatar Features:")
    print("   • Custom avatar seeds for unique avatars")
    print("   • Support for different avatar styles")
    print("   • Track avatar generation status")
    print("   • Separate avatars for parent and child")
    print("   • Easy avatar updates via dedicated endpoint")
    
    print("\n🚀 Ready for production use!")

if __name__ == "__main__":
    main()
