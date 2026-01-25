# Viral Mini-App Discovery Roadmap

> **Branch**: `feature/viral-app-trends`  
> **Last Updated**: 2026-01-25

---

## Saturday Budget (Per Run)

| API | Calls | Notes |
|-----|-------|-------|
| Arcade.dev | ~136 | Reddit (80) + Twitter (56) |
| SerpAPI | ~38 | Google search for validation |
| YouTube | 15 | 5 searches + 10 comment fetches |
| LLM | 7 | 6 extraction + 1 embedding |
| **Est. Cost** | ~$0.15 | LLM + SerpAPI |

---

## Scoring Policy

### Engagement Score (0-100)

Default Source-specific thresholds for max score:

| Source | Threshold | Example |
|--------|-----------|---------|
| YouTube | 50 comment likes | 50+ → 100 |
| Reddit | 100 upvotes | 100+ → 100 |
| ProductHunt | 200 votes | 200+ → 100 |
| Twitter | 100 likes | 100+ → 100 |

Formula: `min(engagement / threshold, 1.0) × 100`

Multi-source bonus: +10 per additional source

### Validation Score (0-50)

Google Search for competing products:
- 0 results → 0 points
- 1-4 results → 10 points each
- 5+ results → 50 points (capped)

### Opportunity Score

```
opportunity = engagement × 0.5 + validation × 0.3 + buildability × 0.2
```

---

## Pipeline

```
Data:    136 Arcade + YouTube + PH → ~3,800 data points
Extract: 5 LLM calls → ~99 pain points
Cluster: Embedding similarity (0.70 threshold) → ~90 clusters
Filter:  1 LLM call → ~38 candidates
Validate: 38 SerpAPI Google searches → demand scores
Score:   1 LLM call → virality + buildability
Output:  Top 20 ranked opportunities
```

---

## Recent Developments (Jan 2026)

### Completed
- [x] **Google Search Validation** - Replaced ProductHunt topic search with SerpAPI Google search for better market validation
- [x] **Per-Source Engagement Scoring** - Fixed bug where all sources used same threshold (200)
- [x] **LLM Filter Robustness** - Added lenient parser (accepts `|`, `.`, `:`) + fallback if parsing fails
- [x] **SerpAPI Usage Tracking** - Now tracked and displayed in API Stats tab
- [x] **Source Breakdown Display** - Shows engagement per source on opportunity cards
- [x] **Similar Products Display** - Shows competing products found via Google search

### Architecture

```
backend/sources/
├── arcade_client.py       # Reddit + Twitter via Arcade.dev
├── google_trends.py       # SerpAPI: Trends + Google Search
├── youtube.py             # YouTube Data API v3
└── product_hunt.py        # GraphQL API

backend/processor/viral_app/
├── graph.py               # LangGraph workflow orchestration
├── clusterer.py           # Embedding-based semantic clustering
├── llm_filter.py          # LLM-based candidate filtering
├── pain_point_extractor.py # Extract problems from raw data
├── scorer.py              # LLM scoring for buildability/virality
└── ranker.py              # Final opportunity ranking
```

---

## Dashboard Tabs

| Tab | Purpose |
|-----|---------|
| Discovery | Top 20 opportunities with scores, sources, similar products |
| Videos | YouTube viral videos collected |
| History | Past briefings by date |
| API Stats | Arcade, SerpAPI, YouTube, LLM usage |

---

## Known Limitations

1. **Clustering** - Distinct problems don't cluster (e.g., "podcast SEO" ≠ "podcast monetization" similarity ~0.47)
2. **Multi-source validation** - Rare due to different vocabulary across platforms
3. **YouTube engagement** - Currently uses comment likes, not video likes
