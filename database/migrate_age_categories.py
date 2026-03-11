"""
Migration: Replace age_range with age_categories in modules and contraindications

This script updates the database schema to store age as a JSON array of categories
instead of min/max range values.

Age categories:
- Young children (1–4 years)
- Older children (5–9 years)
- Young adolescents (10–14 years)
- Older adolescents (15–19 years)
- Young adults (20–24 years)
- Adults (25–59 years)
- Older adults (60–99 years)
"""

import sqlite3
import os
import json
from pathlib import Path

# Find the database path
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
        
        # Check if age_categories column already exists in modules table
        cursor.execute("PRAGMA table_info(modules);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'age_categories' not in columns:
            print("Adding age_categories column to modules table...")
            cursor.execute("ALTER TABLE modules ADD COLUMN age_categories TEXT;")
            print("✓ Added age_categories column to modules")
        else:
            print("age_categories column already exists in modules table")
        
        # Check if age_categories column already exists in contraindications table
        cursor.execute("PRAGMA table_info(contraindications);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'age_categories' not in columns:
            print("Adding age_categories column to contraindications table...")
            cursor.execute("ALTER TABLE contraindications ADD COLUMN age_categories TEXT;")
            print("✓ Added age_categories column to contraindications")
        else:
            print("age_categories column already exists in contraindications table")
        
        # Optionally: migrate existing age_range data to age_categories
        # For now, we'll leave old data as-is and new entries will use the new format
        
        conn.commit()
        conn.close()
        
        print("\n✓ Migration completed successfully!")
        print("  - modules.age_categories: ready for age category JSON arrays")
        print("  - contraindications.age_categories: ready for age category JSON arrays")
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
