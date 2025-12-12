"""Configuration settings for the email digest agent."""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"

# Environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", str(BASE_DIR / "credentials.json"))
TOKEN_PATH = os.getenv("TOKEN_PATH", str(BASE_DIR / "token.json"))
SENDER_WHITELIST_PATH = os.getenv(
    "SENDER_WHITELIST_PATH", 
    str(CONFIG_DIR / "sender_whitelist.json")
)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Gmail API settings
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.send",
]

# Label settings
NEWSLETTER_LABEL = "Newsletters"

# Email settings
DIGEST_RECIPIENT_EMAIL = os.getenv("DIGEST_RECIPIENT_EMAIL", "terresap2010@gmail.com")

# LLM settings
LLM_MODEL = "gpt-5-mini-2025-08-07"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 10000

# Retry settings
MAX_RETRIES = 3
RETRY_MIN_WAIT = 1  # seconds
RETRY_MAX_WAIT = 10  # seconds

# Scheduling
EXECUTION_TIME = "07:00"  # 7:00 AM

# LangSmith settings
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = True
LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
LANGSMITH_PROJECT = "AI Newsletter Digest"


def load_sender_whitelist():
    """Load the sender whitelist from JSON file."""
    with open(SENDER_WHITELIST_PATH, "r") as f:
        return json.load(f)


def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not set in environment variables")
    
    if not os.path.exists(CREDENTIALS_PATH):
        errors.append(f"Gmail credentials not found at {CREDENTIALS_PATH}")
    
    if not os.path.exists(SENDER_WHITELIST_PATH):
        errors.append(f"Sender whitelist not found at {SENDER_WHITELIST_PATH}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True
