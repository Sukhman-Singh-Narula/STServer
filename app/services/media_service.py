# ===== app/services/media_service.py - OPTIMIZED WITH BATCH PROCESSING AND REPLICATE =====
import io
import base64
import asyncio
from typing import Union, List, Dict
from fastapi import HTTPException
from openai import OpenAI
import replicate
from app.config import settings
from PIL import Image

class MediaService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        # Configure Replicate with API token
        replicate.api_token = settings.replicate_api_token
    
    async def generate_audio_batch(self, scene_texts: List[Dict]) -> List[bytes]:
        """Generate audio for multiple scenes in parallel using OpenAI TTS"""
        try:
            print(f"🎵 Starting OpenAI TTS batch audio generation for {len(scene_texts)} scenes...")
            return await self.generate_audio_batch_openai(scene_texts)
            
        except Exception as e:
            print(f"❌ Batch audio generation error: {str(e)}")
            raise e
    
    async def generate_audio_batch_openai(self, scene_texts: List[Dict]) -> List[bytes]:
        """Batch audio generation using OpenAI TTS (full parallel processing)"""
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
                            model="gpt-4o-mini-tts",  # Faster model
                            voice="coral",   # Child-friendly voice
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
            
            # Create tasks for full parallel processing (no concurrency limits)
            tasks = [generate_single_audio_openai(scene_data) for scene_data in scene_texts]
            
            # Execute ALL audio generation tasks simultaneously
            print(f"🚀 Starting FULL parallel audio generation (all {len(tasks)} at once)...")
            audio_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=120.0  # 2 minutes total timeout for all audio
            )
            
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
            
        except asyncio.TimeoutError:
            print(f"❌ OpenAI audio batch timed out after 2 minutes")
            raise HTTPException(status_code=500, detail="Audio generation timed out")
        except Exception as e:
            print(f"❌ OpenAI batch processing failed: {str(e)}")
            raise e
    
    async def generate_image_batch(self, visual_prompts: List[Dict]) -> List[bytes]:
        """Generate images for multiple scenes in parallel using Replicate SDXL (with concurrency control)"""
        try:
            print(f"🖼️ Starting Replicate SDXL batch image generation for {len(visual_prompts)} scenes...")
            
            # Create semaphore to limit concurrent requests (avoid GPU memory issues)
            semaphore = asyncio.Semaphore(1)  # Max 1 concurrent image request to prevent CUDA OOM
            
            async def generate_single_image_replicate(prompt_data):
                """Generate image for a single scene using Replicate SDXL"""
                visual_prompt = prompt_data['visual_prompt']
                scene_number = prompt_data['scene_number']
                
                async with semaphore:  # Limit concurrency
                    try:
                        # Run Replicate generation in thread pool
                        loop = asyncio.get_event_loop()
                        
                        def create_image():
                            # Enhance the prompt for children's book style
                            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
                            
                            # Replicate SDXL input configuration - generate at 1024x1024 for best quality
                            input_config = {
                                "width": 512,  # Reduced from 1024 for memory optimization
                                "height": 512,
                                "prompt": enhanced_prompt,
                                "refine": "expert_ensemble_refiner",
                                "apply_watermark": False,
                                "num_inference_steps": 15  # Reduced for memory optimization
                            }
                            
                            # Generate image using Replicate SDXL with retry for CUDA errors
                            max_retries = 3
                            for attempt in range(max_retries):
                                try:
                                    output = replicate.run(
                                        "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                                        input=input_config
                                    )
                                    break  # Success, exit retry loop
                                except Exception as e:
                                    if "CUDA out of memory" in str(e) and attempt < max_retries - 1:
                                        print(f"🔄 CUDA memory error on attempt {attempt + 1}, retrying in 10 seconds...")
                                        import time
                                        time.sleep(10)  # Wait for GPU memory to clear
                                        continue
                                    else:
                                        raise e  # Re-raise if not CUDA error or max retries reached
                            
                            # Get the first output and read as bytes
                            for item in output:
                                image_data = item.read()
                                break
                            else:
                                raise Exception("No output generated from Replicate")
                            
                            # Resize from 512x512 to 304x304 using PIL
                            image = Image.open(io.BytesIO(image_data))
                            resized_image = image.resize((304, 304), Image.LANCZOS)
                            
                            # Save resized image back to bytes
                            output_buffer = io.BytesIO()
                            format = image.format if image.format else 'JPEG'
                            if format not in ['JPEG', 'PNG']:
                                format = 'JPEG'
                            
                            if format == 'JPEG':
                                resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
                            else:
                                resized_image.save(output_buffer, format=format, optimize=True)
                            
                            return output_buffer.getvalue()
                        
                        image_data = await loop.run_in_executor(None, create_image)
                        
                        print(f"✅ Replicate SDXL color image generated for scene {scene_number}: {len(image_data)} bytes")
                        return image_data
                        
                    except Exception as e:
                        print(f"❌ Replicate SDXL batch error for scene {scene_number}: {str(e)}")
                        raise e
            
            # Create tasks for parallel processing
            tasks = [generate_single_image_replicate(prompt_data) for prompt_data in visual_prompts]
            
            # Execute all image generation tasks in parallel with timeout
            print(f"⏰ Starting controlled parallel image generation (max 2 concurrent)...")
            image_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=240.0  # 4 minutes total timeout for all images
            )
            
            # Check for any failures and collect successful results
            image_batch = []
            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    print(f"❌ Replicate SDXL batch failed for scene {i+1}: {result}")
                    raise result
                else:
                    image_batch.append(result)
            
            print(f"✅ Replicate SDXL batch image generation completed: {len(image_batch)} files")
            return image_batch
            
        except asyncio.TimeoutError:
            print(f"❌ Replicate SDXL image batch timed out after 4 minutes")
            raise HTTPException(status_code=500, detail="Image generation timed out")
        except Exception as e:
            print(f"❌ Replicate SDXL batch processing failed: {str(e)}")
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
    
    def convert_image_to_grayscale_and_resize(self, image_data: bytes, target_size: tuple = (960, 540)) -> bytes:
        """Convert image to grayscale and resize to target resolution using PIL"""
        try:
            print(f"🎨 Converting image to grayscale and resizing to {target_size[0]}x{target_size[1]}...")
            
            # Load image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Resize image to target size (960x540) using high-quality resampling
            resized_image = image.resize(target_size, Image.LANCZOS)
            
            # Convert to grayscale
            grayscale_image = resized_image.convert('L')
            
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
            
            print(f"✅ Image converted and resized: {len(image_data)} → {len(grayscale_data)} bytes ({target_size[0]}x{target_size[1]} grayscale)")
            return grayscale_data
            
        except Exception as e:
            print(f"❌ Image conversion/resize failed: {str(e)}")
            print(f"🔄 Returning original image data")
            return image_data  # Return original if conversion fails
    
    async def generate_image_replicate(self, visual_prompt: str, scene_number: int) -> bytes:
        """Generate image using Replicate SDXL at 1024x1024 then resize to 304x304 (main method)"""
        try:
            print(f"🖼️ Generating image for scene {scene_number} with Replicate SDXL (1024x1024 → 304x304)")
            
            # Enhance the prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            # Replicate SDXL input configuration - generate at 1024x1024 for best quality
            input_config = {
                "width": 512,  # Reduced from 1024 for memory optimization
                "height": 512,
                "prompt": enhanced_prompt,
                "refine": "expert_ensemble_refiner",
                "apply_watermark": False,
                "num_inference_steps": 15  # Reduced for memory optimization
            }
            
            # Run Replicate generation in thread pool
            loop = asyncio.get_event_loop()
            
            def create_and_resize_image():
                # Generate image using Replicate SDXL
                output = replicate.run(
                    "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc",
                    input=input_config
                )
                
                # Get the first output and read as bytes
                for item in output:
                    image_data = item.read()
                    break
                else:
                    raise Exception("No output generated from Replicate")
                
                # Resize from 1024x1024 to 304x304 using PIL
                image = Image.open(io.BytesIO(image_data))
                resized_image = image.resize((304, 304), Image.LANCZOS)
                
                # Save resized image back to bytes
                output_buffer = io.BytesIO()
                format = image.format if image.format else 'JPEG'
                if format not in ['JPEG', 'PNG']:
                    format = 'JPEG'
                
                if format == 'JPEG':
                    resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
                else:
                    resized_image.save(output_buffer, format=format, optimize=True)
                
                return output_buffer.getvalue()
            
            # Execute in thread pool
            resized_image_data = await loop.run_in_executor(None, create_and_resize_image)
            
            print(f"✅ Replicate SDXL image generated and resized for scene {scene_number}: {len(resized_image_data)} bytes (304x304)")
            return resized_image_data
            
        except Exception as e:
            print(f"❌ Replicate SDXL error for scene {scene_number}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Replicate SDXL image generation failed for scene {scene_number}: {str(e)}"
            )
    
    async def generate_image(self, visual_prompt: str, scene_number: int) -> bytes:
        """Generate image using Replicate SDXL (main method)"""
        return await self.generate_image_replicate(visual_prompt, scene_number)