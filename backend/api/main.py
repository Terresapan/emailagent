"""FastAPI backend for Content Agent dashboard."""
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import get_db, init_db
from models import Digest, Email
from schemas import (
    DigestResponse,
    DigestWithEmails,
    EmailResponse,
    HealthResponse,
    ProcessResponse,
)

app = FastAPI(
    title="Content Agent API",
    description="API for viewing AI-generated briefings and LinkedIn content",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://dashboard:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/api/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection (SQLAlchemy 2.x syntax)
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        database=db_status,
    )


@app.get("/api/digest/latest", response_model=Optional[DigestWithEmails])
async def get_latest_digest(
    digest_type: str = "daily",
    db: Session = Depends(get_db)
):
    """Get the most recent digest with associated emails, filtered by type."""
    digest = (
        db.query(Digest)
        .filter(Digest.digest_type == digest_type)
        .order_by(desc(Digest.created_at))
        .first()
    )
    
    if not digest:
        return None
    
    return digest


@app.get("/api/digest/history", response_model=List[DigestResponse])
async def get_digest_history(
    limit: int = 10,
    offset: int = 0,
    digest_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get paginated digest history, optionally filtered by type."""
    query = db.query(Digest)
    
    if digest_type:
        query = query.filter(Digest.digest_type == digest_type)
    
    digests = (
        query
        .order_by(desc(Digest.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return digests


@app.get("/api/digest/{digest_id}", response_model=DigestWithEmails)
async def get_digest_by_id(digest_id: int, db: Session = Depends(get_db)):
    """Get a specific digest by ID with associated emails."""
    digest = db.query(Digest).filter(Digest.id == digest_id).first()
    
    if not digest:
        raise HTTPException(status_code=404, detail="Digest not found")
    
    return digest


@app.get("/api/emails", response_model=List[EmailResponse])
async def get_emails(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get paginated list of raw emails."""
    emails = (
        db.query(Email)
        .order_by(desc(Email.processed_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return emails


@app.get("/api/emails/{email_id}", response_model=EmailResponse)
async def get_email_by_id(email_id: int, db: Session = Depends(get_db)):
    """Get a specific email by ID."""
    email = db.query(Email).filter(Email.id == email_id).first()
    
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return email


@app.post("/api/process", response_model=ProcessResponse)
async def trigger_process():
    """
    Manually trigger email processing.
    
    Note: In production, this would call the emailagent processing logic.
    For now, returns a placeholder response.
    """
    # TODO: Integrate with emailagent main.py processing
    return ProcessResponse(
        status="pending",
        message="Manual processing not yet implemented. Use the cron scheduler.",
        digest_id=None,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
