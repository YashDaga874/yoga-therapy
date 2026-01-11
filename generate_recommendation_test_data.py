"""
Generate Synthetic Test Data for Recommendation System Edge Cases

This script creates test data specifically designed to test various edge cases
in the recommendation system, including:
- Different practice counts per module (7 major, 3 comorbid as example)
- Various proportions and splits
- Edge cases for practice selection
- Different RCT counts and CVR scores
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import (
    Disease, Module, Practice, Citation, Contraindication,
    create_database
)

def get_db_session():
    """Get database session"""
    from database.models import get_session
    return get_session()

def generate_recommendation_test_data():
    """Generate test data for recommendation system edge cases"""
    session = get_db_session()
    
    try:
        print("Generating recommendation system test data...")
        
        # 1. Create test diseases
        diseases_data = [
            {'name': 'Depression', 'description': 'Mood disorder for testing recommendation system'},
            {'name': 'GAD', 'description': 'Generalized Anxiety Disorder for testing'},
            {'name': 'Test Disease A', 'description': 'Test disease with 7 practices'},
            {'name': 'Test Disease B', 'description': 'Test disease with 3 practices'},
            {'name': 'Test Disease C', 'description': 'Test disease with 10 practices'},
            {'name': 'Test Disease D', 'description': 'Test disease with 2 practices'},
        ]
        
        diseases = {}
        for d_data in diseases_data:
            disease = session.query(Disease).filter_by(name=d_data['name']).first()
            if not disease:
                disease = Disease(name=d_data['name'], description=d_data['description'])
                session.add(disease)
                session.flush()
            diseases[d_data['name']] = disease
        
        # 2. Create citations
        citations_data = [
            {
                'citation_text': 'Dr Hemant Bhargav, 2013',
                'citation_type': 'research_paper',
                'full_reference': 'Bhargav, H. (2013). Yoga therapy for depression: A clinical study.',
                'url': 'https://example.com/bhargav2013'
            },
            {
                'citation_text': 'Dr Naveen GH et al., 2019',
                'citation_type': 'research_paper',
                'full_reference': 'Naveen, G.H., et al. (2019). Yoga therapy for GAD: Randomized controlled trial.',
                'url': 'https://example.com/naveen2019'
            },
            {
                'citation_text': 'Test Citation 1',
                'citation_type': 'research_paper',
                'full_reference': 'Test Citation 1 Reference',
                'url': None
            },
        ]
        
        citations = {}
        for c_data in citations_data:
            citation = session.query(Citation).filter_by(citation_text=c_data['citation_text']).first()
            if not citation:
                citation = Citation(**c_data)
                session.add(citation)
                session.flush()
            citations[c_data['citation_text']] = citation
        
        # 3. Create modules with specific practice counts for testing
        modules_data = [
            # Depression module with 7 practices (like user's example)
            {
                'disease': 'Depression',
                'developed_by': 'Dr Hemant Bhargav, 2013',
                'paper_link': 'https://example.com/bhargav2013',
                'module_description': 'Depression module with 7 practices for testing'
            },
            # GAD module with 3 practices (like user's example)
            {
                'disease': 'GAD',
                'developed_by': 'Dr Naveen GH et al., 2019',
                'paper_link': 'https://example.com/naveen2019',
                'module_description': 'GAD module with 3 practices for testing'
            },
            # Additional test modules
            {
                'disease': 'Test Disease A',
                'developed_by': 'Test Citation 1',
                'paper_link': None,
                'module_description': 'Test module with 7 practices'
            },
            {
                'disease': 'Test Disease B',
                'developed_by': 'Test Citation 1',
                'paper_link': None,
                'module_description': 'Test module with 3 practices'
            },
            {
                'disease': 'Test Disease C',
                'developed_by': 'Test Citation 1',
                'paper_link': None,
                'module_description': 'Test module with 10 practices'
            },
            {
                'disease': 'Test Disease D',
                'developed_by': 'Test Citation 1',
                'paper_link': None,
                'module_description': 'Test module with 2 practices'
            },
        ]
        
        modules = {}
        for m_data in modules_data:
            # Check if module already exists
            existing = session.query(Module).filter_by(
                disease_id=diseases[m_data['disease']].id,
                developed_by=m_data['developed_by']
            ).first()
            if not existing:
                module = Module(
                    disease_id=diseases[m_data['disease']].id,
                    developed_by=m_data['developed_by'],
                    paper_link=m_data.get('paper_link'),
                    module_description=m_data.get('module_description')
                )
                session.add(module)
                session.flush()
                modules[f"{m_data['disease']}_{m_data['developed_by']}"] = module
            else:
                modules[f"{m_data['disease']}_{m_data['developed_by']}"] = existing
        
        # 4. Create practices - Depression module: 7 practices
        depression_practices = [
            {'english': 'Shavasana', 'sanskrit': 'Shavasana', 'segment': 'Yogasana', 'subcat': 'Relaxation in corpse pose', 'kosha': 'Annamaya Kosha', 'rct': 3, 'cvr': 8.5},
            {'english': 'Anulom Vilom', 'sanskrit': 'Anulom Vilom', 'segment': 'Pranayama', 'subcat': 'Balancing breath', 'kosha': 'Pranamaya Kosha', 'rct': 5, 'cvr': 9.0},
            {'english': 'Bhramari', 'sanskrit': 'Bhramari', 'segment': 'Pranayama', 'subcat': 'Bee breath', 'kosha': 'Pranamaya Kosha', 'rct': 4, 'cvr': 8.0},
            {'english': 'Yoga Nidra', 'sanskrit': 'Yoga Nidra', 'segment': 'Yogic Counselling', 'subcat': 'Relaxation in corpse pose/Yoga nidra', 'kosha': 'Manomaya Kosha', 'rct': 6, 'cvr': 7.5},
            {'english': 'Om Chanting', 'sanskrit': 'Om', 'segment': 'Meditation', 'subcat': 'Mantra meditation', 'kosha': 'Manomaya Kosha', 'rct': 2, 'cvr': 7.0},
            {'english': 'Dhyana', 'sanskrit': 'Dhyana', 'segment': 'Meditation', 'subcat': 'Mindfulness meditation', 'kosha': 'Vijnanamaya Kosha', 'rct': 1, 'cvr': 6.5},
            {'english': 'Satsang', 'sanskrit': 'Satsang', 'segment': 'Yogic Counselling', 'subcat': 'Group therapy', 'kosha': 'Anandamaya Kosha', 'rct': 0, 'cvr': 5.5},
        ]
        
        # GAD module: 3 practices
        gad_practices = [
            {'english': 'Shavasana (with chanting of A)', 'sanskrit': 'Shavasana', 'segment': 'Yogasana', 'subcat': 'Relaxation in corpse pose', 'kosha': 'Annamaya Kosha', 'rct': 1, 'cvr': 8.0},
            {'english': 'Pratyahara', 'sanskrit': 'Pratyahara', 'segment': 'Meditation', 'subcat': 'Withdrawal of senses', 'kosha': 'Vijnanamaya Kosha', 'rct': 0, 'cvr': 7.5},
            {'english': 'Samadhi', 'sanskrit': 'Samadhi', 'segment': 'Yogic Counselling', 'subcat': 'Transcendental state', 'kosha': 'Anandamaya Kosha', 'rct': 0, 'cvr': 6.0},
        ]
        
        # Test Disease A: 7 practices (various RCT counts)
        test_a_practices = [
            {'english': 'Practice A1', 'sanskrit': None, 'segment': 'Preparatory Practice', 'subcat': None, 'kosha': 'Annamaya Kosha', 'rct': 10, 'cvr': 9.5},
            {'english': 'Practice A2', 'sanskrit': None, 'segment': 'Pranayama', 'subcat': None, 'kosha': 'Pranamaya Kosha', 'rct': 8, 'cvr': 9.0},
            {'english': 'Practice A3', 'sanskrit': None, 'segment': 'Yogasana', 'subcat': None, 'kosha': 'Annamaya Kosha', 'rct': 6, 'cvr': 8.5},
            {'english': 'Practice A4', 'sanskrit': None, 'segment': 'Meditation', 'subcat': None, 'kosha': 'Manomaya Kosha', 'rct': 4, 'cvr': 8.0},
            {'english': 'Practice A5', 'sanskrit': None, 'segment': 'Yogasana', 'subcat': None, 'kosha': 'Annamaya Kosha', 'rct': 2, 'cvr': 7.5},
            {'english': 'Practice A6', 'sanskrit': None, 'segment': 'Pranayama', 'subcat': None, 'kosha': 'Pranamaya Kosha', 'rct': 1, 'cvr': 7.0},
            {'english': 'Practice A7', 'sanskrit': None, 'segment': 'Meditation', 'subcat': None, 'kosha': 'Manomaya Kosha', 'rct': 0, 'cvr': 6.5},
        ]
        
        # Test Disease B: 3 practices
        test_b_practices = [
            {'english': 'Practice B1', 'sanskrit': None, 'segment': 'Yogasana', 'subcat': None, 'kosha': 'Annamaya Kosha', 'rct': 5, 'cvr': 8.5},
            {'english': 'Practice B2', 'sanskrit': None, 'segment': 'Pranayama', 'subcat': None, 'kosha': 'Pranamaya Kosha', 'rct': 3, 'cvr': 8.0},
            {'english': 'Practice B3', 'sanskrit': None, 'segment': 'Meditation', 'subcat': None, 'kosha': 'Manomaya Kosha', 'rct': 1, 'cvr': 7.5},
        ]
        
        # Test Disease C: 10 practices (for testing larger numbers)
        test_c_practices = [
            {'english': f'Practice C{i+1}', 'sanskrit': None, 'segment': 'Yogasana', 'subcat': None, 'kosha': 'Annamaya Kosha', 'rct': 10-i, 'cvr': 9.0 - (i*0.1)} 
            for i in range(10)
        ]
        
        # Test Disease D: 2 practices (for testing edge cases)
        test_d_practices = [
            {'english': 'Practice D1', 'sanskrit': None, 'segment': 'Yogasana', 'subcat': None, 'kosha': 'Annamaya Kosha', 'rct': 2, 'cvr': 8.0},
            {'english': 'Practice D2', 'sanskrit': None, 'segment': 'Pranayama', 'subcat': None, 'kosha': 'Pranamaya Kosha', 'rct': 1, 'cvr': 7.5},
        ]
        
        # Map modules to practices
        module_practices_map = {
            'Depression_Dr Hemant Bhargav, 2013': (depression_practices, 'Depression', 'Dr Hemant Bhargav, 2013'),
            'GAD_Dr Naveen GH et al., 2019': (gad_practices, 'GAD', 'Dr Naveen GH et al., 2019'),
            'Test Disease A_Test Citation 1': (test_a_practices, 'Test Disease A', 'Test Citation 1'),
            'Test Disease B_Test Citation 1': (test_b_practices, 'Test Disease B', 'Test Citation 1'),
            'Test Disease C_Test Citation 1': (test_c_practices, 'Test Disease C', 'Test Citation 1'),
            'Test Disease D_Test Citation 1': (test_d_practices, 'Test Disease D', 'Test Citation 1'),
        }
        
        # Create all practices
        for module_key, (practices_list, disease_name, citation_text) in module_practices_map.items():
            if module_key not in modules:
                continue
                
            module = modules[module_key]
            citation = citations[citation_text]
            disease = diseases[disease_name]
            
            for p_data in practices_list:
                # Check if practice already exists for this module
                existing = session.query(Practice).filter_by(
                    practice_english=p_data['english'],
                    module_id=module.id
                ).first()
                
                if not existing:
                    practice = Practice(
                        practice_sanskrit=p_data.get('sanskrit'),
                        practice_english=p_data['english'],
                        practice_segment=p_data['segment'],
                        sub_category=p_data.get('subcat'),
                        kosha=p_data.get('kosha'),
                        rounds=3,
                        time_minutes=5.0,
                        description=f"Test practice: {p_data['english']}",
                        cvr_score=p_data.get('cvr'),
                        citation_id=citation.id,
                        module_id=module.id,
                        rct_count=p_data.get('rct', 0)
                    )
                    session.add(practice)
                    session.flush()
                    
                    # Link to disease
                    if disease not in practice.diseases:
                        practice.diseases.append(disease)
        
        # 5. Create some contraindications for testing
        contraindications_data = [
            {
                'practice_english': 'Griva shakti vikasaka-I',
                'practice_sanskrit': 'Griva shakti vikasaka-I',
                'practice_segment': 'Preparatory Practice',
                'sub_category': None,
                'reason': 'Test contraindication for Depression',
                'source_type': 'paper',
                'source_name': 'Test source',
                'apa_citation': 'Test Citation',
                'diseases': ['Depression']
            },
            {
                'practice_english': 'Manibandha shakti vikasaka',
                'practice_sanskrit': 'Manibandha shakti vikasaka',
                'practice_segment': 'Pranayama',
                'sub_category': None,
                'reason': 'Test contraindication for Depression',
                'source_type': 'paper',
                'source_name': 'Test source',
                'apa_citation': 'Test Citation',
                'diseases': ['Depression']
            },
        ]
        
        for c_data in contraindications_data:
            # Check if contraindication already exists
            existing = session.query(Contraindication).filter_by(
                practice_english=c_data['practice_english'],
                practice_segment=c_data['practice_segment']
            ).first()
            
            if not existing:
                contraindication = Contraindication(
                    practice_sanskrit=c_data.get('practice_sanskrit'),
                    practice_english=c_data['practice_english'],
                    practice_segment=c_data['practice_segment'],
                    sub_category=c_data.get('sub_category'),
                    reason=c_data.get('reason'),
                    source_type=c_data.get('source_type'),
                    source_name=c_data.get('source_name'),
                    apa_citation=c_data.get('apa_citation')
                )
                session.add(contraindication)
                session.flush()
                
                # Link to diseases
                for disease_name in c_data['diseases']:
                    if diseases[disease_name] not in contraindication.diseases:
                        contraindication.diseases.append(diseases[disease_name])
        
        session.commit()
        print("✅ Test data generated successfully!")
        print("\nTest modules created:")
        print("1. Depression (Dr Hemant Bhargav, 2013) - 7 practices")
        print("2. GAD (Dr Naveen GH et al., 2019) - 3 practices")
        print("3. Test Disease A - 7 practices")
        print("4. Test Disease B - 3 practices")
        print("5. Test Disease C - 10 practices")
        print("6. Test Disease D - 2 practices")
        print("\nYou can now test the recommendation system with various edge cases!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error generating test data: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    # Initialize database
    create_database()
    
    # Generate test data
    generate_recommendation_test_data()
