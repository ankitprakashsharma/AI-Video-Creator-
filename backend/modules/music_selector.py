# modules/music_selector.py
from textblob import TextBlob
import random
import os

# Put your short mp3 files in static/uploads/music/{happy,sad,inspiring}/
MUSIC_DIR = os.path.join("static", "uploads", "music")
MUSIC_LIBRARY = {
    "happy": [
        os.path.join(MUSIC_DIR, "happy1.mp3"),
        os.path.join(MUSIC_DIR, "happy2.mp3")
    ],
    "sad": [
        os.path.join(MUSIC_DIR, "sad1.mp3"),
        os.path.join(MUSIC_DIR, "sad2.mp3")
    ],
    "inspiring": [
        os.path.join(MUSIC_DIR, "inspiring1.mp3")
    ]
}

def select_music(script_text: str) -> str | None:
    polarity = float(getattr(TextBlob(script_text).sentiment, "polarity", 0.0))
    if polarity > 0.25:
        mood = "happy"
    elif polarity < -0.1:
        mood = "sad"
    else:
        mood = "inspiring"
    
    choices = MUSIC_LIBRARY.get(mood, [])
    # Filter out files that don't exist
    choices = [p for p in choices if os.path.exists(p)]
    if not choices:
        return None
    return random.choice(choices)
