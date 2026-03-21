"""
Migration: Add ICD/DSM code column to diseases table
This allows storing diagnostic codes for each condition.
"""

import sqlite3
import os


def add_column(conn, column_name, column_type):
    cursor = conn.cursor()
    cursor.execute(f"ALTER TABLE diseases ADD COLUMN {column_name} {column_type}")
    conn.commit()


def main():
    # Get database path from DATABASE_URL or use default SQLite
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from database.models import get_database_url
    db_url = get_database_url()

    if not db_url.startswith('sqlite'):
        print("This migration is designed for SQLite. PostgreSQL migrations are handled differently.")
        return

    db_path = db_url.replace('sqlite:///', '').replace('sqlite:///', '')
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(diseases)")
        columns = {col[1] for col in cursor.fetchall()}

        if 'icd_dsm_code' in columns:
            print("[OK] Column 'icd_dsm_code' already exists")
        else:
            print("Adding column 'icd_dsm_code' (VARCHAR(100))...")
            add_column(conn, 'icd_dsm_code', 'VARCHAR(100)')
            print("[OK] Column added successfully")

    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
