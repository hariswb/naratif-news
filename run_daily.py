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

# Add pipeline modules to path
sys.path.append(str(Path(__file__).parent))

from pipeline.collect.fetch_rss import collect_all_rss
from pipeline.parse.rss_to_jsonl import parse_to_jsonl, load_jsonl
from pipeline.clean.normalize import clean_articles
from pipeline.signal.sentiment import analyze_all_sentiments
from pipeline.db import get_db_connection, create_pipeline_run, update_pipeline_run, insert_articles, insert_run_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
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

def run_pipeline():
    """Execute the complete pipeline."""
    # Generate run ID
    run_date = datetime.now().date()
    run_id = run_date.strftime("%Y-%m-%d")
    
    logger.info(f"=" * 60)
    logger.info(f"Starting pipeline run: {run_id}")
    logger.info(f"=" * 60)
    
    # Create run directory
    run_dir = Path("data/runs") / run_id
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
    try:
        db_conn = get_db_connection()
        db_conn.connect()
        create_pipeline_run(db_conn, run_id, run_date)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.warning("Continuing without database storage...")
        db_conn = None
    
    try:
        # STAGE 1: COLLECT
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 1: COLLECT - Fetching RSS feeds")
        logger.info("=" * 60)
        
        articles, collect_stats = collect_all_rss(run_dir)
        metadata['stages']['collect'] = {
            "status": "completed",
            "stats": collect_stats,
            "completed_at": datetime.now().isoformat()
        }
        save_run_metadata(run_dir, metadata)
        
        if db_conn:
            update_pipeline_run(db_conn, run_id, stage='collect', stats={
                'total_sources': collect_stats['total_sources'],
                'total_fetched': collect_stats['total_articles']
            })
            insert_run_statistics(db_conn, run_id, 'collect', collect_stats)
        
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
        
        if db_conn:
            update_pipeline_run(db_conn, run_id, stage='parse', stats={
                'total_parsed': parse_stats['total_articles']
            })
            insert_run_statistics(db_conn, run_id, 'parse', parse_stats)
        
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
        
        if db_conn:
            update_pipeline_run(db_conn, run_id, stage='clean', stats={
                'total_cleaned': clean_stats['indonesian_only']
            })
            insert_run_statistics(db_conn, run_id, 'clean', clean_stats)
        
        logger.info(f"✓ Clean stage completed: {clean_stats['indonesian_only']} articles")
        
        # STAGE 4: SIGNAL (Sentiment Analysis)
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 4: SIGNAL - Analyzing sentiment")
        logger.info("=" * 60)
        
        articles_with_sentiment, signal_stats = analyze_all_sentiments(cleaned_articles)
        metadata['stages']['signal'] = {
            "status": "completed",
            "stats": signal_stats,
            "completed_at": datetime.now().isoformat()
        }
        save_run_metadata(run_dir, metadata)
        
        if db_conn:
            update_pipeline_run(db_conn, run_id, stage='signal', stats={
                'total_analyzed': signal_stats['total_analyzed']
            })
            insert_run_statistics(db_conn, run_id, 'signal', signal_stats)
        
        logger.info(f"✓ Signal stage completed: {signal_stats['total_analyzed']} articles analyzed")
        
        # STAGE 5: STORE IN DATABASE
        if db_conn:
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 5: STORE - Saving to PostgreSQL")
            logger.info("=" * 60)
            
            inserted_count = insert_articles(db_conn, articles_with_sentiment, run_id)
            logger.info(f"✓ Stored {inserted_count} articles in database")
            
            # Mark run as completed
            update_pipeline_run(db_conn, run_id, status='completed')
        
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
        logger.info(f"Sentiment distribution: {signal_stats['sentiment_distribution']}")
        logger.info(f"Run directory: {run_dir}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        metadata['status'] = 'failed'
        metadata['error'] = str(e)
        save_run_metadata(run_dir, metadata)
        
        if db_conn:
            update_pipeline_run(db_conn, run_id, status='failed', errors=str(e))
        
        raise
    
    finally:
        if db_conn:
            db_conn.close()

if __name__ == "__main__":
    run_pipeline()