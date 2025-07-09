import cv2

# Load the video
video_path = "repaired.mp4"  # Change this to your video path
cap = cv2.VideoCapture(video_path)

# Read the first frame
ret, frame = cap.read()
if not ret:
    print("Failed to read video.")
    cap.release()
    exit()

# Let user draw bounding box
bbox = cv2.selectROI("Draw Bounding Box", frame, fromCenter=False, showCrosshair=True)
cv2.destroyAllWindows()

# Unpack and print the bounding box
x, y, w, h = map(int, bbox)
print(f"Selected bounding box: x={x}, y={y}, w={w}, h={h}")

# Write to a file
output_path = "bbox_output.txt"
with open(output_path, "w") as f:
    f.write(f"{x},{y},{w},{h}\n")

print(f"Saved to {output_path}")
