# 📚 User CRUD API Documentation

## Overview
This document provides comprehensive documentation for the User CRUD API endpoints with avatar support for the Storytelling Server. These endpoints allow you to manage user profiles, avatar configurations, and associated data.

## 🌐 Base Configuration

### Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### Authentication
All endpoints require Firebase ID token authentication:
```http
Authorization: Bearer <firebase_id_token>
```

---

## 📋 User Profile Endpoints

### 1. Register User
Create a new user profile with parent and child information.

**Endpoint**: `POST /users/register`

**Request Body**:
```json
{
  "firebase_token": "string",
  "parent": {
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com",
    "phone_number": "+1234567890",
    "avatar_seed": "parent-avatar-12345",
    "avatar_style": "avataaars",
    "avatar_generated": true
  },
  "child": {
    "name": "Alex",
    "age": 6,
    "interests": ["dinosaurs", "space", "magic"],
    "avatar_seed": "child-avatar-67890",
    "avatar_style": "avataaars",
    "avatar_generated": true
  },
  "system_prompt": "Create magical stories for Alex about dinosaurs and space adventures",
  "child_image_base64": "optional_base64_encoded_image"
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "User profile created successfully",
  "profile": {
    "user_id": "user-12345",
    "parent": {
      "name": "Sarah Johnson",
      "email": "sarah.johnson@example.com",
      "phone_number": "+1234567890",
      "avatar_seed": "parent-avatar-12345",
      "avatar_style": "avataaars",
      "avatar_generated": true
    },
    "child": {
      "name": "Alex",
      "age": 6,
      "interests": ["dinosaurs", "space", "magic"],
      "image_url": "https://firebase.storage.url/image.jpg",
      "avatar_seed": "child-avatar-67890",
      "avatar_style": "avataaars",
      "avatar_generated": true
    },
    "system_prompt": "Create magical stories for Alex...",
    "created_at": "2025-01-07T10:30:00Z",
    "updated_at": "2025-01-07T10:30:00Z",
    "story_count": 0,
    "last_active": "2025-01-07T10:30:00Z"
  }
}
```

---

### 2. Get User Profile
Retrieve the complete user profile with avatar information.

**Endpoint**: `GET /users/profile?firebase_token={token}`

**Response (200 OK)**:
```json
{
  "success": true,
  "profile": {
    "user_id": "user-12345",
    "parent": {
      "name": "Sarah Johnson",
      "email": "sarah.johnson@example.com",
      "phone_number": "+1234567890",
      "avatar_seed": "parent-avatar-12345",
      "avatar_style": "avataaars",
      "avatar_generated": true
    },
    "child": {
      "name": "Alex",
      "age": 6,
      "interests": ["dinosaurs", "space", "magic"],
      "image_url": "https://firebase.storage.url/image.jpg",
      "avatar_seed": "child-avatar-67890",
      "avatar_style": "avataaars",
      "avatar_generated": true
    },
    "system_prompt": "Create magical stories for Alex...",
    "created_at": "2025-01-07T10:30:00Z",
    "updated_at": "2025-01-07T10:30:00Z",
    "story_count": 5,
    "last_active": "2025-01-07T10:30:00Z"
  }
}
```

---

### 3. Update User Profile
Update the complete user profile information.

**Endpoint**: `PUT /users/profile`

**Request Body** (all fields optional):
```json
{
  "firebase_token": "string",
  "parent": {
    "name": "Sarah Marie Johnson",
    "email": "sarah.marie@example.com",
    "phone_number": "+1234567891",
    "avatar_seed": "updated-parent-avatar-456",
    "avatar_style": "avataaars",
    "avatar_generated": true
  },
  "child": {
    "name": "Alexander",
    "age": 7,
    "interests": ["robots", "space", "magic", "dinosaurs"],
    "avatar_seed": "updated-child-avatar-123",
    "avatar_style": "avataaars",
    "avatar_generated": true
  },
  "system_prompt": "Updated system prompt...",
  "child_image_base64": "optional_new_base64_image"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "profile": {
    // Updated profile object
  }
}
```

---

### 4. Delete User Profile
Delete the user's profile and all associated data.

**Endpoint**: `DELETE /users/profile?firebase_token={token}`

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "User profile and data deleted successfully"
}
```

---

## 🎨 Avatar Management Endpoints

### 5. Update Avatar Settings
Update avatar configuration for child or parent.

**Endpoint**: `PUT /users/avatar`

**Request Body**:
```json
{
  "firebase_token": "string",
  "target": "child",  // or "parent"
  "avatar_seed": "new-avatar-seed-999",
  "avatar_style": "avataaars"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Avatar settings updated for child",
  "profile": {
    // Updated profile with new avatar settings
  }
}
```

---

### 6. Get Avatar Settings
Retrieve avatar configuration for child or parent.

**Endpoint**: `GET /users/avatar/{target}?firebase_token={token}`

**Parameters**:
- `target`: "child" or "parent"

**Response (200 OK)**:
```json
{
  "success": true,
  "target": "child",
  "avatar_settings": {
    "avatar_seed": "child-avatar-67890",
    "avatar_style": "avataaars",
    "avatar_generated": true
  }
}
```

---

## 👶 Child Profile Endpoints

### 7. Update Child Profile Only
Update only the child's profile information.

**Endpoint**: `PUT /users/child?firebase_token={token}`

**Request Body**:
```json
{
  "name": "Alexander",
  "age": 7,
  "interests": ["robots", "space", "magic", "dinosaurs"],
  "avatar_seed": "updated-child-avatar-123",
  "avatar_style": "avataaars",
  "avatar_generated": true
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Child profile updated successfully",
  "child": {
    "name": "Alexander",
    "age": 7,
    "interests": ["robots", "space", "magic", "dinosaurs"],
    "image_url": "https://firebase.storage.url/image.jpg",
    "avatar_seed": "updated-child-avatar-123",
    "avatar_style": "avataaars",
    "avatar_generated": true
  }
}
```

---

### 8. Get Child Profile Only
Retrieve only the child's profile information.

**Endpoint**: `GET /users/child?firebase_token={token}`

**Response (200 OK)**:
```json
{
  "success": true,
  "child": {
    "name": "Alex",
    "age": 6,
    "interests": ["dinosaurs", "space", "magic"],
    "image_url": "https://firebase.storage.url/image.jpg",
    "avatar_seed": "child-avatar-67890",
    "avatar_style": "avataaars",
    "avatar_generated": true
  }
}
```

---

## 👨 Parent Profile Endpoints

### 9. Update Parent Profile Only
Update only the parent's profile information.

**Endpoint**: `PUT /users/parent?firebase_token={token}`

**Request Body**:
```json
{
  "name": "Sarah Marie Johnson",
  "email": "sarah.marie@example.com",
  "phone_number": "+1234567891",
  "avatar_seed": "updated-parent-avatar-456",
  "avatar_style": "avataaars",
  "avatar_generated": true
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Parent profile updated successfully",
  "parent": {
    "name": "Sarah Marie Johnson",
    "email": "sarah.marie@example.com",
    "phone_number": "+1234567891",
    "avatar_seed": "updated-parent-avatar-456",
    "avatar_style": "avataaars",
    "avatar_generated": true
  }
}
```

---

### 10. Get Parent Profile Only
Retrieve only the parent's profile information.

**Endpoint**: `GET /users/parent?firebase_token={token}`

**Response (200 OK)**:
```json
{
  "success": true,
  "parent": {
    "name": "Sarah Johnson",
    "email": "sarah.johnson@example.com",
    "phone_number": "+1234567890",
    "avatar_seed": "parent-avatar-12345",
    "avatar_style": "avataaars",
    "avatar_generated": true
  }
}
```

---

## 🔧 Utility Endpoints

### 11. Health Check
Check the health status of the user service.

**Endpoint**: `GET /users/health`

**Response (200 OK)**:
```json
{
  "success": true,
  "service": "user_service",
  "firebase_available": true,
  "status": "healthy"
}
```

---

## 🎨 Avatar Styles Reference

The `avatar_style` field supports the following values:

| Style | Description |
|-------|-------------|
| `avataaars` | Default cartoon-style avatars |
| `adventurer` | Adventure-themed avatars |
| `adventurer-neutral` | Neutral adventure avatars |
| `avataaars-neutral` | Neutral cartoon avatars |
| `big-ears` | Avatars with prominent ears |
| `big-ears-neutral` | Neutral big-ears style |
| `big-smile` | Happy, smiling avatars |
| `bottts` | Robot-style avatars |
| `croodles` | Hand-drawn style avatars |
| `croodles-neutral` | Neutral hand-drawn style |
| `micah` | Micah-style avatars |
| `miniavs` | Minimalist avatars |
| `open-peeps` | Open Peeps style |
| `personas` | Persona-based avatars |
| `pixel-art` | 8-bit pixel art style |
| `pixel-art-neutral` | Neutral pixel art |

---

## 💻 Frontend Integration Examples

### React/JavaScript Example

```javascript
// Initialize API client
const API_BASE = 'http://localhost:8000';

// Get Firebase ID token
const getFirebaseToken = async () => {
  const user = firebase.auth().currentUser;
  return await user.getIdToken();
};

// Get user profile with avatar
const getUserProfile = async () => {
  const token = await getFirebaseToken();
  
  const response = await fetch(`${API_BASE}/users/profile?firebase_token=${token}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });
  
  if (response.ok) {
    const data = await response.json();
    
    // Generate avatar URLs for display
    const childAvatarUrl = `https://api.dicebear.com/7.x/${data.profile.child.avatar_style}/svg?seed=${data.profile.child.avatar_seed}`;
    const parentAvatarUrl = `https://api.dicebear.com/7.x/${data.profile.parent.avatar_style}/svg?seed=${data.profile.parent.avatar_seed}`;
    
    return {
      ...data.profile,
      child: {
        ...data.profile.child,
        avatarUrl: childAvatarUrl
      },
      parent: {
        ...data.profile.parent,
        avatarUrl: parentAvatarUrl
      }
    };
  }
  
  throw new Error('Failed to fetch user profile');
};

// Update child avatar
const updateChildAvatar = async (newSeed, newStyle) => {
  const token = await getFirebaseToken();
  
  const response = await fetch(`${API_BASE}/users/avatar`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      firebase_token: token,
      target: 'child',
      avatar_seed: newSeed,
      avatar_style: newStyle
    })
  });
  
  return await response.json();
};

// Register new user
const registerUser = async (parentData, childData) => {
  const token = await getFirebaseToken();
  
  const response = await fetch(`${API_BASE}/users/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      firebase_token: token,
      parent: {
        ...parentData,
        avatar_seed: `parent-${Date.now()}`,
        avatar_style: 'avataaars',
        avatar_generated: true
      },
      child: {
        ...childData,
        avatar_seed: `child-${Date.now()}`,
        avatar_style: 'avataaars',
        avatar_generated: true
      }
    })
  });
  
  return await response.json();
};
```

### Flutter/Dart Example

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:firebase_auth/firebase_auth.dart';

class UserApiService {
  static const String baseUrl = 'http://localhost:8000';
  
  Future<String> getFirebaseToken() async {
    final user = FirebaseAuth.instance.currentUser;
    return await user!.getIdToken();
  }
  
  Future<Map<String, dynamic>> getUserProfile() async {
    final token = await getFirebaseToken();
    
    final response = await http.get(
      Uri.parse('$baseUrl/users/profile?firebase_token=$token'),
      headers: {'Content-Type': 'application/json'},
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final profile = data['profile'];
      
      // Add avatar URLs
      final childAvatarUrl = 'https://api.dicebear.com/7.x/${profile['child']['avatar_style']}/svg?seed=${profile['child']['avatar_seed']}';
      final parentAvatarUrl = 'https://api.dicebear.com/7.x/${profile['parent']['avatar_style']}/svg?seed=${profile['parent']['avatar_seed']}';
      
      profile['child']['avatarUrl'] = childAvatarUrl;
      profile['parent']['avatarUrl'] = parentAvatarUrl;
      
      return profile;
    }
    
    throw Exception('Failed to load user profile');
  }
  
  Future<Map<String, dynamic>> updateChildAvatar(String newSeed, String newStyle) async {
    final token = await getFirebaseToken();
    
    final response = await http.put(
      Uri.parse('$baseUrl/users/avatar'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'firebase_token': token,
        'target': 'child',
        'avatar_seed': newSeed,
        'avatar_style': newStyle,
      }),
    );
    
    return json.decode(response.body);
  }
}
```

---

## ⚠️ Error Responses

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired Firebase token"
}
```

### 404 Not Found
```json
{
  "detail": "User profile not found"
}
```

### 409 Conflict
```json
{
  "detail": "User profile already exists"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "target"],
      "msg": "Target must be 'child' or 'parent'",
      "type": "value_error"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create user profile: Database connection error"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Firebase service is not available"
}
```

---

## 🔄 Complete User Flow

Here's a typical user flow for your frontend application:

1. **User Authentication**: Authenticate user with Firebase
2. **Check Profile**: Check if user profile exists
3. **Register/Load**: Register new user or load existing profile
4. **Display Avatar**: Generate and display avatar using DiceBear API
5. **Profile Management**: Allow users to update their information
6. **Avatar Customization**: Let users customize their avatars

```javascript
// Complete user flow example
const handleUserFlow = async () => {
  try {
    // 1. Get Firebase token
    const token = await getFirebaseToken();
    
    // 2. Try to get existing profile
    let userProfile;
    try {
      userProfile = await getUserProfile();
      console.log('Existing user loaded');
    } catch (error) {
      // 3. Profile doesn't exist, register new user
      userProfile = await registerUser(parentData, childData);
      console.log('New user registered');
    }
    
    // 4. Generate avatar URLs for display
    const childAvatarUrl = `https://api.dicebear.com/7.x/${userProfile.child.avatar_style}/svg?seed=${userProfile.child.avatar_seed}`;
    const parentAvatarUrl = `https://api.dicebear.com/7.x/${userProfile.parent.avatar_style}/svg?seed=${userProfile.parent.avatar_seed}`;
    
    // 5. Set up UI with user data
    setUserData({
      ...userProfile,
      child: { ...userProfile.child, avatarUrl: childAvatarUrl },
      parent: { ...userProfile.parent, avatarUrl: parentAvatarUrl }
    });
    
  } catch (error) {
    console.error('User flow error:', error);
  }
};
```

---

## 📝 Notes

- All endpoints use Firebase authentication
- Avatar seeds should be unique for each user to ensure avatar uniqueness
- Image uploads are optional and stored in Firebase Storage
- Profile updates are partial - only provided fields are updated
- The API supports both parent and child profiles within a single user account
- Avatar URLs are generated client-side using the DiceBear API
- All dates are returned in ISO 8601 format (UTC)

---

**🚀 Your User CRUD API with Avatar support is ready for production use!**
