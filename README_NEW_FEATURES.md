# Updated Video Tracking Workflow

## New Features Added

### 1. Enhanced CSV Output with Centroid Tracking
- **New Columns**: Added `centroid_x` and `centroid_y` columns to tracking results
- **Calculation**: Centroid = (x + width/2, y + height/2)
- **Benefits**: Provides precise center point tracking for better analysis

### 2. Video Export with Tracking Overlays
- **Output Location**: `outputs/` folder (created automatically)
- **Naming Convention**: `{original_name}_tracked.mp4`
- **Visual Overlays**:
  - Green bounding boxes around tracked objects
  - Red dots marking centroids
  - Frame numbers and centroid coordinates as text overlays
- **Format**: MP4 with same resolution and framerate as original

### 3. Data Backup and Safety
- **Automatic Backup**: Creates timestamped backup files (`boxes_backup_YYYYMMDD_HHMMSS.csv`)
- **Safety First**: Saves all annotation data before starting SAM2 processing
- **Recovery**: Preserves user work even if processing fails

### 4. Enhanced User Interface
- **Progress Feedback**: Shows processing status to user
- **Error Handling**: Displays informative error messages
- **Success Notifications**: Confirms completion with file locations

## File Structure After Processing

```
samurai/
├── boxes.csv                          # Current annotation data
├── boxes_backup_20250716_143022.csv   # Timestamped backup
├── tracking_results.csv               # Detailed tracking results
├── outputs/                           # New output folder
│   ├── video1_tracked.mp4             # Tracked video with overlays
│   └── video2_tracked.mp4             # Another tracked video
└── scripts/
    └── demo2.py                       # Updated backend script
```

## CSV Format Changes

### Input Format (boxes.csv)
```csv
video_path,frame,x,y,width,height
video1.mp4,27,102,542,41,33
video2.mp4,45,293,508,56,56
```

### Output Format (tracking_results.csv)
```csv
video_path,frame,object_id,x,y,width,height,centroid_x,centroid_y
video1.mp4,27,0,102,542,41,33,122.5,558.5
video1.mp4,28,0,103,543,42,34,124.0,560.0
video2.mp4,45,0,293,508,56,56,321.0,536.0
video2.mp4,46,0,294,509,57,57,322.5,537.5
```

## Usage Instructions

1. **Load Videos**: Use the frontend to load multiple videos
2. **Annotate**: Navigate to desired frames and draw bounding boxes
3. **Save**: Click "Save Frame" for each video
4. **Process**: Click "Finish" to:
   - Save annotation data with backup
   - Run SAM2 tracking
   - Generate tracked videos with overlays
   - Create detailed CSV with centroid data

## Error Recovery

If processing fails or is interrupted:
1. Your annotations are preserved in `boxes.csv`
2. Timestamped backups are available in `boxes_backup_*.csv`
3. You can restart the process without losing work
4. Check error messages for troubleshooting information

## Performance Notes

- **Memory Usage**: Videos are processed one at a time to conserve memory
- **Processing Time**: Depends on video length and resolution
- **Storage**: Tracked videos are saved in compressed MP4 format
- **GPU Acceleration**: Utilizes CUDA when available for faster processing

## Output Analysis

The enhanced CSV format enables:
- **Trajectory Analysis**: Track object movement over time
- **Speed Calculations**: Compute velocity from centroid positions
- **Behavioral Studies**: Analyze movement patterns
- **Statistical Analysis**: Export to tools like Excel, R, or Python for further analysis
