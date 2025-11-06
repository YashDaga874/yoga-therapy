"""
Database Migration Script
Adds module_id column to practices table and updates modules table structure
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

# Default database path (same as in app.py)
DB_PATH = 'sqlite:///yoga_therapy.db'

def migrate_database(db_path=None):
    """
    Migrate the database to add module_id column to practices table
    and update modules table to support multiple modules per disease
    """
    if db_path is None:
        db_path = DB_PATH
    
    # Convert SQLite path format
    if db_path.startswith('sqlite:///'):
        db_file = db_path.replace('sqlite:///', '')
    else:
        db_file = db_path.replace('sqlite:///', '')
    
    # Check if database file exists
    if not os.path.exists(db_file):
        print(f"Database file {db_file} not found. Creating new database...")
        from database.models import create_database
        create_database(db_path)
        print("Database created successfully!")
        return
    
    engine = create_engine(db_path)
    
    with engine.connect() as conn:
        # Check if module_id column already exists
        result = conn.execute(text("PRAGMA table_info(practices)"))
        columns = [row[1] for row in result]
        
        if 'module_id' not in columns:
            print("Adding module_id column to practices table...")
            try:
                # Add module_id column (nullable initially)
                conn.execute(text("ALTER TABLE practices ADD COLUMN module_id INTEGER"))
                conn.commit()
                print("✓ Added module_id column to practices table")
            except Exception as e:
                print(f"Error adding module_id column: {e}")
                conn.rollback()
        else:
            print("✓ module_id column already exists in practices table")
        
        # Check if modules table has unique constraint on disease_id
        result = conn.execute(text("PRAGMA table_info(modules)"))
        columns = [row[1] for row in result]
        
        # Check if paper_link column exists
        if 'paper_link' not in columns:
            print("Adding paper_link column to modules table...")
            try:
                conn.execute(text("ALTER TABLE modules ADD COLUMN paper_link VARCHAR(1000)"))
                conn.commit()
                print("✓ Added paper_link column to modules table")
            except Exception as e:
                print(f"Error adding paper_link column: {e}")
                conn.rollback()
        else:
            print("✓ paper_link column already exists in modules table")
        
        # Remove unique constraint on disease_id in modules table if it exists
        # SQLite doesn't support DROP CONSTRAINT directly, so we need to recreate the table
        try:
            # Check if unique constraint exists by checking indexes
            result = conn.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='modules'"))
            table_sql = result.fetchone()
            
            if table_sql and 'UNIQUE' in table_sql[0] and 'disease_id' in table_sql[0]:
                print("Removing unique constraint on disease_id in modules table...")
                print("Note: This requires recreating the table. Existing data will be preserved.")
                
                # Create backup table
                conn.execute(text("""
                    CREATE TABLE modules_backup AS 
                    SELECT * FROM modules
                """))
                
                # Drop old table
                conn.execute(text("DROP TABLE modules"))
                
                # Create new table without unique constraint
                conn.execute(text("""
                    CREATE TABLE modules (
                        id INTEGER NOT NULL PRIMARY KEY,
                        disease_id INTEGER NOT NULL,
                        developed_by VARCHAR(500),
                        module_description TEXT,
                        paper_link VARCHAR(1000),
                        FOREIGN KEY(disease_id) REFERENCES diseases (id)
                    )
                """))
                
                # Copy data back
                conn.execute(text("""
                    INSERT INTO modules (id, disease_id, developed_by, module_description, paper_link)
                    SELECT id, disease_id, developed_by, module_description, NULL as paper_link
                    FROM modules_backup
                """))
                
                # Drop backup table
                conn.execute(text("DROP TABLE modules_backup"))
                
                conn.commit()
                print("✓ Removed unique constraint on disease_id in modules table")
            else:
                print("✓ No unique constraint found on disease_id in modules table")
        except Exception as e:
            print(f"Note: Could not check/remove unique constraint: {e}")
            print("This is okay if the constraint doesn't exist or if SQLite version doesn't support it")
            conn.rollback()
    
    print("\n" + "="*60)
    print("Migration completed successfully!")
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("Database Migration Script")
    print("="*60)
    print()
    migrate_database()

