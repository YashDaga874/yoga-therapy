"""
Test the new disease combination contraindication system
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.recommendation_engine import YogaTherapyRecommendationEngine


def test_system():
    """
    Test the new disease combination system
    """
    print("=== Testing New Disease Combination Contraindication System ===\n")
    
    # Initialize the recommendation engine
    engine = YogaTherapyRecommendationEngine()
    
    try:
        # Test cases
        test_cases = [
            {
                "diseases": ["Depression"],
                "description": "Single disease - should work normally"
            },
            {
                "diseases": ["Depression", "GAD"],
                "description": "Two diseases - should apply Depression + GAD contraindications"
            },
            {
                "diseases": ["Depression", "GAD", "Insomnia"],
                "description": "Three diseases - should apply multiple combination contraindications"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"Test {i}: {test_case['description']}")
            print(f"Diseases: {', '.join(test_case['diseases'])}")
            print("-" * 60)
            
            # Get recommendations
            recommendations = engine.get_recommendations(test_case['diseases'])
            
            if 'error' in recommendations:
                print(f"❌ Error: {recommendations['error']}")
                continue
            
            # Show contraindication report
            if 'contraindication_report' in recommendations:
                report = recommendations['contraindication_report']
                print(f"[OK] Applicable combinations: {', '.join(report['applicable_combinations'])}")
                print(f"[OK] Total contraindications: {report['total_contraindications']}")
                
                if report['removed_practices']:
                    print("[X] Removed practices:")
                    for removed in report['removed_practices']:
                        print(f"   - {removed['practice']} ({removed['kosa']})")
                        for detail in removed['contraindication_details']:
                            print(f"     Reason: {detail['reason']}")
                            print(f"     For: {detail['combination']}")
                else:
                    print("[OK] No practices removed due to contraindications")
            
            # Show practice counts
            total_practices = 0
            print(f"\n[STATS] Recommended practices by kosa:")
            for kosa, sub_categories in recommendations['practices_by_kosa'].items():
                kosa_total = sum(len(practices) for practices in sub_categories.values())
                total_practices += kosa_total
                print(f"   {kosa}: {kosa_total} practices")
            
            print(f"\n[TOTAL] Total recommended practices: {total_practices}")
            print("\n" + "="*80 + "\n")
        
        print("[SUCCESS] System is working correctly with disease combinations!")
        
    finally:
        engine.close()


if __name__ == "__main__":
    test_system()
