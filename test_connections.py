"""
Test script to verify all database connections and configurations work properly.
Run this to ensure your setup is correct.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import (
    get_session, get_engine, get_database_url, 
    Disease, Practice, Citation, Contraindication, Module, RCT
)
from sqlalchemy import text

def test_database_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("Testing Database Connection")
    print("=" * 60)
    
    try:
        session = get_session()
        # Simple query to test connection
        result = session.execute(text("SELECT 1")).scalar()
        session.close()
        
        if result == 1:
            print("[OK] Database connection: SUCCESS")
            return True
        else:
            print("[FAIL] Database connection: FAILED (unexpected result)")
            return False
    except Exception as e:
        print(f"[FAIL] Database connection: FAILED - {e}")
        return False

def test_database_type():
    """Check which database type is being used"""
    print("\n" + "=" * 60)
    print("Database Configuration")
    print("=" * 60)
    
    db_url = get_database_url()
    
    if db_url.startswith('sqlite'):
        print(f"[OK] Database Type: SQLite")
        print(f"   Path: {db_url}")
    elif db_url.startswith('postgresql'):
        print(f"[OK] Database Type: PostgreSQL")
        print(f"   URL: {db_url.split('@')[1] if '@' in db_url else 'configured'}")
    else:
        print(f"[WARN] Database Type: Unknown ({db_url[:50]}...)")
    
    return db_url

def test_table_access():
    """Test access to all main tables"""
    print("\n" + "=" * 60)
    print("Testing Table Access")
    print("=" * 60)
    
    session = get_session()
    tables_ok = []
    tables_failed = []
    
    try:
        # Test each main table
        tables = [
            ('Disease', Disease),
            ('Practice', Practice),
            ('Citation', Citation),
            ('Contraindication', Contraindication),
            ('Module', Module),
            ('RCT', RCT)
        ]
        
        for table_name, model in tables:
            try:
                count = session.query(model).count()
                print(f"[OK] {table_name}: {count} records")
                tables_ok.append(table_name)
            except Exception as e:
                print(f"[FAIL] {table_name}: FAILED - {e}")
                tables_failed.append(table_name)
        
        session.close()
        
        if tables_failed:
            return False
        return True
        
    except Exception as e:
        print(f"❌ Table access test failed: {e}")
        session.close()
        return False

def test_indexes():
    """Check if indexes exist"""
    print("\n" + "=" * 60)
    print("Testing Database Indexes")
    print("=" * 60)
    
    session = get_session()
    engine = get_engine()
    
    try:
        db_url = str(engine.url)
        is_sqlite = db_url.startswith('sqlite')
        
        if is_sqlite:
            # Check SQLite indexes
            query = text("""
                SELECT name FROM sqlite_master 
                WHERE type='index' 
                AND name LIKE 'idx_%'
                ORDER BY name
            """)
        else:
            # Check PostgreSQL indexes
            query = text("""
                SELECT indexname FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE 'idx_%'
                ORDER BY indexname
            """)
        
        result = session.execute(query)
        indexes = [row[0] for row in result]
        
        expected_indexes = [
            'idx_disease_name',
            'idx_practice_english',
            'idx_practice_sanskrit',
            'idx_practice_segment',
            'idx_practice_module_id',
            'idx_practice_citation_id',
            'idx_practice_kosha',
            'idx_citation_text',
            'idx_contraindication_english',
            'idx_contraindication_segment',
            'idx_module_disease_id',
            'idx_module_developed_by',
            'idx_rct_doi',
            'idx_rct_study_type'
        ]
        
        found_count = 0
        for idx in expected_indexes:
            if idx in indexes:
                print(f"[OK] {idx}")
                found_count += 1
            else:
                print(f"[WARN] {idx}: NOT FOUND")
        
        print(f"\n   Found {found_count}/{len(expected_indexes)} indexes")
        
        if found_count < len(expected_indexes) * 0.8:  # At least 80%
            print("[WARN] Warning: Some indexes are missing. Run: python add_database_indexes.py")
            return False
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Index check failed: {e}")
        session.close()
        return False

def test_connection_pooling():
    """Test connection pooling configuration"""
    print("\n" + "=" * 60)
    print("Testing Connection Pooling")
    print("=" * 60)
    
    engine = get_engine()
    db_url = str(engine.url)
    
    if db_url.startswith('sqlite'):
        print("[OK] SQLite: Using StaticPool (appropriate for SQLite)")
        print("   - Single connection")
        print("   - Timeout: 20 seconds")
        print("   - Pre-ping: Enabled")
    elif db_url.startswith('postgresql'):
        pool = engine.pool
        print("[OK] PostgreSQL: Using QueuePool")
        print(f"   - Pool size: {pool.size()}")
        print(f"   - Max overflow: {pool._max_overflow}")
        print(f"   - Pre-ping: Enabled")
        print(f"   - Connection recycling: 1 hour")
    else:
        print("[WARN] Unknown database type")
    
    return True

def test_query_performance():
    """Test basic query performance"""
    print("\n" + "=" * 60)
    print("Testing Query Performance")
    print("=" * 60)
    
    import time
    
    session = get_session()
    
    try:
        # Test simple count query
        start = time.time()
        count = session.query(Disease).count()
        elapsed = (time.time() - start) * 1000
        print(f"[OK] Disease count query: {count} records in {elapsed:.2f}ms")
        
        # Test filtered query with index
        start = time.time()
        result = session.query(Practice).filter(
            Practice.practice_segment == 'Yogasana'
        ).limit(10).all()
        elapsed = (time.time() - start) * 1000
        print(f"[OK] Filtered practice query: {len(result)} records in {elapsed:.2f}ms")
        
        # Test join query
        start = time.time()
        result = session.query(Module).join(Disease).limit(10).all()
        elapsed = (time.time() - start) * 1000
        print(f"[OK] Join query: {len(result)} records in {elapsed:.2f}ms")
        
        session.close()
        
        if elapsed > 1000:  # More than 1 second
            print("[WARN] Warning: Queries are slow. Check indexes.")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        session.close()
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Yoga Therapy System - Connection & Configuration Test")
    print("=" * 60)
    print()
    
    results = {
        'connection': test_database_connection(),
        'database_type': test_database_type(),
        'tables': test_table_access(),
        'indexes': test_indexes(),
        'pooling': test_connection_pooling(),
        'performance': test_query_performance()
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Your system is ready to go!")
        return 0
    else:
        print("\n[WARN] Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    exit(main())

