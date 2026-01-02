"""
LangGraph-based Product Hunt analyzer for AI tool discovery.

This module defines the ProductHuntAnalyzer class which processes
Product Hunt launches and generates insights using LLM analysis.

Workflow:
    fetch_launches → analyze_trends → generate_content_angles → END

Runs in parallel with EmailSummarizer via main.py
"""
import os
from datetime import datetime
from typing import TypedDict, List, Optional, Literal

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
from sources.product_hunt import ProductHuntClient
from sources.models import ProductLaunch, ProductHuntInsight
from utils.logger import setup_logger

logger = setup_logger(__name__)


# --- State Definition ---

class ProductHuntState(TypedDict):
    """State for Product Hunt processing workflow."""
    launches: List[dict]          # Raw launch data
    trend_summary: str            # LLM-generated trend analysis
    content_angles: List[str]     # Content ideas
    error: Optional[str]          # Error message if any


# --- LLM Output Schemas ---

class TrendAnalysis(BaseModel):
    """Structured output for trend analysis."""
    summary: str
    top_trends: List[str]
    notable_tools: List[str]


class ContentAngles(BaseModel):
    """Structured output for content angles."""
    angles: List[str]


# --- Graph Builder ---

class ProductHuntAnalyzer:
    """LangGraph workflow for analyzing Product Hunt launches."""
    
    def __init__(self, timeframe: Literal["daily", "weekly"] = "daily"):
        self.timeframe = timeframe
        self.days = 7 if timeframe == "weekly" else 1
        self.graph = self._build_graph()
        logger.info(f"Initialized ProductHuntAnalyzer (mode: {timeframe})")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ProductHuntState)
        
        # Add nodes
        workflow.add_node("fetch_launches", self.fetch_launches_node)
        workflow.add_node("analyze_trends", self.analyze_trends_node)
        workflow.add_node("generate_content_angles", self.generate_content_angles_node)
        
        # Add edges (sequential flow)
        workflow.set_entry_point("fetch_launches")
        workflow.add_edge("fetch_launches", "analyze_trends")
        workflow.add_edge("analyze_trends", "generate_content_angles")
        workflow.add_edge("generate_content_angles", END)
        
        return workflow.compile()

    def fetch_launches_node(self, state: ProductHuntState) -> ProductHuntState:
        """Fetch top product launches from Product Hunt homepage."""
        try:
            client = ProductHuntClient()
            # Use self.days determined by timeframe
            launches = client.fetch_ai_launches(limit=20, days=self.days)
            
            # Convert to dict for state storage
            launch_dicts = [
                {
                    "id": l.id,
                    "name": l.name,
                    "tagline": l.tagline,
                    "description": l.description,
                    "votes": l.votes,
                    "website": l.website,
                    "topics": l.topics,
                }
                for l in launches
            ]
            
            logger.info(f"Fetched {len(launch_dicts)} products from Product Hunt (Last {self.days} days)")
            return {"launches": launch_dicts}
            
        except Exception as e:
            logger.error(f"Failed to fetch Product Hunt launches: {e}")
            return {"launches": [], "error": str(e)}

    def analyze_trends_node(self, state: ProductHuntState) -> ProductHuntState:
        """Use LLM to analyze trends."""
        launches = state.get("launches", [])
        
        if not launches:
            return {"trend_summary": "No product launches found."}
        
        # Format launches for LLM
        launches_text = "\n".join([
            f"- {l['name']}: {l['tagline']} ({l['votes']} votes)"
            for l in launches[:10]  # Top 10 by votes
        ])
        
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL_GENERATION,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            model_kwargs={"reasoning_effort": LLM_REASONING_EFFORT_GENERATION}
        )
        
        context_title = "This Week's Best" if self.timeframe == "weekly" else "Today's Top"
        
        prompt = f"""
        Analyze these product launches from Product Hunt.
        Identify the top 3 trends and notable tools.

        {context_title} Product Launches:
        {launches_text}

        Provide a brief summary (2-3 sentences) of the trends, written in a professional tone 
        suitable for a tech-savvy audience interested in new tools and products."""

        try:
            structured_llm = llm.with_structured_output(TrendAnalysis)
            result = structured_llm.invoke(prompt)
            
            summary = f"{result.summary}\n\n**Top Trends:** {', '.join(result.top_trends)}"
            logger.info(f"Generated trend analysis: {len(summary)} chars")
            
            return {"trend_summary": summary}
            
        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")
            return {"trend_summary": f"Analysis pending. {len(launches)} tools discovered."}

    def generate_content_angles_node(self, state: ProductHuntState) -> ProductHuntState:
        """Generate content ideas based on today's launches."""
        launches = state.get("launches", [])
        trend_summary = state.get("trend_summary", "")
        
        if not launches:
            return {"content_angles": []}
        
        llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=LLM_MODEL_GENERATION,
            temperature=0.5,  # Slightly higher for creativity
            max_tokens=LLM_MAX_TOKENS,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
            model_kwargs={"reasoning_effort": LLM_REASONING_EFFORT_GENERATION}
        )
        
        # Get top 10 products
        top_products = "\n".join([
            f"- {l['name']}: {l['tagline']}"
            for l in launches[:10]
        ])
        
        prompt = f"""Based on these trending products from Product Hunt, suggest 3 LinkedIn post ideas.
Trend Summary:
{trend_summary}

Top Products:
{top_products}

Generate 3 concise content angles. Each should be 1-2 sentences describing a post idea 
that would resonate with tech professionals and product enthusiasts.
Focus on insights, comparisons, or practical applications."""

        try:
            structured_llm = llm.with_structured_output(ContentAngles)
            result = structured_llm.invoke(prompt)
            
            logger.info(f"Generated {len(result.angles)} content angles")
            return {"content_angles": result.angles}
            
        except Exception as e:
            logger.error(f"Failed to generate content angles: {e}")
            return {"content_angles": []}
    
    def process(self) -> ProductHuntInsight:
        """Run the workflow and return insights."""
        logger.info(f"Starting Product Hunt analysis ({self.timeframe})...")
        
        initial_state: ProductHuntState = {
            "launches": [],
            "trend_summary": "",
            "content_angles": [],
            "error": None,
        }
        
        final_state = self.graph.invoke(initial_state)
        
        # Use local time (respects TZ environment variable)
        local_now = datetime.now()
        
        # Convert to ProductHuntInsight
        launches = [
            ProductLaunch(
                id=l["id"],
                name=l["name"],
                tagline=l["tagline"],
                description=l.get("description"),
                votesCount=l.get("votes", 0),
                website=l.get("website"),
                topics=l.get("topics", []),
                createdAt=local_now.isoformat(),
            )
            for l in final_state.get("launches", [])
        ]
        
        insight = ProductHuntInsight(
            date=local_now,
            top_launches=launches[:10],  # Top 10
            trend_summary=final_state.get("trend_summary", ""),
            content_angles=final_state.get("content_angles", []),
            period=self.timeframe,
        )
        
        logger.info(f"Product Hunt analysis complete. {len(launches)} products, "
                   f"{len(insight.content_angles)} content angles")
        
        return insight
