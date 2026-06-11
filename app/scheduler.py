import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.library_service import LibraryService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _check_overdue_job():
    async with SessionLocal() as db:
        try:
            service = LibraryService(db)
            count = await service.process_overdue()
            if count:
                logger.info("Overdue job: marked %d borrowing(s) as overdue.", count)
            else:
                logger.debug("Overdue job: no new overdue borrowings.")
        except Exception:
            logger.exception("Overdue job failed.")


def start_scheduler():
    scheduler.add_job(_check_overdue_job, "interval", hours=1, id="overdue_check")
    scheduler.start()
    logger.info("Overdue scheduler started (runs every hour).")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Overdue scheduler stopped.")
