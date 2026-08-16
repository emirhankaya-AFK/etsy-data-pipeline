import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    collector_mode: str
    environment: str


class PipelineRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    source_url: str | None
    collected_count: int
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_url: str
    title: str
    image_url: str | None
    price: Decimal | None
    currency: str | None
    first_seen_at: datetime
    last_seen_at: datetime


class SummaryResponse(BaseModel):
    listing_count: int
    run_count: int
    successful_runs: int
    average_price: Decimal | None
    latest_run_at: datetime | None
