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
    
Deep Dive Node Functions (Weekly):
    - summarize_deepdive_logic: Core LLM call for essay summarization
    - summarize_single_deepdive: Worker node for individual essay processing
    - prepare_deepdive_content: Synchronization point, formats essay summaries
    - generate_deepdive_briefing: Creates strategic weekly briefing
    - quality_check_deepdive: Reviews and improves the briefing
"""
import time
from typing import List

from langgraph.types import Send
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from processor.states import (
    ProcessorState, WorkerState, EmailDigest, CategorySummary,
    DeepDiveProcessorState, DeepDiveDigest, DeepDiveSummary
)
from processor.prompts import (
    EMAIL_SUMMARIZATION_PROMPT, 
    DIGEST_BRIEFING_PROMPT,
    LINKEDIN_CONTENT_PROMPT,
    QUALITY_CHECK_DIGEST_PROMPT,
    QUALITY_CHECK_LINKEDIN_PROMPT,
    DEEPDIVE_SUMMARIZATION_PROMPT,
    DEEPDIVE_BRIEFING_PROMPT,
    QUALITY_CHECK_DEEPDIVE_PROMPT
)
from config.settings import EMAIL_BODY_MAX_CHARS
from utils.logger import setup_logger
from utils.callbacks import TimingCallbackHandler

logger = setup_logger(__name__)


def _extract_text_content(result) -> str:
    """
    Extract text content from LLM response.
    
    GPT-5 reasoning models return content as a list with:
    - {'type': 'reasoning', 'id': '...', 'summary': [...]} - reasoning block
    - {'type': 'text', 'text': '...', 'annotations': [...]} - actual text block
    
    Args:
        result: LLM response object with .content attribute
        
    Returns:
        Extracted text content as a string
    """
    content = result.content
    
    # If content is already a string, return it
    if isinstance(content, str):
        return content
    
    # If content is a list of content blocks, extract text from each
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                # GPT-5 format: look for 'type': 'text' blocks
                if block.get('type') == 'text' and 'text' in block:
                    text_parts.append(block['text'])
                # Fallback: any dict with 'text' key (non-reasoning blocks)
                elif 'text' in block and block.get('type') != 'reasoning':
                    text_parts.append(block['text'])
                elif 'content' in block:
                    text_parts.append(block['content'])
            elif isinstance(block, str):
                text_parts.append(block)
            elif hasattr(block, 'text'):
                text_parts.append(block.text)
            elif hasattr(block, 'content'):
                text_parts.append(block.content)
        
        extracted = ''.join(text_parts)
        if not extracted:
            # Log warning with details about what we received
            block_info = [(b.get('type', 'unknown') if isinstance(b, dict) else type(b).__name__) for b in content]
            logger.warning(f"Could not extract text from content blocks. Block types: {block_info}")
        return extracted
    
    # Fallback: convert to string
    logger.warning(f"Unexpected content type: {type(content).__name__}")
    return str(content)


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
    start_time = time.time()
    original_len = len(email.body)
    truncated_body = email.body[:EMAIL_BODY_MAX_CHARS]
    truncated_len = len(truncated_body)
    was_truncated = "YES" if original_len > EMAIL_BODY_MAX_CHARS else "NO"
    logger.info(f"📧 Starting LLM call for email ID: {email.id} | Body: {original_len} chars → {truncated_len} chars (truncated: {was_truncated})")
    
    prompt = ChatPromptTemplate.from_template(EMAIL_SUMMARIZATION_PROMPT)
    chain = prompt | structured_llm
    
    try:
        result = chain.invoke({
            "subject": email.subject,
            "sender": email.sender,
            "body": truncated_body
        }, config={"callbacks": [TimingCallbackHandler(f"EMAIL-{email.id[:4]}")]})
        
        duration = time.time() - start_time
        logger.info(f"✅ LLM call completed for ID: {email.id} in {duration:.2f}s")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ LLM call failed for ID: {email.id} after {duration:.2f}s: {e}")
        raise


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
    logger.info(f"Worker started for email ID: {email.id} - {email.subject[:30]}...")
    
    try:
        summary = summarize_email_logic(email, structured_llm)
        digest = EmailDigest(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            summary=summary
        )
        logger.info(f"✓ Worker finished for ID: {email.id} - {email.subject[:30]}...")
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
    
    input_chars = len(newsletter_summaries)
    logger.info(f"🚀 [BRIEFING] Starting LLM call | Input: ~{input_chars} chars (~{input_chars//4} tokens)")
    
    prompt = ChatPromptTemplate.from_template(DIGEST_BRIEFING_PROMPT)
    chain = prompt | llm
    
    start_time = time.time()
    result = chain.invoke({
        "newsletter_summaries": newsletter_summaries
    }, config={"callbacks": [TimingCallbackHandler("BRIEFING")]})
    duration = time.time() - start_time
    
    briefing = _extract_text_content(result)
    output_chars = len(briefing)
    logger.info(f"✅ [BRIEFING] Completed in {duration:.2f}s | Output: ~{output_chars} chars (~{output_chars//4} tokens)")
    
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
    newsletter_summaries = state.get("newsletter_summaries", "")
    
    input_chars = len(original_briefing) + len(newsletter_summaries)
    logger.info(f"🚀 [QC-BRIEFING] Starting LLM call | Input: ~{input_chars} chars (~{input_chars//4} tokens)")
            
    prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_DIGEST_PROMPT)
    chain = prompt | llm
    
    start_time = time.time()
    result = chain.invoke({
        "original_briefing": original_briefing,
        "newsletter_summaries": newsletter_summaries
    }, config={"callbacks": [TimingCallbackHandler("QC-BRIEFING")]})
    duration = time.time() - start_time
    
    reviewed_briefing = _extract_text_content(result)
    output_chars = len(reviewed_briefing)
    logger.info(f"✅ [QC-BRIEFING] Completed in {duration:.2f}s | Output: ~{output_chars} chars (~{output_chars//4} tokens)")
    
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
    
    input_chars = len(newsletter_summaries)
    logger.info(f"🚀 [LINKEDIN] Starting LLM call | Input: ~{input_chars} chars (~{input_chars//4} tokens)")
    
    prompt = ChatPromptTemplate.from_template(LINKEDIN_CONTENT_PROMPT)
    chain = prompt | llm
    
    start_time = time.time()
    result = chain.invoke({
        "newsletter_summaries": newsletter_summaries
    }, config={"callbacks": [TimingCallbackHandler("LINKEDIN")]})
    duration = time.time() - start_time
    
    linkedin_content = _extract_text_content(result)
    output_chars = len(linkedin_content)
    logger.info(f"✅ [LINKEDIN] Completed in {duration:.2f}s | Output: ~{output_chars} chars (~{output_chars//4} tokens)")
    
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
    
    input_chars = len(original_linkedin_content)
    logger.info(f"🚀 [QC-LINKEDIN] Starting LLM call | Input: ~{input_chars} chars (~{input_chars//4} tokens)")
    
    prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_LINKEDIN_PROMPT)
    chain = prompt | llm
    
    start_time = time.time()
    result = chain.invoke({
        "original_linkedin_content": original_linkedin_content
    }, config={"callbacks": [TimingCallbackHandler("QC-LINKEDIN")]})
    duration = time.time() - start_time
    
    reviewed_linkedin_content = _extract_text_content(result)
    output_chars = len(reviewed_linkedin_content)
    logger.info(f"✅ [QC-LINKEDIN] Completed in {duration:.2f}s | Output: ~{output_chars} chars (~{output_chars//4} tokens)")
    
    return {"reviewed_linkedin_content": reviewed_linkedin_content}


# =============================================================================
# Deep Dive Nodes (Weekly)
# =============================================================================

def summarize_deepdive_logic(email, structured_llm: ChatOpenAI) -> DeepDiveSummary:
    """
    Core LLM call for deep dive essay summarization with structured output.
    
    Uses structured output to ensure consistent DeepDiveSummary format.
    Email body is truncated to 12,000 characters to fit context limits.
    
    Args:
        email: Email object with subject, sender, and body
        structured_llm: ChatOpenAI with structured output for DeepDiveSummary
        
    Returns:
        DeepDiveSummary with core_thesis, key_concepts, arguments, evidence, implications
    """
    start_time = time.time()
    original_len = len(email.body)
    truncated_body = email.body[:EMAIL_BODY_MAX_CHARS]
    truncated_len = len(truncated_body)
    was_truncated = "YES" if original_len > EMAIL_BODY_MAX_CHARS else "NO"
    logger.info(f"📖 Starting DEEPDIVE LLM call for ID: {email.id} | Body: {original_len} chars → {truncated_len} chars (truncated: {was_truncated})")
    
    prompt = ChatPromptTemplate.from_template(DEEPDIVE_SUMMARIZATION_PROMPT)
    chain = prompt | structured_llm
    
    try:
        result = chain.invoke({
            "subject": email.subject,
            "sender": email.sender,
            "body": truncated_body
        })
        
        duration = time.time() - start_time
        logger.info(f"✅ DEEPDIVE LLM call completed for ID: {email.id} in {duration:.2f}s")
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"❌ DEEPDIVE LLM call failed for ID: {email.id} after {duration:.2f}s: {e}")
        raise


def summarize_single_deepdive(state: WorkerState, structured_llm: ChatOpenAI) -> dict:
    """
    Worker node that processes a single deep dive essay.
    
    Called in parallel for each essay via the Send pattern.
    Returns either a digest on success or an error message on failure.
    
    Args:
        state: WorkerState containing single email/essay
        structured_llm: LLM with structured output (injected via functools.partial)
        
    Returns:
        Dict with either 'digests' list (success) or 'errors' list (failure)
    """
    email = state["email"]
    logger.info(f"📖 DeepDive worker started for ID: {email.id} - {email.subject[:30]}...")
    
    try:
        summary = summarize_deepdive_logic(email, structured_llm)
        digest = DeepDiveDigest(
            email_id=email.id,
            sender=email.sender,
            subject=email.subject,
            summary=summary
        )
        logger.info(f"✓ DeepDive worker finished for ID: {email.id} - {email.subject[:30]}...")
        return {"digests": [digest]}
        
    except Exception as e:
        error_msg = f"Failed to summarize deep dive '{email.subject}': {e}"
        logger.error(error_msg)
        return {"errors": [error_msg]}


def map_deepdives(state: DeepDiveProcessorState) -> List[Send]:
    """
    Conditional edge function that creates parallel workers for each essay.
    
    Args:
        state: Current processor state containing emails list
        
    Returns:
        List of Send objects, one per email
    """
    emails = state["emails"]
    return [Send("summarize_single_deepdive", {"email": email}) for email in emails]


def prepare_deepdive_content(state: DeepDiveProcessorState) -> dict:
    """
    Synchronization node between essay summarization and briefing generation.
    
    Formats the deep dive summaries so the briefing node has access.
    
    Args:
        state: Current processor state with completed digests
        
    Returns:
        Dict containing formatted deepdive_summaries
    """
    digests = state["digests"]
    logger.info(f"📖 All {len(digests)} essays summarized. Preparing deep dive content...")
    
    # Format essay summaries for briefing
    summaries_text = []
    for digest in digests:
        summary_parts = [f"**{digest.subject}** (by {digest.sender})"]
        
        if digest.summary.core_thesis:
            summary_parts.append(f"Core Thesis: {digest.summary.core_thesis}")
        
        if digest.summary.key_concepts:
            summary_parts.append("Key Concepts:")
            for item in digest.summary.key_concepts:
                summary_parts.append(f"  - {item}")
        
        if digest.summary.primary_arguments:
            summary_parts.append("Primary Arguments:")
            for item in digest.summary.primary_arguments:
                summary_parts.append(f"  - {item}")
        
        if digest.summary.evidence:
            summary_parts.append("Evidence/Examples:")
            for item in digest.summary.evidence:
                summary_parts.append(f"  - {item}")
        
        if digest.summary.implications:
            summary_parts.append("Implications:")
            for item in digest.summary.implications:
                summary_parts.append(f"  - {item}")
        
        summaries_text.append("\n".join(summary_parts))
    
    deepdive_summaries = "\n\n---\n\n".join(summaries_text)
    
    return {"deepdive_summaries": deepdive_summaries}


def generate_deepdive_briefing(state: DeepDiveProcessorState, llm: ChatOpenAI) -> dict:
    """
    Generate the weekly strategic briefing from essay summaries.
    
    Creates a high-level briefing with:
    - "Big Ideas This Week" - top 7 ideas
    - "Where Experts Agree" - convergences
    - "Where the Real Bottlenecks Are" - constraints
    - "What This Changes for Builders" - actionable implications
    
    Args:
        state: DeepDiveProcessorState with deepdive_summaries
        llm: ChatOpenAI instance (injected via functools.partial)
        
    Returns:
        Dict with aggregated_briefing
    """
    deepdive_summaries = state["deepdive_summaries"]
    
    if not deepdive_summaries:
        return {"aggregated_briefing": "No essays to process."}
    
    input_chars = len(deepdive_summaries)
    logger.info(f"🚀 [DEEPDIVE-BRIEFING] Starting LLM call | Input: ~{input_chars} chars (~{input_chars//4} tokens)")
    
    prompt = ChatPromptTemplate.from_template(DEEPDIVE_BRIEFING_PROMPT)
    chain = prompt | llm
    
    start_time = time.time()
    result = chain.invoke({
        "deepdive_summaries": deepdive_summaries
    })
    duration = time.time() - start_time
    
    briefing = _extract_text_content(result)
    output_chars = len(briefing)
    logger.info(f"✅ [DEEPDIVE-BRIEFING] Completed in {duration:.2f}s | Output: ~{output_chars} chars (~{output_chars//4} tokens)")
    
    return {"aggregated_briefing": briefing}


def quality_check_deepdive(state: DeepDiveProcessorState, llm: ChatOpenAI) -> dict:
    """
    Quality check and improve the weekly deep dive briefing.
    
    Reviews for clarity, accuracy, curation, structure, actionability, and tone.
    
    Args:
        state: DeepDiveProcessorState with aggregated_briefing
        llm: ChatOpenAI instance (injected via functools.partial)
        
    Returns:
        Dict with reviewed_briefing
    """
    original_briefing = state["aggregated_briefing"]
    deepdive_summaries = state.get("deepdive_summaries", "")
    
    input_chars = len(original_briefing) + len(deepdive_summaries)
    logger.info(f"🚀 [QC-DEEPDIVE] Starting LLM call | Input: ~{input_chars} chars (~{input_chars//4} tokens)")
            
    prompt = ChatPromptTemplate.from_template(QUALITY_CHECK_DEEPDIVE_PROMPT)
    chain = prompt | llm
    
    start_time = time.time()
    result = chain.invoke({
        "original_briefing": original_briefing,
        "deepdive_summaries": deepdive_summaries
    })
    duration = time.time() - start_time
    
    reviewed_briefing = _extract_text_content(result)
    output_chars = len(reviewed_briefing)
    logger.info(f"✅ [QC-DEEPDIVE] Completed in {duration:.2f}s | Output: ~{output_chars} chars (~{output_chars//4} tokens)")
    
    return {"reviewed_briefing": reviewed_briefing}
