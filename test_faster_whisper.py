#!/usr/bin/env python3
"""Quick validation of faster-whisper with GPU acceleration."""

import sys
import os
import subprocess
import time

# Add CUDA libraries to path before importing torch
cuda_lib_path = os.path.expanduser("~/.local/lib/python3.14/site-packages/nvidia/cu13/lib")
if cuda_lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = f"{cuda_lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

from faster_whisper import WhisperModel

def check_gpu():
    """Check GPU status with nvidia-smi."""
    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used,memory.total', '--format=csv,noheader'],
                          capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return "GPU not available"

def main():
    print("=" * 60)
    print("Faster-Whisper GPU Validation Test")
    print("=" * 60)

    # Check GPU before
    print("\n[1] GPU Status Before:")
    print(f"    {check_gpu()}")

    # Load model
    print("\n[2] Loading model 'large-v2' on GPU...")
    start = time.time()
    model = WhisperModel("large-v2", device="cuda", compute_type="float16")
    load_time = time.time() - start
    print(f"    Model loaded in {load_time:.1f}s")

    # Check GPU after load
    print("\n[3] GPU Status After Load:")
    print(f"    {check_gpu()}")

    # Transcribe
    print("\n[4] Transcribing /tmp/test_audio.wav...")
    start = time.time()
    segments, info = model.transcribe("/tmp/test_audio.wav", beam_size=5)
    segments = list(segments)
    transcribe_time = time.time() - start

    print(f"    Transcription complete in {transcribe_time:.1f}s")
    print(f"    Language: {info.language}, Confidence: {info.language_probability:.2%}")

    # Check GPU after transcribe
    print("\n[5] GPU Status After Transcription:")
    print(f"    {check_gpu()}")

    # Print transcript
    print("\n[6] Transcript:")
    for segment in segments:
        print(f"    [{segment.start:05.1f}s - {segment.end:05.1f}s] {segment.text}")

    print("\n" + "=" * 60)
    print("✓ Validation complete")
    print("=" * 60)

if __name__ == "__main__":
    main()
