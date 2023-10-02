from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class FilterType(Enum):
    Include = "include"
    Exclude = "exclude"
    
    @staticmethod
    def from_str(s):
        if s == "include":
            return FilterType.Include
        elif s == "exclude":
            return FilterType.Exclude
        else:
            raise ValueError(f"Unknown filter type: {s}")
        
class FilterField(Enum):
    Title = "title"
    Article = "article"
    
    @staticmethod
    def from_str(s):
        if s == "title":
            return FilterField.Title
        elif s == "article":
            return FilterField.Article
        else:
            raise ValueError(f"Unknown filter field: {s}")

@dataclass
class Item:
    title:str
    link:str
    summary:str
    article:str
    updated:str
    id:str
    guid:str
    published:Optional[str] = ""
    media_content:Optional[Dict] = None
    media_thumbnail: Optional[Dict] = None
    
@dataclass
class HtmlItem:
    old_url: str
    new_url: str
    name: str