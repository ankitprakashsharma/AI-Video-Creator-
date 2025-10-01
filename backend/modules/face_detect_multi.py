# modules/face_detector.py
import face_recognition
import cv2
import os
from PIL import Image
import numpy as np

from PIL import Image
import numpy as np

def load_reference_encodings(ref_images: list[str] | None):
    encodings = []
    if not ref_images:
        return encodings
    for img_path in ref_images:
        try:
            # Open the image with PIL and convert to RGB
            with Image.open(img_path) as img:
                rgb_img = img.convert("RGB")
                image = np.array(rgb_img)
            
            # Now pass the standardized numpy array to face_encodings
            encs = face_recognition.face_encodings(image)
            if encs:
                encodings.append(encs[0])
            else:
                print(f"Warning: No faces found in reference image {img_path}")
        except Exception as e:
            print(f"Warning: Could not process reference image {img_path}. Error: {e}")
    return encodings

def get_multi_person_timestamps(video_path: str, frame_rate: int = 1, reference_paths: list[str] | None = None) -> dict:
    paths = reference_paths or []
    ref_encodings = load_reference_encodings(paths)
    print(f"Loaded {len(ref_encodings)} reference encodings.")

    video = cv2.VideoCapture(video_path)
    fps = int(video.get(cv2.CAP_PROP_FPS))

    timestamps = {i: [] for i in range(len(ref_encodings))}
    frame_count = 0

    while video.isOpened():
        frame_id = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        success, frame = video.read()
        if not success:
            break

        if frame_id % (frame_rate * fps) == 0:
            frame_count += 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame)
            encodings = face_recognition.face_encodings(rgb_frame, locations)
            
            current_time = video.get(cv2.CAP_PROP_POS_MSEC) / 1000
            print(f"Processing frame {frame_count} at {current_time:.2f}s: Found {len(locations)} faces.")

            for (top, right, bottom, left), face_enc in zip(locations, encodings):
                matches = face_recognition.compare_faces(ref_encodings, face_enc, tolerance=0.6)
                for idx, match in enumerate(matches):
                    if match:
                        print(f"  - Match found for reference person {idx}!")
                        timestamp = current_time
                        if not timestamps[idx] or timestamp - timestamps[idx][-1][1] > 1:
                            timestamps[idx].append([timestamp, timestamp])
                        else:
                            timestamps[idx][-1][1] = timestamp

    video.release()
    print("Finished processing video for face detection.")
    return timestamps
