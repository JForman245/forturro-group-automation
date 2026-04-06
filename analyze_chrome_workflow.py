#!/usr/bin/env python3
"""
Analyze Jeff's Chrome MLS workflow video to build full automation
"""

import subprocess
import os

def extract_chrome_workflow():
    """Extract frames from Chrome workflow video"""
    video_path = "/Users/claw1/Desktop/Drop PDFs for Birdy/Screen Recording 2026-04-04 at 10.16.44 PM.mov"
    output_dir = "/tmp/chrome_mls_workflow"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract frames at intervals to capture the full workflow
    frames = [
        ("00:00:02", "chrome_opening"),
        ("00:00:05", "navigation_start"),
        ("00:00:10", "login_process"),
        ("00:00:15", "mls_access"),
        ("00:00:20", "search_interface"),
        ("00:00:25", "property_search"),
        ("00:00:30", "search_results"),
        ("00:00:35", "listing_selection"),
        ("00:00:40", "listing_page"),
        ("00:00:45", "print_trigger"),
        ("00:00:50", "print_dialog"),
        ("00:00:55", "pdf_selection"),
        ("00:01:00", "save_dialog"),
        ("00:01:05", "final_save")
    ]
    
    extracted = []
    for timestamp, label in frames:
        output_file = f"{output_dir}/frame_{label}.png"
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', timestamp,
            '-vframes', '1',
            '-y',
            output_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✅ {timestamp}: {output_file}")
                extracted.append((label, output_file, timestamp))
            else:
                print(f"❌ Failed {timestamp}")
        except Exception as e:
            print(f"❌ Error {timestamp}: {e}")
    
    return extracted

if __name__ == "__main__":
    print("🎬 Analyzing Jeff's Chrome MLS workflow...")
    frames = extract_chrome_workflow()
    
    print(f"\n✅ Extracted {len(frames)} workflow frames")
    print("🔍 Ready to build fully automated Chrome solution!")
    
    for label, path, timestamp in frames:
        print(f"   {timestamp} - {label}")