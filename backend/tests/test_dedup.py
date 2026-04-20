from app.schemas.raw_job import RawJobCreate
from app.services.ingestion.dedup import (
    content_fingerprint,
    dedup_key,
    deduplicate_batch,
)


def test_dedup_key_format():
    job = RawJobCreate(
        source_id=1,
        external_id="gh-100",
        title="Analyst",
        company="co",
        url="https://example.com",
    )
    assert dedup_key(job) == "1:gh-100"


def test_dedup_key_different_sources():
    job_a = RawJobCreate(source_id=1, external_id="100", title="X", company="c", url="http://a")
    job_b = RawJobCreate(source_id=2, external_id="100", title="X", company="c", url="http://b")
    assert dedup_key(job_a) != dedup_key(job_b)


def test_content_fingerprint_stable():
    fp1 = content_fingerprint("Security Analyst", "Acme Corp", "New York")
    fp2 = content_fingerprint("Security Analyst", "Acme Corp", "New York")
    assert fp1 == fp2


def test_content_fingerprint_case_insensitive():
    fp1 = content_fingerprint("Security Analyst", "ACME CORP", "new york")
    fp2 = content_fingerprint("security analyst", "acme corp", "New York")
    assert fp1 == fp2


def test_content_fingerprint_strips_punctuation():
    fp1 = content_fingerprint("Security Analyst!", "Acme, Corp.", "New York")
    fp2 = content_fingerprint("Security Analyst", "Acme Corp", "New York")
    assert fp1 == fp2


def test_deduplicate_batch_removes_dupes(duplicate_raw_jobs):
    result = deduplicate_batch(duplicate_raw_jobs)
    assert len(result) == 1


def test_deduplicate_batch_keeps_unique(sample_raw_jobs):
    result = deduplicate_batch(sample_raw_jobs)
    assert len(result) == 3


def test_deduplicate_batch_empty():
    assert deduplicate_batch([]) == []
