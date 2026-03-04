import os

OUTPUT_DIR = os.path.expanduser("~/Desktop/AI-Music")
STEMS_DIR = os.path.join(OUTPUT_DIR, "stems")
CONVERTED_DIR = os.path.join(OUTPUT_DIR, "converted")
MIXED_DIR = os.path.join(OUTPUT_DIR, "mixed")
BATCH_DIR = os.path.join(OUTPUT_DIR, "batch")

RVC_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai-music-rvc"))

SUPPORTED_FORMATS = {".wav", ".mp3", ".flac", ".m4a", ".ogg", ".aac"}
