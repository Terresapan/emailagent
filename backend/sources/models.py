"""Pydantic models for third-party data sources."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ProductLaunch(BaseModel):
    """A product launch from Product Hunt."""
    id: str
    name: str
    tagline: str
    description: Optional[str] = None
    votes: int = Field(alias="votesCount", default=0)
    website: Optional[str] = None
    topics: list[str] = []
    created_at: datetime = Field(alias="createdAt")
    
    class Config:
        populate_by_name = True


class ProductHuntInsight(BaseModel):
    """LLM-analyzed insights from Product Hunt launches."""
    date: datetime
    top_launches: list[ProductLaunch]
    trend_summary: str  # LLM-generated summary
    content_angles: list[str]  # Content ideas for LinkedIn
    period: Literal['daily', 'weekly'] = "daily"


class HackerNewsStory(BaseModel):
    """A story from Hacker News."""
    id: str
    title: str
    url: Optional[str] = None
    score: int
    comments_count: int = 0
    by: str
    time: Optional[int] = None
    comments: list[str] = []  # Top 3 root comments
    verdict: Optional[str] = None  # LLM-generated community consensus (e.g. "Skeptical")
    sentiment: Optional[str] = None  # Emoji badge (e.g. "⚠️")
    github_stars: Optional[int] = None  # Star count if URL is a GitHub repo


class HackerNewsInsight(BaseModel):
    """LLM-analyzed insights from Hacker News trends."""
    date: datetime
    stories: list[HackerNewsStory]
    summary: str  # LLM-generated summary of developer trends
    top_themes: list[str]  # e.g., "WebComics", "Rust", "AI Safety"
    created_at: datetime
    period: Literal['daily', 'weekly'] = "daily"


class YouTubeVideo(BaseModel):
    """A video from a YouTube influencer channel."""
    id: str
    title: str
    channel_name: str
    channel_id: str
    description: Optional[str] = None
    view_count: int = 0
    published_at: Optional[datetime] = None
    transcript: Optional[str] = None  # Full transcript text
    summary: Optional[str] = None     # LLM-generated summary of content


class YouTubeInsight(BaseModel):
    """LLM-analyzed insights from YouTube influencer videos."""
    date: datetime
    videos: list[YouTubeVideo]
    trend_summary: str  # LLM-generated summary of what influencers are discussing
    key_topics: list[str]  # Main themes across videos
    created_at: datetime
    period: Literal['daily', 'weekly'] = "daily"


# =============================================================================
# GOOGLE TRENDS VALIDATION MODELS
# =============================================================================

class TrendValidation(BaseModel):
    """Validation result for a single topic against Google Trends."""
    keyword: str
    interest_score: int = 0  # 0-100 from Google Trends
    momentum: float = 0.0    # Week-over-week % change
    trend_direction: Literal["rising", "stable", "declining"] = "stable"
    related_queries: list[str] = []
    audience_tags: list[Literal["technical", "strategic"]] = []  # Who this appeals to
    trend_score: int = 0     # Composite 0-100 score
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    api_source: Literal["serpapi", "pytrends", "cached"] = "serpapi"
    content_source: Optional[str] = None  # Original source (e.g., 'newsletter', 'youtube')


class TopicAnalysis(BaseModel):
    """Analysis of topics from a content source, validated against Google Trends."""
    source: Literal["producthunt", "hackernews", "youtube", "newsletter", "manual", "global"]
    source_date: datetime
    topics: list[TrendValidation]
    top_technical_topics: list[str] = []  # Filtered for technical topics
    top_strategic_topics: list[str] = []  # Filtered for strategic topics
    summary: str = ""  # LLM-generated summary of validated trends
    created_at: datetime = Field(default_factory=datetime.utcnow)
