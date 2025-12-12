"""Gmail API client with retry logic."""
import base64
from typing import List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import MAX_RETRIES, RETRY_MIN_WAIT, RETRY_MAX_WAIT, NEWSLETTER_LABEL
from email.mime.text import MIMEText
from gmail.auth import authenticate_gmail
from utils.logger import setup_logger
from utils.html_parser import html_to_text

logger = setup_logger(__name__)


class GmailClient:
    """Gmail API client with retry logic for all operations."""
    
    def __init__(self):
        """Initialize Gmail client with authentication."""
        self.creds = authenticate_gmail()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.user_id = 'me'
        logger.info("Gmail client initialized successfully")
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)
    )
    def _get_or_create_label(self, label_name: str) -> str:
        """
        Get label ID or create if it doesn't exist.
        
        Args:
            label_name: Name of the label
            
        Returns:
            Label ID
        """
        try:
            # Get all labels
            results = self.service.users().labels().list(userId=self.user_id).execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    logger.info(f"Found existing label: {label_name}")
                    return label['id']
            
            # Create label if it doesn't exist
            logger.info(f"Creating new label: {label_name}")
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = self.service.users().labels().create(
                userId=self.user_id,
                body=label_object
            ).execute()
            
            logger.info(f"Created label '{label_name}' with ID: {created_label['id']}")
            return created_label['id']
            
        except HttpError as error:
            logger.error(f"Error getting/creating label: {error}")
            raise
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)
    )
    def fetch_unread_emails(self, sender_configs: List[Dict[str, str]]) -> List[Dict]:
        """
        Fetch unread emails from whitelisted senders.
        
        Args:
            sender_configs: List of dicts with 'name' and 'email' keys
            
        Returns:
            List of email dictionaries with id, sender, subject, and body
        """
        emails = []
        
        # Build query for unread emails from whitelisted senders
        sender_emails = list(set([config['email'] for config in sender_configs]))
        from_queries = " OR ".join([f"from:{email}" for email in sender_emails])
        query = f"is:unread ({from_queries})"
        
        logger.info(f"Fetching unread emails with query: {query}")
        
        try:
            # Get message IDs
            results = self.service.users().messages().list(
                userId=self.user_id,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread emails from whitelisted senders")
            
            # Fetch full message details
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId=self.user_id,
                        id=msg['id'],
                        format='full'
                    ).execute()
                    
                    # Extract headers
                    headers = message['payload']['headers']
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    
                    # Extract body
                    body = self._extract_body(message['payload'])
                    
                    emails.append({
                        'id': msg['id'],
                        'sender': sender,
                        'subject': subject,
                        'body': body
                    })
                    
                    logger.info(f"Fetched email: {subject[:50]}... from {sender}")
                    
                except HttpError as error:
                    logger.error(f"Error fetching message {msg['id']}: {error}")
                    continue
            
            return emails
            
        except HttpError as error:
            logger.error(f"Error fetching emails: {error}")
            raise
    
    def _extract_body(self, payload: Dict) -> str:
        """
        Extract email body from message payload.
        
        Args:
            payload: Message payload from Gmail API
            
        Returns:
            Plain text body content
        """
        body = ""
        
        # Check for parts (multipart message)
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        html_content = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        body = html_to_text(html_content)
                        
        # Single part message
        elif 'body' in payload and 'data' in payload['body']:
            data = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            if payload.get('mimeType') == 'text/html':
                body = html_to_text(data)
            else:
                body = data
        
        return body
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)
    )
    def mark_as_read(self, message_id: str):
        """
        Mark email as read.
        
        Args:
            message_id: Gmail message ID
        """
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info(f"Marked message {message_id} as read")
            
        except HttpError as error:
            logger.error(f"Error marking message as read: {error}")
            raise
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)
    )
    def apply_label(self, message_id: str, label_name: str = NEWSLETTER_LABEL):
        """
        Apply label to email.
        
        Args:
            message_id: Gmail message ID
            label_name: Name of the label to apply
        """
        try:
            label_id = self._get_or_create_label(label_name)
            
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            logger.info(f"Applied label '{label_name}' to message {message_id}")
            
        except HttpError as error:
            logger.error(f"Error applying label: {error}")
            raise
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)
    )
    def archive_email(self, message_id: str):
        """
        Archive email (remove from inbox).
        
        Args:
            message_id: Gmail message ID
        """
        try:
            self.service.users().messages().modify(
                userId=self.user_id,
                id=message_id,
                body={'removeLabelIds': ['INBOX']}
            ).execute()
            logger.info(f"Archived message {message_id} (removed from inbox)")
            
        except HttpError as error:
            logger.error(f"Error archiving message: {error}")
            raise
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT)
    )
    def send_email(self, to: str, subject: str, body: str):
        """
        Send an email.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
        """
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent_message = self.service.users().messages().send(
                userId=self.user_id,
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Sent email to {to} with subject: {subject}")
            logger.info(f"Sent message ID: {sent_message['id']}")
            return sent_message['id']
            
        except HttpError as error:
            logger.error(f"Error sending email: {error}")
            raise
