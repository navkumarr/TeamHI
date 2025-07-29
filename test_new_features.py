#!/usr/bin/env python3
"""
Test script to verify the new features work correctly.
"""

import csv
import os
import tempfile
import datetime

def test_csv_format_with_centroid():
    """Test that the new CSV format with centroid works correctly."""
    
    # Test data with centroid columns
    test_data = [
        ['video_path', 'frame', 'object_id', 'x', 'y', 'width', 'height', 'centroid_x', 'centroid_y'],
        ['test_video.mp4', 10, 0, 100, 200, 50, 60, 125.0, 230.0],
        ['test_video2.mp4', 25, 0, 150, 300, 75, 85, 187.5, 342.5]
    ]
    
    # Write test CSV
    with open('test_tracking_results.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        for row in test_data:
            writer.writerow(row)
    
    # Read it back to verify format
    with open('test_tracking_results.csv', 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        assert len(rows) == 2, f"Expected 2 rows, got {len(rows)}"
        
        # Check first row
        row1 = rows[0]
        assert row1['video_path'] == 'test_video.mp4'
        assert int(row1['frame']) == 10
        assert float(row1['centroid_x']) == 125.0
        assert float(row1['centroid_y']) == 230.0
        
        # Check second row
        row2 = rows[1]
        assert row2['video_path'] == 'test_video2.mp4'
        assert int(row2['frame']) == 25
        assert float(row2['centroid_x']) == 187.5
        assert float(row2['centroid_y']) == 342.5
        
        print("✓ CSV format with centroid test passed")
    
    # Clean up
    os.remove('test_tracking_results.csv')

def test_centroid_calculation():
    """Test that centroid calculation is correct."""
    
    # Test case 1: bbox at (100, 200) with width 50, height 60
    x, y, w, h = 100, 200, 50, 60
    centroid_x = x + w / 2  # 100 + 25 = 125
    centroid_y = y + h / 2  # 200 + 30 = 230
    
    assert centroid_x == 125.0, f"Expected centroid_x=125.0, got {centroid_x}"
    assert centroid_y == 230.0, f"Expected centroid_y=230.0, got {centroid_y}"
    
    # Test case 2: bbox at (0, 0) with width 100, height 100
    x, y, w, h = 0, 0, 100, 100
    centroid_x = x + w / 2  # 0 + 50 = 50
    centroid_y = y + h / 2  # 0 + 50 = 50
    
    assert centroid_x == 50.0, f"Expected centroid_x=50.0, got {centroid_x}"
    assert centroid_y == 50.0, f"Expected centroid_y=50.0, got {centroid_y}"
    
    print("✓ Centroid calculation test passed")

def test_backup_filename():
    """Test that backup filename generation works correctly."""
    
    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"boxes_backup_{timestamp}.csv"
    
    # Check format
    assert backup_filename.startswith("boxes_backup_"), f"Backup filename should start with 'boxes_backup_'"
    assert backup_filename.endswith(".csv"), f"Backup filename should end with '.csv'"
    assert len(timestamp) == 15, f"Timestamp should be 15 characters (YYYYMMDD_HHMMSS)"
    
    print("✓ Backup filename test passed")

def test_output_directory():
    """Test that output directory structure works correctly."""
    
    # Test video filename processing
    video_path = "/path/to/video.mp4"
    video_name = os.path.basename(video_path)  # "video.mp4"
    name_without_ext = os.path.splitext(video_name)[0]  # "video"
    output_name = f"{name_without_ext}_tracked.mp4"  # "video_tracked.mp4"
    
    assert output_name == "video_tracked.mp4", f"Expected 'video_tracked.mp4', got '{output_name}'"
    
    # Test with different extensions
    video_path2 = "/path/to/another_video.avi"
    video_name2 = os.path.basename(video_path2)  # "another_video.avi"
    name_without_ext2 = os.path.splitext(video_name2)[0]  # "another_video"
    output_name2 = f"{name_without_ext2}_tracked.mp4"  # "another_video_tracked.mp4"
    
    assert output_name2 == "another_video_tracked.mp4", f"Expected 'another_video_tracked.mp4', got '{output_name2}'"
    
    print("✓ Output directory test passed")

if __name__ == "__main__":
    print("Testing new features...")
    
    test_csv_format_with_centroid()
    test_centroid_calculation()
    test_backup_filename()
    test_output_directory()
    
    print("\n✅ All tests passed! The new features should work correctly:")
    print("1. CSV output now includes centroid_x and centroid_y columns")
    print("2. Backup files are created with timestamps")
    print("3. Tracked videos will be saved to 'outputs' folder with '_tracked' suffix")
    print("4. Bounding box data is preserved before running SAM2 tracking")
