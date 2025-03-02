import re
from typing import List

from bs4 import BeautifulSoup

from src.const import FilterField, FilterType, Item


def filter_entry(item: Item, filter_type: FilterType, filter_field: FilterField, keywords: List[str]) -> bool:
    """
    Filter an entry based on keywords.
    
    Args:
        item: The item to filter
        filter_type: Include or exclude filter
        filter_field: Which field to apply the filter to
        keywords: List of keywords to match
        
    Returns:
        True if the item should be included, False otherwise
    """
    # Get the text to search in
    if filter_field == FilterField.Title:
        text = item.title
    elif filter_field == FilterField.Article:
        text = clean_html(item.article)
    else:
        raise ValueError(f"Unknown filter field: {filter_field}")
        
    # Skip processing for empty content
    if not text or not keywords:
        return filter_type == FilterType.Include
    
    # Create regex pattern and search
    pattern = r'|'.join(map(re.escape, keywords))
    match_found = re.search(pattern, text, re.IGNORECASE) is not None
    
    # Return based on filter type
    if filter_type == FilterType.Include:
        return match_found
    elif filter_type == FilterType.Exclude:
        return not match_found
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")


def clean_html(html_content: str) -> str:
    """
    Clean HTML content by removing unwanted tags and extracting text.
    
    Args:
        html_content: HTML content to clean
        
    Returns:
        Cleaned text for summarization
    """
    # Return empty string for empty content
    if not html_content or len(html_content.strip()) == 0:
        return ""
        
    try:
        # Parse HTML with lxml for better performance
        soup = BeautifulSoup(html_content, "lxml")
        
        # Remove unwanted tags
        for tag in soup.select('script, style, img, svg, iframe, form, nav, header, footer, aside'):
            tag.decompose()
            
        # Remove attributes from all remaining tags to reduce noise
        for tag in soup.find_all(True):
            tag.attrs = {}
            
        # Get text with proper spacing between elements
        lines = []
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'li']):
            text = element.get_text(strip=True)
            if text:
                lines.append(text)
                
        # If no structured elements, use the entire text
        if not lines:
            return soup.get_text(separator=' ', strip=True)
            
        # Join with newlines between paragraphs
        return '\n'.join(lines)
    except Exception:
        # Fall back to simple tag removal if parsing fails
        soup = BeautifulSoup(html_content, "html.parser")
        for filter_tag in ["script", "style", "img", "a", "video", "audio", "iframe", "input"]:
            for tag in soup.find_all(filter_tag):
                tag.decompose()
        return soup.get_text(separator=' ', strip=True)