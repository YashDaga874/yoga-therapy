"""
Migration Script to Update Contraindications and Add Media Fields
- Changes contraindications from disease combinations to individual diseases
- Adds photo_path and video_path to practices table
"""

import sqlite3
import sys
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'yoga_therapy.db')

def migrate_database():
    """Migrate database structure"""
    
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check current structure
        cursor.execute("PRAGMA table_info(practices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add photo_path if it doesn't exist
        if 'photo_path' not in columns:
            print("Adding 'photo_path' column to practices table...")
            cursor.execute("ALTER TABLE practices ADD COLUMN photo_path TEXT")
        
        # Add video_path if it doesn't exist
        if 'video_path' not in columns:
            print("Adding 'video_path' column to practices table...")
            cursor.execute("ALTER TABLE practices ADD COLUMN video_path TEXT")
        
        # Check if disease_contraindication_association exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='disease_contraindication_association'")
        if cursor.fetchone() is None:
            print("Creating disease_contraindication_association table...")
            cursor.execute("""
                CREATE TABLE disease_contraindication_association (
                    disease_id INTEGER NOT NULL,
                    contraindication_id INTEGER NOT NULL,
                    PRIMARY KEY (disease_id, contraindication_id),
                    FOREIGN KEY(disease_id) REFERENCES diseases (id),
                    FOREIGN KEY(contraindication_id) REFERENCES contraindications (id)
                )
            """)
            
            # Migrate existing data from disease_combination_contraindication_association
            # This maps disease combinations to individual diseases
            cursor.execute("""
                SELECT DISTINCT dc.id as disease_combo_id, dc.diseases_json, dca.contraindication_id
                FROM disease_combination_contraindication_association dca
                JOIN disease_combinations dc ON dca.disease_combination_id = dc.id
            """)
            
            data = cursor.fetchall()
            print(f"Found {len(data)} disease combination contraindications to migrate...")
            
            for disease_combo_id, diseases_json, contra_id in data:
                try:
                    import json
                    disease_names = json.loads(diseases_json) if diseases_json else []
                    
                    for disease_name in disease_names:
                        # Find disease by name
                        cursor.execute("SELECT id FROM diseases WHERE name = ?", (disease_name,))
                        disease = cursor.fetchone()
                        
                        if disease:
                            disease_id = disease[0]
                            # Insert into new association table
                            cursor.execute("""
                                INSERT OR IGNORE INTO disease_contraindication_association (disease_id, contraindication_id)
                                VALUES (?, ?)
                            """, (disease_id, contra_id))
                            print(f"  Migrated: {disease_name} -> contraindication {contra_id}")
                except Exception as e:
                    print(f"  Error migrating disease combo {disease_combo_id}: {e}")
        
        conn.commit()
        conn.close()
        
        print("\nMigration completed successfully!")
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

