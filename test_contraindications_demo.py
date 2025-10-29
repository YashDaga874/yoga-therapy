"""
Demo script to show the disease combination contraindication system in action
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.recommendation_engine import YogaTherapyRecommendationEngine
from database.models import get_session, Disease, DiseaseCombination, Contraindication
import json


def add_demo_contraindications():
    """
    Add some demo contraindications to show the system working
    """
    session = get_session()
    
    try:
        # Get some disease combinations
        depression_gad = session.query(DiseaseCombination).filter_by(
            combination_name="Depression + GAD"
        ).first()
        
        gad_insomnia = session.query(DiseaseCombination).filter_by(
            combination_name="GAD + Insomnia"
        ).first()
        
        all_four = session.query(DiseaseCombination).filter_by(
            combination_name="ADHD + Depression + GAD + Insomnia"
        ).first()
        
        if depression_gad:
            # Add contraindication for Depression + GAD
            contra1 = Contraindication(
                practice_english="Vakrasana (Twisted Pose)",
                practice_sanskrit="Vakrasana",
                kosa="Annamaya_Kosa",
                sub_category="twisted_pose",
                reason="May increase anxiety in patients with both Depression and GAD"
            )
            session.add(contra1)
            depression_gad.contraindications.append(contra1)
            
            # Add another contraindication
            contra2 = Contraindication(
                practice_english="Kapalabhati (Skull Shining Breath)",
                practice_sanskrit="Kapalabhati",
                kosa="Pranamaya_Kosa",
                sub_category="breathing_exercise",
                reason="Too intense for patients with both Depression and GAD"
            )
            session.add(contra2)
            depression_gad.contraindications.append(contra2)
        
        if gad_insomnia:
            # Add contraindication for GAD + Insomnia
            contra3 = Contraindication(
                practice_english="Bhastrika (Bellows Breath)",
                practice_sanskrit="Bhastrika",
                kosa="Pranamaya_Kosa",
                sub_category="breathing_exercise",
                reason="Too stimulating for patients with GAD and Insomnia"
            )
            session.add(contra3)
            gad_insomnia.contraindications.append(contra3)
        
        if all_four:
            # Add contraindication for all four diseases
            contra4 = Contraindication(
                practice_english="Nada-Anusandhana (OM Chanting Meditation)",
                practice_sanskrit="Nada-Anusandhana",
                kosa="Manomaya_Kosa",
                sub_category="meditation",
                reason="May worsen symptoms when all four conditions are present"
            )
            session.add(contra4)
            all_four.contraindications.append(contra4)
        
        session.commit()
        print("Added demo contraindications")
        
    except Exception as e:
        print(f"Error adding contraindications: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def demo_contraindication_system():
    """
    Demonstrate the contraindication system with different disease combinations
    """
    print("=== Disease Combination Contraindication Demo ===\n")
    
    # Initialize the recommendation engine
    engine = YogaTherapyRecommendationEngine()
    
    try:
        # Test cases showing how contraindications work
        test_cases = [
            {
                "diseases": ["Depression"],
                "description": "Single disease - no contraindications expected"
            },
            {
                "diseases": ["GAD"],
                "description": "Single disease - no contraindications expected"
            },
            {
                "diseases": ["Depression", "GAD"],
                "description": "Two diseases - should trigger Depression + GAD contraindications"
            },
            {
                "diseases": ["GAD", "Insomnia"],
                "description": "Two diseases - should trigger GAD + Insomnia contraindications"
            },
            {
                "diseases": ["ADHD", "Depression", "GAD", "Insomnia"],
                "description": "Four diseases - should trigger all applicable contraindications"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test Case {i}: {test_case['description']}")
            print(f"Diseases: {', '.join(test_case['diseases'])}")
            print("-" * 60)
            
            # Get recommendations
            recommendations = engine.get_recommendations(test_case['diseases'])
            
            if 'error' in recommendations:
                print(f"Error: {recommendations['error']}")
                continue
            
            # Show contraindication report
            if 'contraindication_report' in recommendations:
                report = recommendations['contraindication_report']
                print(f"Applicable combinations: {', '.join(report['applicable_combinations'])}")
                print(f"Total contraindications: {report['total_contraindications']}")
                
                if report['removed_practices']:
                    print("\nRemoved practices:")
                    for removed in report['removed_practices']:
                        print(f"  [X] {removed['practice']} ({removed['kosa']})")
                        for detail in removed['contraindication_details']:
                            print(f"     Reason: {detail['reason']}")
                            print(f"     For combination: {detail['combination']}")
                else:
                    print("[OK] No practices removed due to contraindications")
            
            # Show practice counts
            total_practices = 0
            print(f"\nRecommended practices by kosa:")
            for kosa, sub_categories in recommendations['practices_by_kosa'].items():
                kosa_total = sum(len(practices) for practices in sub_categories.values())
                total_practices += kosa_total
                print(f"  {kosa}: {kosa_total} practices")
            
            print(f"\nTotal recommended practices: {total_practices}")
            print("\n" + "="*80 + "\n")
        
    finally:
        engine.close()


def show_database_stats():
    """
    Show current database statistics
    """
    print("=== Database Statistics ===\n")
    
    session = get_session()
    
    try:
        # Count diseases
        diseases = session.query(Disease).all()
        print(f"Total diseases: {len(diseases)}")
        for disease in diseases:
            print(f"  - {disease.name}")
        
        # Count combinations
        combinations = session.query(DiseaseCombination).all()
        print(f"\nTotal disease combinations: {len(combinations)}")
        
        # Show combinations with contraindications
        combinations_with_contra = [c for c in combinations if c.contraindications]
        print(f"Combinations with contraindications: {len(combinations_with_contra)}")
        
        for combo in combinations_with_contra:
            print(f"\n{combo.combination_name}:")
            for contra in combo.contraindications:
                print(f"  [X] {contra.practice_english} ({contra.kosa}) - {contra.reason}")
        
        # Count total contraindications
        contraindications = session.query(Contraindication).all()
        print(f"\nTotal contraindications: {len(contraindications)}")
        
    finally:
        session.close()


def main():
    """
    Main demo function
    """
    print("Setting up demo contraindications...")
    add_demo_contraindications()
    
    print("\n" + "="*80 + "\n")
    show_database_stats()
    
    print("\n" + "="*80 + "\n")
    demo_contraindication_system()


if __name__ == "__main__":
    main()
