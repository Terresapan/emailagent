"""Shared database models and connection management.

This package provides:
- SQLAlchemy models (Digest, Email)
- Database connection with connection pooling
- Session management for both API and emailagent
"""
import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Float, JSON, DateTime, Index, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/contentagent"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Verify connections before use
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Digest(Base):
    """Processed digest containing briefing and LinkedIn content."""
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    digest_type = Column(String(20), default="daily", nullable=False, index=True)  # 'daily' or 'weekly'
    briefing = Column(Text)
    linkedin_content = Column(Text)
    newsletter_summaries = Column(Text)
    structured_digests = Column(JSON)  # List of serialized EmailDigest objects
    emails_processed = Column(JSON)  # List of "sender: subject" strings
    created_at = Column(DateTime, default=datetime.now)

    # Relationship to emails
    emails = relationship("Email", back_populates="digest")


class Email(Base):
    """Raw email storage for future analysis."""
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String(255), unique=True, nullable=False, index=True)
    sender = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    received_at = Column(DateTime)
    processed_at = Column(DateTime, default=datetime.now)
    digest_id = Column(Integer, ForeignKey("digests.id"))

    # Relationship to digest
    digest = relationship("Digest", back_populates="emails")


class ProductHuntInsightDB(Base):
    """Stored Product Hunt analysis results."""
    __tablename__ = "product_hunt_insights"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)  # No index=True, we use composite index below
    period = Column(String(20), default="daily", nullable=False)  # 'daily' or 'weekly'
    launches_json = Column(JSON)  # List of top launches
    trend_summary = Column(Text)  # LLM-generated trend analysis
    content_angles = Column(JSON)  # List of strings
    created_at = Column(DateTime)
    
    __table_args__ = (
        # Ensure only one daily and one weekly entry per date
        Index('ix_product_hunt_insights_date_period', 'date', 'period', unique=True),
    )


class HackerNewsInsightDB(Base):
    """DB Model for Hacker News insights."""
    __tablename__ = "hacker_news_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)  # No index=True, we use composite index below
    period = Column(String(20), default="daily", nullable=False)  # 'daily' or 'weekly'
    stories_json = Column(JSON)  # List of stories
    summary = Column(Text)       # LLM summary
    top_themes = Column(JSON)    # List of strings
    created_at = Column(DateTime)

    __table_args__ = (
        # Ensure only one daily and one weekly entry per date
        Index('ix_hacker_news_insights_date_period', 'date', 'period', unique=True),
    )


class YouTubeInsightDB(Base):
    """DB Model for YouTube influencer insights."""
    __tablename__ = "youtube_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    period = Column(String(20), default="daily", nullable=False)  # 'daily' or 'weekly'
    videos_json = Column(JSON)   # List of videos with summaries
    trend_summary = Column(Text) # LLM summary of influencer discussions
    key_topics = Column(JSON)    # List of topic strings
    created_at = Column(DateTime)

    __table_args__ = (
        Index('ix_youtube_insights_date_period', 'date', 'period', unique=True),
    )


class TopicAnalysisDB(Base):
    """DB Model for Google Trends topic validation results."""
    __tablename__ = "topic_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # 'producthunt', 'hackernews', 'youtube', 'newsletter'
    source_date = Column(Date, nullable=False)
    topics_json = Column(JSON)              # List of TrendValidation dicts
    top_builder_topics = Column(JSON)       # List of topic strings for builders
    top_founder_topics = Column(JSON)       # List of topic strings for founders
    summary = Column(Text)                  # Brief summary of validated trends
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        # One analysis per source per date
        Index('ix_topic_analyses_source_date', 'source', 'source_date', unique=True),
    )


class DiscoveryBriefingDB(Base):
    """DB Model for Saturday viral app discovery briefings."""
    __tablename__ = "discovery_briefings"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)  # One briefing per Saturday
    opportunities_json = Column(JSON)          # List of AppOpportunity dicts
    pain_points_json = Column(JSON)            # List of raw PainPoint dicts
    total_data_points = Column(Integer)
    total_pain_points = Column(Integer)
    total_candidates = Column(Integer)
    arcade_calls = Column(Integer)
    serpapi_calls = Column(Integer)
    youtube_quota = Column(Integer)
    llm_calls = Column(Integer)
    estimated_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.now)


def get_session():
    """Get a new database session."""
    return SessionLocal()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine, checkfirst=True)
