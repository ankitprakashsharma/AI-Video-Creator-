# backend/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import List, Optional
from modules.face_detect_multi import get_multi_person_timestamps
from modules.script_gen import generate_script
from modules.music_selector import select_music
from modules.video_composer_multi import compose_video_with_music
import face_recognition
import shutil
import os
import pickle
import cv2
import uuid
from moviepy.editor import VideoFileClip
from moviepy.video.fx.resize import resize as vfx_resize
from filelock import FileLock

app = FastAPI()

# CORS for local frontend
# Get CORS origins from environment, default to local dev server
cors_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5174").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FACES_DIR = "static/faces"
UPLOADS_DIR = "static/uploads"
ENCODINGS_FILE = "static/encodings.pkl"
ENCODINGS_LOCK_FILE = "static/encodings.pkl.lock"

if not os.path.exists(FACES_DIR):
    os.makedirs(FACES_DIR)
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

import uuid

# Utility to persist uploaded files under UPLOADS_DIR
def save_upload_file(file: UploadFile) -> str:
    safe_name = file.filename or "uploaded.bin"
    _, ext = os.path.splitext(safe_name)
    unique_filename = f"{uuid.uuid4()}{ext}"
    out_path = os.path.join(UPLOADS_DIR, unique_filename)
    with open(out_path, "wb") as out_f:
        shutil.copyfileobj(file.file, out_f)
    return out_path

# Compress uploaded video to reduce processing cost
def compress_video(input_path: str, max_width: int = 360, target_bitrate: str = "500k") -> str:
    try:
        clip = VideoFileClip(input_path)
    except Exception:
        return input_path
    width, height = clip.w, clip.h
    resized_clip = clip
    if width and width > max_width:
        resized_clip = vfx_resize(clip, width=max_width)
    out_name = f"{os.path.splitext(os.path.basename(input_path))[0]}_small.mp4"
    out_path = os.path.join(UPLOADS_DIR, out_name)
    try:
        resized_clip.write_videofile(
            out_path,
            codec="libx264",
            audio_codec="aac",
            bitrate=target_bitrate,
            threads=2,
            logger=None,
        )
        clip.close()
        if resized_clip is not clip:
            resized_clip.close()
        return out_path
    except Exception:
        try:
            clip.close()
            if resized_clip is not clip:
                resized_clip.close()
        except Exception:
            pass
        return input_path

# Compress image references (downscale to max 720px on longer side, JPEG quality ~70)
def compress_image(input_path: str, max_side: int = 480, jpeg_quality: int = 70) -> str:
    try:
        img = cv2.imread(input_path)
        if img is None:
            return input_path
        h, w = img.shape[:2]
        scale = 1.0
        longer = max(h, w)
        if longer > max_side:
            scale = max_side / float(longer)
        if scale != 1.0:
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        out_name = f"{os.path.splitext(os.path.basename(input_path))[0]}_small.jpg"
        out_path = os.path.join(UPLOADS_DIR, out_name)
        cv2.imwrite(out_path, img, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
        return out_path
    except Exception:
        return input_path

@app.post("/upload-face/")
async def upload_face(file: UploadFile = File(...)):
    safe_filename = file.filename or "uploaded_file"
    file_path = os.path.join(FACES_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Load face and encode
    image = face_recognition.load_image_file(file_path)
    encodings = face_recognition.face_encodings(image)

    if encodings:
        lock = FileLock(ENCODINGS_LOCK_FILE)
        with lock:
            if os.path.exists(ENCODINGS_FILE):
                with open(ENCODINGS_FILE, "rb") as f:
                    data = pickle.load(f)
            else:
                data = []

            data.append({"filename": file.filename, "encoding": encodings[0].tolist()})
            
            with open(ENCODINGS_FILE, "wb") as f:
                pickle.dump(data, f)

        return {"status": "success", "message": f"Face saved for {file.filename}"}
    else:
        return {"status": "error", "message": "No face detected in the image"}


@app.post("/api/process")
async def process(
    video: UploadFile = File(...),
    prompt: str = Form(...),
    references: Optional[List[UploadFile]] = File(default=None)
):
    try:
        # Save and compress main video
        video_path = save_upload_file(video)
        compressed_video_path = compress_video(video_path)

        # Optionally save and compress reference images
        _saved_refs = []
        if references:
            _saved_refs = [compress_image(save_upload_file(ref)) for ref in references]

        # Run detection
        timestamps = get_multi_person_timestamps(
            compressed_video_path,
            frame_rate=0.5,
            reference_paths=_saved_refs if references else None
        )

        # Generate script (fallback if OPENAI_API_KEY is missing)
        try:
            if os.getenv("OPENAI_API_KEY"):
                script = generate_script(prompt, timestamps)
            else:
                script = prompt or ""
        except Exception as e:
            print(f"Script generation failed: {e}")
            script = prompt or ""

        # Select background music
        music_path = select_music(script)

        # Compose final video
        final = compose_video_with_music(compressed_video_path, timestamps, music_path, script)

        return JSONResponse({
            "status": "done",
            "video_url": f"/static/uploads/{os.path.basename(final)}",
            "script": script
        })
    except Exception as e:
        import traceback
        error_details = f"Error in /api/process: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(error_details)
        raise HTTPException(status_code=500, detail=str(e))


# removed duplicate minimal /api/process in favor of unified handler above
