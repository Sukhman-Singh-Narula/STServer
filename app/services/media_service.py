# ===== app/services/media_service.py - OPTIMIZED WITH BATCH PROCESSING AND DALL-E 2 =====
import io
import base64
import asyncio
from typing import Union, List, Dict
from fastapi import HTTPException
from openai import OpenAI
from app.config import settings
from PIL import Image

class MediaService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
    
    async def generate_audio_batch(self, scene_texts: List[Dict]) -> List[bytes]:
        """Generate audio for multiple scenes in parallel using OpenAI TTS"""
        try:
            print(f"🎵 Starting OpenAI TTS batch audio generation for {len(scene_texts)} scenes...")
            return await self.generate_audio_batch_openai(scene_texts)
            
        except Exception as e:
            print(f"❌ Batch audio generation error: {str(e)}")
            raise e
    
    async def generate_audio_batch_openai(self, scene_texts: List[Dict]) -> List[bytes]:
        """Batch audio generation using OpenAI TTS (parallel processing)"""
        try:
            print(f"🎵 Using OpenAI TTS batch processing for {len(scene_texts)} scenes")
            
            async def generate_single_audio_openai(scene_data):
                """Generate audio for a single scene using OpenAI TTS"""
                text = scene_data['text']
                scene_number = scene_data['scene_number']
                
                try:
                    # Run OpenAI TTS generation in thread pool
                    loop = asyncio.get_event_loop()
                    
                    def create_tts():
                        response = self.openai_client.audio.speech.create(
                            model="tts-1",  # Faster model
                            voice="nova",   # Child-friendly voice
                            input=text,
                            response_format="mp3"
                        )
                        
                        # Convert response to bytes
                        audio_bytes = b""
                        for chunk in response.iter_bytes():
                            audio_bytes += chunk
                        return audio_bytes
                    
                    audio_data = await loop.run_in_executor(None, create_tts)
                    
                    print(f"✅ OpenAI audio generated for scene {scene_number}: {len(audio_data)} bytes")
                    return audio_data
                    
                except Exception as e:
                    print(f"❌ OpenAI TTS error for scene {scene_number}: {str(e)}")
                    raise e
            
            # Create tasks for parallel processing
            tasks = [generate_single_audio_openai(scene_data) for scene_data in scene_texts]
            
            # Execute all audio generation tasks in parallel
            audio_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for any failures and collect successful results
            audio_batch = []
            for i, result in enumerate(audio_results):
                if isinstance(result, Exception):
                    print(f"❌ OpenAI batch failed for scene {i+1}: {result}")
                    raise result
                else:
                    audio_batch.append(result)
            
            print(f"✅ OpenAI batch audio generation completed: {len(audio_batch)} files")
            return audio_batch
            
        except Exception as e:
            print(f"❌ OpenAI batch processing failed: {str(e)}")
            raise e
    
    async def generate_image_batch(self, visual_prompts: List[Dict]) -> List[bytes]:
        """Generate images for multiple scenes in parallel using DALL-E 2"""
        try:
            print(f"🖼️ Starting DALL-E 2 batch image generation for {len(visual_prompts)} scenes...")
            
            async def generate_single_image_dalle2(prompt_data):
                """Generate image for a single scene using DALL-E 2"""
                visual_prompt = prompt_data['visual_prompt']
                scene_number = prompt_data['scene_number']
                
                try:
                    # Run DALL-E 2 generation in thread pool
                    loop = asyncio.get_event_loop()
                    
                    def create_image():
                        # Enhance the prompt for children's book style
                        enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
                        
                        # Use DALL-E 2 for faster generation
                        response = self.openai_client.images.generate(
                            model="dall-e-2",  # Much faster than DALL-E 3
                            prompt=enhanced_prompt,
                            size=settings.image_size,  # Keep original size (1792x1024)
                            n=1,
                            response_format="b64_json"  # Get base64 data instead of URL
                        )
                        
                        # Extract base64 image data
                        image_b64 = response.data[0].b64_json
                        image_data = base64.b64decode(image_b64)
                        
                        return image_data
                    
                    image_data = await loop.run_in_executor(None, create_image)
                    
                    print(f"✅ DALL-E 2 color image generated for scene {scene_number}: {len(image_data)} bytes")
                    
                    # Convert to grayscale
                    grayscale_image_data = self.convert_image_to_grayscale(image_data)
                    
                    print(f"✅ Final grayscale image ready for scene {scene_number}: {len(grayscale_image_data)} bytes")
                    return grayscale_image_data
                    
                except Exception as e:
                    print(f"❌ DALL-E 2 batch error for scene {scene_number}: {str(e)}")
                    raise e
            
            # Create tasks for parallel processing
            tasks = [generate_single_image_dalle2(prompt_data) for prompt_data in visual_prompts]
            
            # Execute all image generation tasks in parallel
            image_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for any failures and collect successful results
            image_batch = []
            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    print(f"❌ DALL-E 2 batch failed for scene {i+1}: {result}")
                    raise result
                else:
                    image_batch.append(result)
            
            print(f"✅ DALL-E 2 batch image generation completed: {len(image_batch)} files")
            return image_batch
            
        except Exception as e:
            print(f"❌ DALL-E 2 batch processing failed: {str(e)}")
            raise e
        """Batch audio generation using OpenAI TTS (parallel processing)"""
        try:
            print(f"🎵 Using OpenAI TTS batch processing for {len(scene_texts)} scenes")
            
            async def generate_single_audio_openai(scene_data):
                """Generate audio for a single scene using OpenAI TTS"""
                text = scene_data['text']
                scene_number = scene_data['scene_number']
                
                try:
                    # Run OpenAI TTS generation in thread pool
                    loop = asyncio.get_event_loop()
                    
                    def create_tts():
                        response = self.openai_client.audio.speech.create(
                            model="tts-1",  # Faster model
                            voice="nova",   # Child-friendly voice
                            input=text,
                            response_format="mp3"
                        )
                        
                        # Convert response to bytes
                        audio_bytes = b""
                        for chunk in response.iter_bytes():
                            audio_bytes += chunk
                        return audio_bytes
                    
                    audio_data = await loop.run_in_executor(None, create_tts)
                    
                    print(f"✅ OpenAI audio generated for scene {scene_number}: {len(audio_data)} bytes")
                    return audio_data
                    
                except Exception as e:
                    print(f"❌ OpenAI TTS error for scene {scene_number}: {str(e)}")
                    raise e
            
            # Create tasks for parallel processing
            tasks = [generate_single_audio_openai(scene_data) for scene_data in scene_texts]
            
            # Execute all audio generation tasks in parallel
            audio_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for any failures and collect successful results
            audio_batch = []
            for i, result in enumerate(audio_results):
                if isinstance(result, Exception):
                    print(f"❌ OpenAI batch failed for scene {i+1}: {result}")
                    raise result
                else:
                    audio_batch.append(result)
            
            print(f"✅ OpenAI batch audio generation completed: {len(audio_batch)} files")
            return audio_batch
            
        except Exception as e:
            print(f"❌ OpenAI batch processing failed: {str(e)}")
            raise e
    
    async def generate_audio(self, text: str, scene_number: int) -> bytes:
        """Generate audio using OpenAI TTS (individual scene - fallback method)"""
        return await self.generate_audio_openai(text, scene_number)
    
    async def generate_audio_openai(self, text: str, scene_number: int) -> bytes:
        """Fallback: Generate audio using OpenAI Text-to-Speech"""
        try:
            print(f"🎵 Using OpenAI TTS for scene {scene_number}")
            
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # Faster model
                voice="nova",   # Child-friendly voice
                input=text,
                response_format="mp3"
            )
            
            # Convert response to bytes
            audio_bytes = b""
            for chunk in response.iter_bytes():
                audio_bytes += chunk
                
            print(f"✅ OpenAI audio generated for scene {scene_number}: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            print(f"❌ OpenAI TTS error for scene {scene_number}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Audio generation failed for scene {scene_number}: {str(e)}"
            )
    
    def convert_image_to_grayscale(self, image_data: bytes) -> bytes:
        """Convert image to grayscale using PIL"""
        try:
            print(f"🎨 Converting image to grayscale...")
            
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to grayscale
            grayscale_image = image.convert('L')
            
            # Save back to bytes
            output_buffer = io.BytesIO()
            
            # Determine format from original image
            format = image.format if image.format else 'JPEG'
            if format not in ['JPEG', 'PNG']:
                format = 'JPEG'  # Default to JPEG for unsupported formats
            
            # Save grayscale image
            if format == 'JPEG':
                grayscale_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            else:
                grayscale_image.save(output_buffer, format=format, optimize=True)
            
            grayscale_data = output_buffer.getvalue()
            
            print(f"✅ Image converted to grayscale: {len(image_data)} → {len(grayscale_data)} bytes")
            return grayscale_data
            
        except Exception as e:
            print(f"❌ Grayscale conversion failed: {str(e)}")
            print(f"🔄 Returning original image data")
            return image_data  # Return original if conversion fails
    
    async def generate_image_dalle2(self, visual_prompt: str, scene_number: int) -> bytes:
        """Generate image using DALL-E 2 for speed (optimized method)"""
        try:
            print(f"🖼️ Generating image for scene {scene_number} with DALL-E 2 (optimized)")
            
            # Enhance the prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            # Use DALL-E 2 for faster generation (keeping original image size)
            response = self.openai_client.images.generate(
                model="dall-e-2",  # Much faster than DALL-E 3
                prompt=enhanced_prompt,
                size=settings.image_size,  # Keep original size (1792x1024 or 960x540)
                n=1,
                response_format="b64_json"  # Get base64 data instead of URL
            )
            
            # Extract base64 image data
            image_b64 = response.data[0].b64_json
            image_data = base64.b64decode(image_b64)
            
            print(f"✅ DALL-E 2 color image generated for scene {scene_number}: {len(image_data)} bytes")
            
            # Convert to grayscale
            grayscale_image_data = self.convert_image_to_grayscale(image_data)
            
            print(f"✅ Final grayscale image ready for scene {scene_number}: {len(grayscale_image_data)} bytes")
            return grayscale_image_data
            
        except Exception as e:
            print(f"❌ DALL-E 2 error for scene {scene_number}: {str(e)}")
            
            # Fallback: try URL method if base64 fails
            try:
                print(f"🔄 Trying DALL-E 2 URL fallback method for scene {scene_number}...")
                return await self.generate_image_dalle2_url_fallback(visual_prompt, scene_number)
            except Exception as fallback_error:
                print(f"❌ DALL-E 2 URL fallback also failed: {str(fallback_error)}")
                # Final fallback to DALL-E 3
                try:
                    print(f"🔄 Final fallback: trying DALL-E 3 for scene {scene_number}...")
                    return await self.generate_image_dalle3_fallback(visual_prompt, scene_number)
                except Exception as final_error:
                    print(f"❌ All image generation methods failed: {str(final_error)}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"DALL-E 2 image generation failed for scene {scene_number}: {str(e)}"
                    )
    
    async def generate_image_dalle2_url_fallback(self, visual_prompt: str, scene_number: int) -> bytes:
        """Fallback: Generate image with DALL-E 2 URL method, download, and convert to grayscale"""
        import httpx
        from PIL import Image
        from io import BytesIO

        try:
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            response = self.openai_client.images.generate(
                model="dall-e-2",  # Use DALL-E 2 for speed
                prompt=enhanced_prompt,
                size=settings.image_size,  # Keep original size
                n=1,
                response_format="url"
            )

            image_url = response.data[0].url
            print(f"🔗 DALL-E 2 URL generated, attempting immediate download...")

            # Immediately download with aggressive timeout settings
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                download_response = await client.get(image_url)
                download_response.raise_for_status()
                image_data = download_response.content
                print(f"✅ DALL-E 2 fallback download successful: {len(image_data)} bytes")

                # Convert to grayscale
                grayscale_data = self.convert_image_to_grayscale(image_data)

                return grayscale_data

        except Exception as e:
            print(f"❌ DALL-E 2 fallback method failed: {str(e)}")
            raise e
    
    async def generate_image(self, visual_prompt: str, scene_number: int) -> bytes:
        """Generate image using DALL-E 2 at original size and convert to grayscale (main method)"""
        return await self.generate_image_dalle2(visual_prompt, scene_number)
    
    async def generate_image_dalle3_fallback(self, visual_prompt: str, scene_number: int) -> bytes:
        """Fallback: Generate image with DALL-E 3 URL method (legacy support)"""
        import httpx
        from PIL import Image
        from io import BytesIO

        try:
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=settings.image_size,  # Keep original size
                quality="standard",
                n=1,
                response_format="url"
            )

            image_url = response.data[0].url
            print(f"🔗 DALL-E 3 URL generated, attempting immediate download...")

            # Immediately download with aggressive timeout settings
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                download_response = await client.get(image_url)
                download_response.raise_for_status()
                image_data = download_response.content
                print(f"✅ DALL-E 3 fallback download successful: {len(image_data)} bytes")

                # Convert to grayscale
                grayscale_data = self.convert_image_to_grayscale(image_data)

                return grayscale_data

        except Exception as e:
            print(f"❌ DALL-E 3 fallback method failed: {str(e)}")
            raise e