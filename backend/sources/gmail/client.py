"""Gmail API client with retry logic."""
import base64
from email.mime.text import MIMEText
from typing import List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt
from config.settings import LLM_MAX_RETRIES, NEWSLETTER_LABEL
from sources.gmail.auth import authenticate_gmail
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
        stop=stop_after_attempt(LLM_MAX_RETRIES),
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
        stop=stop_after_attempt(LLM_MAX_RETRIES),
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
        stop=stop_after_attempt(LLM_MAX_RETRIES),
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
        stop=stop_after_attempt(LLM_MAX_RETRIES),
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
        stop=stop_after_attempt(LLM_MAX_RETRIES),
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
        stop=stop_after_attempt(LLM_MAX_RETRIES),
    )
    def send_email(self, to: str, subject: str, body: str):
        """
        Send an email with markdown content rendered as HTML.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (markdown format)
        """
        try:
            from email.mime.multipart import MIMEMultipart
            import markdown
            
            # Convert markdown to HTML
            html_body = markdown.markdown(
                body, 
                extensions=['extra', 'nl2br', 'sane_lists']
            )
            
            # Wrap in a styled HTML template (light mode, brand-aligned)
            styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.7;
            color: #1a1a1a;
            max-width: 680px;
            margin: 0 auto;
            padding: 24px;
            background-color: #f8f7f6;
        }}
        .email-container {{
            background-color: #ffffff;
            border-radius: 12px;
            padding: 40px;
            border: 1px solid rgba(0, 0, 0, 0.06);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }}
        h1 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 600;
            color: #1a1a1a;
            font-size: 2em;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }}
        .header-accent {{
            height: 4px;
            background: linear-gradient(to right, #c4b5fd, #86efdf);
            border-radius: 2px;
            margin-bottom: 32px;
        }}
        h2 {{
            font-family: 'Playfair Display', Georgia, serif;
            font-weight: 600;
            color: #1a1a1a;
            margin-top: 32px;
            margin-bottom: 16px;
            font-size: 1.35em;
            letter-spacing: -0.01em;
            padding-bottom: 8px;
            border-bottom: 2px solid #c4b5fd;
        }}
        h3 {{
            font-family: 'DM Sans', sans-serif;
            font-weight: 600;
            color: #86efdf;
            margin-top: 24px;
            font-size: 1.1em;
        }}
        p {{
            margin-bottom: 16px;
            color: #374151;
        }}
        ul, ol {{
            margin-bottom: 16px;
            padding-left: 24px;
        }}
        li {{
            margin-bottom: 10px;
            color: #374151;
        }}
        strong {{
            color: #1a1a1a;
            font-weight: 600;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e5e5e5;
            margin: 28px 0;
        }}
        a {{
            color: #c4b5fd;
            text-decoration: none;
        }}
        a:hover {{
            color: #86efdf;
            text-decoration: underline;
        }}
        code {{
            background-color: #f3f0ff;
            color: #c4b5fd;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.9em;
            font-family: 'SF Mono', Monaco, monospace;
            border: 1px solid #c4b5fd;
        }}
        blockquote {{
            border-left: 4px solid;
            border-image: linear-gradient(to bottom, #c4b5fd, #86efdf) 1;
            margin: 20px 0;
            padding: 16px 24px;
            background-color: #f3f0ff;
            color: #6b7280;
            border-radius: 0 8px 8px 0;
        }}
        .muted {{
            color: #6b7280;
        }}
        .brand-text {{
            background: linear-gradient(to right, #c4b5fd, #86efdf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 24px;
            border-top: 1px solid #e5e5e5;
            text-align: center;
            color: #9ca3af;
            font-size: 0.85em;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        {html_body}
        <div class="footer">
            Generated by AI Newsletter Agent
        </div>
    </div>
</body>
</html>"""
            
            # Create multipart message with both HTML and plain text
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject
            
            # Attach plain text version (for clients that don't support HTML)
            text_part = MIMEText(body, 'plain')
            message.attach(text_part)
            
            # Attach HTML version (preferred)
            html_part = MIMEText(styled_html, 'html')
            message.attach(html_part)
            
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
