#!/usr/bin/env python3
"""
Test script to verify enhanced DeepAI retry mechanisms
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.media_service import MediaService
from app.config import settings
from openai import OpenAI

async def test_retry_mechanisms():
    """Test the enhanced retry mechanisms for DeepAI image generation"""
    
    print("🧪 Testing Enhanced DeepAI Retry Mechanisms")
    print("=" * 50)
    
    # Initialize MediaService
    openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    media_service = MediaService(openai_client)
    
    # Test scenarios
    test_prompts = [
        {
            "prompt": "A brave princess in a magical castle",
            "scene": 1,
            "expected": "Should succeed with normal prompt"
        },
        {
            "prompt": "Children playing in a colorful playground",
            "scene": 2,
            "expected": "Should succeed with simple prompt"
        },
        {
            "prompt": "Very complex detailed intricate fantasy scene with multiple characters and magical elements and dragons and castles",
            "scene": 3,
            "expected": "May fail initially but should succeed with retry variations"
        }
    ]
    
    print(f"🎯 Testing {len(test_prompts)} scenarios with enhanced retry logic")
    
    results = []
    
    for i, test_case in enumerate(test_prompts, 1):
        try:
            print(f"\n--- Test {i}: Scene {test_case['scene']} ---")
            print(f"📝 Prompt: {test_case['prompt']}")
            print(f"🎯 Expected: {test_case['expected']}")
            
            # Test with custom dimensions (240x320 from your request)
            result = await media_service.generate_image_deepai(
                test_case['prompt'], 
                test_case['scene'],
                target_dimensions=(240, 320)
            )
            
            if result and len(result) > 1000:  # Reasonable image size
                print(f"✅ SUCCESS: Generated {len(result)} bytes")
                results.append({"scene": test_case['scene'], "status": "success", "size": len(result)})
            else:
                print(f"⚠️ SUSPICIOUS: Generated only {len(result)} bytes")
                results.append({"scene": test_case['scene'], "status": "suspicious", "size": len(result)})
                
        except Exception as e:
            print(f"❌ FAILED: {str(e)}")
            results.append({"scene": test_case['scene'], "status": "failed", "error": str(e)})
    
    # Summary
    print(f"\n" + "=" * 50)
    print("🎯 Test Results Summary:")
    
    success_count = 0
    for result in results:
        status_emoji = "✅" if result['status'] == 'success' else "⚠️" if result['status'] == 'suspicious' else "❌"
        if result['status'] == 'success':
            success_count += 1
            print(f"  {status_emoji} Scene {result['scene']}: {result['status']} ({result['size']:,} bytes)")
        elif result['status'] == 'suspicious':
            print(f"  {status_emoji} Scene {result['scene']}: {result['status']} ({result['size']:,} bytes)")
        else:
            print(f"  {status_emoji} Scene {result['scene']}: {result['error']}")
    
    success_rate = (success_count / len(test_prompts)) * 100
    print(f"\n📊 Success Rate: {success_count}/{len(test_prompts)} ({success_rate:.1f}%)")
    
    if success_rate >= 100:
        print("🎉 EXCELLENT: All images generated successfully!")
    elif success_rate >= 80:
        print("✅ GOOD: Most images generated successfully")
    elif success_rate >= 60:
        print("⚠️ FAIR: Some issues but mostly working")
    else:
        print("❌ POOR: Significant issues with image generation")
    
    return success_rate >= 80

async def test_emergency_regeneration():
    """Test the emergency regeneration method"""
    print(f"\n🚨 Testing Emergency Regeneration Method")
    print("-" * 40)
    
    openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    media_service = MediaService(openai_client)
    
    try:
        result = await media_service.regenerate_failed_scene_image(
            "A happy cartoon character", 
            99,  # Test scene
            target_dimensions=(240, 320),
            max_attempts=3  # Limited for testing
        )
        
        if result and len(result) > 1000:
            print(f"✅ Emergency regeneration successful: {len(result)} bytes")
            return True
        else:
            print(f"⚠️ Emergency regeneration suspicious: {len(result)} bytes")
            return False
            
    except Exception as e:
        print(f"❌ Emergency regeneration failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Enhanced DeepAI Reliability Testing")
    print("This will test the new retry mechanisms to ensure all story scenes get proper images")
    print("\n")
    
    async def run_all_tests():
        # Test main retry mechanisms
        main_success = await test_retry_mechanisms()
        
        # Test emergency regeneration
        emergency_success = await test_emergency_regeneration()
        
        print(f"\n" + "=" * 60)
        print("🏁 Final Assessment:")
        print(f"  Main Retry System: {'✅ PASS' if main_success else '❌ FAIL'}")
        print(f"  Emergency Regeneration: {'✅ PASS' if emergency_success else '❌ FAIL'}")
        
        if main_success and emergency_success:
            print(f"\n🎉 ALL SYSTEMS GO! Story generation should now be highly reliable.")
            print("No more placeholder images in your stories! 🚀")
        elif main_success:
            print(f"\n✅ Main system working well. Emergency regeneration needs attention.")
        else:
            print(f"\n⚠️ Issues detected. May need to check DeepAI API key or connectivity.")
        
        return main_success and emergency_success
    
    # Run tests
    overall_success = asyncio.run(run_all_tests())
    
    if overall_success:
        print(f"\n🎯 Ready for production! The enhanced retry system should eliminate placeholder images.")
        exit(0)
    else:
        print(f"\n🔧 Some issues found. Please check the results above.")
        exit(1)
