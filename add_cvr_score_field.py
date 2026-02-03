"""
Script to add CVR score field to practices table if missing.
Run this after pulling new changes to ensure database schema stays up to date.
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, get_database_url
from sqlalchemy import text

DB_PATH = get_database_url()


def column_exists(session, table_name, column_name):
    """Check if a column exists in a table for SQLite or PostgreSQL."""
    try:
        engine = session.get_bind()
        dialect = engine.dialect.name
        if dialect == 'sqlite':
            result = session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result]
            return column_name in columns
        # PostgreSQL path
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


def add_cvr_score_column():
    """Add cvr_score column to practices table if it doesn't exist"""
    session = get_session(DB_PATH)
    try:
        if column_exists(session, 'practices', 'cvr_score'):
            print('cvr_score column already exists in practices table')
            return
        engine = session.get_bind()
        dialect = engine.dialect.name
        alter_sql = "ALTER TABLE practices ADD COLUMN cvr_score FLOAT"
        if dialect.startswith('postgres'):
            alter_sql = "ALTER TABLE IF NOT EXISTS practices ADD COLUMN cvr_score DOUBLE PRECISION"

        print('Adding cvr_score column to practices table...')
        session.execute(text(alter_sql))
        session.commit()
        print('cvr_score column added successfully!')
    except Exception as exc:
        session.rollback()
        print(f'Error adding cvr_score column: {exc}')
    finally:
        session.close()


if __name__ == '__main__':
    add_cvr_score_column()

