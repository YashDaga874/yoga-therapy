"""
Database Migration Script

This script recreates the database with the new disease combination structure.
It will:
1. Backup existing data
2. Drop and recreate tables with new schema
3. Re-import the data
4. Populate disease combinations
"""

import os
import shutil
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import create_database, get_session, Disease, Practice, Citation, Module
from utils.populate_disease_combinations import populate_disease_combinations, populate_contraindications


def backup_database():
    """
    Create a backup of the existing database
    """
    db_path = "yoga_therapy.db"
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"yoga_therapy_backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to: {backup_path}")
        return backup_path
    return None


def recreate_database():
    """
    Recreate the database with new schema
    """
    print("Recreating database with new schema...")
    
    # Remove existing database file
    db_path = "yoga_therapy.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    # Create new database with updated schema
    engine = create_database()
    print("New database created with updated schema")
    
    return engine


def reimport_data():
    """
    Re-import the sample data
    """
    print("Re-importing sample data...")
    
    # Import the sample data
    from utils.import_data import import_sample_data
    import_sample_data()
    print("Sample data imported successfully")


def populate_new_structure():
    """
    Populate the new disease combination structure
    """
    print("Populating disease combinations and contraindications...")
    
    session = get_session()
    
    try:
        # Step 1: Create all disease combinations
        created_combinations = populate_disease_combinations(session)
        
        # Step 2: Populate contraindications
        populate_contraindications(session, created_combinations)
        
        print("Disease combinations and contraindications populated successfully")
        
    except Exception as e:
        print(f"Error populating new structure: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def verify_migration():
    """
    Verify that the migration was successful
    """
    print("Verifying migration...")
    
    session = get_session()
    
    try:
        # Check diseases
        diseases = session.query(Disease).all()
        print(f"Diseases: {len(diseases)}")
        
        # Check disease combinations
        from database.models import DiseaseCombination
        combinations = session.query(DiseaseCombination).all()
        print(f"Disease combinations: {len(combinations)}")
        
        # Check contraindications
        from database.models import Contraindication
        contraindications = session.query(Contraindication).all()
        print(f"Contraindications: {len(contraindications)}")
        
        # Show some examples
        print("\nSample disease combinations:")
        for combo in combinations[:5]:
            print(f"  - {combo.combination_name}")
        
        print("\nSample contraindications:")
        for contra in contraindications[:5]:
            print(f"  - {contra.practice_english} ({contra.kosa})")
        
    finally:
        session.close()


def main():
    """
    Main migration function
    """
    print("=== Database Migration: Disease Combination Structure ===\n")
    
    try:
        # Step 1: Backup existing database
        backup_path = backup_database()
        
        # Step 2: Recreate database with new schema
        recreate_database()
        
        # Step 3: Re-import sample data
        reimport_data()
        
        # Step 4: Populate new structure
        populate_new_structure()
        
        # Step 5: Verify migration
        verify_migration()
        
        print("\n=== Migration Completed Successfully ===")
        if backup_path:
            print(f"Original database backed up to: {backup_path}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"You can restore from backup: {backup_path}")
        raise


if __name__ == "__main__":
    main()
