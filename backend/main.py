"""Main orchestration script for the email digest agent."""
import argparse
from datetime import date
from config.settings import validate_config, load_sender_whitelist_by_type, DIGEST_RECIPIENT_EMAIL
from gmail.client import GmailClient
from processor.states import Email
from processor.graph import EmailSummarizer, DeepDiveSummarizer
from processor.prompts import DIGEST_EMAIL_TEMPLATE, LINKEDIN_EMAIL_TEMPLATE, DEEPDIVE_EMAIL_TEMPLATE
from utils.logger import setup_logger
from utils.database import save_to_database

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


def main(email_type: str = "dailydigest", dry_run: bool = False):
    """
    Main execution function.
    
    Args:
        email_type: Either 'dailydigest' or 'weeklydeepdives'
        dry_run: If True, don't mark emails as read or create drafts
    """
    logger.info("=" * 60)
    logger.info(f"Email Agent Starting - Type: {email_type}")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_config()
        logger.info("✓ Configuration valid")
        
        # Load sender whitelist filtered by type
        logger.info(f"Loading sender whitelist for type: {email_type}...")
        sender_configs = load_sender_whitelist_by_type(email_type)
        logger.info(f"✓ Loaded {len(sender_configs)} senders for {email_type}")
        
        if not sender_configs:
            logger.error(f"No senders configured for type: {email_type}")
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
        else:
            logger.error(f"Unknown email type: {email_type}")
            return
        
        logger.info("=" * 60)
        logger.info("Email Agent Completed Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Newsletter Email Digest Agent")
    parser.add_argument(
        "--type",
        choices=["dailydigest", "weeklydeepdives"],
        default="dailydigest",
        help="Type of emails to process: 'dailydigest' (Mon-Fri) or 'weeklydeepdives' (Sunday)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without modifying emails or creating drafts"
    )
    
    args = parser.parse_args()
    main(email_type=args.type, dry_run=args.dry_run)
