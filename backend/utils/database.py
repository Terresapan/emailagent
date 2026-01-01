"""Database utilities for saving digests and emails.

This module uses the shared db package for models and session management.
"""
from datetime import datetime
from typing import List, Optional

from db import Digest as DigestModel, Email as EmailModel, get_session, HackerNewsInsightDB, ProductHuntInsightDB
from sqlalchemy.orm import Session
from sources.models import HackerNewsInsight
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
                existing_digest.created_at = datetime.utcnow()  # Update timestamp
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
        
        # UPSERT: Check if insight exists for today
        existing = session.query(HackerNewsInsightDB).filter_by(
            date=insight_date
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
            }
            for s in insight.stories
        ]
        
        if existing:
            # Update existing
            existing.stories_json = stories_json
            existing.summary = insight.summary
            existing.top_themes = insight.top_themes
            existing.created_at = datetime.utcnow()
            insight_record = existing
            logger.info(f"Updated existing Hacker News insight for {insight_date} (ID: {existing.id})")
        else:
            # Create new
            insight_record = HackerNewsInsightDB(
                date=insight_date,
                stories_json=stories_json,
                summary=insight.summary,
                top_themes=insight.top_themes,
                created_at=datetime.utcnow(),
            )
            session.add(insight_record)
            logger.info(f"Created new Hacker News insight for {insight_date}")
        
        session.flush()
        return insight_record.id
        
    except Exception as e:
        logger.error(f"Database transaction failed for Hacker News insight: {e}")
        raise


def save_product_hunt_insight(insight) -> Optional[int]:
    """
    Save Product Hunt insight to database.
    
    Uses UPSERT logic: if an insight already exists for today,
    it will be updated instead of creating a duplicate.
    
    Args:
        insight: ProductHuntInsight object from analyzer
        
    Returns:
        Insight ID if saved successfully, None otherwise
    """
    # The get_session import is already at the top level.
    # ProductHuntInsightDB is now imported as ProductHuntInsight from sources.models
    
    try:
        session = get_session()
        
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
                existing.created_at = insight.date
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
                )
                session.add(insight_record)
                logger.info(f"Created new Product Hunt {insight.period} insight for {insight_date}")
            
            session.commit()
            return insight_record.id
            
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Failed to save Product Hunt insight: {e}")
        return None
