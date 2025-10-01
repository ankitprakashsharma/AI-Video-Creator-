import os
from uuid import uuid4
from config import UPLOAD_DIR

def save_upload_file(upload_file) -> str:
    """
    Save starndard UploadFile object from FastAPI to disk and return path.
    """
    ext = os.path.splitext(upload_file.filename or "")[1]
    filename = f"{uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    # ensure parent exists and write in chunks
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        while True:
            chunk = upload_file.file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    return filepath
