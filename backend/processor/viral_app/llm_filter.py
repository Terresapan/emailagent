"""LLM-based filtering of pain points.

Uses 1 LLM call to filter 100-145 raw pain points down to 45 unique candidates.
Removes enterprise, highly technical, and off-topic pain points.
"""
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from config.settings import LLM_MODEL_EXTRACTION, LLM_MAX_TOKENS
from processor.viral_app.models import PainPoint

logger = logging.getLogger(__name__)


FILTER_PROMPT = """You are a filter for app ideas targeting individual creators, freelancers, and small business owners.

Given a list of pain points, filter OUT:
1. Enterprise/corporate problems (require team collaboration, compliance, etc.)
2. Highly technical problems (require ML expertise, infrastructure, etc.)
3. Problems that already have obvious simple solutions
4. Vague or unclear pain points
5. Duplicate or near-duplicate problems

KEEP pain points that:
1. Can be solved by a simple web app (2-4 hours to build)
2. Target individuals or small teams
3. Have clear, actionable problems
4. Could go viral (visual, shareable, "wow factor")

For each KEPT pain point, output on a single line:
INDEX | PROBLEM

Where INDEX is the original number and PROBLEM is the pain point.
Output at most {max_candidates} pain points.

Pain points to filter:
{pain_points}

Output the filtered list (one per line, INDEX | PROBLEM format):
"""


class LLMFilter:
    """Filters pain points using LLM."""
    
    def __init__(self, model: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model or LLM_MODEL_EXTRACTION,
            temperature=0.2,
            max_tokens=LLM_MAX_TOKENS,
        )
        self.call_count = 0
    
    def filter_pain_points(
        self,
        pain_points: list[PainPoint],
        max_candidates: int = 45,
    ) -> list[PainPoint]:
        """
        Filter raw pain points to actionable candidates.
        
        Args:
            pain_points: Raw pain points from extraction
            max_candidates: Maximum candidates to return
            
        Returns:
            Filtered list of pain points
        """
        if not pain_points:
            return []
        
        # Format for prompt
        formatted = self._format_pain_points(pain_points)
        
        # Call LLM
        prompt = FILTER_PROMPT.format(
            pain_points=formatted,
            max_candidates=max_candidates,
        )
        
        try:
            response = self.llm.invoke(prompt)
            self.call_count += 1
            logger.info(f"LLM filter call #{self.call_count}")
            
            # Parse response
            filtered = self._parse_response(response.content, pain_points)
            logger.info(f"Filtered {len(pain_points)} → {len(filtered)} candidates")
            return filtered
            
        except Exception as e:
            logger.error(f"LLM filter failed: {e}")
            # Fallback: return first N pain points
            return pain_points[:max_candidates]
    
    def _format_pain_points(self, pain_points: list[PainPoint]) -> str:
        """Format pain points for the prompt."""
        lines = []
        for i, pp in enumerate(pain_points, 1):
            source_tag = f"[{pp.source}]"
            lines.append(f"{i}. {source_tag} {pp.problem}")
        return "\n".join(lines)
    
    def _parse_response(
        self, 
        response: str, 
        original: list[PainPoint],
    ) -> list[PainPoint]:
        """Parse LLM response to get filtered pain points."""
        filtered = []
        
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            
            parts = line.split("|", 1)
            if len(parts) != 2:
                continue
            
            try:
                # Parse index (may have extra text)
                index_str = parts[0].strip().split(".")[0].strip()
                index = int(index_str) - 1  # Convert to 0-indexed
                
                if 0 <= index < len(original):
                    filtered.append(original[index])
            except (ValueError, IndexError):
                continue
        
        return filtered
    
    def get_call_count(self) -> int:
        """Return the number of LLM calls made."""
        return self.call_count
