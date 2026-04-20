# Scoring Rules

## Purpose
Claude scoring should decide whether a job is a good fit for me and should be kept in the main jobs database.

## Score bands
- 90-100: excellent fit
- 75-89: strong fit
- 60-74: stretch but possible
- 40-59: weak fit
- 0-39: reject

## Rules
1. Keep all clearly early-talent jobs in target families unless obviously irrelevant.
2. For higher-level jobs, score against my profile before inserting.
3. Prefer jobs with:
   - Python
   - Linux
   - backend or infrastructure engineering
   - security engineering
   - SIEM / SOC / detection relevance
   - software engineering fundamentals
4. Penalize jobs with:
   - seniority far above my level
   - people management
   - very niche enterprise-only experience requirements
   - non-full-time or non-US constraints
5. Output structured JSON only.

## Required Claude output fields
- role_family
- seniority
- early_talent
- fit_score
- fit_label
- keep_in_db
- needs_user_feedback
- ats_keywords
- matched_skills
- missing_skills
- reasoning_summary
