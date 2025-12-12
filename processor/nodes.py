"""
Node functions for the LangGraph email summarization workflow.

This module contains all standalone node functions that are used in the
email processing graph. Each function is designed to be composed with
functools.partial to inject LLM dependencies.

Node Functions:
    - distribute_emails: Entry point, logs email count
    - prepare_content_generation: Synchronization point, formats summaries
    - map_emails: Fan-out function for parallel email processing
    - summarize_email_logic: Core LLM call for email summarization
    - summarize_single_email: Worker node for individual email processing
    - generate_briefing: Creates aggregated AI briefing
    - quality_check_briefing: Reviews and improves the briefing
    - generate_linkedin_content: Creates LinkedIn post content
    - quality_check_linkedin: Reviews and improves LinkedIn content
"""
from typing import List

from langgraph.types import Send
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from processor.states import ProcessorState, WorkerState, EmailDigest, CategorySummary
from processor.prompts import (
    EMAIL_SUMMARIZATION_PROMPT, 
    DIGEST_BRIEFING_PROMPT,
    LINKEDIN_CONTENT_PROMPT,
    QUALITY_CHECK_DIGEST_PROMPT,
    QUALITY_CHECK_LINKEDIN_PROMPT
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# Email Distribution and Mapping Nodes
# =============================================================================

def distribute_emails(state: ProcessorState) -> dict:
    """
    Entry point node for the email processing workflow.
    
    Logs the number of emails to be processed and passes through.
    The actual fan-out is handled by the map_emails conditional edge.
    
    Args:
        state: Current processor state containing emails
        
    Returns:
        Empty dict (no state updates)
    """
    logger.info(f"Starting distribution of {len(state['emails'])} emails...")
    return {}


def map_emails(state: ProcessorState) -> List[Send]:
    """
    Conditional edge function that creates parallel workers for each email.
    
    Uses LangGraph's Send pattern for map-reduce parallelism.
    Each email spawns a separate summarize_single_email worker.
    
    Args:
        state: Current processor state containing emails list
        
    Returns:
        List of Send objects, one per email
    """
    emails = state["emails"]
    return [Send("summarize_single_email", {"email": email}) for email in emails]


def prepare_content_generation(state: ProcessorState) -> dict:
    """
    Synchronization node between email summarization and content generation.
    
    This node serves two purposes:
    1. Acts as a barrier, waiting for all email workers to complete
    2. Prepares newsletter_summaries so both parallel subgraphs have access
    
    The newsletter_summaries are formatted here (not in generate_briefing)
    to avoid race conditions when parallel subgraphs need the same data.
    
    Args:
        state: Current processor state with completed digests
        
    Returns:
        Dict containing formatted newsletter_summaries
    """
    digests = state["digests"]
    logger.info(f"All {len(digests)} emails summarized. Preparing content generation...")
    
    # Format newsletter summaries for both subgraphs
    summaries_text = []
    for digest in digests:
        summary_parts = [f"**{digest.subject}** (from {digest.sender})"]
        
        if digest.summary.industry_news:
            summary_parts.append("Industry News:")
            for item in digest.summary.industry_news:
                summary_parts.append(f"  - {item}")
        
        if digest.summary.new_tools:
            summary_parts.append("New Tools:")
            for item in digest.summary.new_tools:
                summary_parts.append(f"  - {item}")
        
        if digest.summary.insights:
            summary_parts.append("Insights:")
            for item in digest.summary.insights:
                summary_parts.append(f"  - {item}")
        
        summaries_text.append("\n".join(summary_parts))
    
    newsletter_summaries = "\n\n".join(summaries_text)
    
    return {"newsletter_summaries": newsletter_summaries}


# =============================================================================
# Email Summarization Nodes
# =============================================================================

def summarize_email_logic(email, structured_llm: ChatOpenAI) -> CategorySummary:
    """
    Core LLM call for email summarization with structured output.
    
    Uses structured output to ensure consistent CategorySummary format.
    Email body is truncated to 10,000 characters to fit context limits.
    
    Args:
        email: Email object with subject, sender, and body
        structured_llm: ChatOpenAI with structured output for CategorySummary
        
    Returns:
        CategorySummary with industry_news, new_tools, and insights
    """
    prompt = ChatPromptTemplate.from_template(EMAIL_SUMMARIZATION_PROMPT)
    chain = prompt | structured_llm
    
    result = chain.invoke({
        "subject": email.subject,
        "sender": email.sender,
        "body": email.body[:10000]
    })
    
    return result


def summarize_single_email(state: WorkerState, structured_llm: ChatOpenAI) -> dict:
    """
    Worker node that processes a single email.
    
    Called in parallel for each email via the Send pattern.
    Returns either a digest on success or an error message on failure.
    
    Args:
        state: WorkerState containing single email
        structured_llm: LLM with structured output (injected via functools.partial)
        
    Returns:
        Dict with either 'digests' list (success) or 'errors' list (failure)
    """
    email = state["email"]
    logger.info(f"Worker started for: {email.subject[:30]}...")
    
    try:
        summary = summarize_email_logic(email, structured_llm)
        digest = EmailDigest(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            summary=summary
        )
        logger.info(f"✓ Worker finished: {email.subject[:30]}...")
        return {"digests": [digest]}
        
    except Exception as e:
        error_msg = f"Failed to summarize '{email.subject}': {e}"
        logger.error(error_msg)
        return {"errors": [error_msg]}


# =============================================================================
# Digest Subgraph Nodes
# =============================================================================

def generate_briefing(state: ProcessorState, llm: ChatOpenAI) -> dict:
    """
    Generate the aggregated AI briefing from newsletter summaries.
    
    Creates a high-level summary with:
    - "What's Happening in AI Today" - top 5 themes
    - "What This Means for You" - top 5 actionable takeaways
    
    Args:
        state: ProcessorState with newsletter_summaries
        llm: ChatOpenAI instance (injected via functools.partial)
        
    Returns:
        Dict with aggregated_briefing
    """
    newsletter_summaries = state["newsletter_summaries"]
    
    if not newsletter_summaries:
        return {"aggregated_briefing": "No emails to process."}
    
    logger.info(f"Generating aggregated briefing from {len(state['digests'])} digests...")
    
    prompt = ChatPromptTemplate.from_template(DIGEST_BRIEFING_PROMPT)
    chain = prompt | llm
    
    result = chain.invoke({
        "newsletter_summaries": newsletter_summaries
    })
    
    briefing = result.content
    logger.info("✓ Generated aggregated briefing")
    
    return {"aggregated_briefing": briefing}


def quality_check_briefing(state: ProcessorState, llm: ChatOpenAI) -> dict:
    """
    Quality check and improve the AI briefing.
    
    Reviews the briefing for clarity, actionability, curation quality,
    structure, tone, and accuracy. May rewrite if needed.
    
    Args:
        state: ProcessorState with aggregated_briefing
        llm: ChatOpenAI instance (injected via functools.partial)
        
    Returns:
        Dict with reviewed_briefing
    """
    original_briefing = state["aggregated_briefing"]
    
    logger.info("Running quality check on briefing...")
            
    prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_DIGEST_PROMPT)
    chain = prompt | llm
    
    result = chain.invoke({
        "original_briefing": original_briefing
    })
    
    reviewed_briefing = result.content
    logger.info("✓ Quality check complete")
    
    return {"reviewed_briefing": reviewed_briefing}


# =============================================================================
# LinkedIn Subgraph Nodes
# =============================================================================

def generate_linkedin_content(state: ProcessorState, llm: ChatOpenAI) -> dict:
    """
    Generate LinkedIn post ideas and full posts from newsletter summaries.
    
    Creates content including:
    - 3 post ideas with topics, reasons, and source themes
    - 3 complete LinkedIn posts with hooks, emojis, and CTAs
    
    Args:
        state: ProcessorState with newsletter_summaries
        llm: ChatOpenAI instance (injected via functools.partial)
        
    Returns:
        Dict with linkedin_content
    """
    newsletter_summaries = state["newsletter_summaries"]
    
    if not newsletter_summaries:
        return {"linkedin_content": "No content available for LinkedIn posts."}
    
    logger.info("Generating LinkedIn content...")
    
    prompt = ChatPromptTemplate.from_template(LINKEDIN_CONTENT_PROMPT)
    chain = prompt | llm
    
    result = chain.invoke({
        "newsletter_summaries": newsletter_summaries
    })
    
    linkedin_content = result.content
    logger.info("✓ Generated LinkedIn content")
    
    return {"linkedin_content": linkedin_content}


def quality_check_linkedin(state: ProcessorState, llm: ChatOpenAI) -> dict:
    """
    Quality check and improve LinkedIn content.
    
    Reviews for hook quality, brevity, emoji usage, target audience fit,
    clarity, structure, and tone. May rewrite posts if needed.
    
    Args:
        state: ProcessorState with linkedin_content
        llm: ChatOpenAI instance (injected via functools.partial)
        
    Returns:
        Dict with reviewed_linkedin_content
    """
    original_linkedin_content = state["linkedin_content"]
    
    logger.info("Running quality check on LinkedIn content...")
    
    prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_LINKEDIN_PROMPT)
    chain = prompt | llm
    
    result = chain.invoke({
        "original_linkedin_content": original_linkedin_content
    })
    
    reviewed_linkedin_content = result.content
    logger.info("✓ LinkedIn quality check complete")
    
    return {"reviewed_linkedin_content": reviewed_linkedin_content}
