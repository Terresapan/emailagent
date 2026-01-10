"""
Topic Validation Service for post-processing content insights.

This service extracts topics from various content sources (Product Hunt, Hacker News, 
YouTube, Newsletters) and validates them against Google Trends to prioritize 
content for technical builders and non-tech founders.
"""
import logging
from datetime import datetime
from typing import Optional

from sources.google_trends import GoogleTrendsClient
from sources.models import (
    TrendValidation,
    TopicAnalysis,
    ProductHuntInsight,
    HackerNewsInsight,
    YouTubeInsight,
)

logger = logging.getLogger(__name__)


class TopicValidationService:
    """
    Post-processing service to validate topics from all content sources.
    
    Workflow:
    1. Extract topics from source insights (PH, HN, YouTube, etc.)
    2. Validate each topic against Google Trends
    3. Score and classify for target audiences
    4. Return prioritized topic analysis
    """
    
    def __init__(self, trends_client: Optional[GoogleTrendsClient] = None):
        self.trends = trends_client or GoogleTrendsClient()
    
    def extract_topics_from_producthunt(self, insight: ProductHuntInsight) -> list[str]:
        """
        Extract topic keywords from Product Hunt launches.
        
        Extracts:
        - Product names (if AI-related)
        - Topics/categories from launches
        - Key terms from taglines
        """
        topics = set()
        
        for launch in insight.top_launches:
            # Add product name if it looks like a technology/tool
            name = launch.name.strip()
            if name and len(name) < 50:  # Skip overly long names
                topics.add(name)
            
            # Add topics from categories
            for topic in launch.topics:
                if topic and len(topic) > 2:
                    topics.add(topic)
        
        # Also include any patterns from content_angles that look like topics
        for angle in insight.content_angles:
            # Extract capitalized terms that might be product/tech names
            words = angle.split()
            for word in words:
                if word[0].isupper() and len(word) > 3 and word.isalpha():
                    topics.add(word)
        
        return list(topics)[:15]  # Limit to 15 topics
    
    def extract_topics_from_hackernews(self, insight: HackerNewsInsight) -> list[str]:
        """
        Extract topic keywords from Hacker News stories.
        
        Extracts:
        - top_themes from insight
        - Key terms from story titles
        """
        topics = set()
        
        # Top themes are already extracted
        for theme in insight.top_themes:
            topics.add(theme)
        
        # Extract notable terms from story titles
        for story in insight.stories:
            title_words = story.title.split()
            for word in title_words:
                # Look for tech terms (capitalized, not common words)
                if (word[0].isupper() and 
                    len(word) > 3 and 
                    word.lower() not in ["show", "ask", "tell", "what", "why", "how", "the", "and"]):
                    topics.add(word)
        
        return list(topics)[:15]
    
    def extract_topics_from_youtube(self, insight: YouTubeInsight) -> list[str]:
        """
        Extract topic keywords from YouTube videos.
        
        Extracts:
        - key_topics from insight
        - Notable terms from video titles
        """
        topics = set()
        
        # Key topics are already extracted
        for topic in insight.key_topics:
            topics.add(topic)
        
        # Extract from video titles (mainly tech/product names)
        for video in insight.videos:
            title_words = video.title.split()
            for word in title_words:
                if (word[0].isupper() and 
                    len(word) > 3 and 
                    word.lower() not in ["how", "why", "what", "the", "and", "for", "with"]):
                    topics.add(word)
        
        return list(topics)[:15]
    
    
    def extract_topics_from_newsletter(self, digest_summary: str) -> list[str]:
        """
        Extract topic keywords from Newsletter digest summaries.
        
        Extracts:
        - Capitalized terms that appear to be subjects/tools
        - Key concepts from the summary text
        """
        topics = set()
        
        # Simple heuristic: Look for capitalized words that aren't start of sentences
        # This is a basic implementation that can be improved with NLP
        words = digest_summary.split()
        for i, word in enumerate(words):
            clean_word = word.strip(".,;:()[]\"'")
            if (len(clean_word) > 3 and 
                clean_word[0].isupper() and 
                clean_word.isalpha() and
                i > 0): # Skip first word of sentences roughly
                
                # Filter out likely common words
                if clean_word.lower() not in ["this", "that", "there", "what", "when", "where", "with", "from", "today", "digest"]:
                    topics.add(clean_word)
        
        return list(topics)[:15]

    def validate_and_analyze(
        self,
        source: str,
        topics: list[str],
        source_date: Optional[datetime] = None
    ) -> TopicAnalysis:
        """
        Validate topics and generate analysis.
        
        Args:
            source: Source type ('producthunt', 'hackernews', 'youtube', 'newsletter')
            topics: List of topic keywords to validate
            source_date: Date of the source content
            
        Returns:
            TopicAnalysis with validated topics and audience segmentation
        """
        if source_date is None:
            source_date = datetime.utcnow()
        
        logger.info(f"Validating {len(topics)} topics from {source}")
        
        # Validate all topics
        validations = self.trends.validate_topics_batch(topics)
        
        # Segment by audience
        builder_topics = [
            v.keyword for v in validations 
            if "builder" in v.audience_tags and v.trend_score >= 30
        ]
        founder_topics = [
            v.keyword for v in validations 
            if "founder" in v.audience_tags and v.trend_score >= 30
        ]
        
        # Generate summary of top trends
        top_trends = validations[:5]  # Top 5 by score
        rising = [v.keyword for v in top_trends if v.trend_direction == "rising"]
        
        summary_parts = []
        if rising:
            summary_parts.append(f"Rising: {', '.join(rising)}")
        if builder_topics[:3]:
            summary_parts.append(f"Builder focus: {', '.join(builder_topics[:3])}")
        if founder_topics[:3]:
            summary_parts.append(f"Founder focus: {', '.join(founder_topics[:3])}")
        
        summary = " | ".join(summary_parts) if summary_parts else "No strong trends detected"
        
        return TopicAnalysis(
            source=source,
            source_date=source_date,
            topics=validations,
            top_builder_topics=builder_topics[:5],
            top_founder_topics=founder_topics[:5],
            summary=summary
        )
    
    def validate_producthunt(self, insight: ProductHuntInsight) -> TopicAnalysis:
        """Validate topics from a Product Hunt insight."""
        topics = self.extract_topics_from_producthunt(insight)
        return self.validate_and_analyze("producthunt", topics, insight.date)
    
    def validate_hackernews(self, insight: HackerNewsInsight) -> TopicAnalysis:
        """Validate topics from a Hacker News insight."""
        topics = self.extract_topics_from_hackernews(insight)
        return self.validate_and_analyze("hackernews", topics, insight.date)
    
    def validate_youtube(self, insight: YouTubeInsight) -> TopicAnalysis:
        """Validate topics from a YouTube insight."""
        topics = self.extract_topics_from_youtube(insight)
        return self.validate_and_analyze("youtube", topics, insight.date)

    def validate_newsletter(self, summary: str, date: datetime = None) -> TopicAnalysis:
        """Validate topics from a Newsletter summary."""
        topics = self.extract_topics_from_newsletter(summary)
        return self.validate_and_analyze("newsletter", topics, date)
    
    def get_usage_stats(self) -> dict:
        """Get Google Trends API usage statistics."""
        return self.trends.get_usage_stats()
