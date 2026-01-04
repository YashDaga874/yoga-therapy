"""
Script to add database indexes to existing database.
Run this after updating models.py to ensure indexes are created.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, get_engine
from sqlalchemy import text

def add_indexes():
    """Add indexes to existing database if they don't exist"""
    session = get_session()
    engine = get_engine()
    
    try:
        indexes_to_create = [
            # Disease indexes
            ("idx_disease_name", "diseases", "name"),
            
            # Practice indexes
            ("idx_practice_english", "practices", "practice_english"),
            ("idx_practice_sanskrit", "practices", "practice_sanskrit"),
            ("idx_practice_segment", "practices", "practice_segment"),
            ("idx_practice_module_id", "practices", "module_id"),
            ("idx_practice_citation_id", "practices", "citation_id"),
            ("idx_practice_kosha", "practices", "kosha"),
            
            # Citation indexes
            ("idx_citation_text", "citations", "citation_text"),
            
            # Contraindication indexes
            ("idx_contraindication_english", "contraindications", "practice_english"),
            ("idx_contraindication_segment", "contraindications", "practice_segment"),
            
            # Module indexes
            ("idx_module_disease_id", "modules", "disease_id"),
            ("idx_module_developed_by", "modules", "developed_by"),
            
            # RCT indexes
            ("idx_rct_doi", "rcts", "doi"),
            ("idx_rct_study_type", "rcts", "study_type"),
        ]
        
        # Check if using SQLite or PostgreSQL
        db_url = str(engine.url)
        is_sqlite = db_url.startswith('sqlite')
        
        created_count = 0
        existing_count = 0
        
        for index_name, table_name, column_name in indexes_to_create:
            try:
                if is_sqlite:
                    # SQLite: Check if index exists
                    check_query = text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
                    result = session.execute(check_query).fetchone()
                    
                    if result:
                        print(f"Index {index_name} already exists")
                        existing_count += 1
                        continue
                    
                    # Create index
                    create_query = text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
                    session.execute(create_query)
                    print(f"Created index: {index_name} on {table_name}({column_name})")
                    created_count += 1
                else:
                    # PostgreSQL: Use IF NOT EXISTS
                    create_query = text(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
                    session.execute(create_query)
                    print(f"Created index: {index_name} on {table_name}({column_name})")
                    created_count += 1
            except Exception as e:
                print(f"Error creating index {index_name}: {e}")
        
        # Create composite index for practices (SQLite specific syntax)
        if is_sqlite:
            composite_index_name = "idx_practice_segment_kosha"
            check_query = text(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{composite_index_name}'")
            result = session.execute(check_query).fetchone()
            
            if not result:
                create_query = text(f"CREATE INDEX {composite_index_name} ON practices(practice_segment, kosha)")
                session.execute(create_query)
                print(f"Created composite index: {composite_index_name}")
                created_count += 1
        else:
            # PostgreSQL
            create_query = text("CREATE INDEX IF NOT EXISTS idx_practice_segment_kosha ON practices(practice_segment, kosha)")
            try:
                session.execute(create_query)
                print(f"Created composite index: idx_practice_segment_kosha")
                created_count += 1
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"Error creating composite index: {e}")
        
        session.commit()
        
        print(f"\n[OK] Index creation complete!")
        print(f"   Created: {created_count} indexes")
        print(f"   Already existed: {existing_count} indexes")
        
    except Exception as e:
        session.rollback()
        print(f"[ERROR] Error adding indexes: {e}")
        raise
    finally:
        session.close()

if __name__ == '__main__':
    print("Adding database indexes for performance optimization...")
    add_indexes()
    print("Done!")

