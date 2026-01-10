"""
LangGraph-based Google Trends validation workflow.
Extracts keywords from various sources, ranks them, and validates against Google Trends.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import TypedDict, List, Optional, Literal, Dict

import nest_asyncio
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langsmith import traceable
from pydantic import BaseModel, Field

# Allow nested event loops (for running async in FastAPI context)
nest_asyncio.apply()

from sources.google_trends import GoogleTrendsClient
from sources.models import TrendValidation, TopicAnalysis
from config.langsmith import configure_langsmith


from config.settings import (
    OPENAI_API_KEY,
    LLM_MODEL_GENERATION,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
)


logger = logging.getLogger(__name__)

# Configure LangSmith tracing (centralized)
configure_langsmith()


# --- Prompts ---

EXTRACTION_PROMPTS = {

"newsletter": """
You are analyzing an AI newsletter written for non-technical business owners.

Your task:
Extract 3 to 5 **searchable Google keywords** that a founder might realistically Google.

Keyword rules (STRICT):
- 1 to 3 words only
- Nouns or short noun phrases only
- Must stand alone as a search query
- Prefer widely used, canonical terms

Do NOT output:
- Full sentences or long phrases
- Trend descriptions or opinions
- Overly specific or niche jargon

Examples (GOOD):
- "AI agents"
- "vibe coding"
- "DeepSeek"

Examples (BAD → FIX):
- "AI infrastructure spending trends" → "AI infrastructure"
- "The future of AI assistants" → "AI assistants"

Content:
{content}

Output ONLY keywords, one per line.
No numbering. No explanations.
""",

"producthunt": """
You are analyzing AI-related Product Hunt launches.

Your task:
Extract 3 to 5 **searchable Google keywords** representing product names or product categories.

Keyword rules (STRICT):
- 1 to 3 words only
- Use official product names OR common category names
- Prefer generic categories over marketing language

Do NOT output:
- Feature descriptions
- Value propositions
- Sentences or long phrases

Examples (GOOD):
- "AI spreadsheet"
- "no-code AI"
- "voice cloning"

Examples (BAD → FIX):
- "AI-powered presentation recording" → "presentation recorder"
- "Automated social media tool" → "social automation"

Content:
{content}

Output ONLY keywords, one per line.
No numbering. No explanations.
""",

"youtube": """
You are analyzing AI influencer video content.

Your task:
Extract 3 to 5 **searchable Google keywords** representing the main AI topics discussed.

Keyword rules (STRICT):
- 1 to 3 words only
- High-level topics, tools, or concepts
- Use common terminology people already search for

Do NOT output:
- Sentences or abstract ideas
- Political or philosophical framing
- Overly broad social commentary

Examples (GOOD):
- "ChatGPT"
- "AI agents"
- "robotics automation"

Examples (BAD → FIX):
- "AI-driven job displacement and future of work" → "AI job impact"
- "Robotic automation and surgical robots" → "surgical robots"
- "Platform politics and walled gardens" → "AI platforms"

Content:
{content}

Output ONLY keywords, one per line.
No numbering. No explanations.
""",

"weekly_newsletter": """
You are analyzing weekly AI essays written for business leaders.

Your task:
Extract 3 to 5 **searchable Google keywords** representing strategic AI themes.

Keyword rules (STRICT):
- 1 to 3 words only
- Business-relevant and decision-oriented
- Use established industry language

Do NOT output:
- Narrative phrasing
- Speculative or philosophical language
- Full sentences

Examples (GOOD):
- "AI strategy"
- "enterprise AI"
- "AI transformation"

Examples (BAD → FIX):
- "The evolution of enterprise AI adoption" → "enterprise AI"

Content:
{content}

Output ONLY keywords, one per line.
No numbering. No explanations.
""",

"weekly_producthunt": """
You are analyzing the week's most impactful AI product launches.

Your task:
Extract 3 to 5 **searchable Google keywords** representing tools or tool categories.

Keyword rules (STRICT):
- 1 to 3 words only
- Focus on what the tool *is*, not what it promises
- Prefer category-level terms when possible

Do NOT output:
- Marketing slogans
- Comparative language ("best", "top", "leading")
- Sentences or long phrases

Examples (GOOD):
- "AI writing"
- "workflow automation"
- "no-code AI"

Examples (BAD → FIX):
- "Best AI tools for productivity" → "AI productivity"

Content:
{content}

Output ONLY keywords, one per line.
No numbering. No explanations.
""",

"weekly_youtube": """
You are analyzing a week of AI influencer videos.

Your task:
Extract 3 to 5 **searchable Google keywords** representing the dominant weekly themes.

Keyword rules (STRICT):
- 1 to 3 words only
- Use canonical tool names or well-known AI concepts
- Avoid niche phrasing unique to one creator

Do NOT output:
- Commentary or opinions
- Sentences or multi-clause phrases

Examples (GOOD):
- "AI coding"
- "Claude API"
- "open source AI"

Examples (BAD → FIX):
- "The state of AI coding assistants" → "AI coding"

Content:
{content}

Output ONLY keywords, one per line.
No numbering. No explanations.
"""
}

RANKING_PROMPT = """
You are a senior editor for a business-focused AI newsletter written for non-technical founders.

Your task:
From the input list, select EXACTLY 12 keywords that are most valuable to feature this week.

If two keywords are similar in meaning, select the one with broader appeal.

Rank implicitly by selecting only the top 12.

Evaluation criteria (in order of importance):
1. Trending momentum — actively rising or widely discussed right now
2. Business actionability — a founder could make a decision, investment, or experiment based on this
3. Search intent — founders are likely to Google this term

Deduplication rules (STRICT):
- Remove duplicates, near-duplicates, and trivial variations
  (case differences, pluralization, tense, or minor wording changes)
- If multiple variants exist, keep the most commonly used / canonical form

Output rules (STRICT):
- Output ONLY the final 12 keywords
- One keyword per line
- No numbering, bullets, commentary, or extra text
- Do NOT invent new keywords
- Do NOT rephrase keywords

Input keywords:
{keywords}
"""



# --- State Definition ---

class TrendState(TypedDict):
    inputs: List[Dict[str, str]]    # List of {'source': str, 'content': str}
    extracted_keywords: List[Dict[str, str]] # List of {'keyword': str, 'source': str}
    ranked_keywords: List[Dict[str, str]] # Top 12 keywords with source info
    validation_results: List[TrendValidation] 
    final_analysis: Optional[TopicAnalysis]
    source_type: Literal["daily", "weekly", "global"]  # Context for analysis


# --- Graph Builder ---

class TrendGraph:
    """LangGraph workflow for trend validation."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLM_MODEL_GENERATION,
            temperature=0.3,
            max_tokens=LLM_MAX_TOKENS,
            api_key=OPENAI_API_KEY,
            timeout=LLM_TIMEOUT_SECONDS,
            max_retries=LLM_MAX_RETRIES,
        )
        self.trends_client = GoogleTrendsClient()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(TrendState)
        
        workflow.add_node("extract_keywords", self.extract_keywords_node)
        workflow.add_node("rank_keywords", self.rank_keywords_node)
        workflow.add_node("validate_trends", self.validate_trends_node)
        workflow.add_node("generate_output", self.generate_output_node)
        
        workflow.set_entry_point("extract_keywords")
        workflow.add_edge("extract_keywords", "rank_keywords")
        workflow.add_edge("rank_keywords", "validate_trends")
        workflow.add_edge("validate_trends", "generate_output")
        workflow.add_edge("generate_output", END)
        
        return workflow.compile()

    def extract_keywords_node(self, state: TrendState) -> TrendState:
        """Extract keywords from all input sources concurrently."""
        inputs = state.get("inputs", [])
        
        # Prepare extraction tasks
        extraction_tasks = []
        
        for item in inputs:
            source = item.get("source")
            content = item.get("content")
            
            if not source or not content:
                continue
                
            prompt_template = EXTRACTION_PROMPTS.get(source)
            if not prompt_template:
                # Fallback for generic sources if needed, or skip
                continue
                
            if "producthunt" in source:
                # Optimized handling for Product Hunt JSON to save tokens
                try:
                    import json
                    if isinstance(content, str) and content.strip().startswith("["):
                        data = json.loads(content)
                        # Extract only high-signal fields
                        simplified_items = []
                        for ph_item in data:
                            name = ph_item.get("name", "")
                            tagline = ph_item.get("tagline", "")
                            desc = ph_item.get("description", "")[:200]  # Truncate description
                            simplified_items.append(f"Product: {name}\nTagline: {tagline}\nDescription: {desc}")
                        
                        # Re-join as simplified text
                        content = "\n---\n".join(simplified_items)
                        logger.info(f"Simplified Product Hunt JSON to {len(content)} chars")
                except Exception as e:
                    logger.warning(f"Failed to parse PH JSON: {e}")

            if len(content.strip()) < 50:
                continue

            # Safer truncation limit for LLM
            prompt = prompt_template.format(content=content[:15000])
            extraction_tasks.append((source, prompt))
        
        if not extraction_tasks:
            return {"extracted_keywords": []}
        
        # Define async extraction function
        async def extract_single(source: str, prompt: str) -> List[Dict[str, str]]:
            """Extract keywords from a single source asynchronously."""
            try:
                response = await self.llm.ainvoke(prompt)
                keywords = [
                    line.strip() 
                    for line in response.content.strip().split('\n') 
                    if line.strip() and len(line.strip()) > 1
                ]
                
                # Tag each keyword with its source (limit 5 per source)
                result = [{"keyword": kw, "source": source} for kw in keywords[:5]]
                logger.info(f"Extracted {len(keywords)} keywords from {source}")
                return result
                
            except Exception as e:
                logger.error(f"Extraction failed for {source}: {e}")
                return []
        
        # Run all extractions concurrently
        async def extract_all():
            tasks = [extract_single(source, prompt) for source, prompt in extraction_tasks]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        # Execute the async function - nest_asyncio allows this even in async context
        results = asyncio.run(extract_all())
        
        # Flatten results and filter out exceptions
        all_keywords = []
        for result in results:
            if isinstance(result, list):
                all_keywords.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Extraction task failed with exception: {result}")
        
        return {"extracted_keywords": all_keywords}

    def rank_keywords_node(self, state: TrendState) -> TrendState:
        """Rank extracted keywords and select top 12."""
        extracted = state.get("extracted_keywords", [])
        
        if not extracted:
            return {"ranked_keywords": []}
            
        # Create a mapping to look up source by keyword later
        # Cases: duplicates? We'll take the first source encountered or merge.
        # Simple approach: map keyword -> source
        kw_source_map = {k['keyword']: k['source'] for k in extracted}
        
        unique_keywords = list(kw_source_map.keys())
        
        prompt = RANKING_PROMPT.format(keywords="\n".join(unique_keywords))
        
        ranked_list = []
        try:
            response = self.llm.invoke(prompt)
            ranked_strings = [
                line.strip() 
                for line in response.content.strip().split('\n') 
                if line.strip() and len(line.strip()) > 1
            ]
            
            # Fallback if empty
            if not ranked_strings:
                logger.warning("Empty ranking response, using fallback")
                ranked_strings = unique_keywords[:12]
            
            # Reconstruct list with source info
            # We must fuzzy match or exact match the returned keywords to our source map
            # LLM usually returns exact strings from input list
            
            for rank_kw in ranked_strings[:12]:
                # Try exact match
                if rank_kw in kw_source_map:
                    ranked_list.append({
                        "keyword": rank_kw,
                        "source": kw_source_map[rank_kw]
                    })
                else:
                    # If LLM slightly modified it, try to find close match or skip
                    # For simplicity, skip unmatched to avoid validation errors
                    pass
            
            # If we lost too many due to matching, fill with top extracted
            if len(ranked_list) < min(5, len(unique_keywords)):
                 missing = 12 - len(ranked_list)
                 for kw in unique_keywords:
                     if any(r['keyword'] == kw for r in ranked_list):
                         continue
                     if missing <= 0:
                         break
                     ranked_list.append({
                         "keyword": kw,
                         "source": kw_source_map[kw]
                     })
                     missing -= 1
            
            logger.info(f"Ranked {len(ranked_list)} keywords")
            return {"ranked_keywords": ranked_list}
            
        except Exception as e:
            logger.error(f"Ranking failed: {e}")
            # Fallback
            fallback = []
            for kw in unique_keywords[:12]:
                 fallback.append({
                     "keyword": kw,
                     "source": kw_source_map[kw]
                 })
            return {"ranked_keywords": fallback}

    @traceable(name="validate_trends_node")
    def validate_trends_node(self, state: TrendState) -> TrendState:
        """Validate ranked keywords against Google Trends."""
        ranked = state.get("ranked_keywords", [])
        if not ranked:
            return {"validation_results": []}
            
        keywords = [item['keyword'] for item in ranked]
        
        # Batch validation
        validations = self.trends_client.validate_topics_batch(keywords)
        
        # Re-attach source info to validation objects
        # We need to match back by keyword
        final_validations = []
        
        # Create map for O(1) loop up
        rank_map = {item['keyword']: item['source'] for item in ranked}
        
        for val in validations:
            # Add content_source
            if val.keyword in rank_map:
                val.content_source = rank_map[val.keyword]
            final_validations.append(val)
            
        return {"validation_results": final_validations}

    @traceable(name="generate_output_node")
    def generate_output_node(self, state: TrendState) -> TrendState:
        """Generate final TopicAnalysis object with summary."""
        validations = state.get("validation_results", [])
        source_type = state.get("source_type", "global")
        
        # Segment by audience (technical vs strategic)
        technical_topics = [
            v.keyword for v in validations 
            if "technical" in v.audience_tags and (v.trend_score >= 30 or v.interest_score > 50)
        ]
        strategic_topics = [
            v.keyword for v in validations 
            if "strategic" in v.audience_tags and (v.trend_score >= 30 or v.interest_score > 50)
        ]
        
        # Generate summary string (multi-line with bold titles)
        top_trends = sorted(validations, key=lambda x: x.trend_score, reverse=True)[:5]
        rising = [v.keyword for v in top_trends if v.trend_direction == "rising"]
        
        summary_parts = []
        if rising:
            summary_parts.append(f"**Rising:** {', '.join(rising)}")
        if technical_topics[:3]:
            summary_parts.append(f"**Technical Focus:** {', '.join(technical_topics[:3])}")
        if strategic_topics[:3]:
            summary_parts.append(f"**Strategic Focus:** {', '.join(strategic_topics[:3])}")
            
        summary = "\n".join(summary_parts) if summary_parts else "No strong trends detected"
        
        analysis = TopicAnalysis(
            source="global", # The API output is always global aggregation
            source_date=datetime.now().date(),
            topics=validations,
            top_technical_topics=technical_topics[:5],
            top_strategic_topics=strategic_topics[:5],
            summary=summary
        )
        
        return {"final_analysis": analysis}

    def process(self, inputs: List[Dict[str, str]], source_type: Literal["daily", "weekly"] = "daily") -> TopicAnalysis:
        """Run the workflow."""
        logger.info(f"Starting Trend Validation Graph ({source_type}) with {len(inputs)} inputs")
        
        initial_state: TrendState = {
            "inputs": inputs,
            "extracted_keywords": [],
            "ranked_keywords": [],
            "validation_results": [],
            "final_analysis": None,
            "source_type": source_type
        }
        
        final = self.graph.invoke(initial_state)
        return final["final_analysis"]
