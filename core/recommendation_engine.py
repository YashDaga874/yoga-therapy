"""
Core Recommendation Engine for Yoga Therapy System

This module contains the logic to:
1. Fetch practices for given diseases
2. Combine practices across multiple diseases
3. Remove duplicate practices
4. Apply contraindications
5. Organize output by koshas
6. Include citations

Future: CVR logic will be added within each kosa's practice selection
"""

import sys
import os

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collections import defaultdict
from database.models import Disease, Practice, Contraindication, DiseaseCombination, Module, get_session
import json


class YogaTherapyRecommendationEngine:
    """
    The main engine that generates practice recommendations for multiple diseases
    """
    
    def __init__(self, db_path='sqlite:///yoga_therapy.db'):
        self.session = get_session(db_path)
        self.practice_segment_order = [
            'Preparatory Practice',
            'Breathing Practice',
            'Suryanamaskara',
            'Yogasana',
            'Pranayama',
            'Meditation',
            'Additional Practices',
            'Kriya (Cleansing Techniques)',
            'Yogic Counselling'
        ]
    
    def get_recommendations(self, disease_names):
        """
        Main method to get practice recommendations for a list of diseases
        
        Args:
            disease_names: List of disease names (e.g., ['Depression', 'GAD'])
            
        Returns:
            Dictionary organized by practice segments with combined practices and citations
        """
        
        # Step 1: Fetch all diseases from database
        diseases = self._fetch_diseases(disease_names)
        
        if not diseases:
            return {"error": "No diseases found in database"}
        
        # Step 2: Collect all practices for these diseases
        all_practices = self._collect_practices(diseases)
        
        # Step 3: Organize by practice segment and remove duplicates
        organized_practices = self._organize_by_segment(all_practices)
        
        # Step 4: Apply contraindications
        final_practices = self._apply_contraindications(organized_practices, diseases)
        
        # Step 5: Add module information and format output
        output = self._format_output(final_practices, diseases)
        
        # Add contraindication information if available
        if hasattr(self, '_contraindication_report'):
            output['contraindication_report'] = self._contraindication_report
        
        return output
    
    def _fetch_diseases(self, disease_names):
        """
        Fetch disease objects from database
        """
        diseases = []
        for name in disease_names:
            disease = self.session.query(Disease).filter(
                Disease.name.ilike(f'%{name}%')
            ).first()
            
            if disease:
                diseases.append(disease)
            else:
                print(f"Warning: Disease '{name}' not found in database")
        
        return diseases
    
    def _collect_practices(self, diseases):
        """
        Collect all practices associated with the given diseases
        """
        all_practices = []
        
        for disease in diseases:
            all_practices.extend(disease.practices)
        
        return all_practices
    
    def _organize_by_segment(self, practices):
        """
        Organize practices by practice segment and remove duplicates
        
        Duplicate detection is based on:
        - Matching practice_english (case-insensitive)
        - Same practice_segment and sub_category
        """
        # Dictionary structure: practice_segment -> sub_category -> list of unique practices
        organized = defaultdict(lambda: defaultdict(list))
        
        # Track what we've already added to avoid duplicates
        seen_practices = set()
        
        for practice in practices:
            # Create a unique identifier for this practice
            # We use practice_english (lowercased) + practice_segment + sub_category as the key
            practice_key = (
                practice.practice_english.lower().strip(),
                practice.practice_segment,
                practice.sub_category or ''
            )
            
            # Only add if we haven't seen this exact practice before
            if practice_key not in seen_practices:
                organized[practice.practice_segment][practice.sub_category or 'general'].append(practice)
                seen_practices.add(practice_key)
        
        return organized
    
    def _find_applicable_combinations(self, user_disease_names):
        """
        Find all disease combinations that are subsets of the user's diseases.
        
        Args:
            user_disease_names: Set of disease names the user has
            
        Returns:
            List of DiseaseCombination objects that apply to the user
        """
        # Get all disease combinations from database
        all_combinations = self.session.query(DiseaseCombination).all()
        applicable_combinations = []
        
        for combo in all_combinations:
            # Parse the diseases from JSON
            try:
                combo_diseases = set(json.loads(combo.diseases_json))
                
                # Check if this combination is a subset of user's diseases
                if combo_diseases.issubset(user_disease_names):
                    applicable_combinations.append(combo)
            except (json.JSONDecodeError, TypeError):
                # Skip malformed combinations
                continue
        
        return applicable_combinations
    
    def _apply_contraindications(self, organized_practices, diseases):
        """
        Remove practices that are contraindicated for the user's disease combination
        
        This now works with disease COMBINATIONS rather than individual diseases.
        A practice is removed if it's contraindicated for any subset of the user's diseases.
        """
        # Get user's disease names
        user_disease_names = {d.name for d in diseases}
        
        # Find all disease combinations that are subsets of user's diseases
        applicable_combinations = self._find_applicable_combinations(user_disease_names)
        
        # Collect all contraindications for these combinations
        all_contraindications = []
        contraindication_sources = []  # Track which combinations caused each contraindication
        
        for combo in applicable_combinations:
            for contraindication in combo.contraindications:
                all_contraindications.append(contraindication)
                contraindication_sources.append({
                    'contraindication': contraindication,
                    'combination': combo.combination_name
                })
        
        # Create a set of contraindicated practices for quick lookup
        contraindicated = set()
        contraindication_details = {}  # Store details about why each practice is contraindicated
        
        for source in contraindication_sources:
            contra = source['contraindication']
            combo_name = source['combination']
            
            contra_key = (
                contra.practice_english.lower().strip(),
                contra.practice_segment,
                contra.sub_category or ''
            )
            contraindicated.add(contra_key)
            
            # Store details for reporting
            if contra_key not in contraindication_details:
                contraindication_details[contra_key] = []
            contraindication_details[contra_key].append({
                'practice': contra.practice_english,
                'practice_segment': contra.practice_segment,
                'combination': combo_name,
                'reason': contra.reason
            })
        
        # Filter out contraindicated practices
        filtered_practices = defaultdict(lambda: defaultdict(list))
        removed_practices = []  # Track what was removed for reporting
        
        for segment, sub_categories in organized_practices.items():
            for sub_cat, practices in sub_categories.items():
                for practice in practices:
                    practice_key = (
                        practice.practice_english.lower().strip(),
                        practice.practice_segment,
                        practice.sub_category or ''
                    )
                    
                    # Only include if not contraindicated
                    if practice_key not in contraindicated:
                        filtered_practices[segment][sub_cat].append(practice)
                    else:
                        # Track what was removed
                        removed_practices.append({
                            'practice': practice.practice_english,
                            'practice_segment': segment,
                            'sub_category': sub_cat,
                            'contraindication_details': contraindication_details[practice_key]
                        })
        
        # Store contraindication info for reporting
        self._contraindication_report = {
            'removed_practices': removed_practices,
            'total_contraindications': len(contraindicated),
            'applicable_combinations': [combo.combination_name for combo in applicable_combinations]
        }
        
        return filtered_practices
    
    def _format_output(self, practices_by_segment, diseases):
        """
        Format the final output with proper structure and citations
        """
        output = {
            'diseases': [d.name for d in diseases],
            'modules': [],
            'practices_by_segment': {}
        }
        
        # Add module information for each disease
        for disease in diseases:
            module = self.session.query(Module).filter_by(disease_id=disease.id).first()
            if module:
                output['modules'].append({
                    'disease': disease.name,
                    'developed_by': module.developed_by,
                    'description': module.module_description
                })
        
        # Organize practices by segment in the defined order
        for segment in self.practice_segment_order:
            if segment in practices_by_segment:
                output['practices_by_segment'][segment] = {}
                
                for sub_cat, practices in practices_by_segment[segment].items():
                    formatted_practices = []
                    
                    for practice in practices:
                        practice_dict = {
                            'practice_sanskrit': practice.practice_sanskrit,
                            'practice_english': practice.practice_english,
                            'rounds': practice.rounds,
                            'time_minutes': practice.time_minutes
                        }
                        
                        # Add optional fields if they exist
                        if practice.strokes_per_min:
                            practice_dict['strokes_per_min'] = practice.strokes_per_min
                        
                        if practice.strokes_per_cycle:
                            practice_dict['strokes_per_cycle'] = practice.strokes_per_cycle
                        
                        if practice.rest_between_cycles_sec:
                            practice_dict['rest_between_cycles_sec'] = practice.rest_between_cycles_sec
                        
                        if practice.variations:
                            try:
                                practice_dict['variations'] = json.loads(practice.variations)
                            except:
                                practice_dict['variations'] = practice.variations
                        
                        if practice.steps:
                            try:
                                practice_dict['steps'] = json.loads(practice.steps)
                            except:
                                practice_dict['steps'] = practice.steps
                        
                        if practice.description:
                            practice_dict['description'] = practice.description
                        
                        # Add citation if available
                        if practice.citation:
                            practice_dict['citation'] = {
                                'text': practice.citation.citation_text,
                                'type': practice.citation.citation_type,
                                'reference': practice.citation.full_reference
                            }
                        
                        formatted_practices.append(practice_dict)
                    
                    output['practices_by_segment'][segment][sub_cat] = formatted_practices
        
        return output
    
    def get_summary(self, disease_names):
        """
        Get a text summary of recommendations (useful for RAG output)
        """
        recommendations = self.get_recommendations(disease_names)
        
        if 'error' in recommendations:
            return recommendations['error']
        
        summary = f"Yoga Therapy Recommendations for: {', '.join(recommendations['diseases'])}\n\n"
        
        # Add module information
        if recommendations['modules']:
            summary += "MODULES:\n"
            for module in recommendations['modules']:
                summary += f"- {module['disease']}: Developed by {module['developed_by']}\n"
            summary += "\n"
        
        # Add practices by segment
        summary += "RECOMMENDED PRACTICES:\n\n"
        
        for segment, sub_categories in recommendations['practices_by_segment'].items():
            summary += f"{segment.upper()}:\n"
            
            for sub_cat, practices in sub_categories.items():
                if sub_cat != 'general':
                    summary += f"  {sub_cat.replace('_', ' ').title()}:\n"
                
                for practice in practices:
                    practice_name = practice['practice_english']
                    if practice.get('practice_sanskrit'):
                        practice_name = f"{practice['practice_sanskrit']} ({practice_name})"
                    
                    summary += f"    • {practice_name}"
                    
                    # Add details
                    details = []
                    if practice.get('rounds'):
                        details.append(f"{practice['rounds']} rounds")
                    if practice.get('time_minutes'):
                        details.append(f"{practice['time_minutes']} min")
                    
                    if details:
                        summary += f" - {', '.join(details)}"
                    
                    # Add citation
                    if practice.get('citation'):
                        summary += f" [Cited: {practice['citation']['text']}]"
                    
                    summary += "\n"
                
                summary += "\n"
        
        return summary
    
    def close(self):
        """Close database session"""
        self.session.close()


# Convenience function for quick usage
def get_recommendations_for_diseases(disease_names, db_path='sqlite:///yoga_therapy.db'):
    """
    Quick function to get recommendations
    
    Usage:
        recommendations = get_recommendations_for_diseases(['Depression', 'GAD'])
    """
    engine = YogaTherapyRecommendationEngine(db_path)
    try:
        return engine.get_recommendations(disease_names)
    finally:
        engine.close()


def get_summary_for_diseases(disease_names, db_path='sqlite:///yoga_therapy.db'):
    """
    Quick function to get text summary
    
    Usage:
        summary = get_summary_for_diseases(['Depression', 'GAD'])
        print(summary)
    """
    engine = YogaTherapyRecommendationEngine(db_path)
    try:
        return engine.get_summary(disease_names)
    finally:
        engine.close()