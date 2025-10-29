"""
Interactive Disease Recommendation Tester

This script lets you test yoga recommendations for any combination of diseases.
Just run it and follow the prompts!
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.recommendation_engine import get_summary_for_diseases, get_recommendations_for_diseases

def show_available_diseases():
    """Show what diseases are available in the database"""
    from database.models import Disease, get_session
    
    session = get_session()
    diseases = session.query(Disease).all()
    session.close()
    
    print("\n📋 AVAILABLE DISEASES IN DATABASE:")
    print("-" * 50)
    for i, disease in enumerate(diseases, 1):
        print(f"{i:2d}. {disease.name}")
    print("-" * 50)
    return [d.name for d in diseases]

def interactive_recommendations():
    """Interactive mode for testing disease combinations"""
    print("=" * 80)
    print("🧘‍♀️  YOGA THERAPY RECOMMENDATION TESTER")
    print("=" * 80)
    
    # Show available diseases
    available_diseases = show_available_diseases()
    
    while True:
        print("\n" + "=" * 60)
        print("OPTIONS:")
        print("1. Enter disease names manually")
        print("2. Choose from available diseases")
        print("3. Quick test: Depression + GAD")
        print("4. Quick test: Depression + GAD + ADHD")
        print("5. Exit")
        print("=" * 60)
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            # Manual entry
            print("\nEnter disease names (comma-separated):")
            print("Example: Depression, GAD, ADHD")
            disease_input = input("Diseases: ").strip()
            
            if not disease_input:
                print("❌ No diseases entered!")
                continue
                
            diseases = [d.strip() for d in disease_input.split(',')]
            
        elif choice == '2':
            # Choose from list
            print("\nEnter numbers of diseases you want (comma-separated):")
            print("Example: 1,3,5")
            numbers_input = input("Numbers: ").strip()
            
            if not numbers_input:
                print("❌ No numbers entered!")
                continue
                
            try:
                numbers = [int(n.strip()) for n in numbers_input.split(',')]
                diseases = []
                for num in numbers:
                    if 1 <= num <= len(available_diseases):
                        diseases.append(available_diseases[num-1])
                    else:
                        print(f"❌ Invalid number: {num}")
                        break
                else:
                    if not diseases:
                        print("❌ No valid diseases selected!")
                        continue
            except ValueError:
                print("❌ Invalid input! Please enter numbers only.")
                continue
                
        elif choice == '3':
            diseases = ['Depression', 'GAD']
            
        elif choice == '4':
            diseases = ['Depression', 'GAD', 'ADHD']
            
        elif choice == '5':
            print("\n👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice! Please enter 1-5.")
            continue
        
        # Get recommendations
        print(f"\n🔍 Getting recommendations for: {', '.join(diseases)}")
        print("-" * 60)
        
        try:
            # Get detailed recommendations first
            recommendations = get_recommendations_for_diseases(diseases)
            
            if 'error' in recommendations:
                print(f"❌ Error: {recommendations['error']}")
                continue
            
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
            
            # Ask if user wants to see full summary
            show_summary = input("\n📖 Show full practice summary? (y/n): ").strip().lower()
            
            if show_summary in ['y', 'yes']:
                print("\n" + "=" * 60)
                print("FULL PRACTICE SUMMARY:")
                print("=" * 60)
                summary = get_summary_for_diseases(diseases)
                print(summary)
            
        except Exception as e:
            print(f"❌ Error getting recommendations: {e}")
            continue
        
        # Ask if user wants to continue
        continue_testing = input("\n🔄 Test another combination? (y/n): ").strip().lower()
        if continue_testing not in ['y', 'yes']:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    interactive_recommendations()
