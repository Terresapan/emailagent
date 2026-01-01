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


class HackerNewsInsight(BaseModel):
    """LLM-analyzed insights from Hacker News trends."""
    date: datetime
    stories: list[HackerNewsStory]
    summary: str  # LLM-generated summary of developer trends
    top_themes: list[str]  # e.g., "WebComics", "Rust", "AI Safety"
    created_at: datetime
    period: Literal['daily', 'weekly'] = "daily"
