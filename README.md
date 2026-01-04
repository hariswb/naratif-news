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

### Prerequisites
- Python 3.8+
- Docker and Docker Compose (for PostgreSQL)

### Database Setup

1. **Start PostgreSQL**:
    ```bash
    docker-compose up -d
    ```

2. **Run Migrations**:
    Apply the database schema using Alembic:
    ```bash
    alembic upgrade head
    ```

3. **Verify Connection**:
    You can check if the setup is correct by running:
    ```bash
    python tests/test_db_connection.py
    ```

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
   DB_NAME=media_pipeline
   DB_USER=postgres
   DB_PASSWORD=postgres
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
│   ├── signal/           # Sentiment Analysis, Topic Modelling
│   ├── aggregate/        # [Unimplemented] Aggregation
│   └── narrative/        # [Unimplemented] Narrative generation
├── sql/                  # Database schema
└── requirements.txt
```

## Implementation Details

### Run Daily (Orchestrator)
The `run_daily.py` script manages the sequential execution of the pipeline:
- **Run Management**: Generates a daily `run_id` and creates the directory structure (`data/runs/YYYY-MM-DD/`).
- **Metadata**: Tracks stage status and statistics in `run_meta.json`.
- **Database**: Updates `pipeline_runs` with progress and stats.
- **Logging**: Maintains run-specific logs.

### Collect
Located in `pipeline/collect/fetch_rss.py`.
- **Function**: Iterates through sources in `config/rss_sources.json`.
- **Artifacts**: Saves raw XML responses to `data/runs/{run_id}/raw/rss/`.
- **Processing**: extracts title, link, summary, and publish date; handles timeouts.

### Parse
Located in `pipeline/parse/rss_to_jsonl.py`.
- **Function**: Standardizes raw articles into a common format.
- **Artifacts**: Writes to `data/runs/{run_id}/parsed/raw_articles.jsonl`.
- **Format**: JSON Lines (JSONL) with ISO-formatted dates.

### Clean
Located in `pipeline/clean/normalize.py`.
- **Text Normalization**: Strips HTML tags and normalizes whitespace.
- **Deduplication**: Uses MD5 hash of `title|summary` to remove exact duplicates.
- **Language Filter**: Uses `langdetect` to keep only Indonesian (`id`) articles.

### Sentiment Analysis
Uses a local dictionary-based approach specialized for Indonesian language (Sastrawi + Custom Dictionary).
- **Positive/Negative Words**: Stored in `pipeline/signal/data/`
- **Logic**: Counts weighted matches and normalizes score (-1, 0, 1).

### Topic Modelling
Uses Latent Dirichlet Allocation (LDA) to discover abstract topics within the collected news articles.
- **Library**: `scikit-learn` (TfidfVectorizer, LatentDirichletAllocation)
- **Preprocessing**: 
  - Acronym expansion (e.g., "KPK" -> "Komisi Pemberantasan Korupsi")
  - Custom stopword removal (Indonesian)
  - Text cleaning (lowercase, punctuation/number removal)
- **Output**: Assigns a dominant topic index and top keywords to each article.
- **Example Result**:
  - *Topic 1*: pembangunan, anggaran, pajak, sisa, kerja, lebaran, piala, timnas, asia, indonesia
  - *Topic 2*: prabowo, megawati, jadwal, pertemuan, indonesia, partai, kereta, api, merah, presiden
  - *Topic 3*: trump, tarif, amerika, serikat, indonesia, impor, prabowo, republik, china, undang
