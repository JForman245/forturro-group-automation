#!/usr/bin/env python3
"""
Simple wrapper for MLS Documents Extractor
Usage: python3 get_mls_docs.py "1234 Main St, Myrtle Beach"
"""

import sys
import subprocess

def main():
    if len(sys.argv) != 2:
        print("💡 MLS Documents Extractor")
        print("📋 Downloads PDF documents attached to MLS listings")
        print("")
        print("Usage:")
        print("  python3 get_mls_docs.py '1234 Main St, Myrtle Beach'")
        print("")
        print("Examples:")
        print("  python3 get_mls_docs.py '906 3rd Ave N, Surfside Beach'")
        print("  python3 get_mls_docs.py '123 Ocean Blvd, Myrtle Beach'")
        print("")
        print("📁 Documents will be saved to: /Users/claw1/Desktop/MLS_Documents/")
        sys.exit(1)
    
    address = sys.argv[1]
    
    print("🚀 Starting MLS Documents extraction...")
    print(f"📍 Target: {address}")
    print("")
    
    # Run the main extractor
    result = subprocess.run([
        'python3', 
        '/Users/claw1/.openclaw/workspace/mls_docs_extractor.py', 
        address
    ], capture_output=False)
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()