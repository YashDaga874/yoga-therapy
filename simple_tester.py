"""
Simple Command-Line Disease Tester

Usage examples:
    python simple_tester.py Depression GAD
    python simple_tester.py Depression GAD ADHD
    python simple_tester.py "Generalized Anxiety Disorder" Depression
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.recommendation_engine import get_summary_for_diseases, get_recommendations_for_diseases

def main():
    if len(sys.argv) < 2:
        print("""
🧘‍♀️  YOGA THERAPY RECOMMENDATION TESTER

Usage:
    python simple_tester.py Disease1 Disease2 Disease3 ...
    
Examples:
    python simple_tester.py Depression GAD
    python simple_tester.py Depression GAD ADHD
    python simple_tester.py "Generalized Anxiety Disorder" Depression

Available diseases in database:
""")
        
        # Show available diseases
        from database.models import Disease, get_session
        session = get_session()
        diseases = session.query(Disease).all()
        session.close()
        
        for i, disease in enumerate(diseases, 1):
            print(f"  {i:2d}. {disease.name}")
        
        print("\nJust run: python simple_tester.py DiseaseName1 DiseaseName2")
        return
    
    # Get diseases from command line arguments
    diseases = sys.argv[1:]
    
    print("=" * 80)
    print(f"🧘‍♀️  YOGA THERAPY RECOMMENDATIONS FOR: {', '.join(diseases)}")
    print("=" * 80)
    
    try:
        # Get recommendations
        recommendations = get_recommendations_for_diseases(diseases)
        
        if 'error' in recommendations:
            print(f"❌ Error: {recommendations['error']}")
            return
        
        # Show contraindication report
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
        
        # Show practice counts
        print(f"\n📈 PRACTICE COUNTS BY KOSA:")
        total_practices = 0
        for kosa, sub_categories in recommendations['practices_by_kosa'].items():
            kosa_total = sum(len(practices) for practices in sub_categories.values())
            total_practices += kosa_total
            print(f"   {kosa.replace('_', ' ').title()}: {kosa_total} practices")
        
        print(f"\n🎯 TOTAL RECOMMENDED PRACTICES: {total_practices}")
        
        # Show full summary
        print("\n" + "=" * 60)
        print("FULL PRACTICE SUMMARY:")
        print("=" * 60)
        summary = get_summary_for_diseases(diseases)
        print(summary)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
