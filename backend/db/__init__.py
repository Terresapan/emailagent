"""Shared database models and connection management.

This package provides:
- SQLAlchemy models (Digest, Email)
- Database connection with connection pooling
- Session management for both API and emailagent
"""
import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
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
    created_at = Column(DateTime, default=datetime.utcnow)

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
    processed_at = Column(DateTime, default=datetime.utcnow)
    digest_id = Column(Integer, ForeignKey("digests.id"))

    # Relationship to digest
    digest = relationship("Digest", back_populates="emails")


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
    Base.metadata.create_all(bind=engine)
