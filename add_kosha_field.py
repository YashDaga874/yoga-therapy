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

def add_kosha_column_and_fill():
    """Add Kosha column to practices table and fill it for existing practices"""
    session = get_session(DB_PATH)
    
    try:
        # Check if kosha column exists, if not add it
        try:
            # Try to query the kosha column
            session.execute(text("SELECT kosha FROM practices LIMIT 1"))
            print("Kosha column already exists.")
        except Exception:
            # Column doesn't exist, add it
            print("Adding kosha column to practices table...")
            session.execute(text("ALTER TABLE practices ADD COLUMN kosha VARCHAR(50)"))
            session.commit()
            print("Kosha column added successfully.")
        
        # Get all practices
        practices = session.query(Practice).all()
        updated_count = 0
        
        for practice in practices:
            category = practice.practice_segment
            
            # Determine Kosha based on category
            kosha = CATEGORY_TO_KOSHA.get(category)
            
            # If category is Suryanamaskara, update to Sequential Yogic Practice
            if category == 'Suryanamaskara':
                practice.practice_segment = 'Sequential Yogic Practice'
                kosha = 'Annamaya Kosha'
            
            # If kosha is None, try to determine from sub_category or leave empty
            if not kosha:
                # Check sub_category for additional hints
                if practice.sub_category:
                    sub_cat_lower = practice.sub_category.lower()
                    if 'breathing' in sub_cat_lower or 'pranayama' in sub_cat_lower:
                        kosha = 'Pranamaya Kosha'
                    elif 'meditation' in sub_cat_lower or 'chanting' in sub_cat_lower:
                        kosha = 'Manomaya Kosha'
                    elif 'counselling' in sub_cat_lower or 'counseling' in sub_cat_lower:
                        kosha = 'Vijnanamaya Kosha'
                    elif 'asana' in sub_cat_lower or 'preparatory' in sub_cat_lower or 'kriya' in sub_cat_lower:
                        kosha = 'Annamaya Kosha'
            
            # Update practice
            practice.kosha = kosha
            updated_count += 1
        
        # Commit all changes
        session.commit()
        
        print(f"Successfully updated {updated_count} practices with Kosha field.")
        print(f"Updated {sum(1 for p in practices if p.practice_segment == 'Suryanamaskara')} practices from 'Suryanamaskara' to 'Sequential Yogic Practice'.")
        
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

