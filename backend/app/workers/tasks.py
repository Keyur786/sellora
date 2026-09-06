from datetime import datetime, timezone
import logging
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.models.analytics import SyncJob
from app.models.marketplace import MarketplaceAccount
from app.integrations.marketplaces.base import MockMarketplaceConnector

logger = logging.getLogger(__name__)


@celery.task(name="tasks.sync_marketplace_account")
def sync_marketplace_account(account_id: str, job_id: str):
    """Background task to sync marketplace data asynchronously using MarketplaceConnector."""
    db = SessionLocal()
    try:
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        account = db.query(MarketplaceAccount).filter(MarketplaceAccount.id == account_id).first()
        if not job or not account:
            logger.error(f"Invalid job {job_id} or account {account_id}")
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        # Instantiate connector via abstraction
        connector = MockMarketplaceConnector(marketplace_type=account.marketplace_type)
        
        # In a real task, this fetches orders, fees, products and inserts/updates idempotently
        records_count = 5  # Mock processed count
        
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.records_processed = records_count
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()
        logger.info(f"Successfully synced account {account_id}, {records_count} records processed")
    except Exception as e:
        logger.exception(f"Error syncing account {account_id}: {e}")
        if job:
            job.status = "failed"
            job.completed_at = datetime.now(timezone.utc)
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()
