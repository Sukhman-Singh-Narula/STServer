# ===== app/services/media_service.py - OPTIMIZED WITH BATCH PROCESSING AND DEEPAI =====
import io
import json
import time
import base64
import asyncio
import aiohttp
import requests
import random
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
        
        # Circuit breaker for DeepAI reliability
        self.deepai_failures = 0
        self.deepai_last_failure = 0
        self.deepai_circuit_open = False
        
        print(f"✅ MediaService initialized with DeepAI image generation and circuit breaker")
    
    def _check_deepai_circuit(self):
        """Check if DeepAI circuit breaker should be opened"""
        current_time = time.time()
        
        # Reset failures after 5 minutes
        if current_time - self.deepai_last_failure > 300:
            self.deepai_failures = 0
            self.deepai_circuit_open = False
        
        # Open circuit if too many failures
        if self.deepai_failures > 5:
            self.deepai_circuit_open = True
            print("🚨 DeepAI circuit breaker opened - using placeholders")
        
        return not self.deepai_circuit_open
    
    def _record_deepai_failure(self):
        """Record a DeepAI failure"""
        self.deepai_failures += 1
        self.deepai_last_failure = time.time()
    
    def _create_placeholder_image(self) -> bytes:
        """Create a simple placeholder image when generation fails"""
        try:
            # Create a simple colored square
            placeholder = Image.new('RGB', (304, 304), color='lightblue')
            output_buffer = io.BytesIO()
            placeholder.save(output_buffer, format='JPEG', quality=75)
            return output_buffer.getvalue()
        except:
            # Return minimal bytes if even placeholder fails
            return b"placeholder"
    
    def _process_image_fast(self, image_data: bytes) -> bytes:
        """Optimized image processing for speed"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Fast resize with lower quality for speed
            resized_image = image.resize((304, 304), Image.NEAREST)  # Faster than LANCZOS
            
            if resized_image.mode in ('RGBA', 'LA', 'P'):
                resized_image = resized_image.convert('RGB')
            
            output_buffer = io.BytesIO()
            resized_image.save(output_buffer, format='JPEG', quality=75, optimize=False)  # Lower quality, no optimization for speed
            
            return output_buffer.getvalue()
        except:
            return self._create_placeholder_image()
    
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
        """Optimized batch audio generation using OpenAI TTS"""
        try:
            voice = "sage" if isfemale else "onyx"
            print(f"🎵 Fast OpenAI TTS processing for {len(scene_texts)} scenes")
            print(f"🎤 Voice selected: {voice} ({'female' if isfemale else 'male'})")
            
            async def generate_single_audio_fast(scene_data):
                """Generate audio for a single scene using OpenAI TTS with optimizations"""
                text = scene_data['text']
                scene_number = scene_data['scene_number']
                
                try:
                    loop = asyncio.get_event_loop()
                    
                    def create_tts_fast():
                        response = self.openai_client.audio.speech.create(
                            model="tts-1-hd",  # Use HD model for better quality
                            voice=voice,
                            input=text[:1000],  # Limit text length for speed
                            response_format="mp3",  # MP3 is faster than WAV
                            speed=1.1  # Slightly faster speech
                        )
                        
                        return response.content  # Direct content access
                    
                    audio_data = await loop.run_in_executor(None, create_tts_fast)
                    print(f"✅ Fast audio for scene {scene_number}: {len(audio_data)} bytes")
                    return audio_data
                    
                except Exception as e:
                    print(f"❌ Audio error scene {scene_number}: {str(e)}")
                    return b"audio_placeholder"  # Return placeholder instead of failing
            
            # Parallel execution with shorter timeout
            tasks = [generate_single_audio_fast(scene_data) for scene_data in scene_texts]
            audio_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=60.0  # Reduced from 120 to 60 seconds
            )
            
            # Process results with error tolerance
            audio_batch = []
            for i, result in enumerate(audio_results):
                if isinstance(result, Exception):
                    print(f"⚠️ Audio scene {i+1} failed, using placeholder")
                    audio_batch.append(b"audio_placeholder")
                else:
                    audio_batch.append(result)
            
            print(f"✅ Fast audio batch completed: {len(audio_batch)} files")
            return audio_batch
            
        except asyncio.TimeoutError:
            print(f"⚠️ Audio batch timed out, using placeholders")
            return [b"audio_placeholder" for _ in scene_texts]
        except Exception as e:
            print(f"❌ Audio batch failed: {str(e)}")
            return [b"audio_placeholder" for _ in scene_texts]
            
        except asyncio.TimeoutError:
            print(f"❌ OpenAI audio batch timed out after 2 minutes")
            raise HTTPException(status_code=500, detail="Audio generation timed out")
        except Exception as e:
            print(f"❌ OpenAI batch processing failed: {str(e)}")
            raise e
    
    async def generate_image_batch(self, visual_prompts: List[Dict], child_image_url: str = None) -> List[bytes]:
        """Generate images for multiple scenes in parallel using DeepAI with optimized timeouts"""
        try:
            print(f"🖼️ Starting DeepAI batch image generation for {len(visual_prompts)} scenes...")
            
            # Increase concurrency for faster processing
            semaphore = asyncio.Semaphore(8)  # Increased from 3 to 8
            
            async def generate_single_image_deepai(prompt_data):
                """Generate image for a single scene using DeepAI with optimized retry logic"""
                visual_prompt = prompt_data['visual_prompt']
                scene_number = prompt_data['scene_number']
                
                async with semaphore:
                    try:
                        # Check circuit breaker
                        if not self._check_deepai_circuit():
                            print(f"⚠️ DeepAI circuit open for scene {scene_number}, using placeholder")
                            return self._create_placeholder_image()
                        
                        loop = asyncio.get_event_loop()
                        
                        def create_image_with_retries():
                            safe_visual_prompt = self._sanitize_visual_prompt(visual_prompt)
                            enhanced_prompt = f"Children's book illustration, colorful cartoon: {safe_visual_prompt}"
                            enhanced_prompt = enhanced_prompt[:400]  # Reduced from 500
                            enhanced_prompt = enhanced_prompt.replace('"', "'").replace('\n', ' ').replace('\r', ' ')
                            
                            print(f"🎨 DeepAI prompt for scene {scene_number}: {enhanced_prompt[:100]}...")
                            
                            # Faster retry logic
                            max_retries = 3  # Increased retries
                            for attempt in range(max_retries):
                                try:
                                    response = requests.post(
                                        self.deepai_url,
                                        data={'text': enhanced_prompt},
                                        headers={'api-key': self.deepai_api_key},
                                        timeout=20  # Reduced from 30 to 20 seconds
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        if 'output_url' in result:
                                            # Download with shorter timeout
                                            image_response = requests.get(result['output_url'], timeout=15)
                                            if image_response.status_code == 200:
                                                # Optimized image processing
                                                return self._process_image_fast(image_response.content)
                                            
                                    # Quick retry without long delays
                                    if attempt < max_retries - 1:
                                        time.sleep(0.5)  # Reduced from 2 seconds
                                        
                                except requests.RequestException:
                                    if attempt < max_retries - 1:
                                        time.sleep(0.5)
                                        continue
                                        
                            raise Exception(f"DeepAI failed after {max_retries} attempts")
                        
                        image_data = await loop.run_in_executor(None, create_image_with_retries)
                        print(f"✅ Fast DeepAI image generated for scene {scene_number}: {len(image_data)} bytes")
                        return image_data
                        
                    except Exception as e:
                        print(f"❌ DeepAI error for scene {scene_number}: {str(e)}")
                        self._record_deepai_failure()
                        return self._create_placeholder_image()
                                    
                        
            # Execute with shorter overall timeout
            tasks = [generate_single_image_deepai(prompt_data) for prompt_data in visual_prompts]
            image_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=180.0  # Reduced from 300 to 180 seconds (3 minutes)
            )
            
            # Process results faster
            image_batch = []
            for i, result in enumerate(image_results):
                if isinstance(result, Exception):
                    print(f"❌ Scene {i+1} failed, using placeholder")
                    # Use placeholder instead of failing entire batch
                    image_batch.append(self._create_placeholder_image())
                else:
                    image_batch.append(result)
            
            print(f"✅ DeepAI batch completed: {len(image_batch)} files")
            return image_batch
            
        except asyncio.TimeoutError:
            print(f"⚠️ DeepAI batch timed out, using placeholders")
            return [self._create_placeholder_image() for _ in visual_prompts]
        except Exception as e:
            print(f"❌ DeepAI batch failed, using placeholders: {str(e)}")
            return [self._create_placeholder_image() for _ in visual_prompts]
    
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
    
    def _sanitize_visual_prompt(self, prompt: str) -> str:
        """Apply child safety filters to visual prompts"""
        # Remove potentially inappropriate keywords
        inappropriate_words = [
            'scary', 'dark', 'violent', 'weapon', 'gun', 'knife', 'blood', 'death',
            'monster', 'evil', 'demon', 'horror', 'nightmare', 'spooky', 'creepy',
            'sad', 'crying', 'angry', 'mean', 'dangerous', 'hurt', 'pain'
        ]
        
        safe_prompt = prompt.lower()
        for word in inappropriate_words:
            safe_prompt = safe_prompt.replace(word, '')
        
        # Add positive descriptors
        safe_descriptors = [
            'happy', 'colorful', 'bright', 'cheerful', 'friendly', 'smiling', 
            'magical', 'wonderful', 'beautiful', 'peaceful', 'joyful'
        ]
        
        # Clean up extra spaces
        safe_prompt = ' '.join(safe_prompt.split())
        
        # Add a random positive descriptor if the prompt seems too plain
        if len(safe_prompt.split()) < 5:
            import random
            safe_prompt += f" {random.choice(safe_descriptors)}"
        
        return safe_prompt
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all services"""
        health = {
            "openai_tts": False,
            "deepai_images": False,
            "overall": False
        }
        
        try:
            # Quick OpenAI TTS test
            test_response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice="sage",
                input="test",
                response_format="mp3"
            )
            health["openai_tts"] = len(test_response.content) > 0
            
            # Quick DeepAI test
            if self._check_deepai_circuit():
                test_response = requests.post(
                    self.deepai_url,
                    data={'text': 'test image'},
                    headers={'api-key': self.deepai_api_key},
                    timeout=5
                )
                health["deepai_images"] = test_response.status_code == 200
            
            health["overall"] = health["openai_tts"] or health["deepai_images"]
            
        except Exception as e:
            print(f"Health check failed: {str(e)}")
        
        return health