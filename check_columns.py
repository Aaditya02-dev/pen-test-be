"""
Check the actual column names in all scan-related tables
"""
from sqlalchemy import text
from core.utils.db import SessionLocal

def check_columns():
    db = SessionLocal()
    try:
        tables = [
            'jobs',
            'application_configuration',
            'baseline_scans',
            'network_scans',
            'vulnerabilities',
            'validation_runs',
            'evidence'
        ]
        
        print("Checking column names in all tables...\n")
        
        for table in tables:
            print(f"\n{'='*60}")
            print(f"Table: {table}")
            print(f"{'='*60}")
            
            result = db.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            if columns:
                print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable'}")
                print("-" * 60)
                for col in columns:
                    print(f"{col.column_name:<30} {col.data_type:<20} {col.is_nullable}")
            else:
                print(f"Table '{table}' not found or has no columns")
        
    except Exception as e:
        print(f"\n✗ Failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    check_columns()
