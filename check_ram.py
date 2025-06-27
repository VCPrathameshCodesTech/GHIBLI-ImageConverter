#!/usr/bin/env python3
"""
RAM Usage Check for OmniConsistency
Check current memory usage and requirements
"""

import psutil
import os
import time

def check_current_ram():
    """Check current RAM usage"""
    print("🔍 Current RAM Status:")
    print("-" * 30)
    
    # Get memory info
    memory = psutil.virtual_memory()
    
    total_gb = memory.total / (1024**3)
    available_gb = memory.available / (1024**3)
    used_gb = memory.used / (1024**3)
    percent_used = memory.percent
    
    print(f"Total RAM:     {total_gb:.1f} GB")
    print(f"Used RAM:      {used_gb:.1f} GB ({percent_used:.1f}%)")
    print(f"Available RAM: {available_gb:.1f} GB")
    
    return available_gb

def check_top_processes():
    """Show top memory-consuming processes"""
    print("\n🔍 Top Memory Users:")
    print("-" * 50)
    
    # Get all processes
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            proc_info = proc.info
            memory_mb = proc_info['memory_info'].rss / (1024**2)
            if memory_mb > 50:  # Only show processes using > 50MB
                processes.append({
                    'pid': proc_info['pid'],
                    'name': proc_info['name'],
                    'memory_mb': memory_mb
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # Sort by memory usage
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    
    # Show top 10
    for i, proc in enumerate(processes[:10]):
        print(f"{i+1:2d}. {proc['name']:<20} {proc['memory_mb']:>8.1f} MB")

def check_omni_requirements():
    """Check if we have enough RAM for OmniConsistency"""
    print("\n💡 OmniConsistency RAM Requirements:")
    print("-" * 40)
    
    # Estimated requirements
    base_requirement = 2.0  # GB for base model
    safety_margin = 1.0     # GB for safety
    total_needed = base_requirement + safety_margin
    
    print(f"Base model:    ~{base_requirement:.1f} GB")
    print(f"Safety margin:  {safety_margin:.1f} GB")
    print(f"Total needed:  ~{total_needed:.1f} GB")
    
    available = check_current_ram()
    
    print(f"\nYour available: {available:.1f} GB")
    
    if available >= total_needed:
        print("✅ GOOD: Sufficient RAM for OmniConsistency")
        return True
    elif available >= base_requirement:
        print("⚠️ TIGHT: Might work but could be slow")
        print("💡 Consider closing other applications")
        return "maybe"
    else:
        print("❌ INSUFFICIENT: Need more RAM")
        print("💡 Close applications or use API instead")
        return False

def suggest_optimization():
    """Suggest ways to free up RAM"""
    print("\n💡 How to Free Up RAM:")
    print("-" * 25)
    print("1. Close web browsers (especially Chrome)")
    print("2. Close unnecessary applications")
    print("3. Restart your computer")
    print("4. Close file explorer windows")
    print("5. End background processes you don't need")
    
    print("\n🔄 To recheck RAM after cleanup:")
    print("   python check_ram.py")

def continuous_monitor():
    """Monitor RAM for 30 seconds"""
    print("\n📊 Monitoring RAM for 30 seconds...")
    print("(Close applications and watch the Available RAM)")
    print("-" * 50)
    
    for i in range(6):  # 6 checks over 30 seconds
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        used_percent = memory.percent
        
        print(f"Check {i+1}: Available RAM: {available_gb:.1f} GB ({100-used_percent:.1f}% free)")
        
        if i < 5:  # Don't sleep after last check
            time.sleep(5)
    
    print("\n💡 Use the highest Available RAM value you saw")

def main():
    """Run RAM checks"""
    print("🧠 RAM Check for OmniConsistency")
    print("=" * 40)
    
    # Basic check
    result = check_omni_requirements()
    
    # Show processes
    check_top_processes()
    
    # Suggestions based on result
    if result is True:
        print("\n🎉 RAM looks good! You can proceed with OmniConsistency")
    elif result == "maybe":
        print("\n⚠️ RAM is tight. Consider:")
        print("   Option 1: Free up memory and try")
        print("   Option 2: Use Hugging Face API instead")
        suggest_optimization()
    else:
        print("\n❌ Not enough RAM for OmniConsistency")
        print("   Recommended: Use Hugging Face API")
        suggest_optimization()
    
    print("\n🔄 Want to monitor RAM while you close apps?")
    response = input("Type 'y' to start 30-second monitoring: ")
    
    if response.lower() == 'y':
        continuous_monitor()

if __name__ == "__main__":
    main()