"""HTML to text parser for email content."""
from justhtml import JustHTML
import re


def html_to_text(html_content: str) -> str:
    """
    Convert HTML email content to clean text.
    
    Uses justhtml for lightweight, fast HTML parsing.
    
    Args:
        html_content: Raw HTML content from email
        
    Returns:
        Cleaned text content
    """
    if not html_content:
        return ""
    
    try:
        doc = JustHTML(html_content)
        
        # Get text content - justhtml handles removing scripts/styles
        text = doc.to_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
        
    except Exception as e:
        return ""
