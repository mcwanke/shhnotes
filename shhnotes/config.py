"""Configuration and environment setup for ShhNotes."""

import os
from pathlib import Path


class Config:
    """Central configuration store. All tunables sourced from environment or defaults."""

    # Audio capture
    PIPEWIRE_SINK_NAME: str = os.getenv(
        "SHHNOTES_SINK_NAME", "Vitrual_Shh"
    )
    SAMPLE_RATE: int = int(os.getenv("SHHNOTES_SAMPLE_RATE", "16000"))
    CHUNK_SIZE_MS: int = int(os.getenv("SHHNOTES_CHUNK_SIZE_MS", "1000"))

    # Transcription
    WHISPER_MODEL_SIZE: str = os.getenv("SHHNOTES_MODEL_SIZE", "large-v2")
    WHISPER_DEVICE: str = os.getenv("SHHNOTES_DEVICE", "cuda")
    WHISPER_COMPUTE_TYPE: str = os.getenv("SHHNOTES_COMPUTE_TYPE", "float16")

    # Output
    OUTPUT_DIR: Path = Path(
        os.getenv(
            "SHHNOTES_OUTPUT_DIR",
            "~/Documents/shhnotes/transcripts"
        )
    ).expanduser()

    # API
    API_HOST: str = os.getenv("SHHNOTES_API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("SHHNOTES_API_PORT", "5444"))

    # Transcriber service
    TRANSCRIBER_URL: str = os.getenv("SHHNOTES_TRANSCRIBER_URL", "http://localhost:5445")

    # OBS websocket (optional)
    OBS_HOST: str = os.getenv("SHHNOTES_OBS_HOST", "localhost")
    OBS_PORT: int = int(os.getenv("SHHNOTES_OBS_PORT", "4455"))
    OBS_PASSWORD: str = os.getenv("SHHNOTES_OBS_PASSWORD", "")

    # Logging
    LOG_LEVEL: str = os.getenv("SHHNOTES_LOG_LEVEL", "INFO")

    @classmethod
    def ensure_output_dir(cls) -> None:
        """Create output directory if it doesn't exist."""
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
