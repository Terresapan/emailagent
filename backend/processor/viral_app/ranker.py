"""Final ranking of app opportunities.

Sorts opportunities by combined score and returns top 20.
"""
import logging
from processor.viral_app.models import AppOpportunity

logger = logging.getLogger(__name__)


def rank_opportunities(
    opportunities: list[AppOpportunity],
    top_n: int = 20,
) -> list[AppOpportunity]:
    """
    Rank opportunities by combined opportunity score.
    
    Args:
        opportunities: List of scored AppOpportunity objects
        top_n: Number of top opportunities to return
        
    Returns:
        Top N opportunities sorted by opportunity_score (descending)
    """
    if not opportunities:
        return []
    
    # Sort by opportunity score (descending)
    ranked = sorted(
        opportunities,
        key=lambda x: x.opportunity_score,
        reverse=True,
    )
    
    logger.info(f"Ranked {len(opportunities)} opportunities, returning top {top_n}")
    
    return ranked[:top_n]


def rank_by_virality(
    opportunities: list[AppOpportunity],
    top_n: int = 10,
) -> list[AppOpportunity]:
    """Rank by virality score only (for viral-focused selection)."""
    return sorted(
        opportunities,
        key=lambda x: x.virality_score,
        reverse=True,
    )[:top_n]


def rank_by_buildability(
    opportunities: list[AppOpportunity],
    top_n: int = 10,
) -> list[AppOpportunity]:
    """Rank by buildability score only (for quick wins)."""
    return sorted(
        opportunities,
        key=lambda x: x.buildability_score,
        reverse=True,
    )[:top_n]


def rank_by_demand(
    opportunities: list[AppOpportunity],
    top_n: int = 10,
) -> list[AppOpportunity]:
    """Rank by demand score only (for validated demand)."""
    return sorted(
        opportunities,
        key=lambda x: x.demand_score,
        reverse=True,
    )[:top_n]
