import re
from typing import List

from bs4 import BeautifulSoup

from src.const import FilterField, FilterType, Item


def filter_entry(item:Item, filter_type:FilterType, filter_field:FilterField, keywords:List[str]):
    text = ""
    if filter_field == FilterField.Title:
        text = item.title
    elif filter_field == FilterField.Article:
        text = clean_html(item.article)
    else:
        raise ValueError(f"Unknown filter field: {filter_field}")
    pattern = r'|'.join(keywords)
    if filter_type == FilterType.Include:
        return re.search(pattern, text, re.IGNORECASE) is not None
    elif filter_type == FilterType.Exclude:
        return re.search(pattern, text, re.IGNORECASE) is None
    else:
        raise ValueError(f"Unknown filter type: {filter_type}")
    

def clean_html(html_content):
    """
    This function is used to clean the HTML content.
    It will remove all the <script>, <style>, <img>, <a>, <video>, <audio>, <iframe>, <input> tags.
    Returns:
        Cleaned text for summarization
    """
    soup = BeautifulSoup(html_content, "html.parser")
    filters = ["script", "style", "img", "a", "video", "audio", "iframe", "input"]
    for filter in filters:
        for tag in soup.find_all(filter):
            tag.decompose()
            
    return soup.get_text()