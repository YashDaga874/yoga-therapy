"""
Script to add Kosha field to practices table and fill it based on category mappings
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, Practice
from sqlalchemy import text

# Database path
DB_PATH = 'sqlite:///yoga_therapy.db'

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
    """Check if a column exists in a table"""
    try:
        result = session.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        return column_name in columns
    except Exception:
        return False

def add_kosha_column_and_fill():
    """Add Kosha column to practices table and fill it for existing practices"""
    session = get_session(DB_PATH)
    
    try:
        # First, check and add module_id if it doesn't exist (needed for ORM queries)
        if not column_exists(session, 'practices', 'module_id'):
            print("Adding module_id column to practices table...")
            session.execute(text("ALTER TABLE practices ADD COLUMN module_id INTEGER"))
            session.commit()
            print("module_id column added successfully.")
        
        # Check if kosha column exists, if not add it
        if not column_exists(session, 'practices', 'kosha'):
            print("Adding kosha column to practices table...")
            session.execute(text("ALTER TABLE practices ADD COLUMN kosha VARCHAR(50)"))
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
    print("Starting Kosha field addition and update process...")
    add_kosha_column_and_fill()
    print("Update completed!")

