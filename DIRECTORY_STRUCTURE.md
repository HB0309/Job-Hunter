# Directory Structure

This file explains the recommended project layout for the Job Hunter system.

## Project tree

```text
job-hunter/
├── README.md
├── ARCHITECTURE.md
├── PROFILE_MATCH.md
├── SCORING_RULES.md
├── TASKS.md
├── AGENTS.md
├── .env.example
├── docker-compose.yml
├── Makefile
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── db.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   │   ├── job.py
│   │   │   ├── raw_job.py
│   │   │   ├── source.py
│   │   │   ├── evaluation.py
│   │   │   └── feedback.py
│   │   ├── schemas/
│   │   │   ├── job.py
│   │   │   ├── raw_job.py
│   │   │   ├── evaluation.py
│   │   │   └── feedback.py
│   │   ├── api/
│   │   │   ├── routes_jobs.py
│   │   │   ├── routes_sources.py
│   │   │   ├── routes_feedback.py
│   │   │   └── routes_health.py
│   │   ├── services/
│   │   │   ├── connectors/
│   │   │   │   ├── base.py
│   │   │   │   ├── greenhouse.py
│   │   │   │   ├── lever.py
│   │   │   │   ├── apify_linkedin.py
│   │   │   │   ├── apify_indeed.py
│   │   │   │   └── company_sites.py
│   │   │   ├── ingestion/
│   │   │   │   ├── normalize.py
│   │   │   │   ├── dedup.py
│   │   │   │   └── ingest.py
│   │   │   ├── scoring/
│   │   │   │   ├── prompt_builder.py
│   │   │   │   ├── claude_client.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── scorer.py
│   │   │   ├── scheduler/
│   │   │   │   ├── jobs.py
│   │   │   │   └── apscheduler_runner.py
│   │   │   └── notifications/
│   │   │       └── email_digest.py
│   │   ├── repositories/
│   │   │   ├── jobs.py
│   │   │   ├── raw_jobs.py
│   │   │   ├── evaluations.py
│   │   │   └── feedback.py
│   │   └── workers/
│   │       ├── run_ingestion.py
│   │       ├── run_scoring.py
│   │       └── archive_old_jobs.py
│   └── tests/
│       ├── test_connectors.py
│       ├── test_dedup.py
│       ├── test_scoring.py
│       └── test_api.py
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api/
│       ├── pages/
│       │   ├── NewJobs.tsx
│       │   ├── SavedJobs.tsx
│       │   ├── AppliedJobs.tsx
│       │   ├── ArchivedJobs.tsx
│       │   └── FeedbackQueue.tsx
│       ├── components/
│       │   ├── JobTable.tsx
│       │   ├── JobDetailDrawer.tsx
│       │   ├── FiltersBar.tsx
│       │   └── MatchBadge.tsx
│       └── types/
└── scripts/
    ├── bootstrap.sh
    ├── dev.sh
    └── seed_sources.py
```

## How to read this structure

### Root markdown files
These are the core planning and context files Claude should read before making changes.

- `README.md` -> project purpose and scope
- `ARCHITECTURE.md` -> data flow and system design
- `PROFILE_MATCH.md` -> your background and target job profile
- `SCORING_RULES.md` -> job scoring and filtering logic
- `TASKS.md` -> phased implementation checklist
- `AGENTS.md` -> suggested subagent responsibilities

### `backend/`
This contains the Python FastAPI service and all backend logic.

- `models/` -> SQLAlchemy database models
- `schemas/` -> Pydantic request/response models
- `api/` -> API route files
- `services/connectors/` -> job source integrations
- `services/ingestion/` -> normalization and dedup logic
- `services/scoring/` -> Claude-based ATS extraction and match scoring
- `services/scheduler/` -> scheduled jobs logic
- `services/notifications/` -> email digest logic
- `repositories/` -> database access layer
- `workers/` -> command-line/background worker entrypoints
- `tests/` -> unit and integration tests

### `frontend/`
This contains the dashboard UI.

- `pages/` -> major dashboard pages
- `components/` -> reusable UI pieces
- `api/` -> frontend API calls
- `types/` -> shared TS types

### `scripts/`
Helpful shell/python scripts for setup and development.

## Suggested build order
1. Create backend skeleton
2. Add Postgres and migrations
3. Add Greenhouse connector
4. Add raw job queue
5. Add scoring worker
6. Add canonical jobs table flow
7. Add frontend dashboard
8. Add email digests
9. Add more connectors
