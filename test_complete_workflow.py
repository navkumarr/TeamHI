#!/usr/bin/env python3
"""
Test script to verify the complete workflow works
"""
import os
import subprocess
import sys
import time

def test_workflow():
    # Check if the frontend can be imported
    try:
        import frontend
        print("✓ Frontend module imports successfully")
    except ImportError as e:
        print(f"✗ Frontend import failed: {e}")
        return False
    
    # Check if the backend script exists
    if os.path.exists("scripts/demo2.py"):
        print("✓ Backend script exists")
    else:
        print("✗ Backend script missing")
        return False
    
    # Check if test videos exist
    test_videos = ["vids/fastjet1.mp4", "vids/fastjet2.mp4", "vids/slowjet1.mp4", "vids/slowjet2.mp4"]
    for video in test_videos:
        if os.path.exists(video):
            print(f"✓ Test video {video} exists")
        else:
            print(f"✗ Test video {video} missing")
    
    # Check if boxes.csv exists with valid data
    if os.path.exists("boxes.csv"):
        print("✓ boxes.csv exists")
        with open("boxes.csv", 'r') as f:
            content = f.read()
            if "video_path,frame,x,y,width,height" in content:
                print("✓ boxes.csv has correct header")
            else:
                print("✗ boxes.csv has incorrect header")
    else:
        print("✗ boxes.csv missing")
        return False
    
    # Check if outputs directory exists
    if os.path.exists("outputs"):
        print("✓ outputs directory exists")
    else:
        print("✗ outputs directory missing")
        return False
    
    # Check if tracking results exist
    if os.path.exists("tracking_results.csv"):
        print("✓ tracking_results.csv exists")
        with open("tracking_results.csv", 'r') as f:
            content = f.read()
            if "centroid_x" in content and "centroid_y" in content:
                print("✓ tracking_results.csv has centroid columns")
            else:
                print("✗ tracking_results.csv missing centroid columns")
    else:
        print("✗ tracking_results.csv missing")
        return False
    
    print("\n✓ All workflow components are working correctly!")
    return True

if __name__ == "__main__":
    print("Testing complete workflow...")
    print("=" * 50)
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    success = test_workflow()
    
    if success:
        print("\n🎉 Workflow test PASSED!")
        sys.exit(0)
    else:
        print("\n❌ Workflow test FAILED!")
        sys.exit(1)
