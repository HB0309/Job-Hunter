import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.connectors.apify_linkedin import ApifyLinkedInConnector

MOCK_ACTOR_RUN = {"defaultDatasetId": "dataset-abc123"}

MOCK_ITEMS = [
    {
        "id": "3900000001",
        "title": "Security Engineer",
        "companyName": "Acme Corp",
        "companyLinkedinUrl": "https://linkedin.com/company/acme",
        "location": "Remote, United States",
        "link": "https://linkedin.com/jobs/view/3900000001",
        "descriptionText": "Secure all the infrastructure...",
        "employmentType": "Full-time",
        "seniorityLevel": "Entry level",
        "workRemoteAllowed": True,
        "postedAt": "2026-04-09",
        "industries": ["Cybersecurity"],
        "salary": "",
    },
    {
        "id": "3900000002",
        "title": "Security Analyst",
        "companyName": "Beta Inc",
        "companyLinkedinUrl": "https://linkedin.com/company/beta",
        "location": "New York, United States",
        "link": "https://linkedin.com/jobs/view/3900000002",
        "descriptionText": "Monitor and respond to incidents...",
        "employmentType": "Full-time",
        "seniorityLevel": "Entry level",
        "workRemoteAllowed": False,
        "postedAt": "2026-04-08",
        "industries": [],
        "salary": "",
    },
]


def _make_mock_client(items=MOCK_ITEMS, run=MOCK_ACTOR_RUN):
    mock_client = MagicMock()
    mock_client.actor.return_value.call.return_value = run
    mock_client.dataset.return_value.list_items.return_value.items = items
    return mock_client


@pytest.mark.asyncio
async def test_apify_linkedin_fetch_jobs():
    mock_client = _make_mock_client()
    with patch("app.services.connectors.apify_linkedin.ApifyClient", return_value=mock_client):
        connector = ApifyLinkedInConnector(
            api_token="fake-token",
            keyword="Security Engineer",
            location="United States",
        )
        jobs = await connector.fetch_jobs(source_id=1)

    assert len(jobs) == 2
    assert jobs[0].external_id == "3900000001"
    assert jobs[0].title == "Security Engineer"
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].location == "Remote, United States"
    assert jobs[0].url == "https://linkedin.com/jobs/view/3900000001"
    assert "Secure all the infrastructure" in jobs[0].description_raw
    assert jobs[0].source_id == 1

    assert jobs[1].external_id == "3900000002"
    assert jobs[1].title == "Security Analyst"
    assert jobs[1].location == "New York, United States"


@pytest.mark.asyncio
async def test_apify_linkedin_metadata_json():
    mock_client = _make_mock_client()
    with patch("app.services.connectors.apify_linkedin.ApifyClient", return_value=mock_client):
        connector = ApifyLinkedInConnector(
            api_token="fake-token",
            keyword="Security Engineer",
            location="United States",
        )
        jobs = await connector.fetch_jobs(source_id=1)

    meta = json.loads(jobs[0].metadata_json)
    assert meta["is_remote"] is True
    assert meta["seniority_level"] == "Entry level"
    assert meta["employment_type"] == "Full-time"
    assert meta["search_keyword"] == "Security Engineer"

    meta2 = json.loads(jobs[1].metadata_json)
    assert meta2["is_remote"] is False


@pytest.mark.asyncio
async def test_apify_linkedin_empty_response():
    mock_client = _make_mock_client(items=[])
    with patch("app.services.connectors.apify_linkedin.ApifyClient", return_value=mock_client):
        connector = ApifyLinkedInConnector(
            api_token="fake-token",
            keyword="Security Engineer",
            location="United States",
        )
        jobs = await connector.fetch_jobs(source_id=1)

    assert jobs == []


@pytest.mark.asyncio
async def test_apify_linkedin_actor_run_none():
    mock_client = _make_mock_client(run=None)
    with patch("app.services.connectors.apify_linkedin.ApifyClient", return_value=mock_client):
        connector = ApifyLinkedInConnector(
            api_token="fake-token",
            keyword="Security Engineer",
            location="United States",
        )
        jobs = await connector.fetch_jobs(source_id=1)

    assert jobs == []


@pytest.mark.asyncio
async def test_apify_linkedin_skips_missing_job_id():
    items_with_missing_id = [{"id": "", "title": "Ghost Job"}] + MOCK_ITEMS
    mock_client = _make_mock_client(items=items_with_missing_id)
    with patch("app.services.connectors.apify_linkedin.ApifyClient", return_value=mock_client):
        connector = ApifyLinkedInConnector(
            api_token="fake-token",
            keyword="Security Engineer",
            location="United States",
        )
        jobs = await connector.fetch_jobs(source_id=1)

    # Ghost job with empty jobId should be skipped
    assert len(jobs) == 2
    assert all(j.external_id != "" for j in jobs)


@pytest.mark.asyncio
async def test_apify_linkedin_date_filter_incremental():
    """Jobs older than date_from should be excluded (incremental mode)."""
    mock_client = _make_mock_client()
    # Set cutoff to 2026-04-09 — job 1 is 2026-04-09, job 2 is 2026-04-08
    date_from = datetime(2026, 4, 9, 0, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.connectors.apify_linkedin.ApifyClient", return_value=mock_client):
        connector = ApifyLinkedInConnector(
            api_token="fake-token",
            keyword="Security Engineer",
            location="United States",
            date_from=date_from,
        )
        jobs = await connector.fetch_jobs(source_id=1)

    # Only job posted on 2026-04-09 should pass; 2026-04-08 should be filtered
    assert len(jobs) == 1
    assert jobs[0].external_id == "3900000001"
