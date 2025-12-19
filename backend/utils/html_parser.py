"""HTML to text parser for email content."""
from justhtml import JustHTML
import re


def html_to_text(html_content: str) -> str:
    """
    Convert HTML email content to clean text.
    
    Uses justhtml for HTML5-compliant parsing that handles malformed
    email HTML more reliably than BeautifulSoup.
    
    Args:
        html_content: Raw HTML content from email
        
    Returns:
        Cleaned text content
    """
    if not html_content:
        return ""
    
    try:
        # Parse HTML with HTML5-compliant parser
        doc = JustHTML(html_content)
        
        # Remove script, style, meta, and link elements
        for element in doc.query("script, style, meta, link"):
            element.remove()
        
        # Extract text using justhtml's built-in method
        text = doc.to_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
        
    except Exception as e:
        # Fallback to returning empty string if parsing fails
        # (justhtml is fuzz-tested and shouldn't crash, but just in case)
        return ""
