"""
Quick script to clean up the specific orphaned job
"""
from sqlalchemy import text
from datetime import datetime, timezone
from core.utils.db import SessionLocal

def quick_cleanup():
    db = SessionLocal()
    try:
        # Mark the orphaned job as failed
        db.execute(text("""
            UPDATE jobs
            SET status = 'failed',
                error_message = 'Job failed due to migration - cleaned up automatically',
                completed_at = :ts
            WHERE id = 'ab1f05cf-c037-41cb-8cda-fe66d9358d89'
        """), {
            "ts": datetime.now(timezone.utc)
        })
        db.commit()
        print("✓ Orphaned job marked as failed successfully!")
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    quick_cleanup()
