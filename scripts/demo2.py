import argparse
import csv
import os
import os.path as osp
import numpy as np
import torch
import gc
import sys
import cv2

# Append SAM2 library path
sys.path.append("./sam2")
from sam2.build_sam import build_sam2_video_predictor

# Determine which SAM2 config to use based on the checkpoint name
def determine_model_cfg(model_path):
    if "large" in model_path:
        return "configs/samurai/sam2.1_hiera_l.yaml"
    elif "base_plus" in model_path:
        return "configs/samurai/sam2.1_hiera_b+.yaml"
    elif "small" in model_path:
        return "configs/samurai/sam2.1_hiera_s.yaml"
    elif "tiny" in model_path:
        return "configs/samurai/sam2.1_hiera_t.yaml"
    else:
        raise ValueError("Unknown model size in path!")

# Validate video path format
def prepare_frames_or_path(video_path):
    if video_path.endswith(".mp4") or osp.isdir(video_path):
        return video_path
    else:
        raise ValueError("Invalid video_path format. Should be .mp4 or a directory of frames.")

# Process one video + initial box, writing frame-by-frame tracking to CSV writer
def process_tracking(predictor, video_path, start_frame, initial_bbox, writer):
    frames_or_path = prepare_frames_or_path(video_path)
    # Initialize tracker state
    state = predictor.init_state(frames_or_path, offload_video_to_cpu=True)
    # Add initial box at the specified start_frame for object ID 0
    predictor.add_new_points_or_box(state, box=initial_bbox, frame_idx=start_frame, obj_id=0)

    # Create output directory if it doesn't exist
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Prepare output video path
    video_name = osp.basename(video_path)
    name_without_ext = osp.splitext(video_name)[0]
    output_video_path = osp.join(output_dir, f"{name_without_ext}_tracked.mp4")
    
    # Open input video to get properties
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Store tracking results for video generation
    tracking_results = {}

    # Propagate the object mask throughout the video
    # We don't use start_frame_idx because it can cause KeyError in SAMURAI mode
    # when looking for previous frames that don't exist in the tracking history
    for frame_idx, object_ids, masks in predictor.propagate_in_video(state):
        # Only process and output frames from the start_frame onwards
        if frame_idx >= start_frame:
            for obj_id, mask in zip(object_ids, masks):
                # Convert mask to binary and compute bounding rectangle
                mask_np = mask[0].cpu().numpy()
                mask_bin = mask_np > 0.0
                non_zero = np.argwhere(mask_bin)
                if non_zero.size == 0:
                    bbox = [0, 0, 0, 0]
                else:
                    y_min, x_min = non_zero.min(axis=0).tolist()
                    y_max, x_max = non_zero.max(axis=0).tolist()
                    bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
                
                # Calculate centroid
                centroid_x = bbox[0] + bbox[2] / 2  # x + width/2
                centroid_y = bbox[1] + bbox[3] / 2  # y + height/2
                
                # Store tracking result for this frame
                tracking_results[frame_idx] = {
                    'bbox': bbox,
                    'centroid': (centroid_x, centroid_y),
                    'mask': mask_np
                }
                
                # Write output row: video_path, frame, object_id, x, y, width, height, centroid_x, centroid_y
                writer.writerow([video_path, frame_idx, obj_id, bbox[0], bbox[1], bbox[2], bbox[3], centroid_x, centroid_y])
    
    # Generate output video with tracking overlays
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Draw tracking results if available for this frame
        if frame_idx in tracking_results:
            result = tracking_results[frame_idx]
            bbox = result['bbox']
            centroid = result['centroid']
            
            # Draw bounding box
            cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), 
                         (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3])), 
                         (0, 255, 0), 2)
            
            # Draw centroid
            cv2.circle(frame, (int(centroid[0]), int(centroid[1])), 5, (0, 0, 255), -1)
            
            # Add frame number and centroid text
            cv2.putText(frame, f"Frame: {frame_idx}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f"Centroid: ({int(centroid[0])}, {int(centroid[1])})", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out_video.write(frame)
        frame_idx += 1
    
    # Clean up
    cap.release()
    out_video.release()
    
    print(f"Saved tracked video: {output_video_path}")

    # Clean up state for this video
    del state
    gc.collect()
    torch.cuda.empty_cache()

# Main entrypoint
def main(args):
    # Determine SAM2 config and build predictor once
    model_cfg = determine_model_cfg(args.model_path)
    predictor = build_sam2_video_predictor(model_cfg, args.model_path, device=args.device)

    # Open output CSV for writing tracking results
    output_csv = "tracking_results.csv"
    with open(output_csv, 'w', newline='') as out_f:
        writer = csv.writer(out_f)
        writer.writerow(['video_path', 'frame', 'object_id', 'x', 'y', 'width', 'height', 'centroid_x', 'centroid_y'])

        # Read input boxes.csv (hard-coded)
        with open('boxes.csv', newline='') as in_f:
            reader = csv.DictReader(in_f)
            for row in reader:
                video_path = row['video_path']
                start_frame = int(row['frame'])
                x = float(row['x']); y = float(row['y'])
                w = float(row['width']); h = float(row['height'])
                # Convert to SAM2 box format: (x1, y1, x2, y2)
                initial_bbox = (int(x), int(y), int(x + w), int(y + h))
                process_tracking(predictor, video_path, start_frame, initial_bbox, writer)

    # Final cleanup
    del predictor
    torch.clear_autocast_cache()
    print(f"Tracking complete. Results saved to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch video tracking from boxes.csv using SAM2")
    parser.add_argument("--model_path", default="sam2/checkpoints/sam2.1_hiera_base_plus.pt",
                        help="Path to the SAM2 model checkpoint.")
    parser.add_argument("--device", default="cuda:0", help="Compute device for inference.")
    args = parser.parse_args()
    main(args)
