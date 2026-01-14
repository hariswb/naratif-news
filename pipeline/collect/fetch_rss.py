import requests
import feedparser
import logging
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
import json

logger = logging.getLogger(__name__)

RSS_SOURCES = None

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Linux"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

# Resolve config path relative to project root (assuming this file is in pipeline/collect/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "rss_sources.json"

with open(CONFIG_PATH) as f:
    RSS_SOURCES = json.load(f)

def parse_published_date(entry):
    """Parse the published date safely."""
    try:
        return datetime(*entry.published_parsed[:6]) if hasattr(entry, "published_parsed") else None
    except Exception as e:
        logger.warning(f"Failed to parse published date: {e}")
        return None

def clean_html_images(html_text):
    """Remove <img> tags from HTML content."""
    return re.sub(r'<img[^>]*>', '', html_text)

def fetch_rss(feed_source, feed_url, timeout=10.0):
    """Fetch and parse an RSS feed."""
    logger.info(f"Start fetching {feed_source}")

    try:
        resp = requests.get(feed_url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        msg = f"Timeout when reading RSS from {feed_source} ({feed_url})"
        logger.warning(msg)
        raise Exception(msg)
    except requests.exceptions.RequestException as e:
        msg = f"Request failed for {feed_source} ({feed_url}): {e}"
        logger.warning(msg)
        raise Exception(msg)

    content = BytesIO(resp.content)
    feed = feedparser.parse(content)

    if feed.bozo:
        logger.warning(f"Failed to parse RSS feed from {feed_source}: {feed.bozo_exception}")
        return [], None

    parsed_items = []

    for entry in feed.entries:
        url = entry.get("link", "").strip()
        if not url:
            continue

        description = entry.get("description", "").strip()
         
        parsed_items.append({
            "title": entry.get("title", "No Title").strip(),
            "url": url,
            "summary": clean_html_images(description),
            "published": parse_published_date(entry),
            "source": feed_source,
        })

    return parsed_items, resp.content

def collect_all_rss(run_dir):
    """Collect RSS from all sources and save raw XML artifacts."""
    raw_dir = run_dir / "raw" / "rss"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    all_articles = []
    stats = {"total_sources": len(RSS_SOURCES), "successful": 0, "failed": 0, "total_articles": 0}
    
    for source_name, source_config in RSS_SOURCES.items():
        try:
            articles, xml_content = fetch_rss(source_name, source_config["url"])
            
            if xml_content:
                # Save raw XML artifact
                xml_path = raw_dir / f"{source_name}.xml"
                xml_path.write_bytes(xml_content)
                logger.info(f"Saved raw XML for {source_name} to {xml_path}")
            
            all_articles.extend(articles)
            stats["successful"] += 1
            stats["total_articles"] += len(articles)
            logger.info(f"Collected {len(articles)} articles from {source_name}")
            
        except Exception as e:
            logger.error(f"Failed to collect from {source_name}: {e}")
            stats["failed"] += 1
    
    logger.info(f"Collection complete: {stats['successful']}/{stats['total_sources']} sources, {stats['total_articles']} articles")
    return all_articles, stats

if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(level=logging.INFO)
    test_dir = Path("data/runs/test")
    articles, stats = collect_all_rss(test_dir)
    print(f"Collected {len(articles)} articles")
    print(f"Stats: {stats}")