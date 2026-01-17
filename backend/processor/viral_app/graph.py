"""
LangGraph workflow for Saturday discovery briefing.

Orchestrates the 4-hour discovery process:
1. Collect data from all APIs (200 Arcade calls + free APIs)
2. Extract pain points with LLM (5 calls)
3. Filter candidates with LLM (1 call)
4. Validate with SerpAPI + score with LLM (120 SerpAPI + 1 LLM)
5. Rank and output top 20 opportunities
"""
import logging
from datetime import datetime
from typing import TypedDict, Literal

from langgraph.graph import StateGraph, END

from processor.viral_app.models import (
    PainPoint,
    AppOpportunity,
    SaturdayBriefing,
)
from processor.viral_app.pain_point_extractor import PainPointExtractor
from processor.viral_app.llm_filter import LLMFilter
from processor.viral_app.scorer import Scorer
from processor.viral_app.ranker import rank_opportunities

from sources.arcade_client import ArcadeClient
from sources.youtube import YouTubeClient
from sources.product_hunt import ProductHuntClient
from sources.google_trends import GoogleTrendsClient

logger = logging.getLogger(__name__)


# ==================== State Definition ====================

class DiscoveryGraphState(TypedDict):
    """State for the LangGraph workflow."""
    
    # Raw data from APIs
    reddit_posts: list[dict]
    reddit_comments: list[dict]
    tweets: list[dict]
    youtube_videos: list[dict]
    youtube_comments: list[dict]
    producthunt_products: list[dict]
    
    # Extracted pain points
    raw_pain_points: list[PainPoint]
    
    # Filtered candidates
    filtered_candidates: list[PainPoint]
    
    # Demand scores from SerpAPI
    demand_scores: dict[int, int]
    
    # Scored opportunities
    opportunities: list[AppOpportunity]
    
    # Final output
    top_opportunities: list[AppOpportunity]
    
    # Metadata
    api_usage: dict


# ==================== Target Subreddits ====================

TARGET_SUBREDDITS = [
    "smallbusiness",
    "freelance", 
    "Entrepreneur",
    "startups",
    "SideProject",
    "consulting",
    "realtors",
    "ecommerce",
    "marketing",
    "agencies",
]


# ==================== Workflow Nodes ====================

class DiscoveryGraph:
    """LangGraph workflow for viral app discovery."""
    
    def __init__(self):
        self.arcade_client = None
        self.youtube_client = None
        self.producthunt_client = None
        self.trends_client = None
        self.extractor = None
        self.filter = None
        self.scorer = None
        self.graph = self._build_graph()
    
    def _init_clients(self):
        """Initialize API clients (lazy loading)."""
        if self.arcade_client is None:
            self.arcade_client = ArcadeClient()
        if self.youtube_client is None:
            self.youtube_client = YouTubeClient()
        if self.producthunt_client is None:
            self.producthunt_client = ProductHuntClient()
        if self.trends_client is None:
            self.trends_client = GoogleTrendsClient()
        if self.extractor is None:
            self.extractor = PainPointExtractor()
        if self.filter is None:
            self.filter = LLMFilter()
        if self.scorer is None:
            self.scorer = Scorer()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(DiscoveryGraphState)
        
        # Add nodes
        workflow.add_node("collect_data", self.collect_data_node)
        workflow.add_node("extract_pain_points", self.extract_pain_points_node)
        workflow.add_node("filter_candidates", self.filter_candidates_node)
        workflow.add_node("validate_and_score", self.validate_and_score_node)
        workflow.add_node("rank_output", self.rank_output_node)
        
        # Define flow
        workflow.set_entry_point("collect_data")
        workflow.add_edge("collect_data", "extract_pain_points")
        workflow.add_edge("extract_pain_points", "filter_candidates")
        workflow.add_edge("filter_candidates", "validate_and_score")
        workflow.add_edge("validate_and_score", "rank_output")
        workflow.add_edge("rank_output", END)
        
        return workflow.compile()
    
    # ==================== Node Implementations ====================
    
    def collect_data_node(self, state: DiscoveryGraphState) -> dict:
        """
        Collect data from all APIs.
        
        Budget: 200 Arcade calls + free APIs
        """
        logger.info("=== COLLECTING DATA ===")
        self._init_clients()
        
        api_usage = {"arcade": 0, "youtube": 0, "producthunt": 0}
        
        # --- Reddit via Arcade (155 calls) ---
        reddit_posts = []
        reddit_comments = []
        
        # Get posts from subreddits (20 calls: 10 subreddits × 2 listings)
        for subreddit in TARGET_SUBREDDITS:
            # Hot posts
            posts = self.arcade_client.get_subreddit_posts(
                subreddit=subreddit,
                listing="hot",
                limit=50,
            )
            reddit_posts.extend(posts)
            
            # Top posts this month
            top_posts = self.arcade_client.get_subreddit_posts(
                subreddit=subreddit,
                listing="top",
                limit=50,
                time_range="THIS_MONTH",
            )
            reddit_posts.extend(top_posts)
        
        api_usage["arcade"] = self.arcade_client.get_usage_stats()["total"]
        logger.info(f"Collected {len(reddit_posts)} Reddit posts")
        
        # Get top post content (15 calls for 150 posts)
        top_post_ids = [
            p.get("id") or p.get("name", "")
            for p in sorted(reddit_posts, key=lambda x: x.get("score", 0), reverse=True)[:150]
        ]
        
        if top_post_ids:
            # Batch into groups of 10
            for i in range(0, len(top_post_ids), 10):
                batch = top_post_ids[i:i+10]
                content = self.arcade_client.get_posts_content(batch)
                # Merge content back (simplified)
        
        # Get comments from high-engagement posts (100 calls)
        high_engagement_posts = [
            p for p in reddit_posts 
            if p.get("num_comments", 0) > 10
        ][:100]
        
        for post in high_engagement_posts:
            post_id = post.get("id") or post.get("name", "")
            if post_id:
                comments = self.arcade_client.get_post_comments(post_id)
                for c in comments:
                    c["subreddit"] = post.get("subreddit", "")
                reddit_comments.extend(comments)
        
        api_usage["arcade"] = self.arcade_client.get_usage_stats()["total"]
        logger.info(f"Collected {len(reddit_comments)} Reddit comments")
        
        # --- Twitter via Arcade (disabled - input format issues) ---
        tweets = []
        # TODO: Re-enable once X.SearchRecentTweetsByKeywords input format is fixed
        # twitter_queries = [
        #     "I wish there was an app",
        #     "frustrated with AI tool",
        #     "why isn't there",
        #     "someone should build",
        #     "need an app that",
        # ]
        # 
        # for query in twitter_queries[:6]:
        #     for _ in range(5):
        #         results = self.arcade_client.search_tweets(query)
        #         tweets.extend(results)
        
        logger.info(f"Twitter collection disabled (API input format issue)")
        
        # --- YouTube (free - ~600 quota) ---
        youtube_videos = self.youtube_client.search_for_discovery(
            videos_per_query=5,
            min_views=50000,
        )
        api_usage["youtube"] = len(youtube_videos) * 100 + 50  # Rough quota estimate
        
        youtube_comments = []
        video_ids = [v["video_id"] for v in youtube_videos[:10]]
        youtube_comments = self.youtube_client.get_comments_from_videos(
            video_ids,
            max_comments_per_video=50,
        )
        api_usage["youtube"] += len(video_ids)
        logger.info(f"Collected {len(youtube_videos)} videos, {len(youtube_comments)} comments")
        
        # --- Product Hunt (free) ---
        producthunt_products = self.producthunt_client.fetch_with_reviews(
            limit=50,
            days=7,
        )
        api_usage["producthunt"] = 1
        logger.info(f"Collected {len(producthunt_products)} Product Hunt products")
        
        return {
            "reddit_posts": reddit_posts,
            "reddit_comments": reddit_comments,
            "tweets": tweets,
            "youtube_videos": youtube_videos,
            "youtube_comments": youtube_comments,
            "producthunt_products": producthunt_products,
            "api_usage": api_usage,
        }
    
    def extract_pain_points_node(self, state: DiscoveryGraphState) -> dict:
        """
        Extract pain points from all sources.
        
        Budget: 5 LLM calls (~$0.08)
        """
        logger.info("=== EXTRACTING PAIN POINTS ===")
        self._init_clients()
        
        all_pain_points = []
        
        # Reddit (1 call)
        reddit_pps = self.extractor.extract_from_reddit(
            state["reddit_posts"],
            state["reddit_comments"],
            max_points=30,
        )
        all_pain_points.extend(reddit_pps)
        
        # Twitter (1 call)
        twitter_pps = self.extractor.extract_from_twitter(
            state["tweets"],
            max_points=20,
        )
        all_pain_points.extend(twitter_pps)
        
        # YouTube (1 call)
        youtube_pps = self.extractor.extract_from_youtube(
            state["youtube_comments"],
            max_points=25,
        )
        all_pain_points.extend(youtube_pps)
        
        # Product Hunt (1 call)
        producthunt_pps = self.extractor.extract_from_producthunt(
            state["producthunt_products"],
            max_points=20,
        )
        all_pain_points.extend(producthunt_pps)
        
        logger.info(f"Extracted {len(all_pain_points)} total pain points")
        
        # Update API usage
        api_usage = state.get("api_usage", {})
        api_usage["llm_extraction"] = self.extractor.get_call_count()
        
        return {
            "raw_pain_points": all_pain_points,
            "api_usage": api_usage,
        }
    
    def filter_candidates_node(self, state: DiscoveryGraphState) -> dict:
        """
        Filter pain points to actionable candidates.
        
        Budget: 1 LLM call (~$0.02)
        """
        logger.info("=== FILTERING CANDIDATES ===")
        self._init_clients()
        
        filtered = self.filter.filter_pain_points(
            state["raw_pain_points"],
            max_candidates=45,
        )
        
        logger.info(f"Filtered to {len(filtered)} candidates")
        
        api_usage = state.get("api_usage", {})
        api_usage["llm_filter"] = self.filter.get_call_count()
        
        return {
            "filtered_candidates": filtered,
            "api_usage": api_usage,
        }
    
    def validate_and_score_node(self, state: DiscoveryGraphState) -> dict:
        """
        Validate with SerpAPI and score with LLM.
        
        Budget: 120 SerpAPI calls + 1 LLM call
        """
        logger.info("=== VALIDATING AND SCORING ===")
        self._init_clients()
        
        candidates = state["filtered_candidates"]
        demand_scores = {}
        
        # Validate top candidates with SerpAPI (45 calls for base validation)
        for i, candidate in enumerate(candidates[:45]):
            # Simple keyword extraction from problem
            keywords = candidate.problem[:50]  # First 50 chars as query
            
            try:
                validation = self.trends_client.validate_topic(keywords)
                demand_scores[i] = validation.trend_score
            except Exception as e:
                logger.warning(f"Validation failed for candidate {i}: {e}")
                demand_scores[i] = 50  # Default score
        
        # Score all candidates with LLM (1 call)
        opportunities = self.scorer.score_pain_points(
            candidates,
            demand_scores=demand_scores,
        )
        
        logger.info(f"Scored {len(opportunities)} opportunities")
        
        api_usage = state.get("api_usage", {})
        api_usage["serpapi"] = self.trends_client.get_usage_stats()["serpapi_used"]
        api_usage["llm_scoring"] = self.scorer.get_call_count()
        
        return {
            "demand_scores": demand_scores,
            "opportunities": opportunities,
            "api_usage": api_usage,
        }
    
    def rank_output_node(self, state: DiscoveryGraphState) -> dict:
        """
        Final ranking and output.
        """
        logger.info("=== RANKING OUTPUT ===")
        
        top_20 = rank_opportunities(state["opportunities"], top_n=20)
        
        logger.info(f"Final output: {len(top_20)} top opportunities")
        
        return {
            "top_opportunities": top_20,
        }
    
    # ==================== Public API ====================
    
    def run(self) -> SaturdayBriefing:
        """
        Run the complete Saturday discovery workflow.
        
        Returns:
            SaturdayBriefing with top 20 opportunities
        """
        logger.info("Starting Saturday discovery workflow...")
        
        # Initialize empty state
        initial_state: DiscoveryGraphState = {
            "reddit_posts": [],
            "reddit_comments": [],
            "tweets": [],
            "youtube_videos": [],
            "youtube_comments": [],
            "producthunt_products": [],
            "raw_pain_points": [],
            "filtered_candidates": [],
            "demand_scores": {},
            "opportunities": [],
            "top_opportunities": [],
            "api_usage": {},
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        # Build briefing
        api_usage = final_state.get("api_usage", {})
        
        briefing = SaturdayBriefing(
            date=datetime.now(),
            top_opportunities=final_state["top_opportunities"],
            total_data_points=sum([
                len(final_state.get("reddit_posts", [])),
                len(final_state.get("reddit_comments", [])),
                len(final_state.get("tweets", [])),
                len(final_state.get("youtube_comments", [])),
                len(final_state.get("producthunt_products", [])),
            ]),
            total_pain_points_extracted=len(final_state.get("raw_pain_points", [])),
            total_candidates_filtered=len(final_state.get("filtered_candidates", [])),
            arcade_calls=api_usage.get("arcade", 0),
            serpapi_calls=api_usage.get("serpapi", 0),
            youtube_quota=api_usage.get("youtube", 0),
            llm_calls=sum([
                api_usage.get("llm_extraction", 0),
                api_usage.get("llm_filter", 0),
                api_usage.get("llm_scoring", 0),
            ]),
            estimated_cost=0.13,  # ~$0.13 for 7 LLM calls
        )
        
        logger.info(f"Workflow complete! Generated {len(briefing.top_opportunities)} opportunities")
        return briefing


# Convenience function
def run_saturday_discovery() -> SaturdayBriefing:
    """Run the Saturday discovery workflow."""
    graph = DiscoveryGraph()
    return graph.run()
