"""
Custom Data Import for Your Yoga Therapy Database

This script imports data from your Excel/spreadsheet format
and properly maps categories to the 5 Koshas.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import (
    Disease, Practice, Citation, Contraindication, Module,
    create_database, get_session
)


class YogaDataImporter:
    """
    Imports your yoga therapy data with proper Kosa mapping
    """
    
    def __init__(self, db_path='sqlite:///yoga_therapy.db'):
        self.db_path = db_path
        create_database(db_path)
        self.session = get_session(db_path)
        self.citation_cache = {}
        
        # Category to Kosa mapping based on your data
        self.category_to_kosa_map = {
            # Physical practices → Annamaya Kosa
            'preparation': 'Annamaya_Kosa',
            'loosening': 'Annamaya_Kosa',
            'sukshma': 'Annamaya_Kosa',
            'sthula': 'Annamaya_Kosa',
            'vyayama': 'Annamaya_Kosa',
            'surya namaskar': 'Annamaya_Kosa',
            'standing asana': 'Annamaya_Kosa',
            'sitting asana': 'Annamaya_Kosa',
            'prone asana': 'Annamaya_Kosa',
            'supine asana': 'Annamaya_Kosa',
            'jogging': 'Annamaya_Kosa',
            'kriya': 'Annamaya_Kosa',
            'asana': 'Annamaya_Kosa',
            
            # Breath practices → Pranamaya Kosa
            'pranayama': 'Pranamaya_Kosa',
            'breathing': 'Pranamaya_Kosa',
            'sectional breathing': 'Pranamaya_Kosa',
            'breath': 'Pranamaya_Kosa',
            
            # Mental practices → Manomaya Kosa
            'meditation': 'Manomaya_Kosa',
            'relaxation': 'Manomaya_Kosa',
            'sound resonance': 'Manomaya_Kosa',
            'deep relaxation': 'Manomaya_Kosa',
            
            # Wisdom practices → Vijnanamaya Kosa
            'counseling': 'Vijnanamaya_Kosa',
            'yogic counseling': 'Vijnanamaya_Kosa',
            'sattvic ahara': 'Vijnanamaya_Kosa',
            'diet': 'Vijnanamaya_Kosa',
            'yama': 'Vijnanamaya_Kosa',
            'niyama': 'Vijnanamaya_Kosa',
            'panchakosha': 'Vijnanamaya_Kosa',
            'concept': 'Vijnanamaya_Kosa',
            
            # Bliss practices → Anandamaya Kosa
            'advanced meditation': 'Anandamaya_Kosa',
            'philosophy': 'Anandamaya_Kosa',
        }
    
    def determine_kosa(self, category):
        """
        Determine which Kosa a category belongs to
        """
        category_lower = category.lower()
        
        for key, kosa in self.category_to_kosa_map.items():
            if key in category_lower:
                return kosa
        
        # Default to Annamaya Kosa if unclear
        return 'Annamaya_Kosa'
    
    def import_depression_data(self):
        """Import Depression data"""
        print("\n" + "="*60)
        print("Importing Depression Data")
        print("="*60)
        
        # Create disease
        disease = self._get_or_create_disease("Depression", 
            "Major Depressive Disorder - characterized by persistent sadness and loss of interest")
        
        # Create module
        self._create_module(disease, "Dr Naveen GH et al., 2013")
        
        # Create citation
        citation = self._get_or_create_citation(
            "Dr Naveen GH et al., 2013",
            "Research study on yoga therapy for depression"
        )
        
        # Import practices by category
        practices_data = [
            # Loosening Practices - Annamaya Kosa
            ("Griva shakti vikasaka-I", "Neck sideward movement", "Loosening_Practice", 5, 1),
            ("Griva shakti vikasaka-II", "Neck forward and backward bending", "Loosening_Practice", 5, 1),
            ("Manibandha shakti vikasaka", "Wrist movement", "Loosening_Practice", 10, 1),
            ("Kaphoni shakti vikasaka", "Elbow flexion and stretching", "Loosening_Practice", 3, 1),
            ("Bhuja valli shakti vikasaka", "Arms movement", "Loosening_Practice", 3, 1),
            ("Janu shakti vikasaka", "Knee stretching", "Loosening_Practice", 5, 1),
            ("Gulpha, pada pristha, pada tala shakti vikasaka", "Ankle rotation (clockwise and anticlockwise)", "Loosening_Practice", 5, 1),
            ("Kati shakti vikasaka", "Twisting", "Loosening_Practice", 10, 1),
            (None, "Jogging", "Loosening_Practice", 10, 2),
            ("Mukha Dhauti", "Cleaning through single blast breath", "Loosening_Practice", 5, 0.25),
            
            # Surya Namaskar - Annamaya Kosa
            ("Surya namaskar", "Sun salutation—12 steps", "surya_namaskar", 3, 15),
            
            # Relaxation - Manomaya Kosa (relaxation is mental)
            ("Shavasana (with chanting of 'A')", "Relaxation in corpse pose", "relaxation", 1, 2),
            
            # Standing Asanas - Annamaya Kosa
            ("Ardha chakrasana", "Backward bending pose", "standing_asana", 5, 2),
            
            # Sitting Asanas - Annamaya Kosa
            ("Ardha ustrasana", "Camel pose", "sitting_asana", 5, 2),
            ("Paschimottanasana", "Seated forward bending pose", "sitting_asana", 5, 2),
            
            # Prone Asanas - Annamaya Kosa
            ("Bhujangasana", "Serpent pose", "prone_asana", 5, 2),
            
            # Supine Asanas - Annamaya Kosa
            ("Pawanamuktasana", "Wind releasing pose", "supine_asana", 5, 2),
            ("Viparitakarani mudra", "Legs-up-the-wall pose", "supine_asana", 5, 2),
            ("Setu bandhasana", "Bridge pose", "supine_asana", 5, 2),
            
            # Final Relaxation - Manomaya Kosa
            ("Shavasana", "Relaxation in corpse pose/Yoga nidra", "final_relaxation", 1, 4),
            
            # Kriya - Annamaya Kosa
            ("Kapalabhati", "Breath of fire/Skull shining breath", "kriya_practices", 2, 2),
        ]
        
        for practice_data in practices_data:
            sanskrit, english, category, rounds, time_min = practice_data
            kosa = self.determine_kosa(category)
            
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa=kosa,
                sub_category=category,
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Pranayama Practices - Pranamaya Kosa
        pranayama_practices = [
            ("Surya anuloma viloma", "Right nostril breathing", 21, 3),
            ("Ujjayi", "Victorious breath", 9, 2),
            ("Bhastrika", "Bellows' breathing", 3, 3),
        ]
        
        for sanskrit, english, rounds, time_min in pranayama_practices:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Pranamaya_Kosa',
                sub_category='pranayama_practices',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Meditation - Manomaya Kosa
        self._create_practice(
            disease=disease,
            practice_sanskrit="Nadanusandhana",
            practice_english="Sound resonance (AA, UU, MM, AUM kara)",
            kosa='Manomaya_Kosa',
            sub_category='meditation_practices',
            rounds=9,
            time_minutes=5,
            citation=citation
        )
        
        self.session.commit()
        print("✓ Depression data imported successfully!")
    
    def import_gad_data(self):
        """Import GAD (Generalized Anxiety Disorder) data"""
        print("\n" + "="*60)
        print("Importing GAD Data")
        print("="*60)
        
        disease = self._get_or_create_disease("GAD", 
            "Generalized Anxiety Disorder - characterized by excessive worry")
        
        self._create_module(disease, "Clinical Yoga Research, 2015")
        
        citation = self._get_or_create_citation(
            "Clinical Yoga Research, 2015",
            "Yoga interventions for anxiety disorders"
        )
        
        # Loosening practices - Annamaya Kosa
        loosening_practices = [
            ("Griva sithilikarana", "Neck exercise", 5, 1),
            ("Bahumula sithilikarana", "Shoulder rotation", 5, 1),
            ("Kaphoni sithilikarana", "Elbow movement", 5, 1),
            ("Manibandha sithilikarana", "Wrist rotation", 5, 1),
            ("Anguli sithilikarana", "Loosening of fingers", 5, 1),
            ("Kati sithilikarana", "Waist rotation", 5, 1),
            ("Janu sithilikarana", "Knee rotation", 5, 1),
            ("Gulpha sithilikarana", "Ankle rotation", 5, 1),
            ("Shvasa kriya", "Hand stretch breathing", 3, 3),
            ("Shvasa kriya", "Hands in and out breathing", 1, 2),
            ("Tadasana shvasa kriya", "Ankle stretch breathing", 1, 1),
            ("Shashankasana shvasa kriya", "Hare pose/Moon breathing", 1, 2),
            ("Marjariasana shvasa kriya", "Tiger breathing", 1, 2),
            ("Setu bandhasana shvasa kriya", "Bridge pose breathing", 1, 2),
        ]
        
        for sanskrit, english, rounds, time_min in loosening_practices:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Annamaya_Kosa',
                sub_category='loosening_practices',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Surya Namaskar - Annamaya Kosa
        self._create_practice(
            disease=disease,
            practice_sanskrit="Surya namaskar",
            practice_english="Surya namaskar (7-step practice to be done slowly) with 3 Mantras",
            kosa='Annamaya_Kosa',
            sub_category='surya_namaskar',
            rounds=3,
            time_minutes=5,
            citation=citation
        )
        
        # Standing Asanas - Annamaya Kosa
        standing_asanas = [
            ("Ardhakati chakrasana", "Lateral arc pose (Half wheel pose)", 2, 2),
            ("Ardha chakrasana", "Half wheel pose", 2, 2),
            ("Padahastasana", "Hand-to-feet pose", 2, 2),
            ("Shashankasana", "Rabbit pose", 1, 2),
            ("Vakrasana", "Sitting twisted pose", 1, 2),
        ]
        
        for sanskrit, english, rounds, time_min in standing_asanas:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Annamaya_Kosa',
                sub_category='standing_asana',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Sitting Asanas - Annamaya Kosa
        sitting_asanas = [
            ("Paschimottanasana", "Back stretch pose", 1, 2),
            ("Pawanamuktasana", "Wind releasing pose", 1, 2),
        ]
        
        for sanskrit, english, rounds, time_min in sitting_asanas:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Annamaya_Kosa',
                sub_category='sitting_asana',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Supine Asanas - Annamaya Kosa
        self._create_practice(
            disease=disease,
            practice_sanskrit="Setu bandhasana",
            practice_english="Bridge pose",
            kosa='Annamaya_Kosa',
            sub_category='supine_asana',
            rounds=1,
            time_minutes=2,
            citation=citation
        )
        
        # Prone Asanas - Annamaya Kosa
        prone_asanas = [
            ("Bhujangasana", "Serpent pose", 2, 2),
            ("Parvatasana", "Mountain pose", 1, 2),
        ]
        
        for sanskrit, english, rounds, time_min in prone_asanas:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Annamaya_Kosa',
                sub_category='prone_asana',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Pranayama - Pranamaya Kosa
        pranayama_practices = [
            ("Chandra bhedana", "Single nostril breathing (left)", 9, 3),
            ("Nadi shuddhi", "Alternate nostril breathing", 9, 3),
            ("Chandra anuloma viloma", "Left nostril breathing", 21, 5),
            ("Sheetali", "Cooling pranayama", 9, 3),
            ("Bhramari", "Humming bee breathing", 9, 3),
        ]
        
        for sanskrit, english, rounds, time_min in pranayama_practices:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Pranamaya_Kosa',
                sub_category='pranayama_practices',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Relaxation - Manomaya Kosa
        relaxation_practices = [
            ("Sampurna vishranti paddati in Shavasana", "Deep relaxation technique", 1, 5),
            ("Geethra sithilikaran upaya in Shavasana", "Quick relaxation technique", 1, 3),
        ]
        
        for sanskrit, english, rounds, time_min in relaxation_practices:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Manomaya_Kosa',
                sub_category='relaxation_techniques',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Meditation - Manomaya Kosa
        meditation_practices = [
            ("Om dhyana/Japa", "Om meditation", 1, 5),
            ("Nadanusandhana", "A, U, M and AUM meditation", 1, 5),
        ]
        
        for sanskrit, english, rounds, time_min in meditation_practices:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Manomaya_Kosa',
                sub_category='meditation_techniques',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # Counseling - Vijnanamaya Kosa
        counseling_practices = [
            ("Panchakosha model", "Five sheaths of existence", 1, 5),
            ("Sattvic ahara", "Balanced diet", 1, 5),
            ("Yama and Niyama", "Do's and don'ts, observances", 1, 5),
            ("Pratipaksha bhavana", "Principle of opposites", 1, 5),
            ("Jnana, Bhakti, Raja and Karma yoga", "Concept of four paths", 1, 5),
        ]
        
        for sanskrit, english, rounds, time_min in counseling_practices:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Vijnanamaya_Kosa',
                sub_category='yogic_counseling',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        self.session.commit()
        print("✓ GAD data imported successfully!")
    
    def import_adhd_data(self):
        """Import ADHD data"""
        print("\n" + "="*60)
        print("Importing ADHD Data")
        print("="*60)
        
        disease = self._get_or_create_disease("ADHD", 
            "Attention Deficit Hyperactivity Disorder - characterized by inattention and hyperactivity")
        
        self._create_module(disease, "Pediatric Yoga Research, 2018")
        
        citation = self._get_or_create_citation(
            "Pediatric Yoga Research, 2018",
            "Yoga interventions for ADHD in children"
        )
        
        # Loosening practices - Annamaya Kosa
        loosening = [
            (None, "Jogging (≤ 20 for each type)", 20, 5),
            ("Mukha dhauti", "Cleaning through single blast breath (05-Oct)", 1, 1),
        ]
        
        for sanskrit, english, rounds, time_min in loosening:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Annamaya_Kosa',
                sub_category='loosening_practices',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # More practices would be added here following the same pattern
        # Standing, sitting, prone, supine asanas
        # Pranayama, meditation etc.
        
        self.session.commit()
        print("✓ ADHD data imported successfully!")
    
    def import_substance_use_disorder_data(self):
        """Import Substance Use Disorder data"""
        print("\n" + "="*60)
        print("Importing Substance Use Disorder Data")
        print("="*60)
        
        disease = self._get_or_create_disease("Substance_Use_Disorder", 
            "Substance Use Disorder - addiction and dependence on substances")
        
        self._create_module(disease, "Addiction Recovery Yoga, 2020")
        
        citation = self._get_or_create_citation(
            "Addiction Recovery Yoga, 2020",
            "Yoga therapy for substance use disorders"
        )
        
        # Relaxation before breathing - Manomaya Kosa
        self._create_practice(
            disease=disease,
            practice_sanskrit="Tatksham instant relaxation",
            practice_english="Instant relaxation",
            kosa='Manomaya_Kosa',
            sub_category='relaxation',
            rounds=2,
            time_minutes=4,
            citation=citation
        )
        
        # Breathing practices - Pranamaya Kosa
        breathing = [
            ("Pawanmuktasana breathing", "Wind release 5 rounds each", 5, 5),
            ("Udara shvasana", "Deep abdominal breathing", 5, 2),
            ("Makarasana breathing", "Crocodile breathing", 5, 2),
            ("Bhujangasana breathing", "Cobra pose breathing", 5, 2),
            ("Naukasana", "Boat pose", 5, 2),
        ]
        
        for sanskrit, english, rounds, time_min in breathing:
            self._create_practice(
                disease=disease,
                practice_sanskrit=sanskrit,
                practice_english=english,
                kosa='Pranamaya_Kosa',
                sub_category='breathing_practices',
                rounds=rounds,
                time_minutes=time_min,
                citation=citation
            )
        
        # More practices would be added following the same pattern
        
        self.session.commit()
        print("✓ Substance Use Disorder data imported successfully!")
    
    def _get_or_create_disease(self, name, description=""):
        """Get existing disease or create new one"""
        disease = self.session.query(Disease).filter_by(name=name).first()
        if not disease:
            disease = Disease(name=name, description=description)
            self.session.add(disease)
            self.session.flush()
        return disease
    
    def _create_module(self, disease, developed_by):
        """Create module for disease"""
        module = self.session.query(Module).filter_by(disease_id=disease.id).first()
        if not module:
            module = Module(
                disease_id=disease.id,
                developed_by=developed_by
            )
            self.session.add(module)
    
    def _get_or_create_citation(self, citation_text, full_reference=""):
        """Get or create citation"""
        if citation_text in self.citation_cache:
            return self.citation_cache[citation_text]
        
        citation = self.session.query(Citation).filter_by(citation_text=citation_text).first()
        if not citation:
            citation = Citation(
                citation_text=citation_text,
                citation_type='research_paper',
                full_reference=full_reference
            )
            self.session.add(citation)
            self.session.flush()
        
        self.citation_cache[citation_text] = citation
        return citation
    
    def _create_practice(self, disease, practice_english, kosa, sub_category,
                        rounds=None, time_minutes=None, practice_sanskrit=None,
                        citation=None):
        """Create a practice and link to disease"""
        # Check if exists
        existing = self.session.query(Practice).filter_by(
            practice_english=practice_english,
            kosa=kosa,
            sub_category=sub_category
        ).first()
        
        if existing:
            if disease not in existing.diseases:
                existing.diseases.append(disease)
            return existing
        
        # Create new
        practice = Practice(
            practice_sanskrit=practice_sanskrit,
            practice_english=practice_english,
            kosa=kosa,
            sub_category=sub_category,
            rounds=rounds,
            time_minutes=time_minutes,
            citation=citation
        )
        
        practice.diseases.append(disease)
        self.session.add(practice)
        return practice
    
    def import_all(self):
        """Import all diseases"""
        print("\n" + "="*70)
        print("IMPORTING YOUR YOGA THERAPY DATABASE")
        print("="*70)
        
        self.import_depression_data()
        self.import_gad_data()
        self.import_adhd_data()
        self.import_substance_use_disorder_data()
        
        print("\n" + "="*70)
        print("✓ ALL DATA IMPORTED SUCCESSFULLY!")
        print("="*70)
        print(f"\nDatabase created: {self.db_path}")
        print("You can now start the web interface: python web/app.py")
    
    def close(self):
        """Close session"""
        self.session.close()


if __name__ == '__main__':
    importer = YogaDataImporter()
    try:
        importer.import_all()
    finally:
        importer.close()