"""FastAPI backend for Content Agent dashboard."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Import logger for consistent logging
import logging
logger = logging.getLogger(__name__)

# CORS origins from environment variable (comma-separated)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://dashboard:3000").split(",")

from database import get_db, init_db
from models import Digest, Email
from db import ProductHuntInsightDB
from schemas import (
    DigestResponse,
    DigestWithEmails,
    EmailResponse,
    HealthResponse,
    ProcessResponse,
    ProcessStatusResponse,
    ProductHuntInsightResponse,
    ProductHuntLaunchResponse,
    HackerNewsInsightResponse,
    HackerNewsStoryResponse,
    YouTubeInsightResponse,
    YouTubeInsightResponse,
    YouTubeVideoResponse,
    TopicAnalysisResponse,
    TrendValidationResponse,
    UsageStatsResponse,
)

# In-memory process status tracking
process_status = {
    "status": "idle",
    "started_at": None,
    "completed_at": None,
    "emails_found": None,
    "message": None,
}

# Lifespan context manager (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield

app = FastAPI(
    title="Content Agent API",
    description="API for viewing AI-generated briefings and LinkedIn content",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        timestamp=datetime.now(),  # Local time (TZ=America/Los_Angeles)
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


@app.get("/api/tools/latest", response_model=Optional[ProductHuntInsightResponse])
async def get_latest_tools_insight(
    period: str = "daily",
    db: Session = Depends(get_db)
):
    """Get the most recent Product Hunt insight for AI tools, filtered by period."""
    insight = (
        db.query(ProductHuntInsightDB)
        .filter(ProductHuntInsightDB.period == period)
        .order_by(ProductHuntInsightDB.created_at.desc())
        .first()
    )
    
    if not insight:
        return None
    
    # Transform launches_json to response format
    launches = [
        ProductHuntLaunchResponse(
            id=l.get("id", ""),
            name=l.get("name", "Unknown"),
            tagline=l.get("tagline", ""),
            votes=l.get("votes", 0),
            website=l.get("website"),
            topics=l.get("topics", []),
        )
        for l in (insight.launches_json or [])
    ]
    
    return ProductHuntInsightResponse(
        id=insight.id,
        date=insight.date,
        launches=launches,
        trend_summary=insight.trend_summary,
        content_angles=insight.content_angles or [],
        period=insight.period,
        created_at=insight.created_at or datetime.now(),
    )


@app.get("/api/hackernews/latest", response_model=Optional[HackerNewsInsightResponse])
async def get_latest_hackernews_insight(
    period: str = "daily",
    db: Session = Depends(get_db)
):
    """Get the most recent Hacker News insight, filtered by period."""
    from db import HackerNewsInsightDB
    
    insight = (
        db.query(HackerNewsInsightDB)
        .filter(HackerNewsInsightDB.period == period)
        .order_by(HackerNewsInsightDB.created_at.desc())
        .first()
    )
    
    if not insight:
        return None
    
    # Transform stories_json to response format
    stories = [
        HackerNewsStoryResponse(
            id=s.get("id", ""),
            title=s.get("title", "Unknown"),
            url=s.get("url"),
            score=s.get("score", 0),
            comments_count=s.get("comments_count", 0),
            by=s.get("by"),
            verdict=s.get("verdict"),
            sentiment=s.get("sentiment"),
            github_stars=s.get("github_stars"),
        )
        for s in (insight.stories_json or [])
    ]
    
    return HackerNewsInsightResponse(
        id=insight.id,
        date=insight.date,
        stories=stories,
        summary=insight.summary,
        top_themes=insight.top_themes or [],
        created_at=insight.created_at,
        period=getattr(insight, 'period', 'daily')
    )


@app.get("/api/youtube/latest", response_model=Optional[YouTubeInsightResponse])
async def get_latest_youtube_insight(
    period: str = "daily",
    db: Session = Depends(get_db)
):
    """Get the most recent YouTube influencer insight, filtered by period."""
    from db import YouTubeInsightDB
    
    insight = (
        db.query(YouTubeInsightDB)
        .filter(YouTubeInsightDB.period == period)
        .order_by(YouTubeInsightDB.created_at.desc())
        .first()
    )
    
    if not insight:
        return None
    
    # Transform videos_json to response format
    videos = [
        YouTubeVideoResponse(
            id=v.get("id", ""),
            title=v.get("title", "Unknown"),
            channel_name=v.get("channel_name", "Unknown"),
            channel_id=v.get("channel_id", ""),
            description=v.get("description"),
            view_count=v.get("view_count", 0),
            published_at=v.get("published_at"),
            summary=v.get("summary"),
        )
        for v in (insight.videos_json or [])
    ]
    
    return YouTubeInsightResponse(
        id=insight.id,
        date=insight.date,
        videos=videos,
        trend_summary=insight.trend_summary,
        key_topics=insight.key_topics or [],
        created_at=insight.created_at or datetime.now(),
        period=insight.period,
    )


# =============================================================================
# TOPIC ANALYSIS ENDPOINTS (Google Trends Validation)
# =============================================================================

@app.get("/api/analysis/latest")
async def get_latest_analysis(
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get the most recent topic analysis, optionally filtered by source.
    
    If specific source requested (e.g. 'newsletter') and not found, 
    filter from latest 'global' analysis.
    """
    from db import TopicAnalysisDB
    from schemas import TopicAnalysisResponse, TrendValidationResponse
    
    query = db.query(TopicAnalysisDB)
    
    # Try exact match first
    if source:
        query = query.filter(TopicAnalysisDB.source == source)
    
    analysis = query.order_by(TopicAnalysisDB.created_at.desc()).first()
    
    # Fallback: If specific source requested but not found, check global
    if not analysis and source and source != "global":
        global_analysis = db.query(TopicAnalysisDB).filter(
            TopicAnalysisDB.source == "global"
        ).order_by(TopicAnalysisDB.created_at.desc()).first()
        
        if global_analysis:
            # Filter topics by content_source
            # Handle source mapping (e.g. 'newsletter' should match 'newsletter' and 'weekly_newsletter')
            filtered_topics = []
            for t in (global_analysis.topics_json or []):
                content_source = t.get('content_source', '')
                if not content_source: 
                    continue
                    
                # Loose matching to handle weekly variants
                if source in content_source:
                    filtered_topics.append(t)
            
            if filtered_topics:
                # Return partial view of global analysis
                return TopicAnalysisResponse(
                    id=global_analysis.id,
                    source=source, # Pretend it's the requested source
                    source_date=global_analysis.source_date,
                    topics=[TrendValidationResponse(**t) for t in filtered_topics],
                    top_builder_topics=global_analysis.top_builder_topics or [],
                    top_founder_topics=global_analysis.top_founder_topics or [],
                    summary=global_analysis.summary, # Keep global summary
                    created_at=global_analysis.created_at,
                )
    
    if not analysis:
        return None
    
    # Transform topics_json to response format
    topics = [
        TrendValidationResponse(**t) for t in (analysis.topics_json or [])
    ]
    
    return TopicAnalysisResponse(
        id=analysis.id,
        source=analysis.source,
        source_date=analysis.source_date,
        topics=topics,
        top_builder_topics=analysis.top_builder_topics or [],
        top_founder_topics=analysis.top_founder_topics or [],
        summary=analysis.summary,
        created_at=analysis.created_at,
    )


@app.get("/api/analysis/history")
async def get_analysis_history(
    source: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get paginated topic analysis history."""
    from db import TopicAnalysisDB
    from schemas import TopicAnalysisResponse, TrendValidationResponse
    
    query = db.query(TopicAnalysisDB)
    
    if source:
        query = query.filter(TopicAnalysisDB.source == source)
    
    analyses = query.order_by(TopicAnalysisDB.created_at.desc()).limit(limit).all()
    
    results = []
    for analysis in analyses:
        topics = [
            TrendValidationResponse(**t) for t in (analysis.topics_json or [])
        ]
        results.append(TopicAnalysisResponse(
            id=analysis.id,
            source=analysis.source,
            source_date=analysis.source_date,
            topics=topics,
            top_builder_topics=analysis.top_builder_topics or [],
            top_founder_topics=analysis.top_founder_topics or [],
            summary=analysis.summary,
            created_at=analysis.created_at,
        ))
    
    return results


@app.post("/api/analysis/validate", response_model=TopicAnalysisResponse)
async def validate_topics(
    topics: Optional[str] = None,
    source: str = Query(..., description="Source type: 'producthunt', 'hackernews', 'youtube', 'newsletter', 'manual', or 'all'"),
    force: bool = Query(False, description="Force run even on Saturday (for manual testing)"),
    db: Session = Depends(get_db)
):
    """
    Trigger validation for topics.
    
    If source is 'all', runs validation for all available sources (reads latest insights from DB),
    aggregates results, and sends an email report.
    """
    import sys
    sys.path.insert(0, '/app')
    
    from db import TopicAnalysisDB
    from schemas import TopicAnalysisResponse, TrendValidationResponse
    
    if source == "all":
        from processor.google_trend.trend_validation import TrendValidationService
        
        today = datetime.now()
        day_of_week = today.weekday()
        
        # Saturday skip (unless forced)
        if day_of_week == 5 and not force:
            return TopicAnalysisResponse(
                id=0,
                source="global",
                source_date=today.date(),
                topics=[],
                top_technical_topics=[],
                top_strategic_topics=[],
                summary="Saturday - No validation scheduled (use force=true to override)",
                created_at=today
            )
        
        # Run shared validation service
        service = TrendValidationService(db)
        analysis = service.run(force=force)
        
        if not analysis:
            return TopicAnalysisResponse(
                id=0,
                source="global",
                source_date=today.date(),
                topics=[],
                top_builder_topics=[],
                top_founder_topics=[],
                summary="No content found to analyze",
                created_at=today
            )
        
        # Send email
        try:
            from sources.gmail.client import GmailClient
            gmail = GmailClient()
            gmail.send_analysis_email([analysis])
        except Exception as e:
            print(f"Failed to send email: {e}")
        
        # Get the saved DB object for response
        db_obj = db.query(TopicAnalysisDB).filter(
            TopicAnalysisDB.source == "global",
            TopicAnalysisDB.source_date == today.date()
        ).first()
        
        if not db_obj:
            # Fallback if not found (shouldn't happen)
            return TopicAnalysisResponse(
                id=0,
                source="global",
                source_date=today.date(),
                topics=[TrendValidationResponse(**t.model_dump()) for t in analysis.topics],
                top_technical_topics=analysis.top_technical_topics,
                top_strategic_topics=analysis.top_strategic_topics,
                summary=analysis.summary,
                created_at=today
            )
        
        return TopicAnalysisResponse(
            id=db_obj.id,
            source=db_obj.source,
            source_date=db_obj.source_date,
            topics=[TrendValidationResponse(**t) for t in db_obj.topics_json],
            top_technical_topics=db_obj.top_builder_topics or [],
            top_strategic_topics=db_obj.top_founder_topics or [],
            summary=db_obj.summary,
            created_at=db_obj.created_at
        )

    # Manual validation logic
    if not topics:
         raise HTTPException(status_code=400, detail="No topics provided")

    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
    
    if not topic_list:
        raise HTTPException(status_code=400, detail="No topics provided")
    
    if len(topic_list) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 topics allowed per request")
    
    # Run manual validation via simple Service or Graph?
    # Graph expects inputs with source/content. We can mock it or just use simple validation service?
    # Or better: Add a manual entry point to Graph or just use the old service logic (which is being deprecated).
    # Let's adapt the Graph for manual input?
    # Currently Graph extracts -> ranks -> validates.
    # We just want validate.
    # The old service had validate_and_analyze(source, topics).
    # Since we are deprecating the service, we should probably use the Graph or key components.
    # But for now, to keep it simple and given the user asked for graph refactor for the main flow:
    # I will instantiate GoogleTrendsClient directly for manual mode, similar to what the service did.
    
    from sources.google_trends import GoogleTrendsClient
    from sources.models import TopicAnalysis, TrendValidation
    
    trends = GoogleTrendsClient()
    validations = trends.validate_topics_batch(topic_list)
    
    # Construct rudimentary analysis
    analysis = TopicAnalysis(
        source=source,
        source_date=datetime.now().date(),
        topics=validations,
        top_builder_topics=[],
        top_founder_topics=[],
        summary=f"Manual validation of {len(validations)} topics"
    )
    
    # Save to database
    # Check for existing manual run today
    existing = db.query(TopicAnalysisDB).filter(
        TopicAnalysisDB.source == analysis.source,
        TopicAnalysisDB.source_date == analysis.source_date
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()  # Flush delete before inserting new record
        
    db_analysis = TopicAnalysisDB(
        source=analysis.source,
        source_date=analysis.source_date,
        topics_json=[t.model_dump(mode='json') for t in analysis.topics],
        top_builder_topics=analysis.top_builder_topics,
        top_founder_topics=analysis.top_founder_topics,
        summary=analysis.summary,
        created_at=analysis.created_at,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    return TopicAnalysisResponse(
        id=db_analysis.id,
        source=db_analysis.source,
        source_date=db_analysis.source_date,
        topics=[TrendValidationResponse(**t.model_dump()) for t in analysis.topics],
        top_builder_topics=db_analysis.top_builder_topics or [],
        top_founder_topics=db_analysis.top_founder_topics or [],
        summary=db_analysis.summary,
        created_at=db_analysis.created_at,
    )


@app.get("/api/analysis/usage")
async def get_trends_usage():
    """Get Google Trends API usage statistics."""
    import sys
    sys.path.insert(0, '/app')
    
    from sources.google_trends import GoogleTrendsClient
    from schemas import UsageStatsResponse
    
    client = GoogleTrendsClient()
    stats = client.get_usage_stats()
    
    return UsageStatsResponse(**stats)


@app.post("/api/process", response_model=ProcessResponse)
async def trigger_process(
    digest_type: str = "dailydigest",
    dry_run: bool = False,
    timeframe: str = "daily"
):
    """
    Manually trigger email processing.
    
    Args:
        digest_type: Either 'dailydigest', 'weeklydeepdives', 'productlaunch', or 'hackernews'
        dry_run: If True, preview only without modifying emails
        timeframe: 'daily' or 'weekly' (relevant for productlaunch/hackernews)
        
    Returns:
        ProcessResponse with status and message
    """
    import docker
    import threading
    
    if digest_type not in ["dailydigest", "weeklydeepdives", "productlaunch", "hackernews", "youtube"]:
        return ProcessResponse(
            status="error",
            message=f"Invalid digest_type: {digest_type}. Use 'dailydigest', 'weeklydeepdives', 'productlaunch', 'hackernews', or 'youtube'",
            digest_id=None,
        )
    
    # Build command - redirect output to cron.log so manual runs are logged same as scheduled
    cmd = f"uv run python main.py --type {digest_type} --timeframe {timeframe}"
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
        process_status["started_at"] = datetime.now()  # Local time
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
                
                # Parse log for result based on process type
                import re
                
                # Check for success markers based on digest type
                success = False
                items_found = 0
                
                # Universal success marker
                completed_successfully = "Email Agent Completed Successfully" in log_output
                
                if digest_type in ["dailydigest", "weeklydeepdives"]:
                    # Email-based: Look for email/essay count
                    # Check both "Found X unread" and "processed X" patterns
                    no_emails = "No unread" in log_output or "Found 0 unread" in log_output
                    
                    # Try multiple patterns
                    found_match = re.search(r'Found (\d+) unread (?:emails|essays)', log_output)
                    processed_match = re.search(r'(?:Emails|Essays) processed: (\d+)', log_output)
                    
                    if processed_match:
                        items_found = int(processed_match.group(1))
                    elif found_match:
                        items_found = int(found_match.group(1))
                    
                    success = (completed_successfully and items_found > 0) or (not no_emails and items_found > 0)
                    
                elif digest_type == "productlaunch":
                    # Product Hunt: Look for launches
                    launch_match = re.search(r'Fetched (\d+) AI launches', log_output)
                    analyzed_match = re.search(r'Analyzed (\d+) top launches', log_output)
                    items_found = int(analyzed_match.group(1)) if analyzed_match else (int(launch_match.group(1)) if launch_match else 0)
                    success = completed_successfully or "Product Hunt Processing Complete" in log_output or items_found > 0
                    
                elif digest_type == "hackernews":
                    # Hacker News: Look for stories (fetched or aggregated)
                    story_match = re.search(r'(?:Fetched|Aggregated|Analyzed) (\d+) (?:stories|unique stories|top stories)', log_output)
                    items_found = int(story_match.group(1)) if story_match else 0
                    success = completed_successfully or "Hacker News Processing Complete" in log_output or items_found > 0
                
                elif digest_type == "youtube":
                    # YouTube: Look for videos analyzed
                    video_match = re.search(r'Analyzed (\d+) videos', log_output)
                    items_found = int(video_match.group(1)) if video_match else 0
                    success = completed_successfully or "YouTube Processing Complete" in log_output or items_found > 0
                
                # Update status
                process_status["completed_at"] = datetime.now()  # Local time
                process_status["emails_found"] = items_found
                
                if success:
                    process_status["status"] = "completed"
                    process_status["message"] = f"Processed {items_found} items successfully"
                else:
                    process_status["status"] = "no_emails"
                    process_status["message"] = "No content found to process"
                
                logger.info(f"Process completed: {process_status['status']} ({items_found} items)")
                
            except Exception as e:
                process_status["status"] = "error"
                process_status["completed_at"] = datetime.now()  # Local time
                process_status["message"] = str(e)
                logger.error(f"Exec error: {e}")
        
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

