#!/usr/bin/env python3
"""
Simple server test to check if bucket configuration is working
"""

import requests
import json

def test_server_status():
    """Test if server is running and check Firebase status"""
    print("🔍 Testing Server Status")
    print("=" * 40)
    
    try:
        print("🌐 Checking server health...")
        response = requests.get("http://localhost:8000/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running")
            
            # Check Firebase status
            firebase_status = data.get('services', {}).get('firebase', 'unknown')
            print(f"🔥 Firebase status: {firebase_status}")
            
            if firebase_status == 'connected':
                print("✅ Firebase Storage is connected!")
                return True
            else:
                print("❌ Firebase Storage not connected")
                print("💡 This suggests the bucket configuration is still wrong")
                return False
                
        else:
            print(f"❌ Server responded with error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("💡 Server is not running. Start it with: python app/main.py")
        return False
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        return False

def test_quick_upload():
    """Test a quick story generation to see the exact error"""
    print("\n🧪 Testing Quick Upload")
    print("=" * 40)
    
    # Get Firebase token
    firebase_token = input("Enter your Firebase token (or 'skip' to skip): ").strip()
    
    if firebase_token.lower() == 'skip':
        print("⏭️ Skipping upload test")
        return
    
    payload = {
        "firebase_token": firebase_token,
        "prompt": "Quick test - robot story (1 scene only)"
    }
    
    print("🤖 Testing story generation to see bucket error...")
    
    try:
        response = requests.post(
            "http://localhost:8000/stories/generate",
            json=payload,
            timeout=60  # Short timeout to catch error quickly
        )
        
        if response.status_code == 200:
            print("✅ Story generation started successfully!")
            print("⚠️ Let it run or stop with Ctrl+C - we just needed to see if bucket is working")
        else:
            print(f"❌ Story generation failed: {response.status_code}")
            error_data = response.text
            print(f"Error details: {error_data}")
            
            # Look for bucket errors in the response
            if "storyteller-7ece7.appspot.com" in error_data:
                print("\n🎯 FOUND THE ISSUE!")
                print("❌ Server is still trying to use: storyteller-7ece7.appspot.com")
                print("✅ Should be using: storyteller-7ece7.firebasestorage.app")
                print("\n🔧 FIX NEEDED:")
                print("1. Make sure server is completely stopped (Ctrl+C)")
                print("2. Clear cache: rm -rf __pycache__ app/__pycache__")
                print("3. Restart server: python app/main.py")
            elif "storyteller-7ece7.firebasestorage.app" in error_data:
                print("✅ Server is using correct bucket format")
                print("❌ But there might be another issue")
            
    except requests.exceptions.Timeout:
        print("⏳ Request is taking time (this is normal for story generation)")
        print("✅ The fact that it started means bucket config might be working")
    except Exception as e:
        print(f"❌ Error testing upload: {e}")

def check_env_file():
    """Double-check .env file"""
    print("📋 Double-checking .env file...")
    
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        bucket_lines = [line for line in lines if 'FIREBASE_STORAGE_BUCKET' in line and not line.strip().startswith('#')]
        
        print(f"Found {len(bucket_lines)} active bucket lines:")
        for line in bucket_lines:
            print(f"  {line}")
        
        if len(bucket_lines) == 1:
            bucket_value = bucket_lines[0].split('=', 1)[1].strip()
            if bucket_value == 'storyteller-7ece7.firebasestorage.app':
                print("✅ .env file is correct")
                return True
            else:
                print(f"❌ .env has wrong value: {bucket_value}")
                return False
        elif len(bucket_lines) > 1:
            print("❌ Multiple bucket lines found - this might cause issues")
            return False
        else:
            print("❌ No bucket configuration found")
            return False
            
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False

def main():
    """Run simple tests"""
    print("🧪 Simple Server Bucket Test")
    print("=" * 50)
    
    # Check .env file first
    env_ok = check_env_file()
    
    if not env_ok:
        print("\n❌ .env file issues found. Fix these first:")
        print("Make sure .env contains exactly:")
        print("FIREBASE_STORAGE_BUCKET=storyteller-7ece7.firebasestorage.app")
        return
    
    # Test server
    server_ok = test_server_status()
    
    if not server_ok:
        if "not running" in str(server_ok):
            print("\n🔧 Start your server first:")
            print("python app/main.py")
        else:
            print("\n🔧 Server issues found. Try:")
            print("1. Stop server completely (Ctrl+C)")
            print("2. Clear cache: rm -rf __pycache__ app/__pycache__")  
            print("3. Restart: python app/main.py")
        return
    
    # Test upload
    if server_ok:
        test_quick_upload()
    
    print("\n📊 Summary:")
    print(f"✅ .env file: {'OK' if env_ok else 'NEEDS FIX'}")
    print(f"✅ Server: {'OK' if server_ok else 'NEEDS FIX'}")
    
    if env_ok and server_ok:
        print("🎉 Configuration looks good!")
    else:
        print("⚠️ Issues found - follow the recommendations above")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")