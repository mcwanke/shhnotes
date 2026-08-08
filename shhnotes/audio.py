"""Audio capture from PipeWire virtual sink (OBS monitor output)."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

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

    def record(self, output_file: str, duration_sec: int) -> bool:
        """
        Record audio from the configured sink to a WAV file.

        Records at 16kHz mono PCM (optimal for faster-whisper).

        Args:
            output_file: Path to save the WAV file
            duration_sec: Duration to record in seconds

        Returns:
            True if recording succeeded, False otherwise
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "pw-record",
            "--format=s16",  # 16-bit signed PCM (compatible with WAV)
            "--rate=16000",  # 16 kHz for faster-whisper
            "--channels=1",  # Mono
            "--latency=20ms",  # Low-latency buffer
            f"--target={self.sink_name}",
            str(output_file),
        ]

        logger.info(f"Starting audio capture: {output_file} ({duration_sec}s)")
        logger.debug(f"pw-record command: {' '.join(cmd)}")

        try:
            self._recording_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            # Wait for recording duration + buffer margin
            time.sleep(duration_sec)

            # Terminate gracefully
            self._recording_process.terminate()
            try:
                self._recording_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("pw-record did not terminate, killing...")
                self._recording_process.kill()
                self._recording_process.wait()

            if output_path.exists():
                file_size_mb = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"Audio capture complete: {output_file} ({file_size_mb:.1f} MB)")
                return True
            else:
                logger.error(f"Output file not created: {output_file}")
                return False

        except FileNotFoundError:
            logger.error("pw-record not found. Install PipeWire tools: sudo dnf install pipewire-tools")
            return False
        except Exception as e:
            logger.error(f"Audio capture failed: {e}")
            return False

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
