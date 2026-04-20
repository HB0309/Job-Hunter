"""Title-based pre-filter: cheaply rejects clearly irrelevant jobs before Claude sees them."""

from app.models.raw_job import RawJob

# Any job whose title contains at least one of these is passed to Claude for scoring.
# Jobs with none of these are pre-rejected — no API call needed.
_TECH_KEYWORDS = frozenset({
    "engineer", "developer", "security", "software", "devops", "sre",
    "platform", "infrastructure", "cloud", "detection", "soc", "cyber",
    "researcher", "scientist", "architect", "analyst", "data", "network",
    "systems", "backend", "frontend", "fullstack", "ml", "reliability",
    "intern", "associate", "junior", "programmer", "kubernetes", "python",
    "golang", "rust", "infosec", "appsec", "pentester", "red team",
    "blue team", "threat", "vulnerability", "compliance", "risk",
    "it specialist", "it analyst", "technical",
})


def prefilter(jobs: list[RawJob]) -> tuple[list[RawJob], list[RawJob]]:
    """Split jobs into (pass_to_claude, pre_rejected).

    A job passes if its lowercased title contains at least one tech keyword.
    """
    keep, reject = [], []
    for job in jobs:
        title_lower = (job.title or "").lower()
        if any(kw in title_lower for kw in _TECH_KEYWORDS):
            keep.append(job)
        else:
            reject.append(job)
    return keep, reject
