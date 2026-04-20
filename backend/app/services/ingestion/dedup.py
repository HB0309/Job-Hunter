import hashlib
import re

from app.schemas.raw_job import RawJobCreate


def dedup_key(job: RawJobCreate) -> str:
    """Generate a dedup key from source_id + external_id.

    This is the primary dedup mechanism — the DB unique index on
    (source_id, external_id) is the enforcement layer.
    """
    return f"{job.source_id}:{job.external_id}"


def content_fingerprint(title: str, company: str, location: str) -> str:
    """Generate a content-based fingerprint for cross-source dedup.

    Useful for detecting the same job posted via different sources.
    """
    normalized = f"{_simplify(title)}|{_simplify(company)}|{_simplify(location)}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _simplify(text: str) -> str:
    """Lowercase, strip non-alphanumeric, collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return re.sub(r"\s+", " ", text)


def deduplicate_batch(jobs: list[RawJobCreate]) -> list[RawJobCreate]:
    """Remove in-batch duplicates by dedup_key before DB insertion."""
    seen: set[str] = set()
    unique: list[RawJobCreate] = []
    for job in jobs:
        key = dedup_key(job)
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique
