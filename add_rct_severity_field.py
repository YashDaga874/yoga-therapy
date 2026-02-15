"""
Script to add severity field to rcts table
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, get_database_url
from sqlalchemy import text

# Database path
DB_PATH = get_database_url()

def column_exists(session, table_name, column_name):
    """Check if a column exists in a table (SQLite/PostgreSQL)."""
    try:
        engine = session.get_bind()
        dialect = engine.dialect.name
        if dialect == 'sqlite':
            result = session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result]
            return column_name in columns
        result = session.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table_name AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        )
        return result.first() is not None
    except Exception as e:
        print(f"Error checking column existence: {e}")
        return False

def add_severity_column():
    """Add severity column to rcts table"""
    import os
    from database.models import create_database
    
    # Ensure database exists
    try:
        create_database(DB_PATH)
    except Exception:
        pass
    
    session = get_session(DB_PATH)
    engine = session.get_bind()
    dialect = engine.dialect.name
    
    # For SQLite file-based DBs, short-circuit if the file was missing and just created
    if dialect == 'sqlite':
        db_file = engine.url.database or 'yoga_therapy.db'
        if db_file and not os.path.exists(db_file):
            print("Database file not found. Creating new database...")
            create_database(DB_PATH)
            print("Database created successfully.")
            return
    
    try:
        print("\n=== Adding severity column to rcts table ===")
        
        if not column_exists(session, 'rcts', 'severity'):
            print("Adding severity column to rcts table...")
            alter_sql = "ALTER TABLE rcts ADD COLUMN severity VARCHAR(50)"
            if dialect.startswith('postgres'):
                alter_sql = "ALTER TABLE rcts ADD COLUMN IF NOT EXISTS severity VARCHAR(50)"
            try:
                session.execute(text(alter_sql))
                session.commit()
                print("severity column added successfully.")
            except Exception as e:
                session.rollback()
                error_msg = str(e).lower()
                if 'duplicate column' in error_msg or 'already exists' in error_msg or 'duplicate' in error_msg:
                    print("severity column already exists (skipping).")
                else:
                    print(f"Error adding severity: {e}")
                    raise
        else:
            print("severity column already exists in rcts table.")
        
        print("\n=== Migration completed successfully! ===")
        
    except Exception as e:
        session.rollback()
        print(f"\nError updating database: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting database migration process...")
    print("This will add the severity column to the rcts table.")
    print()
    add_severity_column()
    print("\nDatabase migration completed!")
