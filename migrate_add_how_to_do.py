"""
Migration Script to Add 'how_to_do' Column to Practices Table
Run this script to update your existing database.
"""

import sqlite3
import sys
import os

# Path to your database
DB_PATH = os.path.join(os.path.dirname(__file__), 'yoga_therapy.db')

def migrate_database():
    """Add the how_to_do column to the practices table"""
    
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(practices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'how_to_do' in columns:
            print("Column 'how_to_do' already exists. Migration not needed.")
            conn.close()
            return True
        
        # Add the new column
        print("Adding 'how_to_do' column to practices table...")
        cursor.execute("ALTER TABLE practices ADD COLUMN how_to_do TEXT")
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == '__main__':
    print("Starting database migration...")
    success = migrate_database()
    sys.exit(0 if success else 1)

