"""YouTube Data API client for fetching videos from influencer channels."""
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from config.settings import YOUTUBE_API_KEY
from utils.logger import setup_logger

logger = setup_logger(__name__)


class YouTubeVideo:
    """Data container for a YouTube video."""
    def __init__(
        self,
        video_id: str,
        title: str,
        channel_name: str,
        channel_id: str,
        description: Optional[str] = None,
        view_count: int = 0,
        published_at: Optional[datetime] = None,
        transcript: Optional[str] = None,
    ):
        self.video_id = video_id
        self.title = title
        self.channel_name = channel_name
        self.channel_id = channel_id
        self.description = description
        self.view_count = view_count
        self.published_at = published_at
        self.transcript = transcript


class YouTubeClient:
    """Client for fetching videos from YouTube influencer channels."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or YOUTUBE_API_KEY
        if not self.api_key:
            raise ValueError("YOUTUBE_API_KEY is required")
        self.session = requests.Session()
        self._handle_cache: dict[str, str] = {}  # Cache handle -> channel_id
    
    def _resolve_channel_id(self, channel_identifier: str) -> Optional[str]:
        """
        Resolve a channel identifier to a channel ID.
        
        Supports both formats:
        - Handle: @samwitteveenai -> resolves to UCxxx...
        - Channel ID: UCxxx... -> returns as-is
        
        Args:
            channel_identifier: Either a handle (@xxx) or channel ID (UCxxx...)
            
        Returns:
            The channel ID (UCxxx...) or None if not found
        """
        # If it looks like a channel ID already, return it
        if channel_identifier.startswith("UC") and len(channel_identifier) == 24:
            return channel_identifier
        
        # Check cache first
        if channel_identifier in self._handle_cache:
            return self._handle_cache[channel_identifier]
        
        # Handle format - resolve via API
        handle = channel_identifier.lstrip("@")  # Remove @ if present
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/channels",
                params={
                    "part": "id",
                    "forHandle": handle,
                    "key": self.api_key,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            if not items:
                logger.warning(f"Channel not found for handle: @{handle}")
                return None
            
            channel_id = items[0]["id"]
            self._handle_cache[channel_identifier] = channel_id
            logger.debug(f"Resolved @{handle} -> {channel_id}")
            return channel_id
            
        except Exception as e:
            logger.error(f"Failed to resolve handle @{handle}: {e}")
            return None
    
    def _get_uploads_playlist_id(self, channel_id: str) -> Optional[str]:
        """
        Get the uploads playlist ID for a channel.
        
        The uploads playlist ID is typically 'UU' + channel_id[2:] but we 
        fetch it properly via API to handle edge cases.
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/channels",
                params={
                    "part": "contentDetails",
                    "id": channel_id,
                    "key": self.api_key,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            if not items:
                logger.warning(f"Channel not found: {channel_id}")
                return None
            
            return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except Exception as e:
            logger.error(f"Failed to get uploads playlist for {channel_id}: {e}")
            return None
    
    def get_channel_videos(
        self, 
        channel_identifier: str, 
        channel_name: str,
        max_results: int = 5,
        days: int = 1
    ) -> List[YouTubeVideo]:
        """
        Fetch recent videos from a channel's uploads playlist.
        
        Args:
            channel_identifier: YouTube channel ID (UCxxx...) OR handle (@xxx)
            channel_name: Human-readable channel name (for output)
            max_results: Maximum number of videos to fetch
            days: Number of days to look back (1 for daily, 7 for weekly)
            
        Returns:
            List of YouTubeVideo objects with basic info (no transcript yet)
        """
        # Resolve handle to channel ID if needed
        channel_id = self._resolve_channel_id(channel_identifier)
        if not channel_id:
            logger.warning(f"Could not resolve channel: {channel_identifier}")
            return []
        
        uploads_id = self._get_uploads_playlist_id(channel_id)
        if not uploads_id:
            return []
        
        try:
            # Get playlist items (video IDs)
            response = self.session.get(
                f"{self.BASE_URL}/playlistItems",
                params={
                    "part": "snippet,contentDetails",
                    "playlistId": uploads_id,
                    "maxResults": max_results,
                    "key": self.api_key,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            video_ids = []
            for item in data.get("items", []):
                video_id = item["contentDetails"]["videoId"]
                video_ids.append(video_id)
            
            if not video_ids:
                return []
            
            # Get video details (view counts, etc.)
            videos_response = self.session.get(
                f"{self.BASE_URL}/videos",
                params={
                    "part": "snippet,statistics",
                    "id": ",".join(video_ids),
                    "key": self.api_key,
                },
                timeout=10,
            )
            videos_response.raise_for_status()
            videos_data = videos_response.json()
            
            # Calculate cutoff time based on days parameter
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
            
            videos = []
            skipped_old = 0
            for item in videos_data.get("items", []):
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                
                # Parse published date
                published_str = snippet.get("publishedAt", "")
                published_at = None
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(
                            published_str.replace("Z", "+00:00")
                        )
                    except ValueError:
                        pass
                
                # Skip videos older than 24 hours
                if published_at and published_at < cutoff_time:
                    skipped_old += 1
                    continue
                
                video = YouTubeVideo(
                    video_id=item["id"],
                    title=snippet.get("title", "Untitled"),
                    channel_name=channel_name,
                    channel_id=channel_id,
                    description=snippet.get("description", ""),  # Full description
                    view_count=int(stats.get("viewCount", 0)),
                    published_at=published_at,
                )
                videos.append(video)
            
            if skipped_old > 0:
                logger.info(f"Skipped {skipped_old} videos older than {days} day(s) from {channel_name}")
            logger.info(f"Fetched {len(videos)} new videos from {channel_name}")
            return videos
            
        except Exception as e:
            logger.error(f"Failed to fetch videos for {channel_name}: {e}")
            return []
    
    def get_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch transcript for a video using youtube-transcript-api.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Full transcript text, or None if unavailable
        """
        try:
            # youtube-transcript-api v1.2.3+ uses instance method fetch() instead of static get_transcript()
            api = YouTubeTranscriptApi()
            transcript_list = api.fetch(video_id)
            # Combine all text segments
            full_text = " ".join([segment.text for segment in transcript_list])
            logger.debug(f"Got transcript for {video_id}: {len(full_text)} chars")
            return full_text
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video {video_id}")
            return None
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id}")
            return None
        except Exception as e:
            logger.warning(f"Failed to get transcript for {video_id}: {e}")
            return None
    
    def fetch_videos_from_channels(
        self,
        channels: List[Dict],
        videos_per_channel: int = 3,
        fetch_transcripts: bool = True,
        days: int = 1,
    ) -> List[YouTubeVideo]:
        """
        Fetch recent videos from multiple channels.
        
        Args:
            channels: List of channel configs with 'channel_id' and 'name' keys
            videos_per_channel: Number of recent videos to fetch per channel
            fetch_transcripts: Whether to fetch transcripts (slower)
            days: Number of days to look back (1 for daily, 7 for weekly)
            
        Returns:
            List of YouTubeVideo objects with transcripts (if available)
        """
        all_videos = []
        
        for channel in channels:
            # Support either handle (@xxx) or channel_id (UCxxx...)
            channel_identifier = channel.get("handle") or channel.get("channel_id")
            channel_name = channel.get("name", "Unknown")
            
            if not channel_identifier or channel_identifier == "REPLACE_WITH_CHANNEL_ID":
                logger.warning(f"Skipping channel with no identifier: {channel_name}")
                continue
            
            videos = self.get_channel_videos(
                channel_identifier=channel_identifier,
                channel_name=channel_name,
                max_results=videos_per_channel,
                days=days,
            )
            
            if fetch_transcripts:
                for video in videos:
                    # Rate limit to be polite to YouTube
                    time.sleep(1.5)
                    video.transcript = self.get_transcript(video.video_id)
            
            all_videos.extend(videos)
            
            # Small delay between channels
            time.sleep(0.5)
        
        logger.info(f"Fetched {len(all_videos)} total videos from {len(channels)} channels")
        return all_videos
    
    def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100,
    ) -> list[dict]:
        """
        Fetch top-level comments from a video for pain point mining.
        
        Uses commentThreads API (costs ~1 quota unit per call).
        
        Args:
            video_id: YouTube video ID
            max_results: Maximum comments to fetch (max 100 per call)
            
        Returns:
            List of comment dicts with 'text', 'author', 'likes', 'published_at'
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/commentThreads",
                params={
                    "part": "snippet",
                    "videoId": video_id,
                    "maxResults": min(max_results, 100),
                    "order": "relevance",  # Top comments first
                    "textFormat": "plainText",
                    "key": self.api_key,
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            
            comments = []
            for item in data.get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                comments.append({
                    "text": snippet.get("textDisplay", ""),
                    "author": snippet.get("authorDisplayName", ""),
                    "likes": snippet.get("likeCount", 0),
                    "published_at": snippet.get("publishedAt", ""),
                })
            
            logger.info(f"Fetched {len(comments)} comments from video {video_id}")
            return comments
            
        except Exception as e:
            logger.warning(f"Failed to fetch comments for {video_id}: {e}")
            return []
    
    def get_comments_from_videos(
        self,
        video_ids: list[str],
        max_comments_per_video: int = 50,
    ) -> list[dict]:
        """
        Fetch comments from multiple videos for pain point discovery.
        
        Args:
            video_ids: List of YouTube video IDs
            max_comments_per_video: Comments per video (default 50)
            
        Returns:
            List of all comments with video_id added to each
        """
        all_comments = []
        
        for video_id in video_ids:
            comments = self.get_video_comments(video_id, max_comments_per_video)
            for comment in comments:
                comment["video_id"] = video_id
            all_comments.extend(comments)
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"Fetched {len(all_comments)} total comments from {len(video_ids)} videos")
        return all_comments
    
    # ==================== Viral Video Discovery ====================
    
    # Default queries for pain point discovery (loaded from config)
    @property
    def DISCOVERY_QUERIES(self) -> list[str]:
        """Load discovery queries from config file."""
        import json
        from pathlib import Path
        
        config_path = Path(__file__).parent.parent / "config" / "discovery_youtube_queries.json"
        
        try:
            with open(config_path) as f:
                data = json.load(f)
                queries = [item["query"] for item in data]
                logger.info(f"Loaded {len(queries)} YouTube queries from config")
                return queries
        except Exception as e:
            logger.warning(f"Failed to load YouTube queries config: {e}, using defaults")
            return [
                "AI tool for small business",
                "automate with AI",
                "AI productivity hack",
                "I wish there was an app",
                "built an app in a day",
            ]
    
    def search_viral_videos(
        self,
        query: str,
        min_views: int = 50000,
        max_results: int = 10,
        published_after_days: int = 90,
    ) -> list[dict]:
        """
        Search for viral videos matching a query.
        
        Costs: 100 quota for search + 1 per video for details
        
        Args:
            query: Search query string
            min_views: Minimum view count to qualify as "viral"
            max_results: Max videos to return (after filtering)
            published_after_days: Only videos from last N days
            
        Returns:
            List of viral video dicts with video_id, title, views, channel
        """
        # Calculate publish date filter
        published_after = (
            datetime.now(timezone.utc) - timedelta(days=published_after_days)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        try:
            # Step 1: Search for videos (100 quota)
            search_response = self.session.get(
                f"{self.BASE_URL}/search",
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "order": "viewCount",  # Most viewed first
                    "publishedAfter": published_after,
                    "maxResults": min(max_results * 2, 50),  # Fetch extra for filtering
                    "key": self.api_key,
                },
                timeout=15,
            )
            search_response.raise_for_status()
            search_data = search_response.json()
            
            video_ids = [
                item["id"]["videoId"]
                for item in search_data.get("items", [])
            ]
            
            if not video_ids:
                return []
            
            # Step 2: Get video details for view counts (1 quota per video)
            details_response = self.session.get(
                f"{self.BASE_URL}/videos",
                params={
                    "part": "snippet,statistics",
                    "id": ",".join(video_ids),
                    "key": self.api_key,
                },
                timeout=15,
            )
            details_response.raise_for_status()
            details_data = details_response.json()
            
            # Step 3: Filter by view count and build results
            viral_videos = []
            for item in details_data.get("items", []):
                view_count = int(item.get("statistics", {}).get("viewCount", 0))
                comment_count = int(item.get("statistics", {}).get("commentCount", 0))
                
                if view_count >= min_views and comment_count > 50:
                    snippet = item.get("snippet", {})
                    viral_videos.append({
                        "video_id": item["id"],
                        "title": snippet.get("title", ""),
                        "channel": snippet.get("channelTitle", ""),
                        "channel_id": snippet.get("channelId", ""),
                        "views": view_count,
                        "comments": comment_count,
                        "published_at": snippet.get("publishedAt", ""),
                        "description": snippet.get("description", "")[:500],
                    })
                    
                    if len(viral_videos) >= max_results:
                        break
            
            logger.info(f"Found {len(viral_videos)} viral videos for query: '{query}'")
            return viral_videos
            
        except Exception as e:
            logger.error(f"Failed to search viral videos for '{query}': {e}")
            return []
    
    def search_for_discovery(
        self,
        queries: list[str] = None,
        min_views: int = 50000,
        videos_per_query: int = 5,
    ) -> list[dict]:
        """
        Search multiple queries to find viral videos for pain point discovery.
        
        Uses ~500-600 quota for 5 queries (well under 10K daily limit).
        
        Args:
            queries: List of search queries (defaults to DISCOVERY_QUERIES)
            min_views: Minimum view count
            videos_per_query: Videos to keep per query
            
        Returns:
            Deduplicated list of viral videos across all queries
        """
        if queries is None:
            queries = self.DISCOVERY_QUERIES
        
        all_videos = {}  # Use dict to dedupe by video_id
        
        for query in queries:
            videos = self.search_viral_videos(
                query=query,
                min_views=min_views,
                max_results=videos_per_query,
            )
            for video in videos:
                # Dedupe by video_id
                if video["video_id"] not in all_videos:
                    video["query"] = query  # Track which query found it
                    all_videos[video["video_id"]] = video
            
            time.sleep(0.5)  # Rate limiting between queries
        
        result = list(all_videos.values())
        logger.info(f"Discovery search found {len(result)} unique viral videos from {len(queries)} queries")
        return result


# Convenience function for testing
def fetch_influencer_videos(limit_per_channel: int = 3) -> List[YouTubeVideo]:
    """Fetch videos from all configured influencer channels."""
    from config.settings import load_youtube_channels
    
    client = YouTubeClient()
    channels = load_youtube_channels()
    return client.fetch_videos_from_channels(
        channels=channels,
        videos_per_channel=limit_per_channel,
    )


def fetch_video_comments(video_id: str, max_results: int = 100) -> list[dict]:
    """Fetch comments from a single video."""
    client = YouTubeClient()
    return client.get_video_comments(video_id, max_results)


def search_viral_for_discovery(
    queries: list[str] = None,
    min_views: int = 50000,
) -> list[dict]:
    """Search for viral videos for pain point discovery."""
    client = YouTubeClient()
    return client.search_for_discovery(queries, min_views)
