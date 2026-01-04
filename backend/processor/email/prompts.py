"""
Prompt templates for LLM-based email processing.

This module contains all prompt templates used in the email
summarization and content generation workflow.

Prompt Categories:
1. EMAIL_SUMMARIZATION_PROMPT - Extracts structured summaries from newsletters
2. DIGEST_BRIEFING_PROMPT - Creates aggregated AI briefing
3. LINKEDIN_CONTENT_PROMPT - Generates LinkedIn post ideas and content
4. QUALITY_CHECK_*_PROMPT - Quality checks for briefing and LinkedIn content
5. *_EMAIL_TEMPLATE - Final email formatting templates
"""

# =============================================================================
# Email Summarization Prompt
# =============================================================================

EMAIL_SUMMARIZATION_PROMPT = """You are an AI assistant summarizing AI newsletter content for a professional who builds AI agents for SMEs.

Your task: Analyze the ENTIRE newsletter and extract the TOP 5 most important and relevant points for each category below. Be highly selective and curate only the highest-signal information.

Output format - use these EXACT bold headings:

**Industry News / Trends:**
- External events, market shifts, regulatory changes, product launches, or notable announcements.
- Must be explicitly stated in the newsletter.

**New Tools:**
- New AI tools, products, services, or platform updates that were released, showcased, or reviewed.

**Insights:**
- Expert opinions, strategic guidance, predictions, best practices, or actionable takeaways.
- Must reflect stated ideas, not inferred or invented.

Rules:
- Only include a category if relevant content exists.
- Curate and select the TOP 5 most important and relevant points per category.
- Each bullet must be one sentence, no more than 25 words.
- No fluff, marketing language, or speculation.
- Do NOT infer trends or insights that are not explicitly mentioned.
- If content is purely promotional or lacks substance, write: "No meaningful content."
- If content is mentioned as sponsored or "PRESENTED BY" or "FROM OUR PARTNERS", tag it as "[SPONSORED]" at the start of the bullet.

Newsletter Subject: {subject}
Newsletter From: {sender}

Newsletter Content:
{body}

Provide the summary using the exact bold headings above.
"""

# =============================================================================
# Content Generation Prompts
# =============================================================================

DIGEST_BRIEFING_PROMPT = """You are an AI assistant creating a daily AI briefing for an AI agent builder working with SMEs.

Your input is a set of newsletter summaries. Your goal is to identify true patterns across them — no hallucinations, no invented information.

Create a briefing with the following sections. Use these EXACT bold headings:

**What's Happening (top takeaways)**
- Analyze all summaries and curate the TOP 10 most significant themes and patterns.
- Only use information explicitly contained in the provided summaries.
- Short, casual, easy-to-understand language.
- Each bullet max 25 words.
- If content is mentioned as sponsored, tag it as "[SPONSORED]" at the start.

**What This Means for You (practical actions)**
- Curate the TOP 5 most actionable takeaways for someone building AI agents for SMEs.
- Focus on practical opportunities, risks, and signals derived from today's news.
- Each bullet max 25 words.

**Notes**
- Any important caveats, disclaimers, or context that the reader should know.
- Keep this section brief (1-3 bullets max).

Tone:
- Casual, friendly, and simple (high school level).
- Avoid jargon and avoid speculation.

Input Summaries:
{newsletter_summaries}

Create the briefing using the exact bold headings above.
"""

LINKEDIN_CONTENT_PROMPT = """You are an AI assistant creating LinkedIn content for founders and entrepreneurs building AI agents.

Your input is a set of newsletter summaries. Your goal is to create engaging LinkedIn posts based on real themes from these summaries.

Create LinkedIn content with the following sections. Use these EXACT bold headings:

**LinkedIn Post Ideas — Top 3**

Provide exactly the TOP 3 post ideas based on the themes found in the summaries. For each idea:
- **[Topic Title]** — Clear, engaging title
- **Why It Resonates:** One sentence explaining why founders/entrepreneurs building AI agents would care
- **Based on Theme(s):** List the specific theme(s) from the summaries

**Full LinkedIn Posts — Top 3**

Now write 3 complete LinkedIn posts, one for each idea above.

**Post 1: [Post Title]**
[Full post content here]

**Post 2: [Post Title]**
[Full post content here]

**Post 3: [Post Title]**
[Full post content here]

Target Audience: Founders and Entrepreneurs building AI agents

Post Format Requirements:
- First sentence must be a strong hook that grabs attention
- Use short sentences. Line by line.
- Keep paragraphs to 1-2 lines max
- Use emojis strategically (2-4 per post, not excessive)
- Include a clear takeaway or call-to-action at the end
- Maximum 200 words per post

Tone:
- Casual, friendly, and simple (high school level).
- Avoid jargon and avoid speculation.

**CRITICAL FORMATTING**: All section headings and post titles MUST use bold markdown (**text**).

Input Summaries:
{newsletter_summaries}

Create the LinkedIn content with bold headings:
"""

# =============================================================================
# Quality Check Prompts
# =============================================================================

QUALITY_CHECK_DIGEST_PROMPT = """You are a quality reviewer for AI newsletter briefings.

Evaluate the briefing below and improve it if needed. Focus on:

1. **Clarity** – Is it easy to understand at a high school level?
2. **Actionability** – Are the insights practical, specific, and useful?
3. **Curation** – Are the top points truly the most important and relevant (not just filler)?
4. **Structure** – Are the sections clearly separated and logically organized?
5. **Tone** – Is the tone casual, conversational, and concise?
6. **Accuracy** – Does it avoid speculation, invented themes, or exaggeration?
7. **Sponsored Content** – Are any points explicitly marked as "[SPONSORED]"? Compare with source summaries to ensure nothing was missed.
8. **Consistency** - Does the briefing accurately reflect the input summaries?
9. **Formatting** - Section headings MUST use bold markdown syntax.

**CRITICAL FORMATTING REQUIREMENT**: You MUST preserve bold markdown syntax (**text**) for ALL section headings:
- **What's Happening (top takeaways)**
- **What This Means for You (practical actions)**
- **Notes**
- **Industry News:**
- **New Tools:**
- **Insights:**


You may rewrite, reorganize, shorten, or simplify the briefing as needed.
If it is already excellent, return it exactly as-is.
ALWAYS preserve bold formatting on section headings.

Source Newsletter Summaries:
{newsletter_summaries}

Original Briefing:
{original_briefing}

Provide the final reviewed briefing with bold section headings:
"""

QUALITY_CHECK_LINKEDIN_PROMPT = """You are a quality reviewer for LinkedIn content aimed at founders and entrepreneurs building AI agents.

Evaluate the LinkedIn content below and improve it if needed. Focus on:

1. **Hook Quality** – Does each post start with a strong, attention-grabbing first sentence?
2. **Brevity** – Are sentences short and punchy? Are paragraphs 1-2 lines max?
3. **Emoji Usage** – Are emojis used wisely (2-4 per post, strategically placed)?
4. **Target Audience** – Does the content resonate with founders/entrepreneurs building AI agents?
5. **Clarity & Actionability** – Is each post clear and actionable?
6. **Structure** – Are post ideas and full posts well-organized?
7. **Tone** – Is the tone casual, conversational, and accessible?
8. **Formatting** – Section headings and post titles MUST use bold markdown syntax.

**CRITICAL FORMATTING REQUIREMENT**: You MUST preserve bold markdown syntax (**text**) for ALL headings:
- **LinkedIn Post Ideas — Top 3**
- **[Topic Title]** for each idea
- **Full LinkedIn Posts — Top 3**
- **Post 1: [Title]**, **Post 2: [Title]**, **Post 3: [Title]**

You may rewrite posts if they lack hooks, are too verbose, or miss the target audience.
If it is already excellent, return it exactly as-is.
ALWAYS preserve bold formatting on headings and post titles.

Original LinkedIn Content:
{original_linkedin_content}

Provide the final reviewed LinkedIn content with bold headings:
"""

# =============================================================================
# Email Templates
# =============================================================================

DIGEST_EMAIL_TEMPLATE = """# 📬 AI Newsletter Digest – {date}

{briefing}

---

## 📝 Detailed Summaries

{newsletter_summaries}

---

*Generated by AI Newsletter Agent*
"""

LINKEDIN_EMAIL_TEMPLATE = """# 💼 LinkedIn Content Pack – {date}

{linkedin_content}

---

*Generated by AI Newsletter Agent • Copy & paste directly to LinkedIn!*
"""


# =============================================================================
# Deep Dive Summarization Prompts
# =============================================================================

DEEPDIVE_SUMMARIZATION_PROMPT = """
You are an AI assistant summarizing a long-form AI deep dive written by a credible expert (researcher, operator, or thought leader).

The audience is a professional who builds AI agents and systems for SMEs and cares about strategic clarity, not hype.

Your task:
Analyze the ENTIRE essay and extract its intellectual core.

Produce the following sections, using the exact structure below.

---

**Core Thesis:**
- 1–2 sentences stating the author’s central argument or claim.
- Must be explicitly stated or clearly defended in the text.
- No paraphrasing fluff.

**Key Concepts:**
- List up to 5 named or clearly defined concepts, metaphors, or frameworks introduced or emphasized.
- Each bullet: one sentence, max 25 words.
- Only include concepts actually explained in the essay.

**Primary Arguments:**
- Select the TOP 5 most important arguments that support the thesis.
- Each bullet: one sentence, max 25 words.
- Must reflect the author’s reasoning, not your interpretation.

**Evidence/Examples:**
- Select up to 5 concrete examples, studies, or cases the author uses to make their point.
- One sentence per bullet, max 25 words.
- Only include examples explicitly described.

**Implications:**
- List up to 5 implications the author explicitly states or directly argues follow from their thesis.
- Focus on work, organizations, technology adoption, or human–AI collaboration.
- No speculation.

Rules:
- Be highly selective. Omit anything repetitive, anecdotal, or stylistic.
- Do NOT invent insights or infer unstated conclusions.
- No marketing language.
- If a section has no meaningful content, write: "No meaningful content."
- **IMPORTANT**: All section headings MUST use bold markdown: **Heading Name**

Essay Title: {subject}
Author: {sender}

Essay Content:
{body}

Provide the summary in clean, structured format with bold headings.
"""

# =============================================================================
# Deep Dive Briefing Prompts
# =============================================================================

DEEPDIVE_BRIEFING_PROMPT = """
You are an AI assistant creating a strategic AI deep-dive briefing for a professional who builds AI agents for SMEs.

Your input is a set of summarized long-form essays from experts.

Your job:
Identify shared ideas, tensions, and directional signals across essays — without hallucination or speculation.

Create a briefing with the following sections using these EXACT bold headings:

---

**Big Ideas This Week**
- Curate the TOP 7 most important ideas or arguments that appear across one or more essays.
- Each bullet max 25 words.
- Ideas may come from a single essay if they are especially strong.
- Use simple, direct language.

**Where Experts Agree**
- List up to 5 points where multiple authors converge.
- Must be explicitly supported by the summaries.
- Ideas may come from a single essay if they are especially strong.
- Each bullet max 25 words.

**Where the Real Bottlenecks Are**
- Curate up to 5 constraints, limits, or blockers discussed (technical, human, institutional).
- No speculation.
- Each bullet max 25 words.

**What This Changes for Builders**
- Curate the TOP 5 actionable implications for someone building AI agents for SMEs.
- Focus on design choices, risk management, workflow structure, or product strategy.
- Each bullet max 25 words.

Tone:
- Clear, grounded, and pragmatic.
- Casual but serious.
- No hype, no futurism cosplay.

Input Essay Summaries:
{deepdive_summaries}

Create the briefing using the exact bold headings above.
"""

# =============================================================================
# Deep Dive Quality Check Prompt
# =============================================================================

QUALITY_CHECK_DEEPDIVE_PROMPT = """You are a quality reviewer for AI deep-dive briefings.

Evaluate the briefing below and improve it if needed. Focus on:

1. **Clarity** – Is it easy to understand for a professional audience?
2. **Accuracy** – Does it accurately reflect the source essay summaries?
3. **Curation** – Are the points truly the most important (not filler)?
4. **Structure** – Are all sections present and logically organized?
5. **Actionability** – Are the "What This Changes for Builders" points practical?
6. **Tone** – Is it clear, grounded, and pragmatic (no hype)?
7. **Formatting** - Section headings MUST use bold markdown syntax.

**CRITICAL FORMATTING REQUIREMENT**: You MUST preserve bold markdown syntax (**text**) for ALL section headings:
- **Big Ideas This Week**
- **Where Experts Agree**
- **Where the Real Bottlenecks Are**
- **What This Changes for Builders**

You may rewrite, reorganize, shorten, or clarify as needed.
If it is already excellent, return it exactly as-is.
ALWAYS preserve bold formatting on section headings.

Source Essay Summaries:
{deepdive_summaries}

Original Briefing:
{original_briefing}

Provide the final reviewed briefing with bold section headings:
"""

# =============================================================================
# Deep Dive Email Template
# =============================================================================

DEEPDIVE_EMAIL_TEMPLATE = """# 🧠 Weekly AI Deep Dive – {date}

{briefing}

---

## 📚 Detailed Essay Summaries

{deepdive_summaries}

---

*Generated by AI Newsletter Agent*
"""
