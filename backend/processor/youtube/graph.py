"""
LangGraph-based YouTube influencer video analyzer.
Fetches videos from curated channels and summarizes content.
"""
from datetime import datetime
from typing import TypedDict, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from config.settings import (
    OPENAI_API_KEY,
    LLM_MODEL_GENERATION,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
    LLM_REASONING_EFFORT_GENERATION,
    load_youtube_channels,
)
from sources.youtube import YouTubeClient
from sources.models import YouTubeVideo, YouTubeInsight
from utils.logger import setup_logger

logger = setup_logger(__name__)


# --- State Definition ---

class YouTubeState(TypedDict):
    videos: List[dict]  # List of video data dicts
    summaries: List[dict]  # Videos with summaries added
    trend_summary: str
    key_topics: List[str]
    error: Optional[str]


# --- LLM Schemas ---

class VideoSummary(BaseModel):
    """Summary of a single video's content."""
    video_id: str
    summary: str = Field(description="2-3 sentence summary of the video's main points and takeaways")
    key_points: List[str] = Field(description="3-5 key points or insights from the video")


class ContentAnalysis(BaseModel):
    """Overall analysis of influencer content."""
    trend_summary: str = Field(description="2-3 sentence summary of what tech influencers are discussing")
    key_topics: List[str] = Field(description="5-7 main themes across all videos")
    video_summaries: List[VideoSummary]


# --- Graph Builder ---

class YouTubeAnalyzer:
    """LangGraph workflow for analyzing YouTube influencer videos."""
    
    def __init__(self, timeframe: Literal["daily", "weekly"] = "daily"):
        self.timeframe = timeframe
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(YouTubeState)
        
        workflow.add_node("fetch_videos", self.fetch_videos_node)
        workflow.add_node("analyze_content", self.analyze_content_node)
        
        workflow.set_entry_point("fetch_videos")
        workflow.add_edge("fetch_videos", "analyze_content")
        workflow.add_edge("analyze_content", END)
        
        return workflow.compile()
    
    def fetch_videos_node(self, state: YouTubeState) -> YouTubeState:
        """Fetch recent videos from YouTube API (days=1 for daily, days=7 for weekly)."""
        try:
            # Determine how many days to look back
            days = 7 if self.timeframe == "weekly" else 1
            
            channels = load_youtube_channels()
            
            if not channels:
                logger.warning("No YouTube channels configured")
                return {"videos": [], "error": "No channels configured"}
            
            # Filter out placeholder entries - accept either channel_id or handle
            valid_channels = [
                c for c in channels 
                if (c.get("channel_id") and c.get("channel_id") != "REPLACE_WITH_CHANNEL_ID") or c.get("handle")
            ]
            
            if not valid_channels:
                logger.warning("No valid YouTube channels configured (only placeholders found)")
                return {"videos": [], "error": "No valid channels configured"}
            
            client = YouTubeClient()
            
            # For weekly, fetch more videos per channel since we're looking at 7 days
            videos_per_channel = 5 if self.timeframe == "weekly" else 3
            
            videos = client.fetch_videos_from_channels(
                channels=valid_channels,
                videos_per_channel=videos_per_channel,
                fetch_transcripts=False,  # Use descriptions instead - faster & more reliable
                days=days,
            )
            
            # Convert to dicts for state
            video_dicts = []
            for v in videos:
                video_dicts.append({
                    "id": v.video_id,
                    "title": v.title,
                    "channel_name": v.channel_name,
                    "channel_id": v.channel_id,
                    "description": v.description,
                    "view_count": v.view_count,
                    "published_at": v.published_at.isoformat() if v.published_at else None,
                })
            
            # For weekly, sort by view count and take top 15
            if self.timeframe == "weekly":
                video_dicts = sorted(video_dicts, key=lambda x: x.get("view_count", 0), reverse=True)[:15]
            
            logger.info(f"Fetched {len(video_dicts)} videos ({self.timeframe} mode, {days} days)")
            return {"videos": video_dicts}
            
        except Exception as e:
            logger.error(f"Failed to fetch YouTube videos: {e}")
            return {"videos": [], "error": str(e)}
    
    def analyze_content_node(self, state: YouTubeState) -> YouTubeState:
        """Use LLM to summarize videos and extract trends."""
        videos = state.get("videos", [])
        
        if not videos:
            return {
                "summaries": [],
                "trend_summary": "No videos to analyze.",
                "key_topics": [],
            }
        
        # Prepare content for LLM using title + description (no transcripts needed)
        video_texts = []
        for v in videos[:15]:  # Can handle more videos since descriptions are shorter
            description = v.get("description", "") or "No description provided."
            video_texts.append(
                f"Video ID [{v['id']}]: \"{v['title']}\" by {v['channel_name']}\n"
                f"Views: {v.get('view_count', 0):,}\n"
                f"Description:\n{description}"
            )
        
        videos_text = "\n\n---\n\n".join(video_texts)
        
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL_GENERATION,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            model_kwargs={"reasoning_effort": LLM_REASONING_EFFORT_GENERATION}
        )
        
        prompt = f"""You are an expert tech content analyst reviewing videos from top tech influencers.

Here are the recent videos with their titles and descriptions:

{videos_text}

IMPORTANT: Video descriptions often contain promotional content (social links, Patreon, Discord, email addresses, course ads, sponsorship plugs). IGNORE all promotional content and focus ONLY on:
- The actual video topic description
- Timestamps/chapter markers (e.g., "00:00 Introduction", "04:47 Key Concept")
- Technical content and key points

Please analyze this content and provide:

1. **Video Summaries**: For each video, provide a concise 2-3 sentence summary based on the title and description. Focus on the main technical topic and key takeaways. Ignore any promotional content.

2. **Trend Summary**: A 2-3 sentence overview of what tech influencers are currently discussing and any emerging themes.

3. **Key Topics**: 5-7 main themes or topics that appear across multiple videos (e.g., "AI Coding Assistants", "Framework Wars", "Startup Funding Trends").

Return structured JSON."""
        
        try:
            structured_llm = llm.with_structured_output(ContentAnalysis)
            result = structured_llm.invoke(prompt)
            
            # Merge summaries back into video data
            summary_map = {s.video_id: s for s in result.video_summaries}
            
            updated_videos = []
            for v in videos:
                video_data = dict(v)
                if v["id"] in summary_map:
                    video_data["summary"] = summary_map[v["id"]].summary
                updated_videos.append(video_data)
            
            logger.info(f"Generated summaries for {len(result.video_summaries)} videos")
            
            return {
                "summaries": updated_videos,
                "trend_summary": result.trend_summary,
                "key_topics": result.key_topics,
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze YouTube content: {e}")
            return {
                "summaries": videos,
                "trend_summary": "Analysis failed.",
                "key_topics": [],
            }
    
    def process(self) -> YouTubeInsight:
        """Run the workflow and return insights."""
        logger.info(f"Starting YouTube influencer analysis ({self.timeframe})...")
        
        initial_state: YouTubeState = {
            "videos": [],
            "summaries": [],
            "trend_summary": "",
            "key_topics": [],
            "error": None,
        }
        
        final = self.graph.invoke(initial_state)
        local_now = datetime.now()
        
        # Convert summaries back to YouTubeVideo models
        video_models = []
        for v in final.get("summaries", []):
            try:
                published_at = None
                if v.get("published_at"):
                    published_at = datetime.fromisoformat(v["published_at"])
                
                video_models.append(YouTubeVideo(
                    id=v["id"],
                    title=v["title"],
                    channel_name=v["channel_name"],
                    channel_id=v["channel_id"],
                    description=v.get("description"),
                    view_count=v.get("view_count", 0),
                    published_at=published_at,
                    transcript=None,  # Don't store full transcript in output
                    summary=v.get("summary"),
                ))
            except Exception as e:
                logger.warning(f"Failed to convert video {v.get('id')}: {e}")
        
        return YouTubeInsight(
            date=local_now,
            videos=video_models,
            trend_summary=final.get("trend_summary", ""),
            key_topics=final.get("key_topics", []),
            created_at=local_now,
            period=self.timeframe,
        )
