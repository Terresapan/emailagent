# Trend Discovery Roadmap

> **Goal**: Build a high-volume content discovery system using Google Trends  
> **Budget**: 400 calls/month (2 API keys × 250 free tier)  
> **Output**: 100+ content ideas/month supporting 5-10 videos/week

---

## Overview

Transform the current validation-only approach (8-17% success rate) into a unified discovery + validation system (70%+ success rate) that scales content production.

### Key Metrics
| Metric | Current | Target |
|--------|---------|--------|
| Success rate | 8-17% | 70%+ |
| Videos/week | 1-2 | 5-10 |
| API utilization | 26% | 80% |
| Content ideas/month | 4-8 | 100+ |

---

## Phase 1: Foundation (Week 1)

### 1.1 Dual API Key Rotation
**File**: `backend/config/serpapi_manager.py`

```python
class SerpAPIKeyManager:
    """Rotate between multiple SerpAPI keys automatically."""
    
    def get_available_key(self) -> str:
        """Get key with most remaining quota."""
        
    def increment_usage(self, key: str):
        """Track usage per key, reset monthly."""
        
    def get_stats(self) -> dict:
        """Return usage stats for dashboard."""
```

### 1.2 Partial Seeds Configuration
**File**: `config/partial_seeds.json`

```json
{
  "all_seeds": [
    "AI for", "ChatGPT for", "automate", "best AI", "how to use",
    "AI chatbot", "AI assistant", "automation tool", "AI software",
    "LinkedIn", "Instagram", "social media AI",
    "AI for beginners", "learn AI", "AI explained", "what is AI",
    "AI tutorial", "free AI", "AI tools", "AI help"
  ],
  "week_rotation": {
    "week_1": [0, 1, 2, 3, 4],
    "week_2": [5, 6, 7, 8],
    "week_3": [9, 10, 11],
    "week_4": [12, 13, 14, 15, 16]
  }
}
```

### 1.3 Historical Mining
**File**: `scripts/discover_historical.py`

Query database for past winners to reduce API usage.

### 1.4 pytrends Integration
**File**: `backend/sources/pytrends_client.py`

Use free `suggestions()` API for keyword expansion.

---

## Phase 2: Discovery Workflow (Week 2)

### 2.1 Three Candidate Sources

| Source | Cost | Purpose | Output |
|--------|------|---------|--------|
| Historical mining | 0 calls | Proven winners | 5-10 keywords |
| pytrends expansion | 0 calls | New discovery | 30-50 keywords |
| Trending check | 1 call | Timely content | 0-10 AI topics |

### 2.2 Weekly Seed Rotation
Use 3-5 seeds per week from pool of 20, rotating monthly.

### 2.3 AI Post-Filter for Trending
Filter Tech category (13) for AI-related terms only:
```python
ai_keywords = ["ai", "chatgpt", "gpt", "claude", "gemini", "llm", 
               "automation", "openai", "anthropic", "copilot"]
```

### 2.4 Weekly Schedule (100 calls/week)

| Day | Workflow | Calls |
|-----|----------|-------|
| Monday | Deep discovery | 23 |
| Tue-Fri | Daily micro (×4) | 28 |
| Saturday | Content series | 30 |
| Sunday | Historical re-validation | 17 |

---

## Phase 3: Validation Integration (Week 3)

### 3.1 RELATED_QUERIES Support
**File**: `backend/sources/google_trends.py`

```python
def get_related_queries(self, keyword: str) -> dict:
    """Fetch rising/top queries from SerpAPI."""
    params = {
        "engine": "google_trends",
        "q": keyword,
        "data_type": "RELATED_QUERIES",
    }
```

### 3.2 Database Schema
```sql
-- Store discovered related queries
CREATE TABLE related_queries (
    id SERIAL PRIMARY KEY,
    seed_keyword VARCHAR(255),
    related_keyword VARCHAR(255),
    query_type VARCHAR(20),  -- 'rising' or 'top'
    growth_percentage INTEGER,
    discovered_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(seed_keyword, related_keyword)
);

-- Track discovery performance
CREATE TABLE discovery_metrics (
    week_of DATE PRIMARY KEY,
    candidates_discovered INTEGER,
    candidates_validated INTEGER,
    scored_over_60 INTEGER,
    api_calls_used INTEGER
);
```

### 3.3 Content Gap Analysis
Combine Google Trends interest score with YouTube video count:
- High interest (>70) + Low videos (<100) = HIGH opportunity
- Medium interest (>60) + Medium videos (<300) = MEDIUM
- Otherwise = LOW or SKIP

---

## Phase 4: Automation (Week 4)

### 4.1 LangGraph Workflow
**File**: `backend/processor/discovery/graph.py`

```python
class WeeklyDiscoveryGraph:
    """Orchestrate full discovery workflow."""
    
    # Nodes:
    # mine_historical → expand_seeds → rank_candidates →
    # validate_top → discover_related → check_trending →
    # analyze_gaps → generate_digest
```

### 4.2 Cron Jobs
```bash
# Daily micro-discovery (Mon-Fri 8am)
0 8 * * 1-5 python scripts/daily_discovery.py

# Weekly deep discovery (Monday 8am)  
0 8 * * 1 python scripts/weekly_discovery.py
```

### 4.3 Email Digest
Weekly email with:
- Top 5 content opportunities
- Rising queries discovered
- Content gap analysis
- API usage stats

### 4.4 Dashboard Widget
API stats display showing:
- Per-key usage (Key 1, Key 2)
- Total remaining quota
- Monthly utilization percentage

---

## Budget Summary

### Monthly Allocation (400 calls total)
| Activity | Weekly | Monthly |
|----------|--------|---------|
| Trending check | 1 | 4 |
| Daily validation (5×5 days) | 25 | 100 |
| Monday discovery (15) | 15 | 60 |
| Related queries (7×4) | 28 | 112 |
| Saturday series (15) | 15 | 60 |
| Sunday historical (10) | 10 | 40 |
| **Total** | **94** | **376 (94%)** |

### Expected Output
- 60-80 validated keywords/month
- 150-200 related queries discovered
- 25-30 content ideas/week
- 100-120 content ideas/month

---

## Files to Create/Modify

### New Files
- `backend/config/serpapi_manager.py` - API key rotation
- `backend/sources/pytrends_client.py` - pytrends integration
- `backend/processor/discovery/graph.py` - LangGraph workflow
- `config/partial_seeds.json` - Seed configuration
- `scripts/daily_discovery.py` - Daily workflow
- `scripts/weekly_discovery.py` - Weekly workflow

### Modified Files
- `backend/sources/google_trends.py` - Add RELATED_QUERIES
- `backend/db/__init__.py` - Add new tables
- `dashboard/src/components/` - API stats widget

---

## Success Criteria

### Week 1 Milestone
- [ ] 2 API keys configured and rotating
- [ ] Historical mining returns 10+ keywords
- [ ] pytrends returns 50+ suggestions

### Week 2 Milestone
- [ ] Daily workflow runs successfully
- [ ] Trending filter returns AI-only topics
- [ ] Seed rotation working

### Week 3 Milestone
- [ ] RELATED_QUERIES integrated
- [ ] Content gap scoring works
- [ ] 70%+ validation success rate

### Week 4 Milestone
- [ ] Automated Monday digest sent
- [ ] Dashboard shows API stats
- [ ] 100 calls/week sustained

---

*Last Updated: January 2026*
