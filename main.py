import datetime
import logging
import os
from typing import Any, Dict, List

import feedparser
from dotenv import load_dotenv
from jinja2 import Template

from root import DOCS_DIR, RSS_HTML_TEMPLATE_PATH, RSS_TEMPLATE_PATH, absolute
from src.AI.chatgpt import gpt_summary
from src.const import FilterField, FilterType, HtmlItem, Item
from src.filter import filter_entry
from src.util import get_config, init_dirs, init_logger

logger = logging.getLogger()

def _init():
    load_dotenv()
    init_logger()
    init_dirs()

def get_feeds(rss):
    try:
        feed = feedparser.parse(rss["url"])
    except Exception as e:
        logger.error(f"解析错误: {e}")
        return None
    if feed.bozo: 
        logger.info("解析错误")
        return None
    return feed

def _filter(rss, feed):
    filtered_items = []
    for item in feed.entries:
        data = {
            "link": item.get("link", ""),
            "title": item.get("title", ""),
            "published": item.get("published", ""),
            "updated": item.get("updated", ""),
            "article": item.get("summary", "") if item.get("media_content", None) else "",
            "summary": "",
            "media_content": item.get("media_content", None)
        }
        item = Item(**data)
        need = True 
        for item_filter in rss.get("filters", []):
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

def _render_xml(feed, filtered_items):
    with open(RSS_TEMPLATE_PATH, "r") as f:
        template = Template(f.read())
    rss_xml = template.render(feed=feed.feed, items=filtered_items)
    logger.info(f"rss xml Done")
    return rss_xml

def _output_xml(rss, data):
    if not os.path.exists(DOCS_DIR):
        os.makedirs(DOCS_DIR)
    rss_xml_filename = absolute(DOCS_DIR, rss["name"] + ".xml")
    with open(rss_xml_filename, "w") as f:
        f.write(data)
        
def _render_html(items:List[HtmlItem]):
    with open(RSS_HTML_TEMPLATE_PATH, "r") as f:
        html_template = Template(f.read())
    html = html_template.render(items=items, updatetime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    with open(absolute(DOCS_DIR, "index" + ".html"), "w") as f:
        f.write(html)
    
def _add_rss(rss, container:List[HtmlItem]):
    now = datetime.datetime.now()
    formatted_date = now.strftime("%m%d_%H%M")
    name = rss.get("name", "") + "_" + formatted_date + ".xml"
    new_url = rss.get("name", "") + ".xml"
    container.append(HtmlItem(rss.get("url"), new_url, name))
    

def main():
    # init
    _init()
    # load config
    rss_cfg = get_config()
    # process
    html_items:List[HtmlItem] = []
    for group_name, group_items in rss_cfg.items():
        for rss in group_items:
            logger.info(f"开始处理: {rss.get('text', '获取失败')}")
            feed = get_feeds(rss)
            if not feed: continue
            filtered_items = _filter(rss, feed)
            if len(filtered_items) == 0: continue
            if rss.get("use_chatgpt", False): _use_ai(filtered_items)
            rss_xml = _render_xml(feed, filtered_items)
            _output_xml(rss, rss_xml)
            _add_rss(rss, html_items)
    _render_html(html_items)
        
if __name__ == "__main__":
    main()
        