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
# Supports multiple recipients as comma-separated values, e.g., "user1@example.com,user2@example.com"
DIGEST_RECIPIENT_EMAIL = os.getenv("DIGEST_RECIPIENT_EMAIL")

# Third-party API settings
PRODUCT_HUNT_TOKEN = os.getenv("PRODUCT_HUNT_TOKEN")

# LLM settings
# Use different models for different tasks:
# - nano: Fast extraction/summarization
# - mini: Higher quality content generation
LLM_MODEL_EXTRACTION = "gpt-5-nano-2025-08-07"
LLM_MODEL_GENERATION = "gpt-5-mini-2025-08-07"
LLM_TEMPERATURE = 0.3
LLM_MAX_TOKENS = 8000  # GPT-5-mini uses reasoning tokens internally; 2000 was too low

# Reasoning effort settings for GPT-5-mini
# "low" = faster, fewer reasoning tokens (good for extraction)
# "medium" = balanced (good for content generation)
# "high" = slower, more reasoning tokens (good for complex analysis)
LLM_REASONING_EFFORT_EXTRACTION = "low"  # For email summarization
LLM_REASONING_EFFORT_GENERATION = "medium" # For briefing/LinkedIn (low prevents empty outputs with nano)

# Email processing settings
EMAIL_BODY_MAX_CHARS = 15000  # Truncate email body to this many characters (~3000 tokens)

# LLM timeout and retry settings
LLM_TIMEOUT_SECONDS = 300  # 5 minutes - prevents timeout on slow responses
LLM_MAX_RETRIES = 3  # Disabled to prevent duplicate processing in parallel LangGraph workflow

# Scheduling
EXECUTION_TIME = "08:00"  # 8:00 AM

# LangSmith settings
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_TRACING = True
LANGSMITH_ENDPOINT = "https://api.smith.langchain.com"
LANGSMITH_PROJECT = "AI Newsletter Digest"


def load_sender_whitelist():
    """Load the sender whitelist from JSON file."""
    with open(SENDER_WHITELIST_PATH, "r") as f:
        return json.load(f)


def load_sender_whitelist_by_type(email_type: str = "dailydigest"):
    """
    Load the sender whitelist filtered by email type.
    
    Args:
        email_type: Either 'dailydigest' or 'weeklydeepdives'
        
    Returns:
        List of sender configs matching the specified type
    """
    all_senders = load_sender_whitelist()
    return [s for s in all_senders if s.get("type") == email_type]


def validate_config():
    """Validate that all required configuration is present."""
    errors = []
    
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY not set in environment variables")
    
    if not DIGEST_RECIPIENT_EMAIL:
        errors.append("DIGEST_RECIPIENT_EMAIL not set in environment variables")
    
    if not os.path.exists(CREDENTIALS_PATH):
        errors.append(f"Gmail credentials not found at {CREDENTIALS_PATH}")
    
    if not os.path.exists(SENDER_WHITELIST_PATH):
        errors.append(f"Sender whitelist not found at {SENDER_WHITELIST_PATH}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True
