"""
LangGraph-based email summarizer with parallel processing and quality checking.

This module defines the EmailSummarizer class which orchestrates the email
processing workflow using LangGraph. The workflow includes:

1. Parallel email summarization (map-reduce pattern)
2. Parallel content generation via subgraphs:
   - Digest subgraph: briefing generation + quality check
   - LinkedIn subgraph: content generation + quality check

Architecture:
    distribute_emails → [summarize workers] → prepare_content_generation
                                                        ↓
                                              ┌─────────┴─────────┐
                                              ↓                   ↓
                                        digest_branch       linkedin_branch
                                              ↓                   ↓
                                             END                 END

See processor/graph.png for visual representation.
Run `python processor/visualize_graph.py` to regenerate the diagram.
"""
import os
import functools
from typing import List

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.types import Send

from .states import (
    Email, DailyDigest, ProcessorState,
    WeeklyDeepDive, DeepDiveProcessorState, DeepDiveSummary
)
from .nodes import (
    distribute_emails,
    map_emails,
    prepare_content_generation,
    summarize_single_email,
    generate_briefing,
    generate_linkedin_content,
    quality_check_briefing,
    quality_check_linkedin,
    # Deep dive nodes
    map_deepdives,
    summarize_single_deepdive,
    prepare_deepdive_content,
    generate_deepdive_briefing,
    quality_check_deepdive
)
from config.settings import (
    OPENAI_API_KEY, 
    LLM_MODEL_EXTRACTION,
    LLM_MODEL_GENERATION,
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
    LLM_REASONING_EFFORT_EXTRACTION,
    LLM_REASONING_EFFORT_GENERATION,
)
from config.langsmith import configure_langsmith
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Configure LangSmith tracing (centralized)
configure_langsmith()


class EmailSummarizer:
    """
    LangGraph-based email processing agent with parallel processing.
    
    Orchestrates a workflow that:
    1. Processes multiple emails in parallel using map-reduce
    2. Generates digest briefing and LinkedIn content in parallel via subgraphs
    3. Quality-checks all generated content
    
    Attributes:
        llm: ChatOpenAI instance for content generation
        structured_llm: ChatOpenAI with structured output for email summarization
        graph: Compiled LangGraph workflow
        
    Example:
        summarizer = EmailSummarizer()
        digest = summarizer.process_emails(emails)
    """
    
    def __init__(self):
        """
        Initialize the EmailSummarizer with LLM and compiled graph.
        
        Creates two LLMs with different reasoning efforts:
        - extraction_llm: Low effort for email summarization (faster)
        - generation_llm: Medium effort for content generation (better quality)
        """
        # LLM for extraction tasks (email summarization) - nano model with low reasoning
        self.extraction_llm = ChatOpenAI(
            model=LLM_MODEL_EXTRACTION,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            reasoning={"effort": LLM_REASONING_EFFORT_EXTRACTION}
        )
        
        # LLM for content generation (briefing, LinkedIn) - mini model with medium reasoning
        self.llm = ChatOpenAI(
            model=LLM_MODEL_GENERATION,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            reasoning={"effort": LLM_REASONING_EFFORT_GENERATION}
        )
        
        # Create structured output LLM for category summaries (uses extraction LLM)
        from processor.email.states import CategorySummary
        self.structured_llm = self.extraction_llm.with_structured_output(CategorySummary)
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info(f"Initialized EmailSummarizer | Extraction: {LLM_MODEL_EXTRACTION} ({LLM_REASONING_EFFORT_EXTRACTION}), Generation: {LLM_MODEL_GENERATION} ({LLM_REASONING_EFFORT_GENERATION})")
    
    def _build_digest_subgraph(self):
        """
        Build subgraph for digest generation and quality check.
        
        Flow: generate_briefing → quality_check_digest → END
        
        Returns:
            Compiled StateGraph for digest processing
        """
        subgraph = StateGraph(ProcessorState)
        
        generate_node = functools.partial(generate_briefing, llm=self.llm)
        quality_node = functools.partial(quality_check_briefing, llm=self.llm)
        
        subgraph.add_node("generate_briefing", generate_node)
        subgraph.add_node("quality_check_digest", quality_node)
        
        subgraph.set_entry_point("generate_briefing")
        subgraph.add_edge("generate_briefing", "quality_check_digest")
        subgraph.add_edge("quality_check_digest", END)
        
        return subgraph.compile()
    
    def _build_linkedin_subgraph(self):
        """
        Build subgraph for LinkedIn content generation and quality check.
        
        Flow: generate_linkedin_content → quality_check_linkedin → END
        
        Returns:
            Compiled StateGraph for LinkedIn content processing
        """
        subgraph = StateGraph(ProcessorState)
        
        linkedin_node = functools.partial(generate_linkedin_content, llm=self.llm)
        quality_node = functools.partial(quality_check_linkedin, llm=self.llm)
        
        subgraph.add_node("generate_linkedin_content", linkedin_node)
        subgraph.add_node("quality_check_linkedin", quality_node)
        
        subgraph.set_entry_point("generate_linkedin_content")
        subgraph.add_edge("generate_linkedin_content", "quality_check_linkedin")
        subgraph.add_edge("quality_check_linkedin", END)
        
        return subgraph.compile()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the main LangGraph workflow with parallel processing.
        
        The workflow has three phases:
        1. Distribution: Fan-out emails to parallel workers
        2. Summarization: Each worker processes one email (map-reduce)
        3. Content Generation: Parallel subgraphs for digest and LinkedIn
        
        Returns:
            Compiled StateGraph ready for invocation
        """
        workflow = StateGraph(ProcessorState)
        
        # Bind LLM to summarization node
        summarize_node = functools.partial(
            summarize_single_email, 
            structured_llm=self.structured_llm
        )
        
        # Build compiled subgraphs for parallel content generation
        digest_subgraph = self._build_digest_subgraph()
        linkedin_subgraph = self._build_linkedin_subgraph()

        # Add nodes
        workflow.add_node("distribute_emails", distribute_emails)
        workflow.add_node("summarize_single_email", summarize_node)
        workflow.add_node("prepare_content_generation", prepare_content_generation)
        workflow.add_node("digest_branch", digest_subgraph)
        workflow.add_node("linkedin_branch", linkedin_subgraph)
        
        # Entry point
        workflow.set_entry_point("distribute_emails")
        
        # Phase 1: Fan-out to parallel email workers
        workflow.add_conditional_edges(
            "distribute_emails", 
            map_emails, 
            ["summarize_single_email"]
        )
        
        # Phase 2: Workers converge at synchronization node
        workflow.add_edge("summarize_single_email", "prepare_content_generation")
        
        # Phase 3: Fan-out to parallel subgraphs using Send pattern
        def fan_out_to_subgraphs(state: ProcessorState):
            """Fan out to run both digest and linkedin subgraphs in parallel."""
            return [
                Send("digest_branch", state),
                Send("linkedin_branch", state)
            ]
        
        workflow.add_conditional_edges(
            "prepare_content_generation", 
            fan_out_to_subgraphs,
            ["digest_branch", "linkedin_branch"]
        )
        
        # Both subgraphs complete before END
        workflow.add_edge("digest_branch", END)
        workflow.add_edge("linkedin_branch", END)
        
        return workflow.compile()
    
    def process_emails(self, emails: List[Email]) -> DailyDigest:
        """
        Process a list of emails through the LangGraph workflow.
        
        Runs the complete pipeline: summarization, briefing generation,
        LinkedIn content creation, and quality checks for all content.
        
        Args:
            emails: List of Email objects to process
            
        Returns:
            DailyDigest containing:
                - emails_processed: List of processed email identifiers
                - digests: Individual EmailDigest for each email
                - aggregated_briefing: Quality-checked AI briefing
                - newsletter_summaries: Raw formatted summaries
                - linkedin_content: Quality-checked LinkedIn posts
        """
        logger.info(f"Processing {len(emails)} emails through LangGraph workflow...")
        
        # Initialize state with empty fields
        initial_state = {
            "emails": emails,
            "digests": [],
            "aggregated_briefing": "",
            "newsletter_summaries": "",
            "reviewed_briefing": "",
            "linkedin_content": "",
            "reviewed_linkedin_content": "",
            "errors": []
        }
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state)
        
        # Build result
        emails_processed = [
            f"{digest.sender}: {digest.subject}" 
            for digest in final_state["digests"]
        ]
        
        daily_digest = DailyDigest(
            emails_processed=emails_processed,
            digests=final_state["digests"],
            aggregated_briefing=final_state["reviewed_briefing"],
            newsletter_summaries=final_state["newsletter_summaries"],
            linkedin_content=final_state["reviewed_linkedin_content"]
        )
        
        # Log completion
        logger.info(
            f"✓ LangGraph processing complete. "
            f"Processed {len(final_state['digests'])} emails, "
            f"{len(final_state['errors'])} errors"
        )
        
        if final_state["errors"]:
            for error in final_state["errors"]:
                logger.warning(f"  Error: {error}")
        
        return daily_digest


class DeepDiveSummarizer:
    """
    LangGraph-based deep dive processing agent for weekly essay summarization.
    
    Orchestrates a workflow that:
    1. Processes long-form essays in parallel using map-reduce
    2. Generates a strategic weekly briefing
    3. Quality-checks the briefing
    
    No LinkedIn content generation - deep dives are strategic, not social.
    
    Attributes:
        llm: ChatOpenAI instance for content generation
        structured_llm: ChatOpenAI with structured output for essay summarization
        graph: Compiled LangGraph workflow
        
    Example:
        summarizer = DeepDiveSummarizer()
        weekly_digest = summarizer.process_emails(essays)
    """
    
    def __init__(self):
        """
        Initialize the DeepDiveSummarizer with LLM and compiled graph.
        """
        # LLM for extraction tasks (essay summarization) - nano model with low reasoning
        self.extraction_llm = ChatOpenAI(
            model=LLM_MODEL_EXTRACTION,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            reasoning={"effort": LLM_REASONING_EFFORT_EXTRACTION}
        )
        
        # LLM for content generation (briefing) - mini model with medium reasoning
        self.llm = ChatOpenAI(
            model=LLM_MODEL_GENERATION,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            reasoning={"effort": LLM_REASONING_EFFORT_GENERATION}
        )
        
        # Create structured output LLM for deep dive summaries
        self.structured_llm = self.extraction_llm.with_structured_output(DeepDiveSummary)
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
        
        logger.info(f"Initialized DeepDiveSummarizer | Extraction: {LLM_MODEL_EXTRACTION}, Generation: {LLM_MODEL_GENERATION}")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for deep dive processing.
        
        Simpler than EmailSummarizer - no LinkedIn branch.
        
        Flow: distribute → summarize_workers → prepare_content → briefing → quality_check → END
        
        Returns:
            Compiled StateGraph ready for invocation
        """
        workflow = StateGraph(DeepDiveProcessorState)
        
        # Bind LLM to summarization node
        summarize_node = functools.partial(
            summarize_single_deepdive, 
            structured_llm=self.structured_llm
        )
        
        # Bind LLM to generation nodes
        briefing_node = functools.partial(generate_deepdive_briefing, llm=self.llm)
        quality_node = functools.partial(quality_check_deepdive, llm=self.llm)

        # Add nodes
        workflow.add_node("distribute_emails", distribute_emails)
        workflow.add_node("summarize_single_deepdive", summarize_node)
        workflow.add_node("prepare_deepdive_content", prepare_deepdive_content)
        workflow.add_node("generate_briefing", briefing_node)
        workflow.add_node("quality_check", quality_node)
        
        # Entry point
        workflow.set_entry_point("distribute_emails")
        
        # Phase 1: Fan-out to parallel essay workers
        workflow.add_conditional_edges(
            "distribute_emails", 
            map_deepdives, 
            ["summarize_single_deepdive"]
        )
        
        # Phase 2: Workers converge at synchronization node
        workflow.add_edge("summarize_single_deepdive", "prepare_deepdive_content")
        
        # Phase 3: Generate and quality check briefing (sequential, no LinkedIn)
        workflow.add_edge("prepare_deepdive_content", "generate_briefing")
        workflow.add_edge("generate_briefing", "quality_check")
        workflow.add_edge("quality_check", END)
        
        return workflow.compile()
    
    def process_emails(self, emails: List[Email]) -> WeeklyDeepDive:
        """
        Process a list of essays through the LangGraph workflow.
        
        Runs the complete pipeline: summarization, briefing generation,
        and quality check.
        
        Args:
            emails: List of Email objects (essays) to process
            
        Returns:
            WeeklyDeepDive containing:
                - emails_processed: List of processed essay identifiers
                - digests: Individual DeepDiveDigest for each essay
                - aggregated_briefing: Quality-checked strategic briefing
                - deepdive_summaries: Raw formatted summaries
        """
        logger.info(f"Processing {len(emails)} essays through DeepDive workflow...")
        
        # Initialize state with empty fields
        initial_state = {
            "emails": emails,
            "digests": [],
            "aggregated_briefing": "",
            "deepdive_summaries": "",
            "reviewed_briefing": "",
            "errors": []
        }
        
        # Execute the graph
        final_state = self.graph.invoke(initial_state)
        
        # Build result
        emails_processed = [
            f"{digest.sender}: {digest.subject}" 
            for digest in final_state["digests"]
        ]
        
        weekly_digest = WeeklyDeepDive(
            emails_processed=emails_processed,
            digests=final_state["digests"],
            aggregated_briefing=final_state["reviewed_briefing"],
            deepdive_summaries=final_state["deepdive_summaries"]
        )
        
        # Log completion
        logger.info(
            f"✓ DeepDive processing complete. "
            f"Processed {len(final_state['digests'])} essays, "
            f"{len(final_state['errors'])} errors"
        )
        
        if final_state["errors"]:
            for error in final_state["errors"]:
                logger.warning(f"  Error: {error}")
        
        return weekly_digest
