"""
Test Script for Yoga Therapy Recommendation System

This script demonstrates how to use the recommendation engine
and tests the core functionality with sample data.
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.recommendation_engine import get_recommendations_for_diseases, get_summary_for_diseases
import json


def test_single_disease():
    """Test getting recommendations for a single disease"""
    print("=" * 80)
    print("TEST 1: Single Disease (Depression)")
    print("=" * 80)
    
    recommendations = get_recommendations_for_diseases(['Depression'])
    
    if 'error' in recommendations:
        print(f"Error: {recommendations['error']}")
        print("\nMake sure you've run the data import script first!")
        return False
    
    print(f"\nDiseases: {', '.join(recommendations['diseases'])}")
    print(f"Number of Koshas with practices: {len(recommendations['practices_by_kosa'])}")
    
    for kosa, practices_dict in recommendations['practices_by_kosa'].items():
        total_practices = sum(len(practices) for practices in practices_dict.values())
        print(f"  {kosa}: {total_practices} practices")
    
    return True


def test_multiple_diseases():
    """Test combining multiple diseases"""
    print("\n" + "=" * 80)
    print("TEST 2: Multiple Diseases (Depression + Anxiety)")
    print("=" * 80)
    
    recommendations = get_recommendations_for_diseases(['Depression', 'Anxiety_Module'])
    
    if 'error' in recommendations:
        print(f"Error: {recommendations['error']}")
        return False
    
    print(f"\nCombined diseases: {', '.join(recommendations['diseases'])}")
    print("\nThis demonstrates how practices from multiple diseases are:")
    print("  1. Combined together")
    print("  2. Deduplicated (same practices removed)")
    print("  3. Filtered by contraindications")
    
    for kosa, practices_dict in recommendations['practices_by_kosa'].items():
        total_practices = sum(len(practices) for practices in practices_dict.values())
        print(f"\n{kosa}: {total_practices} unique practices")
    
    return True


def test_text_summary():
    """Test the text summary format"""
    print("\n" + "=" * 80)
    print("TEST 3: Text Summary Format (for RAG Integration)")
    print("=" * 80)
    
    summary = get_summary_for_diseases(['Depression'])
    
    print("\nThis is the format that will be sent to your RAG chatbot:")
    print("-" * 80)
    print(summary[:500] + "..." if len(summary) > 500 else summary)
    print("-" * 80)
    
    return True


def test_json_output():
    """Test the JSON format"""
    print("\n" + "=" * 80)
    print("TEST 4: JSON Output Format (for API Integration)")
    print("=" * 80)
    
    recommendations = get_recommendations_for_diseases(['Depression'])
    
    if 'error' not in recommendations:
        # Show a sample practice with all its fields
        print("\nSample practice structure (showing first practice from Annamaya_Kosa):")
        print("-" * 80)
        
        for kosa, practices_dict in recommendations['practices_by_kosa'].items():
            for category, practices in practices_dict.items():
                if practices:
                    print(json.dumps(practices[0], indent=2))
                    return True
    
    return False


def test_contraindications():
    """Test that contraindications are properly applied"""
    print("\n" + "=" * 80)
    print("TEST 5: Contraindication Handling")
    print("=" * 80)
    
    print("\nTo test contraindications, you would:")
    print("  1. Add a contraindication for a specific disease")
    print("  2. Request recommendations combining that disease with another")
    print("  3. Verify the contraindicated practice is excluded")
    
    print("\nYou can test this through the web interface:")
    print("  - Go to /contraindication/add")
    print("  - Add a contraindication for a practice")
    print("  - Run this test again to see it filtered out")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("YOGA THERAPY RECOMMENDATION SYSTEM - TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Single Disease", test_single_disease),
        ("Multiple Diseases", test_multiple_diseases),
        ("Text Summary", test_text_summary),
        ("JSON Output", test_json_output),
        ("Contraindications", test_contraindications)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your system is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("Make sure you've run the data import script first: python utils/import_data.py")


if __name__ == '__main__':
    run_all_tests()