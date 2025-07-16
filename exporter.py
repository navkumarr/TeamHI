import csv

def export_annotations_to_csv(annotations: dict, output_path: str) -> None:
    """
    Write video annotations to a CSV file.

    :param annotations: Mapping of video file paths to bounding box tuples (frame, x, y, width, height).
    :param output_path: Path to save the CSV.
    """
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # header row
        writer.writerow(['video_path', 'frame', 'x', 'y', 'width', 'height'])
        # write each annotation
        for path, (frame, x, y, w, h) in annotations.items():
            writer.writerow([path, frame, x, y, w, h])