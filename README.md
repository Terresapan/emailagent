# Email Digest Agent

**AI content intelligence platform that synthesizes newsletters, Product Hunt launches, Hacker News discussions, and YouTube videos into actionable briefings with Google Trends validation.**

> Transforms fragmented information sources into strategic content opportunities for creators through automated multi-source curation and trend analysis.

## Architecture

```
emailagent/
├── backend/           # Python backend (LangGraph email processor)
│   ├── api/           # FastAPI service for dashboard
│   ├── main.py        # Email processing logic
│   └── utils/         # Database, logging utilities
├── dashboard/         # Next.js frontend
└── docker-compose.yml # Orchestrates all services
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| `emailagent` | - | Cron-based email processor (runs at 8am) |
| `api` | 8000 | FastAPI backend for dashboard |
| `dashboard` | 3000 | Next.js frontend |
| `db` | 5432 | PostgreSQL database |

---

## Quick Start

```bash
# Start all services
docker-compose up -d

# Open dashboard
open http://localhost:3000
```

---

## Common Docker Commands

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a specific service
docker restart contentagent-dashboard
```

### View Logs

```bash
# View emailagent logs (last 12 hours)
docker logs emailagent --since 12h

# Follow logs in real-time
docker logs -f emailagent

# Check for database save status
docker logs emailagent | grep -i "database\|saving"
```

### Rebuild After Code Changes

```bash
# Rebuild emailagent (backend Python code)
docker-compose up -d --build emailagent

# Rebuild dashboard (frontend)
docker-compose up -d --build dashboard

# Rebuild API
docker-compose up -d --build api

# Rebuild everything
docker-compose up -d --build
```

### Manual Email Processing

```bash
# Daily digest (default) - newsletters → briefing + LinkedIn
docker exec emailagent uv run python main.py --type dailydigest

# Weekly deep dive - expert essays → strategic briefing (no LinkedIn)
docker exec emailagent uv run python main.py --type weeklydeepdives

# Dry run (preview without sending/archiving)
docker exec emailagent uv run python main.py --dry-run
docker exec emailagent uv run python main.py --type weeklydeepdives --dry-run
```

### 3. Product Hunt AI Analysis
Fetches the top AI product launches from Product Hunt (Daily or Weekly).

**Daily Run (Default):**
```bash
# Fetches top products from the last 24 hours
docker exec emailagent uv run python main.py --type productlaunch
```

**Weekly Run:**
```bash
# Fetches top products from the last 7 days + Weekly Trend Analysis
docker exec emailagent uv run python main.py --type productlaunch --timeframe weekly
```

### 4. Hacker News Analysis (Developer Trends)
Fetches top trending stories and analyzes developer culture/sentiment.

```bash
# Daily Analysis
docker exec emailagent uv run python main.py --type hackernews

# Weekly Analysis (uses different prompt context)
docker exec emailagent uv run python main.py --type hackernews --timeframe weekly
```

### 5. YouTube Influencer Analysis (NEW)
Fetches recent videos from curated influencer channels, extracts transcripts, and summarizes content.

```bash
# Daily Analysis (checks for new videos from configured channels)
docker exec emailagent uv run python main.py --type youtube

# Dry run (preview without saving to DB or sending email)
docker exec emailagent uv run python main.py --type youtube --dry-run
```

> **Setup Required**: Edit `backend/config/youtube_channels.json` with your influencer channel IDs before running.

### 6. Saturday Discovery (Viral App Ideas)
Finds viral app opportunities by mining pain points from Reddit, Twitter, YouTube comments, and Product Hunt reviews.

**Run via CLI:**
```bash
# Full discovery workflow (takes 5-10 minutes)
docker exec emailagent uv run python main.py --type discovery

# Dry run (no email sent)
docker exec emailagent uv run python main.py --type discovery --dry-run
```

**Run via API:**
```bash
# Trigger discovery and get results
curl -X POST http://localhost:8000/api/discovery/run

# Get latest briefing (from previous run)
curl http://localhost:8000/api/discovery/briefing

# Check API usage stats
curl http://localhost:8000/api/discovery/stats
```

> **Scheduled**: Runs automatically every Saturday at 8:20 AM (see `backend/scripts/crontab`)

### 7. Parallel Execution

**Parallel Daily Run:**
Runs generic email digest AND daily Product Hunt analysis in parallel.
```bash
docker exec emailagent uv run python main.py --type all
```

**Parallel Weekly Run:**
Runs weekly deep dive analysis AND weekly Product Hunt analysis in parallel.
```bash
docker exec emailagent uv run python main.py --type all_weekly
```

### CLI Options

| Option | Values | Description |
|--------|--------|-------------|
| `--type` | `dailydigest` (default) | Newsletter briefing + LinkedIn content |
| `--type` | `weeklydeepdives` | Expert essays → strategic briefing |
| `--type` | `productlaunch` | Product Hunt AI tools discovery |
| `--type` | `hackernews` | Hacker News developer trends analysis |
| `--type` | `youtube` | YouTube influencer video summaries |
| `--type` | `all` | Run all DAILY processors in parallel |
| `--type` | `all_weekly` | Run all WEEKLY processors in parallel |
| `--timeframe` | `daily` / `weekly` | Timeframe for Product Hunt and HackerNews |
| `--dry-run` | - | Preview output without modifying emails or sending |

### Database Commands

```bash
# View all digests (with type)
docker exec contentagent-db psql -U postgres -d contentagent \
  -c "SELECT id, date, digest_type, created_at FROM digests ORDER BY created_at DESC;"

# View email count
docker exec contentagent-db psql -U postgres -d contentagent \
  -c "SELECT COUNT(*) FROM emails;"

# Delete all data (reset)
docker exec contentagent-db psql -U postgres -d contentagent \
  -c "TRUNCATE digests, emails RESTART IDENTITY CASCADE;"

# Interactive PostgreSQL shell
docker exec -it contentagent-db psql -U postgres -d contentagent
```

### API Health Check

```bash
# Check API health
curl http://localhost:8000/api/health

# Get latest daily digest
curl http://localhost:8000/api/digest/latest

# Get latest weekly deep dive
curl "http://localhost:8000/api/digest/latest?digest_type=weekly"

# Get digest history by type
curl "http://localhost:8000/api/digest/history?digest_type=daily"
curl "http://localhost:8000/api/digest/history?digest_type=weekly"
```

### Troubleshooting

```bash
# Check if all containers are running
docker ps

# Check container resource usage
docker stats

# View container environment variables
docker exec emailagent env | grep DATABASE

# Check cron schedule
docker exec emailagent cat /etc/cron.d/emailagent-cron
```

---

## Scheduling & Data Behavior

### Cron Schedule

| Day | Job Type | Time | What Runs |
|-----|----------|------|-----------|
| Mon-Fri | `all` | 8:20 AM PST | Daily Newsletter + PH + HN + YouTube + Trend Analysis |
| Saturday | Skip | - | No processing (use `force=true` to override) |
| Sunday | `all_weekly` | 8:20 AM PST | Weekly Deep Dive + PH + HN + YouTube (daily + weekly) |

### Sunday Processing Flow

On Sunday, the system captures both daily AND weekly data:

```
1. Weekly Newsletter Deep Dive → Sent via email
2. Daily PH/HN/YouTube → Capture Sunday's fresh data
3. Weekly PH/HN/YouTube → Aggregate + analyze 7-day trends
4. Google Trends Validation → Run on weekly sources
```

**Why both daily and weekly on Sunday?**
- Daily captures Sunday's fresh data for the database
- Weekly aggregates the full week (including Sunday) for trend analysis

### Dashboard Auto-Detection

The dashboard automatically shows the appropriate data based on the day:

| Day | Dashboard Shows | API Parameter |
|-----|-----------------|---------------|
| Mon-Sat | Daily data | `?period=daily` |
| Sunday | Weekly data | `?period=weekly` |

### Database Behavior (UPSERT)

Each data source uses UPSERT logic with unique key: `(date, period)`

| Scenario | Result |
|----------|--------|
| Run Product Hunt daily on Monday | Creates row `(2026-01-06, daily)` |
| Run Product Hunt daily again on Monday | **Updates** existing row (replaces content) |
| Run Product Hunt weekly on Sunday | Creates row `(2026-01-11, weekly)` |
| Run Product Hunt daily on Sunday | Creates row `(2026-01-11, daily)` ← separate from weekly! |

**This means:**
- ✅ Running the same job twice on the same day **updates** (no duplicates)
- ✅ Daily and Weekly are **stored separately** in the database
- ✅ Sunday has **both** daily and weekly rows

### Dashboard Run Buttons

| Button | What It Does | Timeframe |
|--------|--------------|-----------|
| Run Newsletter | Process daily newsletters | daily |
| Run Product Hunt | Fetch today's PH launches | daily |
| Run HackerNews | Fetch today's top stories | daily |
| Run YouTube | Fetch today's influencer videos | daily |
| Run Strategy | Process weekly deep dive essays | weekly |

**Note:** Run buttons always execute with `timeframe=daily` (except Strategy). After clicking, the dashboard refreshes and displays data based on day of week (weekly on Sunday, daily otherwise).

### How Weekly Aggregation Works

| Source | Daily Mode | Weekly Mode |
|--------|------------|-------------|
| **Product Hunt** | API call (last 24h) | API call (last 7 days) |
| **Hacker News** | API call (current top stories) | Database aggregation (HN API doesn't support historical) |
| **YouTube** | API call (videos from last 24h) | API call (videos from last 7 days) ← Fresh view counts! |

### Google Trends Validation

The "Run Global Analysis" button on the Analysis page:

| Day | Sources Used | Output |
|-----|--------------|--------|
| Mon-Fri | Latest daily Newsletter + PH + HN + YouTube | Daily trend validation |
| Saturday | Skipped (unless `force=true`) | - |
| Sunday | Latest weekly Newsletter + PH + YouTube | Weekly trend validation |

To modify, edit `backend/scripts/crontab` and rebuild:

```bash
docker-compose up -d --build emailagent
```

### Mac Wake Schedule

To wake your Mac for scheduled processing:

```bash
# Install wake schedule -- every day at 8:00 AM
sudo pmset repeat wakeorpoweron MTWRFSU 08:00:00

# Verify schedule
pmset -g sched

# Cancel schedule
sudo pmset repeat cancel
```

---

## Development (Hot Reload)

The dashboard has hot-reload enabled. After `docker-compose up -d`, edit files in `dashboard/src/` and changes appear automatically.

For backend Python changes, you need to rebuild:
```bash
docker-compose up -d --build emailagent
```
