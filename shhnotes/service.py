"""Core service managing session lifecycle, audio capture, and transcription."""

import logging
import threading
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4

import numpy as np

from .audio import AudioCapture
from .config import Config
from .transcriber import Transcriber

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Session state machine."""

    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"


class Session:
    """Represents a single transcription session."""

    def __init__(self, label: str):
        self.session_id = str(uuid4())
        self.label = label
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.audio_buffer: list[np.ndarray] = []
        self.state = SessionState.IDLE
        self.segments: list[dict] = []

    def get_duration_seconds(self) -> float:
        """Return session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    def get_audio_array(self) -> np.ndarray:
        """Concatenate buffered chunks into single audio array."""
        if not self.audio_buffer:
            return np.array([], dtype=np.int16)
        return np.concatenate(self.audio_buffer)


class Service:
    """Manages session lifecycle, audio capture, and transcription."""

    def __init__(self):
        self.current_session: Optional[Session] = None
        self.audio_capture: Optional[AudioCapture] = None
        self.transcriber: Optional[Transcriber] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._stop_capture = False

        # Lazy-load transcriber on first use
        self._transcriber_lock = threading.Lock()

    def _get_transcriber(self) -> Transcriber:
        """Lazy-load transcriber (expensive operation)."""
        with self._transcriber_lock:
            if self.transcriber is None:
                logger.info("Loading transcriber model...")
                self.transcriber = Transcriber()
                logger.info("Transcriber ready")
            return self.transcriber

    def start_session(self, label: str = "default") -> str:
        """
        Start a new transcription session.

        Args:
            label: Session label for output file naming.

        Returns:
            Session ID.
        """
        if self.current_session and self.current_session.state != SessionState.IDLE:
            logger.warning("Session already in progress")
            return self.current_session.session_id

        # Create session
        self.current_session = Session(label)
        self.current_session.state = SessionState.RECORDING

        # Setup audio capture
        self.audio_capture = AudioCapture(Config.PIPEWIRE_SINK_NAME)
        if not self.audio_capture.validate_sink_exists():
            logger.error("PipeWire sink not found")
            self.current_session.state = SessionState.IDLE
            return ""

        # Start recording
        if not self.audio_capture.start_recording():
            logger.error("Failed to start audio capture")
            self.current_session.state = SessionState.IDLE
            return ""

        # Start capture thread
        self._stop_capture = False
        self._capture_thread = threading.Thread(target=self._capture_audio_loop, daemon=False)
        self._capture_thread.start()

        logger.info(f"Session started: {self.current_session.session_id} (label: {label})")
        return self.current_session.session_id

    def stop_session(self) -> bool:
        """
        Stop recording and trigger transcription.

        Returns:
            True if successful, False otherwise.
        """
        if not self.current_session or self.current_session.state == SessionState.IDLE:
            logger.warning("No active session")
            return False

        logger.info("Stopping session...")
        self.current_session.state = SessionState.TRANSCRIBING

        # Stop audio capture
        self._stop_capture = True
        if self.audio_capture:
            self.audio_capture.stop()

        # Wait for capture thread
        if self._capture_thread:
            self._capture_thread.join(timeout=5)

        # Transcribe
        audio_array = self.current_session.get_audio_array()
        if len(audio_array) == 0:
            logger.warning("No audio captured")
            self.current_session.state = SessionState.IDLE
            return False

        logger.info(f"Transcribing {len(audio_array)} samples...")
        transcriber = self._get_transcriber()
        self.current_session.segments = transcriber.transcribe(audio_array)

        # Write output
        self.current_session.end_time = datetime.now()
        self._write_output()

        self.current_session.state = SessionState.IDLE
        logger.info("Session complete")
        return True

    def get_status(self) -> str:
        """Return current session state."""
        if not self.current_session:
            return SessionState.IDLE.value
        return self.current_session.state.value

    def _capture_audio_loop(self) -> None:
        """Thread function that reads audio chunks and buffers them."""
        logger.debug("Capture thread started")
        chunk_samples = Config.SAMPLE_RATE  # 1 second chunks at configured sample rate
        total_samples = 0

        while not self._stop_capture and self.current_session:
            chunk = self.audio_capture.read_chunk(chunk_samples)
            if chunk is None:
                break

            self.current_session.audio_buffer.append(chunk)
            total_samples += len(chunk)

            if total_samples % (Config.SAMPLE_RATE * 10) == 0:  # Log every 10 seconds
                logger.debug(f"Captured {total_samples / Config.SAMPLE_RATE:.1f}s of audio")

        logger.debug(f"Capture thread ended. Total samples: {total_samples}")

    def _write_output(self) -> None:
        """Write session output as markdown."""
        if not self.current_session:
            logger.error("No current session")
            return

        if not self.current_session.segments:
            logger.warning(f"No segments to write. Audio buffer size: {len(self.current_session.audio_buffer)} chunks")
            return

        logger.info(f"Writing {len(self.current_session.segments)} segments to file")

        Config.ensure_output_dir()

        # Generate filename: YYYY-MM-DD-HH-MM-<label>.md
        timestamp = self.current_session.start_time.strftime("%Y-%m-%d-%H-%M")
        filename = f"{timestamp}-{self.current_session.label}.md"
        output_path = Config.OUTPUT_DIR / filename

        # Format duration
        duration = self.current_session.get_duration_seconds()
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        # Build markdown
        lines = [
            "# ShhNotes Transcript",
            "",
            f"- **Date:** {self.current_session.start_time.strftime('%Y-%m-%d')}",
            f"- **Label:** {self.current_session.label}",
            f"- **Duration:** {duration_str}",
            "",
            "---",
            "",
        ]

        for segment in self.current_session.segments:
            start_sec = segment["start"]
            text = segment["text"]
            hours = int(start_sec // 3600)
            minutes = int((start_sec % 3600) // 60)
            secs = start_sec % 60
            timestamp_str = f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
            lines.append(f"[{timestamp_str}] {text}")

        output_path.write_text("\n".join(lines))
        logger.info(f"Transcript written: {output_path}")
