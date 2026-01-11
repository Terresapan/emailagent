"""Main orchestration script for the email digest agent."""
import argparse
import concurrent.futures
from datetime import date
from config.settings import validate_config, load_sender_whitelist_by_type, DIGEST_RECIPIENT_EMAIL, PRODUCT_HUNT_TOKEN, YOUTUBE_API_KEY
from sources.gmail.client import GmailClient
from processor.email.states import Email, DailyDigest, WeeklyDeepDive
from processor.email.graph import EmailSummarizer, DeepDiveSummarizer
from processor.product_hunt.graph import ProductHuntAnalyzer
from processor.hacker_news.graph import HackerNewsAnalyzer
from processor.youtube.graph import YouTubeAnalyzer
from processor.email.prompts import DIGEST_EMAIL_TEMPLATE, LINKEDIN_EMAIL_TEMPLATE, DEEPDIVE_EMAIL_TEMPLATE
from utils.logger import setup_logger
from utils.database import save_to_database, save_product_hunt_insight, save_hacker_news_insight, save_youtube_insight

logger = setup_logger(__name__)


# =============================================================================
# HELPER FUNCTIONS (formatters)
# =============================================================================

def format_newsletter_digest(daily_digest: DailyDigest) -> str:
    """
    Format the newsletter digest into an email body.
    
    Args:
        daily_digest: DailyDigest object
        
    Returns:
        Formatted email body text for newsletter digest
    """
    email_body = DIGEST_EMAIL_TEMPLATE.format(
        date=daily_digest.date,
        briefing=daily_digest.aggregated_briefing,
        newsletter_summaries=daily_digest.newsletter_summaries
    )
    return email_body


def format_linkedin_content(daily_digest: DailyDigest) -> str:
    """
    Format the LinkedIn content into an email body.
    
    Args:
        daily_digest: DailyDigest object
        
    Returns:
        Formatted email body text for LinkedIn content pack
    """
    email_body = LINKEDIN_EMAIL_TEMPLATE.format(
        date=daily_digest.date,
        linkedin_content=daily_digest.linkedin_content
    )
    return email_body


def format_deepdive_email(weekly_digest: WeeklyDeepDive) -> str:
    """
    Format the weekly deep dive into an email body.
    
    Args:
        weekly_digest: WeeklyDeepDive object
        
    Returns:
        Formatted email body text for deep dive briefing
    """
    email_body = DEEPDIVE_EMAIL_TEMPLATE.format(
        date=weekly_digest.date,
        briefing=weekly_digest.aggregated_briefing,
        deepdive_summaries=weekly_digest.deepdive_summaries
    )
    return email_body


# =============================================================================
# PROCESSOR FUNCTIONS (called by main)
# =============================================================================

def main_daily_digest(gmail_client: GmailClient, sender_configs: list, dry_run: bool = False):
    """
    Process daily newsletter digest (Monday-Friday).
    
    Args:
        gmail_client: Initialized Gmail client
        sender_configs: Filtered sender configs for dailydigest type
        dry_run: If True, don't modify emails
    """
    logger.info("=" * 60)
    logger.info("Daily Newsletter Digest Processing")
    logger.info("=" * 60)
    
    # Fetch unread emails
    logger.info("Fetching unread daily digest emails...")
    emails_data = gmail_client.fetch_unread_emails(sender_configs)
    logger.info(f"✓ Found {len(emails_data)} unread emails")
    
    if not emails_data:
        logger.info("No unread daily digest emails to process. Exiting!")
        return
    
    # Convert to Email objects
    emails = [Email(**email_data) for email_data in emails_data]
    
    # Initialize summarizer
    logger.info("Initializing email summarizer...")
    summarizer = EmailSummarizer()
    logger.info("✓ Summarizer initialized")
    
    # Process emails
    logger.info("Processing emails...")
    daily_digest = summarizer.process_emails(emails)
    logger.info(f"✓ Processed {len(daily_digest.digests)} emails successfully")
    
    if dry_run:
        logger.info("\n" + "=" * 60)
        logger.info("DRY RUN MODE - Preview of emails")
        logger.info("=" * 60)
        
        logger.info("\n--- EMAIL 1: AI NEWSLETTER DIGEST ---")
        digest_body = format_newsletter_digest(daily_digest)
        print("\n" + digest_body)
        
        logger.info("\n--- EMAIL 2: LINKEDIN CONTENT PACK ---")
        linkedin_body = format_linkedin_content(daily_digest)
        print("\n" + linkedin_body)
        
        logger.info("\n" + "=" * 60)
        logger.info("DRY RUN COMPLETE - No emails modified")
        logger.info("=" * 60)
        return
    
    # Apply labels, mark as read, and archive
    logger.info("Applying labels, marking emails as read, and archiving...")
    for email in emails:
        try:
            gmail_client.apply_label(email.id)
            gmail_client.mark_as_read(email.id)
            gmail_client.archive_email(email.id)
            logger.info(f"✓ Processed: {email.subject[:50]}...")
        except Exception as e:
            logger.error(f"Error processing email {email.id}: {e}")
            continue
    
    # Save to database (for dashboard)
    logger.info("Saving digest and raw emails to database...")
    digest_id = save_to_database(emails, daily_digest, digest_type="daily")
    if digest_id:
        logger.info(f"✓ Saved to database with digest ID: {digest_id}")
    
    # Send digest emails
    logger.info(f"Sending newsletter digest to {DIGEST_RECIPIENT_EMAIL}...")
    digest_subject = f"AI Newsletter Digest – {date.today().isoformat()}"
    digest_body = format_newsletter_digest(daily_digest)
    digest_message_id = gmail_client.send_email(DIGEST_RECIPIENT_EMAIL, digest_subject, digest_body)
    logger.info(f"✓ Sent newsletter digest with ID: {digest_message_id}")
    
    logger.info(f"Sending LinkedIn content pack to {DIGEST_RECIPIENT_EMAIL}...")
    linkedin_subject = f"LinkedIn Content Pack – {date.today().isoformat()}"
    linkedin_body = format_linkedin_content(daily_digest)
    linkedin_message_id = gmail_client.send_email(DIGEST_RECIPIENT_EMAIL, linkedin_subject, linkedin_body)
    logger.info(f"✓ Sent LinkedIn content pack with ID: {linkedin_message_id}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Date: {daily_digest.date}")
    logger.info(f"Emails processed: {len(daily_digest.digests)}")
    logger.info(f"Newsletter Digest sent to: {DIGEST_RECIPIENT_EMAIL}")
    logger.info(f"LinkedIn Content Pack sent to: {DIGEST_RECIPIENT_EMAIL}")
    logger.info("=" * 60)


def main_weekly_deepdive(gmail_client: GmailClient, sender_configs: list, dry_run: bool = False):
    """
    Process weekly deep dives (Sunday only).
    
    Args:
        gmail_client: Initialized Gmail client
        sender_configs: Filtered sender configs for weeklydeepdives type
        dry_run: If True, don't modify emails
    """
    logger.info("=" * 60)
    logger.info("Weekly Deep Dive Processing")
    logger.info("=" * 60)
    
    # Fetch unread essays
    logger.info("Fetching unread deep dive essays...")
    emails_data = gmail_client.fetch_unread_emails(sender_configs)
    logger.info(f"✓ Found {len(emails_data)} unread essays")
    
    if not emails_data:
        logger.info("No unread deep dive essays to process. Exiting!")
        return
    
    # Convert to Email objects
    emails = [Email(**email_data) for email_data in emails_data]
    
    # Initialize deep dive summarizer
    logger.info("Initializing deep dive summarizer...")
    summarizer = DeepDiveSummarizer()
    logger.info("✓ Summarizer initialized")
    
    # Process essays
    logger.info("Processing essays...")
    weekly_digest = summarizer.process_emails(emails)
    logger.info(f"✓ Processed {len(weekly_digest.digests)} essays successfully")
    
    if dry_run:
        logger.info("\n" + "=" * 60)
        logger.info("DRY RUN MODE - Preview of deep dive email")
        logger.info("=" * 60)
        
        logger.info("\n--- WEEKLY DEEP DIVE BRIEFING ---")
        deepdive_body = format_deepdive_email(weekly_digest)
        print("\n" + deepdive_body)
        
        logger.info("\n" + "=" * 60)
        logger.info("DRY RUN COMPLETE - No emails modified")
        logger.info("=" * 60)
        return
    
    # Apply labels, mark as read, and archive
    logger.info("Applying labels, marking emails as read, and archiving...")
    for email in emails:
        try:
            gmail_client.apply_label(email.id, "Deep Dives")
            gmail_client.mark_as_read(email.id)
            gmail_client.archive_email(email.id)
            logger.info(f"✓ Processed: {email.subject[:50]}...")
        except Exception as e:
            logger.error(f"Error processing email {email.id}: {e}")
            continue
    
    # Save to database (for dashboard)
    logger.info("Saving deep dive and raw emails to database...")
    digest_id = save_to_database(emails, weekly_digest, digest_type="weekly")
    if digest_id:
        logger.info(f"✓ Saved to database with digest ID: {digest_id}")
    
    # Send deep dive email
    logger.info(f"Sending weekly deep dive to {DIGEST_RECIPIENT_EMAIL}...")
    deepdive_subject = f"Weekly AI Deep Dive – {date.today().isoformat()}"
    deepdive_body = format_deepdive_email(weekly_digest)
    deepdive_message_id = gmail_client.send_email(DIGEST_RECIPIENT_EMAIL, deepdive_subject, deepdive_body)
    logger.info(f"✓ Sent deep dive with ID: {deepdive_message_id}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Date: {weekly_digest.date}")
    logger.info(f"Essays processed: {len(weekly_digest.digests)}")
    logger.info(f"Weekly Deep Dive sent to: {DIGEST_RECIPIENT_EMAIL}")
    logger.info("=" * 60)


def main_product_hunt(gmail_client: GmailClient, dry_run: bool = False, timeframe: str = "daily"):
    """
    Process Product Hunt AI launches and send insights email.
    
    Args:
        gmail_client: Initialized Gmail client
        dry_run: If True, don't send emails
        timeframe: 'daily' or 'weekly'
    """
    logger.info("=" * 60)
    logger.info(f"Product Hunt AI Tools Processing ({timeframe})")
    logger.info("=" * 60)
    
    if not PRODUCT_HUNT_TOKEN:
        logger.warning("PRODUCT_HUNT_TOKEN not set. Skipping Product Hunt processing.")
        return
    
    # Initialize analyzer
    logger.info(f"Initializing Product Hunt analyzer ({timeframe})...")
    analyzer = ProductHuntAnalyzer(timeframe=timeframe)
    
    # Run the Product Hunt workflow
    logger.info("Fetching and analyzing AI launches...")
    insight = analyzer.process()
    
    if not insight.top_launches:
        logger.info(f"No AI launches found on Product Hunt ({timeframe}).")
        return
    
    logger.info(f"✓ Analyzed {len(insight.top_launches)} top launches")
    
    # Save to database
    if not dry_run:
        logger.info("Saving insight to database...")
        from db import get_session
        session = get_session()
        try:
            insight_id = save_product_hunt_insight(session, insight)
            session.commit()
            logger.info(f"✓ Saved to database with ID: {insight_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save insight: {e}")
        finally:
            session.close()
    
    # Send email
    recipient = DIGEST_RECIPIENT_EMAIL
    if not dry_run and recipient:
        logger.info(f"Sending {timeframe} AI Tools digest to {DIGEST_RECIPIENT_EMAIL}...")
        
        # Format launches
        launches_text = "\n".join([
            f"• **[{l.name}]({l.website or '#'})** ({l.votes} votes)\n  {l.tagline}"
            for l in insight.top_launches[:10]  # Show top 10
        ])
        
        # Format content angles
        angles_text = "\n".join([f"• {angle}" for angle in insight.content_angles])
        
        title_prefix = "Weekly AI Best" if timeframe == "weekly" else "AI Tools Discovery"
        
        email_body = f"""# 🚀 {title_prefix} – {date.today()}

## Top AI Launches {timeframe.capitalize()}

{launches_text}

---

## Trend Analysis

{insight.trend_summary}

---

## Content Ideas

{angles_text}
"""
        
        try:
            msg_id = gmail_client.send_email(
                to=DIGEST_RECIPIENT_EMAIL,
                subject=f"{title_prefix} – {date.today()}",
                body=email_body
            )
            logger.info(f"✓ Sent AI Tools digest with ID: {msg_id}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    else:
        logger.info("[DRY RUN] Would send AI Tools digest email")
        logger.info(f"Top Launches: {[l.name for l in insight.top_launches[:5]]}")
    
    logger.info("=" * 60)
    logger.info("Product Hunt Processing Complete")
    logger.info("=" * 60)


def main_hacker_news(gmail_client: GmailClient, dry_run: bool = False, timeframe: str = "daily"):
    """
    Process Hacker News trends and save insights.
    
    Args:
        gmail_client: Initialized Gmail client
        dry_run: If True, don't save to database
        timeframe: 'daily' or 'weekly' (for future use)
    """
    logger.info("=" * 60)
    logger.info(f"Hacker News Processing ({timeframe})")
    logger.info("=" * 60)
    
    try:
        logger.info(f"Initializing Hacker News analyzer ({timeframe})...")
        analyzer = HackerNewsAnalyzer(timeframe=timeframe)
        
        logger.info("Fetching and analyzing Hacker News trends...")
        insight = analyzer.process()
        
        logger.info(f"✓ Analyzed {len(insight.stories)} top stories")
        logger.info(f"✓ Identified themes: {insight.top_themes}")
        
        # Save to database
        if not dry_run:
            logger.info("Saving insight to database...")
            from db import get_session
            session = get_session()
            try:
                insight_id = save_hacker_news_insight(session, insight)
                session.commit()
                logger.info(f"✓ Saved to database with ID: {insight_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to save insight: {e}")
            finally:
                session.close()
        
        # Format and send email
        recipient = DIGEST_RECIPIENT_EMAIL
        if not dry_run and recipient:
            logger.info(f"Sending HackerNews digest to {recipient}...")
            
            # Format themes
            themes_text = "\n".join([f"• {theme}" for theme in insight.top_themes])
            
            # Format top stories
            stories_text = "\n".join([
                f"• **[{s.title}]({s.url or '#'})** ({s.score} pts, {s.comments_count} comments)\n  {s.sentiment or ''} {s.verdict or ''}"
                for s in insight.stories[:10]
            ])
            
            title_prefix = "Weekly HN Rewind" if timeframe == "weekly" else "HackerNews Trends"
            
            email_body = f"""# 📰 {title_prefix} – {date.today()}

## Developer Zeitgeist

{insight.summary}

---

## Top Themes

{themes_text}

---

## Top Stories

{stories_text}

---

*Generated by AI Newsletter Agent*
"""
            
            try:
                msg_id = gmail_client.send_email(
                    to=recipient,
                    subject=f"{title_prefix} – {date.today()}",
                    body=email_body
                )
                logger.info(f"✓ Sent HackerNews digest with ID: {msg_id}")
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
        else:
            logger.info("[DRY RUN] Would send HackerNews digest email")
            logger.info(f"Summary: {insight.summary[:200]}...")
        
        logger.info("=" * 60)
        logger.info("Hacker News Processing Complete")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Hacker News processing failed: {e}", exc_info=True)
        raise


def main_youtube(gmail_client: GmailClient, dry_run: bool = False, timeframe: str = "daily"):
    """
    Process YouTube influencer videos and send insights email.
    
    Args:
        gmail_client: Initialized Gmail client
        dry_run: If True, don't save to database or send emails
        timeframe: 'daily' or 'weekly'
    """
    logger.info("=" * 60)
    logger.info(f"YouTube Influencer Processing ({timeframe})")
    logger.info("=" * 60)
    
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY not set. Skipping YouTube processing.")
        return
    
    try:
        logger.info(f"Initializing YouTube analyzer ({timeframe})...")
        analyzer = YouTubeAnalyzer(timeframe=timeframe)
        
        logger.info("Fetching videos and analyzing content...")
        insight = analyzer.process()
        
        if not insight.videos:
            logger.info("No videos found from configured channels.")
            return
        
        logger.info(f"✓ Analyzed {len(insight.videos)} videos")
        logger.info(f"✓ Key topics: {insight.key_topics}")
        
        # Save to database
        if not dry_run:
            logger.info("Saving insight to database...")
            from db import get_session
            session = get_session()
            try:
                insight_id = save_youtube_insight(session, insight)
                session.commit()
                logger.info(f"✓ Saved to database with ID: {insight_id}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to save insight: {e}")
            finally:
                session.close()
        
        # Format and send email
        recipient = DIGEST_RECIPIENT_EMAIL
        if not dry_run and recipient:
            logger.info(f"Sending YouTube digest to {recipient}...")
            
            # Format topics
            topics_text = "\n".join([f"• {topic}" for topic in insight.key_topics])
            
            # Format videos
            videos_text = "\n".join([
                f"• **[{v.title}](https://www.youtube.com/watch?v={v.id})** ({v.channel_name})\n  {v.view_count:,} views\n  {v.summary or 'No summary available'}"
                for v in insight.videos[:10]
            ])
            
            title_prefix = "Weekly YouTube Insights" if timeframe == "weekly" else "YouTube Influencer Insights"
            
            email_body = f"""# 🎬 {title_prefix} – {date.today()}

## What Influencers Are Talking About

{insight.trend_summary}

---

## Key Topics

{topics_text}

---

## Video Summaries

{videos_text}

---

*Generated by AI Newsletter Agent*
"""
            
            try:
                msg_id = gmail_client.send_email(
                    to=recipient,
                    subject=f"{title_prefix} – {date.today()}",
                    body=email_body
                )
                logger.info(f"✓ Sent YouTube digest with ID: {msg_id}")
            except Exception as e:
                logger.error(f"Failed to send email: {e}")
        else:
            logger.info("[DRY RUN] Would send YouTube digest email")
            logger.info(f"Summary: {insight.trend_summary[:200]}...")
        
        logger.info("=" * 60)
        logger.info("YouTube Processing Complete")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"YouTube processing failed: {e}", exc_info=True)
        raise


def main_trend_validation(gmail_client: GmailClient, dry_run: bool = False):
    """
    Run trend validation on all sources and send consolidated email report.
    
    Uses LLM-powered keyword extraction for better quality results.
    Auto-detects day of week to use daily vs weekly sources.
    
    Schedule:
    - Mon-Fri: Newsletter (daily), Product Hunt (daily), YouTube (daily)
    - Saturday: No validation
    - Sunday: Newsletter Deep Dive, PH (weekly), YouTube (weekly)
    
    Args:
        gmail_client: Initialized Gmail client
        dry_run: If True, don't send emails
    """
    from datetime import datetime
    import json
    
    # Check day of week (0=Monday, 6=Sunday)
    today = datetime.now()
    day_of_week = today.weekday()
    
    if day_of_week == 5:  # Saturday
        logger.info("Saturday - Skipping trend validation")
        return
    
    is_sunday = day_of_week == 6
    
    logger.info("=" * 60)
    logger.info(f"Trend Validation Processing ({'Weekly' if is_sunday else 'Daily'})")
    logger.info("=" * 60)
    
    from db import get_session, ProductHuntInsightDB, YouTubeInsightDB, TopicAnalysisDB, Digest
    from processor.google_trend.graph import TrendGraph
    from sources.gmail.client import GmailClient
    
    session = get_session()
    
    try:
        inputs = []
        
        if is_sunday:
            # SUNDAY: Weekly sources
            
            # 1. Newsletter Deep Dive (weekly)
            logger.info("Extracting from Weekly Newsletter Deep Dive...")
            weekly_digest = session.query(Digest).filter(
                Digest.digest_type == "weekly"
            ).order_by(Digest.date.desc()).first()
            if weekly_digest and weekly_digest.newsletter_summaries:
                inputs.append({
                    "source": "weekly_newsletter", 
                    "content": weekly_digest.newsletter_summaries
                })
            
            # 2. Product Hunt Weekly
            logger.info("Extracting from Weekly Product Hunt...")
            ph_weekly = session.query(ProductHuntInsightDB).filter(
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
            yt_weekly = session.query(YouTubeInsightDB).filter(
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
            daily_digest = session.query(Digest).filter(
                Digest.digest_type == "daily"
            ).order_by(Digest.date.desc()).first()
            if daily_digest and daily_digest.newsletter_summaries:
                inputs.append({
                    "source": "newsletter", 
                    "content": daily_digest.newsletter_summaries
                })
            
            # 2. Product Hunt (daily)
            logger.info("Extracting from Daily Product Hunt...")
            ph_daily = session.query(ProductHuntInsightDB).filter(
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
            yt_daily = session.query(YouTubeInsightDB).filter(
                YouTubeInsightDB.period == "daily"
            ).order_by(YouTubeInsightDB.date.desc()).first()
            if yt_daily:
                content = f"Topics: {yt_daily.key_topics}\nSummary: {yt_daily.trend_summary}"
                inputs.append({
                    "source": "youtube", 
                    "content": content
                })
        
        if not inputs:
            logger.warning("No logic content found. Skipping validation.")
            return
            
        # Run Trend Graph
        graph = TrendGraph()
        analysis = graph.process(inputs, source_type="weekly" if is_sunday else "daily")
        
        if not analysis:
            logger.error("Analysis graph returned None")
            return
            
        # Save to DB
        existing = session.query(TopicAnalysisDB).filter(
            TopicAnalysisDB.source == "global",
            TopicAnalysisDB.source_date == today.date()
        ).first()
        if existing:
            session.delete(existing)
            session.commit()
            
        db_obj = TopicAnalysisDB(
            source="global",
            source_date=today.date(),
            topics_json=[t.model_dump(mode='json') for t in analysis.topics],
            top_builder_topics=analysis.top_builder_topics,
            top_founder_topics=analysis.top_founder_topics,
            summary=analysis.summary,
            created_at=datetime.utcnow()
        )
        session.add(db_obj)
        session.commit()
        
        # Send Email (use the Pydantic analysis object directly)
        if not dry_run:
            gmail_client.send_analysis_email([analysis])
            logger.info("Analysis email sent successfully")
            
    except Exception as e:
        logger.error(f"Trend validation failed: {e}", exc_info=True)
        session.rollback()
    finally:
        session.close()
        



# =============================================================================
# MAIN ORCHESTRATOR (calls processor functions)
# =============================================================================

def main(email_type: str = "dailydigest", dry_run: bool = False, timeframe: str = "daily"):
    """
    Main execution function.
    
    Args:
        email_type: 'dailydigest', 'weeklydeepdives', 'productlaunch', 'all'
        dry_run: If True, don't mark emails as read or create drafts
        timeframe: 'daily' (default) or 'weekly' - mostly for productlaunch
    """
    logger.info("=" * 60)
    logger.info(f"Email Agent Starting - Type: {email_type} (Timeframe: {timeframe})")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_config()
        logger.info("✓ Configuration valid")
        
        # Load sender whitelist filtered by type
        sender_configs = []
        if email_type in ["dailydigest", "weeklydeepdives", "all", "all_weekly"]:
            # Determine which sender type to load
            if email_type == "all":
                load_type = "dailydigest"
            elif email_type == "all_weekly":
                load_type = "weeklydeepdives"
            else:
                load_type = email_type
            
            logger.info(f"Loading sender whitelist for type: {load_type}...")
            sender_configs = load_sender_whitelist_by_type(load_type)
            logger.info(f"✓ Loaded {len(sender_configs)} senders for {load_type}")
            
            if not sender_configs:
                logger.error(f"No senders configured for type: {load_type}")
                return
        
        # Initialize Gmail client
        logger.info("Initializing Gmail client...")
        gmail_client = GmailClient()
        logger.info("✓ Gmail client initialized")
        
        # Route to appropriate processor
        if email_type == "dailydigest":
            main_daily_digest(gmail_client, sender_configs, dry_run)
        elif email_type == "weeklydeepdives":
            main_weekly_deepdive(gmail_client, sender_configs, dry_run)
        elif email_type == "productlaunch":
            main_product_hunt(gmail_client, dry_run, timeframe=timeframe)
        elif email_type == "all":
            # Run daily email digest, daily product hunt, hacker news, and youtube in parallel
            logger.info("Running all DAILY processors in parallel...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_digest = executor.submit(main_daily_digest, gmail_client, sender_configs, dry_run)
                future_ph = executor.submit(main_product_hunt, gmail_client, dry_run, timeframe="daily")
                future_hn = executor.submit(main_hacker_news, gmail_client, dry_run, timeframe="daily")
                future_yt = executor.submit(main_youtube, gmail_client, dry_run, timeframe="daily")
                concurrent.futures.wait([future_digest, future_ph, future_hn, future_yt])
            logger.info("All daily processors completed")
            
            # Run trend validation AFTER all sources are saved to DB
            logger.info("Running trend validation...")
            main_trend_validation(gmail_client, dry_run)
        elif email_type == "all_weekly":
            # Sunday only: Run weekly processors
            logger.info("Running all WEEKLY processors in parallel...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Weekly deep dive and weekly Product Hunt
                future_digest = executor.submit(main_weekly_deepdive, gmail_client, sender_configs, dry_run)
                future_ph_weekly = executor.submit(main_product_hunt, gmail_client, dry_run, timeframe="weekly")
                
                # Run Daily HN and YouTube first to capture Sunday's data for weekly rollup
                future_hn_daily = executor.submit(main_hacker_news, gmail_client, dry_run, timeframe="daily")
                future_yt_daily = executor.submit(main_youtube, gmail_client, dry_run, timeframe="daily")
                concurrent.futures.wait([future_hn_daily, future_yt_daily])
                
                # Then run Weekly versions (aggregate from database)
                future_hn_weekly = executor.submit(main_hacker_news, gmail_client, dry_run, timeframe="weekly")
                future_yt_weekly = executor.submit(main_youtube, gmail_client, dry_run, timeframe="weekly")
                
                # Wait for all
                concurrent.futures.wait([future_digest, future_ph_weekly, future_hn_weekly, future_yt_weekly])
            logger.info("All weekly processors completed")
        elif email_type == "hackernews":
            main_hacker_news(gmail_client, dry_run, timeframe=timeframe)
        elif email_type == "youtube":
            main_youtube(gmail_client, dry_run, timeframe=timeframe)
        else:
            logger.error(f"Unknown type: {email_type}")
            return
        
        logger.info("=" * 60)
        logger.info("Email Agent Completed Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        raise


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Newsletter Email Digest Agent")
    parser.add_argument(
        "--type",
        choices=["dailydigest", "weeklydeepdives", "productlaunch", "hackernews", "youtube", "all", "all_weekly"],
        default="dailydigest",
        help="Type of processing to run"
    )
    parser.add_argument(
        "--timeframe",
        choices=["daily", "weekly"],
        default="daily",
        help="Timeframe for Product Hunt analysis ('daily' or 'weekly')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without modifying emails or sending digests"
    )
    
    args = parser.parse_args()
    main(email_type=args.type, dry_run=args.dry_run, timeframe=args.timeframe)
