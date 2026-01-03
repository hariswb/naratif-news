#!/usr/bin/env python3
"""
Populate Test Data Script

This script runs a subset of the pipeline (Collect and Parse) to generate
real-world artifacts (XML, JSONL, logs) in `tests/data`.
It does NOT use the database or run sentiment analysis.
"""

import logging
import shutil
import sys
from pathlib import Path

# Add project root to path (parent of tests dir)
sys.path.append(str(Path(__file__).parents[1]))

from pipeline.collect.fetch_rss import collect_all_rss
from pipeline.parse.rss_to_jsonl import parse_to_jsonl

def setup_test_data_dir(base_dir: Path):
    """Ensure clean text data directory exists."""
    if base_dir.exists():
        print(f"Cleaning existing test data in {base_dir}...")
        shutil.rmtree(base_dir)
    
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(exist_ok=True)
    
    print(f"Initialized {base_dir}")

def configure_logging(log_file: Path):
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def populate_data():
    # Data dir is relative to this script: ./data
    base_dir = Path(__file__).parent / "data"
    setup_test_data_dir(base_dir)
    
    configure_logging(base_dir / "logs" / "pipeline.log")
    logger = logging.getLogger("populate_test_data")
    
    logger.info("Starting test data population...")
    
    try:
        # STAGE 1: COLLECT
        logger.info("Fetching RSS feeds...")
        articles, collect_stats = collect_all_rss(base_dir)
        logger.info(f"Collected {collect_stats['total_articles']} articles")
        
        # STAGE 2: PARSE
        logger.info("Parsing to JSONL...")
        parse_stats = parse_to_jsonl(base_dir, articles)
        logger.info(f"Parsed {parse_stats['total_articles']} articles")
        
        logger.info(f"SUCCESS: Test data populated in {base_dir}")
        
    except Exception as e:
        logger.error(f"Failed to populate test data: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    populate_data()
