# Architecture

## High-level flow

1. Source connectors fetch jobs from:
   - Greenhouse
   - Lever
   - company career pages
   - later: Apify LinkedIn / Indeed

2. All fetched jobs go into `raw_jobs` first.

3. A scoring worker processes queued raw jobs:
   - normalize fields
   - extract ATS keywords
   - classify role family and seniority
   - score match against my profile
   - decide keep / reject / needs feedback

4. Accepted jobs are inserted into canonical `jobs`.

5. Dashboard reads from canonical `jobs` and `job_evaluations`.

6. Nightly archival marks old unapplied jobs as archived after 10 days.

## Core tables
- sources
- raw_jobs
- job_evaluations
- jobs
- user_feedback

## Scheduling
Run 3 times per day:
- 10:00 AM
- 3:00 PM
- 8:00 PM

Office-hours style, local scheduling first.

## Queue strategy
Use PostgreSQL as the queue for v1.
`raw_jobs.processing_status` acts as queue state:
- queued
- processing
- processed
- rejected
- error
