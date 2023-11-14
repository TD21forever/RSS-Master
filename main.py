import datetime
import logging
import os
from typing import Any, Dict, List

import feedparser
import openai
from dotenv import load_dotenv
from jinja2 import Template

from root import (CACHE_PATH, CONFIG_PATH, DOCS_DIR, RSS_HTML_TEMPLATE_PATH,
                  RSS_TEMPLATE_PATH, absolute)
from src.AI.chatgpt import gpt_summary
from src.cache import CacheKit
from src.const import FilterField, FilterType, HtmlItem, Item
from src.filter import filter_entry
from src.util import (convert_yaml_to_opml, get_config, init_dirs, init_logger,
                      md5hash_6)

logger = logging.getLogger()
cache = CacheKit(CACHE_PATH)


def _init():
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    init_logger()
    init_dirs()
    cache.load_cache()

def get_feeds(rss):
    try:
        feed = feedparser.parse(rss["url"])
    except Exception as e:
        logger.error(f"解析错误: {e}")
        return None
    if feed.bozo: 
        error = feed.get("bozo_exception", "")
        if error:
            logger.error(f"解析错误:, error:{error}")
        else:
            logger.error(f"解析错误")
        return None
    return feed

def _filter(rss, feed):
    filtered_items = []
    for item in feed.entries:
        id_ = item.get("id", item.get("link", md5hash_6(item.get("title", "没获取数据"))))
        if item.get("media_content", ""):
            article = ""
        else:
            article = item.get("summary", "") or item.get("description", "") or ""
        data = {
            "id": id_,
            "guid": id_,
            "link": item.get("link", ""),
            "title": item.get("title", ""),
            "updated": item.get("updated", ""),
            "article": article,
            "media_thumbnail": item.get("media_thumbnail"),
            "media_content": item.get("media_content"),
            "summary": ""
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

def _use_ai(filtered_items:List[Item]):
    cost = 0
    for item in filtered_items:
        key = md5hash_6(item.id)
        if cache.has(key):
            logger.info(f"{item.title}命中缓存")
            item.summary = cache.get(key)
            continue
        try:
            response = gpt_summary(item.article, "gpt-3.5-turbo")
            summary = response.get("summary", "")
            cache.set(key, summary)
            item.summary = summary
            cost += response.get("price", 0)
        except Exception as e:
            logger.critical(f"AI 错误: {e}")
    if cost:
        logger.info(f"AI 花费: {cost:.4f}")

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
        
def _output_opml():
    convert_yaml_to_opml(CONFIG_PATH, absolute(DOCS_DIR, "opml.xml"))
    
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
    _output_opml()
        
if __name__ == "__main__":
    main()
        