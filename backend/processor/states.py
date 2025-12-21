"""
Pydantic models and state definitions for email processing.

This module defines:
1. Data models (Pydantic BaseModel):
   - Email: Input email data
   - CategorySummary: Structured LLM output for email categorization
   - EmailDigest: Summary of a single email
   - DailyDigest: Complete output of the processing pipeline

2. State definitions (TypedDict):
   - ProcessorState: Main workflow state with reducers for parallel merging
   - WorkerState: State for individual email worker nodes

3. Reducer functions:
   - last_non_empty: Keeps last non-empty string (for parallel merges)
   - last_list: Keeps last non-empty list (for parallel merges)
"""
from typing import List, TypedDict, Annotated
from operator import add
from datetime import date

from pydantic import BaseModel, Field


# =============================================================================
# Pydantic Data Models
# =============================================================================

class Email(BaseModel):
    """
    Input email data model.
    
    Attributes:
        id: Unique email identifier from Gmail
        sender: Email sender address
        subject: Email subject line
        body: Full email body text
    """
    id: str
    sender: str
    subject: str
    body: str


class CategorySummary(BaseModel):
    """
    Structured output for email summarization.
    
    Used with ChatOpenAI.with_structured_output() to ensure
    consistent categorization of newsletter content.
    
    Attributes:
        industry_news: Bullet points about industry news and trends
        new_tools: Bullet points about new tools and products
        insights: Bullet points about insights and analysis
    """
    industry_news: List[str] = Field(
        default_factory=list,
        description="Bullet points about industry news and trends"
    )
    new_tools: List[str] = Field(
        default_factory=list,
        description="Bullet points about new tools and products"
    )
    insights: List[str] = Field(
        default_factory=list,
        description="Bullet points about insights and analysis"
    )


class EmailDigest(BaseModel):
    """
    Summary of a single processed email.
    
    Attributes:
        email_id: Original email ID for tracking
        sender: Email sender for attribution
        subject: Email subject for reference
        summary: Categorized summary content
    """
    email_id: str
    sender: str
    subject: str
    summary: CategorySummary


class DailyDigest(BaseModel):
    """
    Complete output of the email processing pipeline.
    
    This is the final result returned by EmailSummarizer.process_emails().
    Contains all processed content ready for email delivery.
    
    Attributes:
        date: Processing date (auto-generated)
        emails_processed: List of "sender: subject" strings
        digests: Individual EmailDigest for each email
        aggregated_briefing: Quality-checked AI briefing
        newsletter_summaries: Raw formatted summaries
        linkedin_content: Quality-checked LinkedIn posts
    """
    date: str = Field(default_factory=lambda: date.today().isoformat())
    emails_processed: List[str] = Field(
        default_factory=list,
        description="List of email subjects processed"
    )
    digests: List[EmailDigest] = Field(
        default_factory=list,
        description="Individual email digests"
    )
    aggregated_briefing: str = Field(
        default="",
        description="High-level aggregated briefing"
    )
    newsletter_summaries: str = Field(
        default="",
        description="Raw text of all newsletter summaries"
    )
    linkedin_content: str = Field(
        default="",
        description="LinkedIn post ideas and full posts"
    )


# =============================================================================
# Deep Dive Pydantic Models (Weekly)
# =============================================================================

class DeepDiveSummary(BaseModel):
    """
    Structured output for deep dive essay summarization.
    
    Used with ChatOpenAI.with_structured_output() for essays.
    
    Attributes:
        core_thesis: Author's central argument (1-2 sentences)
        key_concepts: Named concepts or frameworks from the essay
        primary_arguments: Top arguments supporting the thesis
        evidence: Concrete examples or cases used
        implications: Stated implications for work/tech/AI
    """
    core_thesis: str = Field(
        default="",
        description="1-2 sentences stating the author's central argument"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Up to 5 named concepts or frameworks from the essay"
    )
    primary_arguments: List[str] = Field(
        default_factory=list,
        description="Top 5 arguments supporting the thesis"
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Up to 5 concrete examples or cases"
    )
    implications: List[str] = Field(
        default_factory=list,
        description="Up to 5 implications the author states"
    )


class DeepDiveDigest(BaseModel):
    """
    Summary of a single processed deep dive essay.
    
    Attributes:
        email_id: Original email ID for tracking
        sender: Email sender (author) for attribution
        subject: Email/essay subject for reference
        summary: Structured summary of the essay
    """
    email_id: str
    sender: str
    subject: str
    summary: DeepDiveSummary


class WeeklyDeepDive(BaseModel):
    """
    Complete output of the weekly deep dive processing pipeline.
    
    This is the final result returned by DeepDiveSummarizer.process_emails().
    Contains all processed content ready for email delivery.
    No LinkedIn content - deep dives are strategic, not social.
    
    Attributes:
        date: Processing date (auto-generated)
        emails_processed: List of "sender: subject" strings
        digests: Individual DeepDiveDigest for each essay
        aggregated_briefing: Quality-checked strategic briefing
        deepdive_summaries: Raw formatted essay summaries
    """
    date: str = Field(default_factory=lambda: date.today().isoformat())
    emails_processed: List[str] = Field(
        default_factory=list,
        description="List of essays processed"
    )
    digests: List[DeepDiveDigest] = Field(
        default_factory=list,
        description="Individual essay digests"
    )
    aggregated_briefing: str = Field(
        default="",
        description="Strategic weekly briefing"
    )
    deepdive_summaries: str = Field(
        default="",
        description="Raw text of all essay summaries"
    )


# =============================================================================
# Reducer Functions for Parallel State Merging
# =============================================================================

def last_non_empty(left: str, right: str) -> str:
    """
    Reducer that keeps the last non-empty string value.
    
    Used for state fields updated by parallel subgraphs.
    When both subgraphs complete, this ensures the non-empty
    value is preserved (e.g., briefing from digest_branch,
    linkedin_content from linkedin_branch).
    
    Args:
        left: Previous state value
        right: New value from parallel branch
        
    Returns:
        right if non-empty, otherwise left
    """
    return right if right else left


def last_list(left: List, right: List) -> List:
    """
    Reducer that keeps the last non-empty list value.
    
    Used for the emails field which is passed through
    but not modified by content generation subgraphs.
    
    Args:
        left: Previous list value
        right: New list value from parallel branch
        
    Returns:
        right if non-empty, otherwise left
    """
    return right if right else left


def add_unique_digests(left: List, right: List) -> List:
    """
    Reducer that combines EmailDigest lists while ensuring uniqueness by email_id.
    
    When parallel subgraphs (digest_branch, linkedin_branch) complete and merge,
    they each return their copy of the digests list. Using the standard `add`
    reducer would triple the list. This reducer ensures each email_id appears
    only once.
    
    Args:
        left: Previous list of EmailDigest objects
        right: New list from parallel branch
        
    Returns:
        Combined list with unique email_ids (preserves order, keeps first seen)
    """
    seen_ids = set()
    result = []
    
    for digest in left + right:
        if digest.email_id not in seen_ids:
            seen_ids.add(digest.email_id)
            result.append(digest)
    
    return result


# =============================================================================
# LangGraph State Definitions
# =============================================================================

class ProcessorState(TypedDict):
    """
    Main workflow state for the email processing graph.
    
    All fields that may receive concurrent updates from parallel
    subgraphs must have reducers to handle state merging.
    
    Attributes:
        emails: Input emails (last_list for parallel merge)
        digests: Accumulated EmailDigest objects (add_unique_digests for deduplication)
        aggregated_briefing: Raw briefing before quality check
        newsletter_summaries: Formatted summaries for content generation
        reviewed_briefing: Quality-checked briefing (final output)
        linkedin_content: Raw LinkedIn content before quality check
        reviewed_linkedin_content: Quality-checked LinkedIn (final output)
        errors: Accumulated error messages (add for combining)
    """
    emails: Annotated[List[Email], last_list]
    digests: Annotated[List[EmailDigest], add_unique_digests]
    aggregated_briefing: Annotated[str, last_non_empty]
    newsletter_summaries: Annotated[str, last_non_empty]
    reviewed_briefing: Annotated[str, last_non_empty]
    linkedin_content: Annotated[str, last_non_empty]
    reviewed_linkedin_content: Annotated[str, last_non_empty]
    errors: Annotated[List[str], add]


class WorkerState(TypedDict):
    """
    State for individual email worker nodes.
    
    Used by summarize_single_email when processing emails
    in parallel via the Send pattern.
    
    Attributes:
        email: Single Email object to process
    """
    email: Email


class DeepDiveProcessorState(TypedDict):
    """
    Workflow state for the deep dive processing graph.
    
    Simpler than ProcessorState - no LinkedIn content generation.
    
    Attributes:
        emails: Input emails/essays
        digests: Accumulated DeepDiveDigest objects
        aggregated_briefing: Raw briefing before quality check
        deepdive_summaries: Formatted essay summaries
        reviewed_briefing: Quality-checked briefing (final output)
        errors: Accumulated error messages
    """
    emails: Annotated[List[Email], last_list]
    digests: Annotated[List[DeepDiveDigest], add_unique_digests]
    aggregated_briefing: Annotated[str, last_non_empty]
    deepdive_summaries: Annotated[str, last_non_empty]
    reviewed_briefing: Annotated[str, last_non_empty]
    errors: Annotated[List[str], add]
