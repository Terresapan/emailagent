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

## Current Progress (December 2024)

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

### Phase 2: Google Sheets Staging ⏭️ SKIPPED

**Decision**: Went straight to PostgreSQL database. Google Sheets may be added later for human-readable exports.

---

### Phase 3: Database Foundation ✅ COMPLETE

**Implemented:**
- PostgreSQL 15 via Docker
- SQLAlchemy models: `Digest`, `Email`
- Raw email body storage for future re-processing
- FastAPI endpoints for dashboard

**Schema:**
```sql
CREATE TABLE digests (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    digest_type VARCHAR(20),  -- 'daily' or 'weekly'
    briefing TEXT,
    linkedin_content TEXT,
    newsletter_summaries TEXT,
    emails_processed JSON,
    created_at TIMESTAMP
);

CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    gmail_id VARCHAR(255) UNIQUE,
    sender VARCHAR(255),
    subject TEXT,
    body TEXT,  -- Raw content stored!
    digest_id INTEGER REFERENCES digests(id),
    processed_at TIMESTAMP
);
```

---

### Phase 4: Product Hunt Integration 🔜 NEXT

**Goal**: Add automated AI tool discovery from Product Hunt.

**Why (a16z)**: Multi-source workflow. Newsletters are curated but delayed; Product Hunt provides real-time tool launches.

**Implementation Plan:**
```python
# backend/sources/product_hunt.py
def fetch_daily_launches() -> list[dict]:
    query = """
    query {
      posts(first: 20, topic: "artificial-intelligence") {
        edges {
          node {
            name, tagline, description, votesCount, createdAt
            topics { name }
          }
        }
      }
    }
    """
```

**Database Addition:**
```sql
CREATE TABLE product_hunt_items (
    id SERIAL PRIMARY KEY,
    ph_id VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    tagline TEXT,
    description TEXT,
    votes_count INTEGER,
    topics TEXT[],
    launched_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

---

### Phase 4.5: Vector Embeddings 📅 AFTER STABILITY

**Goal**: Enable semantic search across all stored content.

**When**: After 2-3 weeks of stable daily/weekly digest runs.

**Implementation:**
1. Switch Docker image: `postgres:15` → `pgvector/pgvector:pg15`
2. Add embedding column: `ALTER TABLE emails ADD COLUMN embedding vector(1536)`
3. Embed on save: Generate embedding when storing new content
4. Backfill: Embed all historical content in one batch

**Cost**: ~$0.10/year at current usage (essentially free)

---

### Phase 5: Dashboard MVP ✅ COMPLETE

**Implemented:**
- Next.js 14 with App Router
- Tailwind CSS with glassmorphism design
- Daily/Weekly toggle with tabs
- `BriefingCard`, `LinkedInCard`, `DeepDiveCard` components
- Real-time polling for new content notifications
- Responsive mobile layout

**Dashboard Views (Current):**
| View | Status |
|------|--------|
| Daily Briefing + LinkedIn | ✅ |
| Weekly Deep Dive | ✅ |
| Processed emails list | ✅ |
| New content notifications | ✅ |

**Dashboard Views (Future):**
| View | Phase |
|------|-------|
| Semantic search | Phase 4.5 |
| Product Hunt feed | Phase 4 |
| Action Queue (approve/reject) | Phase 6 |
| Performance tracking | Phase 7 |

---

### Phase 6: Multi-Agent Architecture 📅 Q1 2025

**Goal**: Evolve from single graph to specialized agent collaboration.

```
┌──────────────────────────────────────────────────────┐
│                 AGENT ORCHESTRATOR                   │
└──────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   CURATOR AGENT     ANALYST AGENT    CREATOR AGENT
   (Ingest/Extract)  (Trend/Score)    (Draft/Generate)
```

**Future Protocol**: Consider A2A (Google's Agent-to-Agent Protocol) for external interoperability.

---

### Phase 7: Feedback Loop 📅 Q2 2025

**Goal**: Close the loop between published content and future suggestions.

```
[Publish Content] → [Track Engagement] → [Learn What Works] → [Improve Suggestions]
```

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|------------|
| Agent Framework | LangGraph |
| LLM (Extraction) | OpenAI o4-mini (low reasoning) |
| LLM (Generation) | OpenAI o4-mini (medium reasoning) |
| Database | PostgreSQL 15 (Docker) |
| Vector Search | pgvector (planned) |
| API | FastAPI |
| Observability | LangSmith |

### Frontend
| Component | Technology |
|-----------|------------|
| Framework | Next.js 14 (App Router) |
| Styling | Tailwind CSS |
| State | React hooks + fetch |
| Deployment | Docker (local) |

### Infrastructure
| Component | Technology |
|-----------|------------|
| Orchestration | Docker Compose |
| Scheduling | cron (macOS launchd) |
| Development | Docker Desktop |

---

## Cost Estimation (Monthly)

| Service | Cost |
|---------|------|
| OpenAI LLM (GPT-4o-mini) | ~$0.25 |
| OpenAI Embeddings (future) | ~$0.01 |
| PostgreSQL | Free (Docker local) |
| Product Hunt API | Free |
| **Total** | **~$0.30/month** |

---

## Inspirational Goal: Content Intelligence API

Once stable, this system can be productized:

```
GET /trending-topics        → Curated, validated topics with trend scores
GET /content-opportunities  → Draft content with confidence scores
POST /feedback              → Client reports what performed
GET /search?q=AI+agents     → Semantic search across knowledge base
```

**This is the "rebundling" opportunity** per a16z: become the data layer for other content tools.

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| PostgreSQL over MongoDB | Simpler, SQL familiarity, pgvector compatible | Dec 2024 |
| Skip Google Sheets | Went straight to database | Dec 2024 |
| Skip X/Twitter | $100/month API; newsletters have same signal | Dec 2024 |
| Local Docker over Supabase | Personal use, keep data local | Dec 2024 |
| pgvector over Chroma/Qdrant | Already have PostgreSQL, one less service | Dec 2024 |
| Embeddings after stability | Finalize schema first, batch backfill later | Dec 2024 |

---

## Next Steps (Priority Order)

1. **Stabilize digests** – Run daily/weekly for 1-2 weeks, fix edge cases
2. **Product Hunt integration** – Add tool discovery data source
3. **pgvector + embeddings** – Enable semantic search (Week 4+)
4. **Google Trends validation** – Add trend scoring to topics

---

*Last Updated: December 21, 2024*
