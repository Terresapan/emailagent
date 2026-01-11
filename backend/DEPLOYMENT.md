# Deployment Guide

This document outlines deployment options, architecture decisions, and refactoring considerations for production deployment.

## Current Architecture (Local Development)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Dashboard    │────▶│       API       │────▶│   emailagent    │
│   (Next.js)     │     │   (FastAPI)     │     │   (Processor)   │
│   Port 3000     │     │   Port 8000     │     │  (Batch Job)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │                       │
         │                      │                       │
         └──────────────────────┴───────────────────────┘
                                │
                         ┌──────▼──────┐
                         │  PostgreSQL │
                         │   Port 5432 │
                         └─────────────┘
```

### How Run Buttons Work (Docker Socket)

The API uses Docker socket to trigger the processor container:

```python
import docker
client = docker.from_env()  # Uses mounted /var/run/docker.sock
container = client.containers.get("emailagent")
container.exec_run(["python", "main.py", "--type", "productlaunch"])
```

**Why this approach:**
- Processor remains a clean batch job (runs once and exits)
- No need to keep processor running 24/7
- Easy to test processor independently
- API stays lightweight

**Limitation:** Won't work on Cloud Run (no Docker socket access)

---

## Cloud Deployment Options

### Option 1: Google Cloud Run (Recommended)

| Component | Deploy As | Why |
|-----------|-----------|-----|
| `api` | Cloud Run **Service** | HTTP endpoints for dashboard |
| `emailagent` | Cloud Run **Job** | Batch processing, triggered on schedule |
| `dashboard` | Cloud Run **Service** or Vercel | Web UI |
| `database` | Cloud SQL (PostgreSQL) | Managed database |

**Cloud Run Jobs** is ideal for the processor because:
- Runs on schedule (cron) or triggered via API
- Pay only while job is running
- Max 24-hour timeout (vs 60 min for Services)
- No need to refactor processor into a web server

### Refactoring Needed for Cloud Run

1. **API → Processor communication:**
   - Replace Docker socket with Cloud Run Jobs API
   - Use `google-cloud-run` Python SDK to trigger jobs

2. **Environment variables:**
   - Move from `.env` file to Cloud Run secrets
   - Update DATABASE_URL to Cloud SQL connection

3. **Gmail authentication:**
   - Store `token.json` in Cloud Storage or Secret Manager
   - Update credential refresh logic

### Option 2: Keep Everything as Services

Convert processor to HTTP endpoints (less ideal):

```python
# Would need to add to emailagent
from fastapi import FastAPI
app = FastAPI()

@app.post("/run/productlaunch")
async def run_product_launch():
    main_product_hunt(...)
```

**Pros:** Simple HTTP communication
**Cons:** Processor runs 24/7, higher cost, less clean architecture

---

## Pricing Comparison

### Cloud Run Pricing (both Services and Jobs)

| Resource | Price | Free Tier |
|----------|-------|-----------|
| vCPU | $0.00002400/vCPU-sec | 180,000 vCPU-sec/mo |
| Memory | $0.00000250/GiB-sec | 360,000 GiB-sec/mo |
| Requests | $0.40/million | 2 million/mo |

### Estimated Costs (your workload)

| Component | Usage | Monthly Cost |
|-----------|-------|--------------|
| API | ~5 min CPU/day | ~$0.50 |
| Processor (Jobs) | ~5 min/day | ~$0.22 |
| Dashboard | ~2 min CPU/day | ~$0.20 |
| Cloud SQL (db-f1-micro) | Always on | ~$7.67 |
| **Total** | | **~$8.60/mo** |

Most processing fits within free tier.

---

## Migration Checklist

When ready to deploy to Cloud Run:

### Phase 1: Database
- [ ] Create Cloud SQL PostgreSQL instance
- [ ] Migrate schema using existing SQLAlchemy models
- [ ] Update DATABASE_URL for Cloud SQL

### Phase 2: Processor → Cloud Run Job
- [ ] Create Dockerfile for processor (or reuse existing)
- [ ] Deploy as Cloud Run Job
- [ ] Set up Cloud Scheduler for cron triggers
- [ ] Test job execution

### Phase 3: API → Cloud Run Service
- [ ] Remove Docker socket code
- [ ] Add Cloud Run Jobs API integration
- [ ] Deploy API as Cloud Run Service
- [ ] Configure secrets (Gmail token, API keys)

### Phase 4: Dashboard
- [ ] Update API_URL to Cloud Run API endpoint
- [ ] Deploy to Cloud Run or Vercel
- [ ] Configure custom domain (optional)

---

## Local Development Notes

### Docker Socket Dependency

The `docker` Python package is required for local development:
- Added to `pyproject.toml`
- Mounted via `/var/run/docker.sock` in docker-compose.yml
- **Not needed for Cloud Run deployment** (will use Cloud Run Jobs API instead)

### Volume Mounts

The docker-compose.yml uses volume mounts for hot-reloading:
- `pyproject.toml` is mounted read-only for uv to locate the venv
- Shared packages (db, sources, processor, etc.) are mounted into both containers
