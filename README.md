# Email Digest Agent

An automated AI newsletter digest agent that processes unread emails every morning at 7:00 AM, generates categorized summaries using GPT-5-mini, and creates a daily digest draft in Gmail.

## Features

- **Automated Email Fetching**: Retrieves unread emails from whitelisted newsletter senders
- **Intelligent Summarization**: Uses GPT-5-mini with LangGraph to categorize content into:
  - Industry News / Trends
  - New Tools
  - Insights
- **Aggregated Briefing**: Generates a high-level briefing tailored for AI agent builders in SME contexts
- **Gmail Integration**: Automatically labels emails and creates drafts
- **Robust Error Handling**: 3-retry logic with exponential backoff for all Gmail API operations
- **Docker Deployment**: Runs in Docker container with scheduled execution

## Setup

### Prerequisites

- Python 3.12
- Docker Desktop
- Gmail account with API access
- OpenAI API key

### 1. Install UV Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup

```bash
cd /Users/terresapan/Documents/LangGraph\ Agents/emailagent
uv sync
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
OPENAI_API_KEY=your_openai_api_key_here
CREDENTIALS_PATH=./credentials.json
TOKEN_PATH=./token.json
SENDER_WHITELIST_PATH=./config/sender_whitelist.json
LOG_LEVEL=INFO
```

### 4. Setup Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place `credentials.json` in the project root

See [docs/gmail_api_setup.md](docs/gmail_api_setup.md) for detailed instructions.

### 5. Update Sender Whitelist (Optional)

Edit `config/sender_whitelist.json` to add/remove newsletter senders:

```json
[
  {
    "name": "Newsletter Name",
    "email": "sender@example.com"
  }
]
```

## Usage

### Manual Execution

```bash
# Dry run (preview without modifying emails)
uv run main.py --dry-run

# Full execution
uv run main.py
```

### Docker Deployment

Build and run the Docker container:

```bash
# Build the image
docker-compose build

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Check cron schedule
docker-compose exec emailagent crontab -l
```

The agent will run automatically at 7:00 AM every day.

## Project Structure

```
emailagent/
├── config/
│   ├── settings.py           # Configuration management
│   └── sender_whitelist.json # Newsletter senders
├── gmail/
│   ├── auth.py              # OAuth authentication
│   └── client.py            # Gmail API operations
├── processor/
│   ├── models.py            # Pydantic data models
│   ├── summarizer.py        # LangGraph email processor
│   └── templates.py         # LLM prompt templates
├── utils/
│   ├── html_parser.py       # HTML to text converter
│   └── logger.py            # Logging configuration
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── main.py                  # Main orchestration script
├── pyproject.toml          # UV dependencies
├── Dockerfile              # Docker configuration
└── docker-compose.yml      # Docker Compose setup
```

## Verification

After running the agent, verify:

1. ✅ Unread newsletter emails are fetched
2. ✅ Only emails from whitelisted senders are processed
3. ✅ Email summaries are properly categorized
4. ✅ Aggregated briefing is relevant and actionable
5. ✅ Emails are marked as read
6. ✅ "Newsletters" label is created and applied
7. ✅ Draft email is created with proper formatting

## Troubleshooting

### Authentication Issues

If you encounter OAuth errors:
```bash
rm token.json
uv run main.py --dry-run
```

This will trigger a new OAuth flow.

### Missing Credentials

Ensure `credentials.json` is in the project root and properly formatted.

### API Rate Limits

The agent includes retry logic with exponential backoff. If you hit rate limits consistently, adjust `RETRY_MIN_WAIT` and `RETRY_MAX_WAIT` in `config/settings.py`.

### No Emails Found

Check that:
- Sender email addresses in `sender_whitelist.json` are correct
- You have unread emails from those senders
- Gmail API permissions are correctly set

## License

MIT
