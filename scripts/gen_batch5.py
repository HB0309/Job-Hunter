import json

def score_to_label(score):
    if score >= 90: return 'excellent_fit'
    if score >= 75: return 'strong_fit'
    if score >= 60: return 'good_fit'
    if score >= 40: return 'weak_fit'
    return 'poor_fit'

def j(raw_job_id, title, company, location, url, keep, score, early_talent, seniority, role_family, reasoning, ats, matched, missing):
    return {
        'raw_job_id': raw_job_id, 'keep_in_db': keep, 'fit_score': score,
        'fit_label': score_to_label(score), 'early_talent': early_talent,
        'seniority': seniority, 'role_family': role_family,
        'reasoning_summary': reasoning, 'ats_keywords': ats,
        'matched_skills': matched, 'missing_skills': missing,
        'title': title, 'company': company, 'location': location, 'url': url
    }

results = []

# ── KEEPS ──────────────────────────────────────────────────────────────────────

# Pinterest Software Engineer I, Backend
results.append(j(
    21888, 'Software Engineer I, Backend', 'pinterest', 'Seattle, WA / Bay Area, CA',
    'https://www.pinterestcareers.com/jobs/?gh_jid=6816337',
    True, 72, False, 'swe_i', 'software_engineer',
    'Pinterest SWE I (entry-level by title). Backend role building Pinner-facing features on one of the largest public cloud workloads. Strong brand, US location. Aligns with Python/backend profile. Minimum requirements explicitly state entry-level.',
    ['Python', 'distributed systems', 'backend', 'API', 'A/B testing', 'scalability', 'microservices'],
    ['Python', 'backend systems', 'distributed systems', 'API design'],
    ['Ruby/React (Pinterest stack)', 'large-scale ads/recommendation systems']
))

# Stripe Software Engineer L2
results.append(j(
    21577, 'Software Engineer L2', 'stripe', 'Seattle, WA',
    'https://stripe.com/jobs/search?gh_jid=7812279',
    True, 68, False, 'l2', 'software_engineer',
    'Stripe SWE L2 — entry-level Stripe band (18 months min). Strong fintech brand. Seattle location. Backend-heavy, Python/Ruby stack. Stripe L2 is the first full-time engineering level above new grad.',
    ['Python', 'Ruby', 'distributed systems', 'API', 'scalability', 'TypeScript', 'backend'],
    ['Python', 'backend systems', 'API design', 'distributed systems'],
    ['Ruby experience', 'fintech/payments domain', 'Stripe-specific stack']
))

# Ramp University Grad SWE Frontend
results.append(j(
    27274, 'University Grad | Software Engineer | Frontend', 'ramp', 'Remote',
    'https://jobs.ashbyhq.com/ramp/a1229aec-1105-4c47-8533-b912e732ed89',
    True, 73, True, 'new_grad', 'software_engineer',
    'Ramp explicit New Grad SWE Frontend. Graduating May 2026 target, deferred start Summer/Fall 2026. Remote role. Ramp is a high-growth fintech unicorn. TypeScript/React stack. Strong new grad signal — exactly the profile this system targets.',
    ['TypeScript', 'React', 'JavaScript', 'frontend', 'Vite', 'web performance', 'new grad'],
    ['TypeScript', 'JavaScript', 'React', 'frontend', 'web development'],
    ['Ramp-specific design system (Ryu)', 'fintech product context', 'frontend specialization']
))

# Zscaler Software Development Engineer (Golang) — SecOps Detection Engine
results.append(j(
    26976, 'Software Development Engineer (Golang)', 'zscaler', 'Remote - USA',
    'https://job-boards.greenhouse.io/zscaler/jobs/5080761007',
    True, 70, False, 'junior', 'security_engineering',
    'Zscaler SDE on SecOps Detection Engine team. Only requires 1+ year Golang + 1+ year AWS. Security-focused company (cloud security leader). Detection engine work aligns with security engineering profile. Remote US. Good entry point into security-focused SWE at a top vendor.',
    ['Golang', 'Go', 'AWS', 'detection engine', 'Parquet', 'Iceberg', 'data warehouse', 'cloud security'],
    ['Go/Golang', 'AWS', 'cloud infrastructure', 'security tooling'],
    ['1+ year Golang production experience', 'data warehousing / Parquet / Iceberg']
))

# ── REJECTS ────────────────────────────────────────────────────────────────────

reject_ids = [
    21224,21334,21422,21546,21564,21586,21639,
    22021,22022,22024,22538,
    24159,24378,24379,24815,
    25109,25110,25119,
    26139,26140,26270,26272,26273,26281,26282,26287,26289,
    26291,26292,26293,26294,26295,26296,26297,26298,26300,
    26303,26304,26311,26314,26317,26318,26372,26473,26474,
    26475,26476,26477,26482,26483,26487,26488,26491,26499,
    26509,26521,26600,26653,26689,26690,26692,26707,26737,
    26738,26746,26751,26766,26767,26816,26850,26865,26866,
    26887,26974,26975,26977,26979,26980,
    27057,27058,27065,27088,27093,27098,27140,27172,27176,
    27233,27237,27238,27242,27249,27251,27252,27253,27263,
    27264,27265,27266,27267,27268,27269,27271,27272,27275,
    27277,27278,27282,27283,27284,27286,27295,27296,27298,
    27299,27300,27301,27302,27303,27305,27312,27314,27315,
    18036,
]

for rid in reject_ids:
    results.append({
        'raw_job_id': rid, 'keep_in_db': False, 'fit_score': 20,
        'fit_label': 'poor_fit', 'early_talent': False,
        'seniority': 'unknown', 'role_family': 'other',
        'reasoning_summary': 'Rejected: senior-level requirements, non-US location, intern/co-op, non-SWE role, or unclear fit.',
        'ats_keywords': [], 'matched_skills': [], 'missing_skills': [],
        'title': '', 'company': '', 'location': '', 'url': ''
    })

with open('/app/scripts/batch5_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"Generated {len(results)} records ({sum(1 for r in results if r['keep_in_db'])} keeps, {sum(1 for r in results if not r['keep_in_db'])} rejects)")
