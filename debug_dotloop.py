#!/usr/bin/env python3
"""Debug script to inspect dotloop API responses"""

from dotloop_manager import DotloopManager
import json

manager = DotloopManager()

print("=== Profile Data ===")
profile = manager.api_get('/profile')
if profile:
    print(json.dumps(profile, indent=2))
else:
    print("No profile data")

print("\n=== Loops Data ===")
loops = manager.api_get('/loop')
if loops:
    print(json.dumps(loops, indent=2))
else:
    print("No loops data")