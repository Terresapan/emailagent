import requests
import time
from typing import List, Dict, Optional
from .models import HackerNewsStory
from utils.logger import setup_logger

logger = setup_logger(__name__)


# Default AI/LLM search queries for filtering HackerNews stories
# These terms are used to search Algolia for AI-related content
DEFAULT_AI_QUERIES = [
    # Core AI terms
    "AI",
    "LLM",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    # Major AI companies/labs
    "OpenAI",
    "Anthropic",
    "DeepMind",
    "Mistral",
    # Major AI products/models
    "ChatGPT",
    "GPT-4",
    "Claude",
    "Gemini",
    "Llama",
    "Copilot",
    # AI applications
    "AI agents",
    "generative AI",
]


class HackerNewsClient:
    """Client for interacting with HackerNews via Algolia Search API.
    
    Uses the free Algolia-powered HackerNews search API to fetch AI/LLM-related
    stories with filtering capabilities. No API key required.
    """
    
    # Algolia Search API (free, no auth required)
    ALGOLIA_BASE_URL = "https://hn.algolia.com/api/v1"
    
    # Firebase API for fetching comments (Algolia doesn't include comment text)
    FIREBASE_BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self, ai_queries: Optional[List[str]] = None):
        """Initialize client with optional custom AI search queries.
        
        Args:
            ai_queries: List of search terms to filter for AI/LLM content.
                       Defaults to DEFAULT_AI_QUERIES if not provided.
        """
        self.session = requests.Session()
        self.ai_queries = ai_queries or DEFAULT_AI_QUERIES
    
    def _fetch_github_stars(self, url: Optional[str]) -> Optional[int]:
        """
        If URL is a GitHub repo, fetch and return its star count.
        
        Args:
            url: The story URL to check
            
        Returns:
            Star count if GitHub repo, None otherwise
        """
        if not url or 'github.com' not in url:
            return None
            
        try:
            # Extract owner/repo from URL like https://github.com/owner/repo/...
            parts = url.replace('https://', '').replace('http://', '').split('/')
            if len(parts) < 3 or parts[0] != 'github.com':
                return None
                
            owner, repo = parts[1], parts[2].split('?')[0].split('#')[0]
            if not owner or not repo:
                return None
                
            # Call GitHub API (unauthenticated - 60 req/hr limit, but fine for ~20 stories)
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            response = self.session.get(api_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                stars = data.get('stargazers_count')
                logger.debug(f"GitHub stars for {owner}/{repo}: {stars}")
                return stars
            else:
                logger.debug(f"GitHub API returned {response.status_code} for {owner}/{repo}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to fetch GitHub stars for {url}: {e}")
            return None
    
    def _fetch_comments(self, story_id: str, limit: int = 3) -> List[str]:
        """
        Fetch text content of top root comments using Firebase API.
        
        Args:
            story_id: The story ID to fetch comments for
            limit: Maximum number of comments to fetch
            
        Returns:
            List of comment text strings
        """
        comments = []
        try:
            # First get the story to find comment IDs
            response = self.session.get(
                f"{self.FIREBASE_BASE_URL}/item/{story_id}.json", 
                timeout=5
            )
            if response.status_code != 200:
                return comments
                
            story_data = response.json()
            if not story_data or 'kids' not in story_data:
                return comments
            
            # Fetch top N comments
            comment_ids = story_data['kids'][:limit]
            
            for cid in comment_ids:
                try:
                    resp = self.session.get(
                        f"{self.FIREBASE_BASE_URL}/item/{cid}.json", 
                        timeout=3
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if data and data.get('text') and not data.get('deleted') and not data.get('dead'):
                            comments.append(data['text'])
                except Exception as e:
                    logger.warning(f"Failed to fetch comment {cid}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Failed to fetch comments for story {story_id}: {e}")
            
        return comments

    def search_ai_stories(
        self, 
        query: Optional[str] = None,
        min_points: int = 5,  # Lowered to ensure enough stories after filtering
        limit: int = 20,
        hours_ago: int = 24  # Only fetch stories from the last N hours
    ) -> List[Dict]:
        """
        Search for recent AI/LLM-related stories using Algolia API.
        
        Uses search_by_date endpoint to get the most recent stories first,
        filtered by age to ensure freshness (last 24 hours by default).
        
        Args:
            query: Custom search query. If None, searches multiple AI terms.
            min_points: Minimum upvote points for stories (default 10 for recent).
            limit: Maximum number of stories to return.
            hours_ago: Only include stories from the last N hours (default 24).
            
        Returns:
            List of story dictionaries from Algolia API, sorted by popularity.
        """
        import time as time_module
        
        # Use search_by_date for recent stories
        endpoint = f"{self.ALGOLIA_BASE_URL}/search_by_date"
        
        # Calculate cutoff timestamp (stories older than this are excluded)
        cutoff_timestamp = int(time_module.time()) - (hours_ago * 3600)
        
        # If custom query provided, use it directly
        if query is not None:
            queries = [query]
        else:
            # Use ALL configured AI queries for comprehensive coverage
            # Latency is ~5s for 18 terms which is acceptable for a daily job
            queries = self.ai_queries
        
        all_hits = []
        seen_ids = set()
        
        for q in queries:
            # Don't break early - we want comprehensive coverage from all terms
            params = {
                "query": q,
                "tags": "story",
                "numericFilters": f"points>{min_points},created_at_i>{cutoff_timestamp}",
                # Fetch more per query to account for false positives that get filtered
                "hitsPerPage": max(limit * 2, 30)
            }
            
            try:
                response = self.session.get(endpoint, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                hits = data.get("hits", [])
                
                # Deduplicate by story ID
                for hit in hits:
                    story_id = hit.get("objectID")
                    if story_id and story_id not in seen_ids:
                        seen_ids.add(story_id)
                        all_hits.append(hit)
                        
            except Exception as e:
                logger.warning(f"Algolia search failed for query '{q}': {e}")
                continue
        
        # Filter out false positives (e.g., "Air Lines" matching "AI")
        # Check that title actually contains AI-related terms as whole words
        import re
        ai_pattern = re.compile(
            r'\b(AI|LLM|GPT|ChatGPT|Claude|Gemini|Llama|Copilot|OpenAI|Anthropic|DeepMind|Mistral|'
            r'artificial\s+intelligence|machine\s+learning|deep\s+learning|neural\s+network|'
            r'generative|transformer|diffusion|AGI)\b',
            re.IGNORECASE
        )
        
        filtered_hits = []
        for hit in all_hits:
            title = hit.get("title", "")
            url = hit.get("url", "") or ""
            # Check title and URL for actual AI-related terms
            if ai_pattern.search(title) or ai_pattern.search(url):
                filtered_hits.append(hit)
            else:
                logger.debug(f"Filtered out non-AI story: {title[:50]}")
        
        logger.info(f"Filtered {len(all_hits)} -> {len(filtered_hits)} truly AI-related stories")
        all_hits = filtered_hits
        
        # Sort by POPULARITY (points) within the 24h window
        # This shows "today's most important AI stories" not just "newest"
        all_hits.sort(key=lambda x: x.get("points", 0), reverse=True)
        
        logger.info(f"Algolia returned {len(all_hits)} AI stories from last {hours_ago}h (sorted by popularity)")
        return all_hits[:limit]

    def get_story_details(self, story_id: int) -> Optional[HackerNewsStory]:
        """Fetch details for a single story (used for fallback/legacy compatibility)."""
        try:
            response = self.session.get(
                f"{self.FIREBASE_BASE_URL}/item/{story_id}.json", 
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or data.get('type') != 'story':
                return None
            
            # Fetch top 3 comments if available
            comments = []
            if 'kids' in data:
                comments = self._fetch_comments(str(story_id), limit=3)
            
            # Fetch GitHub stars if URL is a GitHub repo
            story_url = data.get('url')
            github_stars = self._fetch_github_stars(story_url)
                
            return HackerNewsStory(
                id=str(data.get('id')),
                title=data.get('title', 'Untitled'),
                url=story_url,
                score=data.get('score', 0),
                comments_count=data.get('descendants', 0),
                by=data.get('by', 'unknown'),
                time=data.get('time'),
                comments=comments,
                github_stars=github_stars
            )
        except Exception as e:
            logger.warning(f"Failed to fetch HN story {story_id}: {e}")
            return None

    def fetch_top_stories_with_details(
        self, 
        limit: int = 20,
        min_points: int = 5,  # Lowered to ensure enough stories after AI filtering
        include_comments: bool = True
    ) -> List[HackerNewsStory]:
        """
        Fetch top AI/LLM-related stories with full details using Algolia API.
        
        This is the main method to use for fetching filtered HN content.
        
        Args:
            limit: Maximum number of stories to return.
            min_points: Minimum upvote points for stories.
            include_comments: Whether to fetch top comments (slower but richer).
            
        Returns:
            List of HackerNewsStory objects filtered for AI/LLM content.
        """
        # Search for AI-related stories
        hits = self.search_ai_stories(min_points=min_points, limit=limit)
        
        if not hits:
            logger.warning("No AI stories found via Algolia, falling back to general top stories")
            # Fallback: try broader search
            hits = self.search_ai_stories(
                query="technology OR programming OR startup",
                min_points=50,
                limit=limit
            )
        
        stories = []
        
        for hit in hits:
            if len(stories) >= limit:
                break
            
            try:
                story_id = hit.get("objectID", "")
                
                # Algolia provides most fields directly
                story_url = hit.get("url")
                
                # Fetch comments if requested
                comments = []
                if include_comments and story_id:
                    comments = self._fetch_comments(story_id, limit=3)
                    time.sleep(0.05)  # Brief rate limit
                
                # Fetch GitHub stars
                github_stars = self._fetch_github_stars(story_url)
                
                story = HackerNewsStory(
                    id=story_id,
                    title=hit.get("title", "Untitled"),
                    url=story_url,
                    score=hit.get("points", 0),
                    comments_count=hit.get("num_comments", 0),
                    by=hit.get("author", "unknown"),
                    time=hit.get("created_at_i"),  # Unix timestamp
                    comments=comments,
                    github_stars=github_stars
                )
                stories.append(story)
                
            except Exception as e:
                logger.warning(f"Failed to process Algolia hit: {e}")
                continue
        
        logger.info(f"✓ Fetched {len(stories)} AI/LLM-related HN stories via Algolia")
        return stories

    # Legacy method for backward compatibility
    def get_top_stories(self, limit: int = 20) -> List[int]:
        """Fetch the IDs of the current top stories (legacy method).
        
        Note: This still uses Firebase API. For filtered AI stories,
        use fetch_top_stories_with_details() instead.
        """
        try:
            response = self.session.get(
                f"{self.FIREBASE_BASE_URL}/topstories.json", 
                timeout=10
            )
            response.raise_for_status()
            ids = response.json()
            return ids[:limit]
        except Exception as e:
            logger.error(f"Failed to fetch top stories from HN: {e}")
            return []
