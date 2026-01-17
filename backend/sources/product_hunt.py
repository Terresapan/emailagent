"""Product Hunt GraphQL API client."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests

from config import settings
from sources.models import ProductLaunch

logger = logging.getLogger(__name__)


class ProductHuntClient:
    """Client for fetching AI product launches from Product Hunt."""
    
    API_URL = "https://api.producthunt.com/v2/api/graphql"
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.PRODUCT_HUNT_TOKEN
        if not self.token:
            raise ValueError("PRODUCT_HUNT_TOKEN is required")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
    
    def fetch_ai_launches(self, limit: int = 20, days: int = 1) -> list[ProductLaunch]:
        """
        Fetch top product launches from the past N days (homepage leaderboard).
        
        Args:
            limit: Maximum number of products to fetch (default 20)
            days: Number of past days to fetch (default 1)
            
        Returns:
            List of ProductLaunch objects sorted by votes
        """
        # Query for ALL top products (not just AI topic) to match homepage
        query = """
        query GetTopProducts($first: Int!, $postedAfter: DateTime) {
            posts(
                first: $first,
                postedAfter: $postedAfter,
                order: VOTES
            ) {
                edges {
                    node {
                        id
                        name
                        tagline
                        description
                        votesCount
                        website
                        createdAt
                        topics {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        # Get products from the last N days
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
        
        variables = {
            "first": limit,
            "postedAfter": start_date,
        }
        
        try:
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            
            posts = data.get("data", {}).get("posts", {}).get("edges", [])
            
            launches = []
            for edge in posts:
                node = edge.get("node", {})
                
                # Extract topic names
                topics = []
                topic_edges = node.get("topics", {}).get("edges", [])
                for topic_edge in topic_edges:
                    topic_name = topic_edge.get("node", {}).get("name")
                    if topic_name:
                        topics.append(topic_name)
                
                launch = ProductLaunch(
                    id=node.get("id", ""),
                    name=node.get("name", "Unknown"),
                    tagline=node.get("tagline", ""),
                    description=node.get("description"),
                    votesCount=node.get("votesCount", 0),
                    website=node.get("website"),
                    topics=topics,
                    createdAt=node.get("createdAt", datetime.now(timezone.utc).isoformat()),
                )
                launches.append(launch)
            
            logger.info(f"Fetched {len(launches)} AI products from Product Hunt")
            return launches
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch from Product Hunt: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing Product Hunt response: {e}")
            return []
    
    def fetch_with_reviews(self, limit: int = 50, days: int = 7) -> list[dict]:
        """
        Fetch AI product launches for gap analysis.
        
        Note: Product Hunt API doesn't have reviews field, 
        so we use product details + comments for gap analysis.
        
        Args:
            limit: Maximum products to fetch
            days: Look back period
            
        Returns:
            List of products with details for gap analysis
        """
        # Use the standard query without reviews (reviews field doesn't exist)
        query = """
        query GetProductsForAnalysis($first: Int!, $postedAfter: DateTime) {
            posts(
                first: $first,
                postedAfter: $postedAfter,
                order: VOTES
            ) {
                edges {
                    node {
                        id
                        name
                        tagline
                        description
                        votesCount
                        commentsCount
                        reviewsCount
                        website
                        createdAt
                        topics {
                            edges {
                                node {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        from datetime import datetime, timedelta, timezone
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")
        
        variables = {
            "first": limit,
            "postedAfter": start_date,
        }
        
        try:
            response = requests.post(
                self.API_URL,
                headers=self.headers,
                json={"query": query, "variables": variables},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                return []
            
            posts = data.get("data", {}).get("posts", {}).get("edges", [])
            
            results = []
            for edge in posts:
                node = edge.get("node", {})
                
                # Extract topics
                topics = []
                for topic_edge in node.get("topics", {}).get("edges", []):
                    topic_name = topic_edge.get("node", {}).get("name")
                    if topic_name:
                        topics.append(topic_name)
                
                results.append({
                    "id": node.get("id"),
                    "name": node.get("name"),
                    "tagline": node.get("tagline"),
                    "description": node.get("description"),
                    "votes": node.get("votesCount", 0),
                    "comments_count": node.get("commentsCount", 0),
                    "reviews_count": node.get("reviewsCount", 0),
                    "website": node.get("website"),
                    "topics": topics,
                })
            
            logger.info(f"Fetched {len(results)} products for gap analysis")
            return results
            
        except Exception as e:
            logger.error(f"Failed to fetch products for gap analysis: {e}")
            return []


# Convenience function for testing
def fetch_ai_launches(limit: int = 20) -> list[ProductLaunch]:
    """Fetch AI launches using default client."""
    client = ProductHuntClient()
    return client.fetch_ai_launches(limit)


def fetch_for_gap_analysis(limit: int = 50, days: int = 7) -> list[dict]:
    """Fetch products with reviews for gap analysis."""
    client = ProductHuntClient()
    return client.fetch_with_reviews(limit, days)
