from datetime import datetime

from pydantic import BaseModel


class RawJobCreate(BaseModel):
    """Data shape coming out of a connector, before DB insertion."""
    source_id: int
    external_id: str
    title: str
    company: str
    location: str = ""
    url: str
    description_raw: str = ""
    metadata_json: str = "{}"


class RawJobRead(RawJobCreate):
    id: int
    processing_status: str
    fetched_at: datetime

    model_config = {"from_attributes": True}
