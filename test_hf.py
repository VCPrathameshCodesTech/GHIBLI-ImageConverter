#!/usr/bin/env python3
"""
Test Hugging Face API connection and model
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ghibli_gallery.settings')
django.setup()

from gallery.huggingface_processor import processor

def test_hf_api():
    """Test Hugging Face API connection"""
    print("🧪 Testing Hugging Face API...")
    
    # Test basic connection
    print("\n1. Testing API connection...")
    try:
        success = processor.test_connection()
        if success:
            print("   ✅ API connection successful")
        else:
            print("   ❌ API connection failed")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
    
    # Test token
    print("\n2. Testing API token...")
    if processor.token:
        print(f"   ✅ Token found: {processor.token[:10]}...")
    else:
        print("   ❌ No token found")
    
    # Test model availability
    print("\n3. Testing Ghibli model...")
    try:
        import requests
        api_url = "https://api-inference.huggingface.co/models/nitrosocke/Ghibli-Diffusion"
        headers = {"Authorization": f"Bearer {processor.token}"}
        
        # Make a simple test request
        payload = {"inputs": "test"}
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        print(f"   Status code: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Model is ready")
        elif response.status_code == 503:
            print("   ⚠️ Model is loading (this is normal)")
            try:
                result = response.json()
                if 'estimated_time' in result:
                    print(f"   Estimated loading time: {result['estimated_time']} seconds")
            except:
                pass
        else:
            print(f"   ❌ Model error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Model test error: {e}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_hf_api()