"""
Script to add Kosha field to practices table and fill it based on category mappings
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, get_database_url
from sqlalchemy import text

# Database path
DB_PATH = get_database_url()

# Category to Kosha mappings
CATEGORY_TO_KOSHA = {
    'Preparatory Practice': 'Annamaya Kosha',
    'Yogasana': 'Annamaya Kosha',
    'Kriya (Cleansing Techniques)': 'Annamaya Kosha',
    'Sequential Yogic Practice': 'Annamaya Kosha',
    'Suryanamaskara': 'Annamaya Kosha',  # Will be replaced by Sequential Yogic Practice
    'Breathing Practice': 'Pranamaya Kosha',
    'Pranayama': 'Pranamaya Kosha',
    'Meditation': 'Manomaya Kosha',
    'Chanting': 'Manomaya Kosha',
    'Yogic Counselling': 'Vijnanamaya Kosha',
    'Additional Practices': None,  # Will be determined by sub_category or left empty
}

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
    except Exception:
        return False

def add_kosha_column_and_fill():
    """Add missing columns to database tables and fill them for existing data"""
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
        # Check and add paper_link to modules table if it doesn't exist
        if not column_exists(session, 'modules', 'paper_link'):
            print("Adding paper_link column to modules table...")
            alter_sql = "ALTER TABLE modules ADD COLUMN paper_link VARCHAR(1000)"
            if dialect.startswith('postgres'):
                alter_sql = "ALTER TABLE IF NOT EXISTS modules ADD COLUMN paper_link VARCHAR(1000)"
            session.execute(text(alter_sql))
            session.commit()
            print("paper_link column added successfully.")
        
        # Check and add module_description to modules table if it doesn't exist
        if not column_exists(session, 'modules', 'module_description'):
            print("Adding module_description column to modules table...")
            alter_sql = "ALTER TABLE modules ADD COLUMN module_description TEXT"
            if dialect.startswith('postgres'):
                alter_sql = "ALTER TABLE IF NOT EXISTS modules ADD COLUMN module_description TEXT"
            session.execute(text(alter_sql))
            session.commit()
            print("module_description column added successfully.")
        
        # First, check and add module_id if it doesn't exist (needed for ORM queries)
        if not column_exists(session, 'practices', 'module_id'):
            print("Adding module_id column to practices table...")
            alter_sql = "ALTER TABLE practices ADD COLUMN module_id INTEGER"
            if dialect.startswith('postgres'):
                alter_sql = "ALTER TABLE IF NOT EXISTS practices ADD COLUMN module_id INTEGER"
            session.execute(text(alter_sql))
            session.commit()
            print("module_id column added successfully.")
        
        # Check if kosha column exists, if not add it
        if not column_exists(session, 'practices', 'kosha'):
            print("Adding kosha column to practices table...")
            alter_sql = "ALTER TABLE practices ADD COLUMN kosha VARCHAR(50)"
            if dialect.startswith('postgres'):
                alter_sql = "ALTER TABLE IF NOT EXISTS practices ADD COLUMN kosha VARCHAR(50)"
            session.execute(text(alter_sql))
            session.commit()
            print("Kosha column added successfully.")
        else:
            print("Kosha column already exists.")
        
        # Get all practices using raw SQL to avoid ORM schema issues
        result = session.execute(text("""
            SELECT id, practice_segment, sub_category 
            FROM practices
        """))
        practices_data = result.fetchall()
        
        updated_count = 0
        suryanamaskara_count = 0
        
        for practice_row in practices_data:
            practice_id, category, sub_category = practice_row
            
            # Determine Kosha based on category
            kosha = CATEGORY_TO_KOSHA.get(category)
            
            # If category is Suryanamaskara, update to Sequential Yogic Practice
            new_category = category
            if category == 'Suryanamaskara':
                new_category = 'Sequential Yogic Practice'
                kosha = 'Annamaya Kosha'
                suryanamaskara_count += 1
            
            # If kosha is None, try to determine from sub_category or leave empty
            if not kosha and sub_category:
                sub_cat_lower = sub_category.lower()
                if 'breathing' in sub_cat_lower or 'pranayama' in sub_cat_lower:
                    kosha = 'Pranamaya Kosha'
                elif 'meditation' in sub_cat_lower or 'chanting' in sub_cat_lower:
                    kosha = 'Manomaya Kosha'
                elif 'counselling' in sub_cat_lower or 'counseling' in sub_cat_lower:
                    kosha = 'Vijnanamaya Kosha'
                elif 'asana' in sub_cat_lower or 'preparatory' in sub_cat_lower or 'kriya' in sub_cat_lower:
                    kosha = 'Annamaya Kosha'
            
            # Update practice using raw SQL
            if category == 'Suryanamaskara':
                # Update both category and kosha
                session.execute(text("""
                    UPDATE practices 
                    SET practice_segment = :new_category, kosha = :kosha 
                    WHERE id = :practice_id
                """).bindparams(
                    new_category=new_category,
                    kosha=kosha,
                    practice_id=practice_id
                ))
            else:
                # Update only kosha
                session.execute(text("""
                    UPDATE practices 
                    SET kosha = :kosha 
                    WHERE id = :practice_id
                """).bindparams(
                    kosha=kosha,
                    practice_id=practice_id
                ))
            
            updated_count += 1
        
        # Commit all changes
        session.commit()
        
        print(f"Successfully updated {updated_count} practices with Kosha field.")
        if suryanamaskara_count > 0:
            print(f"Updated {suryanamaskara_count} practices from 'Suryanamaskara' to 'Sequential Yogic Practice'.")
        
    except Exception as e:
        session.rollback()
        print(f"Error updating database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting database migration process...")
    print("This will add missing columns (paper_link, module_description, module_id, kosha) and update existing data.")
    add_kosha_column_and_fill()
    print("Database migration completed!")

