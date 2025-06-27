#!/usr/bin/env python3
"""
Test script for OmniConsistency
This will download models and test basic functionality
"""

import os
import torch
from PIL import Image
import requests
from io import BytesIO
from pathlib import Path

def test_basic_imports():
    """Test if all required libraries are installed"""
    print("🔍 Testing imports...")
    
    try:
        import diffusers
        print(f"   ✅ diffusers: {diffusers.__version__}")
        
        import transformers
        print(f"   ✅ transformers: {transformers.__version__}")
        
        import accelerate
        print(f"   ✅ accelerate: {accelerate.__version__}")
        
        import safetensors
        print(f"   ✅ safetensors: {safetensors.__version__}")
        
        print(f"   ✅ torch: {torch.__version__}")
        print(f"   ✅ CUDA available: {torch.cuda.is_available()}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False

def download_test_image():
    """Download a test image"""
    print("\n📸 Downloading test image...")
    
    try:
        # Download a simple test image
        url = "https://images.unsplash.com/photo-1574158622682-e40e69881006?w=512&h=512&fit=crop"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content)).convert('RGB')
            # Resize to standard size
            image = image.resize((512, 512), Image.Resampling.LANCZOS)
            
            # Save test image
            os.makedirs('test_images', exist_ok=True)
            image.save('test_images/test_input.jpg')
            print("   ✅ Test image downloaded and saved")
            return True
        else:
            print(f"   ❌ Failed to download image: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error downloading image: {e}")
        return False

def test_huggingface_connection():
    """Test connection to Hugging Face"""
    print("\n🤗 Testing Hugging Face connection...")
    
    try:
        from huggingface_hub import hf_hub_download, repo_exists
        
        # Check if OmniConsistency repo exists
        if repo_exists("showlab/OmniConsistency"):
            print("   ✅ OmniConsistency repository found")
            return True
        else:
            print("   ❌ OmniConsistency repository not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error connecting to Hugging Face: {e}")
        return False

def download_minimal_model():
    """Download just the Ghibli LoRA to test downloads"""
    print("\n📦 Testing model download (Ghibli LoRA only)...")
    
    try:
        from huggingface_hub import hf_hub_download
        
        # Create models directory
        models_dir = Path("models/omniconsistency")
        models_dir.mkdir(parents=True, exist_ok=True)
        
        # Download just the small Ghibli LoRA (~100MB)
        print("   📥 Downloading Ghibli LoRA (~100MB)...")
        lora_path = hf_hub_download(
            repo_id="showlab/OmniConsistency",
            filename="LoRAs/Ghibli_rank128_bf16.safetensors",
            local_dir=str(models_dir),
            local_dir_use_symlinks=False
        )
        
        print(f"   ✅ Downloaded to: {lora_path}")
        
        # Check file size
        file_size = os.path.getsize(lora_path) / (1024 * 1024)  # MB
        print(f"   📊 File size: {file_size:.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Download failed: {e}")
        return False

def check_system_resources():
    """Check available system resources"""
    print("\n💻 Checking system resources...")
    
    # Check available RAM
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        ram_available = psutil.virtual_memory().available / (1024**3)
        print(f"   💾 Total RAM: {ram_gb:.1f} GB")
        print(f"   💾 Available RAM: {ram_available:.1f} GB")
    except ImportError:
        print("   💾 RAM: psutil not installed (optional)")
    
    # Check GPU memory if available
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            print(f"   🎮 GPU {i} Memory: {gpu_memory:.1f} GB")
    
    # Check disk space
    import shutil
    free_space = shutil.disk_usage(".").free / (1024**3)
    print(f"   💾 Free disk space: {free_space:.1f} GB")

def main():
    """Run all tests"""
    print("🧪 OmniConsistency Setup Test")
    print("=" * 50)
    
    # Run tests
    tests = {
        'imports': test_basic_imports(),
        'image': download_test_image(),
        'huggingface': test_huggingface_connection(),
        'download': download_minimal_model()
    }
    
    check_system_resources()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    all_passed = True
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.capitalize()}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your system is ready for OmniConsistency")
        print("📁 Files created:")
        print("   - test_images/test_input.jpg")
        print("   - models/omniconsistency/LoRAs/Ghibli_rank128_bf16.safetensors")
        print("\n💡 Next: Set up the full Django project")
    else:
        print("❌ SOME TESTS FAILED")
        print("💡 Fix the failed tests before proceeding")

if __name__ == "__main__":
    main()