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
    UsageStatsResponse,
    # Discovery schemas
    PainPointResponse,
    AppOpportunityResponse,
    DiscoveryBriefingResponse,
    DiscoveryStatsResponse,
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
    allow_origins=["*"],
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
# DISCOVERY ENDPOINTS (Viral App Discovery)
# =============================================================================

# In-memory cache for running discovery (cleared after each run)
_last_discovery_briefing = None

@app.get("/api/discovery/briefing", response_model=DiscoveryBriefingResponse)
async def get_latest_discovery_briefing(db: Session = Depends(get_db)):
    """
    Get the most recent Saturday discovery briefing from database.
    
    Returns the top 20 app opportunities with scores.
    """
    from utils.database import get_latest_discovery_briefing as db_get_latest
    from db import DiscoveryBriefingDB
    
    # Try to get from database first
    briefing_db = db.query(DiscoveryBriefingDB).order_by(
        DiscoveryBriefingDB.date.desc()
    ).first()
    
    if briefing_db is None:
        raise HTTPException(
            status_code=404, 
            detail="No discovery briefing found. Run POST /api/discovery/run or use the CLI."
        )
    
    # Convert database record to response format
    opportunities = []
    for opp_data in (briefing_db.opportunities_json or []):
        pain_points = [
            PainPointResponse(
                text=pp.get("text", ""),
                problem=pp.get("problem", ""),
                source=pp.get("source", ""),
                engagement=pp.get("engagement", 0),
            )
            for pp in opp_data.get("pain_points", [])
        ]
        opportunities.append(AppOpportunityResponse(
            problem=opp_data.get("problem", ""),
            app_idea=opp_data.get("app_idea", ""),
            demand_score=opp_data.get("demand_score", 0),
            virality_score=opp_data.get("virality_score", 0),
            buildability_score=opp_data.get("buildability_score", 0),
            opportunity_score=opp_data.get("opportunity_score", 0),
            category=opp_data.get("category", ""),
            target_audience=opp_data.get("target_audience", ""),
            pain_points=pain_points,
        ))
    
    return DiscoveryBriefingResponse(
        date=briefing_db.date,
        top_opportunities=opportunities,
        total_data_points=briefing_db.total_data_points or 0,
        total_pain_points_extracted=briefing_db.total_pain_points or 0,
        total_candidates_filtered=briefing_db.total_candidates or 0,
        arcade_calls=briefing_db.arcade_calls or 0,
        serpapi_calls=briefing_db.serpapi_calls or 0,
        youtube_quota=briefing_db.youtube_quota or 0,
        llm_calls=briefing_db.llm_calls or 0,
        estimated_cost=briefing_db.estimated_cost or 0.0,
    )


@app.get("/api/discovery/videos")
async def get_discovery_videos(db: Session = Depends(get_db)):
    """
    Get YouTube videos collected during discovery.
    
    Returns list of viral videos with titles, views, and links.
    """
    from db import DiscoveryBriefingDB
    
    briefing_db = db.query(DiscoveryBriefingDB).order_by(
        DiscoveryBriefingDB.date.desc()
    ).first()
    
    if briefing_db is None or not briefing_db.youtube_videos_json:
        return {"videos": [], "message": "No video data available"}
    
    return {
        "videos": briefing_db.youtube_videos_json,
        "date": briefing_db.date,
        "count": len(briefing_db.youtube_videos_json),
    }


@app.get("/api/discovery/trends")
async def get_discovery_trends(db: Session = Depends(get_db)):
    """
    Get Google Trends validation data from discovery.
    
    Returns keywords with interest scores and related queries.
    """
    from db import DiscoveryBriefingDB
    
    briefing_db = db.query(DiscoveryBriefingDB).order_by(
        DiscoveryBriefingDB.date.desc()
    ).first()
    
    if briefing_db is None or not briefing_db.trends_data_json:
        return {"trends": [], "message": "No trends data available"}
    
    return {
        "trends": briefing_db.trends_data_json,
        "date": briefing_db.date,
        "count": len(briefing_db.trends_data_json),
    }


@app.post("/api/discovery/run", response_model=DiscoveryBriefingResponse)
async def run_discovery():
    """
    Trigger the Saturday discovery workflow.
    
    This runs the full 4-phase discovery:
    1. Collect data (200 Arcade + free APIs)
    2. Extract pain points (5 LLM calls)
    3. Filter candidates (1 LLM call)
    4. Validate + Score (120 SerpAPI + 1 LLM call)
    
    Returns the briefing with top 20 opportunities.
    
    WARNING: This is a long-running operation (~5-10 minutes).
    """
    global _last_discovery_briefing
    
    import sys
    sys.path.insert(0, '/app')
    
    try:
        from processor.viral_app.graph import run_saturday_discovery
        
        logger.info("Starting discovery workflow...")
        briefing = run_saturday_discovery()
        
        # Store for later retrieval
        _last_discovery_briefing = briefing
        
        # Convert to response
        opportunities = []
        for opp in briefing.top_opportunities:
            pain_points = [
                PainPointResponse(
                    text=pp.text,
                    problem=pp.problem,
                    source=pp.source,
                    engagement=pp.engagement,
                )
                for pp in opp.pain_points
            ]
            opportunities.append(AppOpportunityResponse(
                problem=opp.problem,
                app_idea=opp.app_idea,
                demand_score=opp.demand_score,
                virality_score=opp.virality_score,
                buildability_score=opp.buildability_score,
                opportunity_score=opp.opportunity_score,
                category=opp.category,
                target_audience=opp.target_audience,
                pain_points=pain_points,
            ))
        
        return DiscoveryBriefingResponse(
            date=briefing.date,
            top_opportunities=opportunities,
            total_data_points=briefing.total_data_points,
            total_pain_points_extracted=briefing.total_pain_points_extracted,
            total_candidates_filtered=briefing.total_candidates_filtered,
            arcade_calls=briefing.arcade_calls,
            serpapi_calls=briefing.serpapi_calls,
            youtube_quota=briefing.youtube_quota,
            llm_calls=briefing.llm_calls,
            estimated_cost=briefing.estimated_cost,
        )
        
    except Exception as e:
        logger.error(f"Discovery workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@app.get("/api/discovery/stats", response_model=DiscoveryStatsResponse)
async def get_discovery_stats():
    """
    Get API usage statistics for discovery.
    
    Returns usage for Arcade, SerpAPI, YouTube, and LLM.
    """
    import sys
    sys.path.insert(0, '/app')
    
    from sources.arcade_client import ArcadeClient
    from sources.google_trends import GoogleTrendsClient
    
    # Get stats from clients
    try:
        arcade_client = ArcadeClient()
        arcade_stats = arcade_client.get_usage_stats()
    except Exception:
        arcade_stats = {"error": "Not configured"}
    
    try:
        trends_client = GoogleTrendsClient()
        serpapi_stats = trends_client.get_usage_stats()
    except Exception:
        serpapi_stats = {"error": "Not configured"}
    
    global _last_discovery_briefing
    last_run = _last_discovery_briefing.date if _last_discovery_briefing else None
    
    return DiscoveryStatsResponse(
        arcade=arcade_stats,
        serpapi=serpapi_stats,
        youtube={"quota_per_day": 10000, "note": "Free tier"},
        llm={"calls_per_run": 7, "estimated_cost_per_run": 0.13},
        last_run=last_run,
    )


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

