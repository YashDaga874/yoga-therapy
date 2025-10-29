"""
Populate Disease Combinations and Contraindications

This script creates all possible disease combinations and populates them with
contraindications based on the new structure where contraindications apply to
disease COMBINATIONS rather than individual diseases.
"""

import sys
import os
import json

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Disease, DiseaseCombination, Contraindication, get_session
from utils.disease_combinations import generate_disease_combinations, create_contraindication_structure


def populate_disease_combinations(session):
    """
    Create all possible disease combinations in the database.
    """
    # Get all diseases from the database
    diseases = session.query(Disease).all()
    disease_names = [d.name for d in diseases]
    
    print(f"Found {len(disease_names)} diseases: {', '.join(disease_names)}")
    
    # Generate all combinations
    combinations_dict = generate_disease_combinations(disease_names)
    
    # Create disease combinations in database
    created_combinations = {}
    
    for size, combos in combinations_dict.items():
        print(f"\nCreating {len(combos)} combinations of {size} disease(s)...")
        
        for combo in combos:
            # Create combination name
            combo_list = sorted(list(combo))
            combination_name = " + ".join(combo_list)
            
            # Check if combination already exists
            existing = session.query(DiseaseCombination).filter_by(
                combination_name=combination_name
            ).first()
            
            if not existing:
                # Create new disease combination
                disease_combo = DiseaseCombination(
                    combination_name=combination_name,
                    diseases_json=json.dumps(combo_list)
                )
                session.add(disease_combo)
                session.flush()  # Get the ID
                
                created_combinations[combo] = disease_combo
                print(f"  Created: {combination_name}")
            else:
                created_combinations[combo] = existing
                print(f"  Already exists: {combination_name}")
    
    session.commit()
    print(f"\nTotal disease combinations created: {len(created_combinations)}")
    
    return created_combinations


def populate_contraindications(session, created_combinations):
    """
    Populate contraindications for disease combinations.
    """
    # Get the contraindication structure
    contraindication_structure = create_contraindication_structure()
    
    print(f"\nPopulating contraindications for {len(contraindication_structure)} combinations...")
    
    contraindications_created = 0
    
    for disease_combo, contraindications_by_kosa in contraindication_structure.items():
        # Find the corresponding database combination
        if disease_combo in created_combinations:
            db_combo = created_combinations[disease_combo]
            print(f"\nProcessing: {db_combo.combination_name}")
            
            # Create contraindications for this combination
            for kosa, practices in contraindications_by_kosa.items():
                for practice_name in practices:
                    # Check if contraindication already exists
                    existing = session.query(Contraindication).filter_by(
                        practice_english=practice_name,
                        kosa=kosa
                    ).first()
                    
                    if not existing:
                        # Create new contraindication
                        contraindication = Contraindication(
                            practice_english=practice_name,
                            kosa=kosa,
                            reason=f"Contraindicated for {db_combo.combination_name}"
                        )
                        session.add(contraindication)
                        session.flush()  # Get the ID
                        contraindications_created += 1
                        print(f"  Created contraindication: {practice_name} in {kosa}")
                    else:
                        contraindication = existing
                        print(f"  Using existing contraindication: {practice_name} in {kosa}")
                    
                    # Link contraindication to disease combination
                    if contraindication not in db_combo.contraindications:
                        db_combo.contraindications.append(contraindication)
    
    session.commit()
    print(f"\nTotal contraindications created: {contraindications_created}")


def create_sample_contraindications():
    """
    Create a more comprehensive sample contraindication structure.
    This is where you would add real contraindications based on medical knowledge.
    """
    return {
        # Single disease contraindications
        frozenset(["Depression"]): {
            "manomaya_kosha": [
                "Nada-Anusandhana (OM Chanting Meditation)"  # May increase rumination
            ]
        },
        
        frozenset(["GAD"]): {
            "annamaya_kosha": [
                "Vakrasana (Twisted Pose)"  # May increase anxiety
            ]
        },
        
        frozenset(["ADHD"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)"  # Too intense for ADHD
            ]
        },
        
        frozenset(["Insomnia"]): {
            "pranamaya_kosha": [
                "Bhastrika (Bellows Breath)"  # Too stimulating before sleep
            ]
        },
        
        # Two disease combinations
        frozenset(["Depression", "GAD"]): {
            "manomaya_kosha": [
                "Nada-Anusandhana (OM Chanting Meditation)"  # May increase rumination
            ],
            "annamaya_kosha": [
                "Vakrasana (Twisted Pose)"  # May increase anxiety in some patients
            ]
        },
        
        frozenset(["ADHD", "Depression"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)"  # Too intense during depression
            ],
            "manomaya_kosha": [
                "Nada-Anusandhana (OM Chanting Meditation)"  # May worsen rumination
            ]
        },
        
        frozenset(["GAD", "Insomnia"]): {
            "pranamaya_kosha": [
                "Bhastrika (Bellows Breath)"  # Too stimulating
            ],
            "annamaya_kosha": [
                "Vakrasana (Twisted Pose)"  # May increase anxiety
            ]
        },
        
        # Three disease combinations
        frozenset(["Depression", "GAD", "Insomnia"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)",
                "Bhastrika (Bellows Breath)"
            ],
            "manomaya_kosha": [
                "Nada-Anusandhana (OM Chanting Meditation)"
            ],
            "annamaya_kosha": [
                "Vakrasana (Twisted Pose)"
            ]
        },
        
        frozenset(["ADHD", "Depression", "GAD"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)"
            ],
            "manomaya_kosha": [
                "Nada-Anusandhana (OM Chanting Meditation)"
            ],
            "annamaya_kosha": [
                "Vakrasana (Twisted Pose)"
            ]
        },
        
        # Four disease combination
        frozenset(["Depression", "GAD", "ADHD", "Insomnia"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)",
                "Bhastrika (Bellows Breath)"
            ],
            "manomaya_kosha": [
                "Nada-Anusandhana (OM Chanting Meditation)"
            ],
            "annamaya_kosha": [
                "Vakrasana (Twisted Pose)"
            ]
        }
    }


def main():
    """
    Main function to populate disease combinations and contraindications.
    """
    print("=== Populating Disease Combinations and Contraindications ===\n")
    
    # Get database session
    session = get_session()
    
    try:
        # Step 1: Create all disease combinations
        print("Step 1: Creating disease combinations...")
        created_combinations = populate_disease_combinations(session)
        
        # Step 2: Populate contraindications
        print("\nStep 2: Populating contraindications...")
        populate_contraindications(session, created_combinations)
        
        print("\n=== Summary ===")
        total_combinations = session.query(DiseaseCombination).count()
        total_contraindications = session.query(Contraindication).count()
        
        print(f"Total disease combinations: {total_combinations}")
        print(f"Total contraindications: {total_contraindications}")
        
        # Show some examples
        print("\n=== Sample Combinations ===")
        sample_combos = session.query(DiseaseCombination).limit(5).all()
        for combo in sample_combos:
            contra_count = len(combo.contraindications)
            print(f"{combo.combination_name}: {contra_count} contraindications")
        
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
