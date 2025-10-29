"""
Disease Combinations Generator for Yoga Therapy System

This module generates all possible combinations of diseases for contraindication analysis.
The idea is that contraindications apply to specific COMBINATIONS of diseases, not individual diseases.

For example:
- A practice might be fine for "depression" alone
- But contraindicated for "depression + GAD" combination
- Or contraindicated for "depression + GAD + insomnia" combination

This module provides utilities to:
1. Generate all possible disease combinations
2. Check if a given set of diseases matches any contraindication combinations
3. Create a mapping structure for contraindications by disease combinations
"""

from itertools import combinations
from typing import List, Set, Dict, FrozenSet


def generate_disease_combinations(disease_names: List[str]) -> Dict[int, List[FrozenSet[str]]]:
    """
    Generate all possible combinations of diseases.
    
    Args:
        disease_names: List of disease names (e.g., ['Depression', 'GAD', 'ADHD', 'Insomnia'])
    
    Returns:
        Dictionary mapping combination size to list of frozen sets
        {
            1: [frozenset(['Depression']), frozenset(['GAD']), ...],
            2: [frozenset(['Depression', 'GAD']), frozenset(['Depression', 'ADHD']), ...],
            3: [frozenset(['Depression', 'GAD', 'ADHD']), ...],
            4: [frozenset(['Depression', 'GAD', 'ADHD', 'Insomnia'])]
        }
    """
    combinations_dict = {}
    
    # Generate combinations of size 1 to len(disease_names)
    for r in range(1, len(disease_names) + 1):
        combo_list = []
        for combo in combinations(disease_names, r):
            combo_list.append(frozenset(combo))
        combinations_dict[r] = combo_list
    
    return combinations_dict


def get_all_combinations(disease_names: List[str]) -> List[FrozenSet[str]]:
    """
    Get all possible combinations as a flat list.
    
    Args:
        disease_names: List of disease names
    
    Returns:
        List of all possible frozen sets of disease combinations
    """
    all_combos = []
    for r in range(1, len(disease_names) + 1):
        for combo in combinations(disease_names, r):
            all_combos.append(frozenset(combo))
    return all_combos


def find_matching_combinations(user_diseases: Set[str], all_combinations: List[FrozenSet[str]]) -> List[FrozenSet[str]]:
    """
    Find which disease combinations match the user's diseases.
    
    Args:
        user_diseases: Set of diseases the user has
        all_combinations: List of all possible disease combinations
    
    Returns:
        List of combinations that are subsets of user_diseases
    """
    user_diseases_frozen = frozenset(user_diseases)
    matching_combos = []
    
    for combo in all_combinations:
        # Check if this combination is a subset of user's diseases
        if combo.issubset(user_diseases_frozen):
            matching_combos.append(combo)
    
    return matching_combos


def create_contraindication_structure() -> Dict[FrozenSet[str], Dict[str, List[str]]]:
    """
    Create the new contraindication structure based on disease combinations.
    
    This is an example structure showing how contraindications would work:
    - Each key is a frozenset of diseases (combination)
    - Each value is a dictionary mapping kosa to list of contraindicated practices
    
    Returns:
        Dictionary structure for contraindications by disease combinations
    """
    contraindications = {
        # Single disease contraindications
        frozenset(["depression"]): {
            "manomaya_kosha": ["Nada-Anusandhana (OM Chanting Meditation)"],  # May increase rumination
        },
        
        frozenset(["GAD"]): {
            "annamaya_kosha": ["Vakrasana (Twisted Pose)"]  # May increase anxiety
        },
        
        # Two disease combinations
        frozenset(["depression", "GAD"]): {
            "manomaya_kosha": ["Nada-Anusandhana (OM Chanting Meditation)"],  # May increase rumination
            "annamaya_kosha": ["Vakrasana (Twisted Pose)"]  # May increase anxiety in some patients
        },
        
        frozenset(["ADHD", "substance_use"]): {
            "pranamaya_kosha": ["Kapalabhati (Skull Shining Breath)"]  # Too intense during recovery
        },
        
        # Three disease combinations
        frozenset(["depression", "GAD", "insomnia"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)",
                "Bhastrika (Bellows Breath)"
            ],
            "manomaya_kosha": ["Nada-Anusandhana (OM Chanting Meditation)"]
        },
        
        # Four disease combinations (if you have 4 diseases)
        frozenset(["depression", "GAD", "ADHD", "insomnia"]): {
            "pranamaya_kosha": [
                "Kapalabhati (Skull Shining Breath)",
                "Bhastrika (Bellows Breath)"
            ],
            "manomaya_kosha": ["Nada-Anusandhana (OM Chanting Meditation)"],
            "annamaya_kosha": ["Vakrasana (Twisted Pose)"]
        }
    }
    
    return contraindications


def get_contraindications_for_user_diseases(user_diseases: Set[str], contraindication_structure: Dict[FrozenSet[str], Dict[str, List[str]]]) -> Dict[str, List[str]]:
    """
    Get all contraindications that apply to the user's disease combination.
    
    Args:
        user_diseases: Set of diseases the user has
        contraindication_structure: The contraindication structure
    
    Returns:
        Dictionary mapping kosa to list of contraindicated practices
    """
    user_diseases_frozen = frozenset(user_diseases)
    applicable_contraindications = {}
    
    # Find all combinations that are subsets of user's diseases
    for disease_combo, contraindications in contraindication_structure.items():
        if disease_combo.issubset(user_diseases_frozen):
            # Merge contraindications for this combination
            for kosa, practices in contraindications.items():
                if kosa not in applicable_contraindications:
                    applicable_contraindications[kosa] = []
                applicable_contraindications[kosa].extend(practices)
    
    # Remove duplicates while preserving order
    for kosa in applicable_contraindications:
        seen = set()
        unique_practices = []
        for practice in applicable_contraindications[kosa]:
            if practice not in seen:
                seen.add(practice)
                unique_practices.append(practice)
        applicable_contraindications[kosa] = unique_practices
    
    return applicable_contraindications


def print_combination_analysis(disease_names: List[str]):
    """
    Print a comprehensive analysis of all possible disease combinations.
    
    Args:
        disease_names: List of disease names to analyze
    """
    print(f"=== Disease Combination Analysis for: {', '.join(disease_names)} ===\n")
    
    combinations_dict = generate_disease_combinations(disease_names)
    
    total_combinations = 0
    for size, combos in combinations_dict.items():
        print(f"Combinations of {size} disease(s): {len(combos)}")
        for combo in combos:
            print(f"  - {', '.join(sorted(combo))}")
        print()
        total_combinations += len(combos)
    
    print(f"Total possible combinations: {total_combinations}")
    print(f"Formula: 2^{len(disease_names)} - 1 = {2**len(disease_names) - 1}")


# Example usage and testing
if __name__ == "__main__":
    # Example with 4 diseases
    diseases = ["Depression", "GAD", "ADHD", "Insomnia"]
    
    print_combination_analysis(diseases)
    
    # Test contraindication structure
    contraindication_structure = create_contraindication_structure()
    
    # Test with different user disease combinations
    test_cases = [
        {"Depression"},
        {"Depression", "GAD"},
        {"Depression", "GAD", "Insomnia"},
        {"Depression", "GAD", "ADHD", "Insomnia"}
    ]
    
    print("\n=== Contraindication Analysis ===")
    for user_diseases in test_cases:
        print(f"\nUser has: {', '.join(sorted(user_diseases))}")
        contraindications = get_contraindications_for_user_diseases(user_diseases, contraindication_structure)
        
        if contraindications:
            print("Contraindicated practices:")
            for kosa, practices in contraindications.items():
                print(f"  {kosa}: {', '.join(practices)}")
        else:
            print("  No contraindications found")
