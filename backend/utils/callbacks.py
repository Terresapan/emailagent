"""Callback handlers for timing and logging."""
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TimingCallbackHandler(BaseCallbackHandler):
    """Callback Handler that logs timing metrics (TTFB and total duration)."""

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.start_time = 0.0
        self.first_token_time = 0.0
        self.has_logged_ttfb = False

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""
        self.start_time = time.time()
        self.has_logged_ttfb = False
        logger.info(f"🚀 [{self.name}] Request sent at {time.strftime('%H:%M:%S', time.localtime(self.start_time))}")

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only runs when streaming is enabled."""
        if not self.has_logged_ttfb:
            self.first_token_time = time.time()
            ttfb = self.first_token_time - self.start_time
            logger.info(f"⏳ [{self.name}] First token received (TTFB: {ttfb:.2f}s)")
            self.has_logged_ttfb = True

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        end_time = time.time()
        duration = end_time - self.start_time
        
        # If we never got a token (non-streaming), TTFB is basically duration
        if not self.has_logged_ttfb:
            logger.info(f"⏳ [{self.name}] Response complete (Non-streaming TTFB: {duration:.2f}s)")
        
        logger.info(f"✅ [{self.name}] Complete (Total: {duration:.2f}s)")

    def on_llm_error(
        self, error: Exception, **kwargs: Any
    ) -> None:
        """Run when LLM errors."""
        duration = time.time() - self.start_time
        logger.error(f"❌ [{self.name}] Error after {duration:.2f}s: {error}")
