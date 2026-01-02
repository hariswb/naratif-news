# Media Monitoring Pipeline - Setup Instructions

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Installation

### 1. Clone or Create Project Structure

Create the following directory structure:

```
media-pipeline/
├── run_daily.py
├── requirements.txt
├── config/
│   └── db.env
├── data/
│   └── runs/
├── logs/
├── pipeline/
│   ├── __init__.py
│   ├── db.py
│   ├── collect/
│   │   ├── __init__.py
│   │   └── fetch_rss.py
│   ├── parse/
│   │   ├── __init__.py
│   │   └── rss_to_jsonl.py
│   ├── clean/
│   │   ├── __init__.py
│   │   └── normalize_text.py
│   └── signal/
│       ├── __init__.py
│       └── sentiment.py
└── sql/
    └── schema.sql
```

### 2. Create Empty `__init__.py` Files

Create empty `__init__.py` files in:
- `pipeline/__init__.py`
- `pipeline/collect/__init__.py`
- `pipeline/parse/__init__.py`
- `pipeline/clean/__init__.py`
- `pipeline/signal/__init__.py`

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL Database

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE media_monitoring;

# Exit psql
\q
```

#### Initialize Schema

```bash
psql -U postgres -d media_monitoring -f sql/schema.sql
```

### 5. Configure Database Connection

Create `config/db.env` file:

```env
DB_NAME=media_monitoring
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
```

**Important:** Never commit `db.env` to version control. Add it to `.gitignore`:

```bash
echo "config/db.env" >> .gitignore
```

### 6. Load Environment Variables

Before running the pipeline, load the environment variables:

```bash
# Linux/Mac
export $(cat config/db.env | xargs)

# Or use python-dotenv in your code
```

Alternatively, modify `run_daily.py` to load from `db.env`:

```python
from dotenv import load_dotenv
load_dotenv('config/db.env')
```

### 7. Create Required Directories

```bash
mkdir -p data/runs
mkdir -p logs
```

## Running the Pipeline

### Manual Execution

```bash
python run_daily.py
```

### Schedule with Cron

Run daily at 7 AM:

```bash
# Edit crontab
crontab -e

# Add this line
0 7 * * * cd /path/to/media-pipeline && /usr/bin/python3 run_daily.py
```

## Testing Individual Stages

### Test RSS Collection

```python
from pipeline.collect.fetch_rss import collect_all_rss
from pathlib import Path

test_dir = Path("data/runs/test")
articles, stats = collect_all_rss(test_dir)
print(f"Collected {len(articles)} articles")
```

### Test Parsing

```python
from pipeline.parse.rss_to_jsonl import parse_to_jsonl, load_jsonl
from pathlib import Path

run_dir = Path("data/runs/2024-01-15")
# Assuming you have articles from collection
parse_to_jsonl(run_dir, articles)

# Load back
articles = load_jsonl(run_dir / "parsed/raw_articles.jsonl")
```

### Test Cleaning

```python
from pipeline.clean.normalize_text import clean_articles

cleaned, stats = clean_articles(articles)
print(f"Cleaning stats: {stats}")
```

### Test Sentiment Analysis

```python
from pipeline.signal.sentiment import analyze_all_sentiments

articles_with_sentiment, stats = analyze_all_sentiments(cleaned)
print(f"Sentiment distribution: {stats['sentiment_distribution']}")
```

## Output Structure

After a successful run, you'll have:

```
data/runs/YYYY-MM-DD/
├── run_meta.json          # Run metadata
├── raw/
│   └── rss/
│       ├── detik_berita.xml
│       ├── detik_finance.xml
│       └── ...
├── parsed/
│   └── raw_articles.jsonl
└── logs/
    └── pipeline.log
```

## Monitoring

### Check Pipeline Status

Query the database:

```sql
-- Latest runs
SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 5;

-- Run statistics
SELECT * FROM run_statistics WHERE run_id = '2024-01-15';

-- Sentiment distribution
SELECT * FROM sentiment_distribution WHERE run_id = '2024-01-15';
```

### View Logs

```bash
# Latest pipeline log
tail -f logs/pipeline.log

# Specific run log
tail -f data/runs/2024-01-15/logs/pipeline.log
```

## Troubleshooting

### Database Connection Failed

1. Check PostgreSQL is running:
   ```bash
   sudo systemctl status postgresql
   ```

2. Verify credentials in `config/db.env`

3. Test connection:
   ```bash
   psql -U postgres -d media_monitoring
   ```

### RSS Feed Timeout

- Some sources may be slow or down
- Check logs for specific failed sources
- Pipeline continues with available sources

### Language Detection Issues

- `langdetect` may fail on very short text
- Articles with detection errors are logged but not included

### Sentiment Analysis Slow

- Translation to English takes time
- Consider running on a subset for testing
- Production runs may take 10-30 minutes depending on article count

## Next Steps

After setup:

1. Run a test pipeline execution
2. Verify data in PostgreSQL
3. Set up cron job for daily execution
4. Build narrative/aggregation stages (future work)
5. Create reporting interface (future work)

## Support

Check logs in:
- `logs/pipeline.log` (global)
- `data/runs/YYYY-MM-DD/logs/pipeline.log` (run-specific)