"""Database utilities for saving digests and emails.

This module uses the shared db package for models and session management.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from db import Digest as DigestModel, Email as EmailModel, get_session, HackerNewsInsightDB, ProductHuntInsightDB, YouTubeInsightDB, DiscoveryBriefingDB
from sqlalchemy.orm import Session
from sources.models import HackerNewsInsight, ProductHuntInsight, YouTubeInsight
from processor.viral_app.models import SaturdayBriefing
from utils.logger import setup_logger

logger = setup_logger(__name__)


def save_to_database(emails: List, digest, digest_type: str = "daily") -> Optional[int]:
    """
    Save raw emails and processed digest to PostgreSQL database.
    
    Uses UPSERT logic for digests: if a digest already exists for the same
    date and type, it will be updated instead of creating a duplicate.
    
    Args:
        emails: List of Email objects (raw emails)
        digest: DailyDigest or WeeklyDeepDive object with processed content
        digest_type: Either 'daily' or 'weekly'
        
    Returns:
        Digest ID if saved successfully, None otherwise
    """
    try:
        logger.info("Connecting to database...")
        session = get_session()
        
        try:
            # Handle both DailyDigest (newsletter_summaries) and WeeklyDeepDive (deepdive_summaries)
            summaries = getattr(digest, 'newsletter_summaries', None) or getattr(digest, 'deepdive_summaries', '')
            linkedin = getattr(digest, 'linkedin_content', None) or ''
            digest_date = datetime.fromisoformat(digest.date).date()
            
            # UPSERT: Check if digest already exists for this date and type
            existing_digest = session.query(DigestModel).filter_by(
                date=digest_date,
                digest_type=digest_type
            ).first()
            
            if existing_digest:
                # Update existing digest
                logger.info(f"Updating existing {digest_type} digest for {digest_date} (ID: {existing_digest.id})")
                existing_digest.briefing = digest.aggregated_briefing
                existing_digest.linkedin_content = linkedin
                existing_digest.newsletter_summaries = summaries
                existing_digest.structured_digests = [d.model_dump() for d in digest.digests]
                existing_digest.emails_processed = digest.emails_processed
                existing_digest.created_at = datetime.now()  # Update timestamp (local time)
                digest_record = existing_digest
            else:
                # Create new digest record
                logger.info(f"Creating new {digest_type} digest for {digest_date}")
                digest_record = DigestModel(
                    date=digest_date,
                    digest_type=digest_type,
                    briefing=digest.aggregated_briefing,
                    linkedin_content=linkedin,
                    newsletter_summaries=summaries,
                    structured_digests=[d.model_dump() for d in digest.digests],
                    emails_processed=digest.emails_processed,
                )
                session.add(digest_record)
                session.flush()  # Get the ID
            
            # Save raw emails (handle duplicates by gmail_id)
            new_emails_count = 0
            updated_emails_count = 0
            for email in emails:
                existing_email = session.query(EmailModel).filter_by(gmail_id=email.id).first()
                if existing_email:
                    # Update existing email to point to current digest
                    existing_email.digest_id = digest_record.id
                    updated_emails_count += 1
                else:
                    # Create new email record
                    email_record = EmailModel(
                        gmail_id=email.id,
                        sender=email.sender,
                        subject=email.subject,
                        body=email.body,
                        digest_id=digest_record.id,
                    )
                    session.add(email_record)
                    new_emails_count += 1
            
            session.commit()
            logger.info(
                f"✓ Saved {digest_type} digest (ID: {digest_record.id}) | "
                f"Emails: {new_emails_count} new, {updated_emails_count} linked"
            )
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


def save_hacker_news_insight(session: Session, insight: HackerNewsInsight) -> Optional[int]:
    """
    Save Hacker News insight to database.
    
    Uses UPSERT logic: if an insight already exists for today,
    it will be updated instead of creating a duplicate.
    
    Args:
        session: The SQLAlchemy session object.
        insight: HackerNewsInsight object from analyzer.
        
    Returns:
        Insight ID if saved successfully, None otherwise.
    """
    try:
        insight_date = insight.date.date() if hasattr(insight.date, 'date') else insight.date
        
        # UPSERT: Check if insight exists for today AND period
        existing = session.query(HackerNewsInsightDB).filter_by(
            date=insight_date,
            period=insight.period
        ).first()
        
        # Serialize stories to JSON
        stories_json = [
            {
                "id": s.id,
                "title": s.title,
                "url": s.url,
                "score": s.score,
                "comments_count": s.comments_count,
                "by": s.by,
                "comments": getattr(s, 'comments', []),
                "verdict": getattr(s, 'verdict', None),
                "sentiment": getattr(s, 'sentiment', None),
                "github_stars": getattr(s, 'github_stars', None),
            }
            for s in insight.stories
        ]
        
        if existing:
            # Update existing
            existing.stories_json = stories_json
            existing.summary = insight.summary
            existing.top_themes = insight.top_themes
            existing.created_at = datetime.now()  # Local time
            insight_record = existing
            logger.info(f"Updated existing Hacker News insight for {insight_date} (ID: {existing.id})")
        else:
            # Create new
            insight_record = HackerNewsInsightDB(
                date=insight_date,
                period=insight.period,
                stories_json=stories_json,
                summary=insight.summary,
                top_themes=insight.top_themes,
                created_at=datetime.now(),  # Local time
            )
            session.add(insight_record)
            logger.info(f"Created new Hacker News insight for {insight_date}")
        
        session.flush()
        return insight_record.id
        
    except Exception as e:
        logger.error(f"Database transaction failed for Hacker News insight: {e}")
        raise


def save_product_hunt_insight(session: Session, insight: ProductHuntInsight) -> Optional[int]:
    """
    Save Product Hunt insight to database.
    
    Uses UPSERT logic: if an insight already exists for today,
    it will be updated instead of creating a duplicate.
    
    Args:
        session: The SQLAlchemy session object.
        insight: ProductHuntInsight object from analyzer.
        
    Returns:
        Insight ID if saved successfully, None otherwise.
    """
    try:
        insight_date = insight.date.date() if hasattr(insight.date, 'date') else insight.date
        
        # UPSERT: Check if insight exists for today AND period
        existing = session.query(ProductHuntInsightDB).filter_by(
            date=insight_date,
            period=insight.period
        ).first()
        
        # Serialize launches to JSON
        launches_json = [
            {
                "id": l.id,
                "name": l.name,
                "tagline": l.tagline,
                "votes": l.votes,  # Use internal field name
                "website": l.website,
                "topics": l.topics,
            }
            for l in insight.top_launches
        ]
        
        if existing:
            # Update existing
            existing.launches_json = launches_json
            existing.trend_summary = insight.trend_summary
            existing.content_angles = insight.content_angles
            existing.created_at = datetime.now()
            insight_record = existing
            logger.info(f"Updated existing Product Hunt {insight.period} insight for {insight_date} (ID: {existing.id})")
        else:
            # Create new
            insight_record = ProductHuntInsightDB(
                date=insight_date,
                period=insight.period,
                launches_json=launches_json,
                trend_summary=insight.trend_summary,
                content_angles=insight.content_angles,
                created_at=datetime.now(),
            )
            session.add(insight_record)
            logger.info(f"Created new Product Hunt {insight.period} insight for {insight_date}")
        
        session.flush()
        return insight_record.id
        
    except Exception as e:
        logger.error(f"Database transaction failed for Product Hunt insight: {e}")
        raise


def get_recent_hacker_news_insights(session: Session, days: int = 7) -> List[HackerNewsInsightDB]:
    """
    Fetch Hacker News insights from the last N days (daily only).
    
    Args:
        session: SQLAlchemy session
        days: Number of days to look back
        
    Returns:
        List of HackerNewsInsightDB objects
    """
    try:
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        insights = session.query(HackerNewsInsightDB).filter(
            HackerNewsInsightDB.period == 'daily',
            HackerNewsInsightDB.date >= cutoff_date
        ).order_by(HackerNewsInsightDB.date.desc()).all()
        
        return insights
    except Exception as e:
        logger.error(f"Failed to fetch recent HN insights: {e}")
        return []


def save_youtube_insight(session: Session, insight: YouTubeInsight) -> Optional[int]:
    """
    Save YouTube insight to database.
    
    Uses UPSERT logic: if an insight already exists for today,
    it will be updated instead of creating a duplicate.
    
    Args:
        session: The SQLAlchemy session object.
        insight: YouTubeInsight object from analyzer.
        
    Returns:
        Insight ID if saved successfully, None otherwise.
    """
    try:
        insight_date = insight.date.date() if hasattr(insight.date, 'date') else insight.date
        
        # UPSERT: Check if insight exists for today AND period
        existing = session.query(YouTubeInsightDB).filter_by(
            date=insight_date,
            period=insight.period
        ).first()
        
        # Serialize videos to JSON
        videos_json = [
            {
                "id": v.id,
                "title": v.title,
                "channel_name": v.channel_name,
                "channel_id": v.channel_id,
                "description": v.description,
                "view_count": v.view_count,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "summary": v.summary,
            }
            for v in insight.videos
        ]
        
        if existing:
            # Update existing
            existing.videos_json = videos_json
            existing.trend_summary = insight.trend_summary
            existing.key_topics = insight.key_topics
            existing.created_at = datetime.now()
            insight_record = existing
            logger.info(f"Updated existing YouTube {insight.period} insight for {insight_date} (ID: {existing.id})")
        else:
            # Create new
            insight_record = YouTubeInsightDB(
                date=insight_date,
                period=insight.period,
                videos_json=videos_json,
                trend_summary=insight.trend_summary,
                key_topics=insight.key_topics,
                created_at=datetime.now(),
            )
            session.add(insight_record)
            logger.info(f"Created new YouTube {insight.period} insight for {insight_date}")
        
        session.flush()
        return insight_record.id
        
    except Exception as e:
        logger.error(f"Database transaction failed for YouTube insight: {e}")
        raise


def get_recent_youtube_insights(session: Session, days: int = 7) -> List[YouTubeInsightDB]:
    """
    Fetch YouTube insights from the last N days (daily only).
    
    Args:
        session: SQLAlchemy session
        days: Number of days to look back
        
    Returns:
        List of YouTubeInsightDB objects
    """
    try:
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        insights = session.query(YouTubeInsightDB).filter(
            YouTubeInsightDB.period == 'daily',
            YouTubeInsightDB.date >= cutoff_date
        ).order_by(YouTubeInsightDB.date.desc()).all()
        
        return insights
    except Exception as e:
        logger.error(f"Failed to fetch recent YouTube insights: {e}")
        return []


def save_discovery_briefing(session: Session, briefing: SaturdayBriefing) -> Optional[int]:
    """
    Save Saturday discovery briefing to database.
    
    Uses UPSERT logic: if a briefing already exists for today,
    it will be updated instead of creating a duplicate.
    
    Args:
        session: The SQLAlchemy session object.
        briefing: SaturdayBriefing object from discovery workflow.
        
    Returns:
        Briefing ID if saved successfully, None otherwise.
    """
    try:
        briefing_date = briefing.date.date() if hasattr(briefing.date, 'date') else briefing.date
        
        # UPSERT: Check if briefing exists for today
        existing = session.query(DiscoveryBriefingDB).filter_by(
            date=briefing_date
        ).first()
        
        # Serialize opportunities to JSON
        opportunities_json = [
            {
                "problem": opp.problem,
                "app_idea": opp.app_idea,
                "demand_score": opp.demand_score,
                "virality_score": opp.virality_score,
                "buildability_score": opp.buildability_score,
                "opportunity_score": opp.opportunity_score,
                "category": opp.category,
                "target_audience": opp.target_audience,
                "pain_points": [
                    {"text": pp.text, "problem": pp.problem, "source": pp.source}
                    for pp in opp.pain_points
                ] if opp.pain_points else [],
            }
            for opp in briefing.top_opportunities
        ]
        
        if existing:
            # Update existing
            existing.opportunities_json = opportunities_json
            existing.youtube_videos_json = briefing.youtube_videos  # NEW: For dashboard
            existing.trends_data_json = briefing.trends_data  # NEW: For dashboard
            existing.total_data_points = briefing.total_data_points
            existing.total_pain_points = briefing.total_pain_points_extracted
            existing.total_candidates = briefing.total_candidates_filtered
            existing.arcade_calls = briefing.arcade_calls
            existing.serpapi_calls = briefing.serpapi_calls
            existing.youtube_quota = briefing.youtube_quota
            existing.llm_calls = briefing.llm_calls
            existing.estimated_cost = briefing.estimated_cost
            existing.created_at = datetime.now()
            briefing_record = existing
            logger.info(f"Updated existing discovery briefing for {briefing_date} (ID: {existing.id})")
        else:
            # Create new
            briefing_record = DiscoveryBriefingDB(
                date=briefing_date,
                opportunities_json=opportunities_json,
                youtube_videos_json=briefing.youtube_videos,  # NEW: For dashboard
                trends_data_json=briefing.trends_data,  # NEW: For dashboard
                total_data_points=briefing.total_data_points,
                total_pain_points=briefing.total_pain_points_extracted,
                total_candidates=briefing.total_candidates_filtered,
                arcade_calls=briefing.arcade_calls,
                serpapi_calls=briefing.serpapi_calls,
                youtube_quota=briefing.youtube_quota,
                llm_calls=briefing.llm_calls,
                estimated_cost=briefing.estimated_cost,
                created_at=datetime.now(),
            )
            session.add(briefing_record)
            logger.info(f"Created new discovery briefing for {briefing_date}")
        
        session.flush()
        return briefing_record.id
        
    except Exception as e:
        logger.error(f"Database transaction failed for discovery briefing: {e}")
        raise


def get_latest_discovery_briefing(session: Session) -> Optional[DiscoveryBriefingDB]:
    """Get the most recent discovery briefing."""
    try:
        return session.query(DiscoveryBriefingDB).order_by(
            DiscoveryBriefingDB.date.desc()
        ).first()
    except Exception as e:
        logger.error(f"Failed to fetch latest discovery briefing: {e}")
        return None
