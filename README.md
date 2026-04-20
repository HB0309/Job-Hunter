<<<<<<< HEAD
# Job-Hunter
=======
# Job Hunter

A local-first job discovery and ranking system for my personal job search.

## Goal
Fetch recent US-based full-time jobs for:
- Security Analyst
- Security Engineer
- Software Engineer

Focus on:
- new grad
- early career
- L2 / junior-ish roles

The system should:
- fetch jobs from Greenhouse, Lever, company career sites, and later Apify-based LinkedIn/Indeed
- deduplicate jobs across sources
- store full descriptions and metadata
- score jobs against my profile
- keep early talent jobs automatically
- score higher-level jobs by match %
- show jobs in a dashboard
- support applied/saved/dismissed/archived states
- ask for feedback on borderline jobs
- send email digests

## Current stack
- Python
- FastAPI
- PostgreSQL
- Docker Compose
- React frontend later

## Non-goals for v1
- multi-user auth
- automatic job applications
- cover letter generation
- WhatsApp notifications
- cloud deployment
>>>>>>> e6628f6 (Initial commit)
