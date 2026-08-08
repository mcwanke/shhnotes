#!/usr/bin/env python3
"""Quick validation of audio capture from PipeWire."""

from shhnotes.audio import AudioCapture, list_pipewire_sinks
from shhnotes import config
import logging

logging.basicConfig(level=logging.INFO)

print("\n" + "="*60)
print("Audio Capture Validation")
print("="*60)

# List available sinks
print("\n[1] Available PipeWire Sinks:")
sinks = list_pipewire_sinks()
for name, sink_id in sinks.items():
    print(f"    {name:40} (ID: {sink_id})")

# Initialize capture
print(f"\n[2] Initializing AudioCapture for '{config.PIPEWIRE_SINK_NAME}'...")
capture = AudioCapture(sink_name=config.PIPEWIRE_SINK_NAME)

# Validate sink exists
if capture.validate_sink_exists():
    print("    ✓ Sink found")
else:
    print("    ✗ Sink not found - may need to configure OBS output")

print("\n" + "="*60)
print("Validation complete")
print("="*60 + "\n")
