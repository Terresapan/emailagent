"""Centralized LangSmith tracing configuration.

Call configure_langsmith() once at application startup to enable tracing.
"""
import os
import logging

from config.settings import (
    LANGSMITH_TRACING,
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    LANGSMITH_PROJECT
)

logger = logging.getLogger(__name__)


def configure_langsmith() -> bool:
    """
    Configure LangSmith tracing environment variables.
    
    Should be called once at application startup (e.g., in main.py).
    
    Returns:
        True if tracing was enabled, False otherwise
    """
    if LANGSMITH_TRACING and LANGSMITH_API_KEY:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
        logger.info(f"LangSmith tracing enabled for project: {LANGSMITH_PROJECT}")
        return True
    else:
        logger.debug("LangSmith tracing not configured (missing API key or disabled)")
        return False
