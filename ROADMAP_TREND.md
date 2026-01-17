# Viral Mini-App Discovery Roadmap

> **Branch**: `feature/viral-app-trends`

---

## Saturday Budget

| API | Calls |
|-----|-------|
| Arcade.dev | 200 |
| SerpAPI | 120 |
| YouTube | 500 (free) |
| Product Hunt | 50 (free) |
| LLM | 7 (~$0.13) |

---

## File Structure

```
backend/sources/           ← API Clients (data fetching)
├── arcade_client.py       # NEW: Reddit + Twitter
├── google_trends.py       # EXTEND: dual SerpAPI keys
├── youtube.py             # EXTEND: comment mining
└── product_hunt.py        # EXTEND: gap analysis

backend/processor/viral_app/   ← Orchestration only
├── graph.py               # LangGraph workflow
├── pain_point_extractor.py
├── llm_filter.py
├── scorer.py
└── ranker.py
```

---

## Pipeline

```
Data: 200 Arcade + free APIs → 2,000 data points
Extract: 5 LLM calls → 100-145 pain points
Filter: 1 LLM call → 45 candidates
Validate: 120 SerpAPI → demand scores
Score: 1 LLM call → virality + buildability
Output: Top 20 ranked opportunities
```

---

## Dashboard (4 Tabs)

| Tab | Purpose |
|-----|---------|
| Discovery | Top 20 opportunities |
| Sources | Raw data |
| History | Past briefings |
| API Stats | Usage tracking |

---

## Phases

1. API Clients (extend sources/)
2. Discovery Logic (processor/viral_app/)
3. Saturday Workflow
4. Backend Endpoints
5. Frontend Dashboard
