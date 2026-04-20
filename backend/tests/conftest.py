import pytest

from app.schemas.raw_job import RawJobCreate


@pytest.fixture
def sample_raw_jobs() -> list[RawJobCreate]:
    return [
        RawJobCreate(
            source_id=1,
            external_id="gh-1001",
            title="Security Analyst - Entry Level",
            company="acmecorp",
            location="New York, NY",
            url="https://boards.greenhouse.io/acmecorp/jobs/1001",
            description_raw="<p>We are looking for a Security Analyst...</p>",
        ),
        RawJobCreate(
            source_id=1,
            external_id="gh-1002",
            title="  Software Engineer, Junior  ",
            company="acmecorp",
            location="  San Francisco,  CA  ",
            url="https://boards.greenhouse.io/acmecorp/jobs/1002",
            description_raw="  Build backend services...  ",
        ),
        RawJobCreate(
            source_id=1,
            external_id="gh-1003",
            title="Security Engineer",
            company="acmecorp",
            location="Remote",
            url="https://boards.greenhouse.io/acmecorp/jobs/1003",
            description_raw="<div>SOC Engineer role</div>",
        ),
    ]


@pytest.fixture
def duplicate_raw_jobs() -> list[RawJobCreate]:
    """Batch with intentional duplicates for dedup testing."""
    base = RawJobCreate(
        source_id=1,
        external_id="gh-2001",
        title="Security Analyst",
        company="testco",
        location="Remote",
        url="https://example.com/jobs/2001",
    )
    return [base, base.model_copy(), base.model_copy()]
