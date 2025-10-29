"""
Test the new disease combination contraindication system

This script tests the updated recommendation engine with disease combinations.
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.recommendation_engine import YogaTherapyRecommendationEngine
from database.models import get_session, Disease, DiseaseCombination, Contraindication
import json


def test_disease_combinations():
    """
    Test the new disease combination system
    """
    print("=== Testing Disease Combination Contraindication System ===\n")
    
    # Initialize the recommendation engine
    engine = YogaTherapyRecommendationEngine()
    
    try:
        # Test with different disease combinations
        test_cases = [
            ["Depression"],
            ["Depression", "GAD"],
            ["Depression", "GAD", "Insomnia"],
            ["ADHD", "Depression"],
            ["ADHD", "Depression", "GAD", "Insomnia"]
        ]
        
        for diseases in test_cases:
            print(f"Testing with diseases: {', '.join(diseases)}")
            print("-" * 50)
            
            # Get recommendations
            recommendations = engine.get_recommendations(diseases)
            
            if 'error' in recommendations:
                print(f"Error: {recommendations['error']}")
                continue
            
            # Print basic info
            print(f"Diseases: {', '.join(recommendations['diseases'])}")
            
            # Print contraindication report if available
            if 'contraindication_report' in recommendations:
                report = recommendations['contraindication_report']
                print(f"Applicable disease combinations: {', '.join(report['applicable_combinations'])}")
                print(f"Total contraindications applied: {report['total_contraindications']}")
                
                if report['removed_practices']:
                    print("Removed practices due to contraindications:")
                    for removed in report['removed_practices']:
                        print(f"  - {removed['practice']} ({removed['kosa']})")
                        for detail in removed['contraindication_details']:
                            print(f"    Reason: {detail['reason']} (for {detail['combination']})")
                else:
                    print("No practices removed due to contraindications")
            
            # Count total practices by kosa
            total_practices = 0
            for kosa, sub_categories in recommendations['practices_by_kosa'].items():
                kosa_total = sum(len(practices) for practices in sub_categories.values())
                total_practices += kosa_total
                print(f"{kosa}: {kosa_total} practices")
            
            print(f"Total recommended practices: {total_practices}")
            print()
        
    finally:
        engine.close()


def check_database_structure():
    """
    Check the database structure for disease combinations
    """
    print("=== Checking Database Structure ===\n")
    
    session = get_session()
    
    try:
        # Check diseases
        diseases = session.query(Disease).all()
        print(f"Total diseases: {len(diseases)}")
        for disease in diseases:
            print(f"  - {disease.name}")
        
        # Check disease combinations
        combinations = session.query(DiseaseCombination).all()
        print(f"\nTotal disease combinations: {len(combinations)}")
        for combo in combinations[:10]:  # Show first 10
            print(f"  - {combo.combination_name}")
            contra_count = len(combo.contraindications)
            print(f"    Contraindications: {contra_count}")
        
        if len(combinations) > 10:
            print(f"  ... and {len(combinations) - 10} more")
        
        # Check contraindications
        contraindications = session.query(Contraindication).all()
        print(f"\nTotal contraindications: {len(contraindications)}")
        for contra in contraindications[:5]:  # Show first 5
            print(f"  - {contra.practice_english} ({contra.kosa})")
            combo_names = [combo.combination_name for combo in contra.disease_combinations]
            print(f"    Applies to: {', '.join(combo_names)}")
        
        if len(contraindications) > 5:
            print(f"  ... and {len(contraindications) - 5} more")
        
    finally:
        session.close()


def main():
    """
    Main test function
    """
    print("Testing the new disease combination contraindication system...\n")
    
    # First check database structure
    check_database_structure()
    print("\n" + "="*60 + "\n")
    
    # Then test the recommendation engine
    test_disease_combinations()


if __name__ == "__main__":
    main()
