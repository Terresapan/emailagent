"""Gmail API authentication handler."""
import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config.settings import GMAIL_SCOPES, CREDENTIALS_PATH, TOKEN_PATH
from utils.logger import setup_logger

logger = setup_logger(__name__)


def authenticate_gmail():
    """
    Authenticate with Gmail API using OAuth 2.0.
    
    Returns:
        Credentials object for Gmail API access
    """
    creds = None
    
    # Check if token.json exists (previously authenticated)
    if os.path.exists(TOKEN_PATH):
        logger.info(f"Loading existing credentials from {TOKEN_PATH}")
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are invalid or don't exist, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("Starting new OAuth flow")
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Credentials file not found at {CREDENTIALS_PATH}. "
                    "Please download it from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
            logger.info("Authentication successful")
        
        # Save credentials for future use
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
            logger.info(f"Saved credentials to {TOKEN_PATH}")
    
    return creds
