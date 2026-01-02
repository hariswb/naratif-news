# Media Monitoring Pipeline — Daily Batch Architecture

## Overview

This project implements a **daily, batch-oriented media monitoring pipeline** focused on **narrative intelligence**, not real-time analytics or dashboards.

The pipeline:

* Collects news headlines from RSS feeds (XML)
* Normalizes and cleans text
* Extracts interpretable signals (sentiment, topics)
* Aggregates signals into patterns
* Produces **ready-to-read narrative outputs**

The system prioritizes:

* Reproducibility
* Explainability
* Clear separation of concerns
* Minimal operational complexity

Execution is manual or via `cron`.

---

## Core Design Principles

1. **Batch-first**
   One run represents one snapshot of the media landscape.

2. **Artifacts over processes**
   Each stage produces concrete outputs that can be inspected and re-used.

3. **Immutability**
   Raw and intermediate artifacts are never mutated.

4. **Narrative over metrics**
   Numbers exist to support interpretation, not dashboards.

5. **No premature orchestration**
   The pipeline is linear and explicit.

---

## High-Level Pipeline Flow

```
RSS XML
→ Raw storage
→ Parsed articles (JSONL)
→ Cleaned canonical articles (DB)
→ Article-level signals
→ Aggregated media signals
→ Narrative blocks
→ Reader outputs
```

Each step depends only on artifacts produced upstream.

---

## Folder Structure

```
media-pipeline/
├── run_daily.py
├── config/
│   ├── sources.yaml
│   ├── db.env
│   └── pipeline.yaml
│
├── data/
│   └── runs/
│       └── YYYY-MM-DD/
│           ├── run_meta.json
│           ├── raw/
│           │   └── rss/
│           │       ├── source_a.xml
│           │       ├── source_b.xml
│           │       └── source_c.xml
│           ├── parsed/
│           │   └── raw_articles.jsonl
│           └── logs/
│               └── pipeline.log
│
├── pipeline/
│   ├── run.py
│   ├── collect/
│   │   └── fetch_rss.py
│   ├── parse/
│   │   └── rss_to_jsonl.py
│   ├── clean/
│   │   └── normalize_text.py
│   ├── signal/
│   │   ├── sentiment.py
│   │   └── topics.py
│   ├── aggregate/
│   │   └── media_signals.py
│   └── narrative/
│       └── assemble.py
│
├── models/
│   └── topic_model.pkl
│
├── sql/
│   ├── schema.sql
│   ├── daily_aggregates.sql
│   └── narratives.sql
│
├── logs/
│   └── pipeline.log
│
├── requirements.txt
└── README.md
```

---

## Directory Responsibilities

### Root

**`run_daily.py`**
Single entry point for the pipeline.
Responsible only for:

* Creating a `run_id`
* Creating run folders
* Executing pipeline stages in order

No business logic lives here.

---

### `config/`

* `sources.yaml`
  Defines RSS sources (name, URL, language).

* `pipeline.yaml`
  Runtime parameters (time window, topic count, model versions).

* `db.env`
  Database connection settings (never committed).

---

### `data/runs/YYYY-MM-DD/`

Run-scoped, immutable artifacts.

* `run_meta.json`
  Metadata tying outputs to a specific execution.

* `raw/rss/`
  Original RSS XML responses (source of truth).

* `parsed/raw_articles.jsonl`
  One article per line, minimally normalized.

* `logs/`
  Logs specific to this run.

---

### `pipeline/`

Core logic, organized strictly by stage.

Each submodule:

* Consumes upstream artifacts
* Produces new artifacts
* Does not reach across stages

**Stages**

* `collect/` — fetch RSS only
* `parse/` — XML → JSONL
* `clean/` — deterministic text normalization
* `signal/` — sentiment & topic inference
* `aggregate/` — outlet/topic-level aggregation
* `narrative/` — human-readable summaries

---

### `models/`

Serialized models (e.g., topic models).
No training code lives here.

---

### `sql/`

Explicit SQL used for:

* Schema definition
* Aggregation logic
* Narrative assembly

This keeps semantic decisions visible and auditable.

---

### `logs/`

Global logs for infrastructure-level debugging.

---

## Storage Model

* **Filesystem**

  * Raw XML
  * Parsed JSONL
  * Logs
  * Immutable run artifacts

* **Database**

  * Canonical articles
  * Signals
  * Aggregations
  * Narrative blocks

The database is **not** used for raw ingestion.

---

## Execution Model

The pipeline is executed once per morning:

```bash
python run_daily.py
```

or via cron:

```bash
0 7 * * * /usr/bin/python /path/to/run_daily.py
```

Each run:

* Is isolated
* Can be re-run safely
* Produces a complete, self-contained snapshot

---

## What This Architecture Intentionally Avoids

* Streaming / real-time processing
* Dashboard-first design
* Hidden model state
* Implicit recomputation
* Tight coupling between stages

---

## Mental Model

> **Raw text → Signals → Patterns → Narratives**

If a component does not clearly belong to one of these stages, it does not belong in the pipeline.

---

This README defines the **contract of the system**.
Implementation details may evolve, but these boundaries should not.

