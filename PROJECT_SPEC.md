# PROJECT_SPEC.md — ShhNotes

> A local voice transcription service. Drop audio in, get markdown out.

ShhNotes captures audio from a single PipeWire virtual sink, transcribes it locally using faster-whisper on a GPU, and writes timestamped markdown files to disk. It runs as a background service on Fedora Linux, controlled via CLI and StreamDeck buttons. No cloud. No UI. No database.

---

## The Problem It Solves

Two scenarios drive this:

1. **Online meetings** — capture both local mic and remote audio (browser, Zoom, etc.), mix them in OBS, transcribe the combined feed.
2. **On-the-fly voice notes** — speak into the mic to capture ideas, get a transcript written to disk.

From ShhNotes' perspective these are identical. OBS handles all audio source complexity and outputs a single monitor sink. ShhNotes reads that one sink regardless of what's feeding it.

---

## Architecture

```
[Mic input]  ──┐
                ├──► OBS (mixing, virtual monitor sink) ──► ShhNotes service ──► .md file
[App audio]  ──┘
```

### Audio Layer
- **PipeWire** is the audio system (Fedora default)
- **qpwgraph** manages virtual sinks and routing
- **OBS** acts as the audio abstraction layer — all sources route into OBS, which outputs a single named PipeWire virtual monitor sink
- ShhNotes reads only that one sink; it has no knowledge of upstream sources

### Transcription Layer
- **faster-whisper** running in a Docker container with CUDA GPU passthrough
- Model: `large-v2` (fits comfortably in 8GB VRAM on RTX 3070)
- ShhNotes calls faster-whisper via its Python API (not over HTTP — direct library call or inter-container IPC TBD at implementation)
- Audio is captured in chunks and fed to the transcription pipeline

### Service Layer
- Python service (`service.py`) manages session state, audio capture loop, and coordinates transcription
- FastAPI (`api.py`) exposes a local HTTP interface on `localhost:5444`
- CLI (`cli.py`) is a thin wrapper around the API
- StreamDeck integration (`streamdeck.py`) drives buttons via `python-elgato-streamdeck` — buttons call the same API endpoints, and the service pushes state back to button lighting
- OBS bridge (`obs_bridge.py`) listens to OBS websocket events to auto-start/stop capture when OBS begins/ends recording

### Output Layer
- Transcripts written as `.md` files to `~/Documents/shhnotes/transcripts/`
- File naming: `YYYY-MM-DD-HH-MM-<label>.md`
- Label is passed at session start (e.g. `--label "standup"` or `--label "idea"`)
- Output format: markdown with session header block + timestamped transcript segments

---

## Component Detail

### `service.py`
The core. Manages session lifecycle (idle → recording → transcribing → done), runs the audio capture loop, coordinates with transcriber, writes output via `output.py`. Exposes session state for the API to serve.

### `api.py`
FastAPI app on `localhost:5444`. Endpoints:
- `POST /start` — start a session, accepts optional `label` param
- `POST /stop` — stop recording, trigger transcription of remaining buffer, write output
- `GET /status` — returns current state: `idle | recording | transcribing`

### `cli.py`
Thin CLI wrapper. Calls the API. Three commands mirror the three endpoints: `shhnotes start [--label <label>]`, `shhnotes stop`, `shhnotes status`.

### `streamdeck.py`
Drives the StreamDeck via `python-elgato-streamdeck`. Three buttons:
- **Start** — calls `POST /start`
- **Stop** — calls `POST /stop`
- **Status** — displays current state; button color reflects state (green = recording, yellow = transcribing, white = idle)

### `obs_bridge.py`
Connects to OBS via `obs-websocket-py`. Listens for `RecordStateChanged` events. When OBS starts recording → calls `POST /start`. When OBS stops → calls `POST /stop`. Optional — OBS integration is not required for the service to function.

### `transcriber.py`
Wraps faster-whisper. Accepts audio data, returns list of timestamped segments `[{ start, end, text }]`. Handles model loading and GPU device binding.

### `output.py`
Formats transcriber output into markdown and writes to disk. Generates filename from timestamp + label. Writes session header (date, label, duration) followed by timestamped transcript body.

### `config.py`
Single source of truth for all tunables:
- PipeWire sink name to read from
- faster-whisper model size
- Output directory path
- API port (default: `5444`)
- OBS websocket host/port/password

---

## Output Format

```markdown
# ShhNotes Transcript

- **Date:** 2026-08-08
- **Label:** standup
- **Duration:** 00:32:14

---

[00:00:04] Good morning everyone, let's get started.
[00:00:09] Quick update on the backend work from yesterday...
```

---

## Docker Setup

faster-whisper runs in a Docker container with:
- NVIDIA CUDA base image
- GPU passthrough via `nvidia-container-toolkit`
- Container has access to the PipeWire sink via host audio device passthrough or shared socket (TBD at implementation)

`docker/faster-whisper/docker-compose.yml` defines the container.

---

## StreamDeck Notes

- StreamDeck device is already operational on Fedora
- udev rules are already configured
- Phase 0.1 uses `python-elgato-streamdeck` to drive buttons directly from the service rather than calling external scripts — this enables state pushback (button lighting)

---

## Phase 0.1 Scope

**In scope:**
- Python service with session lifecycle management
- FastAPI on localhost:5444
- CLI (start / stop / status)
- faster-whisper Docker container with CUDA
- Audio capture from named PipeWire sink (OBS monitor output)
- StreamDeck integration (3 buttons: start, stop, status with color state)
- OBS websocket bridge (auto start/stop on OBS record)
- Markdown output to `~/Documents/shhnotes/transcripts/`
- `config.py` for all tunables

**Explicitly out of scope for 0.1:**
- LLM-synthesized notes (raw transcript only)
- Speaker diarization
- Real-time transcript display
- Any web UI
- Any database or search
- Re-transcription of saved audio
- Audio archiving

---

## Key Decisions Log

| Decision | Rationale |
|---|---|
| OBS as audio abstraction layer | Simplifies ShhNotes — one input sink regardless of source count. Visual routing in OBS. Accepts OBS-as-dependency risk. |
| faster-whisper over stock Whisper | Faster inference, lower VRAM, same accuracy. Better fit for near-real-time on 3070. |
| faster-whisper called as Python library, not HTTP | Avoids unnecessary network hop for same-machine inference. |
| FastAPI on localhost only | Simple, typed, no external exposure. Port 5444 (play on "shh"). |
| python-elgato-streamdeck over script-per-button | Enables state pushback to button lighting. Keeps control surface integrated with service state. |
| Markdown files, no database | MVP simplicity. Searchable via filesystem tools. BlackHole or similar can ingest later if desired. |
| Output to `~/Documents/shhnotes/transcripts/` | Configurable default. Consistent, findable location. |
| No real-time transcript display in 0.1 | Complexity/value tradeoff. Raw .md output is sufficient for MVP. |
