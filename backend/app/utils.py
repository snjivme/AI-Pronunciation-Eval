import os
import uuid
import shutil
from mutagen import File as MutagenFile

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_uploaded_file(file):
    extension = os.path.splitext(file.filename)[1]

    unique_name = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path


def get_audio_duration(file_path):
    audio = MutagenFile(file_path)

    if audio is None or not hasattr(audio, "info"):
        return None

    return audio.info.length