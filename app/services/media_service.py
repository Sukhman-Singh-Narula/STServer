# ===== app/services/media_service.py - OPTIMIZED WITH BATCH PROCESSING AND REPLICATE =====
import io
import json
import time
import base64
import asyncio
import aiohttp
import requests
from typing import Union, List, Dict
from fastapi import HTTPException
from openai import OpenAI
import replicate
from app.config import settings
from app.services.storage_service import StorageService
from PIL import Image

class MediaService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        # Configure Replicate with API token - try multiple methods
        print(f"🔧 Loading Replicate API token: {settings.replicate_api_token[:10]}..." if settings.replicate_api_token else "❌ No Replicate API token found!")
        
        # Method 1: Set via replicate.api_token
        replicate.api_token = settings.replicate_api_token
        
        # Method 2: Also set as environment variable as backup
        import os
        os.environ["REPLICATE_API_TOKEN"] = settings.replicate_api_token
        
        # Method 3: Create client with explicit token
        self.replicate_client = replicate
        
        print(f"🔧 Replicate token set via multiple methods. Testing authentication...")
        # Test token by checking if it's accessible
        try:
            # This should trigger authentication check
            current_token = replicate.api_token
            print(f"✅ Replicate token accessible: {current_token[:10]}..." if current_token else "❌ No token in replicate.api_token")
        except Exception as e:
            print(f"❌ Error accessing replicate token: {e}")
    
    async def swap_face_deepimage(self, target_image_bytes: bytes, source_image_url: str) -> bytes:
        """
        Swap face using Deep-Image AI API with face swapping
        target_image_bytes: The generated story image where we want to swap the face
        source_image_url: The Firebase URL of the child's reference image
        Returns: The face-swapped image as bytes
        """
        try:
            print(f"🔄 Starting face swap with Deep-Image AI API...")
            print(f"   Target image size: {len(target_image_bytes)} bytes")
            print(f"   Source image URL: {source_image_url[:50]}...")
            
            # First upload the target image to get a URL (instead of using base64)
            # Deep-Image works better with URLs than base64
            temp_storage = StorageService()
            
            # Upload target image temporarily to get a URL
            target_filename = f"temp/faceswap_target_{int(time.time())}.jpg"
            target_url = await temp_storage.upload_image(target_image_bytes, target_filename, "image/jpeg")
            
            print(f"   Uploaded target image: {target_url[:50]}...")
            
            # Prepare the API request according to Deep-Image AI documentation
            url = "https://deep-image.ai/rest_api/process_result"
            headers = {
                "x-api-key": settings.deepimage_api_key,
                "Content-Type": "application/json"
            }
            
            # Use the correct format for face swapping with Deep-Image AI
            payload = {
                "url": target_url,  # Target image URL (from Firebase)
                "background": {
                    "generate": {
                        "strength": 0.1,  # Low strength to preserve the scene but swap face
                        "adapter_type": "face",
                        "avatar_generation_type": "creative_img2img",
                        "ip_image2": source_image_url  # Source face image (Firebase URL)
                    }
                }
            }
            
            print(f"   Sending request to Deep-Image API...")
            print(f"   Payload: {json.dumps(payload, indent=2)}")
            
            # Make async HTTP request
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    print(f"   Deep-Image API response status: {response.status}")
                    print(f"   Deep-Image API response: {response_text[:200]}...")
                    
                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                            
                            # Check if we got a result URL directly
                            if 'result_url' in result or 'url' in result:
                                result_url = result.get('result_url') or result.get('url')
                                
                                print(f"   Got result URL: {result_url[:50]}...")
                                
                                # Download the result image
                                async with session.get(result_url) as img_response:
                                    if img_response.status == 200:
                                        swapped_image_bytes = await img_response.read()
                                        print(f"✅ Face swap completed: {len(swapped_image_bytes)} bytes")
                                        
                                        # Clean up temporary target image
                                        try:
                                            await temp_storage.delete_file(target_filename)
                                        except:
                                            pass  # Ignore cleanup errors
                                        
                                        return swapped_image_bytes
                                    else:
                                        raise Exception(f"Failed to download result image: {img_response.status}")
                            
                            # Check if we need to poll for a job
                            elif 'job' in result or 'job_id' in result:
                                job_id = result.get('job') or result.get('job_id')
                                print(f"   Got job ID: {job_id}, polling for completion...")
                                
                                # Poll for completion (max 30 seconds)
                                max_polls = 30
                                poll_count = 0
                                
                                while poll_count < max_polls:
                                    await asyncio.sleep(1)
                                    poll_count += 1
                                    
                                    # Check job status
                                    status_url = f"https://deep-image.ai/rest_api/result/{job_id}"
                                    async with session.get(status_url, headers=headers) as status_response:
                                        if status_response.status == 200:
                                            status_text = await status_response.text()
                                            status_result = json.loads(status_text)
                                            
                                            if status_result.get('status') == 'complete' or 'result_url' in status_result or 'url' in status_result:
                                                result_url = status_result.get('result_url') or status_result.get('url')
                                                if result_url:
                                                    print(f"   Job completed, downloading result...")
                                                    
                                                    # Download the result image
                                                    async with session.get(result_url) as img_response:
                                                        if img_response.status == 200:
                                                            swapped_image_bytes = await img_response.read()
                                                            print(f"✅ Face swap completed after {poll_count}s: {len(swapped_image_bytes)} bytes")
                                                            
                                                            # Clean up temporary target image
                                                            try:
                                                                await temp_storage.delete_file(target_filename)
                                                            except:
                                                                pass
                                                            
                                                            return swapped_image_bytes
                                                        else:
                                                            raise Exception(f"Failed to download result image: {img_response.status}")
                                                else:
                                                    raise Exception("Job completed but no result_url provided")
                                            
                                            elif status_result.get('status') in ['received', 'in_progress', 'processing', 'not_started']:
                                                # Still processing, continue polling
                                                continue
                                            else:
                                                # Error status
                                                raise Exception(f"Job failed with status: {status_result.get('status')} - {status_result.get('message', 'Unknown error')}")
                                        else:
                                            print(f"   Failed to check job status: {status_response.status}")
                                            continue
                                
                                # Timeout
                                print(f"⚠️ Face swap job timed out after {max_polls} seconds")
                                raise Exception("Face swap job timed out")
                            
                            else:
                                # Unknown response format
                                raise Exception(f"Unexpected response format from Deep-Image API: {result}")
                        
                        except json.JSONDecodeError:
                            raise Exception(f"Invalid JSON response from Deep-Image API: {response_text}")
                    
                    else:
                        # API error
                        raise Exception(f"Deep-Image API error {response.status}: {response_text}")
                        
        except Exception as e:
            print(f"❌ Face swap error: {str(e)}")
            # Return original image if face swap fails
            return target_image_bytes
            print("🔄 Returning original image due to face swap failure")
            return target_image_bytes
    
    async def generate_audio_batch(self, scene_texts: List[Dict], isfemale: bool = True) -> List[bytes]:
        """Generate audio for multiple scenes in parallel using OpenAI TTS"""
        try:
            print(f"🎵 Starting OpenAI TTS batch audio generation for {len(scene_texts)} scenes...")
            print(f"🎤 Using {'female' if isfemale else 'male'} voice")
            return await self.generate_audio_batch_openai(scene_texts, isfemale=isfemale)
            
        except Exception as e:
            print(f"❌ Batch audio generation error: {str(e)}")
            raise e
    
    async def generate_audio_batch_openai(self, scene_texts: List[Dict], isfemale: bool = True) -> List[bytes]:
        """Batch audio generation using OpenAI TTS (full parallel processing)"""
        try:
            voice = "sage" if isfemale else "onyx"  # Female = sage, Male = onyx
            print(f"🎵 Using OpenAI TTS batch processing for {len(scene_texts)} scenes")
            print(f"🎤 Voice selected: {voice} ({'female' if isfemale else 'male'})")
            
            async def generate_single_audio_openai(scene_data):
                """Generate audio for a single scene using OpenAI TTS"""
                text = scene_data['text']
                scene_number = scene_data['scene_number']
                
                try:
                    # Run OpenAI TTS generation in thread pool
                    loop = asyncio.get_event_loop()
                    
                    def create_tts():
                        response = self.openai_client.audio.speech.create(
                            model="tts-1",  # Standard model
                            voice=voice,   # Dynamic voice based on isfemale parameter
                            input=text,
                            response_format="wav"  # Changed from mp3 to wav
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
    
    async def generate_image_batch(self, visual_prompts: List[Dict], child_image_url: str = None) -> List[bytes]:
        """Generate images for multiple scenes in parallel using Replicate SDXL (face swapping temporarily disabled)"""
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
                                    # Ensure token is set right before the call
                                    replicate.api_token = settings.replicate_api_token
                                    
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
                            
                            # Get the first output URL and download it
                            if output and len(output) > 0:
                                image_url = output[0]  # First image URL
                                print(f"📥 Downloading image from: {image_url}")
                                
                                # Download the image
                                response = requests.get(image_url, timeout=30)
                                if response.status_code == 200:
                                    image_data = response.content
                                else:
                                    raise Exception(f"Failed to download image: HTTP {response.status_code}")
                            else:
                                raise Exception("No output generated from Replicate")
                            
                            # Resize from 512x512 to 304x304 using PIL
                            image = Image.open(io.BytesIO(image_data))
                            resized_image = image.resize((304, 304), Image.LANCZOS)
                            
                            # Save resized image back to bytes - ALWAYS as JPEG
                            output_buffer = io.BytesIO()
                            # Force JPEG format for all images
                            # Convert RGBA to RGB if needed for JPEG compatibility
                            if resized_image.mode in ('RGBA', 'LA', 'P'):
                                resized_image = resized_image.convert('RGB')
                            
                            resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
                            
                            return output_buffer.getvalue()
                        
                        image_data = await loop.run_in_executor(None, create_image)
                        
                        # Apply face swapping if child image URL is provided
                        # TEMPORARILY DISABLED - keeping code for future use
                        if child_image_url and False:  # Disabled face swap
                            print(f"🔄 Applying face swap for scene {scene_number}...")
                            image_data = await self.swap_face_deepimage(image_data, child_image_url)
                            print(f"✅ Face swap completed for scene {scene_number}")
                        elif child_image_url:
                            print(f"⚠️ Face swap temporarily disabled for scene {scene_number}")
                        
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
    
    async def generate_audio(self, text: str, scene_number: int, isfemale: bool = True) -> bytes:
        """Generate audio using OpenAI TTS (individual scene - fallback method)"""
        return await self.generate_audio_openai(text, scene_number, isfemale=isfemale)
    
    async def generate_audio_openai(self, text: str, scene_number: int, isfemale: bool = True) -> bytes:
        """Fallback: Generate audio using OpenAI Text-to-Speech"""
        try:
            voice = "sage" if isfemale else "onyx"  # Female = sage, Male = onyx
            print(f"🎵 Using OpenAI TTS for scene {scene_number}")
            print(f"🎤 Voice selected: {voice} ({'female' if isfemale else 'male'})")
            
            response = self.openai_client.audio.speech.create(
                model="tts-1",  # Standard model
                voice=voice,   # Dynamic voice based on isfemale parameter
                input=text,
                response_format="wav"  # Changed from mp3 to wav
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
            
            # Save back to bytes - ALWAYS as JPEG
            output_buffer = io.BytesIO()
            
            # Force JPEG format for all images
            # Convert to RGB if needed for JPEG compatibility
            if grayscale_image.mode in ('RGBA', 'LA', 'P'):
                grayscale_image = grayscale_image.convert('RGB')
            
            # Save grayscale image as JPEG
            grayscale_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            
            grayscale_data = output_buffer.getvalue()
            
            print(f"✅ Image converted and resized: {len(image_data)} → {len(grayscale_data)} bytes ({target_size[0]}x{target_size[1]} grayscale)")
            return grayscale_data
            
        except Exception as e:
            print(f"❌ Image conversion/resize failed: {str(e)}")
            print(f"🔄 Returning original image data")
            return image_data  # Return original if conversion fails
    
    async def generate_image_replicate(self, visual_prompt: str, scene_number: int, child_image_url: str = None) -> bytes:
        """Generate image using Replicate SDXL at 512x512 then resize to 304x304 (face swapping temporarily disabled)"""
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
                # Ensure token is set right before the call
                replicate.api_token = settings.replicate_api_token
                
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
            
            # Apply face swapping if child image URL is provided
            # TEMPORARILY DISABLED - keeping code for future use
            if child_image_url and False:  # Disabled face swap
                print(f"🔄 Applying face swap for scene {scene_number}...")
                resized_image_data = await self.swap_face_deepimage(resized_image_data, child_image_url)
                print(f"✅ Face swap completed for scene {scene_number}")
            elif child_image_url:
                print(f"⚠️ Face swap temporarily disabled for scene {scene_number}")
            
            print(f"✅ Replicate SDXL image generated and resized for scene {scene_number}: {len(resized_image_data)} bytes (304x304)")
            return resized_image_data
            
        except Exception as e:
            print(f"❌ Replicate SDXL error for scene {scene_number}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Replicate SDXL image generation failed for scene {scene_number}: {str(e)}"
            )
    
    async def generate_image(self, visual_prompt: str, scene_number: int, child_image_url: str = None) -> bytes:
        """Generate image using Replicate SDXL (face swapping temporarily disabled - main method)"""
        return await self.generate_image_replicate(visual_prompt, scene_number, child_image_url)