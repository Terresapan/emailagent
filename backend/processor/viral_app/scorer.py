"""Scoring system for app opportunities.

Calculates Virality, Buildability, and combined Opportunity scores.
Uses 1 LLM call to score all candidates.
"""
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

from config.settings import LLM_MODEL_EXTRACTION, LLM_MAX_TOKENS
from processor.viral_app.models import PainPoint, AppOpportunity

logger = logging.getLogger(__name__)


SCORING_PROMPT = """You are an app idea scorer. For each pain point, generate:
1. An app idea (simple mini-app that solves the problem)
2. Virality score (0-100): How likely is this app to go viral?
3. Buildability score (0-100): How easy is this to build in 2-4 hours?

VIRALITY SCORING:
- 90-100: Visual transformation, instant wow factor, highly shareable
- 70-89: Useful and novel, people would share with friends
- 50-69: Practical but not exciting
- 0-49: Boring or niche

BUILDABILITY SCORING:
- 90-100: Simple UI, single API call, no auth needed
- 70-89: Small frontend + simple backend, 1-2 APIs
- 50-69: Moderate complexity, may need auth or database
- 0-49: Complex, requires ML/AI training, multiple integrations

For each pain point, output ONE LINE in this format:
INDEX | APP_IDEA | VIRALITY | BUILDABILITY

Example:
1 | Invoice screenshot to spreadsheet converter | 85 | 90
2 | AI meeting notes summarizer | 70 | 65

Pain points to score:
{pain_points}

Output scores (one per line):
"""


class Scorer:
    """Scores pain points for virality and buildability."""
    
    def __init__(self, model: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model or LLM_MODEL_EXTRACTION,
            temperature=0.3,
            max_tokens=LLM_MAX_TOKENS,
        )
        self.call_count = 0
    
    def score_pain_points(
        self,
        pain_points: list[PainPoint],
        demand_scores: Optional[dict[int, int]] = None,
    ) -> list[AppOpportunity]:
        """
        Score pain points and convert to AppOpportunity objects.
        
        Args:
            pain_points: Filtered pain points
            demand_scores: Optional dict mapping index to demand score from SerpAPI
            
        Returns:
            List of scored AppOpportunity objects
        """
        if not pain_points:
            return []
        
        demand_scores = demand_scores or {}
        
        # Format for prompt
        formatted = self._format_pain_points(pain_points)
        
        # Call LLM
        prompt = SCORING_PROMPT.format(pain_points=formatted)
        
        try:
            response = self.llm.invoke(prompt)
            self.call_count += 1
            logger.info(f"LLM scoring call #{self.call_count}")
            
            # Parse response
            opportunities = self._parse_response(
                response.content, 
                pain_points, 
                demand_scores,
            )
            logger.info(f"Scored {len(opportunities)} opportunities")
            return opportunities
            
        except Exception as e:
            logger.error(f"LLM scoring failed: {e}")
            return []
    
    def _format_pain_points(self, pain_points: list[PainPoint]) -> str:
        """Format pain points for the prompt."""
        lines = []
        for i, pp in enumerate(pain_points, 1):
            lines.append(f"{i}. {pp.problem}")
        return "\n".join(lines)
    
    def _parse_response(
        self,
        response: str,
        pain_points: list[PainPoint],
        demand_scores: dict[int, int],
    ) -> list[AppOpportunity]:
        """Parse LLM response into AppOpportunity objects."""
        opportunities = []
        
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line or "|" not in line:
                continue
            
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            
            try:
                # Parse index
                index_str = parts[0].split(".")[0].strip()
                index = int(index_str) - 1
                
                if index < 0 or index >= len(pain_points):
                    continue
                
                app_idea = parts[1].strip()
                virality = int(parts[2].strip())
                buildability = int(parts[3].strip())
                
                # Get demand score from SerpAPI validation
                demand = demand_scores.get(index, 50)  # Default 50 if not validated
                
                # Calculate combined opportunity score
                # Formula: Demand 40%, Virality 40%, Buildability 20%
                opportunity_score = int(
                    demand * 0.4 +
                    virality * 0.4 +
                    buildability * 0.2
                )
                
                pp = pain_points[index]
                
                opportunities.append(AppOpportunity(
                    problem=pp.problem,
                    app_idea=app_idea,
                    demand_score=demand,
                    virality_score=virality,
                    buildability_score=buildability,
                    opportunity_score=opportunity_score,
                    pain_points=[pp],
                ))
                
            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse scoring line: {line} - {e}")
                continue
        
        return opportunities
    
    def get_call_count(self) -> int:
        """Return the number of LLM calls made."""
        return self.call_count


def calculate_opportunity_score(
    demand: int,
    virality: int,
    buildability: int,
) -> int:
    """
    Calculate combined opportunity score.
    
    Formula: Demand 40% + Virality 40% + Buildability 20%
    
    This weights demand and virality equally (most important),
    with buildability as a tie-breaker.
    """
    return int(demand * 0.4 + virality * 0.4 + buildability * 0.2)
