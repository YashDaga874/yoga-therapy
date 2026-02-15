"""
Script to add new fields to modules and contraindications tables:
- Modules: age_range, gender, severity
- Contraindications: kosha, age_range, gender, severity
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
            exists = column_name in columns
            return exists
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

def add_new_columns():
    """Add missing columns to database tables"""
    import os
    from database.models import create_database
    
    # Ensure database exists; for SQLite, check file, for others just create schema
    try:
        # Attempt to create database/tables if missing
        create_database(DB_PATH)
    except Exception:
        # If creation fails (e.g., table already exists), continue with migration
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
            return  # New database already has all columns
    
    try:
        # Add columns to modules table
        print("\n=== Adding columns to modules table ===")
        
        columns_to_add_modules = [
            ('age_range', 'VARCHAR(200)'),
            ('gender', 'VARCHAR(50)'),
            ('severity', 'VARCHAR(50)')
        ]
        
        for col_name, col_type in columns_to_add_modules:
            # Check first, then try to add
            exists = column_exists(session, 'modules', col_name)
            if exists:
                print(f"{col_name} column already exists in modules table.")
            else:
                print(f"Adding {col_name} column to modules table...")
                alter_sql = f"ALTER TABLE modules ADD COLUMN {col_name} {col_type}"
                if dialect.startswith('postgres'):
                    alter_sql = f"ALTER TABLE modules ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                try:
                    session.execute(text(alter_sql))
                    session.commit()
                    print(f"{col_name} column added successfully.")
                except Exception as e:
                    session.rollback()
                    error_msg = str(e).lower()
                    if 'duplicate column' in error_msg or 'already exists' in error_msg or 'duplicate' in error_msg:
                        print(f"{col_name} column already exists (skipping).")
                    else:
                        print(f"Error adding {col_name}: {e}")
                        raise
        
        # Add columns to contraindications table
        print("\n=== Adding columns to contraindications table ===")
        
        columns_to_add_contraindications = [
            ('kosha', 'VARCHAR(50)'),
            ('age_range', 'VARCHAR(200)'),
            ('gender', 'VARCHAR(50)'),
            ('severity', 'VARCHAR(50)')
        ]
        
        for col_name, col_type in columns_to_add_contraindications:
            # Check first, then try to add
            exists = column_exists(session, 'contraindications', col_name)
            if exists:
                print(f"{col_name} column already exists in contraindications table.")
            else:
                print(f"Adding {col_name} column to contraindications table...")
                alter_sql = f"ALTER TABLE contraindications ADD COLUMN {col_name} {col_type}"
                if dialect.startswith('postgres'):
                    alter_sql = f"ALTER TABLE contraindications ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                try:
                    session.execute(text(alter_sql))
                    session.commit()
                    print(f"{col_name} column added successfully.")
                except Exception as e:
                    session.rollback()
                    error_msg = str(e).lower()
                    if 'duplicate column' in error_msg or 'already exists' in error_msg or 'duplicate' in error_msg:
                        print(f"{col_name} column already exists (skipping).")
                    else:
                        print(f"Error adding {col_name}: {e}")
                        raise
        
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
    print("This will add missing columns to modules and contraindications tables:")
    print("  - Modules: age_range, gender, severity")
    print("  - Contraindications: kosha, age_range, gender, severity")
    print()
    add_new_columns()
    print("\nDatabase migration completed!")
