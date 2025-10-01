# modules/face_detector.py
import face_recognition
import cv2
import numpy as np

def load_reference_encodings(ref_images: list[str] | None):
    encodings = []
    if not ref_images:
        return encodings
    for img_path in ref_images:
        try:
            image = face_recognition.load_image_file(img_path)
            if image is None:
                print(f"Warning: Could not read {img_path}")
                continue
            if image.dtype != np.uint8:
                image = image.astype(np.uint8)
            encs = face_recognition.face_encodings(image)
            if encs:
                encodings.append(encs[0])
            else:
                print(f"Warning: No faces found in reference image {img_path}")
        except Exception as e:
            print(f"Warning: Could not process {img_path}, error: {e}")
    return encodings


def get_multi_person_timestamps(video_path: str, frame_rate: int = 1, reference_paths: list[str] | None = None) -> dict:
    ref_encodings = load_reference_encodings(reference_paths or [])
    print(f"Loaded {len(ref_encodings)} reference encodings.")

    video = cv2.VideoCapture(video_path)
    fps = int(video.get(cv2.CAP_PROP_FPS)) or 25  # fallback if fps not detected

    timestamps = {i: [] for i in range(len(ref_encodings))}
    frame_count = 0

    while True:
        success, frame = video.read()
        if not success or frame is None:
            break

        frame_id = int(video.get(cv2.CAP_PROP_POS_FRAMES))

        if frame_id % (frame_rate * fps) == 0:
            frame_count += 1

            # 🔑 Make sure frame is valid
            if not isinstance(frame, np.ndarray):
                print(f"Skipping invalid frame at {frame_id}")
                continue

            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)

            if len(frame.shape) == 2:  
                # grayscale → convert to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:  
                # RGBA → drop alpha
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            else:
                # Normal BGR
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                locations = face_recognition.face_locations(rgb_frame, model="hog")
                encodings = face_recognition.face_encodings(rgb_frame, locations)
            except Exception as e:
                print(f"⚠️ Error in face detection on frame {frame_id}: {e}")
                continue

            current_time = video.get(cv2.CAP_PROP_POS_MSEC) / 1000
            print(f"Frame {frame_count} @ {current_time:.2f}s → {len(locations)} faces found.")

            for face_enc in encodings:
                matches = face_recognition.compare_faces(ref_encodings, face_enc, tolerance=0.6)
                for idx, match in enumerate(matches):
                    if match:
                        print(f"✅ Match for reference person {idx}")
                        timestamp = current_time
                        if not timestamps[idx] or timestamp - timestamps[idx][-1][1] > 1:
                            timestamps[idx].append([timestamp, timestamp])
                        else:
                            timestamps[idx][-1][1] = timestamp

    video.release()
    print("✔ Finished processing video.")
    return timestamps
