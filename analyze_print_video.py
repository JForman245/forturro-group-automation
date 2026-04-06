#!/usr/bin/env python3
"""
Analyze Jeff's print dialog video to perfect the MLS PDF automation
"""

import subprocess
import os

def extract_key_frames():
    """Extract frames showing the print dialog workflow"""
    video_path = "/Users/claw1/Desktop/Drop PDFs for Birdy/Screen Recording 2026-04-04 at 9.24.28 PM.mov"
    output_dir = "/tmp/mls_print_frames"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract frames at key intervals
    frames = [
        ("00:00:01", "start"),
        ("00:00:03", "cmd_p_triggered"),
        ("00:00:05", "print_dialog_open"),
        ("00:00:07", "pdf_button_location"),
        ("00:00:10", "pdf_menu_opened"),
        ("00:00:12", "save_as_pdf_clicked"),
        ("00:00:15", "save_dialog"),
        ("00:00:18", "file_name_entry"),
        ("00:00:20", "final_save")
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
                print(f"✅ Extracted: {output_file}")
                extracted.append((label, output_file))
            else:
                print(f"❌ Failed {timestamp}: {result.stderr}")
        except Exception as e:
            print(f"❌ Error {timestamp}: {e}")
    
    return extracted

if __name__ == "__main__":
    print("🎬 Analyzing Jeff's print dialog video...")
    frames = extract_key_frames()
    
    if frames:
        print(f"\n✅ Extracted {len(frames)} frames for analysis")
        print("🔍 Now I can see exactly how Jeff clicks through the print dialog!")
        
        # Show frame locations
        for label, path in frames:
            print(f"   {label}: {path}")
    else:
        print("❌ No frames extracted - need to troubleshoot video path")