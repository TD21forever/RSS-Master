import asyncio
import datetime
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

import feedparser
import pandas as pd
from dotenv import load_dotenv
from jinja2 import Template
from openai import OpenAI

from root import (CACHE_PATH, CONFIG_PATH, COST_RECORD_PATH, DOCS_DIR,
                  RSS_HTML_TEMPLATE_PATH, RSS_TEMPLATE_PATH, absolute)
from src.AI.chatgpt import gpt_summary
from src.cache import CacheKit
from src.const import FilterField, FilterType, HtmlItem, Item
from src.filter import filter_entry
from src.util import (convert_yaml_to_opml, get_config, init_dirs, init_logger,
                      md5hash_6)

logger = logging.getLogger()
cache = CacheKit(CACHE_PATH)


class RSSProcessorApp:
    """Main application for processing RSS feeds and generating summaries."""

    def __init__(self):
        """Initialize the application."""
        self.html_items: List[HtmlItem] = []
        self.openai_client = None
        self.total_cost = 0
        self.process_count = 0
        self.error_count = 0
        self.start_time = None
        self.default_model = "deepseek-chat"
        self.parallel_workers = 1

    def init(self):
        """Initialize environment, logger, directories, and cache."""
        load_dotenv()
        
        # Configure OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if api_key:
            if base_url:
                self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                self.openai_client = OpenAI(api_key=api_key)
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables.")
            
        # Set log level from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_level_value = getattr(logging, log_level, logging.INFO)
        logging.getLogger().setLevel(log_level_value)
        logger.info(f"Log level set to {log_level}")
        
        # Get OpenAI model from environment
        self.default_model = os.getenv("OPENAI_MODEL", self.default_model)
        logger.info(f"Using OpenAI model: {self.default_model}")
        
        # Get parallel workers count from environment
        try:
            self.parallel_workers = int(os.getenv("PARALLEL_WORKERS", "5"))
        except ValueError:
            self.parallel_workers = 5
        logger.info(f"Using {self.parallel_workers} parallel workers")
        
        init_logger()
        init_dirs()
        cache.load_cache()
        self.start_time = time.time()
        
    async def process_rss_feed(self, rss: Dict[str, Any]) -> None:
        """
        Process a single RSS feed.
        
        Args:
            rss: RSS feed configuration
        """
        try:
            logger.info(f"Processing: {rss.get('text', 'Unknown feed')}")
            
            # Step 1: Fetch feed data
            feed = self.get_feeds(rss)
            if not feed:
                logger.error(f"Failed to fetch feed: {rss.get('text', 'Unknown feed')}")
                self.error_count += 1
                return
                
            # Step 2: Filter entries
            filtered_items = self.filter_entries(rss, feed)
            if not filtered_items:
                logger.info(f"No entries passed filtering: {rss.get('text', 'Unknown feed')}")
                return
                
            # Step 3: Generate AI summaries if enabled
            if rss.get("use_chatgpt", False):
                await self.process_ai_summaries(filtered_items)
                
            # Step 4: Render and save XML
            rss_xml = self.render_xml(feed, filtered_items)
            self.output_xml(rss, rss_xml)
            
            # Step 5: Add to HTML items for index
            self.add_rss_to_html_items(rss)
            
            self.process_count += 1
            logger.info(f"Completed processing: {rss.get('text', 'Unknown feed')}")
            
        except Exception as e:
            logger.error(f"Error processing feed {rss.get('text', 'Unknown')}: {str(e)}", exc_info=True)
            self.error_count += 1

    def get_feeds(self, rss: Dict[str, Any]) -> Optional[Any]:
        """
        Fetch RSS feed data.
        
        Args:
            rss: RSS feed configuration
            
        Returns:
            Parsed feed data or None if fetching fails
        """
        try:
            feed = feedparser.parse(rss["url"])
            
            if feed.bozo and feed.get("bozo_exception"):
                error = feed.get("bozo_exception", "")
                logger.error(f"Feed parse error: {error}")
                return None
                
            if not feed.entries:
                logger.warning(f"Feed has no entries: {rss.get('text', 'Unknown feed')}")
                
            return feed
            
        except Exception as e:
            logger.error(f"Feed fetch error: {str(e)}", exc_info=True)
            return None

    def filter_entries(self, rss: Dict[str, Any], feed: Any) -> List[Item]:
        """
        Filter feed entries based on configured filters.
        
        Args:
            rss: RSS feed configuration
            feed: Parsed feed data
            
        Returns:
            List of filtered feed items
        """
        filtered_items = []
        total_entries = len(feed.entries)
        
        for item in feed.entries:
            try:
                # Extract ID or generate one if missing
                id_ = item.get("id", item.get(
                    "link", md5hash_6(item.get("title", "No Title"))))
                    
                # Get article content if available
                article = ""
                if not item.get("media_content", ""):
                    article = item.get("summary", "") or item.get(
                        "description", "") or ""
                
                # Create item data structure
                data = {
                    "id": id_,
                    "guid": id_,
                    "link": item.get("link", ""),
                    "title": item.get("title", "No Title"),
                    "updated": item.get("updated", ""),
                    "article": article,
                    "media_thumbnail": item.get("media_thumbnail"),
                    "media_content": item.get("media_content"),
                    "summary": ""
                }
                
                # Create Item object and apply filters
                entry_item = Item(**data)
                should_include = True
                
                for item_filter in rss.get("filters", []):
                    filter_type = FilterType.from_str(item_filter["type"])
                    filter_field = FilterField.from_str(item_filter["field"])
                    keywords = item_filter["keywords"]
                    
                    if not filter_entry(entry_item, filter_type, filter_field, keywords):
                        should_include = False
                        break
                        
                if should_include:
                    filtered_items.append(entry_item)
                    
            except Exception as e:
                logger.warning(f"Error processing entry: {str(e)}")
                
        logger.info(f"Filtered {len(filtered_items)}/{total_entries} entries")
        return filtered_items

    async def process_ai_summaries(self, filtered_items: List[Item]) -> None:
        """
        Process AI summaries for items using async processing.
        
        Args:
            filtered_items: List of filtered items to summarize
        """
        # Use configured number of parallel workers
        batch_size = self.parallel_workers
        
        # Process items in batches using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            loop = asyncio.get_event_loop()
            tasks = []
            
            for item in filtered_items:
                # Process if article has sufficient content
                if len(item.article) >= 400:
                    task = loop.run_in_executor(
                        executor, 
                        self.generate_summary,
                        item
                    )
                    tasks.append(task)
            
            # Wait for all tasks to complete
            if tasks:
                await asyncio.gather(*tasks)

    def generate_summary(self, item: Item) -> None:
        """
        Generate summary for a single item.
        
        Args:
            item: The item to generate a summary for
        """
        key = md5hash_6(item.id)
        
        # Use cached summary if available
        if cache.has(key):
            logger.info(f"Cache hit for: {item.title}")
            item.summary = cache.get(key)
            return
            
        # Generate new summary
        try:
            logger.info(f"Generating summary for: {item.title}")
            model = self.default_model  # Use configured model
            
            response = gpt_summary(item.article, model, client=self.openai_client)
            summary = response.get("summary", "")
            cost = response.get("price", 0)
            
            if summary:
                cache.set(key, summary)
                item.summary = summary
                self.total_cost += cost
                logger.info(f"Summary generated ({len(summary)} chars)")
            else:
                logger.warning(f"Empty summary generated for: {item.title}")
                
        except Exception as e:
            logger.error(f"AI summary error: {str(e)}", exc_info=True)

    def render_xml(self, feed: Any, filtered_items: List[Item]) -> str:
        """
        Render XML from feed and filtered items.
        
        Args:
            feed: Parsed feed data
            filtered_items: List of filtered items
            
        Returns:
            Rendered XML string
        """
        try:
            with open(RSS_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template = Template(f.read())
                
            rss_xml = template.render(feed=feed.feed, items=filtered_items)
            logger.info(f"XML rendering complete ({len(rss_xml)} chars)")
            return rss_xml
            
        except Exception as e:
            logger.error(f"XML rendering error: {str(e)}", exc_info=True)
            return ""

    def output_xml(self, rss: Dict[str, Any], data: str) -> None:
        """
        Output XML to file.
        
        Args:
            rss: RSS feed configuration
            data: XML data to write
        """
        if not data:
            return
            
        try:
            if not os.path.exists(DOCS_DIR):
                os.makedirs(DOCS_DIR)
            logger.info(rss)
            rss_xml_filename = absolute(DOCS_DIR, rss["name"] + ".xml")
            
            with open(rss_xml_filename, "w", encoding="utf-8") as f:
                f.write(data)
                
            logger.info(f"XML saved to: {rss_xml_filename}")
            
        except Exception as e:
            logger.error(f"Error saving XML: {str(e)}", exc_info=True)

    def render_html(self) -> None:
        """Render HTML index page from collected HTML items."""
        try:
            with open(RSS_HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                html_template = Template(f.read())
                
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html = html_template.render(
                items=self.html_items, 
                updatetime=current_time
            )
            
            with open(absolute(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
                f.write(html)
                
            logger.info(f"HTML index saved with {len(self.html_items)} feeds")
            
        except Exception as e:
            logger.error(f"Error rendering HTML: {str(e)}", exc_info=True)

    def add_rss_to_html_items(self, rss: Dict[str, Any]) -> None:
        """
        Add RSS feed to HTML items list.
        
        Args:
            rss: RSS feed configuration
        """
        now = datetime.datetime.now()
        formatted_date = now.strftime("%m%d_%H%M")
        name = rss.get("name", "") + "_" + formatted_date + ".xml"
        new_url = rss.get("name", "") + ".xml"
        
        self.html_items.append(HtmlItem(rss.get("url"), new_url, name))

    def output_opml(self) -> None:
        """Output OPML file of all feeds."""
        try:
            convert_yaml_to_opml(CONFIG_PATH, absolute(DOCS_DIR, "opml.xml"))
            logger.info("OPML file generated")
        except Exception as e:
            logger.error(f"Error generating OPML: {str(e)}", exc_info=True)

    def record_cost(self) -> None:
        """Record AI usage cost to Excel file."""
        if not self.total_cost:
            return
            
        try:
            logger.info(f"Total AI cost: {self.total_cost:.8f}")
            
            # Read existing cost record or create new one
            if not os.path.exists(COST_RECORD_PATH):
                df = pd.DataFrame(columns=["time", "cost"])
            else:
                df = pd.read_excel(COST_RECORD_PATH)

            # Add new cost record
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_record = pd.DataFrame([[timestamp, self.total_cost]], columns=["time", "cost"])
            df = pd.concat([df, new_record], ignore_index=True)
            
            # Save to Excel
            df.to_excel(COST_RECORD_PATH, index=False)
            logger.info(f"Cost record saved to: {COST_RECORD_PATH}")
            
        except Exception as e:
            logger.error(f"Error recording cost: {str(e)}", exc_info=True)

    def log_stats(self) -> None:
        """Log processing statistics."""
        elapsed_time = time.time() - self.start_time
        logger.info("=" * 40)
        logger.info(f"Processing complete:")
        logger.info(f"- Feeds processed: {self.process_count}")
        logger.info(f"- Errors encountered: {self.error_count}")
        logger.info(f"- Total AI cost: ${self.total_cost:.6f}")
        logger.info(f"- Total runtime: {elapsed_time:.2f} seconds")
        logger.info("=" * 40)

    async def run(self) -> None:
        """Run the RSS processor application."""
        # Initialize the application
        self.init()
        
        # Load configuration
        rss_cfg = get_config()
        
        # Process each feed group
        tasks = []
        for group_name, group_items in rss_cfg.items():
            logger.info(f"Processing group: {group_name}")
            for rss in group_items:
                tasks.append(self.process_rss_feed(rss))
        
        # Wait for all feeds to be processed
        if tasks:
            await asyncio.gather(*tasks)
        
        # Generate HTML index and OPML
        self.render_html()
        self.output_opml()
        
        # Record cost and log stats
        self.record_cost()
        self.log_stats()


async def main():
    """Run the RSS processor application."""
    app = RSSProcessorApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
