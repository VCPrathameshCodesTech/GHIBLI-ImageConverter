#!/usr/bin/env python3
"""
Test Replicate API connection
"""

import os
import replicate

# Test both token formats
tokens_to_test = [
    "r8_YRXXdX3bPmV9vUWgH6tYykKAavxdn9Z4MnaUY"
    
]

for i, token in enumerate(tokens_to_test):
    print(f"\n🧪 Testing token format {i+1}: {token[:10]}...")
    
    try:
        # Set the token
        os.environ["REPLICATE_API_TOKEN"] = token
        
        # Try to list models (simple API test)
        models = replicate.models.list()
        print(f"✅ Token format {i+1} works! Found {len(list(models))} models")
        print(f"🎉 Use this token: {token}")
        break
        
    except Exception as e:
        print(f"❌ Token format {i+1} failed: {e}")
        continue
else:
    print("\n❌ Neither token format worked")
    print("💡 Try generating a new token at https://replicate.com/account/api-tokens")