"""
LangGraph-based Hacker News analyzer.
Fetches top stories and identifies developer trends/culture.
"""
from datetime import datetime, timezone
import time
from typing import TypedDict, List, Optional
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from config.settings import (
    OPENAI_API_KEY,
    LLM_MODEL_GENERATION,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
    LLM_REASONING_EFFORT_GENERATION,
)
from pydantic import Field
from sources.hacker_news import HackerNewsClient
from sources.models import HackerNewsStory, HackerNewsInsight
from utils.logger import setup_logger
from utils.database import get_session, get_recent_hacker_news_insights
from typing import Literal

logger = setup_logger(__name__)


# --- State Definition ---

class HackerNewsState(TypedDict):
    stories: List[HackerNewsStory]
    summary: str
    top_themes: List[str]
    error: Optional[str]
    timeframe: Literal['daily', 'weekly']


# --- LLM Schemas ---

class StoryVerdict(BaseModel):
    story_id: str
    sentiment: str = Field(description="Emoji representing sentiment: ✅ (Validated), ⚠️ (Skeptical/Flawed), 🍿 (Debate), 🧠 (Insightful), ⚡ (Hype)")
    verdict: str = Field(description="1-sentence summary of the community's dominant critique or key insight from comments")

class TrendAnalysis(BaseModel):
    summary: str
    themes: List[str]
    story_verdicts: List[StoryVerdict]


# --- Node Functions ---

def fetch_stories(state: HackerNewsState) -> HackerNewsState:
    """Fetch top trending stories from HN (Daily) or aggregate from DB (Weekly)."""
    timeframe = state.get("timeframe", "daily")
    
    try:
        if timeframe == "weekly":
            logger.info("Fetching weekly stories from database history...")
            session = get_session()
            try:
                # Fetch last 7 days of insights
                history = get_recent_hacker_news_insights(session, days=7)
                if not history:
                    return {"stories": [], "error": "No history found for weekly rewind"}

                # Aggregate stories (deduplicate by ID, keep highest score)
                story_map = {}
                for insight in history:
                    daily_stories = insight.stories_json or []
                    for s_data in daily_stories:
                        # Convert dict to object temporarily for aggregation
                        # We need to ensure we map fields correctly back to model
                        s_id = s_data.get("id")
                        if not s_id: continue
                        
                        # Logic: keep instance with highest score/comments
                        if s_id not in story_map:
                            story_map[s_id] = s_data
                        else:
                            current = story_map[s_id]
                            if s_data.get("score", 0) > current.get("score", 0):
                                story_map[s_id] = s_data

                # Convert top 30 aggregated stories to HackerNewsStory objects
                sorted_stories = sorted(
                    story_map.values(), 
                    key=lambda x: x.get("score", 0), 
                    reverse=True
                )[:30]
                
                stories_objs = []
                for s in sorted_stories:
                    # comments, verdict, sentiment might be missing in older records
                    # but our DB update ensures new ones have them.
                    # For aggregation, we might lose "fresh" comments if we just take raw JSON.
                    # But saving tokens is good. We assume stored comments are good enough.
                    stories_objs.append(HackerNewsStory(
                        id=s.get("id"),
                        title=s.get("title"),
                        url=s.get("url"),
                        score=s.get("score", 0),
                        comments_count=s.get("comments_count", 0),
                        by=s.get("by", "unknown"),
                        # Reuse stored analysis if available, or re-analyze?
                        # Re-analyzing 30 stories is expensive. 
                        # Better to just use them as context for the "Meta-Trend" analysis.
                        # We will pass them to 'analyze_culture' but maybe skip per-story verdict 
                        # if we want to save tokens, OR we keep existing verdicts.
                        comments=s.get("comments", []) if isinstance(s.get("comments"), list) else [],
                        verdict=s.get("verdict"),
                        sentiment=s.get("sentiment")
                    ))
                
                logger.info(f"Aggregated {len(stories_objs)} unique stories from last 7 days")
                return {"stories": stories_objs}
            finally:
                session.close()

        else:
            # Daily mode (Original)
            client = HackerNewsClient()
            # Fetch top 25 to ensure we have enough substance
            stories = client.fetch_top_stories_with_details(limit=25)
            logger.info(f"Fetched {len(stories)} stories from Hacker News")
            return {"stories": stories}

    except Exception as e:
        logger.error(f"Failed to fetch HN stories: {e}")
        return {"stories": [], "error": str(e)}


def analyze_culture(state: HackerNewsState) -> HackerNewsState:
    """Analyze what developers are talking about and extract comment insights."""
    stories = state.get("stories", [])
    if not stories:
        return {"summary": "No stories found.", "top_themes": []}

    # Format for LLM - Top 15 stories with comments
    text_parts = []
    target_stories = stories[:15]
    
    for s in target_stories:
        part = f"Story ID [{s.id}]: {s.title} ({s.score} pts)"
        if s.comments:
            part += "\nTop Comments Reference:"
            for i, c in enumerate(s.comments):
                # Truncate very long comments to save context
                clean_comment = c[:400].replace('\n', ' ')
                part += f"\n  - {clean_comment}..."
        text_parts.append(part)
    
    stories_text = "\n\n".join(text_parts)

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL_GENERATION,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=LLM_MAX_RETRIES,
        model_kwargs={"reasoning_effort": LLM_REASONING_EFFORT_GENERATION}
    )

    prompt_intro = "You are 'The Sentinel', an expert engineer analyzing Hacker News discussions to find the TRUTH behind the hype."
    if state.get("timeframe") == "weekly":
        prompt_intro += "\n\nThis is a WEEKLY REWIND. Access the 'Meta-Trends' across the last 7 days of top stories."

    prompt = f"""{prompt_intro}

Here are the trending stories and their top comments:
{stories_text}

Task 1: The Zeitgeist
- Identify 3-5 dominating themes (e.g. "Rust vs C++", "AI Fatigue", "Open Source Wins").
- Write a 2-3 sentence summary of the current engineering mood.

Task 2: The Verdicts (Crucial)
- For each story, analyze the comments to find the "Community Verdict".
- Did the community debunk the tool? Are they impressed? Is it a repost?
- Assign a Sentiment Badge:
  ✅ = Validated / Impressive
  ⚠️ = Skeptical / Security Issues / Flawed
  🍿 = Controversial / Holy War
  🧠 = Deep Technical Insight
  ⚡ = Hype / Marketing Fluff
  🤷 = Mixed / Unclear
- Write a 1-sentence verdict explaining WHY. (e.g. "Top comment points out it's a wrapper around GPT-3.")

Return structured JSON.
"""

    try:
        structured_llm = llm.with_structured_output(TrendAnalysis)
        result = structured_llm.invoke(prompt)
        
        # Map verdicts back to stories
        verdict_map = {v.story_id: v for v in result.story_verdicts}
        
        updated_stories = []
        for s in stories:
            # We must create new objects or modify in place? Pydantic models are mutable by default.
            # But let's be safe and simple.
            if s.id in verdict_map:
                v = verdict_map[s.id]
                s.verdict = v.verdict
                s.sentiment = v.sentiment
            updated_stories.append(s)
            
        logger.info(f"Generated HN themes: {result.themes} and {len(result.story_verdicts)} verdicts")
        
        # Return updated stories with verdicts populated
        return {
            "summary": result.summary, 
            "top_themes": result.themes,
            "stories": updated_stories
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze HN trends: {e}")
        return {"summary": "Analysis failed.", "top_themes": []}


# --- Graph Construction ---

class HackerNewsAnalyzer:
    def __init__(self, timeframe: Literal["daily", "weekly"] = "daily"):
        self.timeframe = timeframe
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(HackerNewsState)
        
        workflow.add_node("fetch_stories", fetch_stories)
        workflow.add_node("analyze_culture", analyze_culture)
        
        workflow.set_entry_point("fetch_stories")
        workflow.add_edge("fetch_stories", "analyze_culture")
        workflow.add_edge("analyze_culture", END)
        
        return workflow.compile()

    def process(self) -> HackerNewsInsight:
        """Run the workflow."""
        logger.info(f"Starting Hacker News analysis ({self.timeframe})...")
        
        state: HackerNewsState = {
            "stories": [],
            "summary": "",
            "top_themes": [],
            "error": None,
            "timeframe": self.timeframe
        }
        
        final = self.graph.invoke(state)
        
        # Use local time (respects TZ environment variable)
        local_now = datetime.now()
        
        return HackerNewsInsight(
            date=local_now,
            stories=final.get("stories", [])[:10], # Keep top 10 for dashboard
            summary=final.get("summary", ""),
            top_themes=final.get("top_themes", []),
            created_at=local_now,
            period=self.timeframe
        )
