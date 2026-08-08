"""Configuration for ShhNotes service."""

from pathlib import Path

# Audio capture
PIPEWIRE_SINK_NAME = "Vitrual_Shh"  # PipeWire virtual sink to capture from

# Transcription
WHISPER_MODEL = "large-v2"  # faster-whisper model size
WHISPER_COMPUTE_TYPE = "float16"  # float16 for GPU, int8 for CPU

# Output
OUTPUT_DIR = Path.home() / "Documents" / "shhnotes" / "transcripts"

# API
API_HOST = "127.0.0.1"
API_PORT = 5444

# OBS websocket (optional)
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = ""  # Set if OBS websocket auth is enabled

# Logging
LOG_LEVEL = "INFO"
