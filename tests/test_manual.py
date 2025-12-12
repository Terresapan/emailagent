"""Manual test script for email digest agent components."""
import argparse
import sys
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_auth():
    """Test Gmail authentication."""
    logger.info("Testing Gmail authentication...")
    try:
        from gmail.auth import authenticate_gmail
        creds = authenticate_gmail()
        logger.info("✓ Authentication successful")
        logger.info(f"  Token valid: {creds.valid}")
        return True
    except Exception as e:
        logger.error(f"✗ Authentication failed: {e}")
        return False


def test_fetch():
    """Test fetching emails."""
    logger.info("Testing email fetch...")
    try:
        from gmail.client import GmailClient
        from config.settings import load_sender_whitelist
        
        client = GmailClient()
        senders = load_sender_whitelist()
        emails = client.fetch_unread_emails(senders)
        
        logger.info(f"✓ Fetched {len(emails)} emails")
        if emails:
            logger.info(f"  Sample: {emails[0]['subject'][:50]}...")
        return True
    except Exception as e:
        logger.error(f"✗ Fetch failed: {e}")
        return False


def test_parse():
    """Test HTML parsing."""
    logger.info("Testing HTML parser...")
    try:
        from utils.html_parser import html_to_text
        
        sample_html = """
        <html>
            <body>
                <h1>Test Newsletter</h1>
                <p>This is a test paragraph with <b>bold text</b>.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </body>
        </html>
        """
        
        text = html_to_text(sample_html)
        logger.info("✓ HTML parsing successful")
        logger.info(f"  Output length: {len(text)} chars")
        logger.info(f"  Preview: {text[:100]}...")
        return True
    except Exception as e:
        logger.error(f"✗ HTML parsing failed: {e}")
        return False


def test_summarize():
    """Test email summarization."""
    logger.info("Testing LLM summarization...")
    try:
        from processor.summarizer import EmailSummarizer
        from processor.models import Email
        
        # Create sample email
        sample_email = Email(
            id="test-123",
            sender="test@example.com",
            subject="Test AI Newsletter",
            body="""
            Breaking: OpenAI releases new GPT-5 model with improved reasoning capabilities.
            The model shows 40% better performance on complex tasks.
            
            New tool alert: AgentStudio launches - a visual builder for LLM agents.
            Supports drag-and-drop workflow creation and testing.
            
            Analysis: The SME market is rapidly adopting AI agents for customer service,
            with 60% growth in Q4 2024. Key opportunity in multi-agent orchestration.
            """
        )
        
        summarizer = EmailSummarizer()
        summary = summarizer.summarize_email(sample_email)
        
        logger.info("✓ Summarization successful")
        logger.info(f"  Industry news items: {len(summary.industry_news)}")
        logger.info(f"  New tools items: {len(summary.new_tools)}")
        logger.info(f"  Insights items: {len(summary.insights)}")
        
        if summary.industry_news:
            logger.info(f"  Sample news: {summary.industry_news[0][:60]}...")
        
        return True
    except Exception as e:
        logger.error(f"✗ Summarization failed: {e}")
        return False


def test_label():
    """Test label operations."""
    logger.info("Testing label operations...")
    try:
        from gmail.client import GmailClient
        
        client = GmailClient()
        label_id = client._get_or_create_label("Newsletters")
        
        logger.info("✓ Label operation successful")
        logger.info(f"  Label ID: {label_id}")
        return True
    except Exception as e:
        logger.error(f"✗ Label operation failed: {e}")
        return False


def test_draft():
    """Test draft creation."""
    logger.info("Testing draft creation...")
    try:
        from gmail.client import GmailClient
        from datetime import date
        
        client = GmailClient()
        
        test_subject = f"[TEST] AI Newsletter Digest – {date.today().isoformat()}"
        test_body = """
        This is a test draft created by the Email Digest Agent.
        
        Please delete this draft after verification.
        
        If you see this, draft creation is working correctly!
        """
        
        draft_id = client.create_draft(test_subject, test_body)
        
        logger.info("✓ Draft creation successful")
        logger.info(f"  Draft ID: {draft_id}")
        logger.info("  Please check Gmail drafts and delete the test draft")
        return True
    except Exception as e:
        logger.error(f"✗ Draft creation failed: {e}")
        return False


def main():
    """Run manual tests."""
    parser = argparse.ArgumentParser(description="Manual test script for email digest agent")
    parser.add_argument(
        "--test",
        choices=["auth", "fetch", "parse", "summarize", "label", "draft", "all"],
        default="all",
        help="Test to run"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Email Digest Agent - Manual Tests")
    logger.info("=" * 60)
    
    tests = {
        "auth": test_auth,
        "fetch": test_fetch,
        "parse": test_parse,
        "summarize": test_summarize,
        "label": test_label,
        "draft": test_draft,
    }
    
    results = {}
    
    if args.test == "all":
        for name, test_func in tests.items():
            logger.info("")
            results[name] = test_func()
    else:
        results[args.test] = tests[args.test]()
    
    # Summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{name:12s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    logger.info("")
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
