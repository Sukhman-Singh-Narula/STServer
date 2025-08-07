# ===== app/services/media_service.py - OPTIMIZED WITH BATCH PROCESSING AND DEEPAI =====
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
from app.config import settings
from app.services.storage_service import StorageService
from PIL import Image

class MediaService:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client
        
        # DeepAI Configuration
        self.deepai_api_key = settings.deepai_api_key
        self.deepai_url = "https://api.deepai.org/api/text2img"
        
        print(f"✅ MediaService initialized with DeepAI image generation")
    
    # FACE SWAP FEATURE - COMMENTED OUT FOR NOW (DEEPIMAGE AI)
    # async def swap_face_deepimage(self, target_image_bytes: bytes, source_image_url: str) -> bytes:
    #     """
    #     Swap face using Deep-Image AI API with face swapping
    #     target_image_bytes: The generated story image where we want to swap the face
    #     source_image_url: The Firebase URL of the child's reference image
    #     Returns: The face-swapped image as bytes
    #     """
    #     # Face swap functionality disabled for now - return original image
    #     return target_image_bytes

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
        """Generate images for multiple scenes in parallel using DeepAI (face swapping temporarily disabled)"""
        try:
            print(f"🖼️ Starting DeepAI batch image generation for {len(visual_prompts)} scenes...")
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests to DeepAI
            
            async def generate_single_image_deepai(prompt_data):
                """Generate image for a single scene using DeepAI"""
                visual_prompt = prompt_data['visual_prompt']
                scene_number = prompt_data['scene_number']
                
                async with semaphore:  # Limit concurrency
                    try:
                        # Run DeepAI generation in thread pool
                        loop = asyncio.get_event_loop()
                        
                        def create_image():
                            # Enhance the prompt for children's book style
                            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
                            
                            # Sanitize prompt - limit length and remove problematic characters
                            enhanced_prompt = enhanced_prompt[:500]  # Limit to 500 characters
                            enhanced_prompt = enhanced_prompt.replace('"', "'").replace('\n', ' ').replace('\r', ' ')
                            
                            print(f"🎨 DeepAI prompt for scene {scene_number}: {enhanced_prompt[:100]}...")
                            
                            # DeepAI API request with retry logic
                            max_retries = 2
                            for attempt in range(max_retries):
                                try:
                                    response = requests.post(
                                        self.deepai_url,
                                        data={'text': enhanced_prompt},
                                        headers={'api-key': self.deepai_api_key},
                                        timeout=30
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        if 'output_url' not in result:
                                            raise Exception(f"DeepAI response missing output_url: {result}")
                                        break
                                    else:
                                        if attempt < max_retries - 1:
                                            print(f"⚠️ DeepAI attempt {attempt + 1} failed (status {response.status_code}), retrying...")
                                            time.sleep(2)
                                            continue
                                        else:
                                            raise Exception(f"DeepAI API error {response.status_code}: {response.text}")
                                            
                                except requests.RequestException as e:
                                    if attempt < max_retries - 1:
                                        print(f"⚠️ DeepAI network error attempt {attempt + 1}, retrying...")
                                        time.sleep(2)
                                        continue
                                    else:
                                        raise Exception(f"DeepAI network error: {str(e)}")
                            
                            # Download the generated image
                            image_url = result['output_url']
                            image_response = requests.get(image_url, timeout=30)
                            if image_response.status_code != 200:
                                raise Exception(f"Failed to download image from {image_url}")
                            
                            image_data = image_response.content
                            
                            # Resize to 304x304 using PIL (maintaining existing image processing)
                            image = Image.open(io.BytesIO(image_data))
                            resized_image = image.resize((304, 304), Image.LANCZOS)
                            
                            # Convert RGBA to RGB if needed for JPEG compatibility
                            if resized_image.mode in ('RGBA', 'LA', 'P'):
                                resized_image = resized_image.convert('RGB')
                            
                            # Save resized image back to bytes as JPEG
                            output_buffer = io.BytesIO()
                            resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
                            
                            return output_buffer.getvalue()
                        
                        image_data = await loop.run_in_executor(None, create_image)
                        
                        # Apply face swapping if child image URL is provided
                        # TEMPORARILY DISABLED - keeping code for future use
                        if child_image_url and False:  # Disabled face swap
                            print(f"🔄 Applying face swap for scene {scene_number}...")
                            # image_data = await self.swap_face_deepimage(image_data, child_image_url)
                            print(f"✅ Face swap completed for scene {scene_number}")
                        elif child_image_url:
                            print(f"⚠️ Face swap temporarily disabled for scene {scene_number}")
                        
                        print(f"✅ DeepAI image generated for scene {scene_number}: {len(image_data)} bytes (304x304)")
                        return image_data
                        
                    except Exception as e:
                        print(f"❌ DeepAI batch error for scene {scene_number}: {str(e)}")
                        raise e
            
            # Create tasks for parallel processing
            tasks = [generate_single_image_deepai(prompt_data) for prompt_data in visual_prompts]
            
            # Execute all image generation tasks in parallel with timeout
            print(f"⏰ Starting controlled parallel DeepAI image generation (max 3 concurrent)...")
            image_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300.0  # 5 minutes total timeout for all images
            )
            
            # Check for any failures and collect successful results
            image_batch = []
            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    print(f"❌ DeepAI batch failed for scene {i+1}: {result}")
                    raise result
                else:
                    image_batch.append(result)
            
            print(f"✅ DeepAI batch image generation completed: {len(image_batch)} files")
            return image_batch
            
        except asyncio.TimeoutError:
            print(f"❌ DeepAI image batch timed out after 5 minutes")
            raise HTTPException(status_code=500, detail="Image generation timed out")
        except Exception as e:
            print(f"❌ DeepAI batch processing failed: {str(e)}")
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
    
    async def generate_image_deepai(self, visual_prompt: str, scene_number: int, child_image_url: str = None) -> bytes:
        """Generate image using DeepAI then resize to 304x304 (face swapping temporarily disabled)"""
        try:
            print(f"🖼️ Generating image for scene {scene_number} with DeepAI (original → 304x304)")
            
            # Enhance the prompt for children's book style
            enhanced_prompt = f"Children's book illustration style, colorful and friendly, high quality digital art: {visual_prompt}"
            
            # Run DeepAI generation in thread pool
            loop = asyncio.get_event_loop()
            
            def create_and_resize_image():
                # DeepAI API request
                response = requests.post(
                    self.deepai_url,
                    data={'text': enhanced_prompt},
                    headers={'api-key': self.deepai_api_key}
                )
                
                if response.status_code != 200:
                    raise Exception(f"DeepAI API error {response.status_code}: {response.text}")
                
                result = response.json()
                if 'output_url' not in result:
                    raise Exception(f"DeepAI response missing output_url: {result}")
                
                # Download the generated image
                image_url = result['output_url']
                image_response = requests.get(image_url)
                if image_response.status_code != 200:
                    raise Exception(f"Failed to download image from {image_url}")
                
                image_data = image_response.content
                
                # Resize to 304x304 using PIL
                image = Image.open(io.BytesIO(image_data))
                resized_image = image.resize((304, 304), Image.LANCZOS)
                
                # Save resized image back to bytes
                output_buffer = io.BytesIO()
                
                # Convert RGBA to RGB if needed for JPEG compatibility
                if resized_image.mode in ('RGBA', 'LA', 'P'):
                    resized_image = resized_image.convert('RGB')
                
                resized_image.save(output_buffer, format='JPEG', quality=85, optimize=True)
                
                return output_buffer.getvalue()
            
            # Execute in thread pool
            resized_image_data = await loop.run_in_executor(None, create_and_resize_image)
            
            # Apply face swapping if child image URL is provided
            # TEMPORARILY DISABLED - keeping code for future use
            if child_image_url and False:  # Disabled face swap
                print(f"🔄 Applying face swap for scene {scene_number}...")
                # resized_image_data = await self.swap_face_deepimage(resized_image_data, child_image_url)
                print(f"✅ Face swap completed for scene {scene_number}")
            elif child_image_url:
                print(f"⚠️ Face swap temporarily disabled for scene {scene_number}")
            
            print(f"✅ DeepAI image generated and resized for scene {scene_number}: {len(resized_image_data)} bytes (304x304)")
            return resized_image_data
            
        except Exception as e:
            print(f"❌ DeepAI error for scene {scene_number}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"DeepAI image generation failed for scene {scene_number}: {str(e)}"
            )
    
    async def generate_image(self, visual_prompt: str, scene_number: int, child_image_url: str = None) -> bytes:
        """Generate image using DeepAI (face swapping temporarily disabled - main method)"""
        return await self.generate_image_deepai(visual_prompt, scene_number, child_image_url)