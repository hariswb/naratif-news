#!/usr/bin/env python3
"""
Scheduler for Media Pipeline
Runs the pipeline periodically and tracks the next scheduled run.
"""

import time
import json
import argparse
import logging
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

STATE_FILE = Path("data/scheduler_state.json")

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(next_run):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "updated_at": datetime.now().isoformat(),
        "next_run": next_run.isoformat()
    }
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def run_pipeline_process():
    """Runs the pipeline execution script as a subprocess."""
    logger.info("Executing pipeline run...")
    try:
        # Using the same python interpreter as this script
        cmd = [sys.executable, "run_pipeline.py"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Pipeline run completed successfully.")
            # We could also parse the last line or check run_pipeline logs if needed
        else:
            logger.error(f"Pipeline run failed with return code {result.returncode}")
            logger.error(f"Stderr: {result.stderr}")
            
    except Exception as e:
        logger.error(f"Failed to execute pipeline: {e}")

def main():
    parser = argparse.ArgumentParser(description="Media Pipeline Scheduler")
    parser.add_argument("--interval-hours", type=float, default=24, help="Run interval in hours")
    args = parser.parse_args()
    
    logger.info(f"Starting scheduler. Interval: {args.interval_hours} hours")
    
    while True:
        # 1. Run the pipeline
        run_pipeline_process()
        
        # 2. Calculate next run
        next_run = datetime.now() + timedelta(hours=args.interval_hours)
        logger.info(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 3. Save state for the monitor
        save_state(next_run)
        
        # 4. Wait
        sleep_seconds = (next_run - datetime.now()).total_seconds()
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
            
if __name__ == "__main__":
    main()
