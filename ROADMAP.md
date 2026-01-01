# AI Content Curation Engine: Development Roadmap

> **Vision**: Build an AI-native System of Intelligence that transforms fragmented information sources into a proprietary content asset, surfacing actionable opportunities for content creators.

---

## Project Structure

```
emailagent/                    # Monorepo root
├── backend/                   # Python agents, LangGraph, FastAPI
│   ├── db/                    # Shared database models (NEW)
│   ├── api/                   # FastAPI endpoints
│   └── processor/             # LangGraph workflows
├── dashboard/                 # Next.js frontend
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
| **Phase 5.5** | Code quality improvements | ✅ Complete |

### What's Working Now:
- **Daily Digest**: `python main.py --type dailydigest`
- **Weekly Deep Dive**: `python main.py --type weeklydeepdives`
- **Database**: PostgreSQL with raw email storage + digest upsert
- **Dashboard**: Next.js with Daily/Weekly toggle, **Run Now** button, real-time polling
- **API**: FastAPI with `/api/digest/latest`, `/api/process`, `/api/process/status`
- **Docker Stack**: 4 services (emailagent, api, dashboard, db)

### Recent Improvements (Phase 5.5):
- ✅ Removed hardcoded email fallback (security)
- ✅ Consolidated database models into shared `db/` package
- ✅ Updated to SQLAlchemy 2.0 patterns
- ✅ Added connection pooling for database
- ✅ Digest upsert: one per date+type (no duplicates)
- ✅ **Run Now** button with status polling and progress feedback
- ✅ Edge case: "No emails" detection with proper UI feedback

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

---

## Phase Roadmap

### Phase 0-1: Core Digests ✅ COMPLETE

- `sender_whitelist.json` with `type` field (`dailydigest` / `weeklydeepdives`)
- `EmailSummarizer` for daily news (parallel processing via LangGraph)
- `DeepDiveSummarizer` for weekly thought leadership
- Separate LLM configs: extraction (gpt-5-nano) vs generation (gpt-5-mini)
- Quality check nodes for all content

---

### Phase 3: Database Foundation ✅ COMPLETE

- PostgreSQL 15 via Docker
- SQLAlchemy models: `Digest`, `Email` (shared `db/` package)
- Raw email body storage for future re-processing
- Upsert logic: one digest per date+type

---

### Phase 4: Third Party Integration 🔜 NEXT

**Goal**: Expand content sources beyond newsletters.

---

#### Phase 4a: Product Hunt Integration 🔜 FIRST

**Goal**: Add automated AI tool discovery from Product Hunt.

**Frequency**: Once daily (fetch yesterday's top 20-50 AI products).

**Why**: Catch trending AI tools for "Top Tools" content and product inspiration.

**Implementation Plan:**
```python
# backend/sources/product_hunt.py
# GraphQL API - 500 requests/day (Free)
def fetch_daily_launches() -> list[dict]:
    # Query posts tagged 'artificial-intelligence' ranked by votes
```

---

#### Phase 4b: Hacker News Integration 🔜 SECOND

**Goal**: Technical deep dives and developer sentiment.

**Frequency**: Daily (filtered for high-signal stories).

**Why**: HN is where developers discuss model releases (GPT-5, Claude) honestly.

**Filter Strategy**:
- Min score: 100+ (community consensus)
- Keywords: AI, LLM, GPT, Agents, Automation

---

#### Phase 4c: Video Platform Trending (YouTube & TikTok) 🔜 THIRD

**Goal**: Discover viral topics programmatically from video platforms.

**Frequency**: Daily.

**Why**: Identify what's actually getting views vs just what's being written about.

**Capabilities:**
- **YouTube**: YouTube Data API v3 (`mostPopular`, `videoCategoryId=28` for Science & Tech)
- **TikTok**: TikTok Research API or 3rd-party for trending hashtags

---

### Phase 4.5: Vector Embeddings 📅 AFTER DATA SOURCES

**Goal**: Enable semantic search across all stored content.

**Implementation:**
- Switch to `pgvector/pgvector:pg15` Docker image
- Add vector columns to unified `content_items` table
- Implement monthly embedding cost control (~$0.01/mo)

---

### Phase 4.6: Google Trends Validation 📅 FINAL DATA STEP

**Goal**: Validate topics from all sources against public search interest.

**Strategy**: Validation layer, not discovery. Prioritize topics for content.

---

### Phase 5: Dashboard MVP ✅ COMPLETE

- Next.js 14 with App Router
- Tailwind CSS with glassmorphism design
- Daily/Weekly toggle with tabs
- **Run Now** button with live status polling
- Edge case handling: "No emails to process" feedback

---

### Phase 6: Multi-Agent Architecture 📅 Q1 2026

**Goal**: Evolve from single graph to specialized agent collaboration (Curator, Analyst, Creator).

---

### Phase 7: Feedback Loop 📅 Q2 2026

**Goal**: Track platform engagement (LinkedIn, TikTok, YT) to improve content suggestions.

---

### Phase 8: ChatGPT App Integration 📅 Q1 2026

**Goal**: Publish EmailAgent as a ChatGPT App with multi-source foundation.

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Agent Framework | LangGraph |
| LLM | GPT-5-nano (extraction), GPT-5-mini (generation) |
| Database | PostgreSQL 15 + pgvector (planned) |
| API | FastAPI |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| Product Hunt before HN | More actionable for content; easier API | Dec 2025 |
| Code quality phase added | Security fixes, model consolidation, UX improvements | Dec 2025 |
| Digest upsert logic | Avoid duplicates when testing same day | Dec 2025 |
| Run Now with status polling | Better UX than timeout-based approach | Dec 2025 |
| Skip Reddit | Too noisy; HN + PH provide higher signal | Dec 2025 |

---

*Last Updated: December 31, 2025*
