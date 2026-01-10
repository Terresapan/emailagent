"""Google Trends client with SerpAPI (primary) and pytrends (fallback)."""
import logging
import json
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

import requests

from config import settings
from sources.models import TrendValidation

logger = logging.getLogger(__name__)

# Keywords that indicate technically-focused content
TECHNICAL_KEYWORDS = [
    "tutorial", "how to build", "api", "sdk", "open source", "github",
    "programming", "code", "developer", "framework", "library", "cli",
    "documentation", "integration", "deploy", "self-hosted"
]

# Keywords that indicate strategically-focused content
STRATEGIC_KEYWORDS = [
    "pricing", "for startups", "vs", "alternative", "benefits", "roi",
    "for business", "enterprise", "saas", "productivity", "automation",
    "no-code", "low-code", "cost", "free", "trial", "strategy", "growth"
]


class GoogleTrendsClient:
    """
    Hybrid Google Trends client.
    
    Primary: SerpAPI (reliable, 250 free/month)
    Fallback: pytrends (free but unreliable)
    """
    
    SERPAPI_BASE_URL = "https://serpapi.com/search"
    USAGE_FILE = Path(settings.BASE_DIR) / "logs" / "serpapi_usage.json"
    
    def __init__(self, serpapi_key: Optional[str] = None):
        self.serpapi_key = serpapi_key or settings.SERPAPI_KEY
        self.monthly_limit = settings.SERPAPI_MONTHLY_LIMIT
        self._load_usage()
        
        # Try to import pytrends for fallback
        try:
            from pytrends.request import TrendReq
            self.pytrends_available = True
        except ImportError:
            self.pytrends_available = False
            logger.warning("pytrends not installed - fallback unavailable")
    
    def _load_usage(self):
        """Load monthly usage counter from file."""
        try:
            if self.USAGE_FILE.exists():
                with open(self.USAGE_FILE, "r") as f:
                    data = json.load(f)
                    # Reset if new month
                    if data.get("month") != datetime.now().strftime("%Y-%m"):
                        self._reset_usage()
                    else:
                        self.monthly_usage = data.get("count", 0)
            else:
                self._reset_usage()
        except Exception as e:
            logger.warning(f"Failed to load usage file: {e}")
            self._reset_usage()
    
    def _reset_usage(self):
        """Reset the monthly usage counter."""
        self.monthly_usage = 0
        self._save_usage()
    
    def _save_usage(self):
        """Save monthly usage counter to file."""
        try:
            self.USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.USAGE_FILE, "w") as f:
                json.dump({
                    "month": datetime.now().strftime("%Y-%m"),
                    "count": self.monthly_usage
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save usage file: {e}")
    
    def _increment_usage(self):
        """Increment and save usage counter."""
        self.monthly_usage += 1
        self._save_usage()
    
    def _can_use_serpapi(self) -> bool:
        """Check if we can use SerpAPI (have key and quota)."""
        return bool(self.serpapi_key) and self.monthly_usage < self.monthly_limit
    
    def _get_serpapi_trends(self, keyword: str) -> Optional[dict]:
        """
        Fetch trend data from SerpAPI.
        
        Returns dict with:
            - interest_over_time: list of {date, value} dicts
            - related_queries: list of query strings
        """
        if not self._can_use_serpapi():
            return None
        
        try:
            # Fetch interest over time
            params = {
                "engine": "google_trends",
                "q": keyword,
                "data_type": "TIMESERIES",
                "api_key": self.serpapi_key,
            }
            
            response = requests.get(self.SERPAPI_BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            self._increment_usage()
            
            # Extract interest over time
            interest_data = []
            timeline = data.get("interest_over_time", {}).get("timeline_data", [])
            for point in timeline:
                values = point.get("values", [])
                if values:
                    interest_data.append({
                        "date": point.get("date"),
                        "value": values[0].get("extracted_value", 0)
                    })
            
            # Note: Related queries would require a separate API call (doubling usage)
            # Skipping to conserve API quota - can be enabled if needed
            related = []
            
            return {
                "interest_over_time": interest_data,
                "related_queries": related
            }
            
        except requests.RequestException as e:
            logger.error(f"SerpAPI request failed for '{keyword}': {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing SerpAPI response for '{keyword}': {e}")
            return None
    
    def _get_pytrends_data(self, keyword: str) -> Optional[dict]:
        """
        Fetch trend data using pytrends (fallback).
        
        Note: pytrends is unreliable and may return 429 errors.
        """
        if not self.pytrends_available:
            return None
        
        try:
            from pytrends.request import TrendReq
            import time
            import random
            
            # Add randomized delay to avoid aggressive rate limiting
            sleep_time = random.uniform(5, 10)
            logger.info(f"Sleeping {sleep_time:.1f}s before pytrends request...")
            time.sleep(sleep_time)
            
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([keyword], timeframe='today 3-m')
            
            # Get interest over time
            df = pytrends.interest_over_time()
            interest_data = []
            if not df.empty and keyword in df.columns:
                for date, row in df.iterrows():
                    interest_data.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "value": int(row[keyword])
                    })
            
            # Get related queries
            related = []
            try:
                # Add another small sleep before second request
                time.sleep(2) 
                related_df = pytrends.related_queries()
                if keyword in related_df and related_df[keyword].get("rising") is not None:
                    rising = related_df[keyword]["rising"]
                    if not rising.empty:
                        related = rising["query"].head(5).tolist()
            except Exception:
                pass  # Related queries often fail
            
            return {
                "interest_over_time": interest_data,
                "related_queries": related
            }
            
        except Exception as e:
            logger.warning(f"pytrends failed for '{keyword}': {e}")
            return None
    
    def _classify_audience(self, keyword: str, related_queries: list[str]) -> list[str]:
        """
        Classify topic for target audience based on keyword and related queries.
        
        Returns list of audience tags: ["technical"], ["strategic"], or ["technical", "strategic"]
        """
        all_text = (keyword + " " + " ".join(related_queries)).lower()
        
        tags = []
        
        # Check for technical signals
        if any(tk in all_text for tk in TECHNICAL_KEYWORDS):
            tags.append("technical")
        
        # Check for strategic signals
        if any(sk in all_text for sk in STRATEGIC_KEYWORDS):
            tags.append("strategic")
        
        # Default to both if no clear signal (broad appeal)
        if not tags:
            tags = ["technical", "strategic"]
        
        return tags
    
    def _calculate_momentum(self, interest_data: list[dict]) -> tuple[float, str]:
        """
        Calculate week-over-week momentum from interest data.
        
        Returns:
            (momentum_pct, direction)
            - momentum_pct: % change from previous week
            - direction: "rising", "stable", or "declining"
        """
        if len(interest_data) < 14:
            return 0.0, "stable"
        
        # Compare last 7 days to previous 7 days
        recent = interest_data[-7:]
        previous = interest_data[-14:-7]
        
        recent_avg = sum(p["value"] for p in recent) / len(recent) if recent else 0
        previous_avg = sum(p["value"] for p in previous) / len(previous) if previous else 0
        
        if previous_avg == 0:
            return 0.0, "stable"
        
        momentum = ((recent_avg - previous_avg) / previous_avg) * 100
        
        if momentum > 10:
            direction = "rising"
        elif momentum < -10:
            direction = "declining"
        else:
            direction = "stable"
        
        return round(momentum, 1), direction
    
    def _calculate_trend_score(
        self,
        interest_score: int,
        momentum: float,
        related_count: int,
        has_audience_fit: bool
    ) -> int:
        """
        Calculate composite trend score (0-100).
        
        Weights:
            - interest_score: 35%
            - momentum: 30%
            - related_queries: 20%
            - audience_fit: 15%
        """
        # Normalize momentum to 0-100 (clip to -50 to +50 range)
        momentum_normalized = min(max((momentum + 50), 0), 100)
        
        # Normalize related count (0-5 queries → 0-100)
        related_normalized = min(related_count * 20, 100)
        
        # Audience fit is binary
        audience_score = 100 if has_audience_fit else 50
        
        score = (
            interest_score * 0.35 +
            momentum_normalized * 0.30 +
            related_normalized * 0.20 +
            audience_score * 0.15
        )
        
        return int(round(score))
    
    def validate_topic(self, keyword: str) -> TrendValidation:
        """
        Validate a single topic against Google Trends.
        
        Tries SerpAPI first, falls back to pytrends if quota exhausted.
        
        Args:
            keyword: Topic/keyword to validate
            
        Returns:
            TrendValidation with scores and audience classification
        """
        logger.info(f"Validating topic: '{keyword}'")
        
        # Try SerpAPI first
        data = self._get_serpapi_trends(keyword)
        api_source = "serpapi"
        
        # Fall back to pytrends if SerpAPI unavailable or failed
        if data is None:
            logger.info(f"Falling back to pytrends for '{keyword}'")
            data = self._get_pytrends_data(keyword)
            api_source = "pytrends"
        
        # If both failed, return minimal validation
        if data is None:
            logger.warning(f"All APIs failed for '{keyword}' - returning minimal validation")
            return TrendValidation(
                keyword=keyword,
                interest_score=0,
                momentum=0.0,
                trend_direction="stable",
                related_queries=[],
                audience_tags=["builder", "founder"],
                trend_score=0,
                api_source="cached"
            )
        
        # Extract metrics
        interest_data = data.get("interest_over_time", [])
        related_queries = data.get("related_queries", [])
        
        # Calculate interest score (average of last 7 days)
        if interest_data:
            recent = interest_data[-7:] if len(interest_data) >= 7 else interest_data
            interest_score = int(sum(p["value"] for p in recent) / len(recent))
        else:
            interest_score = 0
        
        # Calculate momentum
        momentum, trend_direction = self._calculate_momentum(interest_data)
        
        # Classify audience
        audience_tags = self._classify_audience(keyword, related_queries)
        
        # Calculate composite score
        trend_score = self._calculate_trend_score(
            interest_score=interest_score,
            momentum=momentum,
            related_count=len(related_queries),
            has_audience_fit=len(audience_tags) > 0
        )
        
        return TrendValidation(
            keyword=keyword,
            interest_score=interest_score,
            momentum=momentum,
            trend_direction=trend_direction,
            related_queries=related_queries,
            audience_tags=audience_tags,
            trend_score=trend_score,
            api_source=api_source
        )
    
    def validate_topics_batch(self, keywords: list[str]) -> list[TrendValidation]:
        """
        Validate multiple topics.
        
        Args:
            keywords: List of topics to validate
            
        Returns:
            List of TrendValidation results
        """
        results = []
        for keyword in keywords:
            result = self.validate_topic(keyword)
            results.append(result)
        
        # Sort by trend score (highest first)
        results.sort(key=lambda x: x.trend_score, reverse=True)
        
        return results
    
    def get_usage_stats(self) -> dict:
        """Get current API usage statistics."""
        return {
            "serpapi_used": self.monthly_usage,
            "serpapi_limit": self.monthly_limit,
            "serpapi_remaining": max(0, self.monthly_limit - self.monthly_usage),
            "month": datetime.now().strftime("%Y-%m"),
            "pytrends_available": self.pytrends_available
        }


# Convenience function for testing
def validate_topic(keyword: str) -> TrendValidation:
    """Validate a single topic using default client."""
    client = GoogleTrendsClient()
    return client.validate_topic(keyword)
