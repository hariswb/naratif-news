#!/usr/bin/env python3
"""
Media Monitoring Pipeline - Daily Batch Runner

This script orchestrates the complete pipeline execution:
1. Collect - Fetch RSS feeds and save raw XML
2. Parse - Convert XML to JSONL
3. Clean - Normalize, deduplicate, filter language
4. Signal - Extract sentiment signals
5. Store - Save to PostgreSQL
"""

import logging
import json
from datetime import datetime
from pathlib import Path
import sys
import argparse

# Add pipeline modules to path
sys.path.append(str(Path(__file__).parent))

from pipeline.collect.fetch_rss import collect_all_rss
from pipeline.parse.rss_to_jsonl import parse_to_jsonl, load_jsonl
from pipeline.clean.normalize import clean_articles
from pipeline.signal.sentiment import analyze_all_sentiments, Inset
from pipeline.signal.topic_modelling import analyze_topics
from pipeline.db import (
    get_db_session, create_pipeline_run, update_pipeline_run, 
    insert_articles, insert_run_statistics, insert_sentiment_results,
    insert_topic_models
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_run_metadata(run_id, run_date):
    """Create run metadata file."""
    return {
        "run_id": run_id,
        "run_date": run_date.isoformat(),
        "started_at": datetime.now().isoformat(),
        "pipeline_version": "1.0.0",
        "stages": {
            "collect": {"status": "pending"},
            "parse": {"status": "pending"},
            "clean": {"status": "pending"},
            "signal": {"status": "pending"}
        }
    }

def save_run_metadata(run_dir, metadata):
    """Save run metadata to file."""
    metadata_path = run_dir / "run_meta.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved run metadata to {metadata_path}")

def run_pipeline(limit=None):
    """Execute the complete pipeline."""
    # Generate run ID
    now = datetime.now()
    run_date = now.date()
    run_id = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    logger.info(f"=" * 60)
    logger.info(f"Starting pipeline run: {run_id}")
    logger.info(f"=" * 60)
    
    # Create run directory
    base_dir = Path("data/runs")
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logs directory
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Add run-specific log handler
    run_log_handler = logging.FileHandler(logs_dir / "pipeline.log")
    run_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(run_log_handler)
    
    # Initialize run metadata
    metadata = create_run_metadata(run_id, run_date)
    save_run_metadata(run_dir, metadata)
    
    # Connect to database
    db_session = None
    try:
        db_session = get_db_session()
        # Create pipeline run using ORM
        create_pipeline_run(db_session, run_id, run_date)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.warning("Continuing without database storage...")
        db_session = None
    
    try:
        # STAGE 1: COLLECT
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 1: COLLECT - Fetching RSS feeds")
        logger.info("=" * 60)
        
        articles, collect_stats = collect_all_rss(run_dir)
        
        if limit and len(articles) > limit:
            logger.info(f"Limiting articles to {limit} (originally {len(articles)})")
            articles = articles[:limit]
            collect_stats['total_articles'] = len(articles)

        metadata['stages']['collect'] = {
            "status": "completed",
            "stats": collect_stats,
            "completed_at": datetime.now().isoformat()
        }
        save_run_metadata(run_dir, metadata)
        
        if db_session:
            update_pipeline_run(db_session, run_id, stage='collect', stats={
                'total_sources': collect_stats['total_sources'],
                'total_fetched': collect_stats['total_articles']
            })
            insert_run_statistics(db_session, run_id, 'collect', collect_stats)
        
        logger.info(f"✓ Collect stage completed: {collect_stats['total_articles']} articles")
        
        # STAGE 2: PARSE
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 2: PARSE - Converting to JSONL")
        logger.info("=" * 60)
        
        parse_stats = parse_to_jsonl(run_dir, articles)
        metadata['stages']['parse'] = {
            "status": "completed",
            "stats": parse_stats,
            "completed_at": datetime.now().isoformat()
        }
        save_run_metadata(run_dir, metadata)
        
        if db_session:
            update_pipeline_run(db_session, run_id, stage='parse', stats={
                'total_parsed': parse_stats['total_articles']
            })
            insert_run_statistics(db_session, run_id, 'parse', parse_stats)
        
        logger.info(f"✓ Parse stage completed: {parse_stats['total_articles']} articles")
        
        # STAGE 3: CLEAN
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 3: CLEAN - Normalizing and filtering")
        logger.info("=" * 60)
        
        cleaned_articles, clean_stats = clean_articles(articles)
        
        metadata['stages']['clean'] = {
            "status": "completed",
            "stats": clean_stats,
            "completed_at": datetime.now().isoformat()
        }
        save_run_metadata(run_dir, metadata)
        
        if db_session:
            update_pipeline_run(db_session, run_id, stage='clean', stats={
                'total_cleaned': clean_stats['indonesian_only']
            })
            insert_run_statistics(db_session, run_id, 'clean', clean_stats)
        
        logger.info(f"✓ Clean stage completed: {clean_stats['indonesian_only']} articles")
        
        # STAGE 4: STORE ARTICLES (New Flow)
        url_to_id = {}
        if db_session:
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 4: STORE ARTICLES")
            logger.info("=" * 60)
            url_to_id = insert_articles(db_session, cleaned_articles, run_id, run_date)
            logger.info(f"✓ Stored {len(url_to_id)} articles in database")
        
        # STAGE 5: SIGNAL (Sentiment Analysis)
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 5: SIGNAL - Analyzing sentiment")
        logger.info("=" * 60)
        
        articles_with_sentiment, signal_stats = analyze_all_sentiments(cleaned_articles)
        metadata['stages']['signal'] = {
            "status": "completed",
            "stats": signal_stats,
            "completed_at": datetime.now().isoformat()
        }
        save_run_metadata(run_dir, metadata)
        
        if db_session:
            # Prepare sentiment results for storage
            sentiment_results = []
            for article in articles_with_sentiment:
                url = article.get('url')
                article_id = url_to_id.get(url)
                sentiment = article.get('sentiment')
                
                if article_id and sentiment:
                    # method_name should be in sentiment dict if we updated analyzer
                    # or retrieve from Inset class
                    method_name = sentiment.get('method', 'inset')
                    
                    sentiment_results.append({
                        "article_id": article_id,
                        "method_name": method_name,
                        "output": sentiment
                    })
            
            if sentiment_results:
                insert_sentiment_results(db_session, sentiment_results)
            
            update_pipeline_run(db_session, run_id, stage='signal', stats={
                'total_analyzed': signal_stats['total_analyzed']
            })
            insert_run_statistics(db_session, run_id, 'signal', signal_stats)
        
        logger.info(f"✓ Signal stage completed: {signal_stats['total_analyzed']} articles analyzed")

        # STAGE 6: TOPIC MODELLING
        if db_session:
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 6: TOPIC MODELLING")
            logger.info("=" * 60)
            
            # Map articles to DB IDs for topic modelling
            # We need to pass articles with IDs to analyze_topics if possible, OR
            # map them back after analysis. analyze_topics takes list of dicts with 'id' and 'title'.
            
            # Construct input with db_ids
            tm_input_articles = []
            for article in cleaned_articles:
                url = article.get('url')
                db_id = url_to_id.get(url)
                if db_id:
                    tm_input_articles.append({
                        "id": db_id,
                        "title": article.get("title", "")
                    })
            
            topic_results = analyze_topics(tm_input_articles)
            
            if topic_results:
                insert_topic_models(db_session, topic_results)
                logger.info(f"✓ Topic modelling completed: {len(topic_results)} articles processed")
            else:
                logger.info("No topic modelling results to store")

        # Mark run as completed
        if db_session:
            update_pipeline_run(db_session, run_id, status='completed')
        
        # Update final metadata
        metadata['completed_at'] = datetime.now().isoformat()
        metadata['status'] = 'completed'
        save_run_metadata(run_dir, metadata)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Run ID: {run_id}")
        logger.info(f"Total sources: {collect_stats['total_sources']}")
        logger.info(f"Articles fetched: {collect_stats['total_articles']}")
        logger.info(f"Articles cleaned: {clean_stats['indonesian_only']}")
        logger.info(f"Articles analyzed: {signal_stats['total_analyzed']}")
        logger.info(f"Run directory: {run_dir}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        metadata['status'] = 'failed'
        metadata['error'] = str(e)
        save_run_metadata(run_dir, metadata)
        
        if db_session:
            update_pipeline_run(db_session, run_id, status='failed', errors=str(e))
        
        raise
    
    finally:
        if db_session:
            db_session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Media Pipeline Daily Runner")
    parser.add_argument("--limit", type=int, help="Limit the number of articles to process")
    args = parser.parse_args()
    
    run_pipeline(limit=args.limit)