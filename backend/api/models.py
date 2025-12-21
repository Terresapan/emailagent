"""SQLAlchemy models for email and digest storage."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class Digest(Base):
    """Processed digest containing briefing and LinkedIn content."""
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    digest_type = Column(String(20), default="daily", nullable=False, index=True)  # 'daily' or 'weekly'
    briefing = Column(Text)
    linkedin_content = Column(Text)
    newsletter_summaries = Column(Text)
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
