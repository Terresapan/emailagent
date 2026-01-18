"""Pain point extraction using LLM.

Extracts pain points from raw social media/review data.
Uses 5 LLM calls (one per source) to extract 100-145 raw pain points.
"""
import logging
from datetime import datetime
from typing import Optional

from langchain_openai import ChatOpenAI

from config.settings import LLM_MODEL_EXTRACTION, LLM_MAX_TOKENS
from processor.viral_app.models import PainPoint

logger = logging.getLogger(__name__)


# Extraction prompt template
EXTRACTION_PROMPT = """You are a pain point analyst. Extract specific pain points from the following {source_type} data.

A PAIN POINT is:
- A specific problem someone is frustrated with
- Something someone wishes existed
- A task that is tedious/manual/time-consuming
- A complaint about existing tools

Look for phrases like:
- "I wish there was..."
- "It's so frustrating that..."
- "Why isn't there an app for..."
- "I spend hours doing..."
- "There should be a way to..."

For each pain point, output:
1. The exact quote or paraphrase
2. The underlying problem in 1-2 sentences

Format each pain point as:
QUOTE: [exact text or paraphrase]
PROBLEM: [the underlying pain point]
---

{source_context}

Data to analyze:
{data}

Output the top {max_points} most actionable pain points. Focus on problems that could be solved by a simple mini-app.
"""


# Source-specific context
SOURCE_CONTEXTS = {
    "reddit": "These are Reddit posts and comments from subreddits like smallbusiness, freelance, and Entrepreneur. Focus on business owner frustrations.",
    "twitter": "These are tweets from people discussing AI tools and productivity. Look for complaints and wishes.",
    "youtube": "These are YouTube comments on viral AI/productivity videos. Find people asking for solutions or expressing frustration.",
    "producthunt": "These are Product Hunt reviews with ratings. Focus on low-rated products and complaints about what's missing.",
}


class PainPointExtractor:
    """Extracts pain points from raw data using LLM."""
    
    def __init__(self, model: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=model or LLM_MODEL_EXTRACTION,
            temperature=0.3,
            max_tokens=LLM_MAX_TOKENS,
        )
        self.call_count = 0
    
    def extract_from_reddit(
        self, 
        posts: list[dict], 
        comments: list[dict],
        max_points: int = 30,
    ) -> list[PainPoint]:
        """Extract pain points from Reddit posts and comments."""
        # Format data for LLM
        data_text = self._format_reddit_data(posts, comments)
        
        if not data_text:
            return []
        
        raw_output = self._call_llm("reddit", data_text, max_points)
        return self._parse_pain_points(raw_output, "reddit")
    
    def extract_from_twitter(
        self,
        tweets: list[dict],
        max_points: int = 20,
    ) -> list[PainPoint]:
        """Extract pain points from tweets."""
        data_text = self._format_twitter_data(tweets)
        
        if not data_text:
            return []
        
        raw_output = self._call_llm("twitter", data_text, max_points)
        return self._parse_pain_points(raw_output, "twitter")
    
    def extract_from_youtube(
        self,
        comments: list[dict],
        max_points: int = 25,
    ) -> list[PainPoint]:
        """Extract pain points from YouTube comments."""
        data_text = self._format_youtube_data(comments)
        
        if not data_text:
            return []
        
        raw_output = self._call_llm("youtube", data_text, max_points)
        return self._parse_pain_points(raw_output, "youtube")
    
    def extract_from_producthunt(
        self,
        products: list[dict],
        max_points: int = 20,
    ) -> list[PainPoint]:
        """Extract pain points from Product Hunt reviews."""
        data_text = self._format_producthunt_data(products)
        
        if not data_text:
            return []
        
        raw_output = self._call_llm("producthunt", data_text, max_points)
        return self._parse_pain_points(raw_output, "producthunt")
    
    def _format_reddit_data(self, posts: list[dict], comments: list[dict]) -> str:
        """Format Reddit data for the prompt."""
        lines = []
        
        # Add posts
        for post in posts[:50]:  # Limit to avoid token overflow
            title = post.get("title", "")
            body = post.get("body", post.get("selftext", ""))[:500]
            score = post.get("score", 0)
            subreddit = post.get("subreddit", "")
            
            lines.append(f"[r/{subreddit} | {score} pts] {title}")
            if body:
                lines.append(f"  {body[:300]}")
        
        # Add comments
        for comment in comments[:100]:
            text = comment.get("body", comment.get("text", ""))[:300]
            score = comment.get("score", 0)
            
            if text:
                lines.append(f"[Comment | {score} pts] {text}")
        
        return "\n".join(lines)
    
    def _format_twitter_data(self, tweets: list[dict]) -> str:
        """Format Twitter data for the prompt."""
        lines = []
        
        for tweet in tweets[:100]:
            text = tweet.get("text", "")[:280]
            likes = tweet.get("likes", tweet.get("like_count", 0))
            
            lines.append(f"[{likes} likes] {text}")
        
        return "\n".join(lines)
    
    def _format_youtube_data(self, comments: list[dict]) -> str:
        """Format YouTube comments for the prompt."""
        lines = []
        
        for comment in comments[:150]:
            text = comment.get("text", "")[:300]
            likes = comment.get("likes", comment.get("likeCount", 0))
            video_id = comment.get("video_id", "")
            
            lines.append(f"[Video: {video_id} | {likes} likes] {text}")
        
        return "\n".join(lines)
    
    def _format_producthunt_data(self, products: list[dict]) -> str:
        """Format Product Hunt data for the prompt (without reviews)."""
        lines = []
        
        for product in products[:50]:
            name = product.get("name", "")
            tagline = product.get("tagline", "")
            description = product.get("description", "")[:300] if product.get("description") else ""
            votes = product.get("votes", 0)
            comments_count = product.get("comments_count", 0)
            
            lines.append(f"[{name}] ({votes} votes, {comments_count} comments)")
            lines.append(f"  Tagline: {tagline}")
            if description:
                lines.append(f"  Description: {description}")
        
        return "\n".join(lines)
    
    def _call_llm(self, source: str, data: str, max_points: int) -> str:
        """Call the LLM with the extraction prompt."""
        prompt = EXTRACTION_PROMPT.format(
            source_type=source,
            source_context=SOURCE_CONTEXTS.get(source, ""),
            data=data,
            max_points=max_points,
        )
        
        logger.info(f"LLM extraction for {source}: data length={len(data)} chars")
        
        try:
            response = self.llm.invoke(prompt)
            self.call_count += 1
            
            content = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"LLM extraction call #{self.call_count} for {source}: response length={len(content)} chars")
            
            # Log first 200 chars of response for debugging
            if content:
                logger.debug(f"Response preview for {source}: {content[:200]}...")
            else:
                logger.warning(f"Empty response from LLM for {source}")
                logger.warning(f"Full response object: {response}")
                if hasattr(response, "response_metadata"):
                     logger.warning(f"Response metadata: {response.response_metadata}")
            
            return content
        except Exception as e:
            logger.error(f"LLM extraction failed for {source}: {e}", exc_info=True)
            return ""
    
    def _parse_pain_points(self, raw_output: str, source: str) -> list[PainPoint]:
        """Parse LLM output into PainPoint objects."""
        pain_points = []
        
        if not raw_output:
            logger.warning(f"Empty LLM output for {source}")
            return []
        
        # Log output length for debugging
        logger.debug(f"Raw output length for {source}: {len(raw_output)} chars")
        
        # Split by separator
        entries = raw_output.split("---")
        
        for entry in entries:
            entry = entry.strip()
            if not entry:
                continue
            
            # Parse QUOTE and PROBLEM
            quote = ""
            problem = ""
            
            for line in entry.split("\n"):
                line = line.strip()
                if line.upper().startswith("QUOTE:"):
                    quote = line[6:].strip()
                elif line.upper().startswith("PROBLEM:"):
                    problem = line[8:].strip()
            
            if problem:  # At minimum we need a problem
                pain_points.append(PainPoint(
                    text=quote or problem,
                    problem=problem,
                    source=source,
                    source_id="",
                    extracted_at=datetime.now(),
                ))
        
        # Fallback: if no pain points parsed but output exists, try alternative formats
        if not pain_points and len(raw_output) > 50:
            logger.warning(f"Standard parsing failed for {source}, trying fallback...")
            # Try parsing numbered lists like "1. Problem description"
            for line in raw_output.split("\n"):
                line = line.strip()
                # Match numbered items like "1. ", "1) ", "- "
                if line and (line[0].isdigit() or line.startswith("-")):
                    # Remove numbering
                    text = line.lstrip("0123456789.-) ").strip()
                    if len(text) > 20:  # Must be substantial
                        pain_points.append(PainPoint(
                            text=text,
                            problem=text,
                            source=source,
                            source_id="",
                            extracted_at=datetime.now(),
                        ))
        
        logger.info(f"Parsed {len(pain_points)} pain points from {source}")
        return pain_points
    
    def get_call_count(self) -> int:
        """Return the number of LLM calls made."""
        return self.call_count
