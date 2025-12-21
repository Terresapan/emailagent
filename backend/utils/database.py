"""Database utilities for saving digests and emails."""
import os
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Check if database is configured
DATABASE_URL = os.getenv("DATABASE_URL")

# Define models inline (same schema as api/models.py)
Base = declarative_base()


class DigestModel(Base):
    """Processed digest containing briefing and LinkedIn content."""
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    digest_type = Column(String(20), default="daily", nullable=False, index=True)  # 'daily' or 'weekly'
    briefing = Column(Text)
    linkedin_content = Column(Text)
    newsletter_summaries = Column(Text)
    emails_processed = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    emails = relationship("EmailModel", back_populates="digest")


class EmailModel(Base):
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

    digest = relationship("DigestModel", back_populates="emails")


def save_to_database(emails: List, digest, digest_type: str = "daily") -> Optional[int]:
    """
    Save raw emails and processed digest to PostgreSQL database.
    
    Args:
        emails: List of Email objects (raw emails)
        digest: DailyDigest or WeeklyDeepDive object with processed content
        digest_type: Either 'daily' or 'weekly'
        
    Returns:
        Digest ID if saved successfully, None otherwise
    """
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set, skipping database save")
        return None
    
    try:
        logger.info("Connecting to database...")
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Handle both DailyDigest (newsletter_summaries) and WeeklyDeepDive (deepdive_summaries)
            summaries = getattr(digest, 'newsletter_summaries', None) or getattr(digest, 'deepdive_summaries', '')
            linkedin = getattr(digest, 'linkedin_content', None) or ''
            
            # Create digest record
            digest_record = DigestModel(
                date=datetime.fromisoformat(digest.date).date(),
                digest_type=digest_type,
                briefing=digest.aggregated_briefing,
                linkedin_content=linkedin,
                newsletter_summaries=summaries,
                emails_processed=digest.emails_processed,
            )
            session.add(digest_record)
            session.flush()  # Get the ID
            
            # Save raw emails
            for email in emails:
                email_record = EmailModel(
                    gmail_id=email.id,
                    sender=email.sender,
                    subject=email.subject,
                    body=email.body,
                    digest_id=digest_record.id,
                )
                session.add(email_record)
            
            session.commit()
            logger.info(f"✓ Saved {digest_type} digest (ID: {digest_record.id}) and {len(emails)} emails to database")
            return digest_record.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Failed to save to database: {e}")
        return None

