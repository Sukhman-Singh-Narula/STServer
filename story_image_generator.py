#!/usr/bin/env python3
"""
Standalone DeepAI Image Generator for Story Scenes
Generates images for story scenes using DeepAI API with custom dimensions
"""

import os
import requests
import time
from PIL import Image
import io
from typing import List, Dict, Tuple

class StoryImageGenerator:
    def __init__(self, deepai_api_key: str, target_dimensions: Tuple[int, int] = (240, 320)):
        """
        Initialize the image generator
        
        Args:
            deepai_api_key: Your DeepAI API key
            target_dimensions: Target image dimensions as (width, height)
        """
        self.deepai_api_key = deepai_api_key
        self.target_dimensions = target_dimensions
        self.deepai_url = "https://api.deepai.org/api/text2img"
        
        print(f"🎨 StoryImageGenerator initialized")
        print(f"📐 Target dimensions: {target_dimensions[0]}x{target_dimensions[1]}")
        
    def generate_and_save_image(self, visual_prompt: str, scene_number: int, output_dir: str = ".") -> str:
        """
        Generate image from visual prompt and save to file
        
        Args:
            visual_prompt: The visual description for the image
            scene_number: Scene number for filename
            output_dir: Directory to save the image (default: current directory)
            
        Returns:
            Path to saved image file
        """
        try:
            print(f"\n🖼️ Generating image for scene {scene_number}...")
            print(f"📝 Prompt: {visual_prompt[:100]}...")
            
            # Enhance prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            # Make request to DeepAI
            print(f"🌐 Sending request to DeepAI...")
            response = requests.post(
                self.deepai_url,
                data={'text': enhanced_prompt},
                headers={'api-key': self.deepai_api_key},
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"DeepAI API request failed with status {response.status_code}: {response.text}")
            
            result = response.json()
            
            if 'output_url' not in result:
                raise Exception(f"No output_url in DeepAI response: {result}")
            
            image_url = result['output_url']
            print(f"✅ DeepAI generated image URL: {image_url}")
            
            # Download the image
            print(f"⬇️ Downloading image...")
            image_response = requests.get(image_url, timeout=30)
            if image_response.status_code != 200:
                raise Exception(f"Failed to download image from {image_url}")
            
            # Process and resize image
            print(f"🔄 Processing and resizing to {self.target_dimensions[0]}x{self.target_dimensions[1]}...")
            image_data = self._process_image(image_response.content)
            
            # Save image to file
            filename = f"scene_{scene_number}_colored.jpg"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            print(f"✅ Image saved: {filepath} ({len(image_data)} bytes)")
            return filepath
            
        except Exception as e:
            print(f"❌ Error generating image for scene {scene_number}: {str(e)}")
            # Create placeholder image on error
            placeholder_path = self._create_placeholder(scene_number, output_dir)
            return placeholder_path
    
    def _process_image(self, image_data: bytes) -> bytes:
        """
        Process and resize image to target dimensions
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Processed image bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Resize to target dimensions
            resized_image = image.resize(self.target_dimensions, Image.LANCZOS)
            
            # Convert to RGB if needed for JPEG compatibility
            if resized_image.mode in ('RGBA', 'LA', 'P'):
                resized_image = resized_image.convert('RGB')
            
            # Save to bytes
            output_buffer = io.BytesIO()
            resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"⚠️ Image processing error: {e}")
            raise
    
    def _create_placeholder(self, scene_number: int, output_dir: str) -> str:
        """
        Create a placeholder image when generation fails
        
        Args:
            scene_number: Scene number for filename
            output_dir: Directory to save the placeholder
            
        Returns:
            Path to placeholder image
        """
        try:
            width, height = self.target_dimensions
            
            # Create placeholder image
            image = Image.new('RGB', (width, height), color='#f0f0f0')
            
            # Add text if possible
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(image)
                
                text = f"Scene {scene_number}\nImage\nPlaceholder"
                text_bbox = draw.textbbox((0, 0), text)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                draw.text((x, y), text, fill='#666666')
            except:
                pass  # Skip text if font issues
            
            # Save placeholder
            filename = f"scene_{scene_number}_colored.jpg"
            filepath = os.path.join(output_dir, filename)
            
            image.save(filepath, format='JPEG', quality=85)
            
            print(f"📝 Placeholder created: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Failed to create placeholder: {e}")
            return ""
    
    def generate_story_images(self, scenes_data: List[Dict], output_dir: str = ".") -> List[str]:
        """
        Generate images for all story scenes
        
        Args:
            scenes_data: List of scene dictionaries with visual_prompt and scene_number
            output_dir: Directory to save images
            
        Returns:
            List of generated image file paths
        """
        print(f"\n🚀 Starting batch image generation for {len(scenes_data)} scenes...")
        print(f"📁 Output directory: {output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = []
        
        for i, scene in enumerate(scenes_data, 1):
            try:
                visual_prompt = scene.get('visual_prompt', f'Scene {i} illustration')
                scene_number = scene.get('scene_number', i)
                
                print(f"\n--- Processing Scene {scene_number} ({i}/{len(scenes_data)}) ---")
                
                filepath = self.generate_and_save_image(
                    visual_prompt, 
                    scene_number, 
                    output_dir
                )
                
                generated_files.append(filepath)
                
                # Add delay between requests to be respectful to API
                if i < len(scenes_data):
                    print(f"⏳ Waiting 2 seconds before next request...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"❌ Failed to process scene {i}: {e}")
                continue
        
        print(f"\n🎉 Batch generation completed!")
        print(f"✅ Generated {len(generated_files)} images")
        print(f"📁 Files saved in: {output_dir}")
        
        return generated_files


def main():
    """Main function to generate images for the Princess Nova story"""
    
    # TODO: Replace with your actual DeepAI API key
    DEEPAI_API_KEY = "796f220f-b6f4-485d-ac1f-318797f11640"
    
    if DEEPAI_API_KEY == "YOUR_DEEPAI_API_KEY_HERE":
        print("❌ Please set your DeepAI API key in the script!")
        print("🔑 Get your API key from: https://deepai.org/")
        return
    
    # Story scenes data extracted from your Firestore document
    scenes_data = [
        {
            "scene_number": 3,
            "text": "Upon arrival, Princess Nova met Sukh Jr. at his favorite place, the basketball court. He showed her his basketball moves and explained to her how machine learning can use data to predict the best shots.",
            "visual_prompt": "Anime style scene showing Sukh Jr. and Princess Nova at a basketball court. Sukh Jr. is demonstrating a jump shot while Princess Nova watches and listens attentively. A holographic screen shows data and graphs related to Sukh's basketball moves."
        },
    ]
    
    # Initialize image generator with 240x320 dimensions
    generator = StoryImageGenerator(
        deepai_api_key=DEEPAI_API_KEY,
        target_dimensions=(320, 240)
    )
    
    print("📚 Princess Nova and Sukh Jr.'s Space Adventure - Image Generation")
    print("=" * 60)
    
    # Generate images for all scenes
    generated_files = generator.generate_story_images(
        scenes_data=scenes_data,
        output_dir="."  # Save in current directory
    )
    
    print("\n" + "=" * 60)
    print("🎯 Generation Summary:")
    for i, filepath in enumerate(generated_files, 1):
        if filepath:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            print(f"  Scene {i}: {filename} ({file_size:,} bytes)")
        else:
            print(f"  Scene {i}: ❌ Failed to generate")
    
    print(f"\n🎉 All done! Check the current directory for your story images.")


if __name__ == "__main__":
    main()
