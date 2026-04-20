from app.schemas.raw_job import RawJobCreate
from app.services.ingestion.normalize import normalize_raw_job, normalize_title, normalize_location


def test_normalize_title_strips_whitespace():
    assert normalize_title("  Software Engineer  ") == "Software Engineer"


def test_normalize_title_collapses_spaces():
    assert normalize_title("Security   Analyst  - Entry") == "Security Analyst - Entry"


def test_normalize_location_collapses_spaces():
    assert normalize_location("  San Francisco,  CA  ") == "San Francisco, CA"


def test_normalize_raw_job_applies_all():
    job = RawJobCreate(
        source_id=1,
        external_id="100",
        title="  Junior  Software  Engineer  ",
        company="co",
        location="  New York,  NY  ",
        url="https://example.com",
        description_raw="  Some description  ",
    )
    result = normalize_raw_job(job)
    assert result.title == "Junior Software Engineer"
    assert result.location == "New York, NY"
    assert result.description_raw == "Some description"
    # Original unchanged
    assert result.source_id == 1
    assert result.external_id == "100"
