from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON, BOOLEAN, Float
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

class SentimentAnalysis(Base):
    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    method_name = Column(String(50), nullable=False)
    
    # Output stored as JSONB for flexibility (e.g. {polarity: 0.1, label: 'positive', subjectivity: 0.2})
    output = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    article = relationship("Article", back_populates="sentiment_analyses")
