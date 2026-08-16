from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models import Listing, PipelineRun
from app.schemas import (
    HealthResponse,
    ListingResponse,
    PipelineRunResponse,
    SummaryResponse,
)
from app.services.collector import CollectorError
from app.services.pipeline import PipelineBusyError, get_pipeline_service

router = APIRouter()
SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok", collector_mode=settings.collector_mode, environment=settings.app_env
    )


@router.post("/api/v1/pipeline/run", response_model=PipelineRunResponse, tags=["pipeline"])
async def trigger_pipeline(session: SessionDep) -> PipelineRun:
    try:
        return await get_pipeline_service().run(session)
    except PipelineBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except CollectorError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/v1/runs", response_model=list[PipelineRunResponse], tags=["pipeline"])
async def list_runs(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[PipelineRun]:
    statement = select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
    return list((await session.scalars(statement)).all())


@router.get("/api/v1/listings", response_model=list[ListingResponse], tags=["listings"])
async def list_listings(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Listing]:
    statement = select(Listing).order_by(Listing.last_seen_at.desc()).limit(limit)
    return list((await session.scalars(statement)).all())


@router.get("/api/v1/summary", response_model=SummaryResponse, tags=["analytics"])
async def summary(session: SessionDep) -> SummaryResponse:
    listing_count = await session.scalar(select(func.count(Listing.id))) or 0
    run_count = await session.scalar(select(func.count(PipelineRun.id))) or 0
    successful_runs = (
        await session.scalar(
            select(func.count(PipelineRun.id)).where(PipelineRun.status == "completed")
        )
        or 0
    )
    average_price = await session.scalar(select(func.avg(Listing.price)))
    latest_run_at = await session.scalar(select(func.max(PipelineRun.started_at)))
    return SummaryResponse(
        listing_count=listing_count,
        run_count=run_count,
        successful_runs=successful_runs,
        average_price=average_price,
        latest_run_at=latest_run_at,
    )
