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
from typing import TypedDict, Literal, Annotated
from operator import add

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
from langchain_openai import ChatOpenAI
from config.settings import LLM_MODEL_EXTRACTION

logger = logging.getLogger(__name__)


# ==================== State Definition ====================

def merge_dicts(a: dict, b: dict) -> dict:
    """Merge two dictionaries."""
    if not a: return b
    if not b: return a
    # Sum simpler keys if they exist in both
    result = a.copy()
    for k, v in b.items():
        if k in result and isinstance(result[k], (int, float)) and isinstance(v, (int, float)):
            result[k] += v
        else:
            result[k] = v
    return result


class DiscoveryGraphState(TypedDict):
    """State for the LangGraph workflow."""
    
    # Raw data from APIs
    reddit_posts: list[dict]
    reddit_comments: list[dict]
    tweets: list[dict]
    youtube_videos: list[dict]
    youtube_comments: list[dict]
    youtube_videos_metadata: list[dict]  # For dashboard: {id, title, views, channel, url}
    producthunt_products: list[dict]
    
    # Extracted pain points - automatically merges lists from parallel nodes
    raw_pain_points: Annotated[list[PainPoint], add]
    
    # Filtered candidates
    filtered_candidates: list[PainPoint]
    
    # Demand scores from SerpAPI
    demand_scores: dict[int, int]
    
    # Trends data for dashboard
    trends_data: list[dict]  # {keyword, interest_score, related_queries, trend_direction}
    
    # Scored opportunities
    opportunities: list[AppOpportunity]
    
    # Final output
    top_opportunities: list[AppOpportunity]
    
    # Metadata
    api_usage: Annotated[dict, merge_dicts]


# ==================== Engagement Normalization ====================

def normalize_engagement(engagement: int, source: str) -> int:
    """
    Normalize engagement scores to 0-100 scale based on source type.
    
    Different sources have different engagement scales:
    - Reddit: 100 upvotes is considered good engagement
    - YouTube: 50 likes on a comment is quite high
    - Product Hunt: 200 votes is a successful launch
    """
    if engagement <= 0:
        return 10  # Base score for items without engagement data
    
    thresholds = {
        "reddit": 100,      # 100 upvotes = max score
        "youtube": 50,      # 50 comment likes = max score  
        "producthunt": 200, # 200 votes = max score
        "twitter": 100,     # 100 likes = max score
    }
    
    threshold = thresholds.get(source, 100)
    
    # Scale to 0-100, capping at 100
    normalized = min(int((engagement / threshold) * 100), 100)
    
    # Ensure minimum of 10 for any positive engagement
    return max(normalized, 10)


# ==================== Target Subreddits (from config) ====================

def load_target_subreddits() -> list[str]:
    """Load target subreddits from config file."""
    import json
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent.parent / "config" / "discovery_subreddits.json"
    
    try:
        with open(config_path) as f:
            data = json.load(f)
            subreddits = [item["name"] for item in data]
            logger.info(f"Loaded {len(subreddits)} subreddits from config: {subreddits}")
            return subreddits
    except Exception as e:
        logger.warning(f"Failed to load subreddits config: {e}, using defaults")
        return ["podcasting", "NewTubers", "photography", "Notion", "nocode", "bookkeeping", "freelance", "ecommerce"]

TARGET_SUBREDDITS = load_target_subreddits()


def load_twitter_queries() -> list[str]:
    """Load Twitter discovery queries from config file."""
    import json
    from pathlib import Path
    
    config_path = Path(__file__).parent.parent.parent / "config" / "discovery_twitter_queries.json"
    
    try:
        with open(config_path) as f:
            data = json.load(f)
            queries = [item["query"] for item in data]
            logger.info(f"Loaded {len(queries)} Twitter queries from config")
            return queries
    except Exception as e:
        logger.warning(f"Failed to load Twitter queries config: {e}, using defaults")
        return ["I wish there was an app", "frustrated with AI tool", "why isn't there", "someone should build", "need an app that"]


# ==================== Workflow Nodes ====================

class DiscoveryGraph:
    """LangGraph workflow for viral app discovery."""
    
    def __init__(self, test_mode: bool = False):
        """
        Initialize discovery workflow.
        
        Args:
            test_mode: If True, limits API calls for cheaper testing
                      (2 subreddits, 5 posts each, no comment fetching)
        """
        self.test_mode = test_mode
        self.arcade_client = None
        self.youtube_client = None
        self.producthunt_client = None
        self.trends_client = None
        self.extractor = None
        self.filter = None
        self.scorer = None
        self.llm = None  # For scoring in validate_and_score_node
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
        if self.llm is None:
            self.llm = ChatOpenAI(model=LLM_MODEL_EXTRACTION, temperature=0.3)
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(DiscoveryGraphState)
        
        # Add nodes
        workflow.add_node("collect_data", self.collect_data_node)
        
        # Parallel extraction nodes
        workflow.add_node("extract_reddit", self.extract_reddit_node)
        workflow.add_node("extract_twitter", self.extract_twitter_node)
        workflow.add_node("extract_youtube", self.extract_youtube_node)
        workflow.add_node("extract_producthunt", self.extract_producthunt_node)
        
        workflow.add_node("filter_candidates", self.filter_candidates_node)
        workflow.add_node("validate_and_score", self.validate_and_score_node)
        workflow.add_node("rank_output", self.rank_output_node)
        
        # Define flow
        workflow.set_entry_point("collect_data")
        
        # Fan out to parallel extraction
        workflow.add_edge("collect_data", "extract_reddit")
        workflow.add_edge("collect_data", "extract_twitter")
        workflow.add_edge("collect_data", "extract_youtube")
        workflow.add_edge("collect_data", "extract_producthunt")
        
        # Fan in to filter
        workflow.add_edge("extract_reddit", "filter_candidates")
        workflow.add_edge("extract_twitter", "filter_candidates")
        workflow.add_edge("extract_youtube", "filter_candidates")
        workflow.add_edge("extract_producthunt", "filter_candidates")
        
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
        
        # --- Reddit via Arcade ---
        reddit_posts = []
        reddit_comments = []
        
        # Test mode: only 2 subreddits, 5 posts each (4 API calls)
        # Full mode: 10 subreddits × 2 listings = 20 API calls
        subreddits = TARGET_SUBREDDITS[:2] if self.test_mode else TARGET_SUBREDDITS
        post_limit = 5 if self.test_mode else 50
        
        logger.info(f"Reddit collection: {'TEST MODE' if self.test_mode else 'FULL'} - {len(subreddits)} subreddits, {post_limit} posts each")
        
        for subreddit in subreddits:
            # Hot posts
            posts = self.arcade_client.get_subreddit_posts(
                subreddit=subreddit,
                listing="hot",
                limit=post_limit,
            )
            reddit_posts.extend(posts)
            
            # Top posts this month (skip in test mode to save calls)
            if not self.test_mode:
                top_posts = self.arcade_client.get_subreddit_posts(
                    subreddit=subreddit,
                    listing="top",
                    limit=post_limit,
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
        
        # Get comments from high-engagement posts
        # Test mode: only 5 posts (5 API calls)
        # Full mode: up to 100 posts (100 API calls)
        comment_limit = 5 if self.test_mode else 100
        
        high_engagement_posts = [
            p for p in reddit_posts 
            if p.get("num_comments", 0) > 10
        ][:comment_limit]
        
        logger.info(f"Fetching comments from {len(high_engagement_posts)} posts")
        
        for post in high_engagement_posts:
            post_id = post.get("id") or post.get("name", "")
            if post_id:
                comments = self.arcade_client.get_post_comments(post_id)
                for c in comments:
                    c["subreddit"] = post.get("subreddit", "")
                reddit_comments.extend(comments)
        
        api_usage["arcade"] = self.arcade_client.get_usage_stats()["total"]
        logger.info(f"Collected {len(reddit_comments)} Reddit comments")
        
        # --- Twitter via Arcade (FIXED - keywords must be array) ---
        tweets = []
        
        # Load Twitter queries from config
        twitter_queries = load_twitter_queries()
        
        for query in twitter_queries:
            results = self.arcade_client.search_tweets(query, max_results=20)
            tweets.extend(results)
        
        api_usage["arcade"] += len(twitter_queries)  # Count Twitter calls
        logger.info(f"Collected {len(tweets)} tweets from Twitter")
        
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
        
        # Store YouTube video metadata for dashboard
        youtube_videos_metadata = [
            {
                "id": v.get("video_id", ""),
                "title": v.get("title", ""),
                "views": v.get("views", 0),
                "channel": v.get("channel", ""),
                "url": f"https://youtube.com/watch?v={v.get('video_id', '')}",
            }
            for v in youtube_videos
        ]
        
        return {
            "reddit_posts": reddit_posts,
            "reddit_comments": reddit_comments,
            "tweets": tweets,
            "youtube_videos": youtube_videos,
            "youtube_comments": youtube_comments,
            "youtube_videos_metadata": youtube_videos_metadata,  # For dashboard
            "producthunt_products": producthunt_products,
            "api_usage": api_usage,
        }
    
    def extract_reddit_node(self, state: DiscoveryGraphState) -> dict:
        """Extract pain points from Reddit."""
        posts = state.get("reddit_posts", [])
        comments = state.get("reddit_comments", [])
        logger.info(f"=== EXTRACTING FROM REDDIT (Input: {len(posts)} posts, {len(comments)} comments) ===")
        
        try:
            extractor = PainPointExtractor()
            points = extractor.extract_from_reddit(
                posts,
                comments,
                max_points=30,
            )
            logger.info(f"Reddit: {len(points)} pain points")
            return {
                "raw_pain_points": points,
                "api_usage": {"llm_extraction": 1}
            }
        except Exception as e:
            logger.error(f"Reddit extraction failed: {e}")
            return {"raw_pain_points": [], "api_usage": {}}

    def extract_twitter_node(self, state: DiscoveryGraphState) -> dict:
        """Extract pain points from Twitter."""
        tweets = state.get("tweets", [])
        logger.info(f"=== EXTRACTING FROM TWITTER (Input: {len(tweets)} tweets) ===")
        
        try:
            extractor = PainPointExtractor()
            points = extractor.extract_from_twitter(
                tweets,
                max_points=20,
            )
            logger.info(f"Twitter: {len(points)} pain points")
            return {
                "raw_pain_points": points,
                "api_usage": {"llm_extraction": 1}
            }
        except Exception as e:
            logger.error(f"Twitter extraction failed: {e}")
            return {"raw_pain_points": [], "api_usage": {}}

    def extract_youtube_node(self, state: DiscoveryGraphState) -> dict:
        """Extract pain points from YouTube."""
        comments = state.get("youtube_comments", [])
        logger.info(f"=== EXTRACTING FROM YOUTUBE (Input: {len(comments)} comments) ===")
        
        try:
            extractor = PainPointExtractor()
            points = extractor.extract_from_youtube(
                comments,
                max_points=25,
            )
            logger.info(f"YouTube: {len(points)} pain points")
            return {
                "raw_pain_points": points,
                "api_usage": {"llm_extraction": 1}
            }
        except Exception as e:
            logger.error(f"YouTube extraction failed: {e}")
            return {"raw_pain_points": [], "api_usage": {}}

    def extract_producthunt_node(self, state: DiscoveryGraphState) -> dict:
        """Extract pain points from Product Hunt."""
        products = state.get("producthunt_products", [])
        logger.info(f"=== EXTRACTING FROM PRODUCT HUNT (Input: {len(products)} products) ===")
        
        try:
            extractor = PainPointExtractor()
            points = extractor.extract_from_producthunt(
                products,
                max_points=20,
            )
            logger.info(f"Product Hunt: {len(points)} pain points")
            return {
                "raw_pain_points": points,
                "api_usage": {"llm_extraction": 1}
            }
        except Exception as e:
            logger.error(f"Product Hunt extraction failed: {e}")
            return {"raw_pain_points": [], "api_usage": {}}
    
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
        Score with LLM first, then validate with SerpAPI using app ideas.
        
        Budget: 1 LLM call + 45 SerpAPI calls
        """
        logger.info("=== SCORING AND VALIDATING ===")
        self._init_clients()
        
        candidates = state["filtered_candidates"]
        
        if not candidates:
            logger.warning("No candidates to score")
            return {
                "demand_scores": {},
                "opportunities": [],
                "api_usage": state.get("api_usage", {}),
            }
        
        # First: Score all candidates with LLM to get app ideas
        formatted = self._format_for_scoring(candidates)
        scored_data = self._call_scoring_llm(formatted)
        
        # Parse scored data and collect trends
        opportunities = []
        demand_scores = {}
        trends_data = []  # Store for dashboard
        
        for i, (pp, data) in enumerate(zip(candidates, scored_data)):
            app_idea = data.get("app_idea", pp.problem[:50])
            # Use ENGAGEMENT from source data instead of LLM-guessed virality
            virality = normalize_engagement(pp.engagement, pp.source)
            buildability = data.get("buildability", 50)  # Keep LLM estimate for now
            
            # Validate demand using the LLM-optimized keyword
            try:
                # Use provided keyword or fallback to crude extraction
                keywords = data.get("keyword") or " ".join(app_idea.split()[:4])
                
                validation = self.trends_client.validate_topic(keywords)
                demand = validation.trend_score
                logger.info(f"Validated '{keywords}': demand={demand}, related={len(validation.related_queries)}")
                
                # Store full validation for dashboard
                trends_data.append({
                    "keyword": keywords,
                    "app_idea": app_idea,
                    "interest_score": validation.interest_score,
                    "trend_score": validation.trend_score,
                    "momentum": validation.momentum,
                    "trend_direction": validation.trend_direction,
                    "related_queries": validation.related_queries,
                })
            except Exception as e:
                logger.warning(f"Validation failed for '{app_idea[:30]}': {e}")
                demand = 50
            
            demand_scores[i] = demand
            
            # Search for similar products on Product Hunt (informational, not penalizing)
            similar_products = []
            try:
                # Use the keyword or first few words of app idea for search
                search_term = data.get("keyword") or " ".join(app_idea.split()[:3])
                ph_results = self.producthunt_client.search_products(search_term, limit=3)
                similar_products = [
                    f"{p['name']} ({p['votes']} votes)" for p in ph_results
                ]
            except Exception as e:
                logger.debug(f"PH search failed for '{app_idea[:20]}': {e}")
            
            # Calculate opportunity score: Demand 40%, Virality (engagement) 40%, Build 20%
            opportunity_score = int(demand * 0.4 + virality * 0.4 + buildability * 0.2)
            
            logger.debug(f"Scoring '{app_idea[:30]}': demand={demand}, virality={virality} (engagement={pp.engagement}), build={buildability}")
            
            opportunities.append(AppOpportunity(
                problem=pp.problem,
                app_idea=app_idea,
                demand_score=demand,
                virality_score=virality,  # Now based on real engagement
                buildability_score=buildability,
                opportunity_score=opportunity_score,
                pain_points=[pp],
                similar_products=similar_products,  # NEW: from Product Hunt
            ))
        
        logger.info(f"Scored {len(opportunities)} opportunities, {len(trends_data)} trend validations")
        
        api_usage = state.get("api_usage", {})
        api_usage["serpapi"] = self.trends_client.get_usage_stats()["serpapi_used"]
        api_usage["llm_scoring"] = 1
        api_usage["producthunt_search"] = len(candidates)  # Track PH API usage
        
        return {
            "demand_scores": demand_scores,
            "opportunities": opportunities,
            "trends_data": trends_data,  # For dashboard
            "api_usage": api_usage,
        }
    
    def _format_for_scoring(self, pain_points: list) -> str:
        """Format pain points for scoring prompt."""
        lines = []
        for i, pp in enumerate(pain_points, 1):
            lines.append(f"{i}. {pp.problem}")
        return "\n".join(lines)
    
    def _call_scoring_llm(self, formatted: str) -> list[dict]:
        """Call LLM to score pain points."""
        prompt = """For each pain point below, provide:

1. SEARCH_KEYWORD: What 2-3 words would someone type into Google to solve this problem?
   - GOOD: "youtube summary", "invoice generator", "follow up reminder", "podcast notes"
   - BAD: "QuickDigest", "InvoiceMaster" (these are product names, not searches)
   - Focus on the PROBLEM or GENERIC SOLUTION, not a brand name.

2. APP_IDEA: A catchy app name + short description

3. VIRALITY (0-100): How shareable? Visual transformation = 90+, useful tool = 60-80

4. BUILDABILITY (0-100): How easy to build in 2-4 hours? Simple UI + 1 API = 90+

Pain points:
{formatted}

Output ONE LINE per item:
INDEX | SEARCH_KEYWORD | APP_IDEA | VIRALITY | BUILDABILITY

Example:
1 | youtube summary | QuickDigest — one-click video summarizer | 75 | 85
2 | invoice generator | QuoteQuick — voice to PDF quote tool | 60 | 90

Output:""".format(formatted=formatted)
        
        try:
            response = self.llm.invoke(prompt)
            # Parse response
            results = []
            for line in response.content.strip().split("\n"):
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 5:
                        try:
                            # New format: INDEX | KEYWORD | APP_IDEA | VIRALITY | BUILDABILITY
                            results.append({
                                "keyword": parts[1],
                                "app_idea": parts[2],
                                "virality": int(parts[3]),
                                "buildability": int(parts[4]),
                            })
                        except (ValueError, IndexError):
                            results.append({
                                "keyword": parts[1] if len(parts) > 1 else "",
                                "app_idea": parts[2] if len(parts) > 2 else "",
                                "virality": 50,
                                "buildability": 50
                            })
                    # Fallback for partial lines
                    elif len(parts) >= 4:
                         results.append({
                            "keyword": parts[1],
                            "app_idea": parts[2] if len(parts) > 2 else parts[1],
                            "virality": int(parts[3]) if len(parts) > 3 else 50,
                            "buildability": int(parts[4]) if len(parts) > 4 else 50,
                        })
            return results
        except Exception as e:
            logger.error(f"Scoring LLM failed: {e}")
            return [{"app_idea": "", "keyword": "", "virality": 50, "buildability": 50} for _ in range(100)]
    
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
            "youtube_videos_metadata": [],  # For dashboard
            "producthunt_products": [],
            "raw_pain_points": [],
            "filtered_candidates": [],
            "demand_scores": {},
            "trends_data": [],  # For dashboard
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
            youtube_videos=final_state.get("youtube_videos_metadata", []),  # For dashboard
            trends_data=final_state.get("trends_data", []),  # For dashboard
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
            estimated_cost=0.15,  # ~$0.15 for LLM calls + 2x SerpAPI
        )
        
        logger.info(f"Workflow complete! Generated {len(briefing.top_opportunities)} opportunities")
        return briefing


# Convenience function
def run_saturday_discovery(test_mode: bool = False) -> SaturdayBriefing:
    """
    Run the Saturday discovery workflow.
    
    Args:
        test_mode: If True, limits API calls for cheaper testing
                  (~7 Arcade calls instead of ~135)
    """
    graph = DiscoveryGraph(test_mode=test_mode)
    return graph.run()
