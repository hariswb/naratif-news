# Media Monitoring Pipeline — Batch Architecture

## Overview

This project implements a **batch-oriented media monitoring pipeline** focused on **narrative intelligence** for Indonesian news.

The pipeline:

* Collects news headlines from RSS feeds (XML)
* Normalizes and cleans text
* Extracts interpretable signals (Sentiment using local Indonesian dictionary)
* [Unimplemented] Aggregates signals into patterns
* [Unimplemented] Produces **ready-to-read narrative outputs**

---

## How to Run

### Prerequisites
- Python 3.8+
- Docker and Docker Compose (for PostgreSQL)

### 1. Setup Phase

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

1. **Start PostgreSQL**:
    ```bash
    docker-compose up -d
    ```

2. **Run Migrations**:
    Apply the database schema using Alembic:
    ```bash
    alembic upgrade head
    ```

### 3. Configuration
The project uses `config/rss_sources.json` for source definitions.

**Optional: Database Storage**
To enable database storage:
1. Create `config/db.env` with the following content:
   ```env
   DB_NAME=media_pipeline
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_HOST=localhost
   DB_PORT=5432
   ```
2. If this file is missing, the pipeline will run but skip the database storage step.

### 4. Execute Pipeline

```bash
# Run the pipeline
python3 run_pipeline.py
```

This will:
1. Fetch RSS feeds to `data/runs/YYYY-MM-DD/raw/rss/`
2. Parse them to `data/runs/YYYY-MM-DD/parsed/`
3. Clean and normalize text
4. Analyze sentiment (Positive/Negative/Neutral)
5. Store results in DB (if configured) or log completion

### 5. Scheduling and Monitoring

#### Scheduler (Cron Job)
To run the pipeline periodically (e.g., every 24 hours), use the `scheduler.py` script:

```bash
# Run every 24 hours (default)
./venv/bin/python3 scheduler.py

# Run every 6 hours
./venv/bin/python3 scheduler.py --interval-hours 6
```

> **Note**: This script runs in a loop. To keep it running in the background, use `nohup`, `screen`, or a systemd service.

#### Monitor
To check the status of recent runs and see when the next run is scheduled:

```bash
./venv/bin/python3 monitor.py
```

**Example Output:**
```
Next Scheduled Run: 2026-01-14 10:00:00
--------------------------------------------------------------------------------
Recent Runs:
Run ID                Date        Status      Started             Duration
2026-01-13_11-18-03   2026-01-13  completed   2026-01-13 11:18    0:01:44
```

---

## Folder Structure

```
media-pipeline/
├── run_pipeline.py          # Orchestrator
├── config/               # Configuration files
├── data/                 # Data artifacts (runs, logs)
├── pipeline/
│   ├── collect/          # RSS Fetching
│   ├── parse/            # XML to JSONL
│   ├── clean/            # Text Normalization
│   ├── signal/           # Sentiment Analysis, NER, Framing Phrase Extraction
├── web/                  # Web application
└── requirements.txt
```


## Architecture

### Core Design Principles

1. **Batch-first**: One run represents one snapshot of the media landscape.
2. **Artifacts over processes**: Each stage produces concrete outputs (files/DB records).
3. **Immutability**: Raw and intermediate artifacts are never mutated.
4. **Narrative over metrics**: Numbers exist to support interpretation.

### Implementation Details

#### Run Pipeline (Orchestrator)
The `run_pipeline.py` script manages the sequential execution of the pipeline:
- **Run Management**: Generates a `run_id` and creates the directory structure (`data/runs/YYYY-MM-DD/`).
- **Metadata**: Tracks stage status and statistics in `run_meta.json`.
- **Database**: Updates `pipeline_runs` with progress and stats.
- **Logging**: Maintains run-specific logs.

#### Collect
Located in `pipeline/collect/fetch_rss.py`.
- **Function**: Iterates through sources in `config/rss_sources.json`.
- **Artifacts**: Saves raw XML responses to `data/runs/{run_id}/raw/rss/`.
- **Processing**: extracts title, link, summary, and publish date; handles timeouts.

#### Parse
Located in `pipeline/parse/rss_to_jsonl.py`.
- **Function**: Standardizes raw articles into a common format.
- **Artifacts**: Writes to `data/runs/{run_id}/parsed/raw_articles.jsonl`.
- **Format**: JSON Lines (JSONL) with ISO-formatted dates.

#### Clean
Located in `pipeline/clean/normalize.py`.
- **Text Normalization**: Strips HTML tags and normalizes whitespace.
- **Deduplication**: Uses MD5 hash of `title|summary` to remove exact duplicates.
- **Language Filter**: Uses `langdetect` to keep only Indonesian (`id`) articles.

#### Sentiment Analysis
Uses a local dictionary-based approach specialized for Indonesian language (Sastrawi + Custom Dictionary).
- **Positive/Negative Words**: Stored in `pipeline/signal/data/`
- **Logic**: Counts weighted matches and normalizes score (-1, 0, 1).



#### Named Entity Recognition (NER)
Uses `cahya/bert-base-indonesian-NER` (NusaBert) to extract entities from news titles and summaries.
- **Library**: `transformers` (Hugging Face)
- **Entities**: 
  ```
    'CRD': Cardinal
    'DAT': Date
    'EVT': Event
    'FAC': Facility
    'GPE': Geopolitical Entity
    'LAW': Law Entity (such as Undang-Undang)
    'LOC': Location
    'MON': Money
    'NOR': Political Organization
    'ORD': Ordinal
    'ORG': Organization
    'PER': Person
    'PRC': Percent
    'PRD': Product
    'QTY': Quantity
    'REG': Religion
    'TIM': Time
    'WOA': Work of Art
    'LAN': Language
  ```
- **Output**: Stores a list of detected entities with confidence scores.

#### Entity Framing
Uses n-gram windowing to extract phrases surrounding key entities (ORG, GPE, PER, etc.).
- **Logic**: Extracts a window of words around detected entities to capture how they are "framed" in the text.
- **Output**: Pairs of `entity_word` and `framing_phrase`.


## Web Dashboard

The project includes a **Visual Analytics Dashboard** located in the `web/` directory.

### Quick Start
```bash
# Start the API server
./venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```
Visit **[http://localhost:8000](http://localhost:8000)** to access the interface.

### Features
- **Trend Analysis**: Monitor sentiment changes over time.
- **Network Graph**: Explore connections between entities (politicians, organizations, etc.).
- **Fraing Analysis**: Identify dominant phrases associated with entities.
- **Interactive Filtering**: Filter by date, entity type, and exclude specific terms.

For detailed documentation, see [web/README.md](web/README.md).
