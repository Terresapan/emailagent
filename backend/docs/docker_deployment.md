# Docker Deployment Guide

This guide covers deploying the Email Digest Agent in a Docker container for automated execution.

## Prerequisites

- Docker Desktop installed and running
- Gmail API credentials configured (`credentials.json`)
- OpenAI API key
- `.env` file configured

## Setup

### 1. Configure Environment

Ensure your `.env` file is properly configured:

```bash
OPENAI_API_KEY=your_openai_api_key_here
CREDENTIALS_PATH=./credentials.json
TOKEN_PATH=./token.json
SENDER_WHITELIST_PATH=./config/sender_whitelist.json
LOG_LEVEL=INFO
```

### 2. Initial Authentication

Before running in Docker, you need to authenticate once locally to generate `token.json`:

```bash
uv run main.py --dry-run
```

This will open a browser for OAuth authentication. After successful authentication, `token.json` will be created.

### 3. Build Docker Image

```bash
docker-compose build
```

This will:
- Create a Python 3.12 container
- Install uv package manager
- Install all dependencies
- Set up cron for 7:00 AM execution

### 4. Start the Container

```bash
docker-compose up -d
```

The container will:
- Start in detached mode
- Run continuously
- Execute the agent at 7:00 AM PST every day
- Persist logs to the `./logs` directory

## Monitoring

### View Logs

```bash
# View all logs
docker-compose logs -f

# View cron execution logs
tail -f logs/cron.log
```

### Check Container Status

```bash
docker-compose ps
```

### Verify Cron Schedule

```bash
docker-compose exec emailagent crontab -l
```

### Manual Execution

To manually trigger the agent inside the container:

```bash
# Dry run
docker-compose exec emailagent uv run main.py --dry-run

# Full run
docker-compose exec emailagent uv run main.py
```

## Timezone Configuration

The container is configured for Pacific Time (America/Los_Angeles). To change:

1. Edit `docker-compose.yml`
2. Update the `TZ` environment variable:
   ```yaml
   environment:
     - TZ=Your/Timezone  # e.g., America/New_York
   ```
3. Rebuild and restart:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## Wake macOS at 7:00 AM

To have your macOS wake up at 6:58 AM from Monday to Friday for notifications:

### Option 1: Using pmset (Requires sudo)

```bash
sudo pmset repeat wake MTWRF 06:58:00
```

This schedules macOS to wake every day at 6:58 AM.

### Option 2: System Preferences

1. Open System Preferences > Battery (or Energy Saver)
2. Click "Schedule"
3. Check "Start up or wake" and set to 6:58 AM from Monday to Friday

## Updating the Agent

If you make changes to the code:

```bash
# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

## Troubleshooting

### Container Exits Immediately

Check logs:
```bash
docker-compose logs
```

Ensure all required files exist:
- `.env`
- `credentials.json`
- `token.json`

### Cron Not Running

Verify cron is active:
```bash
docker-compose exec emailagent ps aux | grep cron
```

Check cron logs:
```bash
docker-compose exec emailagent cat /var/log/emailagent/cron.log
```

### Token Expired

If authentication expires:
1. Stop container: `docker-compose down`
2. Delete `token.json`
3. Re-authenticate locally: `uv run main.py --dry-run`
4. Restart container: `docker-compose up -d`

### Logs Directory Permission Issues

Ensure the logs directory exists and is writable:
```bash
mkdir -p logs
chmod 755 logs
```

## Stopping the Agent

```bash
# Stop the container
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Best Practices

1. **Keep credentials secure**: Never commit `credentials.json` or `token.json`
2. **Monitor logs regularly**: Check `logs/cron.log` for execution status
3. **Test changes locally first**: Use `--dry-run` before deploying
4. **Back up token.json**: Keep a backup of your authenticated token
5. **Update sender whitelist as needed**: Edit `config/sender_whitelist.json` and rebuild
