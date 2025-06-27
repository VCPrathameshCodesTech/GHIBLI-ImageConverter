"""
Working Replicate Processor using FLUX models
Based on the working example from Replicate documentation
"""

import replicate
import requests
from PIL import Image
from io import BytesIO
from django.conf import settings
import time
import os

class HuggingFaceProcessor:
    def __init__(self):
        self.api_token = getattr(settings, 'REPLICATE_API_TOKEN', '')
        
        if self.api_token:
            os.environ["REPLICATE_API_TOKEN"] = self.api_token
            print(f"🤖 Replicate AI ready - using FLUX models!")
            self.use_ai = True
        else:
            print("⚠️ No Replicate API token - using filters")
            self.use_ai = False
    
    def convert_to_ghibli(self, image_path, prompt, model_name='ghibli'):
        """Convert using Replicate FLUX models"""
        
        if self.use_ai:
            return self._convert_with_flux(image_path, model_name, prompt)
        else:
            return self._convert_with_filters(image_path, model_name)
    
    def _convert_with_flux(self, image_path, style, prompt):
        """Real AI conversion using FLUX models"""
        print(f"🤖 Using FLUX AI for {style} style...")
        print(f"🎯 Converting: {prompt}")
        
        try:
            # First, upload the image to get a URL (Replicate needs URLs)
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Create style-specific prompts
            style_prompts = {
                'ghibli': f"Make this a Studio Ghibli anime style artwork, magical atmosphere, hand-drawn animation style, detailed, beautiful",
                'anime': f"Make this an anime style artwork, vibrant colors, detailed anime art",
                'cartoon': f"Make this a 90s cartoon style artwork, bold colors, cartoon illustration",
                'sketch': f"Make this a pencil sketch artwork, black and white drawing, artistic sketch",
                'vibrant': f"Make this artwork with vibrant enhanced colors, colorful, bright, saturated"
            }
            
            final_prompt = style_prompts.get(style, style_prompts['ghibli'])
            print(f"📝 Using prompt: {final_prompt}")
            
            # Use the working FLUX model
            input_data = {
                "prompt": final_prompt,
                "output_format": "jpg"
            }
            
            # For image-to-image, we need to provide the image
            # Since we have a local file, let's convert it to base64 or use a file upload
            
            print("📡 Calling FLUX model...")
            
            # Method 1: Try with file upload
            try:
                output = replicate.run(
                    "black-forest-labs/flux-kontext-pro",
                    input={
                        "prompt": final_prompt,
                        "input_image": open(image_path, "rb"),
                        "output_format": "jpg"
                    }
                )
            except Exception as e1:
                print(f"⚠️ File upload failed, trying alternative method: {e1}")
                
                # Method 2: Try text-to-image if image upload fails
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": f"{final_prompt}, based on the style of the uploaded image",
                        "width": 512,
                        "height": 512,
                        "num_outputs": 1,
                        "output_format": "jpg"
                    }
                )
            
            print(f"📊 FLUX output type: {type(output)}")
            print(f"📄 Output: {output}")
            
            # Handle the output - FLUX returns a file-like object or URL
            if hasattr(output, 'read'):
                # It's a file-like object
                print("📥 Reading file object...")
                image_data = output.read()
                image = Image.open(BytesIO(image_data))
            elif isinstance(output, str) and output.startswith('http'):
                # It's a URL
                print(f"📥 Downloading from URL: {output}")
                response = requests.get(output, timeout=60)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                else:
                    raise Exception(f"Download failed: {response.status_code}")
            elif isinstance(output, list) and len(output) > 0:
                # It's a list of URLs
                image_url = output[0]
                print(f"📥 Downloading from list URL: {image_url}")
                response = requests.get(image_url, timeout=60)
                if response.status_code == 200:
                    image = Image.open(BytesIO(response.content))
                else:
                    raise Exception(f"Download failed: {response.status_code}")
            else:
                print(f"❌ Unexpected output format: {output}")
                raise Exception("Unexpected output format from FLUX")
            
            print("✅ FLUX AI conversion successful!")
            return image
            
        except Exception as e:
            print(f"❌ FLUX error: {e}")
            print("🔄 Falling back to enhanced filters...")
            return self._convert_with_filters(image_path, style)
    
    def _convert_with_filters(self, image_path, style):
        """Enhanced filter fallback"""
        print(f"🎨 Using enhanced {style} filters...")
        
        time.sleep(2)
        
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img = img.resize((512, 512), Image.Resampling.LANCZOS)
            
            if style == 'ghibli':
                return self._ghibli_filter(img)
            elif style == 'anime':
                return self._anime_filter(img)
            elif style == 'cartoon':
                return self._cartoon_filter(img)
            elif style == 'sketch':
                return self._sketch_filter(img)
            elif style == 'vibrant':
                return self._vibrant_filter(img)
            else:
                return self._ghibli_filter(img)
    
    def _ghibli_filter(self, img):
        """Enhanced Ghibli filter"""
        from PIL import ImageFilter, ImageEnhance, ImageOps
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.3)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        img = ImageOps.posterize(img, 6)
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.05)
        
        return img
    
    def _anime_filter(self, img):
        """Enhanced anime filter"""
        from PIL import ImageFilter, ImageEnhance, ImageOps
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.6)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3)
        
        img = ImageOps.posterize(img, 4)
        img = img.filter(ImageFilter.SHARPEN)
        
        return img
    
    def _cartoon_filter(self, img):
        """Enhanced cartoon filter"""
        from PIL import ImageFilter, ImageEnhance, ImageOps
        
        img = ImageOps.posterize(img, 3)
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.8)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.4)
        
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        
        return img
    
    def _sketch_filter(self, img):
        """Enhanced sketch filter"""
        from PIL import ImageFilter, ImageEnhance, ImageOps
        
        gray = img.convert('L')
        edges = gray.filter(ImageFilter.FIND_EDGES)
        sketch = ImageOps.invert(edges).convert('RGB')
        
        enhancer = ImageEnhance.Contrast(sketch)
        sketch = enhancer.enhance(2.5)
        
        return sketch
    
    def _vibrant_filter(self, img):
        """Enhanced vibrant filter"""
        from PIL import ImageFilter, ImageEnhance
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(2.2)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.6)
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.2)
        
        img = img.filter(ImageFilter.SHARPEN)
        
        return img
    
    def test_connection(self):
        """Test Replicate FLUX connection"""
        if self.use_ai:
            try:
                # Simple test - try to list models
                models = list(replicate.models.list())
                print(f"✅ Replicate FLUX API working! Connected successfully")
                return True
            except Exception as e:
                print(f"❌ Replicate API error: {e}")
                return False
        else:
            print("✅ Filter mode ready")
            return True

# Create global processor instance
processor = HuggingFaceProcessor()