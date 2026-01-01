"""Main orchestration script for the email digest agent."""
import argparse
import asyncio
import concurrent.futures
from datetime import date
from config.settings import validate_config, load_sender_whitelist_by_type, DIGEST_RECIPIENT_EMAIL, PRODUCT_HUNT_TOKEN
from gmail.client import GmailClient
from processor.email.states import Email
from processor.email.graph import EmailSummarizer, DeepDiveSummarizer
from processor.product_hunt.graph import ProductHuntAnalyzer
from processor.hacker_news.graph import HackerNewsAnalyzer
from processor.email.prompts import DIGEST_EMAIL_TEMPLATE, LINKEDIN_EMAIL_TEMPLATE, DEEPDIVE_EMAIL_TEMPLATE
from utils.logger import setup_logger
from utils.database import save_to_database, save_product_hunt_insight, save_hacker_news_insight

logger = setup_logger(__name__)


def format_newsletter_digest(daily_digest) -> str:
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


def format_linkedin_content(daily_digest) -> str:
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


def format_deepdive_email(weekly_digest) -> str:
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
        if email_type in ["dailydigest", "weeklydeepdives", "all"]:
            load_type = "dailydigest" if email_type == "all" else email_type
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
            # Default to daily, but can be invoked with timeframe logic via arg if needed
            main_product_hunt(gmail_client, dry_run, timeframe=timeframe)
        elif email_type == "all":
            # Run daily email digest, daily product hunt, and daily hacker news in parallel
            logger.info("Running all DAILY processors in parallel...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_digest = executor.submit(main_daily_digest, gmail_client, sender_configs, dry_run)
                future_ph = executor.submit(main_product_hunt, gmail_client, dry_run, timeframe="daily")
                future_hn = executor.submit(main_hacker_news, gmail_client, dry_run, timeframe="daily")
                concurrent.futures.wait([future_digest, future_ph, future_hn])
            logger.info("All daily processors completed")
            # Run weekly deep dive and weekly product hunt in parallel
            # Also run daily Hacker News fetch to ensure Sunday's data is captured for the weekly rollup
            logger.info("Running all WEEKLY processors in parallel (sequencing HN daily->weekly)...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # independent tasks
                future_digest = executor.submit(main_weekly_deepdive, gmail_client, sender_configs, dry_run)
                future_ph_weekly = executor.submit(main_product_hunt, gmail_client, dry_run, timeframe="weekly")
                future_ph_daily = executor.submit(main_product_hunt, gmail_client, dry_run, timeframe="daily")
                
                # Run Daily HN first
                future_hn_daily = executor.submit(main_hacker_news, gmail_client, dry_run, timeframe="daily")
                
                # Wait for Daily HN to complete so DB is populated
                concurrent.futures.wait([future_hn_daily])
                
                # Run Weekly HN (aggregates the data just saved)
                future_hn_weekly = executor.submit(main_hacker_news, gmail_client, dry_run, timeframe="weekly")
                
                # Wait for everything else
                concurrent.futures.wait([future_digest, future_ph_weekly, future_ph_daily, future_hn_weekly])
            logger.info("All weekly processors completed")
        elif email_type == "hackernews":
            main_hacker_news(gmail_client, dry_run, timeframe=timeframe)
        else:
            logger.error(f"Unknown type: {email_type}")
            return
        
        logger.info("=" * 60)
        logger.info("Email Agent Completed Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        raise


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
        from utils.database import get_session
        session = get_session()
        try:
            insight_id = save_product_hunt_insight(insight)
            logger.info(f"✓ Saved to database with ID: {insight_id}")
            insight.id = insight_id
        except Exception as e:
            logger.error(f"Failed to save insight: {e}")
        finally:
            session.close()
            
    # Format and send email
    # (Reusing a simple template for now or just logging)
    # For now for HN we might want to email too, but user didn't specify template.
    # Let's create a basic one dynamically or skip email if not critical. 
    # Current instruction says "Display on dashboard". Email is optional but good practice.
    
    # Send email
    recipient = DIGEST_RECIPIENT_EMAIL
    if not dry_run and recipient:
        logger.info(f"Sending {timeframe} AI Tools digest to {DIGEST_RECIPIENT_EMAIL}...")
        
        # Format launches
        launches_text = "\n".join([
            f"• **{l.name}** ({l.votes} votes)\n  {l.tagline}\n  {l.website or 'No website'}"
            for l in insight.top_launches[:5]
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
                f"• **{s.title}** ({s.score} pts, {s.comments_count} comments)\n  {s.sentiment or ''} {s.verdict or ''}\n  {s.url or 'No link'}"
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Newsletter Email Digest Agent")
    parser.add_argument(
        "--type",
        choices=["dailydigest", "weeklydeepdives", "productlaunch", "hackernews", "all", "all_weekly"],
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
