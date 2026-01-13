#!/usr/bin/env python3
"""
Monitor for Media Pipeline
Displays the latest run status and the next scheduled run.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import desc

# Add pipeline modules to path
sys.path.append(str(Path(__file__).parent))

from pipeline.db import get_db_session
from pipeline.storage.models import PipelineRun

STATE_FILE = Path("data/scheduler_state.json")

def get_next_run():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get("next_run", "Unknown")
        except Exception:
            return "Error reading state"
    return "Not scheduled (scheduler might not be running)"

def print_row(cols, width=20):
    row = "".join(str(c).ljust(w) for c, w in zip(cols, width))
    print(row)

def main():
    print("="*80)
    print("MEDIA PIPELINE MONITOR")
    print("="*80)
    
    # 1. Show next run
    next_run = get_next_run()
    if next_run != "Unknown" and next_run != "Not scheduled (scheduler might not be running)" and "T" in next_run:
         # Format if it looks like ISO
         try:
             dt = datetime.fromisoformat(next_run)
             next_run = dt.strftime("%Y-%m-%d %H:%M:%S")
         except:
             pass
             
    print(f"Next Scheduled Run: \033[1m{next_run}\033[0m")
    print("-" * 80)
    
    # 2. Show recent runs
    print("Recent Runs:")
    headers = ["Run ID", "Date", "Status", "Started", "Duration", "Errors"]
    widths = [22, 12, 12, 20, 10, 20]
    print_row(headers, widths)
    print("-" * 96) # Slightly wider for the header line
    
    session = get_db_session()
    try:
        runs = session.query(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(5).all()
        
        if not runs:
            print("No runs found in database.")
        
        for run in runs:
            status_color = "\033[92m" if run.status == 'completed' else "\033[91m"
            reset_color = "\033[0m"
            
            # Calculate duration
            duration = "-"
            if run.started_at and run.completed_at:
                delta = run.completed_at - run.started_at
                duration = str(delta).split('.')[0] # Remove microseconds
            
            started_str = run.started_at.strftime("%Y-%m-%d %H:%M") if run.started_at else "-"
            error_summary = (run.errors[:45] + "...") if run.errors and len(run.errors) > 45 else (run.errors or "-")
            
            print_row([
                run.run_id,
                run.run_date,
                f"{status_color}{run.status}{reset_color}",
                started_str,
                duration,
                error_summary
            ], widths)
            
    except Exception as e:
        print(f"Error fetching runs: {e}")
    finally:
        session.close()
        
    print("="*80)

if __name__ == "__main__":
    main()
