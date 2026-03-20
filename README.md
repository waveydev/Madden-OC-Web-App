# Madden OC App

Madden OC App is a voice-first assistant that helps Madden players make better offensive play-calling decisions.

You describe the game situation (for example, down, distance, and defensive look), and the app suggests high-probability offensive plays with a short rationale.

## Why this project exists

Most Madden players can recognize defensive shells, but making fast, consistent play calls under pressure is hard.

This project is built to:
- reduce decision time
- improve consistency in situational play-calling
- turn playbook data into practical recommendations

## Who this is for

### Players and creators (non-engineers)
- Use a mobile app experience to quickly get play suggestions.
- Speak naturally, like a coordinator, instead of manually searching giant playbooks.

### Engineers and contributors
- Work in a service-oriented monorepo.
- Extend ingestion, ranking logic, APIs, or mobile UX independently.
- Iterate toward stronger recommendation quality over time.

## What it does today (MVP)

- Accepts text or voice-style input for a game situation.
- Transcribes audio through cloud speech-to-text.
- Parses situation context (down, distance, shell/front hints).
- Ranks candidate plays with a rule-based engine.
- Supports ingestion pipeline scaffolding for playbook source extraction and normalization.

## Current status

This repository is in active MVP development.

Implemented:
- Mobile shell (React Native + Expo)
- Realtime API (FastAPI)
- Control plane and data models (Django)
- Import pipeline from normalized ingestion artifacts
- Rule-based ranking with fallback behavior

In progress / known limitations:
- Source parsing quality varies by page structure (dynamic/complex markup)
- Data coverage is currently limited by extraction reliability
- Recommendation quality will improve as ingestion coverage and concept mapping improve

## High-level architecture

- `apps/mobile` — React Native client for voice/text situation input and recommendation display
- `services/api-realtime` — FastAPI service for low-latency suggestion flow
- `services/control-plane` — Django service for canonical play data, admin, and import workflows
- `services/ingestion` — source fetch, parsing, normalization, and artifact generation
- `libs/schemas` — shared request/response contracts used across services

## How the flow works

1. User speaks or types a situation.
2. Realtime API transcribes (if audio) and parses context.
3. Realtime API requests candidate plays from control plane.
4. Rules engine scores and ranks plays.
5. Mobile app shows top recommendations with rationale.

## Quick start

### 1) Start control plane (Django)

```bash
cd services/control-plane
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 2) Start realtime API (FastAPI)

```bash
cd services/api-realtime
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

### 3) Start mobile app (Expo)

```bash
cd apps/mobile
npm install
npm run start
```

### 4) Generate ingestion artifacts

```bash
cd services/ingestion
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ingestion.run
```

### 5) Import artifacts into control plane

```bash
cd services/control-plane
source .venv/bin/activate
python manage.py import_ingestion \
	--replace-source \
	--index-file services/ingestion/output/huddle_gg_index.json \
	--plays-file services/ingestion/output/huddle_gg_plays_sample.json
```

## Environment variables

Realtime API (cloud STT):

```bash
export OPENAI_API_KEY=your_key_here
export STT_MODEL=gpt-4o-mini-transcribe
export CONTROL_PLANE_BASE_URL=http://localhost:8000
export MADDEN_VERSION=
```

## API overview

- `GET /healthz` — Realtime service health check
- `POST /v1/suggest` — Suggest plays from structured situation input
- `POST /v1/voice/analyze` — Accept transcript or base64 audio, parse situation, return recommendations
- `GET /api/playbook-entries` — Query candidate plays from control-plane datastore

## Project goals (near term)

- Improve parser coverage and reliability for play-level extraction
- Expand concept taxonomy and scoring rules
- Increase data quality safeguards and provenance tracking
- Improve mobile voice UX and recommendation explainability

## Contribution notes

- Keep changes focused and testable by service.
- Prefer improving data quality before adding ranking complexity.
- Document any ingestion/source assumptions directly in code and PR descriptions.
