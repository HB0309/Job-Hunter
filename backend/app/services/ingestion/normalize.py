import re

from app.schemas.raw_job import RawJobCreate


def normalize_title(title: str) -> str:
    """Lowercase, collapse whitespace, strip leading/trailing junk."""
    title = re.sub(r"\s+", " ", title.strip())
    return title


def normalize_location(location: str) -> str:
    """Basic normalization: strip, collapse whitespace."""
    return re.sub(r"\s+", " ", location.strip())


def normalize_raw_job(job: RawJobCreate) -> RawJobCreate:
    """Return a copy with normalized fields."""
    return job.model_copy(
        update={
            "title": normalize_title(job.title),
            "location": normalize_location(job.location),
            "description_raw": job.description_raw.strip(),
        }
    )
