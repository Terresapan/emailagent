
from processor.states import Email, CategorySummary, EmailDigest, DailyDigest
from processor.graph import EmailSummarizer
from main import format_digest_for_draft
from datetime import date

def test_formatting():
    # Mock data
    digest1 = EmailDigest(
        email_id="1",
        sender="sender1@test.com",
        subject="Subject 1",
        summary=CategorySummary(
            industry_news=["News item 1"],
            new_tools=["Tool 1"],
            insights=["Insight 1"]
        )
    )
    digest2 = EmailDigest(
        email_id="2",
        sender="sender2@test.com",
        subject="Subject 2",
        summary=CategorySummary(
            industry_news=["News item 2"],
            new_tools=[],
            insights=["Insight 2"]
        )
    )
    
    daily_digest = DailyDigest(
        date=date.today().isoformat(),
        emails_processed=["sender1: Subject 1", "sender2: Subject 2"],
        digests=[digest1, digest2],
        aggregated_briefing="This is the briefing.",
        newsletter_summaries="**Subject 1**\nMock summary content 1\n\n**Subject 2**\nMock summary content 2"
    )
    
    formatted = format_digest_for_draft(daily_digest)
    
    print("--- FORMATTED OUTPUT START ---")
    print(formatted)
    print("--- FORMATTED OUTPUT END ---")
    
    if "DETAILED SUMMARIES" in formatted:
        print("PASS: 'DETAILED SUMMARIES' found.")
    else:
        print("FAIL: 'DETAILED SUMMARIES' NOT found.")

    if "**Subject 1**" in formatted:
         print("PASS: Subject 1 found.")
    else:
        print("FAIL: Subject 1 NOT found.")

if __name__ == "__main__":
    test_formatting()
