"""
Script to add CVR score field to practices table if missing.
Run this after pulling new changes to ensure database schema stays up to date.
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session
from sqlalchemy import text

DB_PATH = 'sqlite:///yoga_therapy.db'


def column_exists(session, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        result = session.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        return column_name in columns
    except Exception:
        return False


def add_cvr_score_column():
    """Add cvr_score column to practices table if it doesn't exist"""
    session = get_session(DB_PATH)
    try:
        if column_exists(session, 'practices', 'cvr_score'):
            print('cvr_score column already exists in practices table')
            return

        print('Adding cvr_score column to practices table...')
        session.execute(text('ALTER TABLE practices ADD COLUMN cvr_score FLOAT'))
        session.commit()
        print('cvr_score column added successfully!')
    except Exception as exc:
        session.rollback()
        print(f'Error adding cvr_score column: {exc}')
    finally:
        session.close()


if __name__ == '__main__':
    add_cvr_score_column()

