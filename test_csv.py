import csv

print("Testing existing boxes.csv format:")
with open('boxes.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(f"Video: {row['video_path']}, Frame: {row['frame']}, Bbox: ({row['x']}, {row['y']}, {row['width']}, {row['height']})")
