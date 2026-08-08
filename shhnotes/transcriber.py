"""Transcription client for remote transcriber service."""

import io
import json
import logging
from typing import Any

import numpy as np
import requests
from scipy.io import wavfile

from .config import Config

logger = logging.getLogger(__name__)


class Transcriber:
    """Client for transcriber service (hwdsl2/docker-whisper or similar)."""

    def __init__(self, service_url: str | None = None) -> None:
        """Initialize transcriber client.

        Args:
            service_url: Base URL of transcriber service (default from Config.TRANSCRIBER_URL).
        """
        if service_url is None:
            service_url = Config.TRANSCRIBER_URL
        self.service_url = service_url.rstrip("/")
        self._verify_service_ready()

    def _verify_service_ready(self) -> None:
        """Check if transcriber service is reachable."""
        try:
            resp = requests.get(f"{self.service_url}/health", timeout=2)
            if resp.status_code == 200:
                logger.info(f"Transcriber service ready: {self.service_url}")
            else:
                logger.warning(f"Transcriber service returned {resp.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning(
                f"Transcriber service not reachable at {self.service_url}. "
                "Make sure it's running (docker-compose up)"
            )
        except Exception as e:
            logger.warning(f"Could not verify transcriber service: {e}")

    def transcribe(
        self, audio: np.ndarray | str, language: str = "en"
    ) -> list[dict[str, Any]]:
        """Transcribe audio and return timestamped segments.

        Args:
            audio: Audio as numpy array (mono, 16kHz) or path to audio file.
            language: ISO 639-1 language code (default: "en").

        Returns:
            List of dicts with keys: start (float), end (float), text (str).

        Raises:
            requests.exceptions.RequestException: If transcriber service fails.
        """
        # Convert numpy array to WAV bytes
        if isinstance(audio, np.ndarray):
            wav_bytes = self._numpy_to_wav(audio)
        else:
            with open(audio, "rb") as f:
                wav_bytes = f.read()

        # Send to transcriber service (OpenAI-compatible API)
        try:
            resp = requests.post(
                f"{self.service_url}/v1/audio/transcriptions",
                files={"file": ("audio.wav", wav_bytes, "audio/wav")},
                data={"language": language, "response_format": "json"},
                timeout=600,  # Long timeout for large files
            )
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error("Transcriber service timed out")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to transcriber service at {self.service_url}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"Transcriber service error: {e.response.text}")
            raise

        # Parse response (OpenAI format)
        data = resp.json()
        logger.debug(f"Transcriber response keys: {data.keys()}")

        # fedirz returns either segments array or just text field
        segments = data.get("segments", [])

        if not segments and "text" in data:
            # Fallback: if no segments, use the full text as one segment
            logger.info("No segments in response, using full text as single segment")
            full_text = data.get("text", "")
            return [{"start": 0.0, "end": 0.0, "text": full_text}] if full_text else []

        # Normalize segment format
        return [
            {"start": float(seg.get("start", 0)), "end": float(seg.get("end", 0)), "text": seg.get("text", "")}
            for seg in segments
        ]

    @staticmethod
    def _numpy_to_wav(audio: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Convert numpy array to WAV bytes.

        Args:
            audio: Audio as int16 numpy array.
            sample_rate: Sample rate (default: 16000).

        Returns:
            WAV-formatted bytes.
        """
        wav_buffer = io.BytesIO()
        wavfile.write(wav_buffer, sample_rate, audio.astype(np.int16))
        wav_buffer.seek(0)
        return wav_buffer.read()
