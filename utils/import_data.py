"""
Data Import Utility

This script helps import data from JSON files into the database.
It can handle the sample JSON format provided and populate all tables.
"""

import json
from database.models import (
    Disease, Practice, Citation, Contraindication, Module,
    create_database, get_session
)


class DataImporter:
    """
    Imports yoga therapy data from JSON into the database
    """
    
    def __init__(self, db_path='sqlite:///yoga_therapy.db'):
        self.db_path = db_path
        # Create database if it doesn't exist
        create_database(db_path)
        self.session = get_session(db_path)
        
        # Cache to avoid duplicate citations
        self.citation_cache = {}
    
    def import_from_json(self, json_data):
        """
        Import data from a JSON structure
        
        Args:
            json_data: Dictionary containing disease data
        """
        
        for disease_name, disease_data in json_data.items():
            print(f"\nImporting disease: {disease_name}")
            
            # Create or get disease
            disease = self._get_or_create_disease(disease_name)
            
            # Import module information if it exists
            if 'Module' in disease_data:
                self._import_module(disease, disease_data['Module'])
                disease_data = disease_data['Module']  # Unwrap the Module structure
            
            # Import practices from each kosa
            for kosa_name, kosa_content in disease_data.items():
                if kosa_name == 'Developed by':
                    continue  # Already handled in module
                    
                if kosa_name.endswith('_Kosa'):
                    print(f"  Processing {kosa_name}...")
                    self._import_kosa_practices(disease, kosa_name, kosa_content)
            
            # Commit after each disease
            self.session.commit()
            print(f"[OK] Completed importing {disease_name}")
    
    def _get_or_create_disease(self, disease_name):
        """
        Get existing disease or create new one
        """
        disease = self.session.query(Disease).filter_by(name=disease_name).first()
        
        if not disease:
            disease = Disease(name=disease_name)
            self.session.add(disease)
            self.session.flush()  # Get the ID
        
        return disease
    
    def _import_module(self, disease, module_data):
        """
        Import module metadata
        """
        if 'Developed by' in module_data:
            # Check if module already exists
            module = self.session.query(Module).filter_by(disease_id=disease.id).first()
            
            if not module:
                module = Module(
                    disease_id=disease.id,
                    developed_by=module_data['Developed by']
                )
                self.session.add(module)
    
    def _import_kosa_practices(self, disease, kosa_name, kosa_content):
        """
        Import practices for a specific kosa
        """
        citation = self._get_citation_from_context(kosa_content)
        
        # Handle different structures in the JSON
        if isinstance(kosa_content, dict):
            for category, practices_data in kosa_content.items():
                if category == 'Developed by':
                    continue
                
                # Different categories have different structures
                if category == 'Asana':
                    # Asana has subcategories
                    for sub_cat, asana_list in practices_data.items():
                        if isinstance(asana_list, list):
                            for practice_data in asana_list:
                                self._create_practice(
                                    disease, kosa_name, sub_cat, 
                                    practice_data, citation
                                )
                
                elif isinstance(practices_data, list):
                    # Direct list of practices
                    for practice_data in practices_data:
                        self._create_practice(
                            disease, kosa_name, category,
                            practice_data, citation
                        )
                
                elif isinstance(practices_data, dict):
                    # Could be a single practice or nested structure
                    if 'practice_english' in practices_data or 'practice_sanskrit' in practices_data:
                        # Single practice
                        self._create_practice(
                            disease, kosa_name, category,
                            practices_data, citation
                        )
                    else:
                        # Nested structure (like pranayama_practices)
                        for sub_cat, sub_data in practices_data.items():
                            if isinstance(sub_data, list):
                                for practice_data in sub_data:
                                    self._create_practice(
                                        disease, kosa_name, sub_cat,
                                        practice_data, citation
                                    )
                            elif isinstance(sub_data, dict):
                                self._create_practice(
                                    disease, kosa_name, sub_cat,
                                    sub_data, citation
                                )
    
    def _create_practice(self, disease, kosa, sub_category, practice_data, citation):
        """
        Create a practice entry and link it to the disease
        """
        # Check if this exact practice already exists
        existing_practice = self.session.query(Practice).filter_by(
            practice_english=practice_data.get('practice_english'),
            kosa=kosa,
            sub_category=sub_category
        ).first()
        
        if existing_practice:
            # Link to disease if not already linked
            if disease not in existing_practice.diseases:
                existing_practice.diseases.append(disease)
            return existing_practice
        
        # Create new practice
        practice = Practice(
            practice_sanskrit=practice_data.get('practice_sanskrit'),
            practice_english=practice_data.get('practice_english'),
            kosa=kosa,
            sub_category=sub_category,
            rounds=practice_data.get('rounds'),
            time_minutes=practice_data.get('time_minutes'),
            strokes_per_min=practice_data.get('strokes_per_min'),
            strokes_per_cycle=practice_data.get('strokes_per_cycle'),
            rest_between_cycles_sec=practice_data.get('rest_between_cycles_sec'),
            description=practice_data.get('description')
        )
        
        # Handle variations (convert list to JSON string)
        if 'variations' in practice_data:
            practice.variations = json.dumps(practice_data['variations'])
        
        # Handle steps (convert list to JSON string)
        if 'Steps' in practice_data:
            practice.steps = json.dumps(practice_data['Steps'])
        
        # Add citation if available
        if citation:
            practice.citation = citation
        
        # Link to disease
        practice.diseases.append(disease)
        
        self.session.add(practice)
        return practice
    
    def _get_citation_from_context(self, data):
        """
        Try to extract citation from 'Developed by' field
        """
        if isinstance(data, dict) and 'Developed by' in data:
            citation_text = data['Developed by']
            
            # Check cache
            if citation_text in self.citation_cache:
                return self.citation_cache[citation_text]
            
            # Create new citation
            citation = Citation(
                citation_text=citation_text,
                citation_type='research_paper'
            )
            self.session.add(citation)
            self.session.flush()
            
            self.citation_cache[citation_text] = citation
            return citation
        
        return None
    
    def import_contraindications_from_csv(self, csv_file_path):
        """
        Import contraindications from a CSV file
        
        CSV Format:
        disease_name,practice_english,kosa,sub_category,reason
        """
        import csv
        
        with open(csv_file_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                disease = self._get_or_create_disease(row['disease_name'])
                
                contraindication = Contraindication(
                    disease_id=disease.id,
                    practice_english=row['practice_english'],
                    kosa=row['kosa'],
                    sub_category=row.get('sub_category', ''),
                    reason=row.get('reason', '')
                )
                
                self.session.add(contraindication)
        
        self.session.commit()
        print("[OK] Contraindications imported successfully")
    
    def close(self):
        """Close database session"""
        self.session.close()


def import_sample_data():
    """
    Import the sample JSON data provided by the user
    """
    # Sample JSON from the user
    sample_json = {
        "Depression": {
            "Module": {
                "Developed by": "Dr Naveen GH et al.,2013",
                "Annamaya_Kosa": {
                    "Loosening_Practice": [
                        {
                            "practice_sanskrit": "Griva shakti vikasaka-l",
                            "practice_english": "Neck sideward movement",
                            "rounds": 5,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Griva shakti vikasaka-ll",
                            "practice_english": "Neck forward and backward bending",
                            "rounds": 5,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Manibandha shakti vikasaka",
                            "practice_english": "Wrist movement",
                            "rounds": 10,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Kaphoni shakti vikasaka",
                            "practice_english": "Elbow flexion and stretching",
                            "rounds": 3,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Bhuja valli shakti vikasaka",
                            "practice_english": "Arms movement",
                            "rounds": 3,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Janu shakti vikasaka",
                            "practice_english": "Knee stretching",
                            "rounds": 5,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Gulpha, pada pristha, pada tala shakti vikasaka",
                            "practice_english": "Ankle rotation (clockwise and anticlockwise)",
                            "rounds": 5,
                            "time_minutes": 1
                        },
                        {
                            "practice_sanskrit": "Kati shakti vikasaka",
                            "practice_english": "Twisting",
                            "rounds": 10,
                            "time_minutes": 1
                        },
                        {
                            "practice_english": "Jogging",
                            "variations": [
                                "Slow jogging",
                                "Forward jogging",
                                "Backward jogging",
                                "Sideward jogging"
                            ],
                            "rounds": 10,
                            "time_minutes": 2
                        },
                        {
                            "practice_sanskrit": "Mukha Dhauti",
                            "practice_english": "Cleaning through single blast breath",
                            "rounds": 5,
                            "time_minutes": 15
                        }
                    ],
                    "surya_namaskar": [{
                        "practice_sanskrit": "Surya namaskar",
                        "practice_english": "Sun salutation—12 steps",
                        "rounds": 3,
                        "time_minutes": 15
                    }],
                    "relaxation": [{
                        "practice_sanskrit": "Shavasana (with chanting of 'A')",
                        "practice_english": "Relaxation in corpse pose",
                        "rounds": 1,
                        "time_minutes": 2
                    }],
                    "Asana": {
                        "standing_asana": [
                            {
                                "practice_sanskrit": "Ardha chakrasana",
                                "practice_english": "Backward bending pose",
                                "rounds": 5,
                                "time_minutes": 2
                            }
                        ],
                        "sitting_asana": [
                            {
                                "practice_sanskrit": "Ardha ustrasana",
                                "practice_english": "Camel pose",
                                "rounds": 5,
                                "time_minutes": 2
                            },
                            {
                                "practice_sanskrit": "Paschimottanasana",
                                "practice_english": "Seated forward bending pose",
                                "rounds": 5,
                                "time_minutes": 2
                            }
                        ],
                        "prone_asana": [
                            {
                                "practice_sanskrit": "Bhujangasana",
                                "practice_english": "Serpent pose",
                                "rounds": 5,
                                "time_minutes": 2
                            }
                        ],
                        "supine_asana": [
                            {
                                "practice_sanskrit": "Pawanamuktasana",
                                "practice_english": "Wind releasing pose",
                                "rounds": 5,
                                "time_minutes": 2
                            },
                            {
                                "practice_sanskrit": "Viparitakarani mudra",
                                "practice_english": "Legs-up-the-wall pose",
                                "rounds": 5,
                                "time_minutes": 2
                            },
                            {
                                "practice_sanskrit": "Setu bandhasana",
                                "practice_english": "Bridge pose",
                                "rounds": 5,
                                "time_minutes": 2
                            }
                        ]
                    },
                    "final_relaxation": [{
                        "practice_sanskrit": "Shavasana",
                        "practice_english": "Relaxation in corpse pose/Yoga nidra",
                        "rounds": 1,
                        "time_minutes": 4
                    }],
                    "kriya_practices": [
                        {
                            "practice_sanskrit": "Kapalabhati",
                            "practice_english": "Breath of fire/Skull shining breath",
                            "rounds": 2,
                            "strokes_per_min": 40,
                            "time_minutes": 2
                        }
                    ]
                },
                "Pranamaya_Kosa": {
                    "pranayama_practices": [
                        {
                            "practice_sanskrit": "Surya anuloma viloma",
                            "practice_english": "Right nostril breathing",
                            "rounds": 21,
                            "time_minutes": 3
                        },
                        {
                            "practice_sanskrit": "Ujjayi",
                            "practice_english": "Victorious breath",
                            "rounds": 9,
                            "time_minutes": 2
                        },
                        {
                            "practice_sanskrit": "Bhastrika",
                            "practice_english": "Bellows' breathing",
                            "rounds": 3,
                            "strokes_per_cycle": 20,
                            "rest_between_cycles_sec": 30,
                            "time_minutes": 3
                        }
                    ]
                },
                "Manomaya_Kosa": {
                    "meditation_practices": [{
                        "practice_sanskrit": "Nadanusandhana",
                        "practice_english": "Sound resonance",
                        "Steps": ["AA kara", "UU kara", "MM kara", "AUM kara"],
                        "rounds": 9,
                        "time_minutes": 5
                    }]
                },
                "Vijnanamaya_Kosa": {
                    "yogic_counseling": {
                        "description": "Understanding of kleshas according to Yoga and ways to overcome them according to Patanjali"
                    }
                }
            }
        }
    }
    
    print("=" * 60)
    print("Importing Sample Data into Database")
    print("=" * 60)
    
    importer = DataImporter()
    try:
        importer.import_from_json(sample_json)
        print("\n" + "=" * 60)
        print("[OK] Sample data imported successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[ERROR] Error during import: {e}")
        import traceback
        traceback.print_exc()
    finally:
        importer.close()


if __name__ == '__main__':
    import_sample_data()