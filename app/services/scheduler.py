from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import Settings
from app.core.database import SessionFactory
from app.services.pipeline import get_pipeline_service

scheduler = AsyncIOScheduler(timezone="UTC")


async def scheduled_pipeline_run() -> None:
    async with SessionFactory() as session:
        await get_pipeline_service().run(session)


def start_scheduler(settings: Settings) -> None:
    if settings.schedule_hours <= 0 or scheduler.running:
        return
    scheduler.add_job(
        scheduled_pipeline_run,
        trigger="interval",
        hours=settings.schedule_hours,
        id="listing-collection",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
