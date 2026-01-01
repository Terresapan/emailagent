# Email Digest Agent

AI-powered email digest system that processes newsletters and generates briefings + LinkedIn content.

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

### 5. Parallel Execution

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
| `--type` | `all` | Run all DAILY processors in parallel |
| `--type` | `all_weekly` | Run all WEEKLY processors (and Sunday Daily) in parallel |
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

## Cron Schedule

| Type | Schedule | Time |
|------|----------|------|
| Daily Digest | Mon-Fri | 8:00 AM PST |
| Weekly Deep Dive | Sunday | 8:00 AM PST |

To modify, edit `backend/scripts/crontab` and rebuild:

```bash
docker-compose up -d --build emailagent
```

### Mac Wake Schedule

To wake your Mac for scheduled processing:

```bash
# Install wake schedule -- every day at 7:58 AM
sudo pmset repeat wakeorpoweron MTWRFSU 07:58:00

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
