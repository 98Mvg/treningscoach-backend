# Session Learnings — 2026-03-17 Render runtime vs tool dependencies

## Problem

Render deploy troubleshooting drifted because the repo had two dependency surfaces:

- root `requirements.txt` for the real Flask/Gunicorn production runtime
- `backend/requirements.txt` with stale FastAPI/uvicorn/soundfile-era baggage

At the same time, the R2 audio-pack tool needed `boto3`, which had been added to runtime dependencies even though production Flask requests never import it.

## What matters

- Production deploy path is root runtime:
  - `Procfile` -> `gunicorn main:app`
  - `main.py`
  - root `requirements.txt`
- `backend/requirements.txt` is not the production truth and should not drift into a second runtime definition.

## Fix

- Removed `boto3` from root `requirements.txt`
- Added `requirements-tools.txt` for local tool-only dependencies
- Turned `backend/requirements.txt` into `-r ../requirements.txt`
- Kept `psycopg[binary]` in root runtime because `database.py` normalizes production DB URLs to `postgresql+psycopg://`

## Guardrail

- If a package is only imported by tooling, keep it out of production runtime requirements.
- If a package is required by the actual SQLAlchemy DB driver path, keep it explicit in production requirements even if it used to arrive transitively.
- If Render pipeline minutes start burning too fast, fix deploy scope before chasing micro-optimizations. This repo mixes backend, iOS, watch, docs, and design assets, so the Render web service should use a root directory and build filters that ignore iOS-only paths like `TreningsCoach/**` and other non-runtime folders. The backend should not autodeploy on app-only commits.
