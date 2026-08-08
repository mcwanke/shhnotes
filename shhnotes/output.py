"""Format and write transcripts to files."""

from pathlib import Path
from datetime import datetime
from typing import List


class TranscriptSegment:
    """A single transcribed segment with timing."""

    def __init__(self, start: float, end: float, text: str):
        self.start = start  # seconds
        self.end = end      # seconds
        self.text = text

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Convert seconds to HH:MM:SS.mmm format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def to_vtt(self) -> str:
        """Format segment as VTT cue."""
        return f"{self._format_timestamp(self.start)} --> {self._format_timestamp(self.end)}\n{self.text}"


def format_as_vtt(segments: List[TranscriptSegment]) -> str:
    """Format segments as VTT string."""
    lines = ["WEBVTT", ""]
    for segment in segments:
        lines.append(segment.to_vtt())
        lines.append("")
    return "\n".join(lines)
