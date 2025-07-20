#!/usr/bin/env python3
"""
Script to create a test Firebase ID token for API testing
Run this once to get a token you can use for testing
"""

import firebase_admin
from firebase_admin import credentials, auth
import json

def create_test_token():
    """Create a custom Firebase ID token for testing"""
    
    # Initialize Firebase Admin (using your service account JSON)
    try:
        # Try to initialize if not already done
        if not firebase_admin._apps:
            cred = credentials.Certificate('./firebase-credentials.json')
            firebase_admin.initialize_app(cred)
        
        # Create a custom token for testing
        test_user_id = 'test-user-12345'  # Can be any string
        
        # Create custom token
        custom_token = auth.create_custom_token(test_user_id)
        
        print("✅ Custom token created successfully!")
        print(f"📋 Copy this token for testing:")
        print(f"\n{custom_token.decode('utf-8')}\n")
        
        print("💡 Usage:")
        print("1. Copy the token above")
        print("2. Use it as 'firebase_token' in your API calls")
        print("3. Or set environment variable: export FIREBASE_TOKEN='your_token'")
        
        return custom_token.decode('utf-8')
        
    except Exception as e:
        print(f"❌ Error creating token: {str(e)}")
        print("\n🔍 Troubleshooting:")
        print("1. Make sure firebase-credentials.json exists in current directory")
        print("2. Verify the JSON file has proper service account permissions")
        print("3. Check that Firebase Auth is enabled in your project")
        return None

def create_test_user_token():
    """Alternative: Create a real test user and get their token"""
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate('./firebase-credentials.json')
            firebase_admin.initialize_app(cred)
        
        # Create a test user
        test_email = 'test@example.com'
        test_password = 'testpassword123'
        
        try:
            # Try to create user (might already exist)
            user = auth.create_user(
                email=test_email,
                password=test_password,
                email_verified=True
            )
            print(f"✅ Created test user: {user.uid}")
        except auth.EmailAlreadyExistsError:
            # User already exists, get their info
            user = auth.get_user_by_email(test_email)
            print(f"✅ Using existing test user: {user.uid}")
        
        # Create custom token for this user
        custom_token = auth.create_custom_token(user.uid)
        
        print(f"📋 Token for user {test_email}:")
        print(f"\n{custom_token.decode('utf-8')}\n")
        
        print("💡 This token represents a real user account")
        print(f"   Email: {test_email}")
        print(f"   UID: {user.uid}")
        
        return custom_token.decode('utf-8')
        
    except Exception as e:
        print(f"❌ Error creating user token: {str(e)}")
        return None

if __name__ == "__main__":
    print("🔐 Firebase Test Token Generator")
    print("=" * 40)
    
    print("\nOption 1: Simple custom token")
    token1 = create_test_token()
    
    print("\n" + "="*40)
    print("\nOption 2: Real user token")
    token2 = create_test_user_token()
    
    print("\n" + "="*40)
    print("💾 Save token to environment:")
    if token1:
        print(f"export FIREBASE_TOKEN='{token1}'")