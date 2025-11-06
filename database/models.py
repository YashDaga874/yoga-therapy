"""
Database Models for Yoga Therapy Recommendation System
This defines the complete database schema using SQLAlchemy ORM

Updated to support disease combinations for contraindications
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between diseases and practices
disease_practice_association = Table(
    'disease_practice_association',
    Base.metadata,
    Column('disease_id', Integer, ForeignKey('diseases.id'), primary_key=True),
    Column('practice_id', Integer, ForeignKey('practices.id'), primary_key=True)
)

# Association table for many-to-many relationship between diseases and contraindications
disease_contraindication_association = Table(
    'disease_contraindication_association',
    Base.metadata,
    Column('disease_id', Integer, ForeignKey('diseases.id'), primary_key=True),
    Column('contraindication_id', Integer, ForeignKey('contraindications.id'), primary_key=True)
)


class Disease(Base):
    """
    Represents a disease/condition (e.g., Depression, GAD, Anxiety)
    """
    __tablename__ = 'diseases'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text)
    
    # Relationships
    practices = relationship(
        'Practice',
        secondary=disease_practice_association,
        back_populates='diseases'
    )
    
    contraindications = relationship(
        'Contraindication',
        secondary=disease_contraindication_association,
        back_populates='diseases'
    )
    
    def __repr__(self):
        return f"<Disease(name='{self.name}')>"


class Practice(Base):
    """
    Represents a yoga practice with all its details
    """
    __tablename__ = 'practices'
    
    id = Column(Integer, primary_key=True)
    
    # Practice identification
    practice_sanskrit = Column(String(200))
    practice_english = Column(String(200), nullable=False)
    
    # Practice Category classification (formerly practice_segment)
    practice_segment = Column(String(50), nullable=False)  # Preparatory Practice, Breathing Practice, etc. (now called "Category")
    sub_category = Column(String(100))  # Subcategory within the segment
    kosha = Column(String(50))  # Annamaya Kosha, Pranamaya Kosha, Manomaya Kosha, Vijnanamaya Kosha, Anandamaya Kosha
    
    # Practice details
    rounds = Column(Integer)
    time_minutes = Column(Float)
    strokes_per_min = Column(Integer)
    strokes_per_cycle = Column(Integer)
    rest_between_cycles_sec = Column(Integer)
    variations = Column(Text)  # JSON string for variations list (now includes referred_in field)
    steps = Column(Text)  # JSON string for steps list
    description = Column(Text)
    how_to_do = Column(Text)  # How to do this practice
    
    # Media attachments
    photo_path = Column(String(500))  # Path to uploaded photo
    video_path = Column(String(500))  # Path to uploaded video
    
    # Citation tracking
    citation_id = Column(Integer, ForeignKey('citations.id'))
    citation = relationship('Citation', back_populates='practices')
    
    # Module relationship (practices belong to a module)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=True)
    module = relationship('Module', back_populates='practices')
    
    # Relationships
    diseases = relationship(
        'Disease',
        secondary=disease_practice_association,
        back_populates='practices'
    )
    
    # RCT count for this category and disease combo
    rct_count = Column(Integer, default=0)  # Number of RCTs supporting this practice category for each disease
    
    def __repr__(self):
        return f"<Practice(english='{self.practice_english}', segment='{self.practice_segment}')>"


class Citation(Base):
    """
    Stores research paper/book references for practices
    """
    __tablename__ = 'citations'
    
    id = Column(Integer, primary_key=True)
    citation_text = Column(Text, nullable=False)  # e.g., "Dr Naveen GH et al., 2013"
    citation_type = Column(String(50))  # 'research_paper', 'book', 'study'
    full_reference = Column(Text)  # Complete bibliographic reference
    url = Column(String(500))
    
    # Relationships
    practices = relationship('Practice', back_populates='citation')
    
    def __repr__(self):
        return f"<Citation(text='{self.citation_text}')>"


class DiseaseCombination(Base):
    """
    Represents a combination of diseases for contraindication analysis
    e.g., "Depression + GAD" or "Depression + GAD + Insomnia"
    
    Note: This is kept for backward compatibility but contraindications
    are now linked to individual diseases, not combinations.
    """
    __tablename__ = 'disease_combinations'
    
    id = Column(Integer, primary_key=True)
    combination_name = Column(String(500), unique=True, nullable=False)  # e.g., "Depression + GAD"
    diseases_json = Column(Text, nullable=False)  # JSON string of disease names
    
    def __repr__(self):
        return f"<DiseaseCombination(name='{self.combination_name}')>"


class Contraindication(Base):
    """
    Stores contraindications for specific diseases and practices
    A contraindication means: "For disease X, do NOT include practice Y"
    """
    __tablename__ = 'contraindications'
    
    id = Column(Integer, primary_key=True)
    
    # The practice that should be avoided
    practice_sanskrit = Column(String(200))
    practice_english = Column(String(200), nullable=False)
    
    # Which practice segment does this contraindication apply to
    practice_segment = Column(String(50), nullable=False)
    sub_category = Column(String(100))
    
    # Reason for contraindication
    reason = Column(Text)
    
    # Source information
    source_type = Column(String(50))  # 'book', 'paper', 'ancient_text'
    source_name = Column(String(500))  # Name of book/paper or link
    page_number = Column(String(200))  # Page number/range for books
    apa_citation = Column(Text)  # Full APA citation
    
    # Relationships - now linked to individual diseases, not combinations
    diseases = relationship(
        'Disease',
        secondary=disease_contraindication_association,
        back_populates='contraindications'
    )
    
    def __repr__(self):
        return f"<Contraindication(practice='{self.practice_english}', segment='{self.practice_segment}')>"


class Module(Base):
    """
    Stores metadata about therapy modules for each disease
    Each module represents a research paper/study
    Multiple modules can exist for the same disease
    """
    __tablename__ = 'modules'
    
    id = Column(Integer, primary_key=True)
    disease_id = Column(Integer, ForeignKey('diseases.id'), nullable=False)
    disease = relationship('Disease', backref='modules')
    
    # Module identification
    developed_by = Column(String(500))  # Parenthetical citation (e.g., "Naveen et al., 2013")
    paper_link = Column(String(1000))  # Link to research paper
    module_description = Column(Text)
    
    # Relationship to practices
    practices = relationship('Practice', back_populates='module', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Module(disease='{self.disease.name if self.disease else 'N/A'}', developed_by='{self.developed_by}')>"


# Association table for RCT and symptoms (many-to-many)
rct_symptom_association = Table(
    'rct_symptom_association',
    Base.metadata,
    Column('rct_id', Integer, ForeignKey('rcts.id'), primary_key=True),
    Column('symptom_id', Integer, ForeignKey('rct_symptoms.id'), primary_key=True)
)

# Association table for RCT and diseases (many-to-many)
rct_disease_association = Table(
    'rct_disease_association',
    Base.metadata,
    Column('rct_id', Integer, ForeignKey('rcts.id'), primary_key=True),
    Column('disease_id', Integer, ForeignKey('diseases.id'), primary_key=True)
)


class RCTSymptom(Base):
    """
    Stores symptoms/disease names from RCT studies with p-values
    """
    __tablename__ = 'rct_symptoms'
    
    id = Column(Integer, primary_key=True)
    symptom_name = Column(String(200), nullable=False)
    p_value_operator = Column(String(10))  # <, >, <=, >=, =
    p_value = Column(Float)
    is_significant = Column(Integer)  # 1 if significant (p <= 0.05), 0 if not
    scale = Column(String(200))  # Scale used for this symptom
    
    def __repr__(self):
        return f"<RCTSymptom(symptom='{self.symptom_name}', p_value={self.p_value_operator}{self.p_value}, significant={self.is_significant})>"


class RCT(Base):
    """
    Stores Randomized Controlled Trial (RCT) data
    """
    __tablename__ = 'rcts'
    
    id = Column(Integer, primary_key=True)
    
    # Data enrolled date
    data_enrolled_date = Column(String(50))  # Calendar type
    
    # Database/Journal
    database_journal = Column(String(200))  # PubMed, etc.
    keywords = Column(Text)  # Keywords, boolean, filters used
    
    # Basic information
    doi = Column(String(500))
    pmic_nmic = Column(String(200))  # PMIC/NMIC or extra option if not available
    title = Column(Text)
    parenthetical_citation = Column(Text)  # Parenthetical citation/citation
    citation_full = Column(Text)  # Full citation
    study_type = Column(String(100))  # RCT, Clinical Trial, Others
    
    # Demographics
    participant_type = Column(String(500))  # teacher, army, nurse, elderly, etc.
    age_mean = Column(Float)  # Mean age
    age_std_dev = Column(Float)  # Standard deviation
    age_range_calculated = Column(String(100))  # Calculated from mean and std dev
    gender_male = Column(Integer)  # Count
    gender_female = Column(Integer)  # Count
    gender_not_mentioned = Column(Integer)  # Count
    
    # Citation link
    citation_link = Column(String(1000))  # URL to the paper
    
    # Intervention
    intervention_practices = Column(Text)  # JSON: list of practices with categories
    intervention_category = Column(String(200))  # DEPRECATED: Now in intervention_practices
    number_of_days = Column(Integer)  # DEPRECATED: Now in duration fields below
    
    # Duration fields
    duration_type = Column(String(20))  # 'days', 'weeks', 'months'
    duration_value = Column(Integer)  # e.g., 12
    frequency_per_duration = Column(String(200))  # e.g., "3 times per week"
    
    # Results
    scales = Column(Text)  # Comma separated, can be multiple (moved here from per-symptom)
    results = Column(Text)
    conclusion = Column(Text)  # A line or so
    remarks = Column(Text)  # Optional: report contraindications or special cases
    
    # Relationships
    symptoms = relationship(
        'RCTSymptom',
        secondary=rct_symptom_association,
        backref='rcts'
    )
    
    diseases = relationship(
        'Disease',
        secondary=rct_disease_association,
        backref='rcts'
    )
    
    # RCT count tracking (calculated field stored for performance)
    rct_number = Column(Integer)  # RCT number for this category-disease combo
    
    def __repr__(self):
        return f"<RCT(title='{self.title[:50] if self.title else 'N/A'}...', doi='{self.doi}')>"


# Database setup functions
def create_database(db_path='sqlite:///yoga_therapy.db'):
    """
    Creates the database and all tables
    """
    engine = create_engine(db_path, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path='sqlite:///yoga_therapy.db'):
    """
    Returns a database session for performing operations
    """
    engine = create_engine(db_path, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()