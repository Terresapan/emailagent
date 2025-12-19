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
# Run email processor manually (production)
docker exec emailagent uv run python main.py

# Dry run (preview without sending emails)
docker exec emailagent uv run python main.py --dry-run
```

### Database Commands

```bash
# View all digests
docker exec contentagent-db psql -U postgres -d contentagent \
  -c "SELECT id, date, created_at FROM digests ORDER BY created_at DESC;"

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

# Get latest digest
curl http://localhost:8000/api/digest/latest
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

The email processor runs automatically at **8:00 AM (PST)** every day.

To modify the schedule, edit `backend/scripts/crontab` and rebuild:

```bash
docker-compose up -d --build emailagent
```

---

## Development (Hot Reload)

The dashboard has hot-reload enabled. After `docker-compose up -d`, edit files in `dashboard/src/` and changes appear automatically.

For backend Python changes, you need to rebuild:
```bash
docker-compose up -d --build emailagent
```
