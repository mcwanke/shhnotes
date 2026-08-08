#!/usr/bin/env python3
"""End-to-end test: capture audio from OBS and transcribe."""

import sys
import os
import time
import logging
from pathlib import Path

# Add CUDA library path
cuda_lib_path = os.path.expanduser("~/.local/lib/python3.14/site-packages/nvidia/cu13/lib")
if cuda_lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = f"{cuda_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

from shhnotes.audio import AudioCapture
from shhnotes import config
from faster_whisper import WhisperModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("End-to-End Pipeline Test: OBS → Audio Capture → Transcription")
print("="*70)

# Configuration
RECORD_DURATION = 10  # seconds
OUTPUT_FILE = "/tmp/shhnotes_test.wav"

# Step 1: Validate sink
print("\n[1] Validating PipeWire sink...")
capture = AudioCapture(sink_name=config.PIPEWIRE_SINK_NAME)
if not capture.validate_sink_exists():
    logger.error(f"Sink '{config.PIPEWIRE_SINK_NAME}' not found. Check OBS configuration.")
    sys.exit(1)

# Step 2: Capture audio
print(f"\n[2] Capturing audio from '{config.PIPEWIRE_SINK_NAME}' for {RECORD_DURATION}s...")
print("    → Speak into the Blue Mic now!")
start_capture = time.time()
success = capture.record(OUTPUT_FILE, RECORD_DURATION)
capture_time = time.time() - start_capture

if not success:
    logger.error("Audio capture failed")
    sys.exit(1)

# Step 3: Load transcription model
print(f"\n[3] Loading faster-whisper model '{config.WHISPER_MODEL}'...")
start_load = time.time()
model = WhisperModel(
    config.WHISPER_MODEL,
    device="cuda",
    compute_type=config.WHISPER_COMPUTE_TYPE
)
load_time = time.time() - start_load

# Step 4: Transcribe
print(f"\n[4] Transcribing audio...")
start_transcribe = time.time()
segments, info = model.transcribe(OUTPUT_FILE, beam_size=5)
segments = list(segments)
transcribe_time = time.time() - start_transcribe

# Step 5: Display results
print(f"\n[5] Results:")
print(f"    Language: {info.language} (confidence: {info.language_probability:.1%})")
print(f"    Capture time: {capture_time:.1f}s")
print(f"    Model load time: {load_time:.1f}s")
print(f"    Transcription time: {transcribe_time:.1f}s")

print(f"\n[6] Transcript:")
if segments:
    for segment in segments:
        print(f"    [{segment.start:05.1f}s - {segment.end:05.1f}s] {segment.text}")
else:
    print("    (no speech detected)")

print("\n" + "="*70)
print("✓ Pipeline test complete")
print("="*70 + "\n")
