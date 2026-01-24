"""Arcade.dev API client for Reddit and Twitter access."""
import logging
from typing import Optional

from arcadepy import Arcade
from arcadepy.types.execute_tool_response import OutputError

from config import settings

logger = logging.getLogger(__name__)


class ArcadeClient:
    """Client for Reddit and Twitter access via Arcade.dev."""
    
    def __init__(self, api_key: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize Arcade client.
        
        Args:
            api_key: Arcade API key (defaults to ARCADE_API_KEY from settings)
            user_id: User identifier for OAuth (defaults to ARCADE_USER_ID from settings)
        """
        self.api_key = api_key or settings.ARCADE_API_KEY
        self.user_id = user_id or getattr(settings, "ARCADE_USER_ID", "discovery@emailagent.local")
        
        if not self.api_key:
            raise ValueError("ARCADE_API_KEY is required")
        
        self.client = Arcade(api_key=self.api_key)
        self.usage = {"reddit": 0, "twitter": 0}
    
    def _authorize_and_execute(self, tool_name: str, inputs: dict) -> dict:
        """
        Authorize and execute an Arcade tool.
        
        Args:
            tool_name: Full tool name (e.g., "Reddit.GetPostsInSubreddit")
            inputs: Tool input parameters
            
        Returns:
            Tool output value or empty dict on error
        """
        try:
            # Check authorization
            auth_response = self.client.tools.authorize(
                tool_name=tool_name,
                user_id=self.user_id,
            )
            
            if auth_response.status != "completed":
                logger.warning(f"Tool {tool_name} requires authorization: {auth_response.url}")
                # For automated use, we wait for auth (user needs to authorize beforehand)
                self.client.auth.wait_for_completion(auth_response.id)
            
            # Execute tool
            response = self.client.tools.execute(
                tool_name=tool_name,
                input=inputs,
                user_id=self.user_id,
            )
            
            # Check for errors
            if response.output.error:
                self._handle_error(response.output.error, tool_name)
                return {}
            
            return response.output.value or {}
            
        except Exception as e:
            logger.error(f"Error executing {tool_name}: {e}")
            return {}
    
    def _handle_error(self, error: OutputError, tool_name: str):
        """Handle Arcade tool errors."""
        error_kind = getattr(error, "kind", "UNKNOWN")
        
        if error_kind == "UPSTREAM_RUNTIME_RATE_LIMIT":
            wait_seconds = (error.retry_after_ms or 60000) / 1000
            logger.warning(f"Rate limited on {tool_name}. Wait {wait_seconds}s")
        elif error_kind == "TOOL_RUNTIME_FATAL":
            logger.error(f"Fatal error in {tool_name}: {error.message}")
        else:
            logger.error(f"Error in {tool_name}: {error.message}")
    
    # ==================== Reddit Tools ====================
    
    def get_subreddit_posts(
        self,
        subreddit: str,
        listing: str = "hot",
        limit: int = 50,
        time_range: Optional[str] = None,
    ) -> list[dict]:
        """
        Get posts from a subreddit.
        
        Args:
            subreddit: Subreddit name without "r/"
            listing: "hot", "new", "rising", "top", "controversial"
            limit: Max 100 posts per call
            time_range: For top/controversial: "THIS_WEEK", "THIS_MONTH", "ALL_TIME"
            
        Returns:
            List of posts with title, score, num_comments, id, url
        """
        inputs = {
            "subreddit": subreddit,
            "listing": listing,
            "limit": min(limit, 100),
        }
        
        if time_range and listing in ["top", "controversial"]:
            inputs["time_range"] = time_range
        
        result = self._authorize_and_execute("Reddit.GetPostsInSubreddit", inputs)
        self.usage["reddit"] += 1
        
        # Normalize output to list
        if isinstance(result, dict) and "posts" in result:
            return result["posts"]
        elif isinstance(result, list):
            return result
        return []
    
    def get_posts_content(self, post_ids: list[str]) -> list[dict]:
        """
        Get content (body) of multiple posts.
        
        Args:
            post_ids: List of post IDs or URLs (batch request)
            
        Returns:
            List of posts with full body content
        """
        if not post_ids:
            return []
        
        result = self._authorize_and_execute(
            "Reddit.GetContentOfMultiplePosts",
            {"post_identifiers": post_ids}
        )
        self.usage["reddit"] += 1
        
        if isinstance(result, dict) and "posts" in result:
            return result["posts"]
        elif isinstance(result, list):
            return result
        return []
    
    def get_post_comments(self, post_id: str) -> list[dict]:
        """
        Get top-level comments from a post.
        
        Args:
            post_id: Post ID, URL, or permalink
            
        Returns:
            List of top-level comments
        """
        result = self._authorize_and_execute(
            "Reddit.GetTopLevelComments",
            {"post_identifier": post_id}
        )
        self.usage["reddit"] += 1
        
        if isinstance(result, dict) and "comments" in result:
            return result["comments"]
        elif isinstance(result, list):
            return result
        return []
    
    # ==================== Twitter Tools ====================
    
    def search_tweets(self, query: str, max_results: int = 20) -> list[dict]:
        """
        Search recent tweets by keywords.
        
        Args:
            query: Search query string (will be split into keywords/phrases)
            max_results: Max tweets to return (1-100)
            
        Returns:
            List of tweets from last 7 days
        """
        # API expects keywords as array of strings, not single string
        # Split query into individual words as keywords
        keywords = query.split()
        
        inputs = {
            "keywords": keywords,  # Must be array, not string
            "max_results": min(max_results, 100),
        }
        
        result = self._authorize_and_execute(
            "X.SearchRecentTweetsByKeywords",
            inputs
        )
        self.usage["twitter"] += 1
        
        # Twitter API returns tweets in 'data' key, not 'tweets'
        if isinstance(result, dict):
            tweets = result.get("data", result.get("tweets", []))
            return tweets if tweets else []
        elif isinstance(result, list):
            return result
        return []
    
    # ==================== Utility ====================
    
    def get_usage_stats(self) -> dict:
        """Get current API usage counts."""
        return {
            "reddit": self.usage["reddit"],
            "twitter": self.usage["twitter"],
            "total": self.usage["reddit"] + self.usage["twitter"],
        }
    
    def reset_usage(self):
        """Reset usage counters."""
        self.usage = {"reddit": 0, "twitter": 0}


# Convenience function for quick testing
def test_arcade_connection() -> bool:
    """Test Arcade.dev connection."""
    try:
        client = ArcadeClient()
        posts = client.get_subreddit_posts("test", limit=1)
        logger.info(f"Arcade connection test: {'OK' if posts else 'Empty response'}")
        return True
    except Exception as e:
        logger.error(f"Arcade connection test failed: {e}")
        return False
