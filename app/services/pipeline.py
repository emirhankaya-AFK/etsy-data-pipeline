import asyncio
from datetime import UTC, datetime
from functools import lru_cache

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import Listing, ListingObservation, PipelineRun
from app.services.collector import Collector, build_collector


class PipelineBusyError(RuntimeError):
    pass


class PipelineService:
    def __init__(self, settings: Settings, collector: Collector) -> None:
        self.settings = settings
        self.collector = collector
        self._lock = asyncio.Lock()

    async def run(self, session: AsyncSession) -> PipelineRun:
        if self._lock.locked():
            raise PipelineBusyError("A pipeline run is already in progress")

        async with self._lock:
            run = PipelineRun(source_url=self.settings.target_url, status="running")
            session.add(run)
            await session.commit()
            await session.refresh(run)
            run_id = run.id

            try:
                records = await self.collector.collect(self.settings.target_url)
                for record in records:
                    statement = insert(Listing).values(
                        source_url=record.source_url,
                        title=record.title,
                        image_url=record.image_url,
                        price=record.price,
                        currency=record.currency,
                    )
                    statement = statement.on_conflict_do_update(
                        index_elements=[Listing.source_url],
                        set_={
                            "title": statement.excluded.title,
                            "image_url": statement.excluded.image_url,
                            "price": statement.excluded.price,
                            "currency": statement.excluded.currency,
                            "last_seen_at": datetime.now(UTC),
                        },
                    )
                    await session.execute(statement)
                    session.add(
                        ListingObservation(
                            run_id=run_id,
                            source_url=record.source_url,
                            price=record.price,
                            currency=record.currency,
                        )
                    )

                run.status = "completed"
                run.collected_count = len(records)
                run.finished_at = datetime.now(UTC)
                await session.commit()
                await session.refresh(run)
                return run
            except Exception as exc:
                await session.rollback()
                failed_run = await session.get(PipelineRun, run_id)
                if failed_run is not None:
                    failed_run.status = "failed"
                    failed_run.error_message = str(exc)[:2_000]
                    failed_run.finished_at = datetime.now(UTC)
                    await session.commit()
                raise


@lru_cache
def get_pipeline_service() -> PipelineService:
    settings = get_settings()
    return PipelineService(settings, build_collector(settings))
