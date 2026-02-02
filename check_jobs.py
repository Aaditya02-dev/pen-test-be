"""
Check all jobs in the database
"""
from sqlalchemy import text
from core.utils.db import SessionLocal

def check_all_jobs():
    db = SessionLocal()
    try:
        print("Checking all jobs in database...\n")
        
        result = db.execute(text("""
            SELECT id, application_id, status, started_at, completed_at, error_message
            FROM jobs
            ORDER BY started_at DESC NULLS LAST
        """))
        
        jobs = result.fetchall()
        
        if not jobs:
            print("✓ No jobs found in database!")
            return
        
        print(f"Found {len(jobs)} job(s):\n")
        for idx, job in enumerate(jobs, 1):
            print(f"{idx}. Job ID: {job.id}")
            print(f"   Application: {job.application_id}")
            print(f"   Status: {job.status}")
            print(f"   Started: {job.started_at}")
            print(f"   Completed: {job.completed_at}")
            if job.error_message:
                print(f"   Error: {job.error_message[:100]}...")
            print()
        
        response = input(f"Do you want to delete ALL {len(jobs)} job(s)? (yes/no): ").strip().lower()
        
        if response == 'yes':
            db.execute(text("DELETE FROM jobs"))
            db.commit()
            print(f"\n✓ Successfully deleted all {len(jobs)} job(s)!")
        else:
            print("\nDeletion cancelled.")
            
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    check_all_jobs()
