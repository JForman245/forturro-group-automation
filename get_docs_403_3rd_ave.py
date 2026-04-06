#!/usr/bin/env python3
"""
Get Documents for 403 3rd Ave N
Automated version - assumes you're already logged into MLS
"""

import sys
sys.path.append('/Users/claw1/.openclaw/workspace')

from mls_docs_extractor import MLSDocumentExtractor

def main():
    print("🏠 Getting MLS Documents for 403 3rd Ave N")
    print("=" * 60)
    
    try:
        extractor = MLSDocumentExtractor()
        success = extractor.extract_documents_for_address("403 3rd Ave N")
        
        if success:
            print("\n🎉 SUCCESS! All documents downloaded.")
            print("📁 Check: /Users/claw1/Desktop/Drop PDFs for Birdy/")
        else:
            print("\n❌ FAILED: Could not extract documents")
            print("💡 Try the manual approach or check MLS connection")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()