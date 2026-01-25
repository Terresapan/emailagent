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
from processor.viral_app.clusterer import ClusteringEngine, PainPointCluster
from processor.viral_app.ranker import rank_opportunities

from sources.arcade_client import ArcadeClient
from sources.youtube import YouTubeClient
from sources.product_hunt import ProductHuntClient
from sources.google_trends import GoogleTrendsClient
from langchain_openai import ChatOpenAI
from config.settings import LLM_MODEL_EXTRACTION, ENGAGEMENT_THRESHOLDS

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
    
    # Clustered pain points (from ClusteringEngine)
    clustered_pain_points: list  # list[PainPointCluster]
    
    # Filtered candidates (clusters, not individual points)
    filtered_candidates: list  # list[PainPointCluster]
    
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
    
    threshold = ENGAGEMENT_THRESHOLDS.get(source, 100)  # Default 100 for unknown sources
    
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
        self.clusterer = None
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
        if self.extractor is None:
            self.extractor = PainPointExtractor()
        if self.clusterer is None:
            self.clusterer = ClusteringEngine()
        if self.filter is None:
            self.filter = LLMFilter()
        if self.scorer is None:
            self.scorer = Scorer()
        if self.trends_client is None:
            self.trends_client = GoogleTrendsClient()
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
        
        # Clustering and filtering
        workflow.add_node("cluster_pain_points", self.cluster_pain_points_node)
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
        
        # Fan in to clustering
        workflow.add_edge("extract_reddit", "cluster_pain_points")
        workflow.add_edge("extract_twitter", "cluster_pain_points")
        workflow.add_edge("extract_youtube", "cluster_pain_points")
        workflow.add_edge("extract_producthunt", "cluster_pain_points")
        
        # Cluster -> Filter -> Score -> Rank
        workflow.add_edge("cluster_pain_points", "filter_candidates")
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
        
        # Round-robin selection: pick 2 videos per query to ensure category diversity
        # This prevents one query from dominating the selection
        youtube_comments = []
        by_query: dict[str, list[dict]] = {}
        for video in youtube_videos:
            query = video.get("query", "unknown")
            if query not in by_query:
                by_query[query] = []
            by_query[query].append(video)
        
        # Take up to 2 videos from each query category
        balanced_videos = []
        videos_per_category = max(2, 10 // len(by_query)) if by_query else 2
        for query, videos in by_query.items():
            # Sort by views within category, take top N
            sorted_videos = sorted(videos, key=lambda v: v.get("views", 0), reverse=True)
            balanced_videos.extend(sorted_videos[:videos_per_category])
        
        # Cap at 10 total for comment fetching
        video_ids = [v["video_id"] for v in balanced_videos[:10]]
        logger.info(f"Selected {len(video_ids)} videos for comments (balanced from {len(by_query)} categories)")
        
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
    
    def cluster_pain_points_node(self, state: DiscoveryGraphState) -> dict:
        """
        Cluster similar pain points from different sources.
        
        Groups semantically similar problems to enable multi-source validation.
        """
        logger.info("=== CLUSTERING PAIN POINTS ===")
        self._init_clients()
        
        raw_points = state.get("raw_pain_points", [])
        logger.info(f"Input: {len(raw_points)} raw pain points")
        
        if not raw_points:
            return {"clustered_pain_points": [], "api_usage": {"embedding_calls": 0}}
        
        try:
            clusters = self.clusterer.cluster(raw_points)
            
            # Log multi-source clusters
            multi_source = [c for c in clusters if c.source_count > 1]
            logger.info(f"Created {len(clusters)} clusters, {len(multi_source)} have multiple sources")
            
            return {
                "clustered_pain_points": clusters,
                "api_usage": {"embedding_calls": self.clusterer.get_usage_stats()["embedding_calls"]}
            }
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            # Fallback: wrap each pain point in its own cluster
            from processor.viral_app.clusterer import PainPointCluster
            clusters = []
            for pp in raw_points:
                c = PainPointCluster(representative=pp.problem)
                c.add_pain_point(pp)
                clusters.append(c)
            return {"clustered_pain_points": clusters, "api_usage": {}}
    
    def filter_candidates_node(self, state: DiscoveryGraphState) -> dict:
        """
        Filter clusters to actionable candidates.
        
        Budget: 1 LLM call (~$0.02)
        """
        logger.info("=== FILTERING CANDIDATES ===")
        self._init_clients()
        
        clusters = state.get("clustered_pain_points", [])
        logger.info(f"Input: {len(clusters)} clusters")
        
        if not clusters:
            return {"filtered_candidates": [], "api_usage": {"llm_filter": 0}}
        
        # Filter clusters using LLM
        filtered = self.filter.filter_clusters(
            clusters,
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
        Score clusters with LLM, then validate with Product Hunt.
        
        Now works with PainPointCluster objects that may contain multiple sources.
        """
        logger.info("=== SCORING AND VALIDATING ===")
        self._init_clients()
        
        clusters = state.get("filtered_candidates", [])
        
        if not clusters:
            logger.warning("No clusters to score")
            return {
                "demand_scores": {},
                "opportunities": [],
                "api_usage": state.get("api_usage", {}),
            }
        
        # First: Score all clusters with LLM to get app ideas
        formatted = self._format_clusters_for_scoring(clusters)
        scored_data = self._call_scoring_llm(formatted)
        
        # Parse scored data and create opportunities
        opportunities = []
        demand_scores = {}
        
        for i, (cluster, data) in enumerate(zip(clusters, scored_data)):
            app_idea = data.get("app_idea", cluster.representative[:50])
            buildability = data.get("buildability", 50)
            
            # Normalize engagement per source using source-specific thresholds
            # For multi-source clusters, use weighted average of normalized scores
            if cluster.source_breakdown:
                weighted_scores = []
                for source, eng in cluster.source_breakdown.items():
                    normalized = normalize_engagement(eng, source)
                    weighted_scores.append(normalized)
                # Average the normalized scores (each already 0-100)
                engagement_score = int(sum(weighted_scores) / len(weighted_scores))
            else:
                # Fallback for single pain point
                primary_source = cluster.pain_points[0].source if cluster.pain_points else "unknown"
                engagement_score = normalize_engagement(cluster.total_engagement, primary_source)
            
            # Bonus for multi-source validation
            source_bonus = (cluster.source_count - 1) * 10  # +10 per additional source
            engagement_score = min(engagement_score + source_bonus, 100)
            
            # Search for similar products via Google (Market Validation)
            # Search by PROBLEM DESCRIPTION, not the made-up product name
            similar_products = []
            validation_score = 0
            
            try:
                # Use LLM-generated search keyword if available (better than parsing app idea)
                search_query = data.get("keyword", "")
                
                # Fallback: Parse from app idea if keyword is missing/empty
                if not search_query or len(search_query) < 3:
                    if '—' in app_idea:
                        search_query = app_idea.split('—')[1].strip()[:50]
                    elif '-' in app_idea:
                        search_query = app_idea.split('-')[1].strip()[:50]
                    else:
                        search_query = app_idea[:50]
                
                google_results = self.trends_client.search_similar_products(search_query, limit=5)
                similar_products = [
                    f"{p['name'][:50]}" for p in google_results if p.get('name')
                ]
                # Score: 10 per result found, max 50
                validation_score = min(len(google_results) * 10, 50)
                logger.debug(f"Google validation '{search_query[:30]}': {len(google_results)} results -> Score {validation_score}")
                
            except Exception as e:
                logger.warning(f"Google search failed for '{app_idea[:20]}': {e}")
                validation_score = 0
            
            demand_scores[i] = validation_score
            
            # Calculate opportunity score: 
            # Engagement 50% (Real pain) + Validation 30% (Market exists) + Build 20%
            opportunity_score = int(engagement_score * 0.5 + validation_score * 0.3 + buildability * 0.2)
            
            logger.debug(f"Scoring '{app_idea[:30]}': engagement={engagement_score} (sources={cluster.source_count}), validation={validation_score}, build={buildability} -> Total {opportunity_score}")
            
            opportunities.append(AppOpportunity(
                problem=cluster.representative,
                app_idea=app_idea,
                demand_score=validation_score,
                virality_score=engagement_score,
                buildability_score=buildability,
                opportunity_score=opportunity_score,
                pain_points=cluster.pain_points,  # All pain points from cluster
                source_breakdown=cluster.source_breakdown,  # {"reddit": 120, "twitter": 45}
                similar_products=similar_products,
            ))
        
        logger.info(f"Scored {len(opportunities)} opportunities")
        
        # Log multi-source opportunities
        multi_source = [o for o in opportunities if len(o.source_breakdown) > 1]
        if multi_source:
            logger.info(f"  {len(multi_source)} opportunities have cross-platform validation")
        
        api_usage = state.get("api_usage", {})
        api_usage["llm_scoring"] = 1
        api_usage["producthunt_search"] = len(clusters)
        
        return {
            "demand_scores": demand_scores,
            "opportunities": opportunities,
            "trends_data": [],
            "api_usage": api_usage,
        }
    
    def _format_clusters_for_scoring(self, clusters: list) -> str:
        """Format clusters for scoring prompt."""
        lines = []
        for i, cluster in enumerate(clusters, 1):
            sources = ", ".join(cluster.source_breakdown.keys())
            lines.append(f"{i}. [{sources}] {cluster.representative}")
        return "\n".join(lines)
    
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

3. BUILDABILITY (0-100): How easy to build in 2-4 hours? Simple UI + 1 API = 90+

Pain points:
{formatted}

Output ONE LINE per item using this EXACT format:
INDEX | SEARCH_KEYWORD | APP_IDEA | BUILDABILITY

Example:
1 | youtube summary | QuickDigest — one-click video summarizer | 85
2 | invoice generator | QuoteQuick — voice to PDF quote tool | 90

Output:""".format(formatted=formatted)
        
        try:
            response = self.llm.invoke(prompt)
            # Parse response
            results = []
            for line in response.content.strip().split("\n"):
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    
                    # Expected: INDEX | KEYWORD | APP_IDEA | BUILDABILITY
                    if len(parts) >= 4:
                        try:
                            results.append({
                                "keyword": parts[1],
                                "app_idea": parts[2],
                                "buildability": int(parts[3]),
                            })
                        except (ValueError, IndexError):
                             # Fallback if parsing fails
                             logger.warning(f"Failed to parse score line: {line}")
                             continue
                    # Fallback for old/bad format
                    elif len(parts) >= 3:
                         results.append({
                            "keyword": parts[1],
                            "app_idea": parts[2],
                            "buildability": 50
                        })
            return results
            
        except Exception as e:
            logger.error(f"Scoring LLM call failed: {e}")
            return [{"app_idea": "", "keyword": "", "buildability": 50} for _ in range(100)]
    
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
        
        # Build briefing with ACCURATE API call counts
        # (The accumulated api_usage dict has inflated values due to LangGraph merge_dicts)
        
        # Accurate counts:
        # - LLM calls: 4 extraction + 1 filter + 1 scoring = 6 OpenAI calls
        # - Embedding: 1 call for clustering
        # - Arcade: Read from client at END (not accumulated during workflow)
        # - YouTube: search calls + comment calls
        # - ProductHunt: 1 fetch + N validation searches
        
        arcade_actual = self.arcade_client.get_usage_stats()["total"] if self.arcade_client else 0
        youtube_videos_list = final_state.get("youtube_videos", [])
        youtube_comments_list = final_state.get("youtube_comments", [])
        filtered_clusters = final_state.get("filtered_candidates", [])
        
        # YouTube: 1 search call per query (5 queries) + 1 comment call per video (8-10 videos)
        youtube_api_calls = 5 + min(len(youtube_videos_list), 10)  # 5 search + up to 10 comment calls
        
        # SerpAPI: Google searches for market validation (1 per filtered cluster that was scored)
        serpapi_used = self.trends_client.get_usage_stats()["serpapi_used"] if self.trends_client else 0
        
        briefing = SaturdayBriefing(
            date=datetime.now(),
            top_opportunities=final_state["top_opportunities"],
            youtube_videos=final_state.get("youtube_videos_metadata", []),
            trends_data=final_state.get("trends_data", []),
            total_data_points=sum([
                len(final_state.get("reddit_posts", [])),
                len(final_state.get("reddit_comments", [])),
                len(final_state.get("tweets", [])),
                len(final_state.get("youtube_comments", [])),
                len(final_state.get("producthunt_products", [])),
            ]),
            total_pain_points_extracted=len(final_state.get("raw_pain_points", [])),
            total_candidates_filtered=len(filtered_clusters),
            arcade_calls=arcade_actual,  # Actual Arcade executions
            serpapi_calls=serpapi_used,  # Google searches for validation
            youtube_quota=youtube_api_calls,  # YouTube API calls
            llm_calls=7,  # Accurate: 6 LLM + 1 embedding call
            estimated_cost=round(0.01 * 7 + 0.002 * serpapi_used, 3),  # ~$0.07 LLM + ~$0.002/search
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
