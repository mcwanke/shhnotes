"""Audio capture from PipeWire virtual sink (OBS monitor output)."""

import logging
import subprocess
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def list_pipewire_sinks() -> dict[str, str]:
    """
    List all PipeWire sinks.

    Returns:
        Dict mapping sink name to sink ID (e.g., {'obs-monitor': '47'})
    """
    try:
        result = subprocess.run(
            ["pactl", "list", "sinks", "short"],
            capture_output=True,
            text=True,
            check=True,
        )
        sinks = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                sink_id = parts[0].strip()
                sink_name = parts[1].strip()
                sinks[sink_name] = sink_id
        return sinks
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to list PipeWire sinks: {e}")
        return {}


class AudioCapture:
    """Capture audio from a PipeWire virtual sink."""

    def __init__(self, sink_name: str = "obs-monitor"):
        """
        Initialize audio capture.

        Args:
            sink_name: Name of the PipeWire sink to capture from (e.g., 'obs-monitor')
        """
        self.sink_name = sink_name
        self._recording_process: Optional[subprocess.Popen] = None

    def validate_sink_exists(self) -> bool:
        """Check if the configured sink exists."""
        sinks = list_pipewire_sinks()
        if self.sink_name in sinks:
            logger.info(f"Found PipeWire sink: {self.sink_name} (ID: {sinks[self.sink_name]})")
            return True
        logger.warning(
            f"PipeWire sink '{self.sink_name}' not found. Available sinks: {list(sinks.keys())}"
        )
        return False

    def start_recording(self) -> bool:
        """
        Start streaming audio from the configured sink.

        Spawns pw-record process that outputs raw PCM to stdout (16kHz mono).

        Returns:
            True if process started successfully, False otherwise.
        """
        # Get the numeric ID for the sink (pw-record requires ID, not name)
        sinks = list_pipewire_sinks()
        if self.sink_name not in sinks:
            logger.error(f"PipeWire sink '{self.sink_name}' not found")
            return False

        sink_id = sinks[self.sink_name]

        cmd = [
            "pw-record",
            "--format=s16",  # 16-bit signed PCM
            "--rate=16000",  # 16 kHz for faster-whisper
            "--channels=1",  # Mono
            "--latency=20ms",  # Low-latency buffer
            f"--target={sink_id}",
            "-",  # Output to stdout
        ]

        logger.info(f"Starting audio capture from sink: {self.sink_name}")
        logger.debug(f"pw-record command: {' '.join(cmd)}")

        try:
            self._recording_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )
            logger.info("Audio capture started")
            return True
        except FileNotFoundError:
            logger.error("pw-record not found. Install PipeWire tools: sudo dnf install pipewire-tools")
            return False
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            return False

    def read_chunk(self, num_samples: int = 16000) -> Optional[np.ndarray]:
        """
        Read audio chunk from the recording stream.

        Args:
            num_samples: Number of audio samples to read (default: 1 second at 16kHz).

        Returns:
            Numpy array of int16 samples, or None if stream ended or error.
        """
        if not self._recording_process or not self._recording_process.stdout:
            logger.error("Recording not started")
            return None

        try:
            # 16-bit PCM = 2 bytes per sample
            byte_size = num_samples * 2
            data = self._recording_process.stdout.read(byte_size)

            if not data:
                logger.debug("Audio stream ended")
                return None

            audio_chunk = np.frombuffer(data, dtype=np.int16)
            return audio_chunk

        except Exception as e:
            logger.error(f"Error reading audio chunk: {e}")
            return None

    def stop(self) -> None:
        """Stop the current recording."""
        if self._recording_process:
            logger.info("Stopping audio capture")
            self._recording_process.terminate()
            try:
                self._recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._recording_process.kill()
                self._recording_process.wait()
