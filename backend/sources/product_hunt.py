"""Product Hunt GraphQL API client."""
import logging
from datetime import datetime, timedelta
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
        Fetch top AI product launches from the past N days.
        
        Args:
            limit: Maximum number of products to fetch (default 20)
            days: Number of past days to fetch (default 1)
            
        Returns:
            List of ProductLaunch objects sorted by votes
        """
        query = """
        query GetAIProducts($first: Int!, $postedAfter: DateTime) {
            posts(
                first: $first,
                topic: "artificial-intelligence",
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
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
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
                    createdAt=node.get("createdAt", datetime.utcnow().isoformat()),
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


# Convenience function for testing
def fetch_ai_launches(limit: int = 20) -> list[ProductLaunch]:
    """Fetch AI launches using default client."""
    client = ProductHuntClient()
    return client.fetch_ai_launches(limit)
