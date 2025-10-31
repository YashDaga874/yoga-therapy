"""
Add more diseases to the database for testing disease combinations
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import get_session, Disease, Practice, Citation, Module


def add_sample_diseases():
    """
    Add sample diseases to the database
    """
    session = get_session()
    
    try:
        # Add GAD
        gad = Disease(
            name="GAD",
            description="Generalized Anxiety Disorder"
        )
        session.add(gad)
        
        # Add ADHD
        adhd = Disease(
            name="ADHD",
            description="Attention Deficit Hyperactivity Disorder"
        )
        session.add(adhd)
        
        # Add Insomnia
        insomnia = Disease(
            name="Insomnia",
            description="Sleep disorder characterized by difficulty falling or staying asleep"
        )
        session.add(insomnia)
        
        # Add Substance Use
        substance_use = Disease(
            name="Substance Use",
            description="Substance use disorder"
        )
        session.add(substance_use)
        
        session.commit()
        print("Added diseases: GAD, ADHD, Insomnia, Substance Use")
        
        # Add some sample practices for each disease
        add_sample_practices(session, gad, "GAD")
        add_sample_practices(session, adhd, "ADHD")
        add_sample_practices(session, insomnia, "Insomnia")
        add_sample_practices(session, substance_use, "Substance Use")
        
        session.commit()
        print("Added sample practices for all diseases")
        
    except Exception as e:
        print(f"Error adding diseases: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def add_sample_practices(session, disease, disease_name):
    """
    Add sample practices for a disease
    """
    # Create a citation for this disease
    citation = Citation(
        citation_text=f"Sample citation for {disease_name}",
        citation_type="research_paper",
        full_reference=f"Sample reference for {disease_name} therapy"
    )
    session.add(citation)
    session.flush()  # Get the ID
    
    # Add practices for different segments
    practices = [
        {
            "practice_english": f"Pranayama for {disease_name}",
            "practice_sanskrit": f"Pranayama for {disease_name}",
            "practice_segment": "Breathing Practice",
            "sub_category": f"Breathing Exercise for {disease_name}",
            "rounds": 5,
            "time_minutes": 10.0,
            "description": f"Calming breathing exercise for {disease_name}"
        },
        {
            "practice_english": f"Shavasana for {disease_name}",
            "practice_sanskrit": f"Shavasana for {disease_name}",
            "practice_segment": "Yogasana",
            "sub_category": f"Relaxation Pose for {disease_name}",
            "rounds": 1,
            "time_minutes": 15.0,
            "description": f"Deep relaxation for {disease_name}"
        },
        {
            "practice_english": f"Dhyana for {disease_name}",
            "practice_sanskrit": f"Dhyana for {disease_name}",
            "practice_segment": "Meditation",
            "sub_category": f"Meditation for {disease_name}",
            "rounds": 1,
            "time_minutes": 20.0,
            "description": f"Mindfulness meditation for {disease_name}"
        }
    ]
    
    for practice_data in practices:
        practice = Practice(
            practice_english=practice_data["practice_english"],
            practice_sanskrit=practice_data["practice_sanskrit"],
            practice_segment=practice_data["practice_segment"],
            sub_category=practice_data["sub_category"],
            rounds=practice_data["rounds"],
            time_minutes=practice_data["time_minutes"],
            description=practice_data["description"],
            citation_id=citation.id
        )
        session.add(practice)
        
        # Link practice to disease
        disease.practices.append(practice)
    
    # Add module information
    module = Module(
        disease_id=disease.id,
        developed_by=f"Sample researcher for {disease_name}",
        module_description=f"Therapy module developed for {disease_name} treatment"
    )
    session.add(module)


def main():
    """
    Main function to add diseases
    """
    print("Adding sample diseases to database...")
    add_sample_diseases()
    print("Done!")


if __name__ == "__main__":
    main()
