import requests
import time
from typing import List, Dict, Optional
from .models import HackerNewsStory
from utils.logger import setup_logger

logger = setup_logger(__name__)

class HackerNewsClient:
    """Client for interacting with the official Hacker News API."""
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self):
        self.session = requests.Session()
    
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
    
    def _fetch_comments(self, comment_ids: List[int], limit: int = 3) -> List[str]:
        """
        Fetch text content of top root comments.
        
        Args:
            comment_ids: List of comment IDs (kids)
            limit: Maximum number of comments to fetch
            
        Returns:
            List of comment text strings (HTML stripped/cleaned via simple extraction)
        """
        comments = []
        # Take top N comments
        target_ids = comment_ids[:limit]
        
        for cid in target_ids:
            try:
                # Short timeout for comments to avoid hanging
                response = self.session.get(f"{self.BASE_URL}/item/{cid}.json", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    # Only keep valid text comments (not deleted/dead)
                    if data and data.get('text') and not data.get('deleted') and not data.get('dead'):
                        comments.append(data['text'])
            except Exception as e:
                logger.warning(f"Failed to fetch comment {cid}: {e}")
                continue
                
        return comments
    
    def get_top_stories(self, limit: int = 20) -> List[int]:
        """Fetch the IDs of the current top stories."""
        try:
            response = self.session.get(f"{self.BASE_URL}/topstories.json", timeout=10)
            response.raise_for_status()
            ids = response.json()
            return ids[:limit]
        except Exception as e:
            logger.error(f"Failed to fetch top stories from HN: {e}")
            return []
    
    def get_story_details(self, story_id: int) -> Optional[HackerNewsStory]:
        """Fetch details for a single story."""
        try:
            response = self.session.get(f"{self.BASE_URL}/item/{story_id}.json", timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if not data or data.get('type') != 'story':
                return None
            
            # Fetch top 3 comments if available
            comments = []
            if 'kids' in data:
                comments = self._fetch_comments(data['kids'], limit=3)
            
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

    def fetch_top_stories_with_details(self, limit: int = 20) -> List[HackerNewsStory]:
        """Fetch top stories and their full details."""
        story_ids = self.get_top_stories(limit=limit * 2) # Fetch extra to account for skips
        idx = 0
        stories = []
        
        logger.info(f"Fetching details for {len(story_ids)} trending HN stories...")
        
        for sid in story_ids:
            if len(stories) >= limit:
                break
                
            details = self.get_story_details(sid)
            if details:
                stories.append(details)
            
            # Rate limit politeness
            time.sleep(0.1)
            
        return stories
