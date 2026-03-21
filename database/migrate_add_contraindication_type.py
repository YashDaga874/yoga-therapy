"""
Migration: Add contraindication_type column to contraindications table
This allows storing different contraindication scopes: practice, category, or kosha.
"""

import sqlite3
import os


def add_column(conn, column_name, column_type, default_value=None):
    cursor = conn.cursor()
    if default_value:
        cursor.execute(f"ALTER TABLE contraindications ADD COLUMN {column_name} {column_type} DEFAULT '{default_value}'")
    else:
        cursor.execute(f"ALTER TABLE contraindications ADD COLUMN {column_name} {column_type}")
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

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(contraindications)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'contraindication_type' not in columns:
            print(f"Adding contraindication_type column to {db_path}...")
            add_column(conn, 'contraindication_type', 'VARCHAR(50)', 'practice')
            print("✅ Successfully added contraindication_type column with default 'practice'")
        else:
            print("✅ contraindication_type column already exists")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
