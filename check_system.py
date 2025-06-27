#!/usr/bin/env python3
"""
System Requirements Check for OmniConsistency
Run this to verify your system can handle the AI model
"""

import sys
import subprocess
import shutil
import platform

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    print(f"   Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ❌ Python 3.8+ required")
        return False

def check_gpu():
    """Check if CUDA/GPU is available"""
    print("\n🎮 Checking GPU availability...")
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                print(f"   GPU {i}: {gpu_name}")
                print(f"   Memory: {gpu_memory:.1f} GB")
                
                if gpu_memory >= 6:
                    print("   ✅ Sufficient GPU memory for OmniConsistency")
                else:
                    print("   ⚠️ WARNING: Less than 6GB GPU memory - will be slow")
            return True
        else:
            print("   ❌ No CUDA GPU detected")
            print("   💡 OmniConsistency will run on CPU (very slow)")
            return False
    except ImportError:
        print("   ❓ PyTorch not installed - will check later")
        return None

def check_disk_space():
    """Check available disk space"""
    print("\n💾 Checking disk space...")
    
    # Check current directory
    free_space_gb = shutil.disk_usage(".").free / (1024**3)
    print(f"   Free space: {free_space_gb:.1f} GB")
    
    required_space = 15  # GB needed for all models
    
    if free_space_gb >= required_space:
        print(f"   ✅ Sufficient space (need ~{required_space}GB)")
        return True
    else:
        print(f"   ❌ Need at least {required_space}GB free space")
        print(f"   💡 Clear some space before proceeding")
        return False

def check_internet():
    """Check internet connection"""
    print("\n🌐 Checking internet connection...")
    
    try:
        import urllib.request
        urllib.request.urlopen('http://www.google.com', timeout=5)
        print("   ✅ Internet connection available")
        return True
    except:
        print("   ❌ No internet connection")
        print("   💡 Internet needed to download models")
        return False

def check_system_info():
    """Display system information"""
    print("\n💻 System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Architecture: {platform.machine()}")
    
    # Check RAM
    try:
        if platform.system() == "Linux":
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        ram_kb = int(line.split()[1])
                        ram_gb = ram_kb / (1024**2)
                        print(f"   RAM: {ram_gb:.1f} GB")
                        break
        else:
            print("   RAM: Unable to detect on this OS")
    except:
        print("   RAM: Unable to detect")

def main():
    """Run all system checks"""
    print("🔍 OmniConsistency System Requirements Check")
    print("=" * 50)
    
    # Track results
    checks = {
        'python': check_python_version(),
        'gpu': check_gpu(),
        'disk': check_disk_space(),
        'internet': check_internet()
    }
    
    check_system_info()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    
    if checks['python'] and checks['disk'] and checks['internet']:
        if checks['gpu']:
            print("🎉 EXCELLENT! Your system is ready for OmniConsistency")
            print("   Expected processing time: 30-60 seconds per image")
        elif checks['gpu'] is False:
            print("⚠️ OKAY: System works but no GPU detected")
            print("   Expected processing time: 5-10 minutes per image")
        else:
            print("✅ GOOD: System requirements met")
            print("   GPU check pending PyTorch installation")
    else:
        print("❌ ISSUES DETECTED: Fix the above problems before proceeding")
    
    print("\n💡 Next step: Install required Python packages")

if __name__ == "__main__":
    main()