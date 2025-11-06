"""
Script to update parenthetical citations for all diseases (modules)
and set 'how_to_do' field for all practices to 'To do'
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, Module, Practice

# Database path
DB_PATH = 'sqlite:///yoga_therapy.db'

def update_citations_and_practices():
    """Update all modules' developed_by field and all practices' how_to_do field"""
    session = get_session(DB_PATH)
    
    try:
        # Update all modules' developed_by field (parenthetical citation)
        modules = session.query(Module).all()
        modules_updated = 0
        for module in modules:
            module.developed_by = "Dr Naveen GH et al.,2013"
            modules_updated += 1
        
        # Update all practices' how_to_do field
        practices = session.query(Practice).all()
        practices_updated = 0
        for practice in practices:
            practice.how_to_do = "To do"
            practices_updated += 1
        
        # Commit all changes
        session.commit()
        
        print(f"Successfully updated {modules_updated} modules with parenthetical citation: 'Dr Naveen GH et al.,2013'")
        print(f"Successfully updated {practices_updated} practices with 'how_to_do' field: 'To do'")
        
    except Exception as e:
        session.rollback()
        print(f"Error updating database: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting update process...")
    update_citations_and_practices()
    print("Update completed!")

