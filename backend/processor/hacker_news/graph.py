"""
LangGraph-based Hacker News analyzer.
Fetches top stories and identifies developer trends/culture.
"""
from datetime import datetime
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
from sources.hacker_news import HackerNewsClient
from sources.models import HackerNewsStory, HackerNewsInsight
from utils.logger import setup_logger

logger = setup_logger(__name__)


# --- State Definition ---

class HackerNewsState(TypedDict):
    stories: List[HackerNewsStory]
    summary: str
    top_themes: List[str]
    error: Optional[str]


# --- LLM Schemas ---

class TrendAnalysis(BaseModel):
    summary: str
    themes: List[str]


# --- Node Functions ---

def fetch_stories(state: HackerNewsState) -> HackerNewsState:
    """Fetch top trending stories from HN."""
    try:
        client = HackerNewsClient()
        # Fetch top 25 to ensure we have enough substance
        stories = client.fetch_top_stories_with_details(limit=25)
        logger.info(f"Fetched {len(stories)} stories from Hacker News")
        return {"stories": stories}
    except Exception as e:
        logger.error(f"Failed to fetch HN stories: {e}")
        return {"stories": [], "error": str(e)}


def analyze_culture(state: HackerNewsState) -> HackerNewsState:
    """Analyze what developers are talking about."""
    stories = state.get("stories", [])
    if not stories:
        return {"summary": "No stories found.", "top_themes": []}

    # Format for LLM
    text_lines = []
    for s in stories[:15]: # Analyze top 15
        text_lines.append(f"- {s.title} ({s.score} points, {s.comments_count} comments)")
    
    stories_text = "\n".join(text_lines)

    llm = ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=LLM_MODEL_GENERATION,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT_SECONDS,
        max_retries=LLM_MAX_RETRIES,
        model_kwargs={"reasoning_effort": LLM_REASONING_EFFORT_GENERATION}
    )

    prompt = f"""You are an expert tech culture analyst correctly identifying the 'zeitgeist' of the developer community.

Here are today's top trending stories on Hacker News:
{stories_text}

Task:
1. Identify 3-5 distinct themes or topics dominating the conversation (e.g., "Rust Adoption", "AI Regulation", "Retro Computing").
2. Write a short, punchy summary (2-3 sentences) explaining what is capturing developer attention right now.

Avoid generic summaries. Be specific about the *mood* or *focus* of the discussions implied by these titles.
"""

    try:
        structured_llm = llm.with_structured_output(TrendAnalysis)
        result = structured_llm.invoke(prompt)
        
        logger.info(f"Generated HN themes: {result.themes}")
        return {"summary": result.summary, "top_themes": result.themes}
        
    except Exception as e:
        logger.error(f"Failed to analyze HN trends: {e}")
        return {"summary": "Analysis failed.", "top_themes": []}


# --- Graph Construction ---

class HackerNewsAnalyzer:
    def __init__(self):
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
        logger.info("Starting Hacker News analysis...")
        
        state: HackerNewsState = {
            "stories": [],
            "summary": "",
            "top_themes": [],
            "error": None
        }
        
        final = self.graph.invoke(state)
        
        return HackerNewsInsight(
            date=datetime.utcnow(),
            stories=final.get("stories", [])[:10], # Keep top 10 for dashboard
            summary=final.get("summary", ""),
            top_themes=final.get("top_themes", []),
            created_at=datetime.utcnow()
        )
