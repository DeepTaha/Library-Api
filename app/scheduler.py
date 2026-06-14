import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.library_service import LibraryService
from app.security import token_blacklist, reset_tokens

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


async def _purge_blacklist_job():
    async with SessionLocal() as db:
        try:
            count = await token_blacklist.purge_expired(db)
            if count:
                logger.info("Blacklist purge: removed %d expired JTI(s).", count)
        except Exception:
            logger.exception("Blacklist purge job failed.")


async def _purge_reset_tokens_job():
    async with SessionLocal() as db:
        try:
            count = await reset_tokens.purge_expired(db)
            if count:
                logger.info("Reset-token purge: removed %d expired token(s).", count)
        except Exception:
            logger.exception("Reset-token purge job failed.")


def start_scheduler():
    scheduler.add_job(_check_overdue_job, "interval", hours=1, id="overdue_check")
    scheduler.add_job(_purge_blacklist_job, "interval", hours=1, id="blacklist_purge")
    scheduler.add_job(_purge_reset_tokens_job, "interval", hours=1, id="reset_token_purge")
    scheduler.start()
    logger.info("Overdue scheduler started (runs every hour).")


def stop_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Overdue scheduler stopped.")
