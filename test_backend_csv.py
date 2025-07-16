#!/usr/bin/env python3
"""
Test script to verify the backend can read the boxes.csv file correctly.
This is a dry run that tests the CSV reading without running the full SAM2 processing.
"""

import csv
import os.path as osp

def test_csv_reading():
    """Test that the backend can read the CSV format correctly."""
    
    print("Testing backend CSV reading...")
    
    # Read input boxes.csv (same logic as in demo2.py)
    with open('boxes.csv', newline='') as in_f:
        reader = csv.DictReader(in_f)
        for row in reader:
            video_path = row['video_path']
            start_frame = int(row['frame'])
            x = float(row['x']); y = float(row['y'])
            w = float(row['width']); h = float(row['height'])
            
            # Convert to SAM2 box format: (x1, y1, x2, y2)
            initial_bbox = (int(x), int(y), int(x + w), int(y + h))
            
            print(f"Video: {video_path}")
            print(f"  Start frame: {start_frame}")
            print(f"  Original bbox (x,y,w,h): ({x}, {y}, {w}, {h})")
            print(f"  SAM2 bbox (x1,y1,x2,y2): {initial_bbox}")
            print(f"  Video exists: {osp.exists(video_path)}")
            print()

if __name__ == "__main__":
    test_csv_reading()
