#!/usr/bin/env python3
"""
Test script to verify custom dimensions (932x430) work correctly
"""

import asyncio
import io
from PIL import Image
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.media_service import MediaService
from app.config import settings
from openai import OpenAI

async def test_custom_dimensions():
    """Test that all image processing works with custom dimensions like 932x430"""
    
    print("🧪 Testing custom dimensions: 932x430...")
    
    # Initialize MediaService with OpenAI client
    openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
    media_service = MediaService(openai_client)
    
    # Test dimensions
    test_dimensions = (932, 430)
    
    try:
        # Test 1: Create placeholder image with custom dimensions
        print(f"\n1️⃣ Testing placeholder image creation ({test_dimensions[0]}x{test_dimensions[1]})...")
        placeholder_data = media_service._create_placeholder_image(test_dimensions)
        
        # Verify placeholder is correct size
        placeholder_image = Image.open(io.BytesIO(placeholder_data))
        print(f"✅ Placeholder image size: {placeholder_image.size}")
        assert placeholder_image.size == test_dimensions, f"Expected {test_dimensions}, got {placeholder_image.size}"
        
        # Test 2: Create test image and process it with custom dimensions
        print(f"\n2️⃣ Testing image processing...")
        
        # Create a test colored image at different size
        test_image = Image.new('RGB', (1024, 768), color='blue')
        test_buffer = io.BytesIO()
        test_image.save(test_buffer, format='JPEG')
        test_data = test_buffer.getvalue()
        
        # Process the image with custom dimensions
        processed_data = media_service._process_image_fast(test_data, test_dimensions)
        processed_image = Image.open(io.BytesIO(processed_data))
        
        print(f"✅ Processed image size: {processed_image.size}")
        assert processed_image.size == test_dimensions, f"Expected {test_dimensions}, got {processed_image.size}"
        
        # Test 3: Test grayscale conversion with custom dimensions
        print(f"\n3️⃣ Testing grayscale conversion...")
        grayscale_data = media_service.convert_image_to_grayscale_and_resize(test_data, test_dimensions)
        grayscale_image = Image.open(io.BytesIO(grayscale_data))
        
        print(f"✅ Grayscale image size: {grayscale_image.size}")
        print(f"✅ Grayscale image mode: {grayscale_image.mode}")
        assert grayscale_image.size == test_dimensions, f"Expected {test_dimensions}, got {grayscale_image.size}"
        assert grayscale_image.mode == 'L', f"Expected grayscale mode 'L', got {grayscale_image.mode}"
        
        print(f"\n🎉 All custom dimension tests passed!")
        print(f"✅ Placeholder generation: {test_dimensions[0]}x{test_dimensions[1]}")
        print(f"✅ Image processing/resize: {test_dimensions[0]}x{test_dimensions[1]}")
        print(f"✅ Grayscale conversion: {test_dimensions[0]}x{test_dimensions[1]}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

def test_dimension_parsing():
    """Test the dimension parsing function"""
    print("\n🧪 Testing dimension parsing...")
    
    # Import the parsing function
    sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
    from app.routers.stories import parse_dimensions
    
    test_cases = [
        ("932x430", (932, 430)),
        ("1200x2600", (1200, 2600)),
        ("512x512", (512, 512)),
        ("invalid", (1200, 2600)),  # Should default
        ("100", (1200, 2600)),      # Should default
    ]
    
    for input_str, expected in test_cases:
        result = parse_dimensions(input_str)
        print(f"✅ '{input_str}' → {result}")
        if expected == (1200, 2600) and input_str in ["invalid", "100"]:
            # These should fallback to default
            assert result == expected, f"Expected fallback {expected}, got {result}"
        else:
            assert result == expected, f"Expected {expected}, got {result}"
    
    print("✅ All dimension parsing tests passed!")

if __name__ == "__main__":
    # Test dimension parsing first
    test_dimension_parsing()
    
    # Run the async image tests
    result = asyncio.run(test_custom_dimensions())
    
    if result:
        print("\n🚀 Ready for production with custom dimensions support!")
        print("📝 Example API request:")
        print("""
POST /stories/generate
{
  "firebase_token": "your_token_here",
  "prompt": "Tell me a story about a brave princess",
  "isfemale": false,
  "dimensions": "932x430"
}
        """)
        exit(0)
    else:
        print("\n💥 Tests failed - please check the implementation")
        exit(1)
