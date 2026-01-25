"""Data models for viral app discovery."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal


@dataclass
class PainPoint:
    """A pain point extracted from social media or reviews."""
    
    text: str  # Original text containing the pain point
    problem: str  # Extracted problem statement
    source: Literal["reddit", "twitter", "youtube", "producthunt"]
    source_id: str  # Post ID, tweet ID, video ID, etc.
    engagement: int = 0  # Upvotes, likes, views
    extracted_at: datetime = field(default_factory=datetime.now)
    
    # Optional metadata
    subreddit: Optional[str] = None
    channel: Optional[str] = None
    query: Optional[str] = None


@dataclass
class AppOpportunity:
    """A ranked app opportunity for building."""
    
    # Core fields
    problem: str  # The pain point / problem to solve
    app_idea: str  # Suggested mini-app concept
    
    # Scores (0-100)
    demand_score: int = 0  # Market validation (similar products on PH)
    virality_score: int = 0  # Engagement score (aggregated from sources)
    buildability_score: int = 0  # Ease of building in 2-4 hours
    opportunity_score: int = 0  # Combined weighted score
    
    # Sources - supports multi-source clusters
    pain_points: list[PainPoint] = field(default_factory=list)
    source_breakdown: dict[str, int] = field(default_factory=dict)  # {"reddit": 120, "twitter": 45}
    
    # Metadata
    category: Optional[str] = None  # e.g., "productivity", "automation"
    target_audience: Optional[str] = None  # e.g., "small business owners"
    similar_products: list[str] = field(default_factory=list)
    
    # Trend validation (legacy, may be empty)
    search_volume: Optional[int] = None
    trend_direction: Optional[str] = None  # "rising", "stable", "declining"
    related_queries: list[str] = field(default_factory=list)


@dataclass
class DiscoveryState:
    """State object for the LangGraph discovery workflow."""
    
    # Raw data from APIs
    reddit_posts: list[dict] = field(default_factory=list)
    reddit_comments: list[dict] = field(default_factory=list)
    tweets: list[dict] = field(default_factory=list)
    youtube_videos: list[dict] = field(default_factory=list)
    youtube_comments: list[dict] = field(default_factory=list)
    producthunt_products: list[dict] = field(default_factory=list)
    
    # Extracted pain points (per source)
    raw_pain_points: list[PainPoint] = field(default_factory=list)
    
    # Filtered candidates
    filtered_candidates: list[PainPoint] = field(default_factory=list)
    
    # Validated and scored opportunities
    opportunities: list[AppOpportunity] = field(default_factory=list)
    
    # Final ranked output
    top_opportunities: list[AppOpportunity] = field(default_factory=list)
    
    # Metadata
    run_date: datetime = field(default_factory=datetime.now)
    api_usage: dict = field(default_factory=dict)


@dataclass
class SaturdayBriefing:
    """The final Saturday briefing output."""
    
    date: datetime
    top_opportunities: list[AppOpportunity]
    
    # Source data for dashboard
    youtube_videos: list[dict] = field(default_factory=list)  # {id, title, views, channel, url}
    trends_data: list[dict] = field(default_factory=list)  # {keyword, interest_score, related_queries, trend_direction}
    
    # Stats
    total_data_points: int = 0
    total_pain_points_extracted: int = 0
    total_candidates_filtered: int = 0
    
    # API usage summary
    arcade_calls: int = 0
    serpapi_calls: int = 0
    youtube_quota: int = 0
    llm_calls: int = 0
    estimated_cost: float = 0.0
