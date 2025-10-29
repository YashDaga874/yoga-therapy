"""
Simple test script to get yoga recommendations for Depression + GAD
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.recommendation_engine import get_summary_for_diseases, get_recommendations_for_diseases

def test_depression_gad():
    """
    Test getting recommendations for Depression + GAD
    """
    print("=" * 80)
    print("YOGA THERAPY RECOMMENDATIONS FOR DEPRESSION + GAD")
    print("=" * 80)
    
    # Test with Depression + GAD
    diseases = ['Depression', 'GAD']
    
    print(f"\nTesting recommendations for: {', '.join(diseases)}")
    print("-" * 60)
    
    # Get detailed recommendations (JSON format)
    print("\n1. DETAILED RECOMMENDATIONS (JSON format):")
    print("-" * 40)
    recommendations = get_recommendations_for_diseases(diseases)
    
    if 'error' in recommendations:
        print(f"❌ Error: {recommendations['error']}")
        return
    
    # Show contraindication report if available
    if 'contraindication_report' in recommendations:
        report = recommendations['contraindication_report']
        print(f"\n📊 CONTRAINDICATION REPORT:")
        print(f"   Applicable combinations: {', '.join(report['applicable_combinations'])}")
        print(f"   Total contraindications: {report['total_contraindications']}")
        
        if report['removed_practices']:
            print(f"\n❌ REMOVED PRACTICES ({len(report['removed_practices'])} total):")
            for removed in report['removed_practices']:
                print(f"   • {removed['practice']} ({removed['kosa']})")
                for detail in removed['contraindication_details']:
                    print(f"     Reason: {detail['reason']}")
                    print(f"     For combination: {detail['combination']}")
        else:
            print("\n✅ No practices removed due to contraindications")
    
    # Show practice counts by kosa
    print(f"\n📈 PRACTICE COUNTS BY KOSA:")
    total_practices = 0
    for kosa, sub_categories in recommendations['practices_by_kosa'].items():
        kosa_total = sum(len(practices) for practices in sub_categories.values())
        total_practices += kosa_total
        print(f"   {kosa.replace('_', ' ').title()}: {kosa_total} practices")
    
    print(f"\n🎯 TOTAL RECOMMENDED PRACTICES: {total_practices}")
    
    # Get text summary (human-readable format)
    print("\n\n2. HUMAN-READABLE SUMMARY:")
    print("-" * 40)
    summary = get_summary_for_diseases(diseases)
    print(summary)
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)

if __name__ == "__main__":
    test_depression_gad()
