from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(String(512), unique=True, index=True, nullable=False)
    source = Column(String(100), nullable=False, index=True)
    summary = Column(Text)
    published_at = Column(DateTime, index=True)
    
    # Metadata for traceability
    run_id = Column(String(50), nullable=False, index=True)
    run_date = Column(Date, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sentiment_analyses = relationship("SentimentAnalysis", back_populates="article", cascade="all, delete-orphan")

    ner_results = relationship("NamedEntityRecognition", back_populates="article", cascade="all, delete-orphan")
    framing_results = relationship("EntityFraming", back_populates="article", cascade="all, delete-orphan")


class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    method_name = Column(String(50), nullable=False)
    
    # Structured output
    polarity = Column(Float, nullable=False)
    label = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="sentiment_analyses")

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), unique=True, index=True, nullable=False)
    run_date = Column(Date, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String(50))
    
    # Stage completion flags
    collect_completed = Column(Boolean, default=False)
    parse_completed = Column(Boolean, default=False)
    clean_completed = Column(Boolean, default=False)
    signal_completed = Column(Boolean, default=False)
    
    # Statistics
    total_sources = Column(Integer)
    total_fetched = Column(Integer)
    total_parsed = Column(Integer)
    total_cleaned = Column(Integer)
    total_analyzed = Column(Integer)
    
    errors = Column(Text)
    
    # Relationships
    statistics = relationship("RunStatistic", back_populates="run", cascade="all, delete-orphan")

class RunStatistic(Base):
    __tablename__ = "run_statistics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(50), ForeignKey("pipeline_runs.run_id"), index=True, nullable=False)
    stage = Column(String(50), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float)
    details = Column(JSON)
    
    # Relationships
    run = relationship("PipelineRun", back_populates="statistics")



class NamedEntityRecognition(Base):
    __tablename__ = "named_entity_recognition"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    method_name = Column(String(50), nullable=False)
    
    # Structured output - One row per entity
    entity_group = Column(String(50), nullable=False)
    word = Column(String(255), nullable=False)
    score = Column(Float, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="ner_results")

class EntityFraming(Base):
    __tablename__ = "entity_framing"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Context
    entity_word = Column(String(255), nullable=False, index=True)
    framing_phrase = Column(String(255), nullable=False)
    
    # Metadata
    method_name = Column(String(50), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="framing_results")

