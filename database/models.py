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
    
    # Kosa classification
    kosa = Column(String(50), nullable=False)  # Annamaya_Kosa, Pranamaya_Kosa, etc.
    sub_category = Column(String(100))  # Loosening_Practice, Asana, standing_asana, etc.
    
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
    
    # Relationships
    diseases = relationship(
        'Disease',
        secondary=disease_practice_association,
        back_populates='practices'
    )
    
    def __repr__(self):
        return f"<Practice(english='{self.practice_english}', kosa='{self.kosa}')>"


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
    
    # Which kosa does this contraindication apply to
    kosa = Column(String(50), nullable=False)
    sub_category = Column(String(100))
    
    # Reason for contraindication
    reason = Column(Text)
    
    # Relationships - now linked to individual diseases, not combinations
    diseases = relationship(
        'Disease',
        secondary=disease_contraindication_association,
        back_populates='contraindications'
    )
    
    def __repr__(self):
        return f"<Contraindication(practice='{self.practice_english}', kosa='{self.kosa}')>"


class Module(Base):
    """
    Stores metadata about therapy modules for each disease
    This is where we store 'Developed by' information
    """
    __tablename__ = 'modules'
    
    id = Column(Integer, primary_key=True)
    disease_id = Column(Integer, ForeignKey('diseases.id'), unique=True, nullable=False)
    disease = relationship('Disease')
    
    developed_by = Column(String(500))
    module_description = Column(Text)
    
    def __repr__(self):
        return f"<Module(disease='{self.disease.name}', developed_by='{self.developed_by}')>"


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