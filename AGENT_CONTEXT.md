# AI Agent Context & Guidelines

This document serves as the primary context for any AI agent working on the `media-pipeline` project. It outlines the project's identity, technical constraints, and workflow standards to ensure consistency and prevent repetitive setup instructions.

## 1. Project Identity & Philosophy

*   **Goal**: Narrative intelligence for Indonesian news.
*   **Batch-First**: One run = one snapshot. We process data in specific batches (runs), not necessarily daily.
*   **Artifacts Over Processes**: Each stage must produce concrete, immutable artifacts (files or DB records).
*   **Immutability**: Raw data (XML, JSONL) is sacred. Never mutate intermediate artifacts.
*   **Narrative Over Metrics**: The end goal is human-readable patterns, not just numbers.

## 2. Technology Stack & Environment

**CRITICAL**: You must strictly adhere to these paths. Do not assume the active shell is correct.

*   **Python Virtual Environment**:
    *   **Python Executable**: `./venv/bin/python3`
    *   **Pip Executable**: `./venv/bin/pip`
*   **Database**: PostgreSQL (via Docker Compose) managed by Alembic.
*   **Testing Framework**: `pytest`.

## 3. Workflow Standards

### A. executing the Pipeline
To run the daily pipeline manually:
```bash
./venv/bin/python3 run_pipeline.py
```

### B. Running Tests
To run the test suite:
```bash
./venv/bin/python3 -m pytest
```

### C. Database Operations
**CRITICAL SAFETY RULES**:
*   **Explicit Permission Required**: You must ask for explicit user permission before performing any **Create, Update, or Delete (CUD)** operations on the database content.
*   **Docker Caution**: Be extremely cautious with Docker containers and especially **Docker volumes**. Do not remove volumes unless explicitly instructed to "reset" or "wipe" data.

*   **Start Database**: `docker-compose up -d`
*   **Reset Database** (Extreme caution - requires explicit approval):
    ```bash
    docker-compose down -v
    docker-compose up -d
    ./venv/bin/alembic upgrade head
    ```
*   **Schema Changes**:
    1.  Modify `pipeline/storage/models.py`.
    2.  Generate migration: `./venv/bin/alembic revision --autogenerate -m "description"`
    3.  Apply migration: `./venv/bin/alembic upgrade head`

## 4. Coding Standards & File Structure

### Directory Structure
*   `pipeline/`: Core logic (cleaning, signals, parsing).
    *   `signal/`: New analysis modules go here.
*   `data/`: Runtime artifacts (ignored by git).
*   `tests/`: Unit and integration tests.
*   `alembic/`: Database migrations.

### Adding a New Signal
1.  **Logic & Unit Test**:
    *   Create the logic script in `pipeline/signal/`.
    *   Test it using static data artifacts in `tests/data`.
    *   Create and pass unit tests.
2.  **Model & Migration**:
    *   Define the table in `pipeline/storage/models.py`.
    *   Create and run Alembic migration.
3.  **Integration**: Add the step to `run_pipeline.py`.
4.  **Pipeline Test**: Verify the end-to-end flow.

## 5. Common Common Pitfalls to Avoid
*   **Do not** use `python` or `pip` directly. Always use the `./venv/bin/` prefix.
*   **Do not** modify the `data/` directory manually; it is for pipeline output only.
*   **Do not** skip testing before declaring a task complete.
