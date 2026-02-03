"""
Database Models for Yoga Therapy Recommendation System
This defines the complete database schema using SQLAlchemy ORM

Updated to support disease combinations for contraindications
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, ForeignKey, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool
from datetime import datetime
import os

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
    code = Column(String(50), unique=True)  # Short unique identifier
    
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


# Indexes for Disease table
Index('idx_disease_name', Disease.name)
Index('idx_disease_code', Disease.code)


class Practice(Base):
    """
    Represents a yoga practice with all its details
    """
    __tablename__ = 'practices'
    
    id = Column(Integer, primary_key=True)
    
    # Practice identification
    practice_sanskrit = Column(String(200))
    practice_english = Column(String(200), nullable=False)
    code = Column(String(50))  # Practice code (e.g., K01 for Kapalabhati) - same code for practices with same Sanskrit name
    
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
    cvr_score = Column(Float)  # Capacity-Variability-Responsiveness score
    
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


# Indexes for Practice table - critical for performance
Index('idx_practice_english', Practice.practice_english)
Index('idx_practice_sanskrit', Practice.practice_sanskrit)
Index('idx_practice_code', Practice.code)
Index('idx_practice_segment', Practice.practice_segment)
Index('idx_practice_module_id', Practice.module_id)
Index('idx_practice_citation_id', Practice.citation_id)
Index('idx_practice_kosha', Practice.kosha)
# Composite index for common query patterns
Index('idx_practice_segment_kosha', Practice.practice_segment, Practice.kosha)


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


# Indexes for Citation table
Index('idx_citation_text', Citation.citation_text)


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


# Indexes for Contraindication table
Index('idx_contraindication_english', Contraindication.practice_english)
Index('idx_contraindication_segment', Contraindication.practice_segment)


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
    code = Column(String(50), unique=True)  # Short unique identifier for module
    developed_by = Column(String(500))  # Citation (e.g., "Naveen et al., 2013")
    paper_link = Column(String(1000))  # Link to research paper
    module_description = Column(Text)
    
    # Relationship to practices
    practices = relationship('Practice', back_populates='module', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Module(disease='{self.disease.name if self.disease else 'N/A'}', developed_by='{self.developed_by}')>"


# Indexes for Module table
Index('idx_module_disease_id', Module.disease_id)
Index('idx_module_developed_by', Module.developed_by)
Index('idx_module_code', Module.code)


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
    parenthetical_citation = Column(Text)  # Citation text (optional)
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


# Indexes for RCT table
Index('idx_rct_doi', RCT.doi)
Index('idx_rct_study_type', RCT.study_type)


# Database configuration
def get_database_url():
    """
    Get database URL from environment variable or use default SQLite.
    Supports both SQLite and PostgreSQL.
    
    Environment variables:
    - DATABASE_URL: Full database URL (e.g., 'postgresql://user:pass@localhost/dbname')
    - DB_TYPE: 'sqlite' or 'postgresql'
    - DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME: For PostgreSQL
    
    Returns:
        Database URL string
    """
    # Check for explicit DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        return db_url
    
    # Check for PostgreSQL configuration
    db_type = os.getenv('DB_TYPE', 'sqlite').lower()
    
    if db_type == 'postgresql':
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_user = os.getenv('DB_USER', 'yoga_therapy')
        db_password = os.getenv('DB_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'yoga_therapy')
        
        return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    # Default to SQLite
    return 'sqlite:///yoga_therapy.db'


def create_engine_with_pooling(db_url):
    """
    Create database engine with appropriate pooling configuration.
    
    SQLite: Uses StaticPool (single connection)
    PostgreSQL: Uses QueuePool (connection pooling)
    """
    if db_url.startswith('sqlite'):
        # SQLite configuration
        engine = create_engine(
            db_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={
                'check_same_thread': False,
                'timeout': 20
            },
            pool_pre_ping=True
        )
    else:
        # PostgreSQL configuration with connection pooling
        engine = create_engine(
            db_url,
            echo=False,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
    return engine


# Global engine instance (created on first use)
_engine = None
_session_factory = None


def get_engine():
    """Get or create the global database engine"""
    global _engine
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine_with_pooling(db_url)
    return _engine


# Database setup functions
def create_database(db_path=None):
    """
    Creates the database and all tables with indexes.
    
    Args:
        db_path: Optional database URL. If None, uses get_database_url()
    """
    if db_path is None:
        db_path = get_database_url()
    
    engine = create_engine_with_pooling(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session(db_path=None):
    """
    Returns a database session for performing operations.
    Uses connection pooling for better performance.
    
    Args:
        db_path: Optional database URL. If None, uses get_database_url()
    
    Returns:
        SQLAlchemy session
    """
    global _engine, _session_factory
    
    if db_path is None:
        db_path = get_database_url()
    
    # Use global engine if paths match, otherwise create new
    current_url = get_database_url()
    if db_path == current_url and _engine is not None:
        engine = _engine
    else:
        engine = create_engine_with_pooling(db_path)
        if db_path == current_url:
            _engine = engine
    
    if _session_factory is None or _session_factory.kw['bind'] != engine:
        _session_factory = sessionmaker(bind=engine)
    
    return _session_factory()