"""Main orchestration script for the email digest agent."""
import argparse
from datetime import date
from config.settings import validate_config, load_sender_whitelist, DIGEST_RECIPIENT_EMAIL
from gmail.client import GmailClient
from processor.states import Email
from processor.graph import EmailSummarizer
from processor.prompts import DIGEST_EMAIL_TEMPLATE, LINKEDIN_EMAIL_TEMPLATE
from utils.logger import setup_logger

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


def main(dry_run: bool = False):
    """
    Main execution function.
    
    Args:
        dry_run: If True, don't mark emails as read or create drafts
    """
    logger.info("=" * 60)
    logger.info("Email Digest Agent Starting")
    logger.info("=" * 60)
    
    try:
        # Validate configuration
        logger.info("Validating configuration...")
        validate_config()
        logger.info("✓ Configuration valid")
        
        # Load sender whitelist
        logger.info("Loading sender whitelist...")
        sender_configs = load_sender_whitelist()
        logger.info(f"✓ Loaded {len(sender_configs)} newsletter senders")
        
        # Initialize Gmail client
        logger.info("Initializing Gmail client...")
        gmail_client = GmailClient()
        logger.info("✓ Gmail client initialized")
        
        # Fetch unread emails
        logger.info("Fetching unread emails from whitelisted senders...")
        emails_data = gmail_client.fetch_unread_emails(sender_configs)
        logger.info(f"✓ Found {len(emails_data)} unread emails")
        
        if not emails_data:
            logger.info("No unread emails to process. Exiting!!!")
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
                gmail_client.archive_email(email.id)  # Remove from inbox
                logger.info(f"✓ Processed: {email.subject[:50]}...")
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")
                continue
        
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
        logger.info(f"Emails fetched: {len(emails_data)}")
        logger.info(f"Emails processed: {len(daily_digest.digests)}")
        logger.info(f"Emails skipped: {len(emails_data) - len(daily_digest.digests)}")
        logger.info(f"Newsletter Digest sent to: {DIGEST_RECIPIENT_EMAIL}")
        logger.info(f"Newsletter Digest ID: {digest_message_id}")
        logger.info(f"LinkedIn Content Pack sent to: {DIGEST_RECIPIENT_EMAIL}")
        logger.info(f"LinkedIn Content Pack ID: {linkedin_message_id}")
        logger.info("=" * 60)
        logger.info("Email Digest Agent Completed Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Newsletter Email Digest Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without modifying emails or creating drafts"
    )
    
    args = parser.parse_args()
    main(dry_run=args.dry_run)
