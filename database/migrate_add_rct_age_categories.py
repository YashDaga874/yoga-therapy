"""
Migration: Add age_categories column to rcts table

This adds a new column to store age categories selected when entering RCT data.
"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'yoga_therapy.db')
db_path = os.path.abspath(db_path)

def migrate():
    """Run the migration"""
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if age_categories column already exists in rcts table
        cursor.execute("PRAGMA table_info(rcts);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'age_categories' not in columns:
            print("Adding age_categories column to rcts table...")
            cursor.execute("ALTER TABLE rcts ADD COLUMN age_categories TEXT;")
            print("✓ Added age_categories column to rcts")
        else:
            print("age_categories column already exists in rcts table")
        
        conn.commit()
        conn.close()
        
        print("\n✓ Migration completed successfully!")
        print("  - rcts.age_categories: ready for age category JSON arrays")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
