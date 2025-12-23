# AI Content Curation Engine: Development Roadmap

> **Vision**: Build an AI-native System of Intelligence that transforms fragmented information sources into a proprietary content asset, surfacing actionable opportunities for content creators.

---

## Project Structure

```
emailagent/                    # Monorepo root
├── backend/                   # Python agents, LangGraph, FastAPI
├── dashboard/                 # Next.js frontend
├── conductor/                 # Workflow orchestration configs
├── docker-compose.yml         # Local development stack
└── ROADMAP.md                 # This file
```

---

## Current Progress (December 2025)

### ✅ Completed

| Phase | Feature | Status |
|-------|---------|--------|
| **Phase 0** | Daily newsletter digest | ✅ Complete |
| **Phase 1** | Weekly deep insights digest | ✅ Complete |
| **Phase 3** | PostgreSQL database (local Docker) | ✅ Complete |
| **Phase 5** | Next.js dashboard MVP | ✅ Complete |

### What's Working Now:
- **Daily Digest**: `python main.py --type dailydigest`
- **Weekly Deep Dive**: `python main.py --type weeklydeepdives`
- **Database**: PostgreSQL with raw email storage + digests
- **Dashboard**: Next.js with Daily/Weekly toggle, real-time polling
- **API**: FastAPI with `/api/digest/latest`, `/api/digest/history`, `/api/emails`
- **Docker Stack**: 4 services (emailagent, api, dashboard, db)

---

## Strategic Foundation: a16z Agentic Blueprint

```
┌─────────────────────────────────────────────────────────────┐
│                    THE FOUR-LAYER MODEL                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: COMPOUNDING VALUE (Outcome-Based Pricing)         │
│  Layer 3: PROACTIVE INTERFACE (Push, Not Pull)              │
│  Layer 2: AUTONOMOUS AGENT (Multi-Agent Collaboration)      │
│  Layer 1: DATA FOUNDATION (The Defensible Moat)             │
└─────────────────────────────────────────────────────────────┘
```

| Principle | How We Apply It |
|-----------|-----------------|
| **Data Pipeline = Moat** | Store raw + processed data; build robust extraction pipelines |
| **Workflows > Tasks** | Use LangGraph for complex flows; end-to-end content pipeline |
| **Proactive > Reactive** | Push-based dashboard with Approve/Reject actions |
| **Outcomes > Features** | Track content performance; close feedback loop |

---

## Phase Roadmap

### Phase 0-1: Core Digests ✅ COMPLETE

**Implemented:**
- `sender_whitelist.json` with `type` field (`dailydigest` / `weeklydeepdives`)
- `EmailSummarizer` for daily news
- `DeepDiveSummarizer` for weekly thought leadership
- Separate LLM configs: extraction (nano) vs generation (mini)
- Quality check nodes for all content
- Database persistence via `save_to_database()`

---

### Phase 3: Database Foundation ✅ COMPLETE

**Implemented:**
- PostgreSQL 15 via Docker
- SQLAlchemy models: `Digest`, `Email`
- Raw email body storage for future re-processing
- FastAPI endpoints for dashboard

---

### Phase 5: Dashboard MVP ✅ COMPLETE

**Implemented:**
- Next.js 14 with App Router
- Tailwind CSS with glassmorphism design
- Daily/Weekly toggle with tabs
- `BriefingCard`, `LinkedInCard`, `DeepDiveCard` components
- Real-time polling for new content notifications

---

### Phase 4: Product Hunt Integration 🔜 NEXT

**Goal**: Add automated AI tool discovery from Product Hunt.

**Execution**: Once daily (fetch yesterday's top 20-50 products).

**Why**: Catch trend NO.1 on that day to collect product ideas and create "Top AI Tools" content.

**Implementation Plan:**
```python
# backend/sources/product_hunt.py
# GraphQL API - 500 requests/day (Free)
def fetch_daily_launches() -> list[dict]:
    # Query posts tagged 'artificial-intelligence' ranked by votes
```

---

### Phase 4a: Video Platform Trending (YouTube & TikTok) 🔜 NEXT

**Goal**: Discover viral topics programmatically from YouTube and TikTok.

**Why**: Identify what's actually getting views vs just what's being written about.

**Capabilities:**
- **YouTube Trending**: Use YouTube Data API v3 (`mostPopular`, `videoCategoryId=28`) to find trending tech/AI videos.
- **TikTok Trends**: Use TikTok Research API or 3rd-party scrapers for trending hashtags and hooks.

---

### Phase 4b: Hacker News Integration 🔜 NEXT

**Goal**: Technical deep dives and developer sentiment.

**Execution**: Once weekly (or daily filter for high-signal stories).

**Why**: HN is where developers discuss technical depth and model releases (GPT-5, Claude, etc.) honestly.

**Filter Strategy**:
- Min score: 100+ (community consensus)
- Keywords: AI, LLM, GPT, Agents, Automation

---

### Phase 4.5: Vector Embeddings 📅 AFTER DATA SOURCES

**Goal**: Enable semantic search across all stored content (Newsletters + PH + YT + HN).

**Implementation:**
- Switch to `pgvector/pgvector:pg15` Docker image.
- Add vector columns to unified `content_items` table.
- Implement monthly embedding cost control (~$0.01/mo).

---

### Phase 4.6: Google Trends Validation 📅 FINAL DATA STEP

**Goal**: Validate topics from all sources against general public search interest.

**Strategy**: Validation layer, not discovery. Use to prioritize topics for content creation.

---

### Phase 6: Multi-Agent Architecture 📅 Q1 2026

**Goal**: Evolve from single graph to specialized agent collaboration (Curator, Analyst, Creator).

---

### Phase 7: Feedback Loop 📅 Q2 2026

**Goal**: Track platform engagement (LinkedIn, TikTok, YT) to improve content suggestions.

---

### Phase 8: ChatGPT App Integration 📅 Q1 2026

**Goal**: Publish EmailAgent as a ChatGPT App.

**Enhanced Strategy**: Build the multi-source foundation (PH, YT, HN) FIRST to provide a superior "Know/Do/Show" experience beyond just newsletters.

**Updated Capabilities:**
- `get_trending_ai_tools`: From Product Hunt daily launches.
- `get_platform_trends`: YouTube and TikTok viral hooks.
- `get_validated_insights`: Newsletters + Google Trends validation.

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Agent Framework | LangGraph |
| LLM | OpenAI o4-mini |
| Database | PostgreSQL 15 + pgvector (planned) |
| API | FastAPI |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |

---

## Cost Estimation (Monthly)

| Service | Cost |
|---------|------|
| OpenAI LLM (GPT-4o-mini) | ~$0.25 |
| OpenAI Embeddings (future) | ~$0.01 |
| Data Source APIs | Free (PH, HN, YT Data API) |
| **Total** | **~$0.30/month** |

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Multi-Source Foundation First | Enhance ChatGPT App value with tools, video trends, and dev signals | Dec 2025 |
| Skip Reddit | Too noisy; HN + PH provide higher signal for builder/creator needs | Dec 2025 |
| HN Once Weekly/Daily | Balance signal vs noise; personal use vs content creation | Dec 2025 |
| YouTube Trending Daily | High-value signal for SME/Founder content creation | Dec 2025 |

---

*Last Updated: December 22, 2025*
