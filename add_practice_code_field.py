"""
Migration script to add practice code field and generate codes for existing practices.

This script:
1. Adds the 'code' column to the practices table
2. Generates codes for all existing practices based on their Sanskrit names
3. Ensures practices with the same Sanskrit name get the same code

Run this script once to migrate your database.
"""

import sys
import os
import re
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, Practice, get_engine


def generate_practice_code(sanskrit_name, existing_codes=None):
    """
    Generate a practice code based on Sanskrit name.
    
    Methodology:
    - Take first letter of each word in Sanskrit name (capitalized)
    - If single word, take first 2-3 letters
    - Add a 2-digit number suffix if needed for uniqueness
    
    Examples:
    - Kapalabhati -> K01
    - Shavasana -> S01
    - Bhujangasana -> B01
    - Padmasana -> P01
    - Anulom Vilom -> AV01
    
    Args:
        sanskrit_name: The Sanskrit name of the practice
        existing_codes: Set of existing codes to avoid duplicates
        
    Returns:
        A unique code string
    """
    if not sanskrit_name or not sanskrit_name.strip():
        return None
    
    existing_codes = existing_codes or set()
    
    # Clean the Sanskrit name
    name = sanskrit_name.strip()
    
    # Split by spaces and get first letters
    words = name.split()
    
    if len(words) == 1:
        # Single word: take first 2-3 letters, capitalize
        base_code = name[:3].upper()
    else:
        # Multiple words: take first letter of each word
        base_code = ''.join([word[0].upper() for word in words if word])
    
    # Remove any non-alphabetic characters
    base_code = re.sub(r'[^A-Z]', '', base_code)
    
    if not base_code:
        # Fallback: use first 3 characters of name
        base_code = name[:3].upper()
        base_code = re.sub(r'[^A-Z]', '', base_code)
        if not base_code:
            base_code = 'PRC'  # Practice
    
    # Generate code with number suffix
    code = base_code
    counter = 1
    
    while code in existing_codes:
        # Add 2-digit suffix
        code = f"{base_code}{counter:02d}"
        counter += 1
        
        # Prevent infinite loop
        if counter > 99:
            # Use hash as fallback
            import hashlib
            hash_suffix = hashlib.md5(name.encode()).hexdigest()[:2].upper()
            code = f"{base_code}{hash_suffix}"
            break
    
    return code


def migrate_practice_codes():
    """
    Add code column and generate codes for all practices.
    """
    engine = get_engine()
    session = get_session()
    
    try:
        print("Starting practice code migration...")
        
        # Check if code column already exists
        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(practices)"))
            columns = [row[1] for row in result]
            
            if 'code' not in columns:
                print("Adding 'code' column to practices table...")
                conn.execute(text("ALTER TABLE practices ADD COLUMN code VARCHAR(50)"))
                conn.commit()
                print("Code column added successfully.")
            else:
                print("Code column already exists.")
        
        # Get all practices grouped by Sanskrit name
        print("Generating codes for practices...")
        all_practices = session.query(Practice).all()
        
        # Group practices by Sanskrit name (case-insensitive)
        sanskrit_groups = {}
        for practice in all_practices:
            sanskrit_key = (practice.practice_sanskrit or '').strip().lower()
            if sanskrit_key:
                if sanskrit_key not in sanskrit_groups:
                    sanskrit_groups[sanskrit_key] = []
                sanskrit_groups[sanskrit_key].append(practice)
        
        # Generate codes for each group
        existing_codes = set()
        code_updates = []
        
        # First, collect all existing codes
        for practice in all_practices:
            if practice.code:
                existing_codes.add(practice.code)
        
        # Generate codes for each Sanskrit name group
        for sanskrit_key, practices in sanskrit_groups.items():
            # Use the first practice's Sanskrit name for code generation
            first_practice = practices[0]
            code = generate_practice_code(first_practice.practice_sanskrit, existing_codes)
            
            if code:
                existing_codes.add(code)
                # Assign same code to all practices with this Sanskrit name
                for practice in practices:
                    if not practice.code:  # Only update if code is not already set
                        practice.code = code
                        code_updates.append((practice.id, code))
        
        # Handle practices without Sanskrit names (use English name)
        practices_without_sanskrit = [p for p in all_practices if not (p.practice_sanskrit or '').strip()]
        for practice in practices_without_sanskrit:
            if not practice.code:
                code = generate_practice_code(practice.practice_english, existing_codes)
                if code:
                    existing_codes.add(code)
                    practice.code = code
                    code_updates.append((practice.id, code))
        
        # Commit all changes
        session.commit()
        
        print(f"Successfully generated codes for {len(code_updates)} practices.")
        print(f"Total unique Sanskrit names: {len(sanskrit_groups)}")
        
        # Show some examples
        print("\nSample generated codes:")
        sample_practices = session.query(Practice).filter(Practice.code.isnot(None)).limit(10).all()
        for p in sample_practices:
            print(f"  {p.code}: {p.practice_sanskrit or p.practice_english}")
        
        print("\nMigration completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == '__main__':
    migrate_practice_codes()
