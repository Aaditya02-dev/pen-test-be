"""
Cleanup script to fix orphaned jobs that are stuck in 'running' or 'pending' status
Run this after migration or if jobs get stuck
"""
from sqlalchemy import text
from datetime import datetime, timezone, timedelta
from core.utils.db import SessionLocal

def cleanup_orphaned_jobs():
    db = SessionLocal()
    try:
        # Find jobs stuck in 'running' or 'pending' status
        print("Looking for orphaned jobs...")
        
        result = db.execute(text("""
            SELECT id, application_id, status, started_at
            FROM jobs
            WHERE status IN ('running', 'pending')
            ORDER BY started_at DESC NULLS LAST
        """))
        
        orphaned_jobs = result.fetchall()
        
        if not orphaned_jobs:
            print("✓ No orphaned jobs found!")
            return
        
        print(f"\nFound {len(orphaned_jobs)} orphaned job(s):")
        for job in orphaned_jobs:
            print(f"  - Job ID: {job.id}")
            print(f"    Status: {job.status}")
            print(f"    Started: {job.started_at}")
            print(f"    Application: {job.application_id}")
            print()
        
        response = input(f"Mark these {len(orphaned_jobs)} job(s) as 'failed'? (yes/no): ").strip().lower()
        
        if response == 'yes':
            for job in orphaned_jobs:
                db.execute(text("""
                    UPDATE jobs
                    SET status = 'failed',
                        error_message = 'Job orphaned - marked as failed by cleanup script',
                        completed_at = :ts
                    WHERE id = :id
                """), {
                    "id": job.id,
                    "ts": datetime.now(timezone.utc)
                })
            
            db.commit()
            print(f"\n✓ Successfully marked {len(orphaned_jobs)} job(s) as failed!")
        else:
            print("\nCleanup cancelled.")
            
    except Exception as e:
        print(f"\n✗ Cleanup failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_orphaned_jobs()
