# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Job Hunter is a local-first job discovery and ranking system. It ingests jobs from multiple sources (LinkedIn via Apify, Greenhouse, Lever, Ashby, Workday), queues them in `raw_jobs`, scores/filters them via a 2-stage prescreen pipeline, and surfaces accepted jobs through a dashboard API + UI. Single-user, no auth.

## Commands

```bash
# Start everything (Postgres + FastAPI backend)
docker compose up -d --build

# Run migrations
MSYS_NO_PATHCONV=1 docker compose exec backend alembic upgrade head

# Run tests
MSYS_NO_PATHCONV=1 docker compose exec backend python -m pytest -v

# Run ingestion worker (fetch from all enabled sources)
MSYS_NO_PATHCONV=1 docker compose exec backend python -m app.workers.run_ingestion

# Seed sources table
MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/seed_sources.py

# Prescreen queued jobs (2-stage: title+location then description)
MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/bulk_prescreen.py --dry-run
MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/bulk_prescreen.py --execute

# View logs
docker compose logs backend -f

# Postgres shell
MSYS_NO_PATHCONV=1 docker compose exec db psql -U jobhunter -d jobhunter

# Run a single test file
MSYS_NO_PATHCONV=1 docker compose exec backend python -m pytest tests/test_connectors.py -v
```

> `make` is not available in Git Bash on Windows — use the raw docker compose commands above.

## Architecture

**Data flow:** Sources → `raw_jobs` (queue) → 2-stage prescreen → `review` status (user picks in UI) or `queued` (strong match, score) → `job_evaluations` → canonical `jobs` → Dashboard API

**Queue mechanism:** PostgreSQL-based via `raw_jobs.processing_status`:
- `queued` — passed prescreen, strong match, awaiting Claude scoring
- `review` — ambiguous, waiting for user decision in Review tab
- `processed` — done (scored, rejected, or manually decided)

**Scheduling:** Ingestion planned 3x daily via APScheduler — not yet implemented.

**Tables:** `sources`, `raw_jobs`, `job_evaluations`, `jobs`, `user_feedback`

## Key design decisions

- **Raw queue first:** All fetched jobs land in `raw_jobs` before any scoring.
- **2-stage prescreen:** Stage 1 = title + location hard filters. Stage 2 = description analysis (YOE, clearance, domain mismatch, skill matching).
- **Security clearance auto-reject:** Any job mentioning TS/SCI, secret clearance, polygraph, etc. is auto-rejected — new grad can't meet clearance requirements.
- **Review tab:** Ambiguous jobs get `processing_status='review'` and appear in the dashboard Review tab for manual keep/reject. Kept jobs go directly to `jobs` table (fit_score=70, "Manually approved").
- **Dedup:** Two layers — in-batch dedup by `(source_id, external_id)` key, and DB-level unique index.
- **Connectors are async:** Each connector implements `BaseConnector.fetch_jobs()` returning `list[RawJobCreate]`.
- **first_seen_at filter:** Dashboard filters by `first_seen_at >= 30 days ago` (when WE discovered the job), not `posted_at` (when company listed it — can be stale).
- **Workday URL format:** Public apply URLs must use `https://{tenant}.wd1.myworkdayjobs.com/en-US/{board}{externalPath}` — NOT the CXS API path.

## Backend layout

- `app/core/` — config (Pydantic settings), db (async SQLAlchemy), logging
- `app/models/` — SQLAlchemy ORM models (one file per table)
- `app/schemas/` — Pydantic request/response models
- `app/api/` — FastAPI route files (`routes_health`, `routes_sources`, `routes_jobs`, `routes_raw_jobs`)
- `app/services/connectors/` — source integrations (base ABC + `apify_linkedin.py`, `greenhouse.py`, `lever.py`, `ashby.py`, `workday.py`)
- `app/services/ingestion/` — normalize, dedup, ingest orchestration
- `app/services/scoring/` — Claude scoring (Phase 3, not yet implemented)
- `app/repositories/` — database access layer
- `app/workers/` — CLI entrypoints for ingestion, scoring, archival
- `scripts/` — one-off scripts: `seed_sources.py`, `bulk_prescreen.py`, `skill_match.py`, `write_batch.py`, `discover_workday.py`

## Context files to read before changes

- `ARCHITECTURE.md` — system design and data flow
- `SCORING_RULES.md` — scoring bands, rules, required output fields
- `PROFILE_MATCH.md` — target roles and skill profile for match scoring
- `TASKS.md` — phased implementation checklist
- `AGENTS.md` — subagent role definitions

## Current phase: Phase 2 complete, Phase 3 in progress

**Completed:**
- Docker Compose, FastAPI skeleton, all 5 DB models, Alembic migration
- Apify LinkedIn connector
- Greenhouse connector — 130 company boards
- Lever connector — 37 company slugs
- Ashby connector — 80+ company slugs
- Workday connector (2-phase: paginated listing + concurrent detail fetch) — 10 companies
- Incremental ingestion pipeline with `last_fetched_at` tracking
- Dedup (in-batch + DB unique index)
- 2-stage prescreen pipeline (`scripts/bulk_prescreen.py` + `scripts/skill_match.py`)
  - Stage 1: title + location hard filters
  - Stage 2: description analysis — YOE, clearance detection, domain mismatch, skill matching
- Security clearance auto-rejection (TS/SCI, secret, polygraph, etc.)
- Session-based scoring via Claude Code — `scripts/write_batch.py`
- `GET /api/jobs/` — scored jobs, filtered to last 30 days by `first_seen_at`
- `GET /api/jobs/{id}` — job detail with reasoning, keywords, matched/missing skills
- `PATCH /api/jobs/{id}/status` — save/apply/dismiss
- `GET /api/raw-jobs/review` — ambiguous jobs awaiting user decision
- `POST /api/raw-jobs/review/decide` — keep selected (→ jobs table) or reject rest
- Dashboard UI — Jobs tab (scored) + Review tab (ambiguous, with checkboxes + bulk action)
- Workday URL fix — all stored URLs updated to `en-US/{board}/` format
- **Phase A complete:** Google, Amazon, Apple custom connectors (SSR/REST scraping)
- **Phase B partial:** Workday CSRF connector — Nvidia working (2000 jobs); Salesforce/Qualcomm/ServiceNow/Adobe board names need correction
- Meta and Microsoft connectors are placeholder stubs (locked APIs)

**Current DB state (2026-04-17):**
- 24,612 raw_jobs total: 19,640 processed, 4,972 review
- **81 active jobs in `jobs` table** (up from ~50)
- Sources: 2 LinkedIn, 130 Greenhouse, 37 Lever, 80+ Ashby, 10 Workday, 1 Workday-CSRF (Nvidia), 3 Google Careers, 1 Amazon Jobs, 2 Apple Jobs, 1 Microsoft (stub), 1 Meta (stub)
- Scoring batch history through batch8 (72 jobs from Phase A/B ingestion)

**Phase A ingestion totals (2026-04-15 session):**
- Nvidia (workday_csrf): ~1,784 new jobs
- Google (3 queries: new grad, entry level, university graduate): ~1,460 jobs
- Amazon (software development engineer): ~472 jobs
- Apple (new grad + software engineer): ~3,380 jobs after dedup
- Microsoft: 0 (Eightfold API requires auth, placeholder)
- Meta: 0 (GraphQL doc_id unstable, placeholder)

**Greenhouse boards (130):**
2k, abnormalsecurity, adyen, affirm, airbnb, airtable, alchemy, algolia, amplemarket, amplitude, anthropic, apptronik, archer, arizeai, asana, betterment, beyondtrust, blackforestlabs, block, brex, buildkite, calm, carta, celonis, cerebral, chime, circleci, clever, climateai, cloudflare, cockroachlabs, coinbase, contentful, contentstack, coursera, cribl, cybereason, cymulate, databricks, datadog, deepmind, descript, discord, doximity, dropbox, duolingo, elastic, epicgames, exabeam, expel, figma, figure, found, gemini, getyourguide, gitlab, gleanwork, grafanalabs, graphcore, gusto, hellofresh, helsing, hightouch, homelight, homeward, honeycomb, hubspot, humeai, huntress, hyperproof, imbue, immunefi, instacart, intercom, isomorphiclabs, jfrog, justworks, knock, labelbox, lattice, launchdarkly, lyft, marqeta, mixpanel, mmhmm, mongodb, netskope, newrelic, nuro, okta, opendoor, orca, orchard, pagerduty, pandadoc, parloa, payoneer, peloton, physicsx, pinterest, planetscale, polyai, poshmark, postman, qualia, recordedfuture, reddit, remote, riotgames, robinhood, roblox, rubrik, runpod, safebreach, salesloft, samsara, scaleai, scandit, scopely, sezzle, showpad, speechmatics, stabilityai, storyblok, stripe, sumologic, synack, talkspace, temporal, toast, transcarent, twilio, twitch, udemy, vercel, watershed, waymo, wayve, wing, workato, zscaler

**Lever slugs (37):**
15five, anomali, arcadia, better, clari, conversica, freshworks, greenlight, highspot, houzz, imbue, jobvite, kraken, labelbox, logrocket, mistral, neon, netflix, olo, outreach, palantir, pigment, plaid, prismic, qonto, relay, rover, secureframe, sonatype, sophos, spotify, sysdig, threatconnect, transcarent, wealthfront, zoox

**Ashby slugs (80+):**
acorns, alchemy, anyscale, attio, betterup, boomi, chromatic, clerk, clever, cohere, cursor, dave, deel, deepgram, deepl, drata, elevenlabs, figure, found, fullstory, greenlight, illumio, inngest, juro, knock, kraken, langchain, launchdarkly, leapsome, lindy, linear, loom, lovable, marqeta, mem, menlosecurity, mercury, modal, mosaic, n8n, neon, nerdwallet, notion, openai, opensea, orca, orchard, perplexity, photoroom, pika, pinecone, planet, poshmark, posthog, primer, qualified, ramp, readme, relay, replit, resend, retool, runway, salesloft, sanity, sentry, snapdocs, snyk, stash, statsig, supabase, synthesia, tillster, vanta, vapi, watershed, wiz, zapier, zip

**Workday companies (10 verified CSRF-free):**
intel:External, dell:External, paypal:jobs, equinix:External, globalfoundries:External, calix:External, analogdevices:External, athenahealth:External, caci:External, conocophillips:External

## Prescreen pipeline (bulk_prescreen.py)

```bash
# Stage 1 rejects: non-US location, senior/manager titles, non-technical roles
# Stage 2 rejects: security clearance required, wrong domain (hardware/fab/legacy), YOE > 3 without entry signal
# Stage 2 score queue: entry-level signal + ≥2 skill matches, or no YOE + ≥3 matches
# Stage 2 review queue: ambiguous — marked processing_status='review', shown in Review tab

MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/bulk_prescreen.py --dry-run
MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/bulk_prescreen.py --execute
```

**skill_match.py** — description analysis module:
- `extract_max_yoe()` — returns MAX YOE found (not min — catches "5+ years required" after HR baseline)
- `has_clearance_requirement()` — detects TS/SCI, secret, polygraph, public trust, etc.
- `is_wrong_domain()` — detects hardware/fab/COBOL/SAP/PCB domain mismatches
- `extract_matched_skills()` — matches description against 20+ profile skill categories
- `analyze_description()` — returns DescriptionVerdict with verdict: auto_reject / score / review

## Scoring workflow (session-based)

```bash
# 1. Pre-screen
MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/bulk_prescreen.py --execute

# 2. Score strong matches manually → write JSON to scripts/batchN_results.json
# Format: list of {raw_job_id, keep_in_db, fit_score, fit_label, early_talent,
#   seniority, role_family, reasoning_summary, ats_keywords, matched_skills, missing_skills,
#   title, company, location, url}

# 3. Write results to DB
MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/write_batch.py /app/scripts/batchN_results.json

# OR: use Review tab in UI to manually approve ambiguous jobs (they go straight to jobs table at score=70)
```

**Scoring rules:**
- Accept: New Grad, SWE I / Engineer I / Level 1, Junior, Associate — US locations only
- Reject: intern, apprentice, senior, staff, principal, lead, director, manager, clearance-required, non-US
- fit_score ≥ 60 required to reach `jobs` table

**Scoring batch history:**
- batch1–3: Initial 12 jobs (pre-expansion)
- batch4: 27 keeps from 204 records
- batch5: 4 keeps from 128 records
- batch6: 5 keeps
- batch7: 578 Workday rejects (bulk)
- batch7b: 1 Intel keep (false negative recovery — Linux Kernel Engineer JR0282647)
- Review tab approvals: athenahealth AI Security Automation Engineer (fit_score=70)

## Dashboard UI (localhost:8000)

- **Jobs tab** — scored canonical jobs, dark cards, sortable by fit_score, filter by status (new/saved/applied/dismissed), expandable detail with reasoning + ATS keywords + matched/missing skills
- **Review tab** — ambiguous raw jobs grouped by company, checkboxes to select keepers, "Keep Selected & Reject Rest" button
  - Kept jobs → immediately inserted into `jobs` table (score=70, "Manually approved"), removed from Review
  - Rejected jobs → job_evaluations poor_fit record, processing_status=processed

## API endpoints (localhost:8000)

- `GET /` — dashboard UI
- `GET /health` — health check
- `GET /api/sources/` — list sources
- `GET /api/raw-jobs/` — raw jobs browser
- `GET /api/raw-jobs/count` — count by status
- `GET /api/raw-jobs/review` — jobs awaiting user decision (queued + review status)
- `POST /api/raw-jobs/review/decide` — `{keep_ids: [...]}` — keep selected, reject rest
- `GET /api/raw-jobs/{id}` — raw job detail
- `GET /api/jobs/` — canonical scored jobs (sorted by fit_score desc, last 30 days)
- `GET /api/jobs/{id}` — job detail with reasoning, keywords, skills
- `PATCH /api/jobs/{id}/status` — new/saved/applied/dismissed
- `GET /docs` — Swagger UI

## Workday connector details

**File:** `app/services/connectors/workday.py`

Two-phase fetch:
1. Paginate `POST https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{board}/jobs` — collects stubs
2. Concurrent `GET https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/{board}{externalPath}` — fetches descriptions

**Critical quirks:**
- `total` field in listing response is only populated on page 1 (returns 0 on subsequent pages) — code caches it from first response only
- Public apply URL format: `https://{tenant}.wd1.myworkdayjobs.com/en-US/{board}{externalPath}` (NOT the CXS path)
- Most big-tech Workday boards (NVIDIA, Salesforce, Qualcomm, IBM, etc.) return 422 without a valid CSRF token — Phase B work

**Discovery script:** `scripts/discover_workday.py` — probes tenant×board combinations to find CSRF-free boards

## Phase roadmap

### Phase A — Custom big-tech connectors (COMPLETE)
Implemented connectors:
- **Google** (`google.py`) — scrapes `https://www.google.com/about/careers/applications/jobs/results/` SSR page, parses `AF_initDataCallback` `ds:1` WIZ framework block. ~1,460 jobs fetched.
- **Amazon** (`amazon.py`) — `GET https://www.amazon.jobs/en/search.json` REST API, offset pagination. ~472 jobs fetched.
- **Apple** (`apple.py`) — scrapes `https://jobs.apple.com/en-us/search` Remix SSR page, parses `window.__staticRouterHydrationData`. ~3,380 jobs fetched.
- **Microsoft** (`microsoft.py`) — **STUB** — Eightfold API at `apply.careers.microsoft.com` returns 403 (auth required). Returns 0 jobs.
- **Meta** (`meta.py`) — **STUB** — GraphQL `doc_id` changes per deploy, no stable public API. Returns 0 jobs.

Each connector: `app/services/connectors/{name}.py` + `SourceType.{NAME}` in `models/source.py` + config in `config.py` + seeding in `seed_sources.py` + factory case in `run_ingestion.py`.

### Phase B — CSRF-unlocked Workday (PARTIAL)
- **Nvidia** (`workday_csrf.py`) — CSRF token extracted from careers page, works. `nvidia:NVIDIAExternalCareerSite:wd5`. ~1,784 jobs fetched.
- **Salesforce, Qualcomm, ServiceNow, Adobe** — board names in .env are wrong (404). Need correct board IDs via `scripts/discover_workday.py`.

### Phase B — CSRF-unlocked Workday (~20 more companies)
Fetch CSRF token from careers page before API calls. Would unlock NVIDIA, Salesforce, Qualcomm, IBM, Lockheed, Raytheon, etc.

### Phase C — iCIMS connector
Cisco and many defense/enterprise companies. iCIMS has a documented public API.

### Phase D — Automation
- APScheduler for 3x daily ingestion
- Automated scoring worker using `ANTHROPIC_API_KEY`

## .env keys

```bash
POSTGRES_USER=jobhunter
POSTGRES_PASSWORD=changeme
POSTGRES_DB=jobhunter
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://jobhunter:changeme@db:5432/jobhunter
DATABASE_URL_SYNC=postgresql://jobhunter:changeme@db:5432/jobhunter
LOG_LEVEL=INFO

APIFY_API_TOKEN=apify_api_...
LINKEDIN_SEARCHES=security|United States,software engineer|United States
LINKEDIN_PAGES_PER_SEARCH=3

GREENHOUSE_BOARD_TOKENS=2k,abnormalsecurity,...  (130 boards)
LEVER_COMPANY_SLUGS=15five,anomali,...           (37 slugs)
ASHBY_COMPANY_SLUGS=acorns,alchemy,...           (80+ slugs)
WORKDAY_COMPANIES=intel:External,dell:External,paypal:jobs,equinix:External,globalfoundries:External,calix:External,analogdevices:External,athenahealth:External,caci:External,conocophillips:External

# Phase A additions (not yet added):
# GOOGLE_SEARCH_TERMS=software engineer,security engineer
# AMAZON_SEARCH_TERMS=software engineer,security engineer
# APPLE_SEARCH_TERMS=software engineer,security engineer
# MICROSOFT_SEARCH_TERMS=software engineer,security engineer

ANTHROPIC_API_KEY=sk-ant-...  # not yet in use
```

## Known fixes (do not revert)

- **`migrations/env.py`** — `sys.path.insert(0, ...)` so Alembic can import `app` inside Docker.
- **`scripts/seed_sources.py`** — `sys.path.insert(0, ...)` resolves to `/app` inside Docker.
- **`app/models/source.py`** — `source_type` uses `String(32)` not `Enum(SourceType)`.
- **`app/models/raw_job.py`** — `processing_status` uses `String(32)` + `.value`, not `Enum`.
- **`app/api/routes_sources.py`** — `s.source_type` not `s.source_type.value`.
- **`app/repositories/jobs.py`** — Lever timestamps: check `ts > 1_000_000_000_000` to detect ms vs seconds. 30-day filter uses `first_seen_at` (SQL), not `posted_at` (Python-side).
- **Workday URLs** — all existing URLs backfilled via SQL `regexp_replace` to insert `en-US/{board}/`.

## Windows / Git Bash gotcha

Prefix `docker compose exec` commands with `MSYS_NO_PATHCONV=1` when using Unix paths.

## How to add new job sources

**Greenhouse / Lever / Ashby:**
1. Add slug(s) to `.env`
2. `MSYS_NO_PATHCONV=1 docker compose exec backend python scripts/seed_sources.py`
3. `MSYS_NO_PATHCONV=1 docker compose exec backend python -m app.workers.run_ingestion`

**Workday (new company):**
1. Verify CSRF-free: `curl -X POST https://{tenant}.wd1.myworkdayjobs.com/wday/cxs/{tenant}/External/jobs -H "Content-Type: application/json" -d '{"limit":1,"offset":0,"searchText":"","appliedFacets":{}}'`
2. If 200+jobPostings: add `tenant:board` to `WORKDAY_COMPANIES` in `.env`
3. Seed + ingest as above. No restart needed after `.env` change if using exec.

**New custom connector (Phase A):**
1. Create `app/services/connectors/{name}.py` implementing `BaseConnector.fetch_jobs()`
2. Add config to `app/core/config.py`
3. Add `SourceType.{NAME}` to `app/models/source.py`
4. Add seeding block to `scripts/seed_sources.py`
5. Add factory case to `app/workers/run_ingestion.py`
6. Add `.env` key(s)
7. Rebuild: `docker compose up -d --build`
