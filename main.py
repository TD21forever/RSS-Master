import logging
import os
from typing import Any, Dict, List

import feedparser
from dotenv import load_dotenv
from jinja2 import Template

from root import DOCS_DIR, RSS_TEMPLATE_PATH, absolute
from src.AI.chatgpt import gpt_summary
from src.enum import FilterField, FilterType, Item
from src.filter import filter_entry
from src.util import get_config, init_dirs, init_logger

logger = logging.getLogger()

def _init():
    load_dotenv()
    init_logger()
    init_dirs()

def get_feeds(rss):
    feed = feedparser.parse(rss["url"])
    if feed.bozo: 
        logger.info("解析错误")
        return None
    return feed

def _filter(rss, feed):
    filtered_items = []
    for item in feed.entries:
        data = {
            "link": item["link"],
            "title": item["title"],
            "published": item["published"],
            "updated": item["updated"],
            "article": item["summary"],
            "summary": ""
        }
        item = Item(**data)
        need = True 
        for item_filter in rss["filters"]:
            filter_type = FilterType.from_str(item_filter["type"])
            filter_field = FilterField.from_str(item_filter["field"])
            keywords = item_filter["keywords"]
            if not filter_entry(item, filter_type, filter_field, keywords):
                need = False
                break
        if not need: continue
        filtered_items.append(item)
    logger.info(f"过滤后的条目数: {len(filtered_items)}")
    return filtered_items

def _use_ai(filtered_items):
    for item in filtered_items:
        summary = gpt_summary(item.article, "gpt-3.5-turbo", 3, 200)
        logger.info(f"AI总结: {summary}")
        item.summary = summary

def _render(feed, filtered_items):
    with open(RSS_TEMPLATE_PATH, "r") as f:
        template = Template(f.read())
    rss_xml = template.render(feed=feed.feed, items=filtered_items)
    logger.info(f"rss xml: {rss_xml}")
    return rss_xml

def _output(rss, data):
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    rss_xml_filename = absolute(DOCS_DIR, rss["name"] + ".xml")
    with open(rss_xml_filename, "w") as f:
        f.write(data)

def main():
    # init
    _init()
    # load config
    rss_cfg = get_config("rss")
    logger.info(f"rss config: {rss_cfg}")
    # process
    for rss in rss_cfg:
        feed = get_feeds(rss)
        if not feed: continue
        filtered_items = _filter(rss, feed)
        if len(filtered_items) == 0: continue
        if rss["use_chatgpt"]: _use_ai(filtered_items)
        rss_xml = _render(feed, filtered_items)
        _output(rss, rss_xml)
        
if __name__ == "__main__":
    main()
        