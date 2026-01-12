"""
Shared Trend Validation Service.

Consolidates trend validation logic used by both:
- main.py (cron jobs)
- api/main.py (dashboard API)
"""
import json
import logging
from datetime import datetime
from typing import Optional, Literal

from sqlalchemy.orm import Session

from db import TopicAnalysisDB, ProductHuntInsightDB, YouTubeInsightDB, Digest
from processor.google_trend.graph import TrendGraph
from sources.models import TopicAnalysis

logger = logging.getLogger(__name__)


class TrendValidationService:
    """
    Service for running trend validation on content sources.
    
    Abstracts the common logic for:
    - Determining daily vs weekly mode based on day of week
    - Gathering inputs from database
    - Running the TrendGraph
    - Saving results to TopicAnalysisDB
    """
    
    def __init__(self, session: Session):
        self.session = session
        self.graph = TrendGraph()
    
    def run(self, force: bool = False) -> Optional[TopicAnalysis]:
        """
        Run trend validation based on day of week.
        
        Args:
            force: If True, run even on Saturday (for testing)
            
        Returns:
            TopicAnalysis object if successful, None otherwise
        """
        today = datetime.now()
        day_of_week = today.weekday()
        
        # Skip Saturday unless forced
        if day_of_week == 5 and not force:
            logger.info("Saturday - Skipping trend validation")
            return None
        
        is_sunday = day_of_week == 6
        source_type: Literal["daily", "weekly"] = "weekly" if is_sunday else "daily"
        
        logger.info(f"Running trend validation ({source_type})")
        
        # Build inputs from database
        inputs = self._build_inputs(is_sunday)
        
        if not inputs:
            logger.warning("No content found to analyze")
            return None
        
        # Run TrendGraph
        analysis = self.graph.process(inputs, source_type=source_type)
        
        if not analysis:
            logger.error("TrendGraph returned None")
            return None
        
        # Save to database
        self._save_to_db(analysis, today)
        
        return analysis
    
    def _build_inputs(self, is_sunday: bool) -> list[dict]:
        """Build inputs list from database based on day of week."""
        inputs = []
        
        if is_sunday:
            # SUNDAY: Weekly sources
            
            # 1. Newsletter Deep Dive (weekly)
            logger.info("Extracting from Weekly Newsletter Deep Dive...")
            weekly_digest = self.session.query(Digest).filter(
                Digest.digest_type == "weekly"
            ).order_by(Digest.date.desc()).first()
            if weekly_digest and weekly_digest.newsletter_summaries:
                inputs.append({
                    "source": "weekly_newsletter",
                    "content": weekly_digest.newsletter_summaries
                })
            
            # 2. Product Hunt Weekly
            logger.info("Extracting from Weekly Product Hunt...")
            ph_weekly = self.session.query(ProductHuntInsightDB).filter(
                ProductHuntInsightDB.period == "weekly"
            ).order_by(ProductHuntInsightDB.date.desc()).first()
            if ph_weekly and ph_weekly.launches_json:
                content = json.dumps(ph_weekly.launches_json[:10], default=str)
                inputs.append({
                    "source": "weekly_producthunt",
                    "content": content
                })
            
            # 3. YouTube Weekly
            logger.info("Extracting from Weekly YouTube...")
            yt_weekly = self.session.query(YouTubeInsightDB).filter(
                YouTubeInsightDB.period == "weekly"
            ).order_by(YouTubeInsightDB.date.desc()).first()
            if yt_weekly:
                content = f"Topics: {yt_weekly.key_topics}\nSummary: {yt_weekly.trend_summary}"
                inputs.append({
                    "source": "weekly_youtube",
                    "content": content
                })
        
        else:
            # MON-FRI: Daily sources
            
            # 1. Newsletter (daily)
            logger.info("Extracting from Daily Newsletter...")
            daily_digest = self.session.query(Digest).filter(
                Digest.digest_type == "daily"
            ).order_by(Digest.date.desc()).first()
            if daily_digest and daily_digest.newsletter_summaries:
                inputs.append({
                    "source": "newsletter",
                    "content": daily_digest.newsletter_summaries
                })
            
            # 2. Product Hunt (daily)
            logger.info("Extracting from Daily Product Hunt...")
            ph_daily = self.session.query(ProductHuntInsightDB).filter(
                ProductHuntInsightDB.period == "daily"
            ).order_by(ProductHuntInsightDB.date.desc()).first()
            if ph_daily and ph_daily.launches_json:
                content = json.dumps(ph_daily.launches_json[:10], default=str)
                inputs.append({
                    "source": "producthunt",
                    "content": content
                })
            
            # 3. YouTube (daily)
            logger.info("Extracting from Daily YouTube...")
            yt_daily = self.session.query(YouTubeInsightDB).filter(
                YouTubeInsightDB.period == "daily"
            ).order_by(YouTubeInsightDB.date.desc()).first()
            if yt_daily:
                content = f"Topics: {yt_daily.key_topics}\nSummary: {yt_daily.trend_summary}"
                inputs.append({
                    "source": "youtube",
                    "content": content
                })
        
        return inputs
    
    def _save_to_db(self, analysis: TopicAnalysis, today: datetime) -> None:
        """Save analysis to database, replacing existing if present."""
        # Delete existing entry for today
        existing = self.session.query(TopicAnalysisDB).filter(
            TopicAnalysisDB.source == "global",
            TopicAnalysisDB.source_date == today.date()
        ).first()
        if existing:
            self.session.delete(existing)
            self.session.commit()
        
        # Create new entry
        db_obj = TopicAnalysisDB(
            source="global",
            source_date=today.date(),
            topics_json=[t.model_dump(mode='json') for t in analysis.topics],
            top_builder_topics=analysis.top_technical_topics,  # Map technical -> builder
            top_founder_topics=analysis.top_strategic_topics,  # Map strategic -> founder
            summary=analysis.summary,
            created_at=datetime.utcnow()
        )
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        
        logger.info(f"Saved analysis to database with ID: {db_obj.id}")
