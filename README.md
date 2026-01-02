# Media Monitoring Pipeline — Daily Batch Architecture

## Overview

This project implements a **daily, batch-oriented media monitoring pipeline** focused on **narrative intelligence** for Indonesian news.

The pipeline:

* Collects news headlines from RSS feeds (XML)
* Normalizes and cleans text
* Extracts interpretable signals (Sentiment using local Indonesian dictionary)
* [Unimplemented] Aggregates signals into patterns
* [Unimplemented] Produces **ready-to-read narrative outputs**

## Core Design Principles

1. **Batch-first**: One run represents one snapshot of the media landscape.
2. **Artifacts over processes**: Each stage produces concrete outputs (files/DB records).
3. **Immutability**: Raw and intermediate artifacts are never mutated.
4. **Narrative over metrics**: Numbers exist to support interpretation.

---

## How to Run

### 1. Prerequisites
- Python 3.10+
- PostgreSQL (optional, for storage)

### 2. Setup Phase

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
The project uses `config/rss_sources.json` for source definitions.

**Optional: Database Storage**
To enable database storage:
1. Create `config/db.env` with the following content:
   ```env
   DB_NAME=media_monitoring
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   ```
2. If this file is missing, the pipeline will run but skip the database storage step.

### 4. Execute Pipeline

```bash
# Run the daily pipeline
python3 run_daily.py
```

This will:
1. Fetch RSS feeds to `data/runs/YYYY-MM-DD/raw/rss/`
2. Parse them to `data/runs/YYYY-MM-DD/parsed/`
3. Clean and normalize text
4. Analyze sentiment (Positive/Negative/Neutral)
5. Store results in DB (if configured) or log completion

---

## Folder Structure

```
media-pipeline/
├── run_daily.py          # Orchestrator
├── config/               # Configuration files
├── data/                 # Data artifacts (runs, logs)
├── pipeline/
│   ├── collect/          # RSS Fetching
│   ├── parse/            # XML to JSONL
│   ├── clean/            # Text Normalization
│   ├── signal/           # Sentiment Analysis (PySastrawi)
│   ├── aggregate/        # [Unimplemented] Aggregation
│   └── narrative/        # [Unimplemented] Narrative generation
├── sql/                  # Database schema
└── requirements.txt
```

## Implementation Details

### Sentiment Analysis
Uses a local dictionary-based approach specialized for Indonesian language (Sastrawi + Custom Dictionary).
- **Positive/Negative Words**: Stored in `pipeline/signal/data/`
- **Logic**: Counts weighted matches and normalizes score (-1, 0, 1).

### Storage
- **File System**: Used for raw XML and intermediate JSONL files.
- **PostgreSQL**: Used for structured article data and signal scores.
