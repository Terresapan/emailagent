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
| **Phase 1** | Daily newsletter digest | ✅ Complete |
| **Phase 2** | Weekly deep insights digest | ✅ Complete |
| **Phase 3** | PostgreSQL database (local Docker) | ✅ Complete |
| **Phase 4a** | Product Hunt Integration | ✅ Complete |
| **Phase 4b** | Hacker News Integration | ✅ Complete |
| **Phase 4c** | YouTube Integration | ✅ Complete |
| **Phase 5** | Next.js dashboard MVP | ✅ Complete |
| **Phase 5.5** | Code quality improvements | ✅ Complete |

### What's Working Now:
- **Daily Digest**: `python main.py --type dailydigest`
- **Weekly Deep Dive**: `python main.py --type weeklydeepdives`
- **Product Hunt**: `python main.py --type productlaunch` (daily/weekly)
- **Hacker News**: `python main.py --type hackernews` (daily/weekly)
- **YouTube**: `python main.py --type youtube` (daily/weekly)
- **Database**: PostgreSQL with raw email storage + digest upsert
- **Dashboard**: 4-tab layout (Intelligence, Product Hunt, HackerNews, Strategy)
- **Run Button**: Context-aware – shows which process is running across all tabs
- **API**: FastAPI with `/api/digest/latest`, `/api/producthunt/latest`, `/api/hackernews/latest`, `/api/process`
- **Docker Stack**: 4 services (emailagent, api, dashboard, db)

### Recent Improvements:
- ✅ Hacker News integration with Developer Zeitgeist analysis
- ✅ Product Hunt integration (daily + weekly)
- ✅ 4-tab dashboard layout (Intelligence, Product Hunt, HackerNews, Strategy)
- ✅ Context-aware Run button (shows which process is running)
- ✅ Email delivery for all digest types
- ✅ Removed hardcoded email fallback (security)
- ✅ Consolidated database models into shared `db/` package
- ✅ Digest upsert: one per date+type (no duplicates)

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

### Phase 1-2: Core Digests ✅ COMPLETE

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

#### Phase 4a: Product Hunt Integration ✅ COMPLETE

**Goal**: Automated AI tool discovery from Product Hunt.

**Features:**
- Daily: Fetches top 20 AI launches from last 24 hours
- Weekly: Fetches top launches from last 7 days with trend analysis
- LLM-generated content angles
- Email delivery of digests
- Dashboard card with launches and trend summary

---

#### Phase 4b: Hacker News Integration ✅ COMPLETE

**Goal**: Technical deep dives and developer sentiment.

**Features:**
- Fetches top 25 stories from HN Firebase API
- LLM analysis generates "Developer Zeitgeist" summary
- Top themes extraction
- **Sentiment Analysis ("The Sentinel")**: Analyzing top comments for community verdict
- Email delivery of insights
- Dashboard card with stories, scores, verdicts

---

#### Phase 4c: Video Platform Trending (YouTube & TikTok) 🔜 THIRD

**Goal**: Discover viral topics programmatically from video platforms.

**Frequency**: Daily.

**Why**: Identify what's actually getting views vs just what's being written about.

**Capabilities:**
- **YouTube**: YouTube Data API v3 (`mostPopular`, `videoCategoryId=28` for Science & Tech)
- **TikTok**: TikTok Research API or 3rd-party for trending hashtags

---

#### Phase 4d: The Weekly Rewind (Weekly Aggregation) ✅ COMPLETE

**Goal**: Create a strategic weekly rollup from daily data.

**Features:**
- **Hacker News**: Aggregates last 7 days of DB insights. Deduplicates stories. LLM synthesized "Meta-Themes".
- **Product Hunt**: Standard API query for "Last 7 Days" (better for accumulating votes).
- **Automation**: 
  - True 7-Day Coverage enabled (Mon-Sat Cron + Sun Concurrent Fetch).
  - "Weekly HN Rewind" ensures full context with persisted comments.

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
| Hacker News integration | Developer trends + sentiment analysis | Dec 2025 |
| Context-aware Run button | Shows which process is running across tabs | Dec 2025 |
| 4-tab dashboard layout | Separate tabs for each content source | Dec 2025 |
| Product Hunt before HN | More actionable for content; easier API | Dec 2025 |
| Code quality phase added | Security fixes, model consolidation, UX improvements | Dec 2025 |
| Digest upsert logic | Avoid duplicates when testing same day | Dec 2025 |
| Run Now with status polling | Better UX than timeout-based approach | Dec 2025 |
| Skip Reddit | Too noisy; HN + PH provide higher signal | Dec 2025 |

---

*Last Updated: December 31, 2025*
