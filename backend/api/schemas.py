"""Pydantic schemas for API request/response validation."""
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel


class EmailBase(BaseModel):
    """Base email schema."""
    gmail_id: str
    sender: str
    subject: str
    body: str
    received_at: Optional[datetime] = None


class EmailResponse(EmailBase):
    """Email response with database fields."""
    id: int
    processed_at: datetime
    digest_id: Optional[int] = None

    class Config:
        from_attributes = True


class DigestBase(BaseModel):
    """Base digest schema."""
    date: date
    digest_type: Optional[str] = "daily"  # 'daily' or 'weekly'
    briefing: Optional[str] = None
    linkedin_content: Optional[str] = None
    newsletter_summaries: Optional[str] = None
    structured_digests: Optional[List[dict]] = None
    emails_processed: Optional[List[str]] = None


class DigestResponse(DigestBase):
    """Digest response with database fields."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DigestWithEmails(DigestResponse):
    """Digest response including associated emails."""
    emails: List[EmailResponse] = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    database: str


class ProcessResponse(BaseModel):
    """Response from manual process trigger."""
    status: str
    message: str
    digest_id: Optional[int] = None


class ProcessStatusResponse(BaseModel):
    """Status of the last process run."""
    status: str  # 'idle', 'running', 'completed', 'no_emails'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    emails_found: Optional[int] = None
    message: Optional[str] = None
