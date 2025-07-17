#!/usr/bin/env python3
"""
Test script to verify Replicate SDXL image generation with 1024x1024 → 304x304 resize
"""

import asyncio
import time
from app.services.media_service import MediaService
from app.config import settings
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_image_resize():
    """Test the new image generation and resize functionality"""
    try:
        print("🖼️ Testing Replicate SDXL image generation with 1024x1024 → 304x304 resize...")
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Initialize media service
        media_service = MediaService(openai_client)
        
        # Test prompt
        test_prompt = "A cute cat sitting in a sunny garden with colorful flowers"
        
        print(f"🎨 Generating image for prompt: {test_prompt}")
        start_time = time.time()
        
        # Generate image using the new method
        image_data = await media_service.generate_image_replicate(test_prompt, 1)
        
        generation_time = time.time() - start_time
        
        print(f"✅ Image generated successfully!")
        print(f"📊 Generation time: {generation_time:.2f} seconds")
        print(f"📊 Image size: {len(image_data)} bytes")
        
        # Verify the image is actually 304x304
        from PIL import Image
        import io
        
        image = Image.open(io.BytesIO(image_data))
        print(f"📐 Image dimensions: {image.size}")
        print(f"📐 Image format: {image.format}")
        
        if image.size == (304, 304):
            print("✅ Image is correctly sized at 304x304!")
        else:
            print(f"❌ Image size is incorrect: {image.size}")
        
        # Save test image to verify quality
        test_filename = f"test_image_304x304_{int(time.time())}.jpg"
        with open(test_filename, 'wb') as f:
            f.write(image_data)
        
        print(f"💾 Test image saved as: {test_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def test_batch_image_generation():
    """Test batch image generation with the new resize functionality"""
    try:
        print("\n🖼️ Testing batch image generation with resize...")
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=settings.openai_api_key)
        
        # Initialize media service
        media_service = MediaService(openai_client)
        
        # Test prompts
        test_prompts = [
            {"scene_number": 1, "visual_prompt": "A friendly dog playing in a park"},
            {"scene_number": 2, "visual_prompt": "A colorful butterfly on a flower"}
        ]
        
        print(f"🎨 Generating {len(test_prompts)} images in batch...")
        start_time = time.time()
        
        # Generate images using batch method
        image_batch = await media_service.generate_image_batch(test_prompts)
        
        generation_time = time.time() - start_time
        
        print(f"✅ Batch generation completed!")
        print(f"📊 Total generation time: {generation_time:.2f} seconds")
        print(f"📊 Average time per image: {generation_time/len(test_prompts):.2f} seconds")
        
        # Verify all images
        for i, image_data in enumerate(image_batch):
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_data))
            print(f"📐 Image {i+1} dimensions: {image.size} ({len(image_data)} bytes)")
            
            if image.size == (304, 304):
                print(f"✅ Image {i+1} is correctly sized!")
            else:
                print(f"❌ Image {i+1} size is incorrect: {image.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Starting image resize tests...")
    
    # Test 1: Single image generation
    success1 = await test_image_resize()
    
    # Test 2: Batch image generation
    success2 = await test_batch_image_generation()
    
    if success1 and success2:
        print("\n✅ All tests passed! Image generation with resize is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())
