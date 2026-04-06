#!/usr/bin/env python3
"""
Extract key frames from Jeff's print dialog video to understand the UI flow
"""

import subprocess
import os

video_path = "/Users/claw1/Desktop/Drop PDFs for Birdy/Screen Recording 2026-04-04 at 9.24.28 PM.mov"
output_dir = "/tmp/print_dialog_frames"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

def extract_frame(timestamp, label):
    """Extract a frame at given timestamp"""
    output_file = f"{output_dir}/frame_{label}.png"
    cmd = [
        'ffmpeg', '-i', video_path,
        '-ss', timestamp,
        '-vframes', '1',
        '-y',  # Overwrite output
        output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Extracted frame at {timestamp}: {output_file}")
            return output_file
        else:
            print(f"❌ Failed to extract frame at {timestamp}: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error extracting frame at {timestamp}: {e}")
        return None

# Get video duration first
def get_video_duration():
    cmd = ['ffmpeg', '-i', video_path, '-f', 'null', '-']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    for line in result.stderr.split('\n'):
        if 'Duration:' in line:
            duration = line.split('Duration: ')[1].split(',')[0].strip()
            print(f"Video duration: {duration}")
            return duration
    return "00:00:30"  # Default fallback

if __name__ == "__main__":
    print("🎬 Extracting frames from Safari print dialog video...")
    
    duration = get_video_duration()
    
    # Extract frames at key intervals to capture the print dialog workflow
    frames_to_extract = [
        ("00:00:01", "start"),
        ("00:00:03", "cmd_p_pressed"), 
        ("00:00:05", "print_dialog_open"),
        ("00:00:07", "clicking_pdf_option"),
        ("00:00:10", "pdf_menu_open"),
        ("00:00:12", "save_as_pdf_clicked"),
        ("00:00:15", "save_dialog"),
        ("00:00:18", "entering_filename"),
        ("00:00:20", "final_save"),
    ]
    
    extracted_frames = []
    for timestamp, label in frames_to_extract:
        frame_file = extract_frame(timestamp, label)
        if frame_file:
            extracted_frames.append((label, frame_file))
    
    print(f"\n🎯 Extracted {len(extracted_frames)} frames:")
    for label, file_path in extracted_frames:
        print(f"   {label}: {file_path}")
    
    print(f"\n📁 All frames saved to: {output_dir}")
    print("🔍 Now I can analyze these frames to see your exact print dialog workflow!")