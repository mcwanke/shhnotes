# CLAUDE.md — AI Code Generation Context & Boundaries

## How to Work With Me

This file is consumed by AI-assisted code generation tooling at the start of every session. Read this file completely before writing or modifying any code. For full architecture detail, see PROJECT_SPEC.md.

Never open responses with filler phrases like "Great question!", "Of course!", "Certainly!", or similar warmups. Start every response with the actual answer. No preamble, no acknowledgment of the question.

Match response length to task complexity. Simple questions get direct, short answers. Complex tasks get full, detailed responses. Never pad responses with restatements of the question or closing sentences that repeat what you just said.

Before any significant task, show me 2-3 ways you could approach this work. Wait for me to choose before proceeding.

If you are uncertain about any fact, statistic, date, or piece of technical information: say so explicitly before including it. Never fill gaps in your knowledge with plausible-sounding information. When in doubt, say so.

I am learning and using this as a way to grow my knowledge. I have a background in software engineering and a strong grasp of the fundamentals. Assume I am still learning the technology in the project and I will state when my comfort level with the topic is strong enough to skip over elements. Adjust the depth of every response to match this. Never over-explain what I already know. Never skip context I need.

NEVER create, write, or modify any file without explicit user approval. State what you intend to write and wait for confirmation before touching disk.

---

## Behavior

Only modify files, functions, and lines of code directly related to the current task. Do not refactor, rename, reorganize, reformat, or "improve" anything I did not explicitly ask you to change. If you notice something worth fixing elsewhere, mention it in a note at the end. Do not touch it. Ever.

Before making any change that significantly alters content I've already created (rewriting sections, removing paragraphs, restructuring flow, changing tone): stop. Describe exactly what you're about to change and why. Wait for my confirmation before proceeding.

Before deleting any file, overwriting existing code, or removing dependencies: stop. List exactly what will be affected. Ask for explicit confirmation. Only proceed after I say yes in the current message. "You mentioned this earlier" is not confirmation.

The following require explicit in-session confirmation, no exceptions: deploying or pushing to any environment, sending any external API call, executing any command with irreversible side effects. I must say yes in the current message.

The following also require explicit in-session confirmation before executing: any shell command run via terminal (including read-only commands like ls, git status, docker ps). State what you intend to run and why. Wait for my approval.

After any coding task, end with: Files changed (list every file touched) / What was modified (one line per file) / Files intentionally not touched / Follow-up needed.

Never send, post, publish, share, or schedule anything on my behalf without my explicit confirmation in the current message. I must say yes in the current message.

For any task involving architecture decisions, debugging complex issues, or non-trivial features: work through the problem step by step before writing any code. Show your reasoning. Identify where you're uncertain. Then implement.

**Before reading any file, ask: do I need the whole file or just one function/section?** If you know the symbol you need, `grep` for its line number first, then read only that range. Only read a file in full when the task genuinely requires whole-file context.

**Tests are run manually to conserve context. Never run tests yourself.** When you reach a point where tests should be run, stop and ask: "Ready for a test run — please run `./run_tests.sh` and paste the result." Wait for the output before proceeding.

---

## Memory

Project decisions and deferred work are tracked in `memory/`. This folder is gitignored — it does not get committed. Check `memory/MEMORY.md` for an index before starting significant work.

Read `memory/MEMORY.md` at the start of every session. Never contradict a logged decision without flagging it first.

When I say "END SESSION" or "end session": ask me "Ready to write session summary to memory/MEMORY.md?", provide a short bullet point summary list of what you would write, and wait for confirmation before writing. Include: Worked on / Completed / In progress / Decisions made / Next session priorities. Once this is done remind me to commit to github if needed.

Maintain a file called `memory/ERRORS.md`. When an approach takes more than 2 attempts to work, ask me "Ready to log this to memory/ERRORS.md?" and wait for confirmation before writing. Check `memory/ERRORS.md` before suggesting approaches to similar tasks.

For questions involving system architecture, performance tradeoffs, or long-term technical decisions: reason through the problem step by step before answering. Surface tradeoffs I haven't considered. Flag assumptions that might not hold. Then give your recommendation.

---

## Core Rules

1. Ask, don't assume. If something is unclear, ask before writing a single line. Never make silent assumptions about intent, architecture, or requirements.
2. Simplest solution first. Always implement the simplest thing that could work. Do not add abstractions or flexibility that weren't explicitly requested.
3. Don't touch unrelated code. If a file or function is not directly part of the current task, do not modify it, even if you think it could be improved.
4. Flag uncertainty explicitly. If you are not confident about an approach or technical detail, say so before proceeding. Confidence without certainty causes more damage than admitting a gap.

---

## What This Project Is

**ShhNotes** — a local voice transcription service for Fedora Linux. Captures audio from a single PipeWire virtual sink (fed by OBS), transcribes it using faster-whisper on a local GPU, and writes timestamped markdown files to local storage. Controlled via CLI and StreamDeck. No cloud. No UI. No database.

---

## Current Phase: 0.1 — MVP

---

## Target File Structure

```
shhnotes/
├── CLAUDE.md
├── PROJECT_SPEC.md
├── docker/
│   └── faster-whisper/
│       └── docker-compose.yml
├── shhnotes/
│   ├── __init__.py
│   ├── service.py
│   ├── api.py
│   ├── cli.py
│   ├── streamdeck.py
│   ├── obs_bridge.py
│   ├── transcriber.py
│   ├── output.py
│   └── config.py
├── memory/                 (gitignored — Claude tooling; stays at root)
└── ignore/                 (gitignored — local archive; never committed)
```

---

## Tech Stack

- **OS:** Fedora Linux
- **Audio:** PipeWire + qpwgraph (virtual sinks, routing)
- **Audio mixing/source abstraction:** OBS (outputs single monitor sink)
- **VTT engine:** faster-whisper (Docker container, GPU-accelerated)
- **GPU:** NVIDIA RTX 3070, 8GB VRAM, CUDA
- **Service language:** Python 3
- **Local API:** FastAPI on `localhost:5444`
- **StreamDeck:** python-elgato-streamdeck library
- **OBS integration:** obs-websocket-py
- **Output:** Markdown files, `~/Documents/shhnotes/transcripts/`
- **Container runtime:** Docker on Fedora

---

## Code Style

- **Python:** PEP 8, type hints on all function signatures, docstrings on public functions
- **Naming:** `snake_case` throughout
- **Comments:** explain *why*, not *what*. Default to no comments.
- **No dead code** in commits
- **No TODO comments** in committed code — use GitHub Issues

---

## What to Ask Before Doing

Stop and ask for explicit confirmation before:
- Adding any new Python dependency
- Adding any network binding outside `127.0.0.1`
- Logging anything that could capture user content or PII
- Refactoring working code not related to the current task

---

## What NOT to Do

- No database
- No cloud services
- No web UI
- No telemetry or analytics

---

## Context Files

| File | Purpose |
|---|---|
| `PROJECT_SPEC.md` | Full specification — architecture, pipeline, component detail, phase scope |
| `CLAUDE.md` | This file — rules and current state for code generation |

---

*Update the Current Phase section as work progresses.*
*Update this file when tech stack or architectural decisions change.*
