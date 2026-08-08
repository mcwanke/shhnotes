#!/usr/bin/env python3
"""Live test: capture your voice and transcribe to VTT."""

import sys
import os
import time
import logging

# Add CUDA library path
cuda_lib_path = os.path.expanduser("~/.local/lib/python3.14/site-packages/nvidia/cu13/lib")
if cuda_lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = f"{cuda_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

from shhnotes.audio import AudioCapture
from shhnotes.output import TranscriptSegment, format_as_vtt
from shhnotes import config
from faster_whisper import WhisperModel

logging.basicConfig(level=logging.INFO, format="%(message)s")

print("\n" + "="*70)
print("LIVE PIPELINE TEST")
print("="*70)

RECORD_DURATION = 10
OUTPUT_FILE = "/tmp/live_test.wav"

# Step 1: Prepare capture
print(f"\n[STEP 1] Validating audio sink '{config.PIPEWIRE_SINK_NAME}'...")
capture = AudioCapture(sink_name=config.PIPEWIRE_SINK_NAME)
if not capture.validate_sink_exists():
    print(f"✗ Sink not found")
    sys.exit(1)
print("✓ Sink ready")

# Step 2: Capture audio
print(f"\n[STEP 2] Recording {RECORD_DURATION} seconds...")
print(">>> SPEAK NOW! <<<")
start = time.time()
capture.record(OUTPUT_FILE, RECORD_DURATION)
capture_duration = time.time() - start
print(f"✓ Captured {capture_duration:.1f}s")

# Step 3: Load model
print(f"\n[STEP 3] Loading transcription model...")
model = WhisperModel(
    config.WHISPER_MODEL,
    device="cuda",
    compute_type=config.WHISPER_COMPUTE_TYPE
)
print("✓ Model loaded")

# Step 4: Transcribe
print(f"\n[STEP 4] Transcribing...")
segments_raw, info = model.transcribe(OUTPUT_FILE, beam_size=5)
segments_raw = list(segments_raw)

# Convert to our format
segments = [
    TranscriptSegment(s.start, s.end, s.text)
    for s in segments_raw
]

# Step 5: Display VTT output
print(f"\n[STEP 5] VTT Output:")
print("-" * 70)
vtt_output = format_as_vtt(segments)
print(vtt_output)
print("-" * 70)

print(f"\n[SUMMARY]")
print(f"  Language: {info.language} ({info.language_probability:.0%} confidence)")
print(f"  Segments: {len(segments)}")
print(f"  Duration: {segments[-1].end if segments else 0:.1f}s")

print("\n" + "="*70)
print("✓ Test complete")
print("="*70 + "\n")
