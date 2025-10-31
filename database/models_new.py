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

# Association table for many-to-many relationship between disease combinations and contraindications
disease_combination_contraindication_association = Table(
    'disease_combination_contraindication_association',
    Base.metadata,
    Column('disease_combination_id', Integer, ForeignKey('disease_combinations.id'), primary_key=True),
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
    
    # Practice Segment classification
    practice_segment = Column(String(50), nullable=False)  # Preparatory Practice, Breathing Practice, etc.
    sub_category = Column(String(100))  # Subcategory within the segment
    
    # Practice details
    rounds = Column(Integer)
    time_minutes = Column(Float)
    strokes_per_min = Column(Integer)
    strokes_per_cycle = Column(Integer)
    rest_between_cycles_sec = Column(Integer)
    variations = Column(Text)  # JSON string for variations list
    steps = Column(Text)  # JSON string for steps list
    description = Column(Text)
    
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
    """
    __tablename__ = 'disease_combinations'
    
    id = Column(Integer, primary_key=True)
    combination_name = Column(String(500), unique=True, nullable=False)  # e.g., "Depression + GAD"
    diseases_json = Column(Text, nullable=False)  # JSON string of disease names
    
    # Relationships
    contraindications = relationship(
        'Contraindication',
        secondary=disease_combination_contraindication_association,
        back_populates='disease_combinations'
    )
    
    def __repr__(self):
        return f"<DiseaseCombination(name='{self.combination_name}')>"


class Contraindication(Base):
    """
    Stores contraindications for specific disease combinations and practices
    A contraindication means: "For disease combination X, do NOT include practice Y"
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
    
    # Relationships
    disease_combinations = relationship(
        'DiseaseCombination',
        secondary=disease_combination_contraindication_association,
        back_populates='contraindications'
    )
    
    def __repr__(self):
        return f"<Contraindication(practice='{self.practice_english}', segment='{self.practice_segment}')>"


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
