"""FastAPI backend for Content Agent dashboard."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
    ProcessStatusResponse,
)

# In-memory process status tracking
process_status = {
    "status": "idle",
    "started_at": None,
    "completed_at": None,
    "emails_found": None,
    "message": None,
}

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
async def trigger_process(
    digest_type: str = "dailydigest",
    dry_run: bool = False
):
    """
    Manually trigger email processing.
    
    Args:
        digest_type: Either 'dailydigest' or 'weeklydeepdives'
        dry_run: If True, preview only without modifying emails
        
    Returns:
        ProcessResponse with status and message
    """
    import docker
    import threading
    
    if digest_type not in ["dailydigest", "weeklydeepdives"]:
        return ProcessResponse(
            status="error",
            message=f"Invalid digest_type: {digest_type}. Use 'dailydigest' or 'weeklydeepdives'",
            digest_id=None,
        )
    
    # Build command - redirect output to cron.log so manual runs are logged same as scheduled
    cmd = f"uv run python main.py --type {digest_type}"
    if dry_run:
        cmd += " --dry-run"
    # Append output to cron.log (same as cron job)
    cmd += " >> /var/log/emailagent/cron.log 2>&1"
    
    try:
        # Connect to Docker daemon via mounted socket
        client = docker.from_env()
        container = client.containers.get("emailagent")
        
        # Update status to running
        process_status["status"] = "running"
        process_status["started_at"] = datetime.utcnow()
        process_status["completed_at"] = None
        process_status["emails_found"] = None
        process_status["message"] = f"Processing {digest_type}..."
        
        # Run command in background thread (non-blocking)
        # Use /bin/bash -c to handle the shell redirect properly
        def run_exec():
            try:
                # Run the command and capture output for status detection
                result = container.exec_run(
                    f"/bin/bash -c '{cmd}'",
                    detach=False
                )
                
                # Check log file for result (last few lines)
                log_result = container.exec_run(
                    "tail -20 /var/log/emailagent/cron.log"
                )
                log_output = log_result.output.decode('utf-8') if log_result.output else ""
                
                # Parse log for email count
                import re
                no_emails = "No unread" in log_output or "Found 0 unread" in log_output
                email_match = re.search(r'Found (\d+) unread emails', log_output)
                emails_found = int(email_match.group(1)) if email_match else 0
                
                # Update status
                process_status["completed_at"] = datetime.utcnow()
                process_status["emails_found"] = emails_found
                
                if no_emails or emails_found == 0:
                    process_status["status"] = "no_emails"
                    process_status["message"] = "No unread emails found to process"
                else:
                    process_status["status"] = "completed"
                    process_status["message"] = f"Processed {emails_found} emails successfully"
                
                print(f"Process completed: {process_status['status']} ({emails_found} emails)")
                
            except Exception as e:
                process_status["status"] = "error"
                process_status["completed_at"] = datetime.utcnow()
                process_status["message"] = str(e)
                print(f"Exec error: {e}")
        
        thread = threading.Thread(target=run_exec)
        thread.start()
        
        return ProcessResponse(
            status="started",
            message=f"Processing {digest_type} started. Check dashboard in ~2-3 minutes.",
            digest_id=None,
        )
        
    except docker.errors.NotFound:
        return ProcessResponse(
            status="error",
            message="emailagent container not found. Is it running?",
            digest_id=None,
        )
    except Exception as e:
        return ProcessResponse(
            status="error",
            message=f"Failed to start processing: {str(e)}",
            digest_id=None,
        )


@app.get("/api/process/status", response_model=ProcessStatusResponse)
async def get_process_status():
    """Get the status of the last/current process run."""
    return ProcessStatusResponse(**process_status)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

