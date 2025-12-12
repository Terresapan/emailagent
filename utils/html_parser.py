"""HTML to text parser for email content."""
from bs4 import BeautifulSoup
import re


def html_to_text(html_content: str) -> str:
    """
    Convert HTML email content to clean text.
    
    Args:
        html_content: Raw HTML content from email
        
    Returns:
        Cleaned text content
    """
    if not html_content:
        return ""
    
    # Parse HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style", "meta", "link"]):
        script.decompose()
    
    # Get text
    text = soup.get_text()
    
    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    # Remove excessive newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()
